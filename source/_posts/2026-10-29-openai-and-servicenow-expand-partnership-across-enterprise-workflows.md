---
title: "OpenAI 与 ServiceNow 扩大合作：把 Agent 嵌入企业工作流，把工作流接进 ChatGPT 和 Codex"
date: "2026-10-28 13:15:00"
tags: ["AI", "Agent", "Enterprise", "ServiceNow", "OpenAI"]
categories: "技术动态"
---

## 事件概述

2026 年 10 月 28 日，OpenAI 在官网宣布与 ServiceNow 扩大合作。双方的目标可以概括为双向打通：

- **把 OpenAI 的模型与 Agent 带进 ServiceNow 产品**，覆盖从应用开发到网络安全的多个环节；
- **把 ServiceNow 的工作流接入 ChatGPT 和 Codex**，让企业员工在对话界面里直接推进业务流程。

这次扩展建立在双方今年 1 月宣布的合作基础之上。按照 OpenAI 的说法，新阶段会让 OpenAI 的能力渗透到 ServiceNow 为客户提供的更多工作中，也进入 ServiceNow 自身的业务运营。

从公开信息看，这次合作不是简单的“模型调用 API”式集成，而是围绕**业务上下文、权限规则和可执行动作**做深度融合——这一点是理解整个公告的关键。

## 关键技术点

### 1. ChatGPT 中的 ServiceNow 集成与 Action Fabric

公告提到的第一个落地形态是一个新的 ServiceNow 集成：把业务上下文和工作流动作直接带进 ChatGPT，让团队在同一段对话里既完成问题排查，又执行下一步操作。

原文给出的典型场景是 IT 团队：
- 查找相似事件（incident）；
- 评估某项变更的风险；
- 更新 ServiceNow 记录。

这三个动作过去分散在工单系统、变更管理模块和聊天工具之间，现在被压缩进一次会话。值得注意的是权限机制：客户将自己的 ServiceNow 实例连接到 ChatGPT，并**自行选择开放哪些能力**；ServiceNow 的 **Action Fabric** 会套用企业既有的业务规则和权限，因此用户能执行的动作范围，反映的是其所在组织的配置与访问权限。

这一点在工程上很重要。企业级 Agent 的最大障碍往往不是模型能力，而是“模型能不能代表这个人在这个系统里做这件事”。Action Fabric 承担的是策略执行层（policy enforcement）的角色，把权限判断留在企业既有体系内，而不是交给模型自由决定。

### 2. ChatGPT 内的交互式体验

ServiceNow 还在 ChatGPT 内预览交互式体验。原文举的例子是 on-call 工程师：在 ChatGPT 中查看关联的监控告警、最近的变更和受影响的服务，然后指派合适的团队并推进修复。

这里体现的是**把多个数据源的上下文聚合到单一界面**，再让 Agent 基于聚合后的上下文产出“下一步动作”。原文未说明这类交互式体验的具体技术实现方式与开放时间。

### 3. 三个方向的 ServiceNow 产品增强

公告称计划在三个领域开发新能力：

**应用开发。** 计划在 ServiceNow 的 AI Workflow Factory 中集成 Codex，借助 ServiceNow 的业务上下文与平台能力帮助开发者构建应用。同时，OpenAI 模型将为 **Build Agent** 和 **Autonomous Engineer** 提供支持，用于应用开发与现代化改造。

**网络安全。** 一个联合安全方案，将 OpenAI 的网络安全能力与 ServiceNow 的资产、身份和业务上下文结合，帮助团队调查漏洞、排定风险优先级并协调修复。

**语音。** 在 ServiceNow 的 Super Intelligence Control Tower 中提供一个由 OpenAI 驱动的体验：用户口述一个 AI 用例，系统帮助填充评估字段，并通过追问补全缺失信息。

语音这一项在形态上比较特别——它不是“用语音替代打字”，而是把一段模糊的需求描述转化为结构化的评估表单，本质上是一个**信息抽取加多轮澄清**的任务。

### 4. 全员铺开的 ChatGPT Work 与 Codex

ServiceNow 计划让**全体员工**（不再仅限于工程组织）使用 ChatGPT Work 和 Codex。工程师用 Codex 探索代码库、修改代码并运行测试；各业务团队在日常工作中使用 ChatGPT Work。ServiceNow 还计划把 OpenAI 能力用于内部安全工作。

反向的流动同样存在：OpenAI 表示自己也在自身运营中使用 ServiceNow 的工作流，并由 Super Intelligence Control Tower 提供支撑。这种“互为客户”的结构，在以往的企业合作公告中并不常见。

### 5. 可用时间表

原文给出的时间安排如下：

| 能力 | 时间 |
| --- | --- |
| ServiceNow MCP 插件（OpenAI marketplace） | 公告发布当日已可用 |
| MCP 插件增强能力 | 预计 2026 年底 |
| Super Intelligence Control Tower 语音能力 | 预计 2027 年 Q1 |
| OpenAI 驱动的安全能力 | 预计 2027 年 1 月 early access，2027 年 Q2 正式可用 |
| AI Workflow Factory 中的 Codex | 预计 2027 年内 |

需要注意，除已经上架的 MCP 插件外，其余均为计划中的能力，原文使用的是 “expected”“planned” 一类措辞，尚未给出确切日期。原文未说明 MCP 插件的具体协议细节与功能边界。

## 对数据科学与 AI Agent 落地的意义

**第一，Agent 的竞争重心正在从“模型能力”转向“上下文与权限的接入”。** 这次合作里最实质的部分不是模型本身，而是业务上下文（事件、变更、资产、身份）与执行权限（Action Fabric）如何被安全地暴露给模型。对于任何要做企业内部 Agent 的团队，这基本是一条绕不开的路径：模型再强，拿不到结构化上下文、不敢让它执行写操作，Agent 就只能停在“建议”层面。

**第二，企业 Agent 的产品形态可能是“嵌回原系统”，而不是“另建一个聊天框”。** 公告的两个方向恰好相反：既把 OpenAI 嵌进 ServiceNow（Build Agent、Autonomous Engineer、安全工作流），也把 ServiceNow 嵌进 ChatGPT。这说明主流厂商并不认为对话界面会取代业务系统，而是让两者在会话层交汇。这对数据产品设计的启示是：与其做一个独立的 AI 门户，不如想清楚动作应该发生在哪个界面、上下文应该来自哪个系统。

**第三，对数据科学团队的直接含义在“可观测性与评估”。** 一旦 Agent 能够更新工单、指派团队、参与修复，评估指标就不再是准确率，而是任务完成率、误操作率、权限越界次数。公告没有涉及这方面的度量方式，原文未说明双方如何评估 Agent 的表现。这恰恰是落地阶段最容易被忽略、也最容易出事的环节。

**第四，语音入口把非结构化输入纳入企业流程。** 用口述描述 AI 用例、系统追问补全字段，这类交互降低了业务人员使用门槛，但把“需求澄清”这一环节交给了模型，对抽取准确性和追问策略的要求会比较高。

## 我的技术点评

这份公告的信息密度不低，但需要区分“已交付”和“计划中”。目前真正可用的只有 OpenAI marketplace 上的 ServiceNow MCP 插件，其余核心能力的时间点普遍落在 2026 年底到 2027 年，跨度接近一年。对关注落地的团队来说，短期内最值得动手验证的就是这个 MCP 插件——它决定了“ChatGPT 能不能读到你的 ServiceNow 上下文”。

第二个值得留意的点是权限模型的位置。Action Fabric 把业务规则和权限判断留在 ServiceNow 侧，ChatGPT 侧的模型只负责决定“想做什么”，能不能做由企业配置裁决。这是目前企业 Agent 比较稳妥的分层方式，也意味着**集成的复杂度主要不在模型，而在策略层**。任何自建 Agent 的团队都应该参考这个切分：规划与执行分离，权限不下放给模型。

第三，三家（其实是两家）都在强调“信任执行”（trusted execution）这个说法。Bill McDermott 把 ServiceNow 定位为跨企业编排、保护和治理 AI 的“控制塔”。这是典型的平台叙事，实际效果取决于治理能力能否覆盖到 Codex 这类开发工具在生产环境中的行为——而公告对此语焉不详，原文未说明 Codex 在企业代码库中的具体权限边界与审计机制。这是我认为最需要在后续披露中跟进的细节。

最后，OpenAI 自己也在用 ServiceNow 工作流、ServiceNow 全员用 ChatGPT Work 和 Codex，这种双向依赖让合作更牢固，但也让“供应商中立性”成为一个现实问题。对于正在做技术选型的企业，这份公告更像是一个提醒：**AI 能力的采购决策，正在变成工作流平台的锁定决策。**

## 原文链接

- OpenAI News：<https://openai.com/index/openai-servicenow-partnership-expansion>
