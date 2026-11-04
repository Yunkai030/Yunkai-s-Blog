---
title: "当检索变成 Agent 基础设施：RAGFlow 团队谈知识编译与最小充分上下文"
date: "2026-11-03 05:00:00"
tags: ["AI Agent", "RAG", "知识编译", "RAGFlow", "信息检索"]
categories: "技术动态"
---

## 事件/论文概述

arXiv 新论文 **《Context as Infrastructure: Knowledge Compilation for Retrieval in Agentic Systems with Harnesses》**（arXiv:2610.41172）把 Agentic RAG 的讨论从“更好的检索器”推进到“更好的上下文供给层”。论文由 Zhichang Yu、Baining Cao 等 18 位作者完成，提交于 2026 年 10 月 30 日，主分类为 cs.IR，交叉 cs.AI 与 cs.CL，共 13 页、2 张图。

文章的核心判断是：检索增强生成正在 Agent 化。一个搜索 harness 会自己写 query、读结果、改写 query，并决定何时停止。作者在实验中仅使用 BM25/grep 与 MiniMax M3，不使用编译索引或向量索引，就在 BrowseComp-Plus 上达到 85%、在多跳 FRAMES 上达到 91%。这说明“准确率”问题在很大程度上可以被一个有能力的 harness 解决，但同时也暴露了新的瓶颈：**上下文问题**。不受约束的循环会重复查询、反复阅读文档，并把大量未使用段落塞进上下文窗口。

论文提出的缺失层是 **knowledge compilation（知识编译）**：一个可配置的摄取流水线，由 LLM 为文档补充单个 chunk 无法独立承载的上下文，包括带 claim-evidence 叶子的导航层级、实体图、时间线、思维导图、本体、wiki 和 memory。作者强调，知识编译不是“更强的 retriever”，而是一个 **supply layer（供给层）**。他们描述了 RAGFlow 的 pipeline 与 harness，相关代码已开源于 GitHub。

## 关键技术点

### 1. Harness 解决准确率，但放大上下文浪费

论文把 Agentic RAG 的搜索过程描述为一个由 harness 驱动的循环：写 query、读结果、重写 query、判断是否停止。作者的实验表明，在 harness 足够称职时，仅靠 BM25/grep 和 MiniMax M3 就能在 BrowseComp-Plus 与 FRAMES 上取得较高准确率，无需编译索引或向量索引。

但问题也随之而来：如果没有纪律，循环会重复查询、重复阅读文档，并把未使用的 passage 填入上下文窗口。也就是说，**准确率提升并不等于上下文效率提升**，Agent 的 token 预算和延迟可能被低质量循环消耗掉。

### 2. 知识编译是“供给层”，不是“检索器替代品”

论文将知识编译定义为一个可配置的 ingestion pipeline：LLM 在文档入库时补充结构化上下文。原文列出的 artifacts 包括：

- 带 claim-evidence 叶子的导航层级；
- 实体图；
- 时间线；
- 思维导图；
- 本体；
- wiki；
- memory。

这里的关键词是“单个 chunk 不包含的上下文”。传统 RAG 往往把文档切块后做相似度检索，而知识编译试图在入库阶段就把文档组织成可供 Agent 导航的结构。

不过，作者并没有宣称这些结构一定能提升准确率。原文明确指出：在一个称职的 harness 下，结构化 artifacts 在 FRAMES 上没有带来可检测的准确率增益；PageIndex 风格的大纲在规模扩大时还出现了退化。因此，知识编译的定位不是“更好的 retriever”，而是“更好的上下文供给”。

### 3. 导航树与 claim-evidence 叶子：条件性 token 节省

论文重点测量了一种机制：叶子节点为 claim-evidence 对的导航树。实验结果显示：

- 当证据充分时，查询 token 减少 **91%**；
- 当证据不充分时，查询 token 反而增加 **1.9%**；
- 平均减少 **38%**；
- 这对应约 **2%** 的盈亏平衡充分率，而实测充分率接近 **43%
