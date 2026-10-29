---
title: "数据生成策略如何提升橄榄树病害分类模型：一篇 arXiv 论文解读"
date: "2026-10-28 04:00:00"
tags: ["数据生成", "深度学习", "计算机视觉", "农业AI", "论文解读"]
categories: "技术动态"
---

## 论文概述

这篇来自 arXiv cs.AI 的论文《Enhancing Deep Learning Model Performance through Data Generation Strategies: Classification of Olive Tree Diseases》由 Hicham El Akhal、Abderrahim Waga、Aissa Ben Yahya、Abdelbaki El Belrhiti El Alaoui 撰写，arXiv 编号为 2610.35984，提交时间为 2026 年 10 月 26 日。cs.AI updates 于 2026-10-28 收录推荐。

论文关注橄榄树病害图像分类。深度学习在植物病害诊断中表现有效，但常受数据不足和类别不平衡限制。作者提出一套“数据生成 + 数据分布利用”的综合策略：先使用多种数据生成技术扩充样本，再在三种数据组织场景下训练 EfficientNetV2B0，比较不同数据分布对模型性能的影响。摘要称实验结果显示分类准确率显著提升，并强调数据多样性和类别平衡的关键作用。

## 关键技术点

论文的技术路线可以概括为三个层面。

第一，数据生成技术。作者使用了传统数据增强方法
