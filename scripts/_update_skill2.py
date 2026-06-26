#!/usr/bin/env python3
"""Add precision rules to SKILL.md Phase 4 section using line manipulation."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = 'skills/proofread-docx/SKILL.md'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the target lines
insert_after = None
section_line = None
for i, line in enumerate(lines):
    if '不阻塞流程' in line:
        insert_after = i  # line 219 (0-based: 218)
    if '### 4.2 六维度检查清单' in line:
        section_line = i  # line 221 (0-based: 220)
        break

if insert_after is None or section_line is None:
    print(f'FAIL: insert_after={insert_after}, section_line={section_line}')
    sys.exit(1)

print(f'Insert after line {insert_after+1}, before line {section_line+1}')

new_section = """### 4.1.2 精度铁律（不可违反）

> **实测教训**：违反以下两条导致批注匹配率从 95% 跌到 49%，审查密度从 62 条跌到 35 条。

| # | 铁律 | 违反后果 |
|---|------|----------|
| **A** | **target_quote 必须从 DOCX 逐字复制，一字不改** | 加 `...` 省略号、改符号（℃→C）、改标点 → 字符串匹配失败 → bare ref 无高亮 |
| **B** | **每个子检查项独立出一条 issue，禁止合并** | "这句话有 3 个翻译腔问题"写成 1 条 → Phase 6 高亮只能标一处，报告密度缩水 |

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

**执行清单**：每段译文的每一句，把 2.1-2.26 的 26 个 checkbox 在脑中逐项打勾，命中就写一条，不命中就过。**禁止扫读模式（"这段写得不错，过"）。**

"""

# Insert after the empty line following 不阻塞流程 line
# L218 (0-based) = 不阻塞流程, L219 (0-based) = empty
# We insert new section between empty line and ### 4.2
new_lines = lines[:section_line]  # everything up to ### 4.2
new_lines.append('\n')
new_lines.append(new_section)
new_lines.append('\n')
new_lines.extend(lines[section_line:])  # ### 4.2 and onwards

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('DONE - added 4.1.2 precision rules to SKILL.md')

# Verify
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
if '精度铁律' in content:
    print('VERIFIED: 精度铁律 section present')
if '逐字复制' in content:
    print('VERIFIED: 逐字复制 rule present')
if '一检查项一 issue' in content:
    print('VERIFIED: 一检查项一 issue rule present')
