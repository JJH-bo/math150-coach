# Physics Black Hole Boss Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在独立网页中制作具有真实引力透镜、相对论吸积盘和体积密度的最终 Boss 黑洞样片。

**Architecture:** 使用独立 WebGL2 全屏渲染器承载 Bruneton beam-tracing 模型及预计算查找表；项目自有 shader 只负责体积密度、温度艺术控制和后处理。样片与正式知识场景隔离，用户批准后才讨论集成。

**Tech Stack:** WebGL2、GLSL ES 3.00、Bruneton beam tracing、浮点查找纹理、项目现有星空资产、HDR framebuffer、threshold bloom。

## Global Constraints

- 只修改或新增 Boss 样片文件与第三方许可文件。
- 不修改知识节点、连线、训练接口和正式相机逻辑。
- 不使用黑色球体、黑色平面、TubeGeometry、线框圆环或装饰曲线模拟黑洞。
- 用户视觉批准前不运行全量测试或业务检查。
- 第三方 Bruneton 源码必须保留 BSD-3-Clause 版权声明。

---

### Task 1: 建立独立物理黑洞运行时

**Files:**
- Create: `frontend/space/boss-lab/index.html`
- Create: `frontend/space/boss-lab/boss-lab.css`
- Create: `frontend/space/boss-lab/boss-lab.js`
- Create: `frontend/space/boss-lab/vendor/bruneton/LICENSE`
- Create: `frontend/space/boss-lab/vendor/bruneton/definitions.glsl`
- Create: `frontend/space/boss-lab/vendor/bruneton/functions.glsl`
- Create: `frontend/space/boss-lab/vendor/bruneton/model.glsl`
- Create: `frontend/space/boss-lab/assets/deflection.dat`
- Create: `frontend/space/boss-lab/assets/inverse-radius.dat`
- Create: `frontend/space/boss-lab/assets/noise.png`

**Interfaces:**
- Produces: `createPhysicsBlackHole(canvas, options)` returning `{ setViewPreset, resize, dispose }`.

- [ ] 复制并保留 Bruneton BSD-3-Clause 许可及物理 GLSL 源文件。
- [ ] 获取对应预计算偏转与逆半径查找表，不引入完整 Gaia 瓦片集。
- [ ] 创建全屏 WebGL2 canvas、浮点纹理加载器和着色器拼接器。
- [ ] 加入鼠标拖动、滚轮距离以及 `far`、`close`、`oblique` 三个观察预设。
- [ ] 提交独立运行时：`git commit -m "Build the physical black hole lab"`。

### Task 2: 制作体积吸积盘与电影级颜色

**Files:**
- Create: `frontend/space/boss-lab/physics-black-hole.glsl`
- Create: `frontend/space/boss-lab/volume-disc.glsl`
- Modify: `frontend/space/boss-lab/boss-lab.js`

**Interfaces:**
- Consumes: `createPhysicsBlackHole(canvas, options)` 的 WebGL2 program 和查找纹理。
- Produces: 单次全屏 draw call 中完成的引力透镜、事件视界、光子环、盘面前后像与体积密度。

- [ ] 将 `TraceRay`、盘面求交、Doppler 和 beaming 路径接入项目背景采样。
- [ ] 使用三层旋转 fBm、径向密度衰减和温度梯度构造非均匀盘体，禁止规则同心带。
- [ ] 添加盘面上方稀薄体积云；低密度区域必须透出被透镜扭曲的星空。
- [ ] 添加 HDR framebuffer、ACES 色调映射和只影响白热区域的 threshold bloom。
- [ ] 提交主视觉：`git commit -m "Render the relativistic abyss boss"`。

### Task 3: 只做视觉校准与交付

**Files:**
- Modify: `frontend/space/boss-lab/boss-lab.js`
- Modify: `frontend/space/boss-lab/volume-disc.glsl`
- Modify: `frontend/space/boss-lab/boss-lab.css`

**Interfaces:**
- Consumes: `setViewPreset("far" | "close" | "oblique")`。
- Produces: 独立页面和三个 1600×900 真实渲染截图。

- [ ] 校准黑洞在远景中的轮廓占比、近景事件视界尺寸和侧向视角盘面厚度。
- [ ] 删除所有类似黑椭圆覆盖层、土星环、粗橙色涂抹和独立曲线的视觉结果。
- [ ] 仅截取 `far`、`close`、`oblique` 三张图进行人工画面对照，不执行全量测试。
- [ ] 第一轮不达标时只允许一次针对性视觉修改；仍不达标则停止，不接入正式场景。
- [ ] 用户批准后再提交视觉校准；批准前保持独立样片状态。
