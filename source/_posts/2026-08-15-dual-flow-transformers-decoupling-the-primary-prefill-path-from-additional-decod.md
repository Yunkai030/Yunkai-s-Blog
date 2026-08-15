---
title: "Dual-Flow Transformers：将 Prefill 与 Decode 的计算路径解耦，是否重新定义了大模型推理的效率边界？"
date: "2026-08-15 04:00:00"
tags: ["AI", "Data Science", "LLM", "MoE", "Transformer"]
categories: "技术动态"
---

# Dual-Flow Transformers：将 Prefill 与 Decode 的计算路径解耦，是否重新定义了大模型推理的效率边界？

## 论文概述

随着大语言模型（LLM）从训练走向大规模服务，**累积推理成本**正在成为一个比一次性训练成本更值得关注的指标。论文 `arXiv:2608.12385` 指出，推理的两个阶段对硬件的压力截然不同：

- **Prompt Prefill（提示预填充）**：高度并行，通常受计算量（compute-bound）限制。
- **Autoregressive Decode（自回归解码）**：逐 token 生成，顺序执行，通常受内存带宽（memory-bandwidth-bound）限制。

然而，传统的模型规模扩展（加宽或加深）会同时增加两个阶段的成本——因为每一层在 prefill 和 decode 中都必须被完整计算。这种“绑定”关系意味着，如果我们只想增强模型生成下一个 token 的能力，也不得不付出双倍的计算代价。

由 Liming Liu、Mingze Wang 和 Tuo Zhao 提出的 **Dual-Flow Transformer** 试图回答一个核心问题：

> 能否将新增的学习计算量，专门分配到“续写预测（continuation prediction）”上，同时保留 prompt 的全局主计算和一套持续的 KV 缓存？

## 关键技术点

### 1. 双流架构：Primary Flow 与 Auxiliary Flow

Dual-Flow Transformer 的核心是引入两条计算路径：

- **Primary Flow（主流程）**：一个完整的因果语言模型，负责处理 prompt 并写入 KV 缓存。它在行为上与传统 Transformer 完全一致。
- **Auxiliary Flow（辅助流程）**：在 prompt 处理阶段完全省略，只从最终 prompt 位置之后开始激活，专门为续写预测增加计算深度。

关键之处在于：Auxiliary Flow **不写入任何持久状态（persistent state）**，也**不影响 Primary Flow 的计算路径**。它是叠加在 decode 阶段上的一层额外计算。

### 2. 共享权重与轻量耦合

两条流共享主要的 attention、MLP 和输出矩阵，但使用**独立的 token embeddings** 和**轻量耦合机制**。

这种设计带来的直接好处是：

- 参数总量增加有限；
- 共享权重和主 KV 缓存使得**分组执行（grouped execution）**期间可以重用已加载的权重和缓存的键值对，从而提高硬件利用率。

### 3. MoE 场景下的独立控制

论文另一个重要贡献集中在混合专家模型（MoE）上。

在 Dual-Flow Transformer 中，主、辅流的**专家 fan-out 可以独立设置**。这意味着：

- Prompt 成本由 Primary Flow 的专家数控制；
- 续写成本由 Auxiliary Flow 的专家数控制；
- 预测质量受两者共同影响。

论文研究了两种控制方式：

1. 在固定 prefill 专家计算的情况下，**增加** decode 计算量；
2. 在固定 decode 专家预算下，**重新分配**主辅两流的专家数量。

实验结果揭示了一个 **prefill-decode-quality 权衡**，并展示了按阶段分配专家资源的潜力。

## 对数据科学 / AI Agent 落地的意义

### 1. 推理成本的“精细化控制”

对于数据科学团队而言，LLM 的推理成本往往是一个不透明的“黑盒”。Dual-Flow Transformer 的提出意味着：我们有可能在保持 prompt 理解能力不变的前提下，精准地按需扩展生成能力。这在成本模型和资源规划层面提供了更细粒度的控制选项。

### 2. 对 Agent 场景尤其重要

AI Agent 的典型工作负载是“短 Prompt、长生成、多轮调用”。每一轮 agent 推理都包括一次 prefill 和多次 decode：

- prefill 阶段处理工具调用结果、历史上下文；
- decode 阶段逐步生成动作或回复。

Agent 场景中 decode 的占比通常远高于传统 QA。如果 Dual-Flow 能够在 decode 阶段引入额外的计算而不增加 prefill 开销，那么对于高频调用的 agent 服务，整体吞吐和时延都有潜在的优化空间。

### 3. KV 缓存友好

Auxiliary Flow 不写持久状态，也不影响主缓存，降低了多轮对话和 agent 长期运行时的显存压力。若与共享权重结合，在批处理（grouped execution）中可以更好地复用内存中的数据，这对生产环境部署是很现实的收益。

## 我的技术点评

### 值得肯定的方向

**“按阶段分配计算”** 是一个很优雅的想法。传统上我们考虑模型扩展时，维度往往是宽度（width）和深度（depth），但都逃不出 prefill 和 decode 的同步增长。Dual-Flow 把问题重新定义为一个 **资源分配问题**——不再问“模型多大”，而是问“两个阶段各需要多少计算”。这种思路更贴近真实的服务成本结构。

在 MoE 中独立控制主辅流的 fan-out，非常符合直觉：MoE 本身就是为了在容量和计算之间做权衡，Dual-Flow 把这个权衡从“整个模型”细化到“推理阶段”，是一个自然且有力的延伸。

### 需要保持审慎的地方

- **论文目前只报告了 validation loss 的改善**。原文未说明端到端延迟、吞吐量或显存占用的真实数字。共享权重和缓存重用确实有硬件利用率的理论优势，但这些优势是否能在实际服务中抵消双流带来的调度和实现复杂度，还需要更深入的基准测试。
- **“Auxiliary Flow 不从 prompt 位置开始”意味着什么？** 如果辅助流只从最后位置激活，它的输入表示从一开始就不包含逐步累积的深层上下文特征。论文提到使用单独的 token embeddings 和轻量耦合，但具体的交互机制和初始化策略原文未详细说明。
- **训练稳定性和微调成本未提及**。双流架构在预训练阶段的优化难度、与现有训练框架（如 Megatron、DeepSpeed）的兼容性，以及后续指令微调时的行为变化，都是实际落地前需要验证的环节。
- 论文标注为 18 页，提交于 2026 年 7 月 31 日。目前尚不清楚是否有配套的开源代码或实验配置——原页面在 `Code, Data, Media` 部分没有列出可见的仓库链接。

### 与现有工作的对比空白

论文对“宽度/深度扩展会同时增加两阶段计算”的论述是准确的，但双流结构在直觉上与以下方向存在交集，原文未作详细对比：

- **Early-exit / 分层推理**：只在 decode 阶段增加层数，与 early-exit 在某些层面上有互补关系；
- **Speculative Decoding（推测解码）**：同样是为了加速 decode，但核心机制是多个 token 并行预测，与 Dual-Flow 的优化目标不同；
- **MoE 的动态路由**：phase-specific expert allocation 是否与“按 token 难度路由”存在叠加效果，值得进一步探索。

## 结论

Dual-Flow Transformer 为大模型推理提供了一种**阶段解耦的架构视角**，在理论上让模型设计者第一次拥有对 prefill 和 decode 计算量的独立旋钮。对于 AI Agent 这类“短提示、长生成、高频调用”的场景，它的潜在价值是很明确的。

不过，当前证据主要停留在验证损失层面。是否能够转化为实际部署中的吞吐提升和成本下降，仍需更多硬件实测数据。如果后续有开源实现和下游任务评测，这很可能是推理优化领域一只有力的潜力股。

> 原文链接：[https://arxiv.org/abs/2608.12385](https://arxiv.org/abs/2608.12385)
> 论文标题：Dual-Flow Transformers: Decoupling the Primary Prefill Path from Additional Decode Computation
> 作者：Liming Liu, Mingze Wang, Tuo Zhao | 提交时间：v1, 2026-07-31 | 所属领域：cs.AI
