# Remastered System Composite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将已通过的重制星空、Boss、四颗恒星和五条连线组合成单一视觉验收入口。

**Architecture:** 保留三个独立 WebGL2 渲染器，由 `galaxy-lab` 统一驱动并合成。`cosmos-lab` 增加嵌入模式；Boss 嵌入模式输出事件视界与发光透明度，由主页面透明画布复制；系统层保持透明 HDR 前景。

**Tech Stack:** HTML, CSS compositing, JavaScript, WebGL2, GLSL ES 3.0

## Global Constraints

- 不重画或降级已经通过的单体渲染器。
- 画面顺序固定为星空、Boss、四星系与连线。
- 本轮只做真实浏览器截图验收，不运行项目测试套件。

---

### Task 1: 最终分层合成

**Files:**
- Modify: `frontend/space/cosmos-lab/index.html`
- Modify: `frontend/space/galaxy-lab/index.html`

**Interfaces:**
- Consumes: `cosmos-lab/?view=abyss&embed=1`, `boss-lab/?view=far`
- Produces: `galaxy-lab/?view=overview` 最终验收入口

- [x] **Step 1: 为星空实验室增加嵌入模式**

加入 `body.embed` CSS，隐藏 `.hud`、`.hint` 和 `.credit`；从 URL 的 `embed` 参数设置该类。

- [x] **Step 2: 在组合页加入星空底层**

在 Boss iframe 之前加入 `#cosmos-layer`，使用 `abyss` 视角和 `embed=1`，并固定为不透明底层。

- [x] **Step 3: 将 Boss 改为中间光学层**

Boss 嵌入模式保留原相对论渲染，同时在最终 bloom pass 输出事件视界遮罩与发光透明度；组合页同步复制到透明 `boss-composite-layer`，不直接显示 iframe 底色。

- [x] **Step 4: 保持四颗恒星和五条连线为透明前景**

提高 `#system-layer` 层级，保持现有 premultiplied-alpha HDR 合成，不改星体与连线 shader。

- [x] **Step 5: 真实浏览器截图验收**

Run: Chrome headless 打开 `http://127.0.0.1:4173/space/galaxy-lab/?view=overview` 并保存截图。

Expected: 左侧四颗恒星与五条连线形成单一模块；右侧 Boss 保持巨大、黑体清楚；冷暗星空贯穿背景但不抢主体。

- [x] **Step 6: 提交结果**

```powershell
git add docs/superpowers/specs/2026-07-15-remastered-system-composite-design.md docs/superpowers/plans/2026-07-15-remastered-system-composite.md frontend/space/cosmos-lab/index.html frontend/space/galaxy-lab/index.html
git commit -m "Compose the remastered learning system"
```

## Self-Review

- 需求覆盖：四项已通过资产全部在同一入口出现，且保留方向性单系构图。
- 占位符扫描：无 TBD、TODO 或未定义步骤。
- 接口一致性：嵌入参数为 `embed=1`，组合入口为 `galaxy-lab/?view=overview`。
