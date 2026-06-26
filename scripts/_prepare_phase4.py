#!/usr/bin/env python3
"""
Phase 4 准备: 合并 source (PDF) + target (DOCX) 段落，输出结构化 JSON
供 Agent 逐段校对。
"""
import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')

# Load source PDF pages
with open('cache/split_source.json', 'r', encoding='utf-8') as f:
    src = json.load(f)

# Load target DOCX chapters
with open('cache/split_target.json', 'r', encoding='utf-8') as f:
    tgt = json.load(f)

# Concatenate all PDF text as full source reference
full_source = '\n'.join(p['text'] for p in src['pages'])

# Build paragraph-level pairs
paragraphs = []
para_idx = 0

for ch_idx, chapter in enumerate(tgt.get('chapters', [])):
    ch_title = chapter.get('title', '')
    ch_num = ch_idx + 1

    for p in chapter.get('paragraphs', []):
        para_idx += 1
        text = p.get('text', '').strip()
        if not text:
            continue

        paragraphs.append({
            'global_index': para_idx,
            'chapter': ch_num,
            'chapter_title': ch_title,
            'target_text': text,
            'char_count': len(text),
        })

# Output as JSON for Agent review
output = {
    'total_chapters': len(tgt.get('chapters', [])),
    'total_paragraphs': len(paragraphs),
    'source_full_text': full_source,
    'source_pages': len(src['pages']),
    'paragraphs': paragraphs,
}

with open('cache/phase4_input.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Phase 4 input prepared: {len(paragraphs)} paragraphs across {len(tgt.get('chapters', []))} chapters")
print(f"Source: {len(src['pages'])} PDF pages, {len(full_source)} chars")
