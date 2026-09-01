---
title: "Darling：在 Linux 上运行 macOS 软件的开源翻译层"
date: "2026-08-31 22:53:45"
tags: ["开源", "macOS", "Linux", "翻译层", "跨平台"]
categories: "技术动态"
---

# Darling：让 macOS 软件在 Linux 上原生运行

Darling 是一个正在快速发展的开源翻译层项目，它让 Linux 用户能够直接运行 macOS 软件，其定位与 Wine 在 Linux 上运行 Windows 软件类似，但面向的是 Apple 生态。该项目于 2026 年 8 月 31 日出现在 Hacker News 首页并引发技术社区讨论（83 分，19 条评论）。

## 事件/项目概述

Darling（名字取自 **Darwin** 与 **Linux** 的组合）是一个 macOS 翻译层，它允许 Linux 系统直接运行 macOS 软件，且无需硬件模拟器。项目以 GPL v3 许可开源，代码托管于 GitHub，核心目标是实现完整的 Darwin 环境——包括 Mach、dyld、launchd 等关键组件。

根据官网信息，Darling 具备以下核心特性：

- **快速**：直接运行 macOS 软件，不依赖硬件模拟
- **免费开源**：基于 GPL v3 协议，在 GitHub 上公开开发
- **高兼容性**：实现了完整的 Darwin 运行环境
- **易用**：大多数安装配置由 Darling 自动完成
- **原生体验**：目标是让运行在 Darling 下的应用融入 Linux 桌面，看起来、用起来像原生 Linux 应用

目前 Darling 已具备**基础实验性 GUI 支持**，可以运行简单的图形应用，但这仍是项目最耗时的部分之一。

## 关键技术点

1. **翻译层架构**：与 Wine 类似，Darling 作为兼容层将 macOS 系统调用翻译为 Linux 可理解的调用，而非通过虚拟机模拟完整硬件。这使得性能表现更优。

2. **Darwin 环境实现**：Darling 实现了完整的 Darwin 核心（macOS 和 iOS 所基于的开源操作系统核心），包括 Mach 内核接口、dyld 动态链接器、launchd 进程管理等关键子系统。

3. **Cocoa 实现策略**：Darling 并非从零编写所有代码，它基于 Apple 发布的原始 Darwin 源码，并联合 **The Cocotron** 项目作为 Cocoa 实现基础，同时借鉴了 Apportable Foundation 和 GNUstep 的部分组件。

4. **WSL 2 支持**：官方文档确认，用户可以通过 WSL 2 在 Windows 上运行 Darling。

5. **iOS 应用规划**：项目长期目标是在 ARM 设备（如大多数 Android 手机）上运行 iOS 应用，最大挑战是需要自行实现 UIKit 框架。原文未说明时间表和当前进展。

6. **法律合规性**：项目仅使用 Apple 以完全自由软件形式发布的 Darwin 部分，明确声称不违反 Apple 的 EULA。

## 对数据科学或 AI Agent 落地的意义

尽管 Darling 本身不是数据科学工具，但其技术路线对 AI Agent 和数据处理生态有潜在启示：

- **跨平台兼容层拓宽了工具链边界**：如果 macOS 独占的软件（如某些专业数据软件或创意工具）能无缝运行在 Linux 服务器或工作站上，数据科学团队将拥有更灵活的环境选择。虽然原文未提及具体软件兼容性，但这一方向值得关注。

- **开源协作模式值得借鉴**：Darling 复用 Apple 开源 Darwin 源码、整合 Cocotron 等成熟开源项目的方式，展示了在复杂系统上构建兼容层的高效路径。AI Agent 项目同样需要大量复用和整合现有开源组件。

- **对 ARM 生态的长期规划**：计划在 ARM 设备上运行 iOS 应用的目标，指向了移动端 AI 推理和端侧智能的潜在未来。如果能实现 UIKit，AI Agent 在移动端的部署将多一种选择路径。

- **WSL 支持降低了使用门槛**：允许 Windows 用户通过 WSL 2 使用 Darling，意味着更多开发者可以在熟悉的环境中体验和测试 macOS 软件，降低了参与和贡献的门槛。

## 我的技术点评

Darling 是一个"注定艰难但极其有价值"的项目。说它艰难，因为 macOS 与 Linux 的系统调用面差异巨大，且 Cocoa 框架的复杂度远超 Windows API；说它有价值，因为它一旦成熟，将彻底打破 Apple 生态对桌面软件的绑定。

从技术实现看，Darling 的策略相当务实——不重写一切，而是站在 Apple 开源的 Darwin 和 Cocotron 等既有成果的肩膀上。这种"复用+补全"的思路，比完全从零实现要高效得多。不过，GUI 支持目前仅为"基础实验性"，距离流畅运行现代 macOS 应用还有相当距离。

值得注意的一点是，原文明确表示"只能直接使用 Darwin 中完全自由的部分"，这既是法律上的自我约束，也可能在功能完整性上留下盲区——例如某些闭源 macOS 框架（如 CoreAudio 或 Metal 的某些部分）恐怕难以被完整替代，长期兼容性仍存在不确定性。

从 Hacker News 的讨论热度（83 分、19 条评论）来看，社区对这类"生态桥梁"项目的兴趣是真实且持久的。但正如所有翻译层项目一样，Darling 的成功最终取决于社区的持续投入，以及是否有足够的开发者愿意为"在 Linux 上跑 macOS 软件"这一目标长期贡献。对于数据科学从业者而言，如果 Darling 未来能稳定运行某些 macOS 独占的数据处理工具，那将是实实在在的效率提升——但这仍需时日。

## 原文链接

- 项目官网：https://www.darlinghq.org/
- Hacker News 讨论：https://news.ycombinator.com/item?id=49515830
