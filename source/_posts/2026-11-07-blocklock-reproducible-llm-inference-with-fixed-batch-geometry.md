---
title: "BlockLock：用固定批次几何实现可复现的 LLM 推理"
date: "2026-11-06 05:00:00"
tags: ["LLM 推理", "可复现性", "批处理", "vLLM", "AI Agent"]
categories: "技术动态"
---

## 事件/论文概述

arXiv 新论文《BlockLock: Reproducible LLM Inference with Fixed Batch Geometry》关注大模型推理中的一个实际问题：**同一请求在不同 batch 组合下能否产生完全一致的输出**。论文作者为 Xiuyuan Qi、Pedro Reviriego、Javier Conde、Shanshan Liu。

论文指出，现有方案各有代价：batch-invariant kernels 会约束每一个算子；而将 prefill 隔离、decode 使用固定形状的 CoRun-style baseline，则会放弃共享 prefill 计算，并对 decode 进行 padding。BlockLock 的目标是保留共享的 batched prefill，只固定“被保护请求”所看到的数值路径，从而在 companions 变化时仍保持目标请求输出一致。

BlockLock 提供两种模式：

- **BlockLock-Rows**：使用固定宽度行，并保留所有请求的 batched decode。
- **BlockLock-Pack**：使用 terminal-anchored packing 和隔离的 dummy segment，然后提取被保护请求的 KV state，用于 target-only decode。

论文称，在给定的 per-deployment contract 下，两种模式都能在 companions 变化时逐比特保持目标请求的输出。实验覆盖五个 dense 模型：Qwen3-8B/14B、Llama-3.1-8B-Instruct、Gemma-3-4B/12B-IT；三个单 GPU 部署：NVIDIA A6000、A100、H100；评测集包括 tinyBenchmarks 和 BFCL，并包含两块 NVIDIA A6000 上的初始 tensor-parallel 实验。报告结果显示，两种模式在测试中均保持目标序列和 Top20-logit bits 一致。

在交付相同工作量的条件下，BlockLock-Rows 相对 vLLM Batch-Invariant 将延迟降低 53.5%–55.0%，吞吐提升 115.2%–122.2%。论文还强调，相比 batch-invariant kernels，它不需要自定义 kernel 实现，并且只约束被保护的请求。

## 关键技术点

**1. 可复现性问题的核心是批次几何**

LLM serving 通常会把多个请求动态合批。一个请求的输出可能因为同批次其他请求的长度、padding、kernel 形状和数值归约路径变化而发生细微差异。BlockLock 的思路是，不要求整个 batch 对所有请求都 batch-invariant，而是固定被保护请求所看到的“几何形状”，让它的数值路径不受 companions 影响。

**2. 只保护目标请求，而不是约束所有算子**

论文将 BlockLock 与两类方案对比：一类是全局约束算子的 batch-invariant kernels；另一类是隔离 prefill、固定形状 decode 的 CoRun-style baseline。BlockLock 选择保留共享 batched prefill，只 pin 住被保护请求的数值路径。这种“选择性可复现”是其工程价值所在。

**3. 两种实现模式**

BlockLock-Rows 使用固定宽度 rows，同时保留所有请求的 batched decode，因此更接近常规高吞吐 serving 路径。BlockLock-Pack 则采用 terminal-anchored packing 和隔离 dummy segment，再提取被保护请求的 KV state，转为 target-only decode。论文称两种模式在报告测试中都能保持目标序列与 Top20-logit bits 一致。关于 per-deployment contract 的具体条款，原文未说明。

**4. 实验与性能数字**

论文在五种 dense 模型、三种单 GPU 部署以及 tinyBenchmarks、BFCL 上评测，并补充了两块 A6000 的初始 tensor-parallel 实验。性能方面，论文给出的对比对象是 vLLM Batch-Invariant；在相同 delivered work 下，BlockLock-Rows 延迟降低 53.5%–55.0%，吞吐提升 115.2%–122.2%。原文未给出 BlockLock-Pack 对应的延迟和吞吐数字，也未说明大规模多卡或多节点下的完整结果。

## 对数据科学或 AI Agent 落地的意义

对数据科学和 AI Agent 系统来说，可复现推理的价值不只是“结果好看”。在评测、审计、回归测试和故障复现中，同一个请求如果因为并发 batch 组合变化而输出不同，会显著增加问题定位成本。BlockLock 提出的“只保护关键请求”的思路，适合需要稳定 trace 的场景，例如线上问题回放、评测集复跑、关键业务请求的审计记录，以及 Agent 工具调用链的回归验证。

对 AI Agent 落地而言，稳定输出有助于让同一任务在并发 serving 环境下保持可比较的轨迹。不过需要注意，论文验证的是目标序列和 Top20-logit bits 的一致性，并未说明端到端 Agent 任务成功率、工具调用准确率等指标的变化。原文也未说明该方案在跨 GPU 型号、跨驱动版本或跨部署环境下的可复现性边界。

## 我的技术点评

BlockLock 的亮点在于把“可复现推理”从全局约束改写为**选择性数值路径固定**。这避免了 batch-invariant kernels 对每个算子的普遍约束，也避免了 CoRun-style baseline 放弃共享 prefill 计算的问题。对于真实 serving 系统，这种设计更接近可落地的折中：既保留 batched prefill 的吞吐优势，又只对被保护请求付出额外约束成本。

从论文摘要看，BlockLock-Rows 的性能数字比较有吸引力，而且不需要自定义 kernel 实现，这会降低工程迁移门槛。但仍有几个问题值得后续关注：第一，per-deployment contract 的具体内容和适用边界，原文未说明；第二，BlockLock-Pack 的额外开销、显存占用和
