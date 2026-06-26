#!/usr/bin/env python3
"""
将 pi=0 机械问题通过搜索关联词定位到 DOCX 段落：
- 术语违规: 搜 expected_target（如 "导光臂"）或 domain 相关词
- 数字缺失: 搜 source_value（数字可能在译文不同位置仍存在）
- 小数位不匹配: 同上
匹配不到则保留 pi=0（文档级）。
"""
import json, sys, re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

def locate_all(docx_path, issues_path, output_path):
    from docx import Document

    doc = Document(docx_path)
    para_texts = {}
    for idx, para in enumerate(doc.paragraphs):
        t = para.text.strip()
        if t:
            para_texts[idx + 1] = t

    issues = json.loads(Path(issues_path).read_text(encoding='utf-8'))

    located = 0
    not_found = 0

    for issue in issues:
        pi = issue.get('paragraph_index', 0)
        if pi >= 1:
            continue  # already located

        typ = issue.get('type', '')

        # Build search terms
        search_terms = []

        if typ == 'glossary_violation':
            # Search for the expected Chinese translation
            exp = issue.get('expected_target', '')
            if exp:
                search_terms.append(exp)
            # Also search for the English source term (might appear untranslated)
            src = issue.get('source_term', '')
            if src:
                search_terms.append(src)

        elif typ in ('number_missing', 'decimal_mismatch'):
            # Search for the number itself
            sv = issue.get('source_value', '')
            if sv:
                search_terms.append(sv)
                # Also try without leading zeros
                if sv.lstrip('0') and sv.lstrip('0') != sv:
                    search_terms.append(sv.lstrip('0'))
                # For decimals, try the integer part
                if '.' in sv:
                    search_terms.append(sv.split('.')[0])

        # Search DOCX paragraphs for each term
        matches = []
        for term in search_terms:
            if not term or len(term) < 1:
                continue
            for pidx, text in para_texts.items():
                if term in text:
                    matches.append((pidx, term))
                    break  # first match for this term
            if matches:
                break

        if matches:
            pidx, term = matches[0]
            issue['paragraph_index'] = pidx
            issue['_located_by'] = f'term="{term}" in paragraph {pidx}'
            located += 1
        else:
            issue['_located_by'] = f'no match for terms: {search_terms}'
            not_found += 1

    Path(output_path).write_text(
        json.dumps(issues, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )

    total = located + not_found
    print(f'Mechanical issues: {total} total')
    print(f'  Located:    {located}')
    print(f'  Not found:  {not_found} (stay pi=0)')

    # Breakdown by type
    by_type = {}
    for issue in issues:
        typ = issue.get('type', 'other')
        if issue.get('paragraph_index', 0) >= 1:
            by_type.setdefault(typ, [0, 0])[0] += 1  # located
        else:
            by_type.setdefault(typ, [0, 0])[1] += 1  # not found
    for typ, (loc, nf) in sorted(by_type.items()):
        print(f'  {typ}: {loc} located, {nf} not found')

    print(f'\nOutput: {output_path}')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--docx', required=True)
    parser.add_argument('--issues', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    locate_all(args.docx, args.issues, args.output)
