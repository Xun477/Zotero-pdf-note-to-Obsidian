# CHANGELOG

本文件记录 **Zotero PDF Note to Obsidian** 的版本更新历史（迁移自 README「版本更新记录」）。最新版本在顶部，按时间倒序。

---

### v1.4.3 (2026-08-19)

**变更：新增 README 封面图**

- 新增 `assets/cover.jpg`（1376×783）作为 README 封面图，展示于标题下方
- README 引用图片使用相对路径 `assets/cover.jpg`，随仓库分发

### v1.4.2 (2026-08-18)

**修复：Windows 中文控制台编码错误（UnicodeEncodeError）**

- **问题** -- 中文 Windows 默认代码页为 GBK（cp936），脚本输出被管道捕获时（AI CLI/Agent 均如此调用）Python 按本地代码页编码 stdout，中文输出报 `UnicodeEncodeError` 或乱码，用户需手动以 `python -X utf8` / `PYTHONUTF8=1` 运行才能通过体检
- **修复** -- 全部 6 个脚本（`check_env.py` / `pipeline_prep.py` / `export_to_obsidian.py` / `fetch_item_meta.py` / `md_to_html_and_write.py` / `load_creds.py`）在 import 后统一加入 stdout/stderr 编码保护：`reconfigure(encoding='utf-8', errors='replace')`（带异常兜底）
- **效果** -- 任何用户在任何 Windows 代码页下直接 `python check_env.py`（或任何脚本）均可正常输出中文，无需设置 `PYTHONUTF8`；已验证管道输出中文正常、退出码 0

### v1.4.1 (2026-08-18)

**变更：开源脱敏（去除个人路径与作者默认 ID）**

- 代码 / 示例配置 / 文档中的个人本机绝对路径与作者 Zotero User ID 默认值全部移除，改为占位符（`C:\path\to\...`）；真实路径收敛到 git-ignored 的 `resources/config/config.json`
- `ZOTERO_USER_ID` 不再有内置默认值；`check_env.py` 未设置时改为 [FAIL] 并提示自行配置
- 移除未引用的 `assets/` 截图

### v1.4.0 (2026-08-17)

**变更：skill.md 瘦身重构（渐进披露）**

- **skill.md 128→46 行** —— 参考 nature 系列"SKILL.md 路由表"模式：只留核心流程 + 红线（图片核对/心跳重试）；改写规则外置 `references/rewrite-rules.md`，故障/注意事项外置 `references/troubleshooting.md`（按需 Read，省 context）
- **新增 scripts/check_env.py** —— 依赖/凭据一键检查（[OK]/[WARN]/[FAIL] + 退出码），替代手动 PowerShell

### v1.3.0 (2026-08-17)

**变更：笔记模板深度优化（对照 Zotero-Analytical-Workflow-Skills）**

- **新增提炼性 Frontmatter** —— theme/method/material/performance/key_finding/relevance + zotero_key 稳定身份，一句话提炼、可检索、可跨论文综合
- **「一句话摘要」板块** —— 对象/器件 → 方法 → 关键结论
- **方法板块结构化** —— 设计概述 / 材料试剂 / 流程参数 / 仪器表征 / 公式拆解（防乱码）/ 方法优劣
- **结果板块升级** —— 性能指标数字优先 + 「主要发现+原文引用」成对（注明页码、禁反向生成 quote）+ 机理讨论 + 对比表
- **新增「我的判断」** —— 启发 / 可借鉴 / 可追问 / 与我的研究关联
- **证据分层** —— 原文=证据层、笔记=理解层，AI 转述与原文引用用排版区分
- **general.md 同步** —— 同样补齐 Frontmatter / 一句话摘要 / 原文引用 / 我的判断

### v1.2.0 (2026-08-15)

**变更：去掉中转目录，流程简化**

- **无中转目录** —— 删除 `ZOTERO_NOTE_BASE_DIR` / `--base-dir` / `paths.base_dir`（全部移除，无遗留）。MinerU 提取直接输出到 Obsidian 仓库 `{OBSIDIAN_VAULT_DIR}\文献\{论文名}\`
- **固定目录覆盖** —— 每篇论文固定一个 vault 文件夹（无 `_01/_02` 序号），重跑先清空旧产物再写入，Obsidian 一论文一文件夹
- **导出简化** —— `export_to_obsidian.py` 移除 `--output-dir`/`--vault-dir`/`--subdir`，目录全部从 `--md-file` 推导；完成后自动删除中间 `_note.md`
- **路径配置收敛** —— 环境变量仅剩 `ZOTERO_STORAGE_DIR`、`OBSIDIAN_VAULT_DIR`；vault 子目录 `文献` 可改 config `behavior.subdir`

### v1.1.3 (2026-08-15)

**变更：目录重组为安装包结构 + JSON 配置化**

- **模板目录** —— 两个模板移入 `resources/template/`（`paper.md` / `general.md`），skill.md/README 引用路径同步更新
- **JSON 配置** —— 新增 `resources/config/`：`config.example.json`（随包分发示例）+ `config.json`（用户本地复制，入 .gitignore）；脚本真实读取，优先级 `CLI 参数 > 环境变量 > config.json > 内置默认`
- **MinerU `--model` 参数** —— `pipeline_prep.py` 新增 `--model`（auto/vlm/pipeline/html，默认 auto，取自 config `behavior.model`），config `behavior.timeout` 控制客户端超时
- **README/INSTALL** —— 文件结构图重写为完整安装包结构；安装节与 Step 5 补充 config.json 复制配置说明

### v1.1.2 (2026-08-15)

**变更：开源化准备（备份副本）**

- **开源通用化** —— 硬编码的作者本地路径改为环境变量可配置：`ZOTERO_STORAGE_DIR`、`ZOTERO_NOTE_BASE_DIR`、`OBSIDIAN_VAULT_DIR`（未设置时回退默认值，对原作者无感）
- **新增 INSTALL.md** —— 面向 AI agent / 手动安装的完整指引（找 skill 目录 → 复制 → 装依赖 → 配凭据 → 配路径 → 验证）
- **README 更新** —— 新增"安装"入口、路径环境变量表、`ZOTERO_USER_ID` 必改提示；移除已不依赖的 `zotero-cli`；输出结构改为变量占位
- **清理** —— 排除 `__pycache__`，新增 `.gitignore`

### v1.1.1 (2026-08-15)

**变更：改名 + 图片截图不全修复**

- **改名** —— skill 更名为 **Zotero pdf note to Obsidian**（原 zotero-pdf-to-note），同步更新目录名、脚本路径引用与命令
- **图片兜底（硬保证）** —— `export_to_obsidian.py` 新增 `## 全部图片 / 图片附录`：`images/` 中未被正文引用的图片自动追加到笔记末尾，保证所有图片进笔记；重复导出不产生重复附录
- **校验强化** —— 新增反向不变量检查（磁盘图片必须全部被引用）+ `Images on disk / referenced` 覆盖率报告
- **模板强化** —— paper.md / general.md 由"关键图片"改为"所有图片，一条都不许丢"；skill.md 步骤 3 新增图片清单逐条核对

### v1.0 (2026-08-13)

**变更：笔记写入 Obsidian 论文仓库**

- **新增 export_to_obsidian.py** —— 笔记 + 图片导入 `{OBSIDIAN_VAULT_DIR}\文献\{论文名}\`，自动生成 YAML frontmatter（标题/作者/年份/期刊/DOI/Zotero 链接）
- **图片来源不变** —— 继续用 MinerU 提取（`images/` 相对引用，Obsidian 原生渲染）
- **移除 Zotero POST** —— 不再写 Zotero 笔记；`md_to_html_and_write.py` 保留但不再使用
- **pipeline_prep.py** —— 输出 JSON 追加 `pdf_name` 供导出脚本命名
- **压缩可选** —— `--compress` 将 >800px 的图压缩并保留原格式

### v0.5 (2026-07-23)

**精简：skill.md 瘦身 + 凭据检查简化**

- **skill.md 减至 113 行** —— 删内联改写规则（模板已定义）、删文件结构 section（README 已有）
- **description 优化** —— 覆盖论文/综述/应用笔记/专利四种类型，触发更准确
- **Zotero 注意事项浓缩** —— 编码/凭据/POST 格式等脚本内部知识不再加载到 context
- **依赖检查改纯 PowerShell** —— 不再使用 `python -c`，与脚本执行策略一致
- **目录更名** —— `references/` → `resources/`，模板与参考统一

### v0.4 (2026-07-23)

**重构：自动化 + 目录整理**

- **pipeline_prep.py** —— 搜索 + PDF 定位 + 创建目录 + MinerU 提取合并为一条命令，替代 4 个手动步骤
- **搜索迁移至 Web API** —— 不再依赖 zotero-cli，与写入链路统一
- **目录重组** —— 可执行代码统一到 `scripts/`，模板统一到 `resources/`，删除 `templates/`
- **不再复制到 Temp** —— 脚本从 `scripts/` 直接运行，`load_creds` 同目录导入

### v0.3 (2026-07-23)

**改进：流程优化与模板重构**

- **前置提问合并** —— 类型选择 + 压缩选项合并为一次 AskUserQuestion，之后全程无中断
- **双模板系统** —— 论文（7 板块 IMRaD）+ 其他（自由逐步总结），模板文件外置到 `templates/`
- **general 模板重写** —— 不再强制固定 5 板块，改为按原文章节自由归纳
- **POST 自动重试** —— `md_to_html_and_write.py` 内置 3 次指数退避重试（`ReadError`/`ConnectError`）
- **重试策略章节** —— 安全分类器瞬时故障、MinerU 超时、API 网络波动的标准处置流程
- **skill.md 精简** —— 模板内容外置，skill.md 专注执行流程

### v0.2 (2026-07-22)

**优化：Token 效率与代码组织**

- **MD 读取优化** —— 读到 References/参考文献标题即停止，跳过无价值的引用列表
- **作者查证策略** —— 作者 > 10 或 Review 类型自动跳过 H-index 搜索
- **图片压缩可选** —— 写入前弹出选择框，用户决定是否 PIL 压缩
- **合并脚本** —— MD→HTML + Zotero 写入 + 验证合并为单一 Python 文件
- **代码外置** —— Python 模板抽到 `references/md_to_html_and_write.py`
- **删除"踩过的坑"** —— 不再加载到 context

### v0.1 (2026-07)

- **MD 即笔记** —— MinerU 自带 `![](images/xxx.png)` 图片引用，AI 直接在 MD 上改写
- **流程简化** —— 删除 `figures/` 目录、图片重命名等冗余步骤
- **MD→HTML 转换** —— Python 脚本自动转 Zotero 兼容格式

### v0.0

- **MinerU 替代 PyPDF2** —— 高精度提取 MD + 内嵌图片，彻底解决图片/表格/公式丢失问题
