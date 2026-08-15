# 🔧 Zotero PDF Note to Obsidian

Zotero 论文 PDF 一键转结构化阅读笔记——MinerU 高精度提取 → AI 改写为结构化笔记 → 导出 Markdown + 图片到 Obsidian 论文仓库。

## 📥 安装

面向 AI agent / 手动两种方式的完整安装指引见 **[INSTALL.md](INSTALL.md)**。简要步骤：

1. 把 `Zotero pdf note to Obsidian` 文件夹复制到 skill 目录（Claude Code 为 `~/.claude/skills/`，Windows 为 `%USERPROFILE%\.claude\skills\`）
2. `pip install httpx Pillow mineru-open-api`
3. 配置三个凭据：`ZOTERO_API_KEY`、`ZOTERO_USER_ID`（默认值是作者 ID，**必须改自己的**）、`MINERU_TOKEN`
4. 配置三个路径环境变量：`ZOTERO_STORAGE_DIR`、`ZOTERO_NOTE_BASE_DIR`、`OBSIDIAN_VAULT_DIR`

## 一句话简介

把"下载论文 → 读论文 → 做笔记"的 1-2 小时手工劳动压缩为 ~3 分钟自动完成。你在 Zotero 里存了 PDF，说一声论文标题，结构化笔记就出现在 Obsidian 论文仓库。

**双模板设计：**
- 📄 **论文（非综述）** → [7 板块 IMRaD](resources/paper.md)（Author → Keywords → Abstract → Introduction → Experimental → Results → Conclusion）
- 📋 **其他**（综述/应用笔记/技术报告/专利）→ [自由逐步总结](resources/general.md)（按原文章节归纳，不强制固定板块）

## 适用场景

- 📄 **期刊论文精读**：原创研究按 IMRaD 组织，综述/应用笔记按自然章节归纳
- 📚 **批量文献调研**：多篇论文顺序整理，输出格式统一便于横向对比
- 🔬 **组会准备**：关键数据、对比图表、个人评注直接可用
- 📝 **论文写作引用**：Introduction 背景素材、实验方法参考、结论讨论对比一键提取

## 依赖清单

- **Python 3.9+**
- **命令行工具：** `mineru-open-api`（PDF 高精度提取，MD + 图片）
- **Python 包：** `httpx`（Zotero Web API 请求）、`Pillow`（图片压缩，可选）

一键安装：`pip install httpx Pillow mineru-open-api`

### 环境变量

**凭据（必填）：**

| 变量 | 说明 | 获取方式 |
|---|---|---|
| `ZOTERO_API_KEY` | Zotero Web API 密钥 | 见下方 [Zotero Web API Key 配置](#zotero-web-api-key-配置) |
| `ZOTERO_USER_ID` | Zotero 用户 Library ID | 同 Zotero API Key 页面显示。⚠️ 默认值 `21068406` 是作者 ID，**务必改用自己的** |
| `MINERU_TOKEN` | MinerU API Token | 注册 [MinerU 开放平台](https://mineru.net) 获取 |

**路径（其他用户必须设置，否则回退到作者本地路径）：**

| 变量 | 用途 | 默认值 |
|---|---|---|
| `ZOTERO_STORAGE_DIR` | Zotero 附件存储目录（`storage` 文件夹） | `G:\硕士\Zotero\storage` |
| `ZOTERO_NOTE_BASE_DIR` | 笔记中转输出目录 | `G:\硕士\ai\中转` |
| `OBSIDIAN_VAULT_DIR` | Obsidian 论文仓库根目录 | `G:\硕士\论文` |

> 凭据备份文件：`~/.zotero_credentials`（格式 `ZOTERO_API_KEY=...`，仅本机使用，勿分享）

---

## Zotero 接入说明

本 skill 不依赖 MCP——通过 **zotero-cli**（本地读）和 **Zotero Web API**（云端写）直接与 Zotero 交互。MCP 是可选的增强方案。

### Zotero Web API Key 配置

Zotero Web API 是本 skill 的**核心依赖**，用于将笔记写入 Zotero 云端。

**获取步骤：**

1. 打开 https://www.zotero.org/settings/keys
2. 点击 **"Create New Private Key"**
3. 在 "Key Description" 中填写名称（如 `Claude-Skill`）
4. 在 "Personal Library" 下勾选 **"Allow notes access"** 和 **"Allow write access"**
5. 点击 **"Save Key"**，复制生成的 24 位密钥字符串
6. 页面顶部会显示 **"Your userID for use in API calls"**——记下这串数字

**配置到环境变量：**

```powershell
[System.Environment]::SetEnvironmentVariable('ZOTERO_API_KEY', '你的24位API密钥', 'User')
[System.Environment]::SetEnvironmentVariable('ZOTERO_USER_ID', '你的数字UserID', 'User')
```

或者写入凭据备份文件 `C:\Users\ASUS\.zotero_credentials`：

```
ZOTERO_API_KEY=你的24位API密钥
ZOTERO_USER_ID=你的数字UserID
```

> ⚠️ **安全提示：** API Key 相当于密码。不要分享、不要提交到 git、不要在对话中直接粘贴。

### Zotero MCP 配置（可选增强）

如果你的 Claude Code 需要**搜索、读取、管理** Zotero 条目的能力（而不仅是本 skill 的写笔记），可以配置 Zotero MCP Server。

**方案 1：社区 MCP Server（推荐）**

社区项目 `zotero-mcp` 封装了 Zotero Web API 为 MCP 工具。配置方式：

在 Claude Code 的 settings.json 中添加：

```json
{
  "mcpServers": {
    "zotero": {
      "command": "npx",
      "args": ["-y", "zotero-mcp"],
      "env": {
        "ZOTERO_API_KEY": "你的API密钥",
        "ZOTERO_USER_ID": "你的UserID"
      }
    }
  }
}
```

或在 `%APPDATA%\Claude\claude_desktop_config.json` 中配置。

**方案 2：Zotero 本地 API（实验性）**

Zotero 7 内置了本地 HTTP API（默认端口 23119），可读取已打开的本地库。但**只能读不能写**，写入仍需 Web API。

**MCP 提供的典型能力：**
- 搜索条目（标题/作者/标签/DOI）
- 读取条目元数据与附件
- 管理集合（Collections）与标签
- 创建/修改笔记与条目

> 📌 **本 skill 默认不使用 MCP**——zotero-cli + Web API 已覆盖全部需求。MCP 适合需要更精细 Zotero 操作的场景（如按标签批量整理、跨库检索等）。

---

## 快速开始

### 前置确认

```powershell
# 检查工具是否安装
mineru-open-api --version         # 应有版本号输出
python -m pip show httpx Pillow   # 应显示已安装
```

检查环境变量：

```powershell
[System.Environment]::GetEnvironmentVariable('ZOTERO_API_KEY', 'User')       # 应有值
[System.Environment]::GetEnvironmentVariable('ZOTERO_USER_ID', 'User')       # 必须是你自己的 ID
[System.Environment]::GetEnvironmentVariable('MINERU_TOKEN', 'User')         # 应有值
[System.Environment]::GetEnvironmentVariable('OBSIDIAN_VAULT_DIR', 'User')   # 你的 Obsidian 仓库
```

### 使用

在 Claude Code 对话中：

```
/Zotero pdf note to Obsidian Advantages of measuring surface roughness with white light interferometry
```

AI 会先弹出一个合并问题框（类型 + 压缩），之后全自动完成：

1. **前置提问** —— 一次弹窗：PDF 类型（论文/其他）+ 是否压缩图片
2. **pipeline_prep.py** —— 搜索 Zotero → 定位 PDF → 创建目录 → MinerU 提取（一条命令）
3. **AI 改写** → 按选择的模板生成结构化笔记
4. **export_to_obsidian.py** —— 笔记（带 YAML frontmatter）+ 图片导入 Obsidian 论文仓库

### 最后一步：查看笔记

- 在 Obsidian 打开论文仓库（`$OBSIDIAN_VAULT_DIR`）查看 `文献\{论文名}\{论文名}.md`
- 如需笔记也在 Zotero 里，可在 Zotero 中 `右键条目 → 添加笔记` 手动粘贴

---

## 输出结构

```
{ZOTERO_NOTE_BASE_DIR}\{PDF文件名}_{序号}/      ← 工作目录（临时，默认 G:\硕士\ai\中转）
  ├── {PDF文件名}.md              ← MinerU 原始完整 MD
  ├── {PDF文件名}_note.md         ← AI 结构化笔记
  └── images/                     ← MinerU 提取的图表

{OBSIDIAN_VAULT_DIR}\文献\{论文名}/            ← Obsidian 论文仓库（最终产物，默认 G:\硕士\论文）
  ├── {论文名}.md                 ← 笔记：YAML frontmatter + 正文
  └── images/                     ← 复制的图片（与笔记同目录，相对引用）
```

---

## 笔记模板

### 论文（非综述）— 7 板块 IMRaD

| # | 板块 | 面向的问题 |
|---|---|---|
| 1 | 👤 Author / 作者背景 | 谁写的？通讯作者水平？ |
| 2 | 🏷️ Key words / 关键词 | 跟我的方向有关吗？ |
| 3 | 📝 Abstract / 摘要 | 方法？效果（数字）？创新点？ |
| 4 | 🚪 Introduction / 引言 | 以前怎么做 + 不足 → 本文改进 |
| 5 | 🔬 Experimental method / 实验方法 | 设备/试剂/参数 → 复现依据 |
| 6 | 📈 Result and Discussion / 结果与讨论 | 关键数据 + 分析逻辑 + 与他文对比 |
| 7 | 🏁 Conclusion / 结论与个人评注 | 作者自评 + 未解决问题 + 个人评注 |

### 其他 — 自由逐步总结

不设固定板块，按原文自然章节归纳。仅要求：文章首部（元数据）、结尾（结论与个人评注）、尾部标注。

详见 [resources/paper.md](resources/paper.md) 和 [resources/general.md](resources/general.md)。

---

## 常见问题 (FAQ)

### Q1: MinerU 提取失败？

- 检查 `MINERU_TOKEN` 环境变量是否有效、是否过期
- PDF 是否为扫描版——扫描版需加 `--ocr`（AI 会自动判断并添加）
- 网络问题重试 2-3 次

### Q2: 笔记没有出现在 Zotero 中？

- **先 Sync 一次** —— 笔记通过 Web API 写入云端，需要 Sync 才能下载到本地
- 确认条目在 Zotero 中已存在且已同步（写入前需要条目在云端有记录）
- 检查 API Key 权限是否勾选了 "Allow notes access" 和 "Allow write access"

### Q3: 笔记写入报 413 "too long"？

- 图片过多或过大导致 HTML 超过 Zotero 限制
- **解决：** 前置提问时选"压缩图片（推荐）"

### Q4: zotero-cli 搜不到条目？

- 确认 Zotero 正在运行且该条目在库中
- 尝试用更短的关键词搜索（如只搜标题中的 2-3 个核心词）
- 检查条目是否被移到了回收站

### Q5: 同一篇论文跑两次会覆盖吗？

不会。输出目录自动递增：`_01`, `_02`, ...。每次运行独立保存。但在 Zotero 中每次会创建一个新的子笔记。

### Q6: 扫描版 PDF 图片/表格能提取吗？

MinerU `--ocr` 模式可以识别扫描件中的文字，但图表提取质量取决于扫描清晰度。高清晰度扫描件效果较好。

### Q7: 笔记中的图片为什么有时不显示？

Zotero 笔记中的图片采用 Base64 内嵌——只要 HTML 写入成功就不会丢。如果 Zotero 中不显示，可能是 Sync 未完成或 Zotero 渲染延迟，尝试重新打开条目。

### Q8: MCP 和 Web API 什么关系？我需要配置 MCP 吗？

**不需要。** 本 skill 默认用 zotero-cli（本地搜索）+ Zotero Web API（云端写入），无需 MCP。MCP 是可选增强，适合需要在对话中频繁搜索/管理 Zotero 库的场景。

### Q9: "论文" 和 "其他" 类型怎么选？

- **论文（非综述）**：有明确的实验方法、结果、讨论章节的原创研究论文
- **其他**：综述（Review）、Application Note、技术报告、专利、白皮书

不确定时选"其他"——自由模板更灵活，不会丢失信息。

### Q10: Skill 运行中报 "temporarily unavailable"？

这是安全分类器瞬时过载，非流程错误。Skill 内置了重试策略：心跳确认 → 3 秒后重试，最多 3 次。通常第一次重试即可恢复。

---

## 版本更新记录

### v1.1.2 (2026-08-15)

**变更：开源化准备（备份副本）**

- 🌍 **开源通用化** —— 硬编码的作者本地路径改为环境变量可配置：`ZOTERO_STORAGE_DIR`、`ZOTERO_NOTE_BASE_DIR`、`OBSIDIAN_VAULT_DIR`（未设置时回退默认值，对原作者无感）
- 📥 **新增 INSTALL.md** —— 面向 AI agent / 手动安装的完整指引（找 skill 目录 → 复制 → 装依赖 → 配凭据 → 配路径 → 验证）
- 📖 **README 更新** —— 新增"📥 安装"入口、路径环境变量表、`ZOTERO_USER_ID` 必改提示；移除已不依赖的 `zotero-cli`；输出结构改为变量占位
- 🧹 **清理** —— 排除 `__pycache__`，新增 `.gitignore`

### v1.1.1 (2026-08-15)

**变更：改名 + 图片截图不全修复**

- 🏷️ **改名** —— skill 更名为 **Zotero pdf note to Obsidian**（原 zotero-pdf-to-note），同步更新目录名、脚本路径引用与命令
- 🖼️ **图片兜底（硬保证）** —— `export_to_obsidian.py` 新增 `## 📷 全部图片 / 图片附录`：`images/` 中未被正文引用的图片自动追加到笔记末尾，保证所有图片进笔记；重复导出不产生重复附录
- 🔍 **校验强化** —— 新增反向不变量检查（磁盘图片必须全部被引用）+ `Images on disk / referenced` 覆盖率报告
- 📝 **模板强化** —— paper.md / general.md 由"关键图片"改为"所有图片，一条都不许丢"；skill.md 步骤 3 新增图片清单逐条核对

### v6.0 (2026-08-13)

**变更：笔记写入 Obsidian 论文仓库**

- ✨ **新增 export_to_obsidian.py** —— 笔记 + 图片导入 `G:\硕士\论文\文献\{论文名}\`，自动生成 YAML frontmatter（标题/作者/年份/期刊/DOI/Zotero 链接）
- 🔄 **图片来源不变** —— 继续用 MinerU 提取（`images/` 相对引用，Obsidian 原生渲染）
- 🗑️ **移除 Zotero POST** —— 不再写 Zotero 笔记；`md_to_html_and_write.py` 保留但不再使用
- 🔧 **pipeline_prep.py** —— 输出 JSON 追加 `pdf_name` 供导出脚本命名
- 🖼️ **压缩可选** —— `--compress` 将 >800px 的图压缩并保留原格式

### v0.5 (2026-07-23)

**精简：skill.md 瘦身 + 凭据检查简化**

- 🔪 **skill.md 减至 113 行** —— 删内联改写规则（模板已定义）、删文件结构 section（README 已有）
- 📝 **description 优化** —— 覆盖论文/综述/应用笔记/专利四种类型，触发更准确
- 🧹 **Zotero 注意事项浓缩** —— 编码/凭据/POST 格式等脚本内部知识不再加载到 context
- 🔧 **依赖检查改纯 PowerShell** —— 不再使用 `python -c`，与脚本执行策略一致
- 📁 **目录更名** —— `references/` → `resources/`，模板与参考统一

### v0.4 (2026-07-23)

**重构：自动化 + 目录整理**

- ✨ **pipeline_prep.py** —— 搜索 + PDF 定位 + 创建目录 + MinerU 提取合并为一条命令，替代 4 个手动步骤
- 🤖 **搜索迁移至 Web API** —— 不再依赖 zotero-cli，与写入链路统一
- 📁 **目录重组** —— 可执行代码统一到 `scripts/`，模板统一到 `resources/`，删除 `templates/`
- 🔧 **不再复制到 Temp** —— 脚本从 `scripts/` 直接运行，`load_creds` 同目录导入

### v0.3 (2026-07-23)

**改进：流程优化与模板重构**

- ✨ **前置提问合并** —— 类型选择 + 压缩选项合并为一次 AskUserQuestion，之后全程无中断
- ✨ **双模板系统** —— 论文（7 板块 IMRaD）+ 其他（自由逐步总结），模板文件外置到 `templates/`
- 🔄 **general 模板重写** —— 不再强制固定 5 板块，改为按原文章节自由归纳
- 🔧 **POST 自动重试** —— `md_to_html_and_write.py` 内置 3 次指数退避重试（`ReadError`/`ConnectError`）
- 📋 **重试策略章节** —— 安全分类器瞬时故障、MinerU 超时、API 网络波动的标准处置流程
- 📁 **skill.md 精简** —— 模板内容外置，skill.md 专注执行流程

### v0.2 (2026-07-22)

**优化：Token 效率与代码组织**

- 🔇 **MD 读取优化** —— 读到 References/参考文献标题即停止，跳过无价值的引用列表
- 🔇 **作者查证策略** —— 作者 > 10 或 Review 类型自动跳过 H-index 搜索
- ✨ **图片压缩可选** —— 写入前弹出选择框，用户决定是否 PIL 压缩
- 🔧 **合并脚本** —— MD→HTML + Zotero 写入 + 验证合并为单一 Python 文件
- 📁 **代码外置** —— Python 模板抽到 `references/md_to_html_and_write.py`
- 🗑️ **删除"踩过的坑"** —— 不再加载到 context

### v0.1 (2026-07)

- ✨ **MD 即笔记** —— MinerU 自带 `![](images/xxx.png)` 图片引用，AI 直接在 MD 上改写
- 🔧 **流程简化** —— 删除 `figures/` 目录、图片重命名等冗余步骤
- ✨ **MD→HTML 转换** —— Python 脚本自动转 Zotero 兼容格式

### v0.0

- ✨ **MinerU 替代 PyPDF2** —— 高精度提取 MD + 内嵌图片，彻底解决图片/表格/公式丢失问题

---

## 文件结构

```
skills/Zotero pdf note to Obsidian/
├── skill.md                              # AI 执行指令
├── README.md                             # 本文档
├── scripts/                              # 可执行 Python 脚本
│   ├── load_creds.py                     # 凭据加载模块（三级兜底）
│   ├── pipeline_prep.py                  # 搜索 + PDF 定位 + MinerU 提取
│   ├── export_to_obsidian.py             # 笔记 + 图片导入 Obsidian 仓库
│   └── md_to_html_and_write.py           # （旧）Zotero POST 版本，保留未用
└── resources/                            # 模板与参考
    ├── paper.md                          # 论文模板：7 板块 IMRaD
    └── general.md                        # 通用模板：自由逐步总结
```

---

## 技术说明

### 为什么把笔记放入 Obsidian 而不是写回 Zotero？

早期版本把笔记写回 Zotero（`md_to_html_and_write.py`，现已停用），但**带图片的笔记**在 Zotero 里代价很高：

- 📁 **膨胀 `Zotero\storage`** —— Zotero 会把笔记中的每张图片转成独立的附件文件，存到 `storage\<条目key>\` 下。一篇论文几十张图，就在 storage 里多出几十个文件；笔记越多，storage 目录越臃肿，还随每次同步全量上传到云端。
- 🗂️ **附件条目污染库结构** —— 每张图片都是一个附件，条目下挂满图片附件，分类、检索、迁移都变麻烦。
- ⚠️ **413 体积上限** —— 笔记 HTML 过长（图片多/大）时，Zotero API 会报 `413 too long`，笔记写不进去（见 FAQ Q3）。
- 🔍 **检索/复用受限** —— 图片在 Zotero 里只是附件，无法被全文检索，也难以按笔记批量浏览。

改用 **Obsidian 论文仓库**后：

- ✅ **`images/` 与笔记同目录** —— 图片以相对路径 `![](images/xxx.png)` 存放，Obsidian 原生渲染，不碰 Zotero 库，`storage` 零增量。
- ✅ **无体积上限** —— 本地文件系统，多图/大图都不受 413 限制。
- ✅ **全库可检索** —— 笔记与图片都在 Obsidian 里，可全文搜索、双向链接、图谱浏览。
- ✅ **仓库即备份** —— `G:\硕士\论文\文献\{pdf名}\` 一个文件夹一篇论文（笔记 + images），方便整体同步/迁移。

**取舍：** 笔记不再自动出现在 Zotero 条目下方；如需保留在 Zotero 中，可在 Zotero 里 `右键条目 → 添加笔记` 手动粘贴（图片需另行处理）。

### 为什么用 Web API 而不是本地 API？

Zotero 7 的本地 HTTP API（端口 23119）**只能读不能写**。笔记写入必须通过 Web API（`api.zotero.org`）。

### 为什么 MD→HTML 要用 Python 脚本而不是 AI 直接生成 HTML？

- 图片 Base64 编码必须在文件系统完成，AI 无法直接读取二进制图片
- Markdown 表格 → HTML 表格的转换涉及复杂的正则匹配
- Python httpx 手动 `encode('utf-8')` + `content=` 发送是避免中文乱码的唯一可靠方式
- 脚本内置 3 次自动重试，应对网络瞬时波动
