---
title: "运营 1000+ API 认证的教训：当 OAuth 轮换让普通 Bug 不可逆"
date: "2026-11-23 01:01:11"
tags: ["OAuth", "API 认证", "AI Agent", "工程实践"]
categories: "技术动态"
---

## 事件概述

Nango 是一个开源项目，用于让 Web 应用和 Agent 集成第三方 API。客户把 Nango 嵌入自己的产品，终端用户连接第三方账号后，Nango 负责维持这些连接持续可用。根据原文，Nango 支持的 API 数量已从约 400 个增长到 1000 多个。

文章复盘了一次生产事故：2025 年 5 月，Nango 合并的一个 PR 中存在关键 Bug——一个永远不会触发的 `if` 条件，导致刷新后的凭据无法保存到数据库。团队在不到两小时内发现并回滚，但在这两小时里，定时任务已经刷新并丢弃了数百个连接的 access token 和 refresh token。

对多数 API 来说，这个问题可以恢复：旧的 refresh token 仍然有效，下一次定时刷新可以修复连接。但问题在于，很多 Provider 会轮换 refresh token，并在新 token 签发时立即让旧 refresh token 失效。Airtable、Atlassian 属于这一类；Salesforce 和 Slack 在 OAuth 应用启用轮换时也可能如此。对于这些受影响的连接，token 无法找回，客户只能让终端用户重新走一遍授权同意页面。

文章的核心结论是：OAuth 是标准，但 OAuth Provider 并不是可互换的。每个 API 的认证行为都有细微差异，其中一些差异没有文档，只在生产环境中暴露。

## 关键技术点

### 1. Refresh token 轮换让普通 Bug 变成不可逆事故

原文把 refresh token 轮换视为安全收益，但同时指出：轮换路径上的 Bug 可能永久破坏一个连接，迫使用户重新授权。这也是那次事故代价高昂的原因。

Nango 现在的做法是：

- 把 refresh token 当作“钱”，而不是缓存；
- 新 token 必须在其他操作可能失败之前先持久化；
- 持久化路径有独立的回归测试；
- 平台级刷新异常会立即呼叫 on-call 团队。

不同 Provider 对 refresh token 轮换的执行方式差异很大：

- **Airtable**：使用陈旧 token 或错误 client credentials 发起刷新，可能返回 400 或 401，但 Airtable 不止于此——它会撤销用户对应用的全部授权，唯一恢复方式是用户重新连接。重复发送同一个刷新请求也可能导致撤销。Airtable 文档中提到了重复刷新的短宽限期，但超过该宽限期后重试陈旧 token 会撤销授权。Airtable 还会在刷新成功的瞬间让旧 access token 失效，因此仍在运行的长任务可能中途失败。
- **Xero**：处理得更好。如果刷新失败或响应未到达，可以在最多 30 分钟内使用之前的 refresh token 重试。
- **Exact Online**：access token 只有 10 分钟有效期，token endpoint 会拒绝在过期前 30 秒以上发起的刷新。Nango 原先“提前 15 分钟刷新”的规则导致每次刷新都落在窗口之外并被拒绝，后来不得不增加按 Provider 配置的过期缓冲。

这些问题推动 Nango 用分布式锁把同一连接的刷新操作串行化。

### 2. Access token 何时过期并不可靠可知

OAuth 2.0 规范 RFC 6749 中，`expires_in` 对 access token 是可选字段。原文指出，这成为静默故障的常见来源。

- **Zendesk**：为 OAuth 客户端推出会过期的 access token，包括已有客户端。只有请求时才会在 token 响应中返回 `expires_in`；不请求该参数时，access token 仍会按默认策略过期，但响应不会说明何时过期。Nango 是在轮换 refresh token 失效、连接开始死亡之后才发现这一点。
- **Salesforce**：token 响应不包含过期时间。文档给出的检查方式是调用单独的 introspection endpoint，Nango 在决定是否刷新 access token 之前会调用该端点。但 2024 年 6 月，该 introspection endpoint 开始对部分 token 间歇性返回 `unsupported_token_type`。introspection 失败时，Nango 仍然执行刷新；替换后的 access token 可以正常 introspection，但原文表示始终没有弄清原始 token 失败的原因。

Refresh token 的生命周期同样不一致：

- **NetSuite**：OAuth refresh token 在 7 天后过期，需要完整重新授权，因此很多团队改用其 token-based authentication。
- **Google**：refresh token 原则上无限期有效，但文档列出的条件除外，包括应用处于“Testing”状态、六个月未使用，或用户对某个 client 的 live refresh token 超过 100 个。

Nango 现在的做法是用 cron 刷新陈旧凭据，让 token 在因不活跃而失效之前先被使用。

### 3. 认证失败不一定表现为 401

原文强调，认证失败并不总是返回 401：

- **Zoho CRM**：token endpoint 返回 HTTP 200，错误放在响应体里。
- **Workday 和 Dayforce**：缺少权限策略时完全不返回错误，API 只是返回空数据。
- 原文支持的一个基于 SOAP 的 API 对所有请求都返回 HTTP 200，包括错误密码。
- **LastPass**：同样返回 HTTP 200，失败信息以纯文本形式放在响应体中；Nango 对它的凭据检查实际上是在响应中搜索字符串“Authorization Error”。

因此 Nango 构建了按 Provider 的启发式检查。原文统计时，其注册表中约 935 个 Provider 里有 276 个声明了 Nango 可以调用的认证端点，用来检查凭据是否仍然有效。

### 4. Provider 会对 API 认证做破坏性变更

原文提到，Nango 的 Provider 配置提交中有 16% 是修复。Provider 认证变更没有可靠的订阅源，团队往往通过失败的流程或客户报告才知道。

- **Figma**：通过邮件宣布凭据必须从请求体移到 Basic Authorization header，并且 OAuth host 也要变更。Nango 发布了更新，但错过邮件的人可能在刷新开始失败时才发现变化。
- **Shopify**：改变了 offline token 的签发方式，应用开始收到会过期的 token，而以前不会。Nango 发布配置变更以保留旧行为。

### 5. 有时要绕过 Provider 来构建

支持新 API 通常假设两件事：能拿到凭据测试，以及能找到准确的认证文档。原文表示，在 Nango 的规模下，这两个假设经常不成立，绕过 Provider 构建已是常规操作：

- **Salesforce Data Cloud**：单独 provision，Nango 的测试组织都不包含它。其认证需要对不同 host 进行两次链式 token exchange。Nango 根据文档中的响应构建了 mock server，以便在没有真实凭据的情况下实现和测试流程。
- **LastPass**：API 并不是真正的 REST，几乎每个操作都命中同一个 URL，action 放在请求体中。这打破了 Nango 代理中“每个集成都定义单独端点”的假设，于是他们增加了对只有 base URL 的 API 的支持。
- **Asana**：一个反复出现的 OAuth 错误（`client_id is missing or invalid`）的解决方案由社区成员在 Asana 支持论坛中找到，并补充进 Nango 文档。Asana 自己的文档并未覆盖这一点。
- **Read.ai**：文档中的授权 URL 指向其内部开发者测试页面，真实端点来自查询其 OpenID discovery。原文在此处截断，后续内容未说明。

## 对数据科学或 AI Agent 落地的意义

这篇文章虽然讲的是 API 认证基础设施，
