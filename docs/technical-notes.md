# 设计决策（Technical Notes）

记录本 skill 的关键设计取舍，供维护者与高级用户参考。

## 为什么把笔记放入 Obsidian 而不是写回 Zotero？

早期版本把笔记写回 Zotero（`scripts/md_to_html_and_write.py`，现已停用），但**带图片的笔记**在 Zotero 里代价很高：

- **膨胀 `Zotero\storage`** —— Zotero 会把笔记中的每张图片转成独立的附件文件，存到 `storage\<条目key>\` 下。一篇论文几十张图，就在 storage 里多出几十个文件；笔记越多，storage 目录越臃肿，还随每次同步全量上传到云端。
- **附件条目污染库结构** —— 每张图片都是一个附件，条目下挂满图片附件，分类、检索、迁移都变麻烦。
- **413 体积上限** —— 笔记 HTML 过长（图片多/大）时，Zotero API 会报 `413 too long`，笔记写不进去。
- **检索/复用受限** —— 图片在 Zotero 里只是附件，无法被全文检索，也难以按笔记批量浏览。

改用 **Obsidian 论文仓库**后：

- **`images/` 与笔记同目录** —— 图片以相对路径 `![](images/xxx.png)` 存放，Obsidian 原生渲染，不碰 Zotero 库，`storage` 零增量。
- **无体积上限** —— 本地文件系统，多图/大图都不受 413 限制。
- **全库可检索** —— 笔记与图片都在 Obsidian 里，可全文搜索、双向链接、图谱浏览。
- **仓库即备份** —— `{OBSIDIAN_VAULT_DIR}\文献\{论文名}\` 一个文件夹一篇论文（笔记 + images），方便整体同步/迁移。

**取舍：** 笔记不再自动出现在 Zotero 条目下方；如需保留在 Zotero 中，可在 Zotero 里 `右键条目 → 添加笔记` 手动粘贴（图片需另行处理）。

## 为什么用 Web API 而不是本地 API？

Zotero 7 的本地 HTTP API（端口 23119）**只能读不能写**。笔记写入必须通过 Web API（`api.zotero.org`）——本 skill 当前只用它做**只读**操作（搜索条目、定位 PDF、读取元数据），不存在写回问题。

## 为什么脚本错误消息要脱敏？

进错误消息的任何文本（异常 str、响应正文、URL）先过 `scripts/redact.py` 脱敏，确保终端、JSON 输出与 agent 上下文里不出现密钥（`ZOTERO_API_KEY`、`MINERU_TOKEN`）。原则：宁可脱敏过度——多脱敏的错误消息仍可读、可行动，泄露的 key 不可挽回。
