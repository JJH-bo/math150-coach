# Free Exploration Camera Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为重制星系组合页加入拖拽、滚轮、WASD 和复位，并用同一镜头状态驱动星空、Boss 与四星系产生分层视差。

**Architecture:** `galaxy-lab` 持有唯一的 `exploration` 状态和输入循环。`cosmos-lab` 暴露 `window.cosmosCamera.setExploration()`；Boss 继续使用原模型的相机参数；系统 shader 读取平滑后的偏移和缩放。

**Tech Stack:** HTML, CSS, JavaScript, WebGL2, Canvas 2D compositor

## Global Constraints

- 不修改恒星、连线或 Boss 材质参数。
- 水平边界 `-0.48–0.40`，垂直边界 `-0.32–0.32`，缩放 `0.80–1.45`。
- Boss 事件视界必须持续位于画面右侧可见区域。
- 只进行真实浏览器交互验收，不运行项目测试套件。

---

### Task 1: 暴露星空镜头接口

**Files:**
- Modify: `frontend/space/cosmos-lab/index.html`

**Interfaces:**
- Produces: `window.cosmosCamera.setExploration({ x, y, zoom })`
- Produces: `window.cosmosCamera.reset()`

- [x] **Step 1: 加入外部镜头状态**

```js
const exploration = { x: 0, y: 0, zoom: 1 };
window.cosmosCamera = {
  setExploration(next) { Object.assign(exploration, next); },
  reset() { Object.assign(exploration, { x: 0, y: 0, zoom: 1 }); },
};
```

- [x] **Step 2: 将状态应用于星空 uniform**

```js
gl.uniform3f(skyUniforms.orientation,
  view.yaw + exploration.x * 0.62,
  view.pitch - exploration.y * 0.42,
  view.roll + exploration.x * 0.025);
gl.uniform1f(skyUniforms.fov,
  Math.max(48, Math.min(86, view.fov / exploration.zoom)));
```

### Task 2: 统一自由镜头与三层视差

**Files:**
- Modify: `frontend/space/galaxy-lab/index.html`

**Interfaces:**
- Consumes: `window.cosmosCamera.setExploration()`
- Consumes: Boss 透明合成画布的目标位置与缩放
- Produces: `window.explorationCamera.reset()` and `.snapshot()` for browser verification

- [x] **Step 1: 建立带阻尼的镜头状态和软边界**

```js
const exploration = {
  current: { x: 0, y: 0, zoom: 1 },
  target: { x: 0, y: 0, zoom: 1 },
};
const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
```

- [x] **Step 2: 接入拖拽、滚轮、WASD 和双击复位**

拖拽更新 `target.x/y`；滚轮更新 `target.zoom`；按键循环以时间增量移动目标；双击调用 `resetExploration()`。按钮区域不截获为镜头拖拽。

- [x] **Step 3: 驱动三个视觉层**

系统 shader 使用 `view.offset + current` 和 `view.zoom * current.zoom`；星空收到同一状态；Boss 保持已通过的相对论相机不变，合成画布按 `current` 产生较小位置和缩放变化，形成近中远三层视差并保护事件视界遮罩。

- [x] **Step 4: 更新交互提示**

显示“拖拽环视 · 滚轮推进 · WASD 移动 · 双击复位”，并在镜头离开原位后标记“自由镜头”。

### Task 3: 浏览器交互验收与提交

**Files:**
- Verify: `frontend/space/galaxy-lab/index.html`

- [x] **Step 1: 依次执行交互**

使用真实浏览器打开 `http://127.0.0.1:4173/space/galaxy-lab/?view=overview`，依次拖拽、滚轮、按住 `D` 与 `W`，读取 `window.explorationCamera.snapshot()`。

Expected: `x/y/zoom` 均发生变化；四星系位移最大，Boss 位移较小，星空只改变方向；Boss 仍在画面右侧。

- [x] **Step 2: 双击复位并截图**

Expected: `snapshot()` 回到 `{ x: 0, y: 0, zoom: 1 }` 附近；画面恢复初始验收构图。

- [x] **Step 3: 提交并推送**

```powershell
git add frontend/space/cosmos-lab/index.html frontend/space/galaxy-lab/index.html docs/superpowers/plans/2026-07-15-free-exploration-camera.md
git commit -m "Add free exploration to the remastered system"
git push origin stellar-material-proof
```

## Self-Review

- 规格覆盖：四种输入、三层联动、软边界、Boss 常驻和最小提示均有对应步骤。
- 占位符扫描：无未完成占位内容或未定义接口。
- 接口一致性：星空接口与组合页调用均为 `setExploration({ x, y, zoom })`。
