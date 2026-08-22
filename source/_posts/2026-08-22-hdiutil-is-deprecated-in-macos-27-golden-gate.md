---
title: "hdiutil 在 macOS 27 Golden Gate 中被弃用：磁盘映像工具的迁移与阵痛"
date: "2026-08-23 10:00:00"
tags: ["macOS", "开发者工具", "命令行", "Apple"]
categories: "技术动态"
---

## 事件概述

2026 年 8 月，macOS 27 Golden Gate 测试版带来了一个令资深开发者侧目的变化：经典命令行磁盘映像工具 `hdiutil` 被正式标记为 **deprecated**（弃用）。这一信息来自最新测试版系统中 `man hdiutil` 的 "WHAT'S NEW" 部分。

Apple 给出的替代方案是 `diskutil image` 子命令体系，宣称可以覆盖所有磁盘映像操作，包括 attach、create、resize、info 和 chpass。值得注意的是，Apple 自家的 ASIF（Apple Sparse Image Format）格式仅被 `diskutil image` 支持，`hdiutil` 无法处理。

这一消息迅速在 Hacker News 引发讨论（144 分，53 条评论），背后的核心争议在于：Apple 在未完全补齐功能的情况下，就急于宣判一个被无数脚本和第三方应用依赖的工具的“死刑”。

## 关键技术点

### hdiutil 与 diskutil image 的功能对比

根据作者 Jeff Johnson 的详细测试，`diskutil` 虽然继承了 `hdiutil` 的大部分选项（但名称有所变化），却丢失了一些关键能力：

1. **`-puppetstrings` 缺失**：这是一个专门为程序化解析设计的进度输出选项，允许外部程序可靠解析 `hdiutil` 的进度（包括 `-1` 表示耗时不确定的状态）。新 `diskutil` 虽能在原地动态刷新进度百分比，但缺乏标准化的机器可读输出格式。

2. **`hdiutil create -srcfolder` 专属选项缺失**：包括 `-[no]crossdev`、`-[no]scrub`、`-[no]anyowners`、`-skipunreadable`、`-[no]atomic` 和 `-copyuid`。这些选项涉及跨设备文件处理、临时文件清理、属主处理等高级场景。

### 实测性能对比

作者在 Golden Gate 上与 macOS Sequoia 上的日常备份流程进行了对比：

| 项目 | hdiutil | diskutil |
|------|---------|----------|
| 平均耗时 | 110-115 秒 | 40-45 秒 |
| 生成文件大小 | 2.89 GB | 2.8 GB |
| 认证行为 | 触发管理员认证提示 | 直接失败，无提示 |

**性能提升**非常显著，`diskutil` 比 `hdiutil` 快了一倍多，同时生成的 DMG 文件更小（可能与其默认清理行为有关）。

### 权限处理的退化

测试中最棘手的问题：源目录中存在一个 root 拥有的文件。`hdiutil` 会主动弹出认证窗口，在用户输入管理员凭据后跳过文件继续完成创建。而 `diskutil` 则直接报出模糊的错误 `Operation not permitted`（操作不允许），**且 verbose 模式下也不提供任何有帮助的诊断信息**。作者不得不手动删除该文件后才得以继续。

### 行为差异：Scrub 逻辑

对比挂载两个 DMG 后发现，`diskutil` 生成的映像默认排除了 `~/.Trash/` 文件夹，行为像是强制开启了 `hdiutil` 的 `-scrub` 选项。对很多用户来说这或许是改进（更小的镜像），但对需要完整卷映像的场景则是个隐患。

## 对数据科学与 AI Agent 落地的意义

表面看这只是一个命令行工具的变迁，但深入思考，这背后与 AI Agent 和自动化数据管道的落地有着微妙而重要的关联：

1. **Agent 的工具依赖稳定性问题**：随着 AI Agent 越来越频繁地接管系统管理、数据备份等自动化任务，底层 CLI 工具的稳定性和可预测性变得至关重要。此次 `hdiutil` 的弃用与 `diskutil` 的不完全兼容，意味着依赖旧命令的 Agent 脚本将在升级后**静默失败**——正如作者展示的那样，连 `--verbose` 都很难诊断出失败原因。对于 Agent 开发者而言，建议在工具调用层增加结果校验和回退机制。

2. **自动化流水线的可观测性风险**：`-puppetstrings` 的缺失是程序化集成的一次倒退。Agent 在执行长耗时操作（如创建加密镜像）时，若无法获得标准化的进度输出，将难以进行超时判断、状态上报和异常恢复。这提醒 AI 工程化开发者：**人类可读的输出 ≠ 机器可解析的输出**，在 Agent 编排中必须显式声明输出格式。

3. **数据科学场景的连锁影响**：磁盘映像管理是数据归档、环境快照和数据集分发的常见底层操作。数据科学家经常使用 DMG 来打包特定版本的模型环境或数据集。`diskutil` 目前的功能缺失可能导致这些工作流的破坏，且从报错信息来看难以定位问题（"Operation not permitted" 完全没有提示是权限还是路径问题）。

4. **迁移教训对未来 Agent 设计的启示**：Apple 这次处理弃用的方式——在没有 1:1 功能替代、没有透明迁移路径的情况下直接标记 deprecated——为我们提供了一个反面教材。在设计 AI Agent 的长期 API 契约或工具接口时，应当维护**向后兼容层**、提供**弃用过渡期**，并保证报错信息对机器可诊断。

## 我的技术点评

### 性能提升值得肯定，但替代逻辑令人费解

`diskutil` 在同一任务上快一倍以上且镜像更小，这显然是 Apple 内部重写了底层实现所带来的红利。然而，正如作者所说：**既然功能都要在 `diskutil` 中保留，为什么非要弃用 `hdiutil` 不可？** 很简单，Apple 想摊销 `diskutil` 的维护成本，将两套代码收敛为一套。但问题是，收敛的方式应该是“让新工具成为超集后淘汰旧工具”，而不是“先淘汰旧工具再补齐新工具”。

### 认证提示的移除：安全隐患还是 UX 倒退？

`hdiutil` 触发认证弹窗的行为虽然打断自动化，但至少是**显式、可预期**的。`diskutil` 直接把错误吞掉并返回一个泛化的 `Operation not permitted`，这是命令行工具设计中非常糟糕的实践。即使是后端服务，也应该在错误响应中携带足够的排查上下文（如具体路径、期望的权限、触发策略），而不是让用户靠猜（作者原文："Luckily, I guessed the reason"）。

### 对 Knox 这类第三方应用的警示

作者曾在 Knox 应用中直接调用 `hdiutil`。一旦 macOS 未来某版本彻底移除 `hdiutil`，这些未及时适配的存量应用将直接崩溃。这给第三方 macOS 开发者敲响警钟：**深度依赖 Apple 私有或半公开系统工具是有风险的**，应及时抽象封装层，并关注系统更新日志中的 deprecation 标记。

### 顺便一提：`.bnnsir` 文件的 bug 依然未修复

作者顺带提到去年提交的关于 `.bnnsir` 文件导致 `hdiutil create` 失败的 bug（FB17162985）在 Golden Gate 中依旧存在。更有意思的是，Apple 的回复居然建议为 macOS 的 bug 提交 **iOS** sysdiagnose——这不禁让人怀疑 Apple 的 bug 分流系统是否存在严重问题，或者内部对文件系统的所有权实际上分散到了不同团队。

> 注：关于 Apple 内部的 bug 处理流程、为何选择在 Golden Gate 中弃用而非移除，以及 diskutil 后续是否会补齐缺失选项的官方时间表，**原文未说明**。

## 原文链接

- 原始文章：[hdiutil is deprecated in macOS 27 Golden Gate](https://lapcatsoftware.com/articles/2026/8/7.html)
- Hacker News 讨论：[News: YC 讨论帖](https://news.ycombinator.com/item?id=49402741)
