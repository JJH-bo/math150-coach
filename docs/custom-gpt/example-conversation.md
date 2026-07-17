# Custom GPT 示例对话

## 用户

请读取我上传的《无穷级数》章节，创建这一章的知识星系。我希望核心板块按材料实际内容拆分，每个星系 3–5 个训练行星，全章一个综合 Boss。

## GPT 的正确行为摘要

1. 调用 `getProjectContract`。
2. 阅读全部材料，生成完整结构化 Markdown。
3. 调用 `createChapterDraft`。
4. 调用 `validateChapterDraft`。
5. 如果返回问题，修复 Markdown 并调用 `updateChapterDraft`，随后再次校验。
6. 状态达到 `preview_ready` 后返回：

> 已创建“无穷级数”章节草稿 revision 3。共 7 个核心星系、31 个训练行星和 1 个综合 Boss；阻断问题为 0。请打开预览页检查内容与画面：`https://your-domain.example/trainer/chapter-review/?draft=...&revision=3`

## GPT 不应这样回答

- “我已经直接把章节上线了。”
- “请把 API Key 发给我。”
- 只输出一个章节目录，不调用 Action。
- 第一次提交出现问题后仍把无效草稿交给用户。
- 自己发明不存在的最终确认工具。
