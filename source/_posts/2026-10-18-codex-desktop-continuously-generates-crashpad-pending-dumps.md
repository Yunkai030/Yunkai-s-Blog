---
title: "Codex Desktop 把磁盘写满的背后：Crashpad 处理器自己崩溃，每天产出 5GB 转储"
date: "2026-10-17 17:45:08"
tags: ["AI Agent", "Electron", "可观测性", "工程实践"]
categories: "技术动态"
---

## 事件概述

GitHub 上 openai/codex 仓库的 issue #25921 记录了一个相当“反直觉”的缺陷：**Codex Desktop 在 macOS 上持续不断地生成 Crashpad 待上传转储文件，数量与体积都没有上界**。

问题不在于应用崩溃——报告者明确说，应用本身仍然可用，可以正常操作界面、查看文件系统、访问 GitHub。真正的问题是后台有一个 Crashpad 崩溃处理进程在**稳定、持续、无节制地**产出 `.dmp` 与 `_sidecar.json` 配对文件，把用户本地磁盘一点点吃光。

- 报告者 Jolg42 于 2026 年 6 月 2 日提交 issue，最初观察到一天内积累 **4.9GB、54,504 个文件**（27,252 个 `.dmp` + 27,252 个 `_sidecar.json`），并且在调查过程中计数仍在上涨（53,444 → 54,064 → 54,504）。
- 另一位用户 mxggle 在同一 issue 下回复，自己的机器达到 **59GB**，在触及 65535 的文件数量限制后，后台进程“仍在无情地尝试写更多文件”。（原文未说明该 65535 限制具体对应哪一层系统限制。）
- 用户 dionylon 在更新的 Codex Desktop 版本上给出了更完整的诊断数据：pending 目录约 **58.89 GiB / 63,233,668,274 字节 / 738,864 个文件**，其中 369,431 个 `.dmp`、369,433 个 `_sidecar.json`；最近 24 小时新增 98,218 个文件，最近 7 天 573,480 个。

截至本文所依据的原文内容，issue 状态为 **Open**，带有 `bug`、`app`、`performance` 标签。官方修复计划与根因结论**原文未说明**。

## 关键技术点

### 问题现场：一个标准的 Crashpad 待上传队列

出问题的目录路径非常明确：

```text
~/Library/Application Support/com.openai.codex/web/Crashpad/pending
```

Crashpad 是 Chromium / Electron 体系里的崩溃收集与上报组件，`pending` 目录的角色就是“已生成、待上传/待处理”的队列。正常状态下，这个队列应该是有界的：上报成功、处理完成或轮转之后被清理。而这里的表现是队列只进不出。

报告者的取证命令也很朴素，值得作为排查模板：

```bash
du -sh "$HOME/Library/Application Support/com.openai.codex/web/Crashpad/pending"
find "$HOME/Library/Application Support/com.openai.codex/web/Crashpad/pending" -maxdepth 1 -type f | wc -l
find ... | sed 's/.*\.//' | sort | uniq -c | sort -nr
```

报告者还做了一个关键实验：手工清空 `pending` 目录后，占用从 4.9G 立刻降到 6.4M（70 个文件，35 对 dump/sidecar），**但新的配对文件马上又开始出现**。这排除了“历史遗留垃圾堆积”的解释，确认是活跃的持续生成。

### 根因线索：崩溃处理器自己在崩溃

dionylon 提供的最有价值的一条证据，是新生成的 `.dmp` 里记录的 FATAL 信息——它来自 `browser_crashpad_handler` **自身**：

```text
browser_crashpad_handler Codex_Mac crashpad-handler
[0609/103121.674299:FATAL:third_party/crashpad/crashpad/handler/mac/exception_handler_server.cc:76]
Check failed: kr == KERN_SUCCESS.
mach_port_request_notification: (os/kern) invalid capability (20)
executable_path=/Applications/Codex.app/Contents/Frameworks/Codex Framework.framework/Versions/149.0.7827.54/Helpers/browser_crashpad_handler
--database=/Users/<user>/Library/Application Support/com.openai.codex/web/Crashpad
```

也就是说：**负责收集别人崩溃报告的进程，自己在 macOS 上因 Mach port 通知注册失败（invalid capability）而 FATAL 退出，然后它自己的崩溃又变成一个待写入的 dump 文件。** 一旦进入这个循环，写入速率就基本等于进程重启速率。dionylon 的采样显示重装+重启后目录仍以约“每秒一份崩溃报告”的速度增长：

```text
10:28:46 files=142 MiB=11.63
10:28:51 files=152 MiB=12.44
10:29:01 files=172 MiB=14.08
10:29:06 files=182 MiB=14.89
```

这是典型的**自举型故障**：dump 生成路径本身失效，没有任何机制能感知“我产出的东西永远不会被消费”，于是产出一个、失败一个、再产出下一个。

### 孤儿 helper 与版本升级残留

报告者还注意到两个 `browser_crashpad_handler` 进程处于 `PPID=1`，即已被 init 收养的孤儿进程，自 2026 年 5 月 30 日起一直运行，并且**共用同一个 Crashpad database**。issue 中列出的相关历史问题也指向同一类症状：

- #25259：Codex App 更新后遗留旧的 Crashpad helper，残留导致重新启动可能变成 no-op；
- #11090：UI 卡死、worker 崩溃、并发孤儿 app-server 进程；
- #10627：更早
