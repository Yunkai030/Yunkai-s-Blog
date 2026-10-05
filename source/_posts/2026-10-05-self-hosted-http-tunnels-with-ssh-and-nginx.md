---
title: "用 OpenSSH 与 Nginx 自建 HTTP 隧道：一条命令替代 ngrok"
date: "2026-10-04 22:25:10"
tags: ["SSH", "Nginx", "内网穿透", "自托管", "运维"]
categories: "技术动态"
---

## 一、事件概述

Hacker News 首页在 2026-10-04 出现了一篇题为《Self-hosted HTTP tunnels with SSH and Nginx》的技术文章（53 分、11 条评论），作者在文中给出了一套**只依赖 OpenSSH 和 nginx** 的 HTTP 隧道方案。

问题的起点非常日常：朋友想帮你校对一篇还在草稿状态的博客文章，而预览服务只跑在本机的 `localhost:8080` 上。作者列举了几类现成方案：

- **商业服务**：ngrok、Cloudflare Quick Tunnels；
- **可自托管但需要专用客户端**：frp、localtunnel；
- **只需普通 SSH 客户端、但依赖特定 SSH 服务端实现**：sish。

作者的思路是：既然服务器上本来就在跑 OpenSSH 和 nginx，为什么不直接用它们拼出一个自托管隧道？最终效果是一条命令：

```bash
$ ssh -R 0:localhost:8080 http-over-ssh
Allocated port 41535 for remote forward to localhost:8080
https://6J3jK1WmB15c6WmjW_X-Wg--1789928654@p41535.ssh.luffy.cx/
```

命令执行后直接打印出一个带签名、带过期时间的可分享 URL。作者使用的域名是 `luffy.cx`，服务器是 `web02.luffy.cx`；原文未说明该域名或服务器的更多背景。

## 二、关键技术点

### 1. SSH 远程端口转发：`-R 0`

```bash
$ ssh -N -R 0:localhost:8080 web02.luffy.cx
Allocated port 41535 for remote forward to localhost:8080
```

把远程端口指定为 `0` 时，SSH 服务端会**自行分配一个空闲端口**，并把它回显出来。这一步就把本地 `8080` 暴露到了服务器的 `127.0.0.1:41535` 上。注意 `-N` 表示不执行远程命令，只做转发。

### 2. nginx：正则 `server_name` + 动态 `proxy_pass`

核心配置只有几行，靠 `server_name` 的正则捕获端口号，再拼进 `proxy_pass`：

```nginx
server {
  listen 0.0.0.0:443 ssl;
  listen [::0]:443 ssl;
  server_name ~^p(?<port>\d\d\d\d\d)\.ssh\.luffy\.cx$;

  location / {
    proxy_pass http://127.0.0.1:$port;
  }
}
```

也就是说，访问 `https://p41535.ssh.luffy.cx` 就会被代理到 `http://127.0.0.1:41535`，从而命中 SSH 建立的转发。

### 3. DNS 与通配符证书

需要为 `*.ssh.luffy.cx` 配置 DNS，并通过 Let's Encrypt 申请通配符证书。文中的做法是：

```dns
*.ssh.luffy.cx.     CNAME web02.luffy.cx.
ssh.luffy.cx.       CAA 0 issuewild "letsencrypt.org"
_acme-challenge.ssh.luffy.cx. CNAME ssh.luffy.cx.acme.luffy.cx.
```

`acme.luffy.cx` 是托管在 Route 53 上的一个 zone，作者用它来处理 **ACME DNS-01** 挑战——既用于通配符证书，也用于多台 Web 服务器承载的域名。作者使用 NixOS，证书是自动获取的。

### 4. 访问控制：端口不是可靠的秘密

作者明确指出：**端口本身是唯一保护内容机密性的"秘密"，而这个秘密的熵很低**。内核从本地端口范围里分配端口，作者实测：

```bash
$ sysctl -n net.ipv4.ip_local_port_range | awk '{print $1"—"$2" ≈ "log($2-$1+1)/log(2)" bits"}'
32768—60999 ≈ 14.785 bits
```

而且内核在选择随机空闲端口时**偏向奇数端口**，这意味着还要再损失一位熵。
