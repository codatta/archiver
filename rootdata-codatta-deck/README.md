# RootData × Codatta 合作方案

战略合作提案 — 把 RootData 升级为 Web3 项目可信事实层 (Source of Truth Protocol for Web3)。

🔗 **在线查看**: https://rootdata-codatta-deck.vercel.app

---

## 文件

- `index.html` — 提案 deck (29 页,单文件,无任何依赖,纯 HTML/CSS/JS)

## 翻页操作

- 键盘:← / → / ↑ / ↓ / 空格 / Page Up / Page Down
- 鼠标:滚轮上下
- 触屏:上下滑动
- 点右侧小圆点跳到任意页

## 怎么编辑

1. 用任何文本编辑器打开 `index.html`(VS Code / Sublime / 浏览器开发者工具均可)
2. 直接改文字。每张 slide 用 `<section class="slide">` 包裹,顶部有注释标记(例如 `<!-- SLIDE 02 — 三层协作架构 -->`)便于定位。
3. 改主题色:页面顶部 `<style>` 块内的 `:root { --card-bg: #ff3300; ... }` 是所有颜色变量,改一处全局生效。

## 怎么本地预览

```bash
open index.html      # macOS
# 或直接拖到 Chrome / Safari
```

## 怎么部署上线

### 方式 A · 用 Vercel CLI(已配置)

```bash
npx vercel deploy --prod
```

### 方式 B · 用 GitHub 集成(推荐,改完 push 自动部署)

到 https://vercel.com/import 导入这个 repo,Vercel 会自动监听 main 分支,push 后自动重新部署。同一个 URL `rootdata-codatta-deck.vercel.app` 不变。

---

## Deck 结构

| # | 页面 |
|---|---|
| 01 | 封面 |
| 02 | 三层协作架构 |
| 03 | 三方分工 |
| 04 | 摘要 |
| 05–07 | RootData 数据资产价值 |
| 08–10 | 现状 5 大问题 |
| 11–13 | 现有模式 4 种缺陷 |
| 14–16 | 双方资产 + 合作路径 |
| 17–19 | 整合方案七步 |
| 20–24 | 用户场景三个 |
| 25–26 | 为什么这个方案更好 + 品牌定位 |
| 27–28 | Phase 1 范围 |
| 29 | 后续路线图 + 商业模式 |

## 风格

Swiss Modern — Bauhaus 平面设计传统:
- 字体:Archivo (display) + Nunito (body) + Noto Sans SC + JetBrains Mono
- 主色:Red `#ff3300`
- 底色:White `#ffffff`
- 96px 网格背景
- 卡片硬阴影 `12px 12px 0 #000`
