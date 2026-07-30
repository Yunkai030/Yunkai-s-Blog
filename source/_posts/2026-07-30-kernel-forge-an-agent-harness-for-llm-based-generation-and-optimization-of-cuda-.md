---
title: "Kernel Forge：基于LLM的CUDA Kernel自动生成与优化Agent框架"
date: "2026-07-30 04:00:00"
tags: ["LLM", "CUDA", "Kernel Optimization", "Agent"]
categories: "技术动态"
---

# Kernel Forge：基于LLM的CUDA Kernel自动生成与优化Agent框架

## 事件/论文概述

2026年7月30日，arXiv上发布了一篇题为《Kernel Forge: An Agent Harness for LLM-based Generation and Optimization of CUDA Kernels》的新论文。该论文由Joshua Brodsky、Dhravid Kumar等七位作者共同完成，提出了一个名为**Kernel Forge**的开源端到端Agent框架，用于基于大型语言模型（LLM）自动生成和优化CUDA内核。

传统上，优化GPU计算内核（如矩阵乘法、卷积、归一化等）是降低深度学习模型推理延迟和成本的最直接手段，但需要专家手工编写底层GPU代码，人力成本极高。虽然已有一些基于LLM的Agent系统能够生成和优化内核，但现有工具多存在局限：评估时使用随机生成张量和孤立内核、输出需手动整合的独立CUDA代码、主要面向LLM PyTorch模型、以及缺乏对结果的检查和调试支持。

Kernel Forge旨在解决上述问题，它接受任何未经修改的PyTorch模型作为输入，支持视觉、扩散和LLM工作负载，并采用蒙特卡洛树搜索（MCTS）来探索多个优化路径，而非单一线性的精炼链。此外，它还配备了一个图形用户界面（GUI），用于监控进度、检查候选内核和调试失败情况。

## 关键技术点

1. **端到端Agent框架**：Kernel Forge是一个完整的Agent harness，能够直接接受未修改的PyTorch模型，自动遍历其中的计算图，定位可优化的内核（如adaptive_avgpool2d、group_norm、softmax等），并生成和优化对应的CUDA实现。

2. **蒙特卡洛树搜索（MCTS）**：不同于传统方法中线性生成→评估→修改的单链路径，Kernel Forge利用MCTS同时探索多个候选优化策略。MCTS树中的每个节点代表一个内核变体，通过模拟和回溯选择最有潜力的分支，从而避免陷入局部最优。

3. **支持多种模型类型**：Kernel Forge覆盖了视觉模型（ResNet-50）、扩散模型（Stable Diffusion 3.5 Medium）以及LLM（Gemma 4 E2B、Qwen 3.5 35B-A3B），表明其通用性不仅限于Transformer架构。

4. **图形用户界面**：提供了用于监控优化进度、检查候选内核代码以及调试失败的GUI，降低了开发和调试门槛。

5. **评估硬件与实验设置**：所有实验在NVIDIA DGX Spark（搭载GB10 GPU）上进行。每个内核仅进行50次优化迭代，即能发现优胜内核。

6. **性能提升量化结果**：
   - ResNet-50中的adaptive_avgpool2d：1.52倍加速
   - Stable Diffusion 3.5 Medium中的group_norm：1.70倍加速
   - Gemma 4 E2B中的softmax：2.83倍加速
   - Qwen 3.5 35B-A3B中的softmax：1.54倍加速

## 对数据科学或AI Agent落地的意义

- **降低CUDA优化门槛**：Kernel Forge使得非GPU编程专家也能为深度学习模型生成高效的CUDA内核，大幅减少手工调优所需的人力。这对于中小规模团队或快速原型验证尤为有价值。

- **Agent能力的延伸**：该工作展示了LLM Agent从“文本生成”向“底层计算优化”的延伸。Agent不仅能写代码，还能通过搜索和迭代改进编译器级别的性能，体现了Agent在系统工程中的潜力。

- **多路径搜索优于线性精炼**：MCTS的引入为Agent优化任务提供了新的范式。在传统“提示-生成-评估”循环中加入树搜索，可以更有效地探索解空间，避免过早收敛于次优解。

- **集成Debug与可视化**：GUI和调试支持使Agent不再是“黑盒”，提升了实际工程中的可接受度。对于数据科学家而言，能够直观看到每个候选内核的性能和代码，增强了信任感。

## 我的技术点评

这篇论文最大的亮点在于**将MCTS与LLM Agent结合用于CUDA内核优化**。传统基于LLM的代码生成往往是一次性的，或者通过简单的迭代改进（如反馈循环）。Kernel Forge的MCTS机制使得Agent能够在多个候选方案中并行探索，并在有限预算（50次迭代）内找到优于PyTorch默认实现的内核，这在实用性和创新性上都可圈可点。

另一个亮点是**对多种模型类型的支持**，包括视觉、扩散和语言模型，证明该方法并非针对特定架构的“过拟合”。不过，论文仅在单个GPU平台（DGX Spark GB10）上评估，且优化迭代次数较少（50次），是否在更复杂的模型或更大规模核函数上仍有效，需要进一步验证。此外，论文未明确说明Kernel Forge生成的CUDA内核是否能够自动集成到PyTorch的eager模式或torch.compile中，以及是否支持动态形状——这些是实际部署中的常见需求。

作为数据科学从业者，我认为Kernel Forge提供了一个良好的框架，但它目前仍属于研究原型。未来若能与PyTorch的Inductor或Triton后端结合，自动化程度会更高。另外，MCTS的搜索策略（如UCT参数）如何影响收敛速度，以及能否自适应调整迭代次数，论文未深入讨论。总体而言，这是一个方向正确的积极探索，值得关注。

## 原文链接

- arXiv论文：https://arxiv.org/abs/2607.24762
- 代码仓库：原文注明代码在此 https URL，但未给出具体URL（原文未说明）。
