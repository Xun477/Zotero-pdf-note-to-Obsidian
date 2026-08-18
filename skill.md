---
name: Zotero pdf note to Obsidian
description: Zotero PDF to structured reading notes. Use when the user asks to 整理/生成 Zotero 笔记, convert a Zotero paper PDF into a structured note, or says things like 生成笔记/整理这篇论文/写笔记. Covers both original research papers (7-section IMRaD) and other document types (reviews, application notes, technical reports, patents) with free-form summarization. Pipeline: pipeline_prep.py → AI rewrites → export_to_obsidian.py.
---

# Zotero PDF Note to Obsidian

把 Zotero 中的论文 PDF 一键转为结构化阅读笔记。MinerU 高精度提取 MD（自带图片引用）→ AI 在 MD 上改写为结构化笔记 → 导出 Markdown + 图片到 Obsidian 论文仓库（`$OBSIDIAN_VAULT_DIR`，默认 `C:\path\to\Obsidian\vault`）。用户只需告诉论文标题。

凭据通过环境变量管理：`ZOTERO_API_KEY`、`ZOTERO_USER_ID`、`MINERU_TOKEN`，备份文件 `~\.zotero_credentials`。`ZOTERO_API_KEY` 只读用于搜索/定位 PDF；笔记写入 Obsidian 本地文件，无需 Zotero 写入权限。Python 脚本一律写成 `.py` 文件再执行，避免 `python -c` 内联。

## 依赖检查

首次使用或怀疑环境有问题时：

```powershell
python "$env:USERPROFILE\.claude\skills\Zotero pdf note to Obsidian\scripts\check_env.py"
```

脚本逐项检查 Python 包与凭据，输出 `[OK]`/`[FAIL]`。

## 流程

### 步骤 1 — 前置提问（一次 AskUserQuestion）

| 问题 | 选项 |
|------|------|
| 这篇 PDF 是什么类型？ | **论文（非综述）** / **其他**（综述/应用笔记/技术报告/专利） |
| 写入 Obsidian 时是否压缩图片（>800px 压缩）？ | **压缩图片（推荐）** / 不压缩 |

- 论文 → Read [resources/template/paper.md](resources/template/paper.md)，IMRaD 骨架
- 其他 → Read [resources/template/general.md](resources/template/general.md)，自由总结
- 压缩选择在步骤 4 用 `--compress` 生效

### 步骤 2 — pipeline_prep.py（搜索 + PDF + 目录 + MinerU）

```powershell
python "$env:USERPROFILE\.claude\skills\Zotero pdf note to Obsidian\scripts\pipeline_prep.py" --query "论文标题关键词"
```

输出 JSON（agent 解析后获取后续步骤所需路径与 key）：

```json
{"item_key": "ABC123", "title": "...", "pdf_path": "C:\\path\\to\\Zotero\\storage\\XXXX\\paper.pdf",
 "output_dir": "C:\\path\\to\\Obsidian\\vault\\文献\\paper", "md_file": "C:\\path\\to\\Obsidian\\vault\\文献\\paper\\paper.md",
 "pdf_name": "paper"}
```

- 搜索结果不对 → `--item-key` 直接指定条目 Key 跳过搜索
- 扫描版 PDF → `--ocr`；图片多/截图不全 → `--model vlm`（更慢更贵，默认 `auto`）
- 输出路径取 `$OBSIDIAN_VAULT_DIR` → `resources/config/config.json` → 默认值，详见 README

### 步骤 3 — 读取 MD 并改写为结构化笔记

1. 读 `md_file`，**读到 `## References` / `# References` / `参考文献` 标题行即停**，引用列表不读。
2. 枚举 MD 中 References 之前的所有 `![](images/xxx.png)` 图片引用，形成图片清单。
3. Read 对应模板 + [references/rewrite-rules.md](references/rewrite-rules.md)，按两者改写，保存为 `{output_dir}\{pdf名}_note.md`。
4. **图片完整性核对（必做）：** 对照图片清单逐条确认——原文每一张图都必须出现在新笔记（对应板块内，或文末 `## 全部图片 / 图片附录`）。**图片数不得少于原文。** 缺失即补上，不得省略任何一张。
5. 放不下的图，在 `## Conclusion` 之后、尾部标注之前加 `## 全部图片 / 图片附录` 一节列出。

### 步骤 4 — export_to_obsidian.py（导出 Markdown + 图片）

```powershell
python "$env:USERPROFILE\.claude\skills\Zotero pdf note to Obsidian\scripts\export_to_obsidian.py" --md-file "{output_dir}\{pdf名}_note.md" --pdf-name "{pdf名}" --item-key "{item_key}" --compress
```

步骤 1 选不压缩时去掉 `--compress`。脚本就地生成最终笔记（YAML frontmatter + 图片附录兜底），成功后**自动删除中间产物 `{pdf名}_note.md`**。输出 `Vault Note: <路径>` + `Result: OK` 即成功。

> 脚本从 `scripts/` 直接运行，`load_creds.py` 在同目录。

### 步骤 5 — 告知查看位置

告诉用户到 Obsidian 论文仓库查看（`$OBSIDIAN_VAULT_DIR\文献\{pdf名}\`），必要时 Ctrl+R 刷新。如需笔记也在 Zotero，可 `右键条目 → 添加笔记` 手动粘贴。

## 故障处理

- 若遇 `temporarily unavailable`（安全分类器瞬时过载）→ **心跳重试**：`Write-Output "heartbeat"` 确认恢复后重试被阻断操作，最多 3 次，不要放弃当前步骤。
- 其他故障 / 超时 / MinerU 与导出细节 → [references/troubleshooting.md](references/troubleshooting.md)。
