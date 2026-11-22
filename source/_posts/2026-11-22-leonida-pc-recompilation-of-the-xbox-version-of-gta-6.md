---
title: "Leonida：把 Xbox 版 GTA 6 静态重编译到 PC 的工程拆解"
date: "2026-11-22 00:57:26"
tags: ["静态重编译", "逆向工程", "Vulkan", "着色器翻译", "AI Agent"]
categories: "技术动态"
---

## 事件概述

Hacker News 首页出现了一个名为 **Leonida** 的 GitHub 项目（仓库 `ItsNotRexed/Leonida`，1,494 次提交），自称是 **Xbox Series 版《Grand Theft Auto VI》的原生 PC 静态重编译（static recompilation）**：用玩家自己持有的游戏副本，在本地 PC 上把主机版代码与资源重建为可在 Windows 上运行的原生程序。该帖在 HN 上获得 15 分、3 条评论，评论内容原文未说明。

需要先明确项目状态：**目前游戏还不能启动（The game does not boot yet）**。作者的说法是，所有"不依赖游戏可执行文件"的部分已经就位，等有可执行文件的开发者接入即可开始攻坚启动流程。可玩性、剧情模式等均为"❌ No"。

合规边界在 README 中写得相当清楚：仓库**不包含游戏本体、密钥或可执行文件**，也不说明如何获取；使用前提是玩家自己的 Xbox Series 包（版本 1.0.2.1），文件已可在磁盘上以明文形式读取；项目**不做任何解密、不绕过任何保护**；构建产物（生成的着色器、导出的资源、runtime 目录、存档）全部留在本机，且明确要求不要分享。

## 关键技术点

### 1. 静态重编译的前提：x86-64 同构

项目的核心假设是：Xbox Series 的 CPU 是 x86-64，与 PC 同架构，因此游戏代码可以**加载并原生执行**，只需要重新实现主机的系统软件层。这与模拟器路线（动态翻译 + 硬件行为模拟）是两条完全不同的工程路径：静态重编译把"翻译"前移到构建期，运行期不再付出指令翻译开销，代价是需要为每一个平台 API、每一个 GPU 特性手写等价实现。

### 2. 着色器：26,503 个 RDNA2 程序的整体搬迁

这是目前完成度最高、也最能体现工程量的一块：

| 环节 | 状态 |
| --- | --- |
| 抠取、解包原生 RDNA2 代码、反汇编 | ✅ 全部 26,503 个 |
| RDNA2 → SPIR-V 翻译 | ✅ 全部 26,503 个，全部通过 `spirv-val` |
| 着色器类型分布 | 2,236 VS、12,101 PS、2,689 CS、9,282 mesh、195 geometry |

反汇编使用 LLVM 21；README 提到 LLVM 23 目前会让 1,471 个着色器被拒绝（issue #644）。每个着色器还附带一份元数据索引，供后续 pipeline 创建使用。

**Wave64 是这里最实质的技术障碍**：26,503 个着色器中有 21,545 个是 wave64。在 64 宽子组的 AMD GPU 上语义精确；在 32 宽子组的 NVIDIA / Intel 上，compute 与 mesh 着色器可以通过 `--wave64-emulate`（默认开启）做到精确，**但 vertex、pixel、geometry 着色器里的跨半 wave 操作目前仍是近似**。这一条被作者显式标为 ⚠️，是理解"能跑"与"跑对"之间差距的关键。

验证方式也值得注意：手写 GPU 测试（vertex fetch、纹理采样、export、ALU、部分寄存器、重心坐标、wave-uniform 分支、compute 的 LDS / barrier / buffer store、wave64 mask 等）在 **30 多种 GPU 与驱动组合**上跑过，覆盖 NVIDIA Turing 到 Blackwell（Windows 与 Linux）、AMD GCN3 到 RDNA4（含 Windows 驱动与 RADV）、Intel Gen9（ANV）、Apple M1（MoltenVK，无 geometry / mesh 阶段）、Mesa llvmpipe。但这些都是小测试着色器；**游戏自己的着色器只通过 `spirv-val` 与驱动 pipeline 创建（`vk_pipeline_check`）验证，没有做输出比对**。

### 3. 资源与音频管线

- **模型**：可导出为 OBJ，带真实名称、UV、材质引用；但并非所有布局都已解码。
- **纹理**：纹理字典与世界纹理池可导出为 DDS；以 BCPack 存储的池条目在导出时仍被跳过，作者另写了 clean-room 解码器 `tools/bcpack.py` 可重建 BC1 / BC3 / BC4 / BC5，但尚未接入 `rpf9dump`。
- **音频**：AWC 音频库整体导出；Opus 无损重封装为 Ogg Opus，PCM（codec 0/2）转 WAV，XMA2 用 ff
