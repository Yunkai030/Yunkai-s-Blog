---
title: "Show HN：用 Behringer FCB1010 MIDI 踏板在 macOS 上做宏命令（fcbnerd）"
date: "2026-09-14 23:01:36"
tags: ["MIDI", "macOS", "命令行工具", "自动化", "AI Agent"]
categories: "技术动态"
---

## 事件概述

Hacker News 首页出现了一个名为 **fcbnerd** 的开源项目（Show HN），作者是 JamesRyanATX。项目的定位一句话就能说清：

> 把 MIDI 脚控制器当成 Mac 的“第二块键盘”。

具体来说，`fcbnerd` 是一个 macOS 命令行工具。它连接到 CoreMIDI 输入源，监听脚踏开关和表情踏板发出的消息，然后做两件事之一：

1. 匹配到用户预先配置的绑定（binding）时，执行一条 shell 命令；
2. 或者把每一条 MIDI 消息按行输出为一个 JSON 对象，交给别的程序去决定“这一脚是什么意思”。

项目虽然是为 Behringer FCB1010 这个 MIDI 踏板写的，但作者明确说明**它本身不含任何 FCB1010 专属逻辑，任何 CoreMIDI 输入源都可以用**。

原文给出的数据：Hacker News 上 28 points、2 条评论；GitHub 仓库 9 个 commit、9 个 star、0 个 fork（截至原文抓取时）。许可证内容原文未说明。

## 关键技术点

### 1. 为什么是命令行工具，而不是一个 App

这是整个项目最有意思的设计取舍。README 里给的理由很直接：

- 在 Mac 上做“按键 / 执行脚本”这类动作，需要沙盒应用拿不到的权限；
- 而且每个用户想要触发的动作完全不同，做成 App 反而没法通用。

于是 `fcbnerd` 只做**读 MIDI** 这一件事——读 MIDI 不需要任何权限。真正的动作交给用户自己的 shell，或者交给已经有权限的工具（原文点名了 Hammerspoon 和 Keyboard Maestro）。这是一个很典型的权限切分：工具本身待在低权限区，把高权限行为外置。

### 2. 三种运行模式

```
fcbnerd [listen] [--source NAME] [--format json|text] [--bind BINDING]... [--quiet] [--shell PATH]
fcbnerd list [--format json|text]
fcbnerd simulate
```

- `listen`（默认）：连接所有 MIDI 源，或只连接名字包含 `--source` 指定的那些，持续输出事件直到中断。它**支持热插拔**：演出中途拔掉接口再插回来，事件流会继续，并插入 `disconnected` / `connected` 行。
- `list`：打印当前可用的 MIDI 源。
- `simulate`：发布一个名为 `fcbnerd simulator` 的虚拟 MIDI 源，循环播放合成的按键、一次踏板扫动和一条 sysex 消息。这样没有实体踏板也能开发消费端——一个终端跑 `simulate`，另一个终端跑 `fcbnerd`。

输出方面，`--format text` 会打印对齐的列，并且每一行都带上可直接用于绑定的 `bind=` 模式；脚本则应该用默认的 JSON，因为文本布局可能变化。状态信息走 stderr，stdout 只有事件，并且每行写完立即 flush，管道能立刻看到事件。

### 3. 绑定语法

先用文本模式按一下踏板，看它发什么：

```
$ fcbnerd -f text
16:30:41.115  pc                channel=1 program=7  bind=pc:1:7  [USB MIDI Interface]
16:30:41.115  cc                channel=1 controller=20 value=127  bind=1:20:127  [USB MIDI Interface]
```

然后把命令绑上去：

```
fcbnerd --bind '1:20:127=open ~/Downloads'
```

绑定格式是 `PATTERN=COMMAND`，**第一个 `=` 之后的所有内容都属于命令**，所以命令里可以再出现 `=` 和 `:`。`--bind` 可以重复多次。

| Pattern | 匹配内容 |
| --- | --- |
| `CHANNEL:CONTROLLER:VALUE` | Control Change，例如 `1:20:127`；写 `cc:1:20:127` 也行 |
| `pc:CHANNEL:PROGRAM` | Program Change，例如 `pc:1:7` |
| 任意数字位置写 `*` | 通配，例如 `1:30:*` 表示通道 1 上控制器 30 的所有取值 |

命令通过 `/bin/sh -c`（或用 `--shell` 指定的 shell）在后台执行，stdin 是 `/dev/null`，stdout 被重定向到 fcbnerd 的 stderr，避免污染事件流；加了 `--quiet` 才回到 stdout。命令可以看到这些环境变量：`MIDI_TYPE`、`MIDI_CHANNEL`、`MIDI_CONTROLLER`、`MIDI_VALUE`（cc）、`MIDI_PROGRAM`（pc）、`MIDI_SOURCE`。

README 给的表情踏板示例，是用踏板直接控制系统音量：

```
# Expression pedal sets output volume
fcbnerd -q --bind '1:30:*=osascript -e "set volume output volume $((MIDI_VALUE * 100 / 127))"'
```

### 4. 两个容易被忽略的工程细节

**重复触发与扫动节流。** 每一次“跺一脚”都会执行一次命令，所以连续两次快按会跑两次，哪怕第一次还没结束——也就是说，每一条匹配的消息都会启动一个 shell。作者明确警告：不要把 `*:*:127`、`pc:*:*` 这种宽模式留给会刷数据的设备。

踏板扫动是例外。一次扫动每秒会发几十个值，所以对于 value 位带 `*` 的绑定，每个控件（通道 + 控制器）同时只跑一份命令；运行期间只保留该控件最新的值，等它跑完再执行，这样既压住了 shell 数量，又能落在踏板的最终位置上。如果某条命令超过 5 秒仍在运行，fcbnerd 会在 stderr 上提示。

**Shell 函数与开关语义。** `sh -c` 不会加载交互式 shell 里的函数和别名。bash 里可以用 `export -f` 导出函数（macOS 的 `/bin/sh` 就是 bash，所以默认 shell 能看到）；zsh 不能导出函数，需要把函数写在文件
