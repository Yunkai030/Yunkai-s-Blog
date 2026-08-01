---
title: "Morph (YC S23) 招聘技术专家：面向 Coding Agent 的推理优化"
date: "2026-08-01 22:52:44"
tags: ["AI", "Agent", "推理优化", "招聘", "YC"]
categories: "技术动态"
---

## 事件概述

Morph（Y Combinator S23 批次）于 2026 年 8 月通过 Hacker News 发布了一则招聘信息，职位为 **Member of Technical Staff**。Morph 专注于构建“面向 Coding Agent 优化的快速模型”，其核心方向是研发专门用于代码生成的模型，并基于自研推理栈提供服务。该职位位于旧金山，全职，要求 6 年以上经验，薪资范围在 $175K–$350K，另加 0.40% 股权。岗位属于工程与机器学习交叉领域，且明确要求美国公民或持有有效签证。

值得注意的是，招聘信息中提到了“PD disaggregation research”（即 Prefill-Decode 分离研究），这是当前大模型推理优化中的热门方向，但原文并未详细展开其具体实现或研究目标。

## 关键技术点

根据招聘描述，Morph 的推理基础设施覆盖了从底层 kernel 到模型服务、路由、自动扩缩容和容量管理的完整技术栈。岗位职责聚焦于性能工程，具体包括：

- **定位理论硬件性能与生产性能之间的差距**：通过剖析从 API 层到单个 kernel 的延迟和吞吐量退化，找到性能瓶颈。
- **优化多个关键环节**：包括批处理（batching）、调度（scheduling）、路由（routing）、量化（quantization）和分布式执行（distributed execution）。
- **构建基准测试与可观测性工具**：让瓶颈变得“显而易见”，并为每次优化验证模型质量和正确性。
- **进行“PD disaggregation”研究**：招聘信息中明确列出了这一研究方向，通常涉及将预填充（Prefill）和解码（Decode）阶段分离到不同资源上，以提升推理效率，但原文未说明具体方案。

理想的候选人需要在推理栈的多个环节具备 Top 1% 的能力，熟悉 GPU 性能、内存带宽、集合通信（collectives）和推理服务，并精通 Python。Morph 特别强调“tokens per second、tokens per dollar 和 correctness”三者同样重要，这表明他们追求的是综合效率而非单一指标。

另外，面试流程包含 **2 天工作试用（work trial）**，这意味着候选人会在真实项目中接受检验，而不仅仅是算法题或系统设计面试。

## 对数据科学和 AI Agent 落地的意义

Morph 的定位非常明确：为 **Coding Agent** 提供极致的推理性能。在 AI Agent 落地过程中，尤其是代码生成、自动编程等场景，推理延迟和成本直接决定了产品的可用性和商业可行性。一个轻量但极快的模型，配合专门优化的推理栈，可以显著降低 Agent 的响应时间，提升用户体验。

“Fast Models Optimized for Coding Agents”这一口号暗示了模型与服务栈的协同设计。不是简单地使用现成的大模型，而是针对代码生成这一特定任务训练专用模型，并为其量身定制推理系统。这种“模型+系统”联合优化的思路，是 Agent 从演示走向规模化生产的关键路径之一。

此外，“PD disaggregation”如果成熟，将有助于更灵活地调度计算资源，降低大模型服务的成本。对于数据科学团队而言，这意味着未来可以以更低的成本、更高的吞吐量运行复杂的 Agent 工作流，进而推动更多实验和产品创新。

## 我的技术点评

从招聘信息可以看出，Morph 正在做一件极其硬核的事情：**从 kernel 到路由全栈自研，只为让 Coding Agent 更快、更便宜**。这种深度优化的文化在 AI 基础设施公司中并不常见，大多数团队会依赖现成的推理框架如 vLLM 或 TensorRT-LLM。Morph 选择自建，说明他们可能在现有框架无法满足需求，或者看到了别人看不到的性能空间。

我注意到职位要求中有一条：“Find the gap between theoretical hardware performance and production performance”——这句话揭示了大多数推理系统的真实痛点：GPU 理论上能跑多少 FLOPs，实际生产往往只能达到一小部分。这种差距来自调度、内存、通信、内核实现等多个层面的开销。能系统性缩小这一差距的人才，必然是各大 AI 基础设施公司争抢的对象。

另外，“2 天工作试用”这种面试形式值得点赞。性能优化是一项非常依赖动手能力和直觉的工作，传统面试很难衡量候选人是否真的能在复杂的推理栈中快速定位问题并落地优化。实际工作考察远比几轮对话更有效。

不过，招聘信息中也存在一些模糊之处，比如“PD disaggregation research”具体指什么、Morph 的“custom speculative-decoding models”如何与推理栈协同等，原文均未展开说明。对于关注该公司的技术人来说，这可能需要在投递或面试中进一步了解。

总体而言，Morph 作为一家 2025 年成立、仅 3 人的初创公司，专注于 Coding Agent 的模型与推理优化，方向非常聚焦，且创始团队直接参与，这会是一个极具技术挑战和影响力的岗位。

## 原文链接

原始招聘信息发布于 Y Combinator 平台：  
[https://www.ycombinator.com/companies/morph/jobs/0Z8vI3K-member-of-technical-staff](https://www.ycombinator.com/companies/morph/jobs/0Z8vI3K-member-of-technical-staff)  
Hacker News 讨论帖：  
[https://news.ycombinator.com/item?id=49139352](https://news.ycombinator.com/item?id=49139352)
