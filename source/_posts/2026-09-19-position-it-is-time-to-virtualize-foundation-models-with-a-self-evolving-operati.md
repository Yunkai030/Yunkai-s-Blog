---
title: "基础模型需要操作系统：FMOS 自进化系统层立场论文解读"
date: "2026-09-18 04:00:00"
tags: ["AI", "Agent", "基础模型", "操作系统", "arXiv"]
categories: "技术动态"
---

## 论文概述

arXiv 上新出现一篇立场论文《Position: It is Time to Virtualize Foundation Models with a Self-evolving Operating System Layer》。据 arXiv 页面，该文提交于 2026 年 9 月 16 日，作者包括 Suparna Bhattacharya、Tarun Kumar 等共 10 人，文章被列为 ICML 2026 Position Paper Track。原始信息给出的发布时间为 2026-09-18 04:00:00。

论文的核心主张是：AI 应用已经从单一、单体式的基础模型（Foundation Model, FM）转向复合式 agentic 系统，但当前的技术栈仍然高度碎片化。即使 MCP、A2A 等协议在工具与 Agent 连接层面提供了便利，每个框架仍然内嵌了一套隐式运行时，用来处理状态、记忆、预算与护栏，导致行为不可移植、治理脆弱。作者将这一状态类比为操作系统出现之前的计算阶段：每个程序都要重新实现基本服务。

为此，论文提出领域需要一个 **Foundation Model Operating System（FMOS）**，也就是一个系统层，用来虚拟化 FM 交互。它的类比对象是虚拟机对物理硬件的抽象：应用层可以获得“专用、可信赖的 FM 实例”的幻象，并具备实际上无界的能力。FMOS 内部负责跨记忆层级编排知识、模型选择与资源分配，以及验证和政策执行。进一步地，它类似人脑在快速直觉与慢速审慎之间的切换，学习何时干预、何时让推理直接进行，并基于运行经验持续调整策略。

## 关键技术点

1. **问题诊断：复合 Agent 系统缺一层运行时抽象**
   论文指出，当前 AI 栈的碎片化体现在：每个框架都自行实现
