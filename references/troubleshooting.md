# 故障排查与注意事项（Troubleshooting）

> 仅在遇到对应故障、或需要确认运行细节时打开本文件。

## 目录

- [重试策略](#重试策略)
  - [安全分类器瞬时故障](#安全分类器瞬时故障)
  - [MinerU 提取超时](#mineru-提取超时)
  - [Obsidian 导出](#obsidian-导出)
- [MinerU 注意事项](#mineru-注意事项)
- [Obsidian 导出注意事项](#obsidian-导出注意事项)

---

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

## MinerU 注意事项

- 提取耗时 30-60 秒，不要中途取消。
- 扫描版 PDF 必须加 `--ocr`。判断方法：如果提取出的 MD 内容极少或全是乱码，说明是扫描版。
- 输出目录结构：`{pdf名}.md` + `images/` 子目录（图片以 hash 命名，格式为 jpg/png）。

## Obsidian 导出注意事项

- `export_to_obsidian.py` 已处理 frontmatter 生成、图片复制、路径校验——agent 无需关心。
- `--compress` 会把超过 800px 的图压缩并保留原格式；不压缩则原样复制。
- **图片兜底：** 即使改写时遗漏了某些图片引用，导出脚本也会把 `images/` 中未被正文引用的图片自动追加到笔记末尾的 `## 全部图片 / 图片附录`，**保证图片一张不丢**；重复导出不会生成重复附录。脚本会打印 `Images on disk: N | Images referenced in note: N` 供核对。
- 步骤 4 输出 `Vault Note` + `Result: OK` 即成功。
