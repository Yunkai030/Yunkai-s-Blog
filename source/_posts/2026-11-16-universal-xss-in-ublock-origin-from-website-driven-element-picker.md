---
title: "uBlock Origin 曝一键通用 XSS：网站可借元素选择器注入受信任过滤器"
date: "2026-11-16 02:04:48"
tags: ["浏览器安全", "XSS", "uBlock Origin", "浏览器扩展", "AI安全"]
categories: "技术动态"
---

## 事件概述

2026 年 11 月 15 日，安全研究者 Smitty van Bodegom（loops）发表文章，披露 uBlock Origin 中存在一个“一键通用 XSS”（one-click universal XSS）问题。受影响的是 Firefox 上的 MV2 版本 uBlock Origin；原文同时提到，MV3 版本 uBO Lite 也受到一个类似但影响较小的问题影响。该问题目前已经修复，原文提到可参考 GitHub advisory 了解更多细节，但给定文本中没有给出 advisory 的具体链接。

问题的核心是：恶意网站可以
