# Zotero PDF Note to Obsidian

Zotero 论文 PDF 一键转结构化阅读笔记——MinerU 高精度提取 → AI 改写为结构化笔记 → 导出 Markdown + 图片到 Obsidian 论文仓库。

## 安装

面向 AI agent / 手动两种方式的完整安装指引见 **[INSTALL.md](INSTALL.md)**。

##### AI agent 安装

**交给你的 AI**，把这句话发给它：

> 按 https://github.com/Xun477/Zotero-pdf-note-to-Obsidian 的 INSTALL.md 安装并配置 Zotero PDF Note to Obsidian skill，完成后运行体检并把结果告诉我。

##### 手动安装

简要步骤：

1. 把 `Zotero pdf note to Obsidian` 文件夹复制到 skill 目录（Claude Code 为 `~/.claude/skills/`，Windows 为 `%USERPROFILE%\.claude\skills\`）
2. `pip install httpx Pillow mineru-open-api`
3. 配置三个凭据：`ZOTERO_API_KEY`、`ZOTERO_USER_ID`（无内置默认，**必须填自己的**）、`MINERU_TOKEN`
4. 配置两个路径：复制 `resources/config/config.example.json` → `resources/config/config.json` 并修改（推荐），或用环境变量 `ZOTERO_STORAGE_DIR`、`OBSIDIAN_VAULT_DIR` 覆盖

> **开源协议：** 本 skill 以 **MIT** 协议发布，见 [LICENSE](LICENSE)。
>
> **致谢：** 本 skill 的功能流程参考自 [cheneternity/Zotero-Analytical-Workflow-Skills](https://github.com/cheneternity/Zotero-Analytical-Workflow-Skills)，特此致谢。

## 一句话简介

把"下载论文 → 读论文 → 做笔记"的 1-2 小时手工劳动压缩为 ~3 分钟自动完成。你在 Zotero 里存了 PDF，说一声论文标题，结构化笔记就出现在 Obsidian 论文仓库。

**双模板设计：**
- **论文（非综述）** → [IMRaD 骨架 + 分析增强](resources/template/paper.md)（Author → Keywords → 一句话摘要 → Abstract → Introduction → Experimental → Results → Conclusion → 我的判断）
- **其他**（综述/应用笔记/技术报告/专利）→ [自由逐步总结](resources/template/general.md)（按原文章节归纳，不强制固定板块）

## 适用场景

- **期刊论文精读**：原创研究按 IMRaD 组织，综述/应用笔记按自然章节归纳
- **批量文献调研**：多篇论文顺序整理，输出格式统一便于横向对比
- **组会准备**：关键数据、对比图表、个人评注直接可用
- **论文写作引用**：Introduction 背景素材、实验方法参考、结论讨论对比一键提取

## 依赖清单

- **Python 3.9–3.12(3.12 已验证)**
- **命令行工具：** `mineru-open-api`（PDF 高精度提取，MD + 图片）
- **Python 包：** `httpx`（Zotero Web API 请求）、`Pillow`（图片压缩，可选）

一键安装：`pip install httpx Pillow mineru-open-api`

### 环境变量

**凭据（必填）：**

| 变量 | 说明 | 获取方式 |
|---|---|---|
| `ZOTERO_API_KEY` | Zotero Web API 密钥 | 见下方 [Zotero Web API Key 配置](#zotero-web-api-key-配置) |
| `ZOTERO_USER_ID` | Zotero 用户 Library ID | 同 Zotero API Key 页面显示。**必须填自己的，无内置默认** |
| `MINERU_TOKEN` | MinerU API Token | 注册 [MinerU 开放平台](https://mineru.net) 获取 |

**路径（必设，无内置默认路径）：**

| 变量 | 用途 | 默认值 |
|---|---|---|
| `ZOTERO_STORAGE_DIR` | Zotero 附件存储目录（`storage` 文件夹） | `C:\path\to\Zotero\storage` |
| `OBSIDIAN_VAULT_DIR` | Obsidian 论文仓库根目录 | `C:\path\to\Obsidian\vault` |

> **推荐改配置文件的路径**（`resources/config/config.json` 的 `paths` 字段），环境变量优先级更高、可临时覆盖；都不设置时回退到上表示例占位符。
>
> 凭据备份文件：`~/.zotero_credentials`（格式 `ZOTERO_API_KEY=...`，仅本机使用，勿分享）。凭据**不进**配置文件，避免随包泄露。

---

## Zotero 接入说明

本 skill 不依赖 MCP、也不依赖本地 CLI——通过 **Zotero Web API**（只读）直接与 Zotero 交互。MCP 是可选的增强方案（见 [docs/mcp-setup.md](docs/mcp-setup.md)）。

### Zotero Web API Key 配置

Zotero Web API 是本 skill 的**核心依赖**，用于搜索条目、定位 PDF、读取元数据（只读操作）。

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

或者写入凭据备份文件 `~\.zotero_credentials`：

```
ZOTERO_API_KEY=你的24位API密钥
ZOTERO_USER_ID=你的数字UserID
```

> **安全提示：** API Key 相当于密码。不要分享、不要提交到 git、不要在对话中直接粘贴。

### Zotero MCP 配置（可选增强）

本 skill 默认不使用 MCP。如需在对话中搜索/管理 Zotero 库的 MCP 能力，见 [docs/mcp-setup.md](docs/mcp-setup.md)。

---

## 快速开始

### 前置确认

```powershell
# 推荐：一键检查 Python 包 + 凭据（httpx/Pillow、ZOTERO_API_KEY、ZOTERO_USER_ID、MINERU_TOKEN、凭据备份文件）
python "$env:USERPROFILE\.claude\skills\Zotero pdf note to Obsidian\scripts\check_env.py"
```

脚本输出 `[OK]/[WARN]/[FAIL]`；有 `[FAIL]` 按提示补齐后重跑。

```powershell
# 补充：MinerU 命令行工具
mineru-open-api --version         # 应有版本号输出
```

### 使用

在 Claude Code 对话中：

```
/Zotero pdf note to Obsidian Advantages of measuring surface roughness with white light interferometry
```

AI 会先弹出一个合并问题框（类型 + 压缩），之后全自动完成：

1. **前置提问** —— 一次弹窗：PDF 类型（论文/其他）+ 是否压缩图片
2. **pipeline_prep.py** —— 搜索 Zotero → 定位 PDF → 创建目录 → MinerU 提取（一条命令）
3. **AI 改写** → 按对应模板 + `references/rewrite-rules.md` 生成结构化笔记
4. **export_to_obsidian.py** —— 就地生成最终笔记（YAML frontmatter + 图片附录兜底）+ 清理中间 `_note.md`

### 最后一步：查看笔记

- 在 Obsidian 打开论文仓库（`$OBSIDIAN_VAULT_DIR`）查看 `文献\{论文名}\{论文名}.md`
- 如需笔记也在 Zotero 里，可在 Zotero 中 `右键条目 → 添加笔记` 手动粘贴

---

## 输出结构

```
{OBSIDIAN_VAULT_DIR}\文献\{论文名}/            ← Obsidian 论文仓库（MinerU 输出与最终笔记都在这里，默认 C:\path\to\Obsidian\vault）
  ├── {论文名}.md                 ← 最终笔记：YAML frontmatter + 正文
  └── images/                     ← 图片（与笔记同目录，相对引用）
```

**无中转目录** —— MinerU 提取的 `{论文名}.md` + `images/` 直接写入 vault；AI 改写后由导出脚本就地生成最终笔记并清理中间 `_note.md`。每篇论文固定一个文件夹，重跑覆盖（Obsidian 一论文一文件夹）。

---

## 笔记模板

### 论文（非综述）— IMRaD 骨架 + 分析增强

| # | 板块 | 面向的问题 |
|---|---|---|
| 0 | Frontmatter（YAML） | theme/method/material/performance/key_finding/relevance 一句话提炼 → 可检索、可跨论文综合 |
| 1 | Author / 作者背景 | 谁写的？通讯作者水平？ |
| 2 | Key words / 关键词 | 跟我的方向有关吗？ |
| 3 | 一句话摘要 | 对象/器件 → 方法 → 关键结论（Obsidian 列表视图用） |
| 4 | Abstract / 摘要 | 方法？效果（数字）？创新点？ |
| 5 | Introduction / 引言 | 背景与不足 → 研究缺口 → 本文改进 |
| 6 | Experimental method / 实验方法 | 设计概述 → 材料试剂 → 流程参数 → 仪器表征 → 公式拆解 → 方法优劣 |
| 7 | Result and Discussion / 结果与讨论 | 性能指标（数字）→ 主要发现+原文引用 → 机理讨论 → 对比表 |
| 8 | Conclusion / 结论与个人评注 | 作者自评 + 未解决问题 + 个人评注 |
| 9 | 我的判断 | 启发 / 可借鉴 / 可追问 / 与我的研究关联 |

### 其他 — 自由逐步总结

不设固定板块，按原文自然章节归纳。要求：Frontmatter + 一句话摘要 + 关键结论配原文引用 + 结尾（结论与个人评注）+ 我的判断 + 尾部标注。

详见 [resources/template/paper.md](resources/template/paper.md) 和 [resources/template/general.md](resources/template/general.md)。

---

## 常见问题

常见问题见 [docs/faq.md](docs/faq.md)。

---

版本更新历史见 [CHANGELOG.md](CHANGELOG.md)。

---

## 文件结构

```
skills/Zotero pdf note to Obsidian/
├── skill.md                              # AI 执行指令
├── README.md                             # 本文档
├── CHANGELOG.md                          # 版本更新历史
├── docs/                                 # 人类阅读的文档（FAQ / 技术说明 / MCP）
│   ├── faq.md                            # 常见问题
│   ├── technical-notes.md                # 设计决策
│   └── mcp-setup.md                      # Zotero MCP 可选配置
├── INSTALL.md                            # 安装指引（AI agent / 手动）
├── LICENSE                               # MIT 开源协议
├── .gitignore                            # 排除 __pycache__、凭据、本地 config.json
├── scripts/                              # 可执行 Python 脚本
│   ├── load_creds.py                     # 凭据 + 配置加载（三级兜底）
│   ├── pipeline_prep.py                  # 搜索 + PDF 定位 + MinerU 提取
│   ├── export_to_obsidian.py             # 笔记 + 图片导入 Obsidian 仓库
│   ├── check_env.py                      # 环境/依赖检查（[OK]/[WARN]/[FAIL]）
│   ├── fetch_item_meta.py                # 取条目元数据（辅助）
│   └── md_to_html_and_write.py           # （旧）Zotero POST 版本，保留未用
├── references/                           # 按需加载的参考（skill.md 只留指针）
│   ├── rewrite-rules.md                  # 改写必做清单（Frontmatter/引用/公式/我的判断/证据分层）
│   └── troubleshooting.md                # 重试策略 + MinerU/Obsidian 注意事项
└── resources/                            # 模板与配置
    ├── config/                           # JSON 配置（非敏感）
    │   ├── config.example.json           # 示例/默认值（随包分发）
    │   └── config.json                   # 用户本地覆盖（复制 example 而来，不入库）
    └── template/                         # 笔记改写模板
        ├── paper.md                      # 论文模板：IMRaD 骨架 + 分析增强
        └── general.md                    # 通用模板：自由逐步总结
```

---

## 技术说明

设计决策见 [docs/technical-notes.md](docs/technical-notes.md)。
