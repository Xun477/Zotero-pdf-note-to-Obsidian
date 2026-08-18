# 常见问题（FAQ）

> 故障排查细节（重试策略、MinerU/Obsidian 注意事项）另见 [references/troubleshooting.md](../references/troubleshooting.md)。

## Q1: MinerU 提取失败？

- 检查 `MINERU_TOKEN` 环境变量是否有效、是否过期
- PDF 是否为扫描版——扫描版需加 `--ocr`（AI 会自动判断并添加）
- 网络问题重试 2-3 次

## Q2: 笔记为什么在 Obsidian 而不是写回 Zotero？

这是设计取舍：早期版本写回 Zotero，但带图片的笔记在 Zotero 里代价很高（膨胀 storage、污染附件条目、413 体积上限、图片无法全文检索）。改用 Obsidian 论文仓库后：图片与笔记同目录原生渲染、无体积上限、全库可检索、仓库即备份。详见 [technical-notes.md](technical-notes.md)。

## Q3: 笔记中的图片为什么有时不显示？

笔记与图片以相对路径 `![](images/xxx.png)` 同目录存放，Obsidian 原生渲染，正常不会丢失。若导出后看不到：在 Obsidian 中刷新索引（Ctrl+R），或确认 `文献\{论文名}\` 下确有 `images/` 文件夹。

## Q4: 同一篇论文跑两次会覆盖吗？

会，且这是预期行为。每篇论文固定写入 `{OBSIDIAN_VAULT_DIR}\文献\{论文名}\`，重跑会先清空该目录下的旧 `.md` 与 `images/` 再写入新笔记——Obsidian 中一个文件夹始终对应一篇论文的最新笔记。

## Q5: 扫描版 PDF 图片/表格能提取吗？

MinerU `--ocr` 模式可以识别扫描件中的文字，但图表提取质量取决于扫描清晰度。高清晰度扫描件效果较好。

## Q6: "论文" 和 "其他" 类型怎么选？

- **论文（非综述）**：有明确的实验方法、结果、讨论章节的原创研究论文
- **其他**：综述（Review）、Application Note、技术报告、专利、白皮书

不确定时选"其他"——自由模板更灵活，不会丢失信息。

## Q7: Skill 运行中报 "temporarily unavailable"？

这是安全分类器瞬时过载，非流程错误。Skill 内置了重试策略：心跳确认 → 3 秒后重试，最多 3 次。通常第一次重试即可恢复。
