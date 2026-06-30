#!/usr/bin/env python3
"""Phase 4: 逐章校对 - Batch 1-6 (P6-P111)"""
import json, os

B5 = '/home/mx766/.qwenpaw/workspaces/default/jobs/proofread/5/20260630_061759'

with open(f'{B5}/split_target.json') as f:
    tgt = json.load(f)
with open(f'{B5}/split_source.json') as f:
    src = json.load(f)
with open(f'{B5}/phase3_verdict_sheet.json') as f:
    vs = json.load(f)

# --- P6-P111 段落列表 ---
all_paras = []
idx = 0
for ch in tgt['chapters']:
    for p in ch['paragraphs']:
        idx += 1
        all_paras.append((idx, ch['name'], p.get('text','').strip()))

paras_range = [(pi,ch,txt) for pi,ch,txt in all_paras if 6 <= pi <= 111]
print(f"P6-P111: {len(paras_range)} 段（含空）")
nonempty = sum(1 for _,_,t in paras_range if t)
print(f"非空段: {nonempty}")

# 打印每段
for pi, ch_name, txt in paras_range:
    if txt:
        print(f"\n--- P{pi} [{ch_name}] ({len(txt)}字) ---")
        print(txt)
    else:
        print(f"\n--- P{pi} [{ch_name}] (空) ---")

# 对应源文本（按页匹配）
print("\n\n===== 源PDF文本（按页面）=====")
for page in src['pages'][:10]:  # 前10页
    print(f"\n--- Page {page['page_num']} ---")
    print(page['text'][:500])
