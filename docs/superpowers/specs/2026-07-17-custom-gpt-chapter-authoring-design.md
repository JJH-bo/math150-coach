# Custom GPT 章节知识网接入设计

日期：2026-07-17

## 1. 目标

让用户在自定义 GPT 中上传或粘贴章节材料，由 GPT 理解材料并提交完整章节草稿。项目自动完成结构校验、知识网资产生成和三维预览。用户在网站预览页确认画面与内容后，只需点击一次“批准发布”，即可将经过确认的同一版本发布为正式章节。

最终用户流程固定为：

1. 用户把教材或章节材料交给自定义 GPT。
2. GPT 根据项目契约生成章节草稿并提交。
3. 项目自动校验并生成知识网预览。
4. GPT 返回预览链接和校验摘要。
5. 用户在网站查看预览。
6. 用户点击一次“批准发布”。
7. 后端发布用户实际预览的同一份内容，并返回正式章节入口。

用户不需要复制哈希、填写人工审核表、运行命令或手工把内容写入项目文件。

## 2. 已有能力与缺口

### 2.1 直接复用的已有能力

当前项目已经拥有以下基础：

- 章节 Markdown 的结构解析和校验；
- `GalaxyPlan`、`MacroNodes`、`MicroNodes`、`Edges`、`GalaxyBoss`、训练资产的解析；
- 将章节转换为 `systems / planets / links / boss` 的知识网资产；
- 每个星系 3–5 个训练星球的约束；
- 星系内部可见连线完整性检查；
- Boss 覆盖全部星系的检查；
- 候选章节 dry-run；
- 发布计划和内容哈希；
- 默认禁止写入的受控发布执行器；
- 已验收的行星、连线、Boss 黑洞、宇宙星空和有限角度观察场景。

### 2.2 必须补齐的能力

当前场景仍直接导入 `infinite-series-data.mjs`，因此还不能根据章节 ID 动态显示任意新章节。当前 authoring HTTP 接口也没有 Custom GPT 专用的权限边界、草稿持久化和面向人的一次批准入口。

本次必须补齐：

- Custom GPT 专用 API Key 认证；
- 面向 GPT 的精简 OpenAPI Action Schema；
- 章节草稿持久化和稳定的 `draft_id`；
- 幂等提交和版本号；
- 自动校验、知识网资产构建和预览；
- 通用章节资产加载，不再写死无穷级数；
- 独立的人类审核认证；
- 一次点击批准并发布已预览版本；
- 审计记录、错误报告和回滚所需的发布快照；
- 配置文档和 Custom GPT Instructions 模板。

## 3. 方案选择

### 3.1 方案 A：GPT 直接调用现有受控发布接口

改动最少，但 GPT 会获得接近正式发布的能力；现有接口面向内部 authoring 流程，不适合作为公开 Action 契约。一次错误调用可能直接影响正式章节。

不采用。

### 3.2 方案 B：GPT 草稿网关 + 网站一次批准

在现有生成、校验和发布链路外增加一层窄接口。GPT 只能创建、更新、校验和读取草稿；正式发布只能由网站中的人类审核会话触发。

采用此方案。它最大程度复用现有能力，同时将用户操作控制为一次预览和一次批准。

### 3.3 方案 C：GPT 提交后全自动发布

用户操作最少，但数学内容划分、训练题答案和视觉密度都可能需要人工判断。全自动发布会把模型判断错误直接变成正式内容。

本轮不采用。未来如果积累了足够的章节验收数据，可将其作为可选模式，但不能作为默认模式。

## 4. 总体架构

```text
Custom GPT
  │ Bearer GPT_AUTHORING_KEY
  ▼
GPT Authoring API /api/gpt/v1
  ├─ 读取项目契约
  ├─ 创建或更新草稿
  ├─ 自动校验
  ├─ 构建知识网资产
  └─ 返回预览链接
          │
          ▼
Draft Store + Immutable Revision
          │
          ▼
通用 Galaxy Preview
          │ Human review session
          ▼
一次点击批准
          │ exact revision hash
          ▼
现有 Controlled Publish
          │
          ▼
正式 Chapter Registry + Galaxy Asset
```

GPT API 和人类批准 API 必须分开。GPT 的 Action Schema 中不得出现批准或正式发布操作。

## 5. 数据契约

### 5.1 GPT 提交格式

GPT 继续提交项目已经支持的规范化章节 Markdown，避免同时维护第二套完整章节语义模型。请求外层使用严格 JSON：

```json
{
  "chapter_id": "power_series",
  "title": "幂级数",
  "source_markdown": "...完整章节 Markdown...",
  "client_request_id": "stable-unique-id",
  "contract_version": "chapter-galaxy-v1"
}
```

`client_request_id` 用于幂等处理。同一个请求 ID 和同一个内容哈希重复提交时，服务器返回原草稿，不创建副本；相同请求 ID 对应不同内容时拒绝请求。

### 5.2 草稿记录

每个草稿至少保存：

- `draft_id`
- `chapter_id`
- `title`
- `status`
- `revision`
- `content_hash`
- `contract_version`
- `source_markdown`
- `validation_report`
- `galaxy_asset`
- `created_at`
- `updated_at`
- `published_at`
- `publish_result`

草稿状态：

```text
received
  → invalid
  → preview_ready
  → approved
  → published

preview_ready → superseded
published → rolled_back
```

每次 GPT 修改草稿都创建不可变 revision。用户批准时必须指定当前预览 revision 和内容哈希，保证发布内容与预览内容一致。

### 5.3 持久化方式

项目目前以文件和清单为主要 authoring 方式，本轮不引入数据库。草稿使用项目运行数据目录中的原子写入 JSON/Markdown 文件保存：

```text
runtime/chapter_drafts/<draft_id>/
  manifest.json
  revisions/0001.md
  revisions/0001.asset.json
  revisions/0001.validation.json
```

正式发布仍复用现有 publish plan 和 controlled publish，不让 GPT 网关自行拼接正式目录。

## 6. API 设计

### 6.1 暴露给 Custom GPT 的 Action

#### `GET /api/gpt/v1/contract`

返回当前契约版本、章节模板、允许的节点类型、星系数量建议、每系 3–5 星球约束、Boss 规则、训练资产要求和错误码说明。

GPT 每次创建章节前读取该接口，避免其知识文件中的项目规则过期。

#### `POST /api/gpt/v1/drafts`

创建草稿或幂等返回已有草稿。服务器自动：

1. 验证认证和请求大小；
2. 解析 Markdown；
3. 执行结构与质量校验；
4. 构建知识网资产；
5. 保存不可变 revision；
6. 返回校验摘要和预览链接。

无论校验是否通过都保留诊断信息，但只有 `preview_ready` 状态才能显示完整预览和申请人工批准。

#### `PUT /api/gpt/v1/drafts/{draft_id}`

提交修订。必须携带上一 revision，防止覆盖并发修改。

#### `GET /api/gpt/v1/drafts/{draft_id}`

返回状态、当前 revision、校验问题、系统数、星球数、Boss 覆盖情况和预览链接。不返回服务器密钥或内部文件路径。

#### `POST /api/gpt/v1/drafts/{draft_id}/validate`

重新执行确定性校验并返回机器可读问题列表。该接口不修改正式内容。

### 6.2 不暴露给 Custom GPT 的人类操作

#### `POST /api/chapter-review/session`

用户使用单独的 `CHAPTER_REVIEW_KEY` 建立短期审核会话。成功后设置 `HttpOnly`、`SameSite=Strict` 的审核 Cookie。浏览器只需首次配置或会话过期后重新认证。

#### `GET /chapter-review/{draft_id}`

显示当前 revision 的三维知识网预览、章节结构摘要、校验结果和一次批准按钮。

#### `POST /api/chapter-review/{draft_id}/approve`

只接受有效审核会话，并要求：

- 草稿状态为 `preview_ready`；
- 请求中的 revision 与页面当前 revision 一致；
- 内容哈希与服务器保存值一致；
- 当前校验无阻断问题。

随后调用现有 publish plan 和 controlled publish。批准操作本身不接收任意 Markdown，防止批准时被替换内容。

#### `POST /api/chapter-review/{draft_id}/reject`

可选填写简短原因，将草稿退回 GPT 修订；不需要复杂审核表。

## 7. 认证和安全边界

### 7.1 GPT Authoring Key

- 环境变量：`GPT_AUTHORING_KEY`
- 请求方式：`Authorization: Bearer <key>`
- 只授权 `/api/gpt/v1` 草稿接口；
- 使用恒定时间比较；
- 日志中不得输出密钥或完整 Authorization Header；
- 支持轮换；
- 缺失配置时 GPT authoring 路由默认不可用；
- 不得调用批准、发布、用户数据和项目管理接口。

### 7.2 Human Review Key

- 环境变量：`CHAPTER_REVIEW_KEY`
- 与 GPT Key 必须不同；
- 只用于换取短期审核 Cookie；
- 批准接口不得出现在 GPT Action Schema 中；
- 审核 Cookie 有有效期并绑定服务端签名；
- Cookie 和密钥不得进入 URL。

### 7.3 请求保护

- 限制 Markdown 请求体大小；
- 对 GPT 写请求实施基础速率限制；
- 记录请求 ID、草稿 ID、revision、结果和时间，不记录密钥；
- 拒绝路径穿越和非法 `chapter_id`；
- 所有发布文件通过临时文件和原子替换写入；
- 发布前保留原版本快照；
- 正式环境只允许 HTTPS。

## 8. 通用知识网预览与正式加载

### 8.1 移除章节硬编码

现有场景的模型、材质、Boss、星空、连线和相机逻辑保留。只替换章节数据来源：

```text
硬编码 import infinite-series-data.mjs
                ↓
按 chapterId / draftId 请求统一 galaxy asset
```

正式章节：

```text
GET /api/challenge/v1/chapters/{chapter_id}/galaxy
```

草稿预览：

```text
GET /api/chapter-review/{draft_id}/galaxy?revision=N
```

两者返回同一 `ChapterGalaxyAsset` 数据结构，确保预览和正式画面使用同一渲染器。

### 8.2 布局规则

布局继续由项目端确定，而不是让 GPT 提交任意三维坐标：

- GPT 决定核心模块、学习顺序、优先级和推荐扇区；
- 项目布局器决定安全距离、扇形分区、星系间隔和相机观察边界；
- 每个星系 3–5 颗星球；
- 系统较多时按安全容量分扇区或分页，不将所有星系挤入一个画面；
- Boss 始终保持已验收的视觉中心和压迫感；
- 不允许章节内容修改材质、着色器或相机安全参数。

这样新增章节只改变知识结构，不会破坏已验收画面质量。

### 8.3 节点训练交互

每颗星球从 `planet.training` 读取训练数据，并继续调用现有训练入口动画和训练界面。GPT 必须提供核心题和迁移题；项目负责将节点 ID、题目数据和训练入口连接起来。

## 9. Custom GPT 交付物

项目仓库提供：

- `docs/custom-gpt/chapter-authoring-instructions.md`
  - 可直接复制到自定义 GPT Instructions；
- `docs/custom-gpt/chapter-authoring-actions.openapi.yaml`
  - 只含五个草稿 Action；
- `docs/custom-gpt/setup.md`
  - 域名、API Key、Action认证和Preview测试步骤；
- `docs/custom-gpt/example-conversation.md`
  - 从上传章节到返回预览链接的示例；
- `.env.example`
  - 仅包含变量名称和安全说明，不包含真实密钥。

Instructions 规定 GPT：

1. 先读取项目契约；
2. 分析材料后生成完整章节，而不是要求 Codex补全；
3. 提交草稿；
4. 根据机器校验结果自行修订；
5. 校验通过后把预览链接交给用户；
6. 不声称已经正式发布；
7. 不请求、显示或复述 API Key。

## 10. 错误处理

Action 返回稳定错误结构：

```json
{
  "error": {
    "code": "chapter_validation_failed",
    "message": "章节草稿存在阻断问题",
    "retryable": false,
    "issues": []
  }
}
```

主要错误：

- `authoring_auth_required`
- `authoring_auth_invalid`
- `contract_version_unsupported`
- `request_too_large`
- `idempotency_conflict`
- `chapter_validation_failed`
- `draft_not_found`
- `revision_conflict`
- `preview_not_ready`
- `review_auth_required`
- `approval_revision_mismatch`
- `publish_write_disabled`
- `publish_failed`

GPT 可根据 `retryable` 和 `issues` 决定修订或停止，不依赖解析自然语言错误。

## 11. 测试与验收

### 11.1 后端

- 无 Key、错误 Key、正确 Key；
- GPT Key 无法调用批准接口；
- 相同幂等请求不重复创建；
- 幂等 ID 内容冲突被拒绝；
- 非法章节 ID 和超大请求被拒绝；
- 无效章节返回结构化校验问题；
- 有效章节生成正确 systems、planets、links、boss；
- revision 冲突不会覆盖新版本；
- 批准时 revision 或 hash 不一致被拒绝；
- 一次批准只发布一次；
- 发布失败保留原正式章节和可诊断记录。

### 11.2 前端

- `chapterId` 可动态加载正式章节；
- `draftId + revision` 可加载草稿预览；
- 无穷级数不再依赖页面硬编码数据；
- 多章节复用同一行星、连线、Boss、星空和相机渲染；
- 节点点击继续进入对应训练动画；
- 审核按钮只在校验通过且会话有效时可用；
- 发布后显示正式章节入口。

### 11.3 端到端验收

使用一份不在仓库中的新章节材料验证：

1. Custom GPT读取契约；
2. GPT提交章节并根据校验结果至少完成一次修订；
3. 返回可打开的预览链接；
4. 预览正确显示多个星系、3–5训练星球/系、连线和Boss；
5. 用户点击一次批准；
6. 正式章节入口可访问；
7. 正式画面与批准前预览一致；
8. 星球点击进入对应训练交互。

## 12. 非目标

本轮不做：

- GPT 自动绕过人工批准；
- 让 GPT 改动着色器、相机、Boss模型或星空材质；
- 完整用户账号和多角色权限系统；
- 数据库迁移；
- 向 GPT 暴露整个项目 OpenAPI；
- 在代码仓库中保存真实密钥；
- 自动替用户购买域名或选择外部托管服务。

代码将具备部署到公开 HTTPS 域名后供 Custom GPT Actions 调用的能力。实际域名、证书和运行环境由部署配置提供。

## 13. 完成标准

本功能完成必须同时满足：

- GPT 可以独立创建与修订对应章节的完整知识网草稿；
- 新章节不需要 Codex手工转换或修改前端硬编码；
- 用户只需打开预览并点击一次批准；
- GPT 永远不能直接调用正式发布；
- 发布内容与用户预览版本完全一致；
- 任意章节复用当前已验收的高质量三维视觉系统；
- 提供可以直接粘贴到 Custom GPT 的 Instructions 和 OpenAPI Action Schema；
- 不包含真实密钥，且默认配置为拒绝未认证写入。
