# Custom GPT 章节星系接入验证报告

验证日期：2026-07-17

## 结果

Custom GPT 草稿创建、结构化修复、星系预览、人工精确版本确认和正式章节读取链路已贯通。Action 权限不包含人工确认接口。

## 自动化测试

### 聚焦后端回归

命令：

```powershell
python -m pytest backend/tests/test_chapter_galaxy_asset.py backend/tests/test_chapter_galaxy_builder.py backend/tests/test_gpt_draft_store.py backend/tests/test_gpt_authoring_api.py backend/tests/test_chapter_review_api.py backend/tests/test_custom_gpt_action_contract.py backend/tests/test_challenge_frontend_api.py backend/tests/test_chapter_publish_plan.py backend/tests/test_chapter_training_question_builder.py -q --basetemp .pytest_tmp -p no:cacheprovider
```

结果：`61 passed in 3.07s`

### 前端模块测试

命令：

```powershell
node --test frontend/space/galaxy-lab/chapter-data-loader.test.mjs frontend/space/galaxy-lab/infinite-series-scene.test.mjs frontend/space/galaxy-lab/observatory-camera.test.mjs
```

结果：`20 passed, 0 failed`

### 全量后端回归

命令：

```powershell
python -m pytest backend/tests -q --basetemp .pytest_tmp -p no:cacheprovider
```

结果：`641 passed in 24.56s`

## 真实 HTTP 烟测

使用 mixed profile 的本地 Uvicorn 服务，经真实 HTTP 完成：

1. 读取 `chapter-galaxy-v1` 契约；
2. 提交基于无穷级数章节的完整草稿；
3. 确认 `preview_ready` 且 `approval_ready=true`；
4. 建立独立人工审核 Cookie 会话；
5. 读取精确 revision 的预览星系资产；
6. 确认同一 revision 与 content hash；
7. 读取正式章节星系资产；
8. 比较正式资产与预览资产。

观察结果：

```json
{
  "draft_id": "infinite_series-7c01ab9bed792d3b",
  "revision": 1,
  "draft_status": "preview_ready",
  "approval_ready": true,
  "review_status": "published",
  "assets_equal": true,
  "contract_version": "chapter-galaxy-v1"
}
```

烟测使用了内存中的无穷级数内容修订，为缺少深层诊断覆盖的训练节点补充 HiddenAbilities；没有改写已提交的 `docs/chapter_inputs/infinite_series.md`。这同时验证了 GPT 可根据 `approval_ready` 和结构化问题完成修订后再交给人工确认。

## 权限与密钥检查

- Action schema 只包含五个 operation：
  `getProjectContract`、`createChapterDraft`、`updateChapterDraft`、`getChapterDraft`、`validateChapterDraft`。
- Action schema 不包含人工确认或正式写入 operation。
- GPT 使用 `GPT_AUTHORING_KEY`；人工审核使用不同的 `CHAPTER_REVIEW_KEY` 和 HttpOnly Cookie。
- `.env.example` 只包含占位值，没有真实密钥。
- 临时烟测密钥只进入本地进程环境和已删除的忽略文件。
- 仓库扫描未发现形如真实 OpenAI secret 的长 `sk-` 值。

## 部署前提

当前验证证明本地实现链路可用，但不能据此声称 Custom GPT 已能访问项目。正式连接前必须：

1. 把 mixed profile 服务部署在稳定的公网 HTTPS 域名；
2. 替换 OpenAPI 的 `servers[0].url` 和 `PUBLIC_BASE_URL`；
3. 在 GPT Action 设置中配置独立 Bearer 密钥；
4. 按 `docs/custom-gpt/setup.md` 完成私有验收；
5. 对外共享前补齐域名验证、隐私政策和访问频率限制。

## 仓库范围

本功能提交未纳入已有的未提交文件：

`frontend/space/galaxy-lab/infinite-series-data.mjs`
