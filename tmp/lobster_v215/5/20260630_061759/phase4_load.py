#!/usr/bin/env python3
import json
B5 = '/home/mx766/.qwenpaw/workspaces/default/jobs/proofread/5/20260630_061759'
with open(B5 + '/split_target.json') as f:
    tgt = json.load(f)
with open(B5 + '/split_source.json') as f:
    src = json.load(f)
with open(B5 + '/phase3_verdict_sheet.json') as f:
    vs = json.load(f)

# 译文段
paras = []
idx = 0
for ch in tgt['chapters']:
    for p in ch['paragraphs']:
        idx += 1
        if 6 <= idx <= 111:
            txt = p.get('text', '').strip()
            paras.append((idx, ch['title'], txt))

nonempty = [(i, ch, t) for i, ch, t in paras if t]
print("译文 P6-P111（90非空段）:")
for pi, title, txt in nonempty:
    print("P%d [%s] (%d字) %s" % (pi, title, len(txt), txt[:120]))

# 源PDF
print("\n\n源PDF 前6页:")
for p in src['pages'][:6]:
    print("\n=== Page %d ===" % p['page_num'])
    print(p['text'][:800])

# 判决书
vids = [v for v in vs['verdicts'] if 6 <= v.get('paragraph_index',0) <= 111]
print("\n\nP6-P111判决书 (%d条):" % len(vids))
for v in vids:
    print("  %s P%d [%s] '%s' => '%s'" % (v['verdict_id'], v['paragraph_index'], v['type'], v.get('source_term',''), v.get('expected_target','')))
