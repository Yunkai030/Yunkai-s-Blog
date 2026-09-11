---
title: "OpenAI 推出 ChatGPT Work 中的 Data agent，让人人都能利用数据"
date: "2026-09-10 15:00:00"
tags: ["OpenAI", "ChatGPT", "Data Agent", "数据分析", "AI Agent"]
categories: "技术动态"
---

## 事件概述

OpenAI 于 2026 年 9 月 10 日发布 ChatGPT Work 中的新 Data agent。该产品旨在帮助更多员工自行回答业务问题，连接公司数据，调查数据变化，并构建可分享的交互式仪表板，而无需编写查询或学习新的分析工具。用户可以直接在对话中指导和优化分析过程。

## 关键技术点

- **多源数据连接**：Data agent 可连接已批准的数据源，包括 Amazon Redshift、Datadog、Google BigQuery、ClickHouse、Databricks、MongoDB、Snowflake 等，还能将 Google Drive 和 SharePoint 中的文件与文档纳入分析。
- **业务上下文理解**：它利用组织的业务术语、指标定义、自定义计算和数据关系来解释数据。这些上下文来自语义层和可信来源，例如 Databricks Genie Ontology、dbt、GitHub、Snowflake Horizon 以及 BI 仪表板。
- **权限与治理**：企业管理员选择可用的数据连接以及哪些角色可以使用。查询会强制执行所连接账户的现有权限，包括表、行和列级别的限制。
- **分析与可视化**：用户可追问以调查结果并审查每项发现背后的证据；可将分析转化为带内置可视化的交互式仪表板，团队能编辑、分享和刷新。还可分享品牌指南以定制输出风格。
- **BI 工具集成**：Data agent 能在 Omni、Oracle BI、Power BI、Sigma、Tableau、ThoughtSpot 中构建和交互仪表板，用自然语言在团队现有工具中指导工作。
- **行动闭环**：可要求 ChatGPT Work 推荐下一步并识别需要参与的人员，通过 Slack 或电子邮件分享发现，并通过连接的工具执行用户批准的操作。
- **内部实践**：OpenAI 几乎全部产品团队和超过三分之二的 GTM 组织使用 ChatGPT Work 中的数据代理自行分析公司数据。其数据团队创建了共享业务定义、访问规则，并为敏感数据设置了保护措施。
- **客户案例**：NTT Data、Thermo Fisher、ServicePiston 等 Alpha 计划组织正在使用该功能分析销售与支出、发现报告错误、决定追求哪些机会以及如何配备人员。原文未说明更广泛的可用性、定价或具体模型细节。

## 对数据科学或 AI Agent 落地的意义

Data agent 代表了 AI Agent 在企业数据分析场景中的典型落地路径：以自然语言为交互界面，以语义层和治理框架为信任基础，以现有 BI 工具为交付载体，最终形成从洞察到行动的闭环。它显著降低了业务人员获取数据洞察的门槛，让数据分析不再是少数专家的专属。对于数据科学团队而言，这意味着角色可能进一步分化：一部分人专注于构建和维护语义层、指标定义与数据治理，另一部分人则利用 Data agent 加速探索和交付。同时，权限继承和审计能力是企业级 Agent 能否被采纳的关键，Data agent 对这些方面的强调为行业提供了参考。

## 我的技术点评

OpenAI 这次发布的 Data agent 并没有追求“替代 BI 工具”，而是选择与 Tableau、Power BI、Sigma 等深度集成，把自然语言能力嵌入既有工作流。这种策略很务实：企业数据的信任建立在语义层和权限体系之上，LLM 只有接入这些上下文才能给出可靠答案。值得注意的几个设计——权限继承、证据审查、品牌定制、行动闭环——都直指企业落地的核心障碍。不过，语义层的维护成本、跨源数据关系的准确性、以及 LLM 在复杂分析中的幻觉风险，仍是需要持续观察的挑战。原文未说明底层模型、具体延迟或成本，但从 OpenAI 内部的高使用率来看，该产品已具备一定的成熟度。对于正在探索 AI Agent 落地的团队，这个案例提醒我们：Agent 的价值不仅在于“能回答”，更在于“在正确的上下文和权限下，把回答变成可执行的行动”。

## 原文链接

[Now everyone can put data to work - OpenAI](https://openai.com/index/put-data-to-work)
