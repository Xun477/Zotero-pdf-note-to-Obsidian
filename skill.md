---
name: Zotero pdf note to Obsidian
description: Zotero PDF to structured reading notes. Use when the user asks to 整理/生成 Zotero 笔记, convert a Zotero paper PDF into a structured note, or says things like 生成笔记/整理这篇论文/写笔记. Covers both original research papers (7-section IMRaD) and other document types (reviews, application notes, technical reports, patents) with free-form summarization. Pipeline: pipeline_prep.py → AI rewrites → export_to_obsidian.py.
---

# Zotero PDF Note to Obsidian

把 Zotero 中的论文 PDF 一键转为结构化阅读笔记。MinerU 高精度提取 MD（自带图片引用）→ AI 直接在 MD 上改写为结构化笔记 → 导出 Markdown + 图片到 Obsidian 论文仓库（`$OBSIDIAN_VAULT_DIR`，默认 `G:\硕士\论文`）。用户只需告诉论文标题。

凭据通过环境变量管理：`ZOTERO_API_KEY`、`ZOTERO_USER_ID`、`MINERU_TOKEN`。凭据备份文件 `~\.zotero_credentials`（Windows 为 `%USERPROFILE%\.zotero_credentials`）。`ZOTERO_API_KEY` 用于搜索条目/定位 PDF（只读）；笔记写入 Obsidian 仓库本地文件，无需 Zotero 写入权限。Python 脚本一律写成 `.py` 文件再执行，避免 `python -c` 内联。

## 依赖检查

首次使用或怀疑环境有问题时，先确认：

```powershell
pip show httpx Pillow
[System.Environment]::GetEnvironmentVariable('ZOTERO_API_KEY', 'User')
[System.Environment]::GetEnvironmentVariable('MINERU_TOKEN', 'User')
```

三项都应该有有效输出。`httpx` 和 `Pillow` 缺失时 `pip install httpx Pillow`。

## 重试策略

### 安全分类器瞬时故障

Write / PowerShell 操作可能返回 `deepseek-v4-pro[1M] is temporarily unavailable, so auto mode cannot determine the safety of ...`——这是分类器瞬时过载，非流程问题。**不要放弃当前步骤**，等待 3 秒后重试该操作。每次重试前先跑一个轻量心跳确认分类器恢复：

```powershell
Write-Output "heartbeat"
```

若心跳返回 `heartbeat` 则分类器已恢复，继续之前被阻断的操作。连续 3 次失败再放弃。

### MinerU 提取超时

`pipeline_prep.py` 内置 120s 超时。若超时，检查输出目录是否已生成 `.md` 文件——有时 API 已完成但客户端超时。

### Obsidian 导出

`export_to_obsidian.py` 是本地文件写入（复制笔记 + 图片到仓库），无网络 POST。同一篇论文重复导出会覆盖 `$OBSIDIAN_VAULT_DIR\文献\{pdf名}\` 下的旧笔记。

## 流程

### 步骤 1 — 前置提问（合并为一次 AskUserQuestion）

用 **一次** `AskUserQuestion` 同时拿到两个选择，之后不再中断：

| 问题 | 选项 |
|------|------|
| 这篇 PDF 是什么类型？ | **论文（非综述）** / **其他**（综述/应用笔记/技术报告/专利） |
| 写入 Obsidian 时是否压缩图片（>800px 压缩）？ | **压缩图片（推荐）** / 不压缩 |

**类型选择影响后续模板：**
- 论文（非综述）→ 改写时 Read [resources/template/paper.md](resources/template/paper.md)，7 板块 IMRaD
- 其他 → 改写时 Read [resources/template/general.md](resources/template/general.md)，自由逐步总结

**压缩选择**在步骤 4 执行脚本时生效（`--compress` 参数）。

### 步骤 2 — pipeline_prep.py（搜索 + PDF + 目录 + MinerU）

一条命令完成原步骤 2-5 的全部机械操作：

```powershell
python "$env:USERPROFILE\.claude\skills\Zotero pdf note to Obsidian\scripts\pipeline_prep.py" --query "论文标题关键词" --base-dir $env:ZOTERO_NOTE_BASE_DIR
```

> 脚本路径随 skill 安装位置而定，此处用 `$env:USERPROFILE\.claude\skills\...` 作通用占位。`--base-dir` 默认取环境变量 `ZOTERO_NOTE_BASE_DIR`（未设置时依次回退 `resources/config/config.json` 的 `paths.base_dir` → `G:\硕士\ai\中转`）；Zotero 附件目录同理可用 `--storage-dir`、`ZOTERO_STORAGE_DIR` 或配置文件的 `paths.storage_dir` 覆盖。

输出 JSON（agent 解析后获取后续步骤所需的所有路径和 key）：

```json
{"item_key": "ABC123", "title": "...", "pdf_path": "G:\\...",
 "output_dir": "G:\\...\\paper_01", "md_file": "G:\\...\\paper_01\\paper.md"}
```

- 如果搜索结果不对，用 `--item-key` 直接指定 Zotero 条目 Key 跳过搜索
- 扫描版 PDF 加 `--ocr`
- 图片多或截图不全时，可加 `--model vlm` 提升 MinerU 提取完整度（更慢更贵，默认 `auto`）

### 步骤 3 — 读取 MD 并改写为结构化笔记

1. 读取步骤 2 输出的 `md_file`——**读到 `## References` / `# References` / `参考文献` 标题行立即停止**，后面的引用列表不读。
2. 在读取过程中，**枚举并记录 MD 中出现的所有 `![](images/xxx.png)` 图片引用**（正文中 References 之前出现的全部图片），形成一张图片清单。
3. 根据步骤 1 的类型选择，Read 对应模板：
   - 论文 → [resources/template/paper.md](resources/template/paper.md)
   - 其他 → [resources/template/general.md](resources/template/general.md)
4. 按模板中的改写规则和格式改写 MD，保存为 `{output_dir}\{pdf名}_note.md`。（规则已定义在模板文件中，无需在此重复。）
5. **图片完整性核对（必做）：** 改写完成后，对照第 2 步的图片清单逐条确认——原文每一张图片都必须出现在新笔记中（对应板块内，或文末 `## 📷 全部图片 / 图片附录`）。**笔记里的图片数不得少于原文图片数。** 有缺失就补上，不得省略任何一张。
6. 图片放不下的，在 `## 🏁 Conclusion` 之后、尾部标注之前加 `## 📷 全部图片 / 图片附录` 一节列出剩余图片。

### 步骤 4 — export_to_obsidian.py（导出 Markdown + 图片到 Obsidian）

```powershell
python "$env:USERPROFILE\.claude\skills\Zotero pdf note to Obsidian\scripts\export_to_obsidian.py" --md-file "{output_dir}\{pdf名}_note.md" --output-dir "{output_dir}" --pdf-name "{pdf名}" --item-key "{item_key}" --compress
```

步骤 1 选不压缩时去掉 `--compress`。`--pdf-name` 取步骤 2 输出 JSON 里的 `pdf_name`。脚本把笔记（自动加 YAML frontmatter）+ `images/` 写入 Obsidian 仓库 `文献\{pdf名}\`，输出 `Vault Note: <路径>` 和 `Result: OK` 即为成功。图片引用保持 `![](images/xxx.png)` 相对路径，Obsidian 内正常渲染。Obsidian 仓库根目录默认取环境变量 `OBSIDIAN_VAULT_DIR`（未设置时依次回退 `resources/config/config.json` 的 `paths.vault_dir` → `G:\硕士\论文`），也可用 `--vault-dir` 覆盖。

> 脚本直接从 `scripts/` 运行，`load_creds.py` 在同目录。

### 步骤 5 — 告知查看位置

告诉用户在 Obsidian 打开论文仓库查看笔记（`$OBSIDIAN_VAULT_DIR\文献\{pdf名}\`）。Obsidian 会自动索引新文件，必要时按 Ctrl+R 刷新。如需笔记也在 Zotero 里，可在 Zotero 中 `右键条目 → 添加笔记` 手动粘贴。

## MinerU 注意事项

- 提取耗时 30-60 秒，不要中途取消。
- 扫描版 PDF 必须加 `--ocr`。判断方法：如果提取出的 MD 内容极少或全是乱码，说明是扫描版。
- 输出目录结构：`{pdf名}.md` + `images/` 子目录（图片以 hash 命名，格式为 jpg/png）。

## Obsidian 导出注意事项

- `export_to_obsidian.py` 已处理 frontmatter 生成、图片复制、路径校验——agent 无需关心。
- `--compress` 会把超过 800px 的图压缩并保留原格式；不压缩则原样复制。
- **图片兜底：** 即使改写时遗漏了某些图片引用，导出脚本也会把 `images/` 中未被正文引用的图片自动追加到笔记末尾的 `## 📷 全部图片 / 图片附录`，**保证图片一张不丢**；重复导出不会生成重复附录。脚本会打印 `Images on disk: N | Images referenced in note: N` 供核对。
- 步骤 4 输出 `Vault Note` + `Result: OK` 即成功。

