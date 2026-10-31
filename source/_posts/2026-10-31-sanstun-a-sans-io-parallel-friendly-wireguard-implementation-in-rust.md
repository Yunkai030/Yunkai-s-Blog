---
title: "sanstun：面向并行与易用性的 sans-IO WireGuard Rust 实现"
date: "2026-10-30 21:30:00"
tags: ["Rust", "WireGuard", "sans-IO", "网络编程", "开源"]
categories: "技术动态"
---

## 事件概述

Firezone 博客宣布了一个名为 **sanstun** 的新项目：用 Rust 实现的 WireGuard 状态机，采用 sans-IO 设计，强调易用性、安全性和性能，并提供“parallel-friendly”的惯用 API。

根据原文，Firezone 早期使用 `boringtun` 作为 WireGuard 实现。随着产品需求演进，他们不断在 fork 中打补丁，同时尽量保持与上游 API 兼容，但维持 100% 兼容变得越来越困难。原文提到，即使排除依赖升级，相关补丁和修复也超过 70 个 PR，其中包含边缘情况修复、新 API 和可配置性改进。经过两年多的使用和修补，团队对用户态 WireGuard 实现应有的 API 形态有了更清晰的认识，最终将其整理为 sanstun。

该文章来自 Hacker News Front Page，摘要显示当时获得 59 points、14 条评论。原文正文在讨论并行密码学实现的部分被截断，因此本文只能基于已展示内容进行梳理。

## 关键技术点

### 1. sans-IO：把 IO 与副作用从状态机中剥离

sans-IO 的核心思想是：将 IO 和副作用与状态及“业务逻辑”清晰分离。原文特别指出，这里的 IO 不仅指文件或网络 IO，也包括**时间和随机性**。由于没有副作用，sans-IO 组件更容易组合和测试，也能避免 function coloring 问题，并且与 Rust 的所有权规则配合较好。

原文强调，sans-IO 并非 Rust 专属，其模式可以应用到任何语言。

### 2. 时间处理与可模拟性

Firezone 对 `boringtun` 最早的重大改动之一，是让时间处理完全 sans-IO：新增带 `_at` 后缀的 API，接收 `Instant`。原文认为，如果想准确模拟整个系统，sans-IO 的时间处理非常重要。

### 3. 移除内部缓冲

`boringtun` 在没有会话时会自动建立会话，并在库内部缓冲待发送报文。原文指出这带来几个问题：缓冲区最终需要被排空，`boringtun` 通过要求调用 `decapsulate` 并传入零长度数据报来解决，方式不够直观；还会引入额外分配；缓冲区大小本应可配置。sanstun 的结论是：**库内不缓冲**，从而简化接口和两侧实现。

### 4. 新的 API 骨架

原文列出的核心 API 包括：

- 入站报文：`Tunnel::handle_handshake_initiation`、`Tunnel::handle_handshake_response`、`Tunnel::handle_cookie_reply`、`Tunnel::begin_decapsulate` 与 `Tunnel::commit_decapsulate`
- 出站报文：`Tunnel::begin_encapsulate`
- 定时器更新：`Tunnel::handle_timeout` 与 `Tunnel::poll_timeout`
- 事件处理：`Tunnel::poll_event`

发送报文时调用 `Tunnel::begin_encapsulate`；如果尚无会话，是否缓冲由调用方决定。需要新建会话时，可以随时通过 `Tunnel::initiate_handshake` 发起握手。

### 5. 用类型系统固化协议不变量

原文用较大篇幅解释 WireGuard 协议中与 API 设计相关的部分：

- WireGuard 支持 4 类消息：握手初始化、握手响应、cookie 回复和加密数据。
- 每个会话以 Diffie-Hellman 密钥交换开始，这是相对昂贵的操作。
- 为防止 DoS，WireGuard 规定 cookie 机制，迫使远端证明其声称的源 IP 所有权，从而支持按源 IP 对握手限速。限速作用于整个 WireGuard 接口，而非单个隧道。
- 握手完成后，双方可交换对称加密数据包，并交换本地选择的 session index，用于隧道解复用以及隧道内多会话区分。

sanstun 将这些概念直接映射为 `Interface` 和 `Tunnel` 类型。所有入站报文都必须经过 `Interface::receive`，这是唯一解析原始数据报的公开 API。它会解析报文、应用限速、生成 cookie 回复并校验握手消息，然后返回 `ReceivedMessage`。原文强调，`HandshakeInitiation` 等类型的构造器都是 crate-private：即使 `Tunnel` 暴露了公开的 `handle_handshake_initiation`，调用方也必须先经过 `Interface::receive` 获得对应类型，从而无法绕过限速器。

### 6. 并行友好

标题和开头提到 sanstun 是 “parallel-friendly” 的，但原文正文在 “Parallel crypt” 处截断，**具体并行密码学实现和并行调度机制原文未完整说明**。

## 对数据科学或 AI Agent 落地的意义

需要说明的是，原文并未直接讨论 sanstun 与数据科学或 AI Agent 的关系，以下是从工程模式层面的引申，而非原文结论。

sans-IO 对 AI Agent 工程化有几点可借鉴之处：

1. **状态与副作用分离，便于回放和测试**。Agent 系统大量依赖网络调用、时间、随机采样和外部工具，如果把这些副作用从核心状态机中剥离，就可以在模拟环境中复现完整交互轨迹，降低线上问题定位成本。
2. **时间可注入**。原文把 `Instant` 作为显式参数，这对 Agent 的超时、重试、调度和模拟推进都有直接参考价值。测试中不必依赖真实时钟。
3. **不在库内隐式缓冲**。Agent 框架经常在工具调用层做隐式排队和缓冲，容易造成背压不透明。sanstun 把缓冲责任交给调用方，接口更简单，但也要求上层明确管理队列和生命周期。
4. **用类型系统固化不变量**。通过私有构造器和统一入口强制经过限速、校验等安全路径，这种思路可以迁移到 Agent 的工具调用网关：让“绕过安全检查”在类型层面难以表达。

对数据科学平台而言，sanstun 本身是网络隧道实现，并非数据分析工具；但其 sans-IO 设计对构建可测试、可模拟的分布式数据管道和 Agent 运行时具有方法论层面的参考意义。

## 我的技术点评

sanstun 的设计取向相当克制，值得肯定。

第一，**“不缓冲”是一个正确的简化**。库内自动建会话和缓冲看似方便，但会把生命周期、背压和内存分配问题藏起来。sanstun 把 `begin_encapsulate` / `commit_encapsulate` 拆开，把“是否需要缓冲”的决定权交给调用方，接口语义更清晰。代价是调用方要承担更多状态管理责任，迁移成本不容忽视。

第二，**用类型系统强制安全路径**是这篇文章最有价值的部分之一。`Interface::receive` 作为唯一解析入口，构造器 crate-private，使得限速和 cookie 校验难以被绕过。原文提到“忘记应用限速器”和“把入站报文路由到错误隧道”这类 bug 在正常运行时不易暴露，用编译期不变量来防范是合理思路。

第三，**sans-IO 的时间处理**对模拟和测试非常关键。
