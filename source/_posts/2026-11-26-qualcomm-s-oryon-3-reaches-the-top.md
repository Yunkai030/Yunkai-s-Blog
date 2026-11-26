---
title: "Qualcomm Oryon 3 登顶：Snapdragon X2 Elite 的 CPU 架构剖析"
date: "2026-11-26 03:43:24"
tags: ["Qualcomm", "Oryon", "CPU架构", "Arm", "芯片设计"]
categories: "技术动态"
---

# Qualcomm Oryon 3 登顶：Snapdragon X2 Elite 的 CPU 架构剖析

## 事件/产品概述

Qualcomm 的笔记本之路并非一帆风顺。早期基于 Arm 的笔记本产品直接使用手机 SoC，性能表现甚至明显落后于低端 Intel 芯片。但 Qualcomm 显然把 PC 市场当成一场马拉松，而不是短跑：通过推出面向笔记本的高性能 Snapdragon 变体，一代代积累竞争力。到了 Snapdragon X2 Elite Extreme，其 CPU 性能已经可以挑战 x86-64 阵营的顶尖产品。

支撑这一表现的核心，是 Qualcomm 第三代自研 Oryon 架构，作者 Chester Lam 简称为 Oryon 3。Snapdragon X2 Elite 同时部署了 Oryon 3 的 E-Core 和 P-Core 变体，Qualcomm 分别将其称为 “performance” 和 “prime” 核。P-Core 是绝对主角：它不仅提供最高单线程性能，还承担了大部分多线程吞吐。原因在于 Qualcomm 的 P-Core 数量是 E-Core 的两倍，形成了一种与 Intel 相反的反向混合策略。也正因如此，Oryon 3 的 P-Core 变体扛起了 Qualcomm 进军 PC 市场的主要压力。

值得注意的是，Oryon 3 在架构上与第一代 Oryon 高度相似。Qualcomm 实际上有第二代 Oryon，但只用于手机；其官网也暗示第二代相对第一代只是很小的改动。因此，作者把第一代 Oryon 视为 Oryon 3 的直接前代。

## 关键技术点

### 继承自 Oryon 1 的宽核基础

Oryon 3 从 Oryon 1 继承了超过 600 个 micro-ops 的乱序执行窗口，以及一套强调速度而非容量的两级缓存结构。这套底子放在 2026 年的高性能设计中依然不算落伍。

相比前代，Oryon 3 的升级主要集中在以下几个方面：

- **频率提升到 5 GHz**：相比 Oryon 1 的 4.3 GHz 提升了 16%，仅这一项就足以带来代际性能增益。
- **核心宽度从 8 micro-ops 提升到 9 micro-ops**：前端相应增加了一个解码槽。
- **支持 SVE2 和 SME**：跟上 aarch64 架构演进，为软件优化打开新空间。

在定位上，Oryon 3 面对的是 AMD Zen 5、Intel Lion
