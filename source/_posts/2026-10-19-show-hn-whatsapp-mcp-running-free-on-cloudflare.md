---
title: "WhatsApp MCP 免费跑在 Cloudflare 上：让 AI Agent 读取个人聊天记录"
date: "2026-10-18 21:36:10"
tags: ["MCP", "WhatsApp", "Cloudflare", "AI Agent", "数据隐私"]
categories: "技术动态"
---

# WhatsApp MCP 免费跑在 Cloudflare 上：让 AI Agent 读取个人聊天记录

## 事件概述

Hacker News 的 Show HN 板块出现了一个名为 **whatsapp-mcp** 的项目（作者 finereli），定位是一个**只读的 MCP Server**：把它部署在你自己的 Cloudflare 账号里，用个人 WhatsApp 账号扫码关联一次，之后任何支持 MCP 的客户端（Claude Code、Claude Desktop 等）都可以搜索和读取你的聊天记录。

作者的出发点很具体：他希望手机上的 Claude 能访问自己的 WhatsApp 消息，但能找到的方案要么要求使用 WhatsApp Business，要么需要一台真实服务器来运行 Baileys。他想在 Cloudflare 上免费跑，并且使用个人 WhatsApp 账号，于是自己写了这个项目。

帖子发布时获得 29 分、19 条评论。原文摘要还提到一个"重要特性"：它会连接你的 Google 账号，以获取 WhatsApp 联系人姓名，否则很多聊天只显示电话号码，搜索效果会变差。不过 README 的说法更精确——服务器本身**不会**连接任何联系人服务，而是把这件事交给 Agent 用它已有的联系人工具（例如 Google Contacts 或 Gmail 连接器）完成。两处表述存在细微差异，原文未进一步说明。

## 关键技术点

### 1. 链接设备模式，而非常驻在线

项目复用了 WhatsApp Web 的协议：你的手机始终是数据的"真相源"，服务器只是一个被关联的设备。它**不会一直保持与 WhatsApp 的连接**。只有在 Agent 发起请求时，以及每天一次（cron 04:00 UTC），它才会连接、收取 WhatsApp 在此期间排队给它的消息、写入自己的数据库，然后断开。手机的正常使用和通知不受影响。

这个设计同时降低了账号风险和运行成本，但也意味着数据新鲜度有上限：README 说明，每个读工具在存储副本超过十分钟时，会先从 WhatsApp 补拉一次。

### 2. 单个 Durable Object 承载全部状态

架构大致是：

- Worker（`src/index.ts`）负责路由、OAuth、登录、配对页面和 cron；
- `/mcp` 端点由 `mcp.ts` 处理，每个请求创建一个新的 `McpServer` 实例；
- 所有状态集中在一个名为 `owner` 的 Durable Object（`src/whatsapp-do.ts`）中，其中的 SQLite 同时充当 Baileys 的认证存储和消息库，并建有 FTS5 全文索引；
- Baileys 的 WebSocket 只在会话期间（配对或拉取）打开；
- Worker 本身基本无状态，只依赖一个 KV namespace 存放 OAuth token 和短期的"待登录"记录。

这种"一个 Durable Object 装下所有东西"的做法，对单用户场景是合理的简化，也天然满足了"数据不出你的 Cloudflare 账号"的承诺。

### 3. 工具集面向"可检索的个人记忆"

暴露给 Agent 的工具包括：

- `
