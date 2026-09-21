---
title: "Google 的开放智能体编排器 AX：把 Agent 当成一种全新工作负载来调度"
date: "2026-09-20 22:32:43"
tags: ["AI Agent", "Google", "编排器", "沙箱", "Agent Runtime"]
categories: "技术动态"
---

## 事件概述

Hacker News 首页出现了一篇题为《Google's Open Agentic Orchestrator》的帖子，指向项目站点 [agentexecutor.io](https://agentexecutor.io)，讨论区为 HN item 49780797。截至抓取时该帖获得 121 points、47 条评论。

站点介绍的项目代号为 **AX**（CLI 命令即 `ax`），定位是"声明式智能体控制平面"：用户声明一个 agentic task，AX 负责在集群上大规模执行。原文给出的核心主张包括：

- AX 会为任务做沙箱隔离、自动装配工作区、限制网络，并支持"每集群运行数十亿任务"；
- 既可以用"一个 agent 一个 task"的简单模式，也可以按 agent 需要组合任意多个 task；
- 页面提供了 "Get started" 与 "View on GitHub" 两个入口（原文未给出具体的 GitHub 仓库地址与开源许可证）。

需要特别说明的是：**AX 的 Google 背景来自项目站点的自述**——原文写的是 "AX was born at Google when agentic runtime systems research met frontier compute"，并提到借鉴了 Google DeepMind 的 agentic runtime 研究。原文未说明该项目在 Google 内部的具体归属、是否已正式对外发布，也未说明其开源范围（例如底层 Agent Substrate 是否同样开源）。

## 关键技术点

### 1. 四个声明式原语

AX 把智能体运行时拆成四个小原语，全部通过 YAML 声明：

| 原语 | 作用 | 原文描述要点 |
| --- | --- | --- |
| **Task** | 隔离执行 | 在带 CPU/内存限制的沙箱中运行不可信 agent 代码，创建、挂起、销毁都很廉价 |
| **Workspace** | 工作区准备 | 声明式列出 Git 仓库、MCP server、skills，或直接用自然语言描述目标；AX 会在任务启动前在每个沙箱中准备好 |
| **Gateway** | 网络策略 | 定义并快速管理网络策略，把流量锁定到显式的 host/port 白名单，并向入站请求注入凭据 |
| **Model** | 配置中心 | 集中配置模型、模型参数与密钥，一次 `apply` 即可轮换密钥或固定新模型版本 |

### 2. CLI 工作流

原文展示了一条完整链路：

```bash
ax apply -f task.yaml     # 创建 workspace 与 task
ax watch task test        # 观察 Phase 从 Pending -> Running，并显示 WorkerIP
ax get tasks              # 列出任务及所处阶段
ax ssh test -- ls /workspace
ax ssh test -- cd /workspace/go && go build ./...
ax ssh test -- ps -o pid,cmd
# PID 1 为 /usr/local/bin/ax-task-runner，PID 12 为 go build ./...
ax suspend task test
ax resume task test       # 恢复后 notes.txt 依然存在
ax delete task test
```

一个值得注意的细节是任务里的 `ps` 输出：沙箱内的 1 号进程是 `ax-task-runner`，说明每个 task 是一个自包含的执行单元，而非共享主机的普通进程。`suspend`/`resume` 之后文件仍然存在，也印证了"有状态 actor"的设计。

### 3. 底层：Agent Substrate

AX 宣称运行在 **Agent Substrate** 之上——一个"从零开始为高密度和快速有状态 actor 生命周期设计"的计算运行时。原文给出三项能力主张：

- **数十亿任务**：每个 task 是一个轻量 actor，每集群可扩展到数十亿并发 agent session，且没有编排器层面的上限；
- **亚秒级恢复**：等待模型响应、外部工具调用或人工确认的空闲 agent 会被 checkpoint、挂起，并在 1 秒内恢复，零冷启动延迟；
- **密集多路复用**：几十个 task 共享 worker 资源，把空闲等待时间变成可复用算力，从而"只在 agent 真正思考与执行代码时付费"。

原文未说明这些数字的测试口径、硬件前提，也未说明 checkpoint 的实现机制与存储开销。

### 4. 生成式工作区

AX 把生成式能力做进了平台本身：可以直接用自然语言描述"一个就绪环境应该长什么样"，AX 会在任务首次启动时把这个目标交给一个 agent，由它安装工具链并验证依赖。原文给的例子是：

```yaml
apiVersion: ax.io/v1alpha1
kind: Task
metadata:
  name: data-analysis
spec:
  workspaces:
    - name: python-env
      goal: "Set up a Python 3 development environment"
```

### 5. 支持的工作负载类型

原文列出的适用场景包括：交互式编码 agent、长时间运行的 agent server、Jupyter notebook、无头浏览器测试、自定义工具运行时；研究侧则强调可以批量拉起可复现的沙箱，用于收集轨迹（trajectories）、跑强化学习循环、以及规模化评估 agent。

## 对数据科学与 AI Agent 落地的意义

**第一，编排对象变了。** 原文有一个很准确的判断：agent 既不是 microservice 也不是 batch job。它累积状态、需要严格隔离、会调用模型 API 和工具服务，而且"如果没人盯着，可能在一个循环里烧钱"。传统面向无状态微服务或可预测批任务的编排器在面对这种负载时有两个结构性缺陷：让空闲沙箱一直挂着在成本上不可接受，同时又缺少原生的亚秒级 suspend/resume 支持。把 agent 当作一等公民的 actor 来调度，是对这个错配的直接回应。

**第二，空闲即浪费，这是 Agent 成本模型的核心。** 一个 agent 的典型时间分布是"思考一分钟、等响应几十秒"。如果按常驻进程计费，利用率会极低。密集多路复用加上挂起时不计算力，是把单位 agent 任务成本压下来的关键手段——对需要跑成千上万条轨迹的 RL 训练或评估流水线来说，这直接决定实验预算。

**第三，声明式环境对可复现性的价值。** 数据科学工作流最怕"环境漂移"：同一个评估脚本在不同机器上跑出不同结果。Workspace 原语把 Git 仓库、MCP server、skills 显式列进配置，配合隔离沙箱，为"同一任务可复现地重放"提供了基础设施层保证。而用自然语言生成 workspace 的做法，则是把环境搭建这件脏活交给 agent，降低上手成本——但同时也引入了不确定性，评估场景下是否该用这个模式，需要谨慎。

**第四，安全边界前置。** Gateway 的出站白名单加凭据注入，解决的是"agent 拿着密钥跑不可信代码"这一现实痛点。对任何要在生产里跑工具调用型 agent 的团队来说，网络围栏通常比模型选择更难做对。

## 我的技术点评

AX 的产品叙事相当清晰：用四个原语覆盖隔离、环境、网络、模型，把复杂度收在平台侧，把声明式 YAML 留给用户。`ax apply` / `ax watch` / `ax ssh` 这套 CLI 的交互手感明显参考了 Kubernetes，对云原生背景的开发者几乎没有学习成本——这是聪明的选择。

但作为一篇技术动态，我更愿意把它的关键主张标成"待验证"：

1. **"每集群数十亿任务"是数量级最大的宣称，也是最难核验的。** 原文没有给出集群规模、单任务资源下限、调度器吞吐等前提。几十亿并发 actor 在调度、状态存储、网络身份（每个沙箱的网络策略与凭据注入）上都意味着极高的元数据压力。这个数字更可能指的是"可寻址的任务总量/密度上限"，而不是"同时活跃执行的十亿个 agent"——但原文未作区分，读者不宜直接按字面理解。

2. **亚秒级恢复的代价没有披露。** Checkpoint 一个包含文件系统状态、进程状态的沙箱，并在一秒内恢复到零冷启动，需要非常激进的内存/存储快照策略。原文强调了"零冷启动延迟"，但未说明快照介质、恢复后的一致性保证，以及进程内未持久化状态（例如打开的 socket、正在执行的系统调用）如何处理。这是评估它能否替代现有方案时最该追问的点。

3. **"Born at Google" 与 "open" 需要分开看。** 页面自称诞生于 Google，HN 标题也用了 "Google's"，但一手信息只有项目站点自述，且原文未说明开源许可证、代码托管位置与治理方式。在许可证与仓库细节明确之前，"开源"应视为站点表述而非既成事实。另外在 Google 内部同赛道还有若干智能体运行时与 Agent 框架项目，AX 与它们的定位差异，原文未说明。

4. **生成式 workspace 是一把双刃剑。** 用自然语言让 agent 装环境，Demo 效果通常很好，但在研究场景下会削弱可复现性——同一句 goal 在不同时间可能装出不同版本的依赖。如果 AX 想主打"Perfect for research"，更稳妥的姿势是把生成式配置当作快速起步手段，把产物固化成显式声明后再用于正式实验。原文没有说明生成出的环境是否会被持久化/版本化。

5. **生态位判断。** 原文提到 AX "重度依赖 Agent Substrate"并在此之上提供 agentic 抽象与生成式运行时组件。这意味着 AX 更偏向控制平面与运行时的组合，而非又一个 agent 应用框架。真正决定它能否被采纳的，是 Workspace 的 MCP/skills 集成深度、Model 原语对多供应商模型的适配程度，以及既有 K8s 集群能否平滑接入——这三点原文均未展开。

**一句话
