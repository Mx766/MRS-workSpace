#!/usr/bin/env python3
"""
将 pi=0 的机械检查问题通过搜索 source_value 定位到 DOCX 具体段落。
匹配不到或匹配到多处且无法判别的保留 pi=0。
"""
import json, sys
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

def locate_issues(docx_path: str, issues_path: str, output_path: str):
    from docx import Document

    doc = Document(docx_path)
    # Build paragraph index → full text
    para_texts = {}
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if text:
            para_texts[i + 1] = text  # 1-based paragraph index

    issues = json.loads(Path(issues_path).read_text(encoding='utf-8'))

    located = 0
    still_doc_level = 0
    multi_match = 0

    for issue in issues:
        pi = issue.get('paragraph_index', 0)
        if pi >= 1:
            continue  # Already has paragraph location

        src_val = issue.get('source_value', '').strip()
        if not src_val:
            still_doc_level += 1
            continue

        # Search for source_value in DOCX paragraphs
        matches = []
        for pidx, text in para_texts.items():
            if src_val in text:
                matches.append(pidx)

        if len(matches) == 1:
            # Unique match — assign paragraph
            issue['paragraph_index'] = matches[0]
            issue['_located_by'] = f'source_value="{src_val}" matched paragraph {matches[0]}'
            located += 1
        elif len(matches) == 0:
            # Not found — truly missing from translation
            issue['_located_by'] = f'source_value="{src_val}" not found in DOCX'
            still_doc_level += 1
        else:
            # Multiple matches — ambiguous
            # For numbers, prefer the paragraph closest to other matched issues
            issue['_located_by'] = f'source_value="{src_val}" matched paragraphs {matches} (ambiguous)'
            multi_match += 1

    # Write updated issues
    Path(output_path).write_text(json.dumps(issues, ensure_ascii=False, indent=2), encoding='utf-8')

    total_mech = located + still_doc_level + multi_match
    print(f'Total mechanical issues: {total_mech}')
    print(f'  Located to paragraph:  {located}')
    print(f'  Not found (stays pi=0): {still_doc_level}')
    print(f'  Multiple matches (stays pi=0): {multi_match}')
    print(f'Output: {output_path}')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--docx', required=True, help='Path to translated DOCX')
    parser.add_argument('--issues', required=True, help='Path to issues JSON')
    parser.add_argument('--output', required=True, help='Output JSON path')
    args = parser.parse_args()
    locate_issues(args.docx, args.issues, args.output)
