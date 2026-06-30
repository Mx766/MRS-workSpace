---
name: proofread-docx
description: Use when asked to proofread outsourced translation files — "校对翻译", "检查外包稿件", "审校译文". Use when given a folder containing original documents (no language suffix) paired with translated documents (carrying _CHN/_ENG/_JPN etc. suffixes). Use when the task involves comparing source and translated Word/Excel/PDF files for quality assurance.
---

# 翻译校对工作流

## 概述

对外包返回的翻译稿件执行系统化校对。**脚本做机械检查，Agent 做语义判断。** 只写批注不修改原文。

## 前置条件（BEFORE ANYTHING ELSE）

开始校对前，**必须**确认以下环境就绪，否则后续所有步骤都会失败：

```
1. Python 3.9+ 可用
2. 依赖已安装（否则装完再继续）:
   pip install python-docx openpyxl PyMuPDF
3. 确认 skill 目录结构完整:
   SKILL.md 所在目录/scripts/ 下有全部 .py 文件
```

执行验证命令：
```bash
python -c "import docx, openpyxl; print('deps ok')"
```

**若失败**：先 `pip install python-docx openpyxl PyMuPDF`，确认通过后再进入 Phase 0。

**Skill 根目录** = SKILL.md 所在目录。所有脚本路径 `${SKILL_ROOT}/scripts/xxx.py`。

---

## 硬约束（不可跳过）

| # | 规则 | 违反后果 |
|---|------|----------|
| **0** | **开发日志先行——任何改动前先写 devlog，所有改动记入 devlog** | 改完就忘 → 脚本与文档不一致 → 同一个 bug 反复出现 |
| 1 | **只写批注，不修改原文** | 人工无法回溯原始译文 |
| 2 | **每条疑点必须引用原文+译文** | 无引用的疑点 = 不可复核 = 无效 |
| 3 | **先跑脚本，再做判断** | Agent 重复做机械对比 → 漏检 + 误判 |
| 4 | **一章一章来，不混排** | 上下文溢出 → 跨章信息串扰 |
| 5 | **术语必查证，不凭空猜** | 编造术语 = 专业事故 |
| 6 | **脚本报错必须处理，不能跳过** | 脚本挂了后面数据全错 |

---

## 完整流程（Phase 0→7，顺序执行，不可跳步）

```
Phase 0: 环境就绪 + 术语库加载
	   ↓
Phase 1: 文件配对（脚本）
	   ↓
Phase 2: 文档拆分（脚本）
	   ↓
Phase 3: 机械检查（脚本）
	   ↓
Phase 3.5: 上下文注入（脚本）← v2.14 新增
	   ↓
Phase 4: 逐章校对（Agent）← 最核心，耗时最长
	   ↓
Phase 4.4: 严重度校准（脚本）← v2.14 新增
	   ↓
Phase 4.5: 跨文件术语一致性（脚本 + Agent）← 仅多文件批次
	   ↓
Phase 4.6: 全文档模式传播（脚本 + Agent）
	   ↓
Phase 5: 未匹配术语查证（Agent + 脚本）
	   ↓
Phase 6: 批注写入（脚本）
	   ↓
Phase 7: 生成报告（脚本）
```bash
python -c "import docx, openpyxl; print('ok')"
```

### 0.2 加载术语库

```bash
python ${SKILL_ROOT}/scripts/load_glossary.py --auto-scan
```

自动扫描 `${SKILL_ROOT}/glossaries/` 下所有 .xlsx/.csv 文件。

**输出解读**:
- `status: "ok"` → 有术语库，记录 `total_terms` 数量
- `status: "no_glossary"` → 无术语库，**这是允许的**。跳转到 Phase 1，后续 Phase 3/4 仅跳过术语检查维度，其他维度照常进行

**如果用户额外指定了术语库路径**：
```bash
python ${SKILL_ROOT}/scripts/load_glossary.py --auto-scan --glossary-dir "/path/to/extra/glossaries"
```

---

### 0.3 术语库双格式管理（铁律——不可违反）

术语库同时维护两种格式，**两者必须随时同步**：

| 格式 | 路径 | 用途 | 使用者 |
|------|------|------|--------|
| **Excel** | `glossaries/术语库_标准格式.xlsx` | 人类可读、可编辑 | 人类检查/审核/手动修改 |
| **JSON** | `glossaries/glossary.json` | AI 可读、快速加载 | `check_mechanical.py` / `load_glossary.py` |

**Excel 列结构**：`英文术语 | 中文译法 | 处理方式 | 领域 | 备注 | 入库时间`

**同步规则**：

```
Excel ──[load_glossary.py]──→ JSON       ← 每次 Phase 0 自动生成
JSON ──[classify/Agent]────→ JSON 更新   ← 领域分类、修正
JSON ──[写回脚本]──────────→ Excel       ← 分类完成后必须同步回 Excel
```

**何时写回 Excel**：
- Agent 完成术语领域分类后
- 手动修正术语领域标签后
- 新增术语入库后

### 0.4 版本目录检测（每次运行必须执行）

Phase 0 启动时必须检测输出目录的版本号，**禁止手动指定或跳过**：

```bash
# 自动检测：扫描 proofread/<批次>/ 下已有 v<N>/ 目录
ls -d proofread/1/v*/ 2>/dev/null | sort -V | tail -1
# 新版本号 = 最大已有版本号 + 1（无则从 v1 开始）
```

| 规则 | 说明 |
|------|------|
| **自动递增** | `VERSION = max(existing v{N}) + 1`，首次运行 = 1 |
| **全流程统一** | Phase 6/7 输出路径统一为 `proofread/<批次>/v<VERSION>/` |
| **严禁行为** | ❌ 输出到批次根目录（如 `proofread/1/`）  ❌ 手动指定版本号  ❌ 文件名加版本后缀 |

**Agent 必须**：Phase 0 结束时记录 `VERSION=N`，Phase 6/7 的 `--output` 参数必须指向 `proofread/<批次>/v<N>/` 目录。

### 0.5 客户术语需求检测 `2026-06-29 新增`

**背景**：客户可能要求特定词必须译为指定译法（如"test group"→"试验组"）。这些需求优先级高于术语库。

Phase 0 必须扫描批次目录下是否存在客户术语需求文件：

| 检测文件名 | 格式 |
|-----------|------|
| `_术语要求.xlsx` | Excel：`原文` / `译法要求` / `备注` |
| `client_terms.json` | JSON：`{"terms": {"src1": "tgt1", ...}}` |

```bash
# Phase 0 检测（由 load_glossary.py 提供）
python -c "
from scripts.load_glossary import find_client_glossary
path = find_client_glossary('proofread/<批次>/')
print(path or '未找到客户术语文件')
"
```

**如果找到**：
1. 加载客户术语，记录条数
2. Phase 3 `check_mechanical.py` 传 `--client-glossary <path>`
3. 客户术语违规标记为 `type: "client_glossary_violation"`，severity=critical
4. Phase 4 检查清单优先执行 4.0 客户术语合规

**如果未找到**：正常流程，无额外步骤。

- 任何对 `glossaries/glossary.json` 的修改之后

**写回命令**（示例）：
```bash
python -c "
import json, openpyxl
gl = json.load(open('glossaries/glossary.json'))
domain_map = {v['source']: v.get('domain','通用') for v in gl['terms'].values()}
wb = openpyxl.load_workbook('skills/proofread-docx/glossaries/术语库_标准格式.xlsx')
ws = wb.active
for row in range(2, ws.max_row+1):
    src = ws.cell(row, 1).value
    if src and src in domain_map:
        ws.cell(row, 4).value = domain_map[src]
wb.save('skills/proofread-docx/glossaries/术语库_标准格式.xlsx')
"
```

**验证同步**——每次更新后必须跑：
```bash
python -c "
import json, openpyxl
from collections import Counter
gl = json.load(open('glossaries/glossary.json'))
wb = openpyxl.load_workbook('skills/proofread-docx/glossaries/术语库_标准格式.xlsx')
ws = wb.active
json_domains = Counter(v.get('domain','?') for v in gl['terms'].values())
xlsx_domains = Counter()
for row in range(2, ws.max_row+1):
    xlsx_domains[ws.cell(row, 4).value or '通用'] += 1
assert json_domains == xlsx_domains, f'MISMATCH!\nJSON: {json_domains}\nXLSX: {xlsx_domains}'
print('OK: JSON and Excel in sync')
"
```

**教训**：Agent 只更新了 JSON 缓存没写回 Excel，导致人类检查时 Excel 仍显示全"通用"——浪费了分类工作。**JSON 的修改不算完成，直到 Excel 也同步更新。**

---

```bash
python ${SKILL_ROOT}/scripts/pair_files.py --input-dir "<用户给定的目录>"
```

**脚本输出是唯一定价**——Agent 不得手动配对、手动猜方向。

输出示例：
```json
{
  "pairs": [
    {"source": {"filename": "报告.docx", "fullpath": "...", "format": "docx"},
     "target": {"filename": "报告_CHN.docx", "fullpath": "...", "lang_name": "中文", "format": "docx"}}
  ],
  "stats": {"total_pairs": 3, "orphan_originals": 1, "orphan_translations": 0}
}
```

**必须向用户确认**：
```
已配对 N 组文件:
  1. 原文→中文: 报告.docx ←→ 报告_CHN.docx
  2. ...

孤立文件（未配对）: [...]
确认开始校对？(输入 y 继续)
```

**若 `total_pairs == 0`**：向用户报告"未找到可配对文件"，列出原因，**停止流程**。

---

## Phase 2: 文档拆分

对每对文件执行：

**Word**:
```bash
python ${SKILL_ROOT}/scripts/split_docx.py --input "<译文文件路径>"
```
对原文也执行同样拆分，两边章节数/标题应对齐。

**Excel**:
```bash
python ${SKILL_ROOT}/scripts/split_docx.py --type xlsx --input "<译文文件路径>"
```

**PDF 原文**:
```bash
python ${SKILL_ROOT}/scripts/split_docx.py --type pdf --input "<原文PDF路径>"
```

**拆分后向用户汇报**：
```
文件 "报告_CHN.docx": 拆分为 18 章（按 H1/H2 标题）
文件 "报告.docx" (原文): 拆分为 18 章
跨页表格警告: 3 处（详见输出）
```

**若拆分失败**（脚本返回 error）：不要强行继续。报告错误给用户，询问是否换手动拆分方式。

---

## Phase 3: 机械检查

```bash
python ${SKILL_ROOT}/scripts/check_mechanical.py \
  --source "<原文路径>" \
  --target "<译文路径>" \
  --glossary "<Phase 0 输出的 glossary JSON 路径>" \
  --direction "en→zh"
```

**重要**：`--glossary` 参数：如果 Phase 0 返回 `status: "no_glossary"`，则省略此参数。

**脚本输出结构**（Agent 必须理解）：
```json
{
  "number_mismatches": [{"paragraph_index": N, "type": "number_missing|decimal_mismatch|...", "severity": "critical|medium|low", ...}],
  "symbol_issues": [{"paragraph_index": N, "type": "symbol_missing|cas_missing|punctuation_mixed|...", "severity": "critical|medium|low", ...}],
  "glossary_violations": [{"paragraph_index": N, "source_term": "...", "expected_target": "...", ...}],
  "format_issues": [{"type": "heading_count|table_count|table_rows|bold_loss|...", ...}],
  "unit_issues": [...],
  "range_stats": {"dash": N, "tilde": N, "chinese": N},
  "range_consistency_warning": "..." or null,
  "summary": {"total_issues": N, "by_severity": {"critical": N, "medium": N, "low": N}}
}
```

**Agent 行动**：记录 `summary.total_issues` 和 `range_consistency_warning`。将此输出留存，Phase 4 每章加载时引用对应段的疑点。

### 3.1 机械检查数据契约（重要）

Phase 3 输出与 Phase 4 输出**字段名不同**，Phase 6/7 消费端已做归一化处理，但新增脚本时需注意：

| 字段用途 | Phase 3 字段名 | Phase 4 字段名 |
|----------|---------------|---------------|
| 问题类型 | `type` (如 `number_missing`) | `check_item` (如 `1.4 错译`) |
| 原文引用 | `source_value` / `source_term` | `source_quote` |
| 译文引用 | `expected_target` | `target_quote` |
| 问题描述 | `check` (描述+建议合一) | `issue` (仅描述) + `suggestion` |
| 段落定位 | `paragraph_index` | `paragraph_index` + `chapter` |

### 3.2 术语库领域过滤（关键——防止大规模假阳性）

> **实测教训**：2772 条跨领域术语库对医美文档做机械检查，产生 60 条 `glossary_violation`，经核实 **60 条全部为假阳性**。根因：同一英文词在不同医学子领域有完全不同的正确译法。

**领域错配示例**：

| 英文 | 术语库领域 | 术语库译法 | 本文领域（医美） | 本文正确译法 |
|------|-----------|-----------|-----------------|-------------|
| arm | 激光设备 | 导光臂 | 解剖/治疗 | 手臂/臂部 |
| monitor | 临床监查 | 监查员 | 设备操作 | 监视器（显示屏） |
| control | QC/质控 | 质控品 | 临床研究 | 对照/对照组 |
| protocol | 检测方法 | 测试方案 | 临床治疗 | 治疗方案 |
| cord | 设备线缆 | 软电线 | 解剖学 | （本文无此义） |

**术语库违规必须通过三层过滤才能成立**：

```
1. 源术语在原文中存在？
   ├─ 否 → 跳过（假阳性：术语库太宽泛，本文不涉及此术语）
   └─ 是 → 进入第 2 层

2. 预期译文在 DOCX 中存在？
   ├─ 是 → 跳过（术语已正确翻译）
   └─ 否 → 进入第 3 层

3. 本文字段中该术语的实际译法是否错误？
   ├─ 译法对（同词异域）→ 跳过（如 arm 在医美文里译"手臂"是正确的）
   ├─ 译法存疑 → 降级为 low severity + 标注"需人工判断领域适用性"
   └─ 译法确实错 → 保留为 medium/critical
```

**执行规则**：

- Phase 3 机械检查 `glossary_violation` 必须携带 `domain` 字段，Agent 在 Phase 4 中逐条复核领域适配性
- 术语库加载时优先按文档领域过滤：先识别文档领域（医美/医疗器械/临床试验/MRI/…），仅加载同领域术语
- 发现术语库领域与文档领域完全不匹配时（如 MRI 术语库用于医美文档），**整个 glossary_violation 类别可标记为"领域不匹配，跳过"**
- `write_report.py` 对 glossary_violation 单独归类，标注"全文匹配 + 领域待确认"

**代码支持**：
- `load_glossary.py` 支持 `--domain` 参数按领域过滤
- `${SKILL_ROOT}/scripts/filter_glossary_violations.py`：事后清洗脚本，对照 PDF 原文过滤假阳性

> ⚠️ **pi=0 问题处理**：Phase 3 跨格式（PDF→DOCX）全文匹配产生的 `paragraph_index=0` 问题无法精确定位到具体段落。
> 
> **处理流程（三步）**：
> 
> **Step 1 — 尝试定位**：
> ```bash
> # 通过 PDF 页码→DOCX 段落相似度映射，将机械问题分配到近似段落
> python ${SKILL_ROOT}/scripts/locate_by_pdf_page.py \
>   --pdf "<原文PDF>" --docx "<译文DOCX>" \
>   --issues "<issues.json>" --output "<issues_located.json>"
> ```
> 脚本自动：提取 PDF 每页文本 → 滑动窗口与 DOCX 段落做相似度匹配 → 搜索 source_value 在 PDF 哪一页 → 映射到 DOCX 段落 → 轮询分配（均匀分布，避免堆积在同一段）。
> 
> **Step 1b — 补全过短的 target_quote**（语义问题专用）：
> ```bash
> python ${SKILL_ROOT}/scripts/fix_target_quotes.py \
>   --issues "<issues.json>" --docx "<译文DOCX>" --output "<issues_fixed.json>"
> ```
> 自动从 DOCX 段落中搜索完整句子替换 "mm3"、"焦深" 等过短碎片。
> 
> **Step 2 — 分类处理**：
> - **pi ≥ 1（定位成功）**：`write_comments.py` 逐条写入对应段落，机械问题用简化格式 + `⚠️ [全文匹配]` 前缀，语义问题用完整格式 + 高亮
> - **pi < 1（仍无法定位）**：`write_report.py` 归入"机械检查参考"汇总统计（不逐条列出）；`write_comments.py` 按 type 合并为综合批注（每条类型一条），放在文档末尾
> 
> **Step 3 — 禁止**：全部堆在文档开头段落、全部静默丢弃、不经验证直接列入报告

### 3.3 Phase 3 已知假阳性模式（必须逐条核实）

> **实测教训**：跨格式（PDF→DOCX）场景下，`check_mechanical.py` 的数字和术语检查均产生 **100% 假阳性**（96/96 条）。Agent 必须核实以下四类已知误报，不可盲信脚本输出。

| # | 假阳性类型 | 示例 | 根因 | 处理 |
|---|-----------|------|------|------|
| **A** | DOI/标识符片段 | "10.1016"、"2016.03.012" | 文献标识符被当作可翻译数字 | `filter_number_issues.py` Pattern 过滤 |
| **B** | 日期成分 | "July 27" → 译为 "7月27日"，"27" 被认为缺失 | 日期格式转换后数字位置变化 | `filter_number_issues.py` Pattern 过滤 |
| **C** | 参考文献页码 | "164–71"、"262–9" 等引用页数 | 参考文献区的页码不是翻译内容 | `filter_number_issues.py` Pattern 过滤 |
| **D** | 领域错配术语 | "arm"→"导光臂"（激光设备），本文是医美 | 术语库涵盖多子领域，同一词译法不同 | `filter_glossary_violations.py` 三层过滤 |

**Agent 执行规则**：

- Phase 4 加载 Phase 3 机械疑点时，**先跑过滤脚本**（`filter_glossary_violations.py` + `filter_number_issues.py`），再对残留的做人工复核
- 跨格式场景下，默认假设 `glossary_violation` + `number_missing` + `decimal_mismatch` 三者假阳性率 >90%
- 只有同格式（DOCX↔DOCX）逐段对齐的结果可以直接采信
- 数字检查的可信场景：**测量值 + 单位**（如 "1.5 mm"、"60℃"），非独立出现的裸数字

### 3.4 强制过滤（铁律 I——不可违反）

> **v19 P2/P3 教训**：机械检查产出 113+99 条 glossary_violations，未经过滤直接进入报告，报告中术语违规章节全是假阳性。**机械检查原始输出禁止直接用于任何下游环节。**

**Phase 3 完成后，以下两步必须执行，不执行不得进入 Phase 4：**

```bash
# Step 3.4.1: 术语违规清洗 → 输出 cache/issues_glossary_filtered.json
python ${SKILL_ROOT}/scripts/filter_glossary_violations.py \
  --issues cache/issues_mechanical.json \
  --pdf "<原文PDF路径>" \
  --docx "<译文DOCX路径>" \
  --output cache/issues_glossary_filtered.json \
  --auto-remove

# Step 3.4.2: 数字/小数清洗 → 输出 cache/issues_number_filtered.json
python ${SKILL_ROOT}/scripts/filter_number_issues.py \
  --issues cache/issues_mechanical.json \
  --pdf "<原文PDF路径>" \
  --docx "<译文DOCX路径>" \
  --output cache/issues_number_filtered.json \
  --auto-remove
```

| # | 铁律 | 违反后果 |
|---|------|----------|
| **I** | **机械检查原始输出禁止直接用于报告** | 报告术语违规章节充斥假阳性（P2: 113条→0条真实, P3: 99条→0条真实），译者对报告失去信任 |
| **J** | **过滤后 glossary_violations 必须 ≤ 原始数量的 30%** | 若过滤后仍 >30%，说明术语库与文档严重不匹配，需 Agent 手动审查领域标签（见 3.2 三层过滤） |

**过滤后输出**：
- `cache/issues_glossary_filtered.json` — 清洗后的术语违规（供 Phase 4 复核 + Phase 7 报告）
- `cache/issues_number_filtered.json` — 清洗后的数字问题

**Phase 7 报告生成必须使用过滤后的文件**，禁止传原始 `issues_mechanical.json`。

---

### 3.5 上下文注入 `2026-06-30 新增`

> **背景**：同一份 SKILL.md + 同一批输入，不同 Agent/模型跑 Phase 4 结果差异巨大。实测 WorkBuddy 和本地 Claude 对同一文档的 Critical 发现重叠率仅 ~25%。根本原因是 Phase 4 的 AI 无确定的"注意力锚点"——不同模型关注不同的东西。

**Phase 3 完成后、Phase 4 之前，必须运行以下脚本**，为 Phase 4 预计算领域上下文和注意力锚点：

```bash
python ${SKILL_ROOT}/scripts/inject_context.py \
  --split-source cache/split_source.json \
  --split-target cache/split_target.json \
  --glossary glossaries/glossary.json \
  --pair-info cache/pair_info.json \
  --issues-mech cache/issues_mechanical.json \
  --output cache/phase4_context.json
```

**输出 `cache/phase4_context.json` 包含**：

| 字段 | 用途 |
|------|------|
| `domain` | 自动检测的文档领域（如"网络安全评估"、"医疗器械注册"）及置信度 |
| `key_terminology` | 源文中出现 ≥3 次的术语库术语 + 必须验证的译法 |
| `high_risk_paragraphs` | 高风险段落列表（含数字/术语/长句/比较逻辑） |
| `structure_checklist` | 结构完整性检查项（标题数、表格数、跨格式断段） |
| `mandatory_checks` | 基于领域+Phase 3 结果推导的不可跳过检查项 |
| `domain_escalation_rules` | 领域特定的严重度升级规则 |

此文件在 Phase 4 分批时将注入到每批的 prompt 中（见 4.1.0）。

---

## Phase 4: 强制分批逐段审查（Agent 核心）

**这是整个流程最关键的阶段。148 段必须逐段覆盖，一段不漏。不可跳段、不可扫读、禁止任何零 issue 章节。**

> **v18 教训**：Agent 宣称"逐段逐句对照"，实际 7/17 章零 issue、Ch13 55段仅3条。Agent 自我评估不可信——必须用机制保证覆盖。

### 4.1 强制分批机制

Phase 2 拆分出的全部段落按 **15 段一批** 切分，每批独立派发 Agent 审查，确保覆盖无死角。

#### 4.1.0 分批与派发

```
Step 4.0.0: 加载 cache/phase4_context.json（领域上下文 + 必检项 + 高风险段）← 新增
Step 4.0.1: 从 cache/split_target.json 读取全部段落（N 段）
Step 4.0.2: 按 15 段一批切分，生成批次清单
Step 4.0.3: 逐批运行 prepare_batch_prompt.py 富化 batch 数据：
  python ${SKILL_ROOT}/scripts/prepare_batch_prompt.py \
    --batch-data cache/batch_N_data.json \
    --context cache/phase4_context.json \
    --output cache/batch_N_prompt.json
Step 4.0.4: 逐批派发 Agent（model=fable），每批 prompt 必须包含：
  - 段落对（source + target）
  - Phase 3 机械检查疑点（对应段落）
  - DOMAIN CONTEXT（来自 phase4_context.json）
  - MANDATORY CHECK ITEMS（来自 phase4_context.json）
  - HIGH-RISK PARAGRAPH FLAGS（来自 phase4_context.json）
Step 4.0.5: 每批完成后合并 issues（含 dimension_coverage）
Step 4.0.6: 全部批次完成后校验覆盖率 → 100% 进入 Phase 4.4
```

**Batch Prompt 模板**（每批派发时必须包含以下结构）：

```
You are reviewing a [DOMAIN] document.
Domain notes: [DOMAIN_NOTES]

KEY TERMINOLOGY TO VERIFY (non-negotiable — these terms appear 3+ times):
  [source_term] → required: [required_target] (status: present/missing)

HIGH-RISK PARAGRAPHS in this batch: [paragraph_indices]
  (these contain numbers, units, or complex structures — scrutinize more carefully)

MANDATORY CHECKLIST ITEMS (every item below MUST be explicitly addressed in your output):
  [check_id] [name]: [reason why this is mandatory for this document type]

[EXISTING 34-ITEM CHECKLIST — see 4.2]

OUTPUT FORMAT REQUIREMENTS:
1. You MUST include "dimension_coverage" attesting you checked every single item
2. You MUST include "paragraph_coverage" for EVERY paragraph in this batch
3. Severity MUST follow the 14-rule decision table (see 4.4) — no personal judgment
4. Each issue MUST include "severity_justification" from the predefined enum
```

**跨格式特殊处理**：若 Phase 3 报告 `alignment_mode: cross_format_per_page`（原文 PDF + 译文 DOCX 不对齐），batch 数据中的 `_prompt_context.is_cross_format` 为 true。此时需注意：
- 机械检查疑点标记为 `[全文匹配，仅供参考]`
- PDF 文本提取可能遗漏表格/图片中的文字
- 检测 `structure_checklist` 中的断段提示（不以标点结尾的段落）

**批次切分规则**：
| 规则 | 说明 |
|------|------|
| 批次大小 | **15 段/批**（最后一批可能不足 15 段） |
| 跨章不断 | 同一批可以跨越章节边界，但不能中断连续性 |
| 段落编号 | 使用 `split_target.json` 中的全局 `index`（1-148），非章内编号 |

**覆盖追踪**（`cache/phase4_coverage.json`）：
```json
{
  "total_paragraphs": 148,
  "batches": [
    {"batch": 1, "paragraphs": [1,2,3,...15], "status": "done", "issues": 3},
    {"batch": 2, "paragraphs": [16,17,...30], "status": "done", "issues": 2},
    ...
  ],
  "coverage_pct": 100.0
}
```

#### 4.1.1 覆盖铁律（不可违反）

> **这些规则的存在就是为了防止 Agent 偷懒跳段。v18 的 7 章零 issue 就是违反这些规则的结果。**

| # | 铁律 | 违反后果 |
|---|------|----------|
| **E** | **禁止零 issue 批次** | 任何批次审查后 issue 数为 0 → 审查失败，必须换模型（fable→opus→sonnet）重审该批次。连续 3 个模型均为 0 才接受 |
| **F** | **每段必须输出结果** | 即使是"本段无问题"，也要在批次结果中显式标注 `{"paragraph_index": N, "status": "clean"}`。禁止整段跳过不留痕迹 |
| **G** | **覆盖率门禁** | `coverage_pct` 必须 = 100% 才能进入 Phase 5。少一段都不行 |
| **H** | **批次不可合并** | 禁止"这批和上批差不多，跳过"。每批必须独立完成完整的 34 项检查 |

#### 4.1.2 单批次审查规范

对每个批次的每一段，执行以下步骤：

```
Step A: 加载该批次的 source_text + target_text（从 split JSON 取）
Step B: 加载 Phase 3 中对应段落的机械检查疑点
Step C: 先执行 2.0 逐句通读（遮蔽原文，只读中文译文）
Step D: 命中红线信号 → 立即标记，反向定位根因 → 写 issue
Step E: 逐项执行六维度 34 项检查清单（见 4.2）
Step F: 将疑点追加到全局 issues 列表
Step G: 更新术语索引
```

**每段检查密度要求**：
- 短段（<50字）：至少检查 2.1/2.4/2.12/2.G1 四项
- 中段（50-200字）：至少检查全部 34 项
- 长段（>200字）：逐句拆分，每句独立检查全部 34 项

### 4.1.3 执行方式与回退

Phase 4 首选使用 Agent 工具（model=fable）逐批派发子代理审查。**若 Agent 工具报 model unavailable 错误**，按以下顺序回退：

1. **换模型重试**：依次尝试 `opus` → `sonnet` → 不指定 model
2. **若全部不可用**：主 Agent 自行执行审查——
   - 读入 `cache/split_target.json` 全部段落
   - 逐段对照六维度 34 项检查清单
   - 将问题按标准 JSON 格式写入 `cache/issues_phase4_new.json`
3. **不阻塞流程**：主 Agent 直审的结果与子代理审查等效，但同样受覆盖铁律约束

### 4.1.4 精度铁律（不可违反）

> **实测教训**：违反以下两条导致批注匹配率从 95% 跌到 49%，审查密度从 62 条跌到 35 条。

| # | 铁律 | 违反后果 |
|---|------|----------|
| **A** | **target_quote 必须从 DOCX 逐字复制，一字不改** | 加 `...` 省略号、改符号（℃→C）、改标点 → 字符串匹配失败 → bare ref 无高亮 |
| **B** | **每个子检查项独立出一条 issue，禁止合并** | "这句话有 3 个翻译腔问题"写成 1 条 → Phase 6 高亮只能标一处，报告密度缩水 |
| **C** | **target_quote 必须完整可用（≥10字，完整句子）** | 只摘 "mm3"、"焦深" 等碎片 → DOCX 中搜不到/无法精确定位 → 译者看不到位置 |
| **D** | **空字段不输出对应行（Phase 6 + Phase 7 均遵守）** | source_quote 为空仍输出 "原文: " → 批注/报告显示空白行，译者困惑。write_comments.py 和 write_report.py 均已内置动态行构建 |

**铁律 A 详解——target_quote 摘取规范**：

```
正确：从 cache/split_target.json 中找到对应段落的 target_text，原样复制
错误：手打、加省略号 "...文字..."、改符号 ℃→C、改标点
错误：包含多余上下文使匹配范围过大
正确：摘取恰好包含问题文字的最短连续子串（10-80 字为宜）
```

**验证方法**：每写完一条 issue，在译文 DOCX 对应段落中 Ctrl+F 搜索 target_quote，搜不到 = 必定失败。

**铁律 B 详解——一检查项一 issue**：

同一段译文的同一句话，分别检查 2.4/2.5/2.6/2.8/2.12/2.14/2.15，**每个命中项单独成条**。例如：

```
错误（合并写法，1 条）:
  "这句话口语化、导致带贬义、都可以太随意——综合建议改写"

正确（拆分写法，3 条）:
  [1] 2.4 口语化: "看不到改善" → "无明显改善"
  [2] 2.5 褒贬色彩: "导致" → "推动"
  [3] 2.6 近义词: "都可以" → "均可"
```

**铁律 C 详解——target_quote 完整性**：

```
正确：从 DOCX 段落中摘取完整的包含问题文字的句子（≥10字）
错误：只摘一个字/词/数字（如 "mm3"、"焦深"、"热损伤区域"）
错误：手写描述代替原文（如 "摘要（P140标题）"）
正确：写完后在 DOCX 对应段落 Ctrl+F 验证，搜不到 = 必定失败
```

**铁律 D 详解——空字段处理**：

Phase 6 `write_comments.py` 已按此规则实现：`source_quote` 为空时跳过"原文:"行，`target_quote` 为空时跳过"译文:"行，以此类推。**Phase 4 生成 issue 时仍需尽量填写所有字段**——空字段通常意味着跨段引用问题（如"P73 术语与 P22 不一致"），此时 source_quote 可留空，但不能为了让字段非空而填错误内容。

**执行清单**：每段译文的每一句，把 2.1-2.G4 的 34 个 checkbox 在脑中逐项打勾，命中就写一条，不命中就过。**禁止扫读模式（"这段写得不错，过"）。禁止跳过任何段落。**


### 4.2 六维度检查清单（逐段执行，必须全部覆盖）

对每段原文+译文对，按以下检查项逐条过。**每完成一项打 ✅，发现疑点记录后继续下一项。**

> **⚠️ 重要原则**：以下每一条都是独立的检查点。一段译文中可能同时存在多个问题——例如某段可能既有翻译腔（2.5）、又有用词不当（2.4）、还有术语不统一（4.1）。**必须逐条独立判断，不要因为发现了一个问题就跳过同段的其他检查项。**

---

#### 〇、客户术语合规（1 项） `2026-06-29 新增`

> **仅在 Phase 0 检测到客户术语需求文件时执行。此维度优先级最高，在所有其他检查之前执行。**

- [ ] 4.0 客户指定术语：此段原文中是否出现客户指定译法的术语？若出现，译文中是否正确使用了客户要求的译法？

**不可协商**：客户术语要求 > 术语库推荐 > AI 判断。客户说"test group"必须译为"试验组"，即使术语库允许"检测组"也不接受。

**检查方法**：
1. 读取 Phase 0 加载的客户术语列表
2. 对照每段原文，识别是否包含客户指定的术语
3. 若包含，译文必须使用客户要求的译法（一字不差）
4. 不匹配 → 立即标记为 critical，注明"客户要求：{source} → {required_target}"

---

#### 一、双语忠实度（9 项）

- [ ] 1.1 完整性：有无漏词、漏句、漏数字、整段缺译
- [ ] 1.2 增译：有无无依据增加的解释性文字
- [ ] 1.3 减译：有无删除原文限定词（only/approximately/at least/shall not）
- [ ] 1.4 错译：核心概念/因果关系/条件关系是否正确
- [ ] 1.5 指代：it/this/that/其/该 指代对象是否正确
- [ ] 1.6 双重否定：是否正确处理，是否误判为肯定
- [ ] 1.7 部分否定：not all 是否误译为"都不"
- [ ] 1.8 时态：过去/现在/将来/完成时是否正确传达
- [ ] 1.9 情态：must/shall(强制) vs should(建议) vs may/can(允许) 是否准确区分

---

#### 二、表达规范（34 项）

> **这是 AI 校对与人工校对差距最大的维度。必须逐项深度检查，不可走马观花。**

##### 2.0 逐句通读强制流程（不通顺第一道防线）

> **在对每段译文执行 2.A-2.G 检查清单之前，必须先完成以下通读步骤。此步骤不可跳过。**

对每段译文的**每个句子**执行：

1. **遮蔽原文**：不看英文原文，把译文逐句读一遍
2. **标记别扭句**：读起来需要停顿、回读、或"中文不会这么说"的句子 → 立即标记 `fluency_concern`
3. **反向定位根因**：对每个标记句，再看英文原文，判断根因（翻译腔/用词不当/句式杂糅/成分残缺/语义冗余）
4. **写 issue**：按根因归类到对应检查项下（2.C/2.D/2.F/2.G），各写一条

**红线信号（读到立即标记，不许思考、不许放过）**：

| 信号 | 说明 | 对应检查项 |
|------|------|-----------|
| 一句话读两遍才懂 | 必然有句式或翻译腔问题 | 2.D / 2.G |
| "的"字 ≥4 次 | 定语堆砌的强信号 | 2.14 |
| 句子 >80 字 | 中文单句极限，必有问题 | 2.20 |
| "进行/实现/发生/存在" + 动词 | 冗余动词，中文不这么说 | 2.G3 |
| 主语中途换了没过渡 | 话题链断裂 | 2.21 |
| "被"字句 | 被动直译嫌疑 | 2.13 |
| "当…时" + "如果/则/便" | 翻译腔叠 buff | 2.12 |

##### 2.A 错别字与标点（3 项）

- [ ] 2.1 错别字/拼写：中文错字/别字/繁简混用/衍文（多字）/漏字；英文拼写错误
- [ ] 2.2 标点体系：译文使用目标语标点——中文用 `，。；：、"''「」（）`，英文用 `,.;:""''()`。**逐句检查**：中英文括号是否混用（如中文句内出现 `(SMAS)` 应为 `（SMAS）`）、引号是否为中文引号
- [ ] 2.3 标点多余/缺失：句末漏句号、引号不成对、书名号用于非书名（如法规编号不应加《》）

##### 2.B 用词准确性（8 项）——逐词审视，不可扫读

- [ ] 2.4 口语化 vs 书面语：如"它会变性"→"会发生变性"、"看不到改善"→"无明显改善"、"没了"→"消失"。**医学/学术文献必须用书面语**
- [ ] 2.5 褒贬色彩（connotation）：如 "leading to" 译为"导致"（贬）还是"推动/促使"（中/褒）；"due to" 译为"由于"（中性）还是"得益于"（褒，用于正面结果）；"claim" 译为"声称"（带质疑色彩）还是"主张"
- [ ] 2.6 近义词混淆（易错对检查表）：
  - "避免"（avoid doing）vs "避开"（stay away from a thing）
  - "影响"（通常负面）vs "作用"（中性/正面）——"affect tissue" → "作用于组织"而非"影响组织"
  - "允许"（permit）vs "可/能够"（can）——"allows visualization" → "可直观显示"而非"允许直观显示"
  - "传递"vs"递送"vs"输送"——"deliver energy" → "传递能量"（标准术语）
  - "潜力"（potential for growth）vs "能力"（capability）——"healing potential" → "愈合能力"而非"愈合潜力"
  - "通常"（usually）vs "常规"（routinely）——"is routinely used" → "常规用于"而非"通常用于"
  - "程序"（procedure, software）vs "治疗手段"（treatment modality）——"skin tightening procedure" → "皮肤紧致治疗"而非"皮肤紧致程序"
  - **领域自适应近义词（根据文档类型判断，来自人工校对训练数据）**：
    - 医疗器械注册文档：「探头」→「治疗探头」、「受试者/求美者」→「患者」（监管用语）、「填充剂」→「皮肤填充剂」
    - MSDS/安全文档：「安全技术说明书」→「安全数据表」（GB/T 16483 标准用语）、「化学」→「化学药品/化学品」
    - 临床试验报告：「test group」→「investigational group」、「improvement rate」→「responder rate」、「blinded evaluation investigator」→「blinded evaluator」
    - 检测报告：「未污染已清洁」→「未污染的清洁」（机器翻译残留修复）、「接种试验Endozime的产品」→「接种了Endozime的受试产品」
- [ ] 2.7 动词-宾语搭配（collocation）：中文动词和宾语的搭配是否成立。如"测量了…评估和满意度"→ 测量不能搭配评估/满意度；"导致…产生离散间隔"→ 导致不能搭配空间排布。**每个动宾结构读一遍，不成立的就标**
- [ ] 2.8 修饰语-名词搭配：如"界限清晰的热损伤区域"→ 中文习惯"边界清晰"优于"界限清晰"；"能量源设备"→ "能量类设备"或"能量型设备"
- [ ] 2.9 介词/连词选用：如"与"vs"或"——在临床试验对照语境中，"compared with placebo" → "与安慰剂对照"（用"与"，表示对比），"ibuprofen or hydrocodone" → "布洛芬或氢可酮"（用"或"，表示选择）。**逐句确认 and/or/with/versus 的译法**
- [ ] 2.10 程度副词冗余/缺失：如"可能**有所**改善"（保留程度感）、"**显著**改善"（clinically significant → 不能漏"显著"）。**检查原文的程度修饰词是否在译文中正确传达**
- [ ] 2.11 范畴词：中文是否需要加范畴词（情况/状态/现象/过程/效果）。如"改善"→"改善效果"、"传递"→"传递过程"。**不是每个名词都需要范畴词，但医学文本中适当使用可提升自然度**

##### 2.C 翻译腔检测（7 项）——这是 AI 漏检最严重的区域

> **翻译腔** = 译文语法正确但读起来不像地道中文，保留了英文的句式结构/语序/虚词习惯。以下是最高频的 English→Chinese 翻译腔模式：

- [ ] 2.12 **"当…时"冗余**：英文 "When X, Y" → 中文经常不需要"当…时"。如 "当胶原蛋白暴露于60℃时，它会变性" → "胶原蛋白暴露于60℃时会发生变性"。**每个"当…时"都问一句：删掉是否更通顺？**
- [ ] 2.13 **被动语态直译**："is used/are treated/was approved" 一律译成"被使用/被治疗/被批准"。中文被动标记"被/让/叫/给/由/受/为…所"中，"被"带消极色彩。**每个被动句检查：能否用话题-述题结构替代？如"设备被用于治疗" → "设备用于治疗"**
- [ ] 2.14 **"的"字堆砌（>2 个"的"连用）**：英文 of/for/in 结构 → 中文"的"字连用导致定语过长。如"35例患者中有30例（86%）的眉部提升在临床上获得显著改善" → "35例患者中30例（86%）眉部提升获得临床上显著改善"。**每个段落数"的"字数量，有>3个"的"的句子重点审查**
- [ ] 2.15 **"使/让/令"冗余**：英文 "X allows/enables/causes Y to Z" → 中文"X使Y能够Z"。如"同时使周围组织不受影响" → "同时周围组织不受影响"（删"使"字即可）。"使"字过多是翻译腔的强信号
- [ ] 2.16 **"对于/关于/就…而言"句首冗余**：英文 "For/Regarding/As for X" → 中文常常省略或后置。如"对于RF设备，要达到高温，需要表面冷却" → "RF设备要达到高温，则需要表面冷却"
- [ ] 2.17 **"尽管…但/然而"结构直译**：英文 "Although X, Y" → 中文有时更适合"X，但Y"或直接陈述。如"尽管目前批准的适应症如下所列，但其他区域也已接受治疗" → "以下为目前获批的适应症，此外还在其他区域开展了治疗应用"
- [ ] 2.18 **"不同的"冗余**：英文 "different/various depths" → 中文"不同深度"中的"不同"有时冗余。如"可设定为不同深度" → "可设定以下深度"

##### 2.D 句法与流畅度（4 项）

- [ ] 2.19 **单读测试**：脱离原文，**把译文逐句读一遍，问自己：这是地道的中文吗？** 如果读起来别扭、需要回看英文才能理解 → 必然是翻译腔或句式问题 → 必须标记。**不要因为"语法对"就放过**
- [ ] 2.20 **长句拆分**：中文单句超过 60 字时，是否包含英文式嵌套结构（如长定语前置、多重从句压缩）。如果一句话需要反复读才能理解 → 标记，建议拆分
- [ ] 2.21 **主语-话题一致性**：中文偏好话题链（同一话题贯穿多个小句）。如果连续小句频繁切换主语，可能是照搬英文主谓结构。如"设备利用声波。较高的频率影响组织。较低的频率影响深层组织" → 话题从设备跳到频率，不连贯
- [ ] 2.22 **连接词自然度**：中文偏好意合（靠语义连接），英文偏好形合（靠连接词）。检查"因此/然而/此外/另一方面/与此同时"等是否过多——过多连接词 = 典型的翻译腔信号

##### 2.E 机器翻译残留检测（4 项）——来自人工校对训练数据的高频模式

> 机器翻译（MT）输出即使经过人工初校，仍会残留以下典型问题。**这些是人工校对最常修复的 MT 缺陷。**

- [ ] 2.23 **术语过于泛化（MT直译短词）**：MT 倾向于将专业术语直译为 2-3 字的字面义，缺少领域修饰语。如 "探头"（应为"治疗探头"）、"求美者"（应为"患者"）、"填充剂"（应为"皮肤填充剂"）、"安全技术说明书"（应为"安全数据表"，GB/T 16483 标准）。**每遇到短名词，问：这个领域是否有更规范的全称或修饰限定？**
- [ ] 2.24 **修饰语位置欧化**：MT 保留英文语序。如 "接种试验Endozime的产品" → "接种了Endozime的受试产品"、"所述条件的情况下" → "使用条件"。**多字定语前置时逐词检查语序是否通顺。**
- [ ] 2.25 **字面直译短语**：MT 逐词翻译产生的不通顺搭配。如 "未污染已清洁" → "未污染的清洁"、"联系"（contact）→ 在 MSDS 中应译为"联系方式/联系人"。**每个短句读一遍，不通顺就标——不需要对照英文。**
- [ ] 2.26 **英文/数字残留**：MT 可能漏译个别英文单词（articles、prepositions）、保留英文标号如 "(i)" "(ii)"、或残留孤立数字/页码。**逐段扫读，确认无孤立英文残留。**

##### 2.F 用词精确度增强（4 项）——翻译反馈驱动 `2026-06-29`

> **翻译反馈**：AI 漏检了大量"用词不准确"——词义大致对但不够精确。以下 4 项针对词义精度做深度检查。

- [ ] 2.F1 **词义范围偏差**：译词在语义场内但范围/侧重点不对。高频易错组：
  - **"改善" vs "改进" vs "提升" vs "增强"** —— "improve" 四个译法：症状/指标→改善，设计/方法→改进，性能/效果→提升，强度/表达→增强
  - **"显示" vs "表明" vs "呈现" vs "证明"** —— 影像/图像→显示，数据趋势→表明，临床表现→呈现，因果关系→证明
  - **"治疗" vs "疗法"** —— 具体治疗行为/次数→治疗，治疗方法体系→疗法
  - **"评估" vs "评价"** —— 临床数据/疗效→评估，主观判断/满意度→评价
  - **"显著" vs "明显" vs "大幅度"** —— 统计学意义→显著，肉眼可辨→明显，数量级变化→大幅度
  - **"不良反应" vs "副作用" vs "不良事件"** —— 药物→不良反应，操作/手术→副作用（日常语境），临床试验记录→不良事件（AE）
- [ ] 2.F2 **抽象名词过度直译**：英文抽象名词 → 中文应转为具体动词/短语。高频模式：
  - "application of X results in..." → 不是"X 的应用导致……"而是"施加 X 使……"
  - "the occurrence of AE" → 不是"不良事件的发生"而是"不良事件发生率"（如有数据）或"出现不良事件"
  - "the use of X allows..." → 不是"X 的使用允许……"而是"使用 X 可……"
  - "demonstration of efficacy" → 不是"有效性的证明"而是"证实了有效性"或"疗效验证"
  - **判断标准**："XX 的 YY"结构中，如果 YY 是动作名词（应用/使用/发生/证明/评估），转为动词更通顺
- [ ] 2.F3 **语域一致性**：同一段落/章节内，用语正式程度应一致。不一致本身即标为 `wording_register`：
  - **人称指代**：前后都用"患者"还是混用"求美者/受试者/使用者"——根据文档类型锁定一个
  - **程度修饰**：前后都用"极其"还是混用"非常/很/极为"——学术文献应统一用正式的
  - **连接词**：前后都用"此外"还是混用"还有/另外/而且"——统一
  - **检查方法**：扫一眼段内是否有"风格突变"的词——一段中突然冒出一个口语词或超正式词
- [ ] 2.F4 **字面翻译 vs 语境翻译**：英文词在不同语境有不同约定译法，不可字面直译：
  - **"contact"**：MSDS/安全文档→"联系方式"，日常→"接触"
  - **"safety"**：器械注册数据章节→"安全性"（指标），操作说明→"安全"
  - **"procedure"**：医疗→"手术"或"治疗操作"，软件→"程序"，临床试验→"流程"
  - **"control"**：临床试验→"对照组"，实验室→"质控品"，工程→"控制"
  - **"site"**：临床试验→"研究中心"，注射/治疗→"部位"，解剖→"位置"
  - **判断标准**：打开术语库，看该文档的领域标签，选该领域下的译法

##### 2.G 不通顺增强（4 项）——翻译反馈驱动 `2026-06-29`

> **翻译反馈**：大量"读起来不通顺"的句子未被标记。AI 只检查了翻译腔模式（2.12-2.18），但成分残缺、句式杂糅、语义冗余这三类高频不通顺模式没有强制检查项。

- [ ] 2.G1 **成分残缺**：中文句子缺少必要的主语/谓语/宾语。MT 输出高频模式：
  - **介词短语当句子**："通过对组织进行加热"——不完整句，谁加热？加热后怎样？
  - **缺主语**："可实现紧致效果"——什么可实现？设备？治疗？
  - **缺宾语**："该设备用于治疗"——治疗什么？
  - **检查方法**：每个句子提取主谓宾主干，缺任何一个成分 → 标记 `incomplete_sentence`
- [ ] 2.G2 **句式杂糅**：两种句式的前后半强行拼在一起。高频模式：
  - "目的是为了……" → 应为"目的是……"或"是为了……"
  - "是由于……的原因" → 应为"是由于……"或"……的原因是……"
  - "基于……的基础上" → 应为"基于……"或"在……的基础上"
  - "涉及到……的问题" → 应为"涉及……"或"关系到……的问题"
  - **检查方法**：搜索"是为了/是由于/基于/涉及到"等词，看前后是否重复表达同一逻辑
- [ ] 2.G3 **语义冗余/啰嗦**：删掉多余的字词后更通顺。高频冗余模式：
  - **"进行" + 动词**：进行处理→处理，进行评估→评估，进行分析→分析
  - **"实现" + 动词**：实现了改善→改善了，实现提升→提升了
  - **"发生" + 动词**：发生变性→变性，发生坏死→坏死
  - **"存在" + 形容词**：存在着差异→有差异/不同
  - **"具有" + 属性**：具有重要性→重要，具有有效性→有效
  - **"不同的" + 名词**：不同的深度→不同深度（有时"不同的"冗余）
  - **检查方法**：**每句问一句：删掉"进行/实现/发生/存在/具有"后是否更通顺？是 → 标记 `redundant_word`**
- [ ] 2.G4 **逻辑连接断裂**：不看英文原文，译文句子之间的逻辑关系能否自然理解？
  - **意合断裂**：两句话放在一起，读者需要脑补因果关系/转折关系/递进关系才能懂它们在说什么
  - **话题跳跃**：前一句在说 A 的效果，后一句突然说 B 的参数，中间没有过渡
  - **检查方法**：遮蔽原文，只读译文的连续 3-5 句。如果中间有"为什么会说到这个"的困惑 → 标记 `logic_gap`
  - **注意**：不是让你加连接词（2.22 已检查连接词过多），而是句子本身的逻辑顺序/信息排布是否合理

---

#### 三、数字符号单位（6 项）

> 优先复核 Phase 3 脚本疑点

- [ ] 3.1 数值：阿拉伯数字/百分比/小数是否一致
- [ ] 3.2 范围：1-5 / 1至5 全文统一的记录（Phase 6 做全局判断）
- [ ] 3.3 单位缩写：5 mg/kg 保留不译 ✅ / 全写：5 milligrams → 5 毫克。**特别注意复合单位**如 mg/kg² vs kg/m²（BMI单位常被写错）
- [ ] 3.4 专有名词：人名/公司/机构/产品名保留不译
- [ ] 3.5 法规编号：ISO/ICH/FDA/§ 编号完整
- [ ] 3.6 公式变量：上下标/符号/变量含义匹配

---

#### 四、术语合规（5 项）

- [ ] 4.1 术语库一致：术语库规定的译法是否遵守。**即使无术语库，也应根据文档类型主动判断**：
  - 医疗器械注册文档：检查"求美者→患者""探头→治疗探头""填充剂→皮肤填充剂"等监管用语是否规范
  - MSDS/GHS 文档：检查是否符合 GB/T 16483 标准（如"安全技术说明书→安全数据表"）
  - 临床试验报告：检查终点指标术语（如"improvement rate→responder rate""test group→investigational group"）
  - 检测报告/CoA：检查方法学术语、设备名称是否使用全称
- [ ] 4.2 **段内术语统一**：同一个英文术语在同一段内出现多次时，中文译法必须一致。如 thermal injury zone 不能前句译"热损伤区域"后句译"热损伤区"
- [ ] 4.3 **跨段术语统一**：同一个核心概念在不同段落中译法是否一致。**每校对完一段，在术语索引中记录 `{source_term: "thermal injury zone", target_term: "热损伤区", paragraph_index: N}`。遇到相同 source_term 但 target_term 不同时 → critical**
- [ ] 4.4 缩写规范：缩写首次出现是否标全称
- [ ] 4.5 跨领域区分：多义术语是否按文档领域选对译法

---

#### 五、格式排版（3 项，脚本为主 Agent 复核）

> Phase 3 脚本已做机械检查，Agent 仅复核脚本疑点 + 关注视觉问题

- [ ] 5.1 标题层级：H1/H2/H3 对应 + 编号一致
- [ ] 5.2 表格完整：行列数/合并单元格/表头/跨页表头重复
- [ ] 5.3 强调标记：加粗/斜体/下划线是否保留

---

#### 六、（跨章，Phase 6 执行）

> 此维度在当前章完成时收集数据，Phase 6 汇总检查

- 术语索引条目追加（每个 source_term → target_term 映射 + 首次出现段落）
- 相同段落译文记录追加
- 范围表达形式统计追加

---

### 4.3 输出格式（强制字段 + 覆盖率追踪）`2026-06-30 强化`

每批输出必须包含两部分：**A. 覆盖率声明** + **B. 疑点列表**。缺一不可。

> ⚠️ **target_quote 精度要求**：此字段用于 Phase 6 在 DOCX 中定位和高亮对应文字。必须从译文 DOCX 段落中**逐字原样复制**，不得加省略号、不得改符号、不得改标点。参见 [4.1.2 铁律 A](#412-精度铁律不可违反)。

**Section A: DIMENSION_COVERAGE（覆盖率声明）** — 34+1 项检查清单每项必须显式声明：

```json
{
  "dimension_coverage": {
    "0.客户术语合规": {"checked": true, "issues_found": 0},
    "1.1": {"checked": true, "issues_found": 1},
    "1.2": {"checked": true, "issues_found": 0},
    "1.3": {"checked": true, "issues_found": 0},
    "1.4": {"checked": true, "issues_found": 2},
    "...": "... (all 34+1 items must be present)",
    "5.3": {"checked": true, "issues_found": 0}
  },
  "paragraph_coverage": [
    {"paragraph_index": 1, "status": "clean"},
    {"paragraph_index": 2, "status": "issues_found", "issue_count": 2}
  ]
}
```

**Section B: ISSUES（疑点列表）** — 每条 issue 新增 `severity_justification` 字段：

```json
{
  "chapter": "Ch3",
  "paragraph_index": 12,
  "dimension": "一.双语忠实度",
  "check_item": "1.4 错译",
  "severity": "critical",
  "severity_justification": "changes_meaning",
  "confidence": "high",
  "source_quote": "<原文原句，不可截断>",
  "target_quote": "<译文原句，不可截断>",
  "issue": "<一句话说明问题>",
  "suggestion": "<具体修改建议>"
}
```

**severity 取值只有三个**：`critical` / `medium` / `low`
**confidence 取值只有三个**：`high` / `medium` / `low`
**severity_justification 必须从以下枚举中选择**：

| justification | 含义 |
|---------------|------|
| `changes_meaning` | 错译导致含义改变 |
| `missing_unit_conversion` | 单位换算错误 |
| `breaks_sentence_structure` | 句子结构破碎不可读 |
| `terminology_inconsistency` | 同一术语不同译法 |
| `connotation_mismatch` | 褒贬色彩/语域不当 |
| `unnatural_expression` | 语法正确但不地道 |
| `style_preference` | 正确但可更优 |
| `format_deviation` | 视觉/格式不一致 |

### 4.4 严重度决策表 `2026-06-30 强化`

**严重度不由主观判断，必须按以下优先级规则顺序匹配，命中即停。**

| # | 规则 | severity | 示例 |
|---|------|----------|------|
| 1 | 数值/单位错误（原文 6→译文 7，kg/m²→mg/kg²） | **critical** | Phase 3 数字疑点、测量值+单位 |
| 2 | 错译导致含义改变（医学/安全/法律） | **critical** | handpieces→"手机"（而非"手持件"） |
| 3 | 客户指定术语未满足 | **critical** | client_terms.json 要求但译文不匹配 |
| 4 | 术语前后不一致（同一概念不同译法） | **critical** | thermal injury zone 前译"热损伤区"后译"热损伤区域" |
| 5 | 句子结构破碎导致无法理解 | **critical** | 缺主语+动宾不配+词序混乱→读不通 |
| 6 | 褒贬色彩不当（导致/推动/促使 不当使用） | **medium** | compromise→"影响"应为"损害" |
| 7 | 翻译腔（被动直译、当…时、的堆砌、字面直译） | **medium** | attention is drawn to→"提请注意" |
| 8 | 近义词混淆（允许/可、程序/治疗、影响/损害） | **medium** | efficacy vs effectiveness 都译"有效" |
| 9 | 成分残缺/句式杂糅（但仍可理解） | **medium** | "不会影响或需要采取"主谓断裂 |
| 10 | 术语过于泛化（MT 将专科术语模糊化） | **medium** | penetration→"渗透"而非"穿刺" |
| 11 | 标点风格（中英文括号混用、双空格） | **low** | 中文使用英文括号 (like this) |
| 12 | 口语化表达（学术/正式档应用书面语） | **low** | "好多"、"搞"、"弄" |
| 13 | 格式微调（数字-单位空格、章节号格式） | **low** | "5.1标题" vs "5.1 标题" |
| 14 | 可有可无的修饰词增删 | **low** | "不同的手机"中"不同的"冗余 |

**Agent 赋值流程**：写出 issue → 从规则 1 顺序往下扫 → 命中的第一条规则就是严重度 → 把规则编号写入 `severity_justification`。不可跳过、不可凭感觉、不可用默认值。

### 4.5 逐段检查执行规范

> ⚠️ **核心纪律**：参见 [4.1.2 铁律 B](#412-精度铁律不可违反)——每个子检查项（2.1-2.26）命中后**独立成条**，禁止合并为"综合建议"。

**每段必须执行以下两轮，不可只做一轮：**

**第一轮：对照检查（14 项跨维度核心项）**
对着原文和译文，逐项检查 1.1-1.9（忠实度）+ 3.1-3.6（数字符号单位）+ 4.1-4.5（术语合规）。此轮关注"对不对"。

**第二轮：单读检查（34 项表达规范）**
离开原文，**只读译文**，逐项检查 2.1-2.G4。此轮关注"好不好"。读的时候问自己：
- 这句话像地道中文吗？
- 我能不看英文就完全理解吗？
- 有没有觉得某处"别扭但说不上来"？→ 那一定是翻译腔 → 标记

> **⚠️ 第二轮的常见陷阱**：读了几段之后会"习惯"翻译腔，不再觉得别扭。**每 5 段停下来重置语感**——脑中想一句地道中文（如新闻标题），再继续读下一段。

### 4.7 输出术语索引（跨文件一致性准备）

每完成一个文件的 Phase 4，**必须**输出该文件的术语索引供 Phase 4.5 跨文件比对：

```bash
# Agent 在完成单文件全部章节后，将其记录的术语映射写入 JSON
# 手动创建 cache/term_index_<file_prefix>.json，格式：
{
  "file": "[1]-CN.docx",
  "terms": {
    "Caucasian": {"target": "白种人", "count": 5, "first_para": 12},
    "thermal injury zone": {"target": "热损伤区", "count": 8, "first_para": 3}
  }
}
```

**收集规则**：
- 收录 Phase 4 中出现的所有**专业术语**（非通用词如"the/and/also"）
- 每个 source_term 记录其在本文中的译法 + 出现次数 + 首次段落
- 如果同一文件内同一 source_term 有多个译法（已在 4.3 中标记为 critical），记录**最后一个**译法 + 标注 `"intra_file_conflict": true`

---

### 4.6 严重度校准 `2026-06-30 新增`

> **背景**：不同模型对严重度的判断差异巨大。同一类问题（如近义词混淆），模型 A 标 critical，模型 B 标 low。严重度不一致导致译者无法区分哪些必须改、哪些可选改。此步骤用确定性规则消除模型间主观差异。

**Phase 4 所有批次完成后、Phase 4.5 之前运行**：

```bash
python ${SKILL_ROOT}/scripts/calibrate_severity.py \
  --issues cache/issues_phase4.json \
  --context cache/phase4_context.json \
  --phase3-issues cache/issues_mechanical.json \
  --output cache/issues_phase4_calibrated.json
```

**校准逻辑**：
1. **规则归一化**：按 4.4 节的 14 条决策表重新计算每条 issue 的严重度
2. **领域升级**：按 `phase4_context.json` 中的 `domain_escalation_rules`，特定领域的关键术语错误自动升一级
3. **低置信度降级**：confidence=low 且 severity=critical → 降为 medium（低置信度不配 critical）
4. **同类归一化**：同一 check_item 分组内，少数派严重度统一为多数派
5. **强制规则**：check_item 含"错译" → 强制 critical（不可被模型降级）

**输出**：
- `cache/issues_phase4_calibrated.json` — 校准后的 issues（原始字段 + `_calibration` 说明变更原因）
- `cache/phase4_flags.json` — 红旗清单：

| Flag 类型 | 含义 | Agent 行动 |
|-----------|------|-----------|
| `empty_dimension` | 某维度零 issue | 检查是否遗漏，特别是维度一（忠实度）和维度四（术语合规） |
| `phase3_phase4_mismatch` | Phase 3 发现大量问题但 Phase 4 零 issue | 该维度可能被跳过了 → 重审 |
| `high_risk_missed` | 高风险段落零 issue | 检查标记段落是否被遗漏 |
| `severity_justification_mismatch` | severity 与 justification 矛盾 | 修正严重度或 justification |

**Agent 根据 `phase4_flags.json` 决定**：
- `empty_dimension` 或 `phase3_phase4_mismatch` → 对缺失维度重新审查对应的批次
- `high_risk_missed` → 重点审查 top 10 个未覆盖的高风险段落
- 无 flags → 直接进入 Phase 4.5

**后续环节（Phase 4.5/Phase 4.6 全文档模式传播/Phase 6/Phase 7）必须使用校准后的 `issues_phase4_calibrated.json`**，不再使用原始 `issues_phase4.json`。

---

## Phase 4.5: 跨文件术语一致性检查 `2026-06-29 新增`

> **翻译反馈**："当时这批文件有三个，他在另一个文件里面翻的白种人"——同一批文件中同一英文术语译法不一致，人工校对后才发现的跨文件问题。

**触发条件**：同一批次校对包含 **≥2 个文件**时，在所有文件完成 Phase 4 后执行。

### 4.5.1 脚本自动比对

```bash
python ${SKILL_ROOT}/scripts/check_cross_file_terms.py \
  --index-dir "cache/" \
  --glossary "glossaries/glossary.json" \
  --output "cache/cross_file_issues.json"
```

脚本自动：
1. 收集 `cache/term_index_*.json` 中所有术语映射
2. 按 source_term 分组，找出跨文件译法不一致的术语
3. 排除同领域允许的多译法（查术语库 `处理方式` 字段）
4. 输出 `cross_file_issues.json`

### 4.5.2 Agent 复核

脚本输出后，Agent 逐条判断：

| 判定 | 条件 | 处理 |
|------|------|------|
| **真不一致** | 同一英文术语在同一批同类文件中用了不同中文 | 标为 `cross_file_term_mismatch`，severity=critical |
| **领域差异** | 不同文件属于不同领域，译法不同是合理的 | 标为 `domain_variance`，severity=low |
| **术语库多译法** | 术语库允许 2+ 种译法 | 跳过（不报） |

### 4.5.3 输出格式

```json
{
  "type": "cross_file_term_mismatch",
  "severity": "critical",
  "source_term": "Caucasian",
  "files": {
    "[1]-CN.docx": "白种人",
    "[2]-CN.docx": "高加索人"
  },
  "recommendation": "统一为'白种人'（文件[1]译法，出现 5 次）",
  "check_id": "cross_file.1"
}
```

### 4.5.4 合并到主 issues

跨文件一致性疑点合并到 `cache/issues_merged.json`，与其他 Phase 4 疑点一起进入 Phase 6 写入批注。写入时：
- 在**每个涉及的 DOCX 文件**中插入对应批注（标注"跨文件一致性"前缀）
- 如果某文件已存在该译法的术语库一致性批注 → 合并，不重复插入

---

## Phase 4.6: 全文档模式传播 `2026-06-29 新增`

> **背景**：翻译人员反馈"目录里指出 test group 应改，但后文出现了它就没再指出来"。
> Phase 4 分批机制中每批 Agent 独立审查，互不知晓。发现一个模式后必须全局扫描补报。

### 4.6.1 脚本自动传播

```bash
python ${SKILL_ROOT}/scripts/propagate_patterns.py \
  --issues cache/issues_phase4.json \
  --target cache/split_target.json \
  --min-confidence medium \
  --merge cache/issues_phase4.json
```

**逻辑**：
1. 从 `issues_phase4.json` 中提取"建议修改"模式（如"副反应"→"不良反应"、"书面允许"→"书面许可"）
2. 在 `split_target.json` 全文搜索每个模式的所有出现位置
3. 排除已有 issue 标记的段落（包括原始标记和同模式其他 issue 的标记）
4. 对未标记位置生成新 issue，标注 `"_propagated": true` + `"_source_pattern"` 追踪来源
5. 合并回原始 issues 文件

**传播范围控制**：
- 仅传播 confidence ≥ medium 的 issue 中提取的模式
- 模式提取要求 old_text 长度 ≥ 2 且 ≠ new_text
- 补报 issue 的 confidence 固定为 `medium`，severity 继承原始 issue

### 4.6.2 Agent 复核（可选）

脚本传播后，Agent 快速扫视新增的 `_propagated` issue：
- 确认 old_text 在所有上下文中确实是同一个问题（非领域差异）
- 排除合理例外（如目录 vs 正文的不同表达风格）
- 批量接受或拒绝传播结果

### 4.6.3 输出格式

```json
{
  "paragraph_index": 75,
  "dimension": "四.术语合规",
  "check_item": "4.3 跨段术语统一",
  "severity": "medium",
  "confidence": "medium",
  "issue": "前文已将「副反应」修正为「不良反应」，此处仍使用旧译法「副反应」，应统一",
  "suggestion": "将「副反应」改为「不良反应」",
  "_propagated": true,
  "_source_pattern": "副反应→不良反应"
}
```

---

## Phase 5: 未匹配术语查证

**仅在 Phase 3 + Phase 4 中发现术语库未覆盖的专业术语时执行。**

### 5.1 收集

汇总 Phase 3 `glossary_violations` 和 Phase 4 中标记的未知术语，去重，按出现频次降序排列。

### 5.2 查证

对每个未知术语调用查证脚本：
```bash
python ${SKILL_ROOT}/scripts/search_term.py --terms "term1" "term2" --format text
```

脚本按优先级尝试：术语在线(termonline.cn) → WHO → FDA → 通用搜索。

**⚠️ 注意**：`search_term.py` 依赖外部网络 API（`urllib.request.urlopen`）。在离线/沙箱环境中，所有后端均不可用，脚本将返回"无法查证"。此时应标记术语为"建议人工确认"，不阻塞流程。

### 5.3 询问入库

```
以下术语未在术语库中，已查证建议：

1. carboxyhemoglobin → 碳氧血红蛋白
   来源: 术语在线 | 置信度: 高 | 出现: 8 次

是否入库？(y=全部 / 编号如 "1,3" / n=都不)
```

---

## 输出命名规范（铁律——不可违反）

> **v18 教训**：校对稿和报告直接散落在 `proofread/1/` 根目录，没有建 `v18/` 文件夹。版本混乱，无法追溯。

| 产物 | 路径模板 | 示例 |
|------|---------|------|
| 版本目录 | `proofread/<批次>/v<N>/` | `proofread/1/v18/` |
| 校对稿 | `<版本目录>/<前缀>_校对稿.docx` | `proofread/1/v18/[1]-CN_校对稿.docx` |
| 校对报告 | `<版本目录>/<前缀>_校对报告.docx` | `proofread/1/v18/[1]-CN_校对报告.docx` |
| 中间产物（cache） | `cache/`（不编码版本） | `cache/issues_merged.json` |

**版本号规则**（Phase 0.4 自动执行）：
1. `N = max(已有 v{N} 目录编号) + 1`，无则从 1 开始
2. Phase 6/7 输出路径强制 `proofread/<批次>/v<N>/`

**严禁行为**：
| ❌ 禁止 | ✅ 正确 |
|--------|--------|
| 输出到 `proofread/1/` 根目录 | 输出到 `proofread/1/v18/` |
| 文件名加版本后缀 `_v18` `_final` `_clean` | 文件名不含版本信息 |
| 手动指定版本号 | Phase 0.4 自动检测 |
| 跳过版本检测（"反正是第一次"） | 每次运行必须检测 |

---

## Phase 6: 批注写入

将 Phase 3 + Phase 4 的所有疑点写入译文文件：

```bash
python ${SKILL_ROOT}/scripts/write_comments.py \
  --input "<译文文件路径>" \
  --issues "<合并后的issues.json>" \
  --output "<输出目录>/<文件名>_校对稿.docx"
```

### 6.1 批注渲染三路径

`write_comments.py` 根据 issue 类型自动选择渲染方式：

| 路径 | 触发条件 | 高亮 | 批注格式 |
|------|---------|------|---------|
| **语义-完整** | 无 `type` 字段（Phase 4 产出） | ✅ 有（匹配 target_quote） | `原文 → 译文 → 问题 → 建议`，空字段自动跳过对应行 |
| **跨文件一致性** | `type: "cross_file_term_mismatch"`（Phase 4.5 产出） | ❌ bare ref（文档开头） | `🌐 [跨文件一致性] → 英文术语 → 本文译法 vs 他文译法 → 建议统一` |
| **机械-定位** | 有 `type` 字段 + `paragraph_index ≥ 1`（经 PDF 映射定位） | ❌ bare ref | 简化格式：`⚠️ [全文匹配] → 原文 → check描述`，无"问题/建议"标签 |
| **机械-合并** | 有 `type` 字段 + `paragraph_index < 1`（无法定位） | ❌ bare ref（文档末尾） | 按 type 合并为综合批注，列出全部具体值 |

**判断逻辑**：`write_comments.py` 通过 `is_mechanical = bool(issue.get('type'))` 区分机械/语义问题，通过 `is_doc_level = (para_idx == -1)` 区分文档级/段落级。

**字段 fallback**：机械问题和语义问题的字段名不同，`write_comments.py` 使用 `_get(issue, 'source_quote', 'source_value', 'source_term')` 等链式 fallback 读取，确保两种格式都能正确显示。详见 [3.1 数据契约](#31-机械检查数据契约重要)。

### 6.2 颜色编码

- Word: 高亮疑点文字（critical=浅红/medium=浅橙/low=浅绿）+ 插入批注段落
- Excel: 单元格填充色 + Comment

**若写入失败**（如文件被占用）：报告错误，询问用户是否重试或换路径。

---

## Phase 7: 生成校对报告

```bash
python ${SKILL_ROOT}/scripts/write_report.py \
  --pair-info "<Phase 1 输出>" \          # 必传：缺则基本信息表空白
  --issues "<Phase 4 疑点 JSON>" \        # 必传：缺则问题清单为空
  --mechanical-report "<Phase 3 过滤后输出>" \  # 必传：必须用 cache/issues_glossary_filtered.json，禁止用原始 issues_mechanical.json
  --glossary-changes "<Phase 5 入库术语 JSON>" \  # 可选：无新增术语可省略
  --output "<输出目录>/<文件名>_校对报告.docx"
```

> ⚠️ `--pair-info` 和 `--mechanical-report` 缺一都会导致报告出现空白章节。`--pair-info` 所需字段见 [7.1 pair-info 格式](#71-pair-info-格式)。
> 
> ⚠️ **`--mechanical-report` 必须传过滤后的文件**（`issues_glossary_filtered.json`）。传原始 `issues_mechanical.json` 会导致报告术语违规章节充斥假阳性（铁律 I）。

### 7.1 pair-info 格式

`write_report.py` 从 pair_info 读取以下字段填充基本信息表：

| 路径 | 用于 | 缺失后果 |
|------|------|----------|
| `pairs[0].source.filename` | "原文文件"行 | 显示空 |
| `pairs[0].source.format` | 格式标注（如 PDF） | 无格式标注 |
| `pairs[0].target.filename` | "译文文件"行 | 显示空 |
| `pairs[0].target.lang_name` | "校对方向"行 | 显示空 |
| `glossary_files` | "使用术语库"行 | 不显示 |
| `total_paragraphs` | "文档总段数"行 | 不显示 |
| `chapter_count` | "校对章节数"行 | 不显示 |

Phase 1 `pair_files.py` 输出已包含 `source.filename` / `source.format` / `target.filename`，但 `target.lang_name` 为方向码（如 `en→zh`）非中文名。Agent 可在 pair_info 中补充 `target.lang_name` 为中文名（如"中文"）。若无 Phase 1 输出，手动构建最小 pair_info：

```json
{
  "pairs": [{
    "source": {"filename": "[1].pdf", "format": "pdf"},
    "target": {"filename": "[1]-CN.docx", "lang_name": "中文"}
  }],
  "glossary_files": ["术语库.xlsx"],
  "total_paragraphs": 148,
  "chapter_count": 17
}
```

输出：Word (.docx) 格式报告，含：
- 基本信息 + 颜色图例
- 问题统计表（按维度×严重度，表头红橙绿底色）
- critical / medium / low 三级问题清单
- 术语一致性报告
- 范围表达统一性检查
- 术语库变更记录

---

## 脚本失败处理

| 脚本 | 常见失败 | 处理方式 |
|------|----------|----------|
| load_glossary | 无术语库 | ✅ 允许，返回 no_glossary，跳过术语检查 |
| pair_files | 输入目录不存在 | ❌ 停止，请用户确认路径 |
| pair_files | total_pairs=0 | ❌ 停止，报告无配对文件 |
| split_docx | python-docx 未安装 | ❌ 停止，先 pip install |
| split_docx | 文件损坏/格式不支持 | ❌ 报告具体文件，跳过该对 |
| check_mechanical | 原文/译文格式不一致 | ⚠️ 报告警告，Agent 仍然继续但仅做能做的检查 |
| write_comments | 输出文件被占用 | ⚠️ 提示用户关闭文件后重试 |
| write_report | 输出文件被占用 | ⚠️ 同上 |
| write_report | 报告基本信息表空白（原文文件/译文文件/校对方向为空） | ✅ 传 `--pair-info` 参数，并按 [7.1 pair-info 格式](#71-pair-info-格式) 构建 JSON |
| write_report | 术语库匹配率显示"无术语库" | ✅ 传 `--mechanical-report` 参数，指向 **过滤后** 的 `issues_glossary_filtered.json` |
| write_report | 报告术语违规章节充斥假阳性 | ✅ 铁律 I：禁止传原始 mechanical JSON 进报告 |
| write_report | 问题明细中"原文:"行为空 | ✅ write_report.py v2 内置铁律 D：空字段自动跳过，不输出对应行 |
| write_report / write_comments | Phase 3/4 字段名不一致导致批注/报告内容为空 | ✅ `write_report.py` 内置 `_normalize_issues()` 归一化；`write_comments.py` 通过 `_get()` 链式 fallback + `is_mechanical` 分支处理；新脚本需遵循 [3.1 数据契约](#31-机械检查数据契约重要) |
| check_mechanical | pi=0 跨格式问题充斥报告 | ✅ 报告汇总为"机械检查参考"；批注先尝试定位（PDF页码映射或搜预期译文），无法定位的按 type 合并到文档末尾 |
| check_mechanical | glossary_violation 全部为假阳性（术语库领域与文档不匹配） | ✅ 按 [3.2 术语库领域过滤](#32-术语库领域过滤关键防止大规模假阳性) 三层过滤；事后可用 `filter_glossary_violations.py` 清洗 |
| write_comments | target_quote 过短（如 "mm3"）无法高亮定位 | ✅ 修复脚本 `fix_target_quotes.py` 从 DOCX 段落自动反查完整句子；Phase 4 须遵守 [4.1.2 铁律 C](#412-精度铁律不可违反) |
| write_comments | source_quote 为空导致 "原文: " 空行 | ✅ 已改为动态构建行列表，空字段跳过对应标签行；Phase 4 须遵守 [4.1.2 铁律 D](#412-精度铁律不可违反) |
| locate_by_pdf_page | 机械问题 pi=0 无法定位 | ✅ 通过 PDF 页码→DOCX 段落相似度映射自动分配近似 paragraph_index；详见 [3.1 pi=0 处理](#31-机械检查数据契约重要) |
| search_term | 网络不通/API不可用 | ⚠️ 标记为"无法查证，建议人工确认"，不阻塞流程 |

---

## 大文件策略

500+ 页文档：

1. Phase 2 强制拆分，不跳过
2. 按章节顺序排队，一章一章来
3. 维护"术语索引"跨章跟踪（每校对完一章追加）
4. 每章开始前重新加载机械检查疑点（不混章）
5. 所有章节完成后，Phase 6 执行全局一致性扫描

---

## 红牌行为（绝对禁止）

以下行为被视为校对事故，**绝对不可做**：

| 禁止 | 替代做法 |
|------|----------|
| 凭记忆判断"这翻译不对" | 必须引用原文+译文原文 |
| 改译文 | 只写批注 |
| 跳过 Phase 3 直接用 Agent 做数字检查 | 先跑脚本，再复核 |
| 术语库没有就自己编 | 走 Phase 5 查证流程 |
| 多章混在一起校对 | 一章一章来 |
| 脚本报错假装没看见 | 按"脚本失败处理"表执行 |
| 报告用 Markdown 输出 | 跑 Phase 7 脚本生成 .docx |

## 版本
- v2.8 (2026-06-26): 新增 3.3 Phase 3 已知假阳性模式（四类误报 + 过滤脚本 + Agent 执行规则）；新增 `filter_number_issues.py`；确认跨格式场景下数字/术语检查假阳性率 >90%
- v2.13 (2026-06-29): **翻译反馈修复**：Fix C 机械检查附加上下文定位（number_missing/decimal_mismatch/symbol_missing 均附带 source_quote）；Fix D Phase 4.6 全文档模式传播（相同问题全局补报）；Fix E 客户术语需求加载（Phase 0.5 + check_mechanical --client-glossary + 4.0检查项）；符号等价宽容（≥↔>=等不报缺失）
- v2.12 (2026-06-29): **Phase 3 强制过滤铁律**：新增 3.4 强制过滤步骤（铁律 I/J）——机械检查原始输出禁止直接进报告，过滤后 glossary_violations 须 ≤30%；Phase 7 `--mechanical-report` 必须传过滤后文件。修复 P2/P3 报告术语违规章节充斥假阳性问题
- v2.11 (2026-06-29): **Phase 4 强制分批逐段审查**：148段按15段/批切分，每批独立派发Agent，覆盖追踪+零issue批次重审+覆盖率门禁100%；新增铁律 E/F/G/H（禁止零issue批次/每段必须输出结果/覆盖率门禁/批次不可合并）；Phase 0 新增 0.4 版本目录自动检测；输出命名规范升级为铁律，强制版本目录。修复 v18 漏审7章和输出散落根目录问题
- v2.10 (2026-06-26): Phase 7 新增 7.1 pair-info 格式文档；铁律 D 扩展至报告端；脚本失败表新增报告空白三行；write_report.py 空字段跳过（动态行构建）
- v2.9 (2026-06-26): 新增"输出命名规范"章节；Phase 6/7 输出模板统一
- v2.7 (2026-06-26): Phase 6 新增 6.1 批注渲染三路径（语义-完整/机械-定位/机械-合并）；3.1 pi=0 处理新增 locate_by_pdf_page.py 和 fix_target_quotes.py 调用；修复脚本失败表 `_normalize_issues()` 适用范围描述；脚本路径统一为 `${SKILL_ROOT}/scripts/`；硬约束新增铁律 0（开发日志先行）
- v2.6 (2026-06-26): 新增 3.2 术语库领域过滤（三层过滤机制+领域错配示例）；脚本失败表新增 glossary_violation 全部假阳性条目；load_glossary.py 支持 --domain 参数
- v2.5 (2026-06-26): 新增 4.1.2 铁律 C（target_quote 完整性 ≥10字）和铁律 D（空字段不输出）；更新 3.1 pi=0 处理规则（先定位→再合并→禁止丢弃/堆积）；脚本失败表新增 target_quote 过短和空字段条目
- v2.4 (2026-06-26): 新增 3.1 数据契约（Phase 3 vs Phase 4 字段名对照 + pi=0 处理规则）；脚本失败处理表新增字段名不一致条目
- v2.3 (2026-06-26): 新增 4.1.2 精度铁律：target_quote 逐字复制铁律 + 一检查项一 issue 铁律，修复批注匹配率 49% 和审查密度不足问题：target_quote 逐字复制铁律 + 一检查项一 issue 铁律，修复批注匹配率 49% 和审查密度不足问题
- v2.2 (2026-06-26): 新增 2.E 机器翻译残留检测（4 项）；2.6 新增领域自适应近义词（来自人工校对训练数据）；4.1 新增无术语库时的文档类型自适应检查；表达规范从 22→26 项
- v2.1 (2026-06-25): Phase 4 表达规范从 6 项扩展到 22 项（新增翻译腔模式库 7 项、用词准确性 8 项、句法流畅度 4 项）；术语合规增加段内/跨段统一检查；新增逐段两轮检查执行规范
- v2.0 (2026-06-25): 重构为结构化检查清单，修复 auto-scan bug，加前置条件检查，severity 统一为 critical/medium/low
- v1.0 (2026-06-25): 初始版本
