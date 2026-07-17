# Custom GPT 章节星系接入

这套接入把 GPT 限制在“创建与修订章节草稿”的范围内。最终确认保留在网站审核页，GPT 拿不到该权限。

## 1. 准备可访问的服务

Custom GPT Action 不能访问 `127.0.0.1` 或仅局域网可见的服务。先把 mixed profile 的 FastAPI 应用部署到稳定的公网 HTTPS 域名，并确认：

- `/api/gpt/v1/contract` 可从公网访问；
- `/trainer/chapter-review/` 可在浏览器访问；
- `PUBLIC_BASE_URL` 是同一个公网 HTTPS 根地址；
- 反向代理允许最多 750,000 字符的 JSON 文本请求；
- 运行目录可以持久化 `CHAPTER_DRAFT_ROOT`。

## 2. 配置项目环境

复制 `.env.example` 中的变量到实际运行环境。用密码管理器或系统随机数工具生成两个不同的长随机密钥：

- `GPT_AUTHORING_KEY`：只放进 Custom GPT Action 的 Bearer 认证配置；
- `CHAPTER_REVIEW_KEY`：只给人工审核者，不写进 GPT Instructions 或 Action schema。

不要把真实 `.env`、密钥、审核 Cookie 或运行时草稿目录提交到 Git。

## 3. 导入 Action

1. 打开 `docs/custom-gpt/chapter-authoring-actions.openapi.yaml`。
2. 已部署服务可直接从 `https://你的域名/api/gpt/v1/action-schema` 读取自动替换域名后的 OpenAPI；也可以手动导入本地文件，并只修改 `servers[0].url`。
3. 在 GPT 编辑器的 Actions 中导入这个 OpenAPI 3.1 Schema。
4. Authentication 选择 API Key，Auth Type 选择 Bearer。
5. 填入 `GPT_AUTHORING_KEY` 的真实值。不要把它写进 schema 或 Instructions。
6. 确认工具列表恰好包含：
   `getProjectContract`、`createChapterDraft`、`updateChapterDraft`、`getChapterDraft`、`validateChapterDraft`。

## 4. 配置 GPT

把 `chapter-authoring-instructions.md` 的正文复制到 GPT Instructions。把以下文件作为知识文件提供给 GPT：

- `docs/ai_coordination/CHATGPT_CHAPTER_GALAXY_UPLOAD_STANDARD.md`
- 一份你希望 GPT 处理的教材或章节材料

不要上传 `.env`、运行时草稿或任何密钥文件。

## 5. 首次验收顺序

先保持 GPT 为 Only me/private，按顺序测试：

1. 调用 contract，确认返回 `chapter-galaxy-v1`；
2. 提交一个明显缺少章节表的草稿，确认得到结构化问题；
3. 提交一个完整的小章节，确认得到 `preview_ready`；
4. 打开返回的 `preview_url`，使用单独的人工审核密钥登录；
5. 核对预览 revision 与 content hash；
6. 在网站里完成最终确认，检查正式章节读取接口返回相同内容；
7. 再修改草稿，确认旧预览不能误操作新 revision。

## 6. 对外共享前

若以后把 GPT 分享给其他人，需要再完成域名验证、隐私政策、数据保留说明、密钥轮换方案和访问频率限制。不要在尚未完成这些准备时把 GPT 设为公开。

## 本地开发入口

本地服务启动后，人工审核页格式是：

`http://127.0.0.1:8000/trainer/chapter-review/?draft=<draft_id>&revision=<revision>`

这个地址只供本机调试，不能填入 Custom GPT 的 Action server。

## 容器部署

仓库根目录提供生产容器入口 `Dockerfile`。托管平台必须：

- 挂载可持久化目录，并将 `CHAPTER_DRAFT_ROOT` 与 `CHAPTER_PUBLISH_TARGET_ROOT` 指向该目录；
- 把真实密钥放在平台 Secret 管理中，而不是镜像或仓库；
- 提供 `PORT` 和公网 HTTPS；
- 使用 `/health` 作为健康检查；
- 设置 `PUBLIC_BASE_URL` 为部署后的 HTTPS 根地址。

没有持久化磁盘的临时容器只能用于联调，不能作为正式章节存储。
