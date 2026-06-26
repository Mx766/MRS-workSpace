#!/usr/bin/env python3
"""Update 4.3 JSON format and 4.5 execution spec in SKILL.md."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = 'skills/proofread-docx/SKILL.md'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Update 4.3 - add target_quote precision warning
marker_43 = '每发现一条疑点，按此格式记录。**所有字段必填，不可省略**：'
if marker_43 in content:
    new_43_marker = '''每发现一条疑点，按此格式记录。**所有字段必填，不可省略**：

> ⚠️ **target_quote 精度要求**：此字段用于 Phase 6 在 DOCX 中定位和高亮对应文字。必须从译文 DOCX 段落中**逐字原样复制**，不得加省略号、不得改符号、不得改标点。参见 [4.1.2 铁律 A](#412-精度铁律不可违反)。'''
    content = content.replace(marker_43, new_43_marker)
    print('4.3 marker updated')
else:
    print('4.3 marker NOT found')

# Update 4.5 section title to add emphasis
old_45_title = '### 4.5 逐段检查执行规范'
new_45_title = '''### 4.5 逐段检查执行规范

> ⚠️ **核心纪律**：参见 [4.1.2 铁律 B](#412-精度铁律不可违反)——每个子检查项（2.1-2.26）命中后**独立成条**，禁止合并为"综合建议"。'''
if old_45_title in content:
    content = content.replace(old_45_title, new_45_title)
    print('4.5 title updated')
else:
    print('4.5 title NOT found')

# Update version footer
old_ver = '## 版本\n- v2.2 (2026-06-26):'
new_ver = '''## 版本
- v2.3 (2026-06-26): 新增 4.1.2 精度铁律：target_quote 逐字复制铁律 + 一检查项一 issue 铁律，修复批注匹配率 49% 和审查密度不足问题
- v2.2 (2026-06-26):'''
if old_ver in content:
    content = content.replace(old_ver, new_ver)
    print('Version updated')
else:
    print('Version NOT found')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('\nAll updates applied to SKILL.md')
