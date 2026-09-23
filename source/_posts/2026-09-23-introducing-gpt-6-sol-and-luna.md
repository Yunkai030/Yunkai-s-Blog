---
title: "OpenAI 发布 GPT-6 Sol 与 Luna：把前沿智能压到成本曲线上"
date: "2026-09-22 18:00:00"
tags: ["OpenAI", "GPT-6", "AI Agent", "大模型成本", "基准测试"]
categories: "技术动态"
---

## 事件概述

OpenAI 于 2026 年 9 月 22 日发布 GPT-6 Sol 和 GPT-6 Luna 两款新模型，定位是在 GPT-6 Astra 之外提供"能力与成本不同配比"的选择。官方表述很明确：Astra 依然是最智能、对齐最好的模型，用于最苛刻的项目；Sol 和 Luna 的目标是把 Astra 背后的那代智能"分发"出去，路径是压低成本。

按原文说法，两款模型使用了与 Astra 相似的方法训练，把 Astra 在专业工作、事实性、编码、计算机使用和对齐方面的进展，带到了更快、更便宜的模型上。同时，OpenAI 将 Sol 和 Luna 的 API 价格相比其 GPT-5.6 促销定价下调 50%，并称这来自缓存与推理效率的提升，节省被直接传导给了用户。

需要说明的是，原文未披露两款模型的参数规模、上下文长度、模态支持范围、具体训练数据或架构细节，也未说明除 API 之外的分发渠道与上线时间。

## 关键技术点

### 价格与成本结构

价格以每百万 token 计：

| 模型 | 输入 | 输出 | 降幅 |
| --- | --- | --- | --- |
| GPT-5.6 Sol → GPT-6 Sol | $4 → $2 | $20 → $10 | 官方标注 50% |
| GPT-5.6 Luna → GPT-6 Luna | $0.20 → $0.10 | $1.20 → $0.50 | 官方标注 50% |

一个值得注意的细节：Luna 的输入单价正好减半，但输出单价从 $1.20 降到 $0.50，实际降幅约 58%。原文统一标注为 "50% cheaper"，未说明这一口径差异的原因，可能是取整或综合口径，原文未说明。

### 专业工作与 Agent 基准

OpenAI 主要引用了 AutomationBench 和 Agents' Last Exam 两组评测。AutomationBench 1.0.6 测试 AI Agent 在销售、市场、运营、支持、财务、HR 六类场景中使用 47 个工具完成端到端工作流的能力。原文给出的一组数据是：

- GPT-6 Sol（xhigh effort）得分 33.2%，每任务成本 $0.27；
- GPT-6 Astra（low effort）得分 30.3%，成本为 Sol 的 3.9 倍；
- Claude Opus 5（max effort）得分 26.9%，成本为 11.1 倍；
- Claude Fable 5.1（含 Opus 5 fallback，max effort）得分 31.4%，成本超过 8.9 倍。

原文表格中成本一列的基准未逐项说明，从数值关系看应是以 GPT-6 Sol（xhigh）的 $0.27/任务为参照的相对倍数，但原文未明确确认。OpenAI 还特别指出，Fable 5.1 的数据低估了其真实成本，因为约 40% 的任务触发了 Opus 5 fallback，而 fallback 成本未计入。

在 Agents' Last Exam V1 上，该评测覆盖 55 个子行业的长周期、有经济价值的专业任务，GPT-6 Sol（max effort）得分 56.4%，高于 Claude Opus 5 在该评测中的最高分，同时每任务成本低 60%。

### 事实性

事实性评测使用的是去标识化的真实对话，这些对话中用户曾标记过模型的 factual error。原文称 GPT-6 Sol 的错误量约为前代的一半，在低得多的成本下接近 Astra 的可靠性水平；GPT-6 Luna 在高 effort 下与 GPT-5.6 Sol 相当，成本约为其百分之一。OpenAI 同时提示，这批由错误触发的对话并不代表典型使用分布（典型场景中事实错误更罕见），且分数未按长度做控制，但其 verbosity 扫描显示答案长度几乎不影响结果。

### 编码

编码部分引用了 FrontierCode 1.1 Main 和 DeepSWE v1.1。前者不仅评正确性，还评"可合并性"，包括测试质量、改动范围纪律、代码风格和对代码库规范的遵循。原文称 GPT-6 Sol 相比 GPT-5.6 Sol 有实质性提升，并能以低得多的成本匹配 Claude Fable 5.1 xhigh。

DeepSWE v1.1 测试真实代码库中的复杂软件工程任务：GPT-6 Sol（max effort）得分 68.8%，与 Claude Fable 5 的最高分 69.9%（xhigh）相差 1.1 个百分点，每任务成本低约 80%；GPT-6 Luna（max effort）得分 66.6%，与 Claude Opus 5、Fable 5 的中等 effort 相当，且每任务成本比 Opus 5 低 93%、比 Fable 5 低 96%。

OpenAI 还披露了一个内部数据点：按 API 价格折算，OpenAI 内部研究员每日 token 消耗的中位数已超过 $600，90 分位超过 $7,000。这是理解这轮降价动机的关键背景。

### 计算机使用与协作风格

在 OSWorld 2.0 offline（v2026.08.08 版本的 offline 集，报告部分奖励）上
