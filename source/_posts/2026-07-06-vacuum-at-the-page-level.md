---
title: Vacuum at the Page Level：深入 PostgreSQL 存储内核对 VACUUM 的字节级剖析
date: 2026-07-06 10:02:08
tags: [PostgreSQL, 数据库, VACUUM, 存储引擎, 性能优化]
categories: 技术动态
---

## 事件/论文/产品概述

[boringsql.com](https://boringsql.com/) 发布了一篇深度技术文章 **“Vacuum at the Page Level”**，它是 **PostgreSQL Storage Internals** 系列教程的第 7 章。文章不再重复讲解 VACUUM 的操作配置（如 autovacuum 调优、worker 分配），而是采用“逐字节”的方式，通过 `pageinspect`、`pg_visibility`、`pg_freespacemap` 等工具，**可视化**地展示 VACUUM 在对一个简单表执行清理时，页面（page）内部每一个字段、每一条行指针（line pointer）、每一个元组头部如何变化。文章完整记录了从创建基线、产生死元组、到 VACUUM 三个阶段（堆扫描、索引清理、堆清理）后的前后快照，并详细解释了行指针从 `LP_NORMAL` → `LP_DEAD` → `LP_UNUSED` 的生命周期。

## 关键技术点

1. **VACUUM 的三个阶段**  
   - **Phase 1: Heap scan** – 顺序扫描堆页面，执行 page pruning（清理 HOT 链之外的空闲空间），冻结旧元组，收集死元组的 TID（事务ID + 偏移量）。从 PostgreSQL 17 开始，使用基于 radix tree 的 TID 存储，更节省内存。  
   - **Phase 2: Index cleanup** – 遍历所有索引，移除指向死 TID 的索引条目。这是开销最大的阶段，即使只有少量条目需要删除，也需要读取索引的全部页面。  
   - **Phase 3: Heap cleanup** – 将之前被标记为 `LP_DEAD` 的行指针释放为 `LP_UNUSED`，更新空闲空间图（Free Space Map）和可见性图（Visibility Map）。

2. **行指针状态转换**  
   - 插入元组后：`LP_NORMAL`。  
   - 发生 DELETE 后，元组被标记为死（`t_xmax` 非零），但行指针仍为 `LP_NORMAL`，未释放任何存储空间。  
   - VACUUM Phase 1 的 pruning 删除元组存储，行指针变为 `LP_DEAD`（占位），等待索引清理。  
   - VACUUM Phase 3 将行指针设为 `LP_UNUSED`，空闲空间映射更新，页面空间完全回收。

3. **页面结构变化量化**  
   - 文章通过 SQL 查询精确显示了 `pd_lower`（行指针区域末尾）、`pd_upper`（元组区域起始）在删除前后的变化，以及每个元组 `lp_off`、`lp_len` 的位移，验证了 VACUUM 的 defragmentation（碎片整理）效果。

4. **与 VACUUM FULL 的对比**  
   - 常规 VACUUM 只回收页内空间，不改变元组的物理顺序；VACUUM FULL 会重建整个表，释放多余空间给操作系统，但代价更高。

## 对数据科学或 AI Agent 落地的意义

- **数据科学场景**：大规模数据仓库中，频繁的 DELETE/UPDATE 操作会导致表膨胀（bloat），直接影响查询性能（需要扫描更多页面）和 I/O 开销。深入理解 VACUUM 的字节级行为，有助于精准设置 autovacuum 阈值、调整 `maintenance_work_mem` 等参数，在保持数据一致性的同时最大化空间利用率。
- **AI Agent 落地**：Agent 系统往往依赖长时间运行的、带有状态管理的数据库（如会话存储、任务队列）。PostgreSQL 的 bloat 管理直接影响这些系统的稳定性和响应时间。理解 VACUUM 内部机制，能帮助 Agent 开发者设计更合理的清理策略，避免因表爆炸导致 Agent 服务中断。

## 我的技术点评

这篇文章堪称 PostgreSQL 性能调优的“显微手术”式教学。作者没有停留在“VACUUM 清除死元组”的抽象层面，而是通过具体的工具命令和数字对比，把页面内的每个字节变化都暴露在读者眼前。特别值得赞赏的是，文章强调了 **Pruning 与 VACUUM 的分工**：Pruning 只处理同一页面内的 HOT 链，而 VACUUM 负责跨页面、带索引的清理。这种分层解释帮助读者理解为什么 VACUUM 的 Phase 1 要设置 `LP_DEAD` 而非直接复用行指针——因为索引尚未更新。自从 PostgreSQL 17 引入 radix tree 存储 TID 后，`maintenance_work_mem` 瓶颈大大缓解，这一改进也很清晰地体现在文章中。

不过，原文未说明非索引表的行为是否有所不同，也未讨论 `LP_DEAD` 状态在并发读取时如何影响可见性规则（虽然文章隐含了它只是占位）。总体而言，这是“数据库内核工程师的必读内容”，也是“高级 DBA 和系统架构师的案头参考”。强烈推荐所有使用 PostgreSQL 的数据从业者阅读原文。

## 原文链接

英文原文：[Vacuum at the Page Level](https://boringsql.com/posts/vacuum-at-the-page-level/)  
Hacker News 讨论：[News.ycombinator.com](https://news.ycombinator.com/item?id=48802660)
