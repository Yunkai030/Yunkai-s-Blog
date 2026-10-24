---
title: "OpenAI 如何将 Habitat 在线存储扩展至 10 亿 ChatGPT 用户：Azure Cosmos DB 多租户实践（Part II）"
date: "2026-10-23 17:00:00"
tags: ["OpenAI", "Azure Cosmos DB", "多租户", "在线存储", "数据工程"]
categories: "技术动态"
---

## 事件/产品概述

OpenAI Engineering 发布了《Rapidly scaling online storage to serve over 1 billion ChatGPT users (Part II)》，介绍其在线存储平台 Habitat 如何通过优化 Azure Cosmos DB 来支撑 ChatGPT 的超大规模增长。

根据原文，Habitat 是 OpenAI 产品快速、可靠访问数据的在线存储平台，需要在 40 个地理区域内为超过 10 亿用户提供毫秒级响应。Part I 主要讲 Habitat 如何从 Python 客户端演进为服务，以及如何把 Python 服务推到通常被认为不现实的规模；Part II 则聚焦底层存储组件 Azure Cosmos DB 的扩展实践。

原文提到，OpenAI 与 Azure 团队紧密合作，形成了可行的多租户方案：co-managed containers，并在全球大规模场景下获得良好的读性能。文章摘要还提到，Habitat 借助可靠的多租户、全局缓存和 Azure Cosmos DB，为 ChatGPT 带来 12 倍更快的读取。不过，原始正文在 “Weak partitions” 段落处截断，关于 co-managed containers 的具体实现、全局缓存的细节以及 12 倍读性能的测量条件，原文未说明。

## 关键技术点

### 1. Habitat 的定位与架构位置

Habitat 是 OpenAI 的在线存储平台，服务于 ChatGPT、API、Codex 和内部服务等。原文架构图显示，Habitat 涉及缓存、ACL 策略、授权、放置与数据驻留、加密、数据安全、隔离、多租户、限流、请求整形、路由、schema 查找等能力；底层存储资源包括 Azure Cosmos DB、Nanobase、Valkey、Blob storage，并通过 CDC 服务对接 Databricks、Rockset、Kafka 等系统。

这说明 Habitat 并不是简单的数据库客户端，而是位于产品与存储资源之间的平台层，承担多租户、安全、路由、缓存和数据驻留等职责。

### 2. 单租户与多租户的权衡

原文对单租户和多租户的取舍讲得比较直接：

- 单租户让每个产品面团队维护自己的系统，可以缩小故障爆炸半径，所有权边界清晰，工作负载隔离容易；但随着团队和产品面增长，运维成本高，容量规划分散，容易过度预留资源。
- 多租户把控制权交给集中化的数据库团队，由更有经验的团队做资源供给；但会带来 noisy-neighbor 问题，即某个租户占用异常高比例资源，影响其他租户。

Habitat 的多租户路径并不是一条直线：原文称其经历了从“一个多租户 Azure Cosmos DB 容器”，到“为单租户提供后备容器”，再回到“默认多租户容器”的循环旅程。OpenAI 也表示，Habitat 的多租户故事仍处于早期阶段，他们尽量利用 Azure Cosmos DB 的内置原语来推迟相关投入。

### 3. Azure Cosmos DB 容器模型

原文给出了一个简化背景：

- Azure Cosmos DB account 定义一组容器和复制策略。
- 每个容器按 RU/s 配置吞吐量。
- 容器内数据按指定的逻辑分区键进行分片，逻辑分区键有文档化的存储和吞吐限制。
- Azure Cosmos DB 会把逻辑分区键分布到较少的物理分区上；当存储超过阈值，或容器需要更多物理分区来维持配置吞吐时，会拆分成多个物理分区。

关键点在于：文档中的逻辑分区键限制，实际执行限制的位置是物理分区。原文在 Phase I 问题中明确指出，逻辑分区无法真正达到 10,000 RU/s，而是与同一物理分区上的其他逻辑分区键共享物理分区限制。

### 4. Phase I 的问题：直接依赖 Cosmos DB 原语

Phase I 中，OpenAI 最初允许任何客户端负载进入，依赖每个逻辑分区键 10K RU/s 的限制提供背压；同时每个 account 只使用一个默认 Azure Cosmos DB 容器。原文指出这带来几类问题：

**逻辑分区键限制与冲突。** 由于早期 API 选择，Habitat 把逻辑分区键选择直接暴露给客户端。结果，不同产品用例经常在 `user_id`、`workspace_id` 等常用分区键上发生冲突。这些用例共享同一逻辑分区键上的 Cosmos DB 限制，从而约束了单个用户的整体吞吐。

**Noisy neighbors。** 物理分区才是限制实际执行的位置。一个热点或噪声租户可能影响同一物理分区上许多不相关的逻辑分区键，甚至让细分产品功能的工作负载干扰核心登录和注册流程。

**Weak partitions。** 原文提到，给定物理分区的吞吐限制会随容器总配置吞吐变化。但正文在此处截断，后续关于 weak partitions 的完整分析原文未说明。

原文还提到，在迁移到 Habitat 和 Azure Cosmos DB 之前，他们扩展 Postgres 时也遇到过类似问题：来自非常热的组织或热键的请求可能打垮整个数据库；团队曾投入大量精力缓存这些键，并在缓存未命中时引入 lease，避免缓存未命中负载压垮底层数据库。这一段可以作为理解 Habitat 多租户设计动机的背景。

### 5. 多租户与缓存方向

原文明确提到的方向包括：与 Azure 合作采用 co-managed containers 的多租户方案，以及摘要中提到的 global caching。结合 Habitat 架构图，缓存是其平台能力的一部分。但具体如何做全局缓存、如何隔离 co-managed containers、如何实现 12 倍读性能提升，原文正文未展开，不能过度推断。

## 对数据科学或 AI Agent 落地的意义

对 AI Agent 和数据科学平台来说，这篇工程文章
