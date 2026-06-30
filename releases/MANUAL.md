# proofread-docx 安装使用手册

> 英语→中文外包翻译稿全流程自动化校对工具  
> 适用：Claude Code / Codex / Gemini CLI / Copilot CLI  
> 版本：v2.13 (2026-06-30)

---

## 目录

1. [功能概览](#1-功能概览)
2. [环境要求](#2-环境要求)
3. [安装](#3-安装)
4. [快速上手](#4-快速上手)
5. [项目文件组织](#5-项目文件组织)
6. [运行校对](#6-运行校对)
7. [理解校对结果](#7-理解校对结果)
8. [进阶功能](#8-进阶功能)
9. [常见问题](#9-常见问题)
10. [更新 skill](#10-更新-skill)

---

## 1. 功能概览

上传一篇英文原文 + 翻译公司的中文译文，AI 自动完成：

| 环节 | 做什么 |
|------|--------|
| **机械检查** | 数字是否遗漏 / 符号是否缺失 / 术语是否符合术语库 / 格式是否规范 |
| **语义审查** | 错译、漏译、翻译腔、用词不当、句式杂糅、语域不一致 —— 六维度 35 项逐一过 |
| **术语查证** | 专业术语自动联网查标准译法 |
| **生成校对稿** | Word 文档，段落高亮 + 批注说明问题 + 修改建议 |
| **生成校对报告** | Word 报告，按严重度分级、分类统计、逐条明细 |

---

## 2. 环境要求

### 软件

- **Python 3.10+**
- **任一支持的 Agent**：Claude Code / Codex / Gemini CLI / Copilot CLI

### Python 依赖

```bash
pip install python-docx openpyxl lxml PyMuPDF
```

### 术语库（可选）

术语库是 Excel 或 JSON，存放专业术语的英文→中文标准译法。没有也行——没有术语库时只跳过术语检查，其他维度照常。

自带一份 2800+ 条医学术语库（`glossaries/` 目录下），涵盖医美、医疗器械、临床试验等领域。

---

## 3. 安装

### 方式一：GitHub 下载（推荐，能自动更新）

```bash
# 1. 克隆仓库
git clone https://github.com/Mx766/MRS-workSpace.git
cd MRS-workSpace

# 2. 创建软链接到 Agent 的 skills 目录
# Claude Code：
ln -s "$(pwd)/skills/proofread-docx" ~/.claude/skills/proofread-docx

# Codex：
ln -s "$(pwd)/skills/proofread-docx" ~/.codex/skills/proofread-docx

# Gemini CLI / Copilot CLI（通用路径）：
ln -s "$(pwd)/skills/proofread-docx" ~/.agents/skills/proofread-docx
```

以后执行 `git pull` 即可更新，无需重新安装。

### 方式二：下载打包文件

从 [Releases](../../releases) 下载 `proofread-docx-v1.0.0.zip` 或 `.tar.gz`，解压到 Agent 的 skills 目录：

```bash
unzip proofread-docx-v1.0.0.zip -d ~/.claude/skills/proofread-docx/
```

### 方式三：一键安装脚本

```bash
bash install.sh                   # 自动检测 Agent 类型
bash install.sh --runtime codex   # 指定 Agent 类型
bash install.sh --runtime all     # 安装到全部可用的 Agent
```

### 验证安装

新开 Agent 会话，输入：

> 帮我校对翻译文件

如果 Agent 开始按步骤执行（环境检查 → 文件配对 → 机械检查 → 语义审查 → …），说明安装成功。

---

## 4. 快速上手

### 4.1 准备文件

```
我的项目文件夹/
├── report_EN.docx          ← 英文原文（无语言后缀 = 原文）
├── report_CHN.docx         ← 中文译文（_CHN 后缀 = 译文）
└── _术语要求.xlsx          ← （可选）客户指定术语
```

**命名规则**：

| 角色 | 命名方式 | 示例 |
|------|---------|------|
| 原文 | 无语言后缀 或 `_ENG`/`_EN` | `report.docx`, `report_ENG.docx` |
| 译文 | `_CHN`/`_CN`/`_ZH` | `report_CHN.docx` |
| PDF 原文 | `.pdf` | `report.pdf`（译文仍是 `.docx`） |

### 4.2 启动校对

把项目文件夹路径发给 Agent：

> 校对 `D:\我的项目文件夹\` 里的翻译

Agent 会自动：
1. 配对原文和译文
2. 拆分为段落
3. 执行机械检查
4. 分批逐段语义审查（每 15 段一批，100% 覆盖）
5. 生成 Word 校对稿（高亮 + 批注）
6. 生成 Word 校对报告

### 4.3 查看结果

```
我的项目文件夹/
├── report_EN.docx
├── report_CHN.docx
└── v1/                              ← 自动创建
    ├── report_CHN_校对稿.docx       ← 给译者看的（高亮 + 批注）
    └── report_CHN_校对报告.docx     ← 给 PM 看的（统计 + 明细）
```

第二次校对同一项目会自动创建 `v2/`、`v3/`……每次独立，不覆盖。

---

## 5. 项目文件组织

```
翻译项目根目录/
│
├── [原文文件].pdf / .docx           ← 英文原文
├── [译文文件]_CHN.docx              ← 中文译文（必须 _CHN 后缀）
│
├── _术语要求.xlsx                   ← （可选）客户指定翻译
│   列：原文 | 译法要求 | 备注
│   例：test group | 试验组 | 客户强制要求
│
├── client_terms.json                ← （可选）JSON 格式同上
│   {"terms": {"test group": "试验组"}}
│
├── v1/                              ← 第 1 次校对输出
│   ├── *_校对稿.docx                ← 带批注的校对稿
│   └── *_校对报告.docx              ← 结构化校对报告
├── v2/                              ← 第 2 次校对输出
│   └── ...
└── _修订记录/                       ← （可选）翻译公司修订稿存档
```

---

## 6. 运行校对

### 基础用法

```
帮我校对 D:\projects\medical-translation\ 里的翻译文件
```

### 指定术语库领域

如果知道文档属于某个特定医学领域，可以限定术语检查范围，减少假阳性：

```
校对这批文件，术语库领域用"医学-皮肤美容"
```

可选领域（当前术语库已分类）：
`医学-皮肤美容` / `医学-器械` / `医学-临床试验` / `医学-实验室` / `医疗器械` / `MRI` 等

### 多文件批次

一个文件夹下有多个原文-译文对时，Agent 会一次处理全部：

```
我的项目/
├── report1_EN.docx  →  report1_CHN.docx
├── report2_EN.docx  →  report2_CHN.docx
└── report3_EN.docx  →  report3_CHN.docx
```

输出会分别生成校对稿和报告，并自动执行跨文件术语一致性检查。

---

## 7. 理解校对结果

### 校对稿（给译者）

Word 文档，包含：

- **黄色高亮**：问题所在位置
- **右侧批注**：问题说明 + 修改建议，按严重度分色
  - 🔴 Critical：必须修改（错译、漏译、事实错误）
  - 🟡 Medium：建议修改（用词不当、翻译腔、术语不一致）
  - 🟢 Low：可选优化（风格微调、冗余）

批注格式示例：

```
[一.1.4 错译] [高]
原文: without the written permission of...
译文: 未经CLASSYS Inc.书面允许...
问题: "permission"译为"允许"不当，正式法律语境应为"书面许可"
建议: 改为"未经CLASSYS Inc.书面许可"
```

### 校对报告（给 PM）

Word 文档，包含：

1. **概览**：总问题数、严重度分布、覆盖率
2. **按维度分类**：忠实度 / 表达规范 / 术语合规 / 格式 各多少条
3. **按严重度明细**：Critical → Medium → Low 逐条列出
4. **机械检查参考**：数字/符号/术语违规的原始检查结果
5. **术语入库建议**：新发现的术语及建议译法

---

## 8. 进阶功能

### 8.1 客户指定术语（Fix E）

客户要求特定词必须按指定方式翻译时，在项目目录下放置 `_术语要求.xlsx`：

| 原文 | 译法要求 | 备注 |
|------|---------|------|
| test group | 试验组 | 客户强制 |
| adverse reaction | 不良反应 | GCP 术语 |
| investigational device | 试验器械 | 区别于 commercial device |

这些术语的优先级高于任何术语库。一旦译文不匹配，直接标为 🔴 Critical。

**支持格式**：
- Excel: `_术语要求.xlsx`（列名自动识别：原文/译法要求/备注）
- JSON: `client_terms.json`（`{"terms": {"src": "tgt"}}`）

### 8.2 全文档模式传播（Fix D）

Agent 在审查中发现"副反应→不良反应"这类术语修正后，会**自动全文扫描**所有出现"副反应"的地方——即使是后文没有逐段审查到的段落，也会补报。

不需要任何额外操作，Phase 4 结束后自动执行。补报的问题会标注 `[模式传播]`。

### 8.3 跨文件术语一致性

同一批次的多个文件之间，自动检查同一英文术语是否用了不同中文译法。比如文件 A 翻译为"白种人"，文件 B 翻译为"高加索人"——会被标记为不一致。

### 8.4 术语库维护

新增术语到术语库：

1. 编辑 `glossaries/术语库_标准格式.xlsx`
2. 运行 `python scripts/load_glossary.py --auto-scan`
3. 提交 git

---

## 9. 常见问题

### Q: 报告里上百条术语违规，都是假阳性？

**原因**：术语库领域与文档不匹配（如医学术语库用于网络安全文档）。

**解决**：
1. 校对时指定领域：`术语库领域用"医学-临床试验"`
2. 如无可匹配领域，Agent 会自动执行三层过滤，过滤后通常只剩 ≤30% 的条目
3. v2.12 后假阳性强制过滤才进报告，不会再出现大批量误报

### Q: 符号缺失提示找不到在哪？

**原因**（v2.13 已修复）：旧版只报"符号≥缺失"，不给位置。加上译者可能用了 `>=`（等效写法），精确匹配误报。

**解决**（v2.13）：
- 每个符号缺失现在附带原文上下文，可以定位
- 常见等效写法（≥↔>=、≤↔<=、±↔+/- 等）不再报缺失

### Q: 目录指出要改的词，后文出现了没再报？

**原因**：分批审查时每批 Agent 不知道其他批发现了什么。

**解决**（v2.13）：Phase 4 结束后自动执行模式传播，全文扫描补报（见 [8.2](#82-全文档模式传播fix-d)）。

### Q: 校对稿在 WPS 里看不到批注？

WPS 的批注渲染需要完整的 OOXML 范围标记，v6 已修复。如仍有问题，请检查是否用的最新版。

### Q: 能校对其他语言吗？

当前仅支持 EN→ZH（英语→中文）。其他语言方向需要修改检查清单和 prompt。

### Q: PDF 原文准不准？

PDF→DOCX 跨格式校对受 PDF 文本提取质量影响，数字/符号检查假阳性率较高（>90%），报告会标注"跨格式匹配，仅供参考"。建议优先使用 DOCX 原文。

---

## 10. 更新 Skill

### Git 安装方式

```bash
cd MRS-workSpace
git pull
# 无需其他操作，软链接自动指向最新代码
```

### 手动安装方式

重新下载最新打包文件，覆盖原有目录。

---

## 附录：涉及脚本一览

| 脚本 | 用途 |
|------|------|
| `pair_files.py` | 文件配对（原文↔译文） |
| `split_docx.py` | 段落拆分 |
| `check_mechanical.py` | 机械检查（数字/符号/术语/格式） |
| `filter_glossary_violations.py` | 术语违规假阳性过滤 |
| `filter_number_issues.py` | 数字误报过滤 |
| `propagate_patterns.py` | 全文档模式传播（v2.13 新增） |
| `check_cross_file_terms.py` | 跨文件术语一致性 |
| `write_comments.py` | 校对稿批注写入 |
| `write_report.py` | 校对报告生成 |
| `load_glossary.py` | 术语库 + 客户术语加载 |
| `search_term.py` | 未匹配术语联网查证 |
| `fix_target_quotes.py` | 批注定位修复 |
| `classify_glossary.py` | 术语库领域分类 |
