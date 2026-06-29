# 操作手册：Agent 批量验证 Excel 数据

> **适用场景**：用 LLM Agent 上网查证 Excel 表格中上千条数据的真实性，但 Agent 在处理长上下文时出现偷懒、跳过、敷衍等问题。
>
> **核心原则**：**小批次 + 结构化输出 + 并行处理 + 复核机制**

---

## 目录

1. [问题诊断](#1-问题诊断)
2. [方案一：手动拆分 + 并行 Agent（推荐入门方案）](#2-方案一手动拆分--并行-agent推荐入门方案)
3. [方案二：Workflow 全自动编排（推荐进阶方案）](#3-方案二workflow-全自动编排推荐进阶方案)
4. [方案三：逐条循环 + 断点续跑（最高准确率）](#4-方案三逐条循环--断点续跑最高准确率)
5. [关键技巧清单](#5-关键技巧清单)
6. [故障排查](#6-故障排查)
7. [附录：模板与脚本](#7-附录模板与脚本)

---

## 1. 问题诊断

### 1.1 为什么会偷懒？

LLM Agent 在处理超长上下文时会出现 **注意力衰减（Attention Decay）**：

| 数据量 | 表现 |
|--------|------|
| 前 10-20 条 | 每条详查，附带来源 URL |
| 20-40 条 | 开始简写，偶尔合并同类项 |
| 40+ 条 | 输出 "其余类似..."、"以上数据基本属实" |
| 100+ 条 | 大概率直接返回摘要，跳过逐条验证 |

**根因**：Agent 的上下文窗口有限，当一次性塞入上千条数据时，模型倾向于"总结"而不是"逐条处理"。

### 1.2 自检清单

在动手解决之前，先确认你的情况：

- [ ] 数据量 > 50 条？
- [ ] 每条验证需要独立上网搜索？
- [ ] Agent 输出中出现 "其余"、"类似"、"略" 等跳过词？
- [ ] Agent 输出格式不统一，难以解析？

如果勾选 ≥ 2 项，继续往下看。

---

## 2. 方案一：手动拆分 + 并行 Agent（推荐入门方案）

### 2.1 整体流程

```
原始 Excel（1000 条）
    │
    ▼
┌─────────────────────────────┐
│ Step 1: 拆分为小批次         │
│ 每批 20-25 条，存为 JSON     │
└──────────────┬──────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│Agent 1 │ │Agent 2 │ │Agent N │  ← 并行运行
│验证批次1│ │验证批次2│ │验证批次N│
└───┬────┘ └───┬────┘ └───┬────┘
    │          │          │
    └──────────┼──────────┘
               ▼
    ┌─────────────────────┐
    │ Step 3: 汇总结果     │
    │ 合并 JSON，生成报告   │
    └─────────────────────┘
```

### 2.2 Step 1：拆分数据

用 Python 脚本把 Excel 拆成小批次：

```python
# split_excel.py
import pandas as pd
import json
import os

# === 配置 ===
INPUT_FILE = "data.xlsx"          # 你的 Excel 文件
SHEET_NAME = 0                     # Sheet 名或索引
BATCH_SIZE = 25                    # 每批条数，建议 20-25
OUTPUT_DIR = "batches/"            # 输出目录
COLUMNS_TO_VERIFY = ["名称", "数值", "来源"]  # 需要验证的列

os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME)
total = len(df)
print(f"总数据量: {total} 条")

for i in range(0, total, BATCH_SIZE):
    batch = df.iloc[i : i + BATCH_SIZE]
    batch_data = []
    for _, row in batch.iterrows():
        item = {"row_index": int(row.name)}
        for col in COLUMNS_TO_VERIFY:
            item[col] = str(row[col]) if pd.notna(row[col]) else ""
        batch_data.append(item)

    batch_num = i // BATCH_SIZE + 1
    output_file = os.path.join(OUTPUT_DIR, f"batch_{batch_num:03d}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(batch_data, f, ensure_ascii=False, indent=2)
    print(f"  → {output_file} ({len(batch_data)} 条)")

print(f"拆分完成，共 {total // BATCH_SIZE + (1 if total % BATCH_SIZE else 0)} 批")
```

### 2.3 Step 2：并行运行 Agent

对每个批次文件，用 Agent 验证。**关键：给每个 Agent 严格的结构化输出要求。**

#### Agent 提示词模板

```markdown
## 任务

验证以下 {BATCH_SIZE} 条数据的真实性。每条数据都必须独立上网搜索确认，不能跳过任何一条。

## 数据

{JSON_DATA}

## 要求

1. **每条都必须验证**：不允许写"其余类似"、"同上"等跳过描述
2. **每条必须搜索**：用 WebSearch 查找可靠来源（官方网站、权威数据库、学术论文优先）
3. **如实标记**：准确→true，错误→false，无法确认→"uncertain"
4. **输出严格 JSON**：必须包含全部 {BATCH_SIZE} 条结果，一条不能少

## 输出格式

```json
{
  "batch_index": {N},
  "results": [
    {
      "row_index": 0,
      "original_data": "原始数据内容",
      "is_accurate": true,
      "evidence": "验证依据：说明为什么判断为正确/错误",
      "source_url": "https://...",
      "confidence": "high"
    }
  ]
}
```

**confidence 取值**：high（多源交叉验证）/ medium（单源确认）/ low（推断或不确定）

## 警告

- 如果某条数据你无法确认，confidence 设为 "low"，is_accurate 设为 false，evidence 写 "无法找到可靠来源验证"
- 不要编造结果！不确定就是不确定
- 必须有恰好 {BATCH_SIZE} 条结果
```

#### 并行调用方式

在 Claude Code 中，一次性发送多个 Agent：

```
请同时运行 4 个 Agent，分别验证以下批次文件：
- Agent 1: batches/batch_001.json (25条)
- Agent 2: batches/batch_002.json (25条)
- Agent 3: batches/batch_003.json (25条)
- Agent 4: batches/batch_004.json (25条)

每个 Agent 的提示词使用上面模板，输出保存为 results/batch_001_result.json 等。
```

### 2.4 Step 3：汇总结果

```python
# merge_results.py
import json
import os
import glob

RESULTS_DIR = "results/"
OUTPUT_FILE = "final_report.json"

all_results = []
total_accurate = 0
total_inaccurate = 0
total_uncertain = 0

for filepath in sorted(glob.glob(os.path.join(RESULTS_DIR, "batch_*_result.json"))):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    for r in data.get("results", []):
        all_results.append(r)
        if r.get("is_accurate") is True:
            total_accurate += 1
        elif r.get("confidence") == "low":
            total_uncertain += 1
        else:
            total_inaccurate += 1

print(f"=== 验证汇总 ===")
print(f"总计: {len(all_results)} 条")
print(f"确认正确: {total_accurate} 条")
print(f"确认错误: {total_inaccurate} 条")
print(f"无法确认: {total_uncertain} 条")

# 输出完整报告
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump({
        "summary": {
            "total": len(all_results),
            "accurate": total_accurate,
            "inaccurate": total_inaccurate,
            "uncertain": total_uncertain
        },
        "details": all_results
    }, f, ensure_ascii=False, indent=2)

print(f"完整报告已保存至: {OUTPUT_FILE}")
```

### 2.5 优缺点

| 优点 | 缺点 |
|------|------|
| 不需要编程基础 | 需要手动管理批次文件 |
| 可随时中断续跑 | 并行数量受限于手动操作 |
| 结果可审核 | 1000 条需要约 40 个批次 |

---

## 3. 方案二：Workflow 全自动编排（推荐进阶方案）

如果你熟悉 Claude Code，可以用 Workflow 工具全自动完成 拆分 → 并行验证 → 汇总。

### 3.1 前提条件

- Claude Code CLI 环境
- 数据已解析为 JSON 数组

### 3.2 Workflow 脚本

```javascript
export const meta = {
  name: 'verify-excel-data',
  description: '拆分 Excel 数据并用并行 Agent 逐批验证真实性，最后汇总',
  phases: [
    { title: 'Split', detail: '拆分数据为小批次' },
    { title: 'Verify', detail: '并行 Agent 验证各批次' },
    { title: 'Review', detail: '复核不确定条目' },
    { title: 'Aggregate', detail: '汇总验证结果' }
  ]
}

// args 传入：{ rows: [...], batchSize: 25 }
const BATCH_SIZE = args.batchSize || 25
const rows = args.rows

// === Split ===
phase('Split')
const batches = []
for (let i = 0; i < rows.length; i += BATCH_SIZE) {
  batches.push({
    index: Math.floor(i / BATCH_SIZE) + 1,
    rows: rows.slice(i, i + BATCH_SIZE)
  })
}
log(`拆分完成：${batches.length} 批，每批最多 ${BATCH_SIZE} 条`)

// === Verify（并行） ===
phase('Verify')

const VERIFY_SCHEMA = {
  type: "object",
  properties: {
    batch_index: { type: "integer" },
    results: {
      type: "array",
      items: {
        type: "object",
        properties: {
          row_index: { type: "integer" },
          original_data: { type: "string" },
          is_accurate: { type: "boolean" },
          evidence: { type: "string" },
          source_url: { type: "string" },
          confidence: { type: "string", enum: ["high", "medium", "low"] }
        },
        required: ["row_index", "is_accurate", "evidence", "confidence"]
      }
    }
  },
  required: ["batch_index", "results"]
}

const results = await parallel(
  batches.map(batch => () =>
    agent(
      `逐条验证以下 ${batch.rows.length} 条数据的真实性，每条都要上网搜索确认，不允许跳过或合并。

数据：
${JSON.stringify(batch.rows, null, 2)}

要求：
- 每条都必须独立搜索验证
- 不能写"其余类似"、"同上"等跳过描述
- 无法确认的标记 confidence=low, is_accurate=false
- 必须包含恰好 ${batch.rows.length} 条结果`,
      {
        label: `verify-batch-${String(batch.index).padStart(3, '0')}`,
        schema: VERIFY_SCHEMA
      }
    )
  )
)

// === Review: 复核低置信度条目 ===
phase('Review')
const uncertainItems = results
  .filter(Boolean)
  .flatMap(r => r.results || [])
  .filter(item => item.confidence === 'low')

log(`发现 ${uncertainItems.length} 条低置信度条目，进行深度复核...`)

const reviewedResults = []
if (uncertainItems.length > 0) {
  const reviewBatches = []
  for (let i = 0; i < uncertainItems.length; i += 10) {
    reviewBatches.push(uncertainItems.slice(i, i + 10))
  }

  const reviews = await parallel(
    reviewBatches.map((batch, i) => () =>
      agent(
        `以下 ${batch.length} 条数据前一轮验证不确定，请做深度搜索复核：

${JSON.stringify(batch, null, 2)}

对每条数据：
1. 尝试用不同关键词重新搜索
2. 查找多个独立来源交叉验证
3. 仍然无法确认的保持 confidence=low，但补充说明搜索尝试`,
        {
          label: `review-uncertain-${i + 1}`,
          schema: VERIFY_SCHEMA
        }
      )
    )
  )
  reviewedResults.push(...reviews.filter(Boolean).flatMap(r => r.results || []))
}

// === Aggregate ===
phase('Aggregate')
const allVerified = results
  .filter(Boolean)
  .flatMap(r => r.results || [])

// 用复核结果替换低置信度条目
const reviewedMap = new Map(reviewedResults.map(r => [r.row_index, r]))
const final = allVerified.map(item => reviewedMap.get(item.row_index) || item)

const summary = {
  total: final.length,
  accurate: final.filter(r => r.is_accurate === true).length,
  inaccurate: final.filter(r => r.is_accurate === false && r.confidence !== 'low').length,
  uncertain: final.filter(r => r.confidence === 'low').length,
  verified_at: new Date().toISOString()
}

log(`=== 验证完成 ===
总计: ${summary.total} 条
确认正确: ${summary.accurate} 条
确认错误: ${summary.inaccurate} 条
无法确认: ${summary.uncertain} 条`)

return { summary, results: final }
```

### 3.3 调用方式

```
用 Workflow 工具运行 verify-excel-data，传入解析好的 Excel 数据
```

### 3.4 优缺点

| 优点 | 缺点 |
|------|------|
| 全自动，无需手动管理文件 | 需要熟悉 Workflow/Agent 工具 |
| 自动并行，效率最高 | 一次性运行，中断需重跑 |
| 内置复核机制 | 调试较复杂 |

---

## 4. 方案三：逐条循环 + 断点续跑（最高准确率）

当数据质量要求极高、或者每条的验证逻辑差异大时，逐条处理是最保险的。

### 4.1 核心思路

```
for 每条数据:
    1. 单独调用 Agent 验证
    2. 结果写入 results.jsonl（追加模式）
    3. 每 10 条保存 checkpoint
    4. 中断后从 checkpoint 恢复
```

### 4.2 Python 断点续跑脚本

```python
# verify_one_by_one.py
import json
import os
import time

INPUT_FILE = "batches/all_data.json"   # 所有待验证数据
OUTPUT_FILE = "results/results.jsonl"  # 逐条追加结果
CHECKPOINT_FILE = "results/checkpoint.txt"

# 读取所有数据
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    all_data = json.load(f)

# 读取已完成的 row_index
completed = set()
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line.strip())
                completed.add(r["row_index"])
            except:
                pass

pending = [d for d in all_data if d["row_index"] not in completed]
print(f"总计 {len(all_data)} 条，已完成 {len(completed)} 条，剩余 {len(pending)} 条")

# 逐条处理（此处需要替换为实际的 Agent 调用）
for i, item in enumerate(pending):
    row_idx = item["row_index"]
    print(f"[{i+1}/{len(pending)}] 验证 row_index={row_idx}: {item.get('名称', '')}")

    # === 这里替换为你的 Agent 调用 ===
    # result = call_agent_to_verify(item)
    # === Agent 调用结束 ===

    # 保存结果
    result = {
        "row_index": row_idx,
        "verified_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        # ... 其他字段
    }
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

    # 每 10 条保存 checkpoint
    if (i + 1) % 10 == 0:
        with open(CHECKPOINT_FILE, "w") as f:
            f.write(str(row_idx))
        print(f"  → checkpoint 已保存 (完成 {len(completed) + i + 1}/{len(all_data)})")

    # 避免频率限制
    time.sleep(2)

print(f"全部完成！结果保存在 {OUTPUT_FILE}")
```

### 4.3 优缺点

| 优点 | 缺点 |
|------|------|
| 准确率最高 | 速度最慢 |
| 支持断点续跑 | 需要自行管理频率限制 |
| 可逐条审核 | 1000 条可能需要数小时 |

---

## 5. 关键技巧清单

### 5.1 批次大小选择

| 数据复杂度 | 推荐批次 | 原因 |
|-----------|---------|------|
| 简单（数字/日期核对） | 30-50 条/批 | 搜索量小 |
| 中等（事实陈述验证） | 20-30 条/批 | 每条 1-2 次搜索 |
| 复杂（多源交叉验证） | 10-15 条/批 | 每条 3-5 次搜索 |

**经验法则：单批次的预期处理时间不要超过 15 分钟。**

### 5.2 结构化输出铁律

**绝对不要用自然语言描述结果。** 必须用 JSON Schema 约束：

```json
// ❌ 坏：Agent 可以自由发挥
"请验证这些数据的真实性"

// ✅ 好：强制每条都有结构化输出
"输出 JSON，results 数组必须恰好有 25 个元素，每个元素包含 row_index/is_accurate/evidence/source_url"
```

**Schema 中 required 字段越多，越能防止偷懒。**

### 5.3 提示词设计要点

| 要点 | 示例 |
|------|------|
| **明确禁止跳过** | "不允许写'其余类似'、'同上'、'略'等任何跳过描述" |
| **要求逐条计数** | "输出必须包含恰好 N 条结果，我会检查数量" |
| **不确定也是结果** | "无法确认的标记为 uncertain，不要漏掉或编造" |
| **给出负面示例** | "❌ 错误输出：'其余 15 条类似，略' → ✅ 正确输出：每条单独列出" |

### 5.4 质量控制

1. **数量校验**：汇总后检查 `len(results) == len(original_data)`
2. **空值检查**：每条结果至少 3 个非空字段
3. **URL 有效性**：抽查 source_url 是否可访问
4. **争议复核**：confidence=low 的条目集中二次验证
5. **随机抽查**：每 50 条随机抽 3 条人工复核

### 5.5 并行度建议

| Agent 数量 | 适用场景 |
|-----------|---------|
| 3-5 个 | 安全稳妥，适合首次运行 |
| 5-10 个 | 常规运行，平衡速度与稳定性 |
| 10-15 个 | 紧急大批量，需关注 API 频率限制 |

**注意**：并行太多可能触发 API rate limit，导致部分 Agent 失败。

---

## 6. 故障排查

### 6.1 Agent 中途崩溃

**症状**：某个批次的 Agent 返回空或报错。

**解决**：
1. 检查该批次 JSON 文件是否损坏
2. 重新单独运行该批次
3. 如果反复失败，将该批次再拆分为更小批次（10 条/批）

### 6.2 输出结果数量不匹配

**症状**：Agent 返回 18 条结果，但输入了 25 条数据。

**解决**：
1. 对比输入和输出的 row_index，定位缺失条目
2. 将缺失条目组成新批次重新验证
3. 在提示词中更强调数量要求

### 6.3 Agent 返回非 JSON

**症状**：Agent 返回自然语言文本而非 JSON。

**解决**：
1. 在提示词中前置 JSON 格式要求（放在任务描述之前）
2. 使用 Agent 的 `schema` 参数强制结构化输出
3. 添加后缀提示："只输出 JSON，不要任何其他文字"

### 6.4 搜索不到结果

**症状**：大量条目返回 `confidence: "low"`、`evidence: "无法找到可靠来源"`。

**解决**：
1. 检查数据本身是否过于冷门/过时
2. 调整搜索策略：尝试不同关键词、不同语言
3. 对确实无法验证的数据，在报告中单独标注
4. 考虑是否部分条目不适合 AI 验证，需人工处理

### 6.5 API 频率限制

**症状**：多个 Agent 同时报错或超时。

**解决**：
1. 减少并行 Agent 数量
2. 在批次间加入延迟（`time.sleep(5)`）
3. 错峰运行——分多个 session 跑

---

## 7. 附录：模板与脚本

### 7.1 完整 Agent 提示词模板（可直接复制）

```markdown
## 任务：逐条验证数据真实性

你需要验证以下 {BATCH_SIZE} 条数据的真实性。**每条都必须独立上网搜索验证，不允许跳过任何一条。**

### 数据

```json
{JSON_DATA}
```

### 验证规则

1. **必须逐条处理**：每条数据都要有独立的搜索结果，不能合并、不能跳过
2. **搜索要求**：每条至少用 1 个不同关键词搜索，优先查找：
   - 官方网站（政府、企业官网）
   - 权威数据库（学术论文、行业报告）
   - 新闻媒体报道
3. **判断标准**：
   - `is_accurate: true` → 至少 1 个可靠来源确认数据正确
   - `is_accurate: false` → 有可靠来源证伪，或核心数据与来源矛盾
   - `confidence: "low"` → 找不到任何可靠来源
4. **禁止行为**：
   - ❌ 写"其余类似"、"同上"、"略"
   - ❌ 合并多条为一条总结
   - ❌ 编造不存在的来源
   - ❌ 只搜 1-2 条就推断其余

### 输出格式

只输出以下 JSON，**不要任何其他文字**。results 数组必须恰好包含 {BATCH_SIZE} 个元素：

```json
{
  "results": [
    {
      "row_index": 0,
      "original_data": "原始数据原文",
      "is_accurate": true,
      "evidence": "验证依据（说明搜索了什么、找到了什么来源、为什么判断为正确/错误）",
      "source_url": "https://...",
      "confidence": "high"
    }
  ]
}
```

**confidence 取值**：
- `high`：多个可靠来源交叉验证一致
- `medium`：单个可靠来源确认
- `low`：无法找到可靠来源，或来源可信度不足

**特别注意**：如果无法找到可靠来源，必须保留该条目，将 `is_accurate` 设为 `false`，`confidence` 设为 `"low"`，`evidence` 写上你尝试了哪些搜索但未找到。**不要删除条目。**
```

### 7.2 批次文件 JSON 模板

```json
[
  {
    "row_index": 0,
    "名称": "张三",
    "数值": "100万元",
    "来源": "某新闻报道",
    "备注": ""
  },
  {
    "row_index": 1,
    "名称": "李四",
    "数值": "50%",
    "来源": "某公司年报",
    "备注": "2024年数据"
  }
]
```

### 7.3 结果文件 JSON 模板

```json
{
  "batch_index": 1,
  "verified_at": "2026-06-26 18:00:00",
  "results": [
    {
      "row_index": 0,
      "original_data": "张三 | 100万元 | 某新闻报道",
      "is_accurate": true,
      "evidence": "在某新闻官网找到原始报道，确认为100万元",
      "source_url": "https://example.com/news/123",
      "confidence": "high"
    }
  ]
}
```

### 7.4 快速启动 Checklist

- [ ] Excel 数据导出为 JSON（使用 `split_excel.py`）
- [ ] 按 20-25 条拆分为批次文件
- [ ] 确认每批次的 JSON 格式正确
- [ ] 准备 Agent 提示词（复制 7.1 模板）
- [ ] 确定并行数量（建议 3-10 个）
- [ ] 创建 `results/` 目录存放结果
- [ ] 运行 Agent 验证
- [ ] 运行 `merge_results.py` 汇总
- [ ] 数量校验：`len(results) == len(original_data)`
- [ ] 抽查 5-10 条结果
- [ ] 对 `confidence=low` 条目进行二次复核
- [ ] 生成最终报告

---

> **最后提醒**：如果数据量超过 500 条，建议先用方案二（Workflow）跑一轮，然后对 `confidence=low` 的条目用方案三（逐条循环）做二次复核。两种方案组合使用，兼顾效率与准确率。
