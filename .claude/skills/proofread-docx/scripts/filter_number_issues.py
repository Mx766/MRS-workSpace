#!/usr/bin/env python3
"""
过滤 number_missing / decimal_mismatch 假阳性。

三层检查：
  1. Pattern 过滤：DOI、日期、参考文献页码 → 删除
  2. Presence 过滤：数字实际存在于 DOCX 中 → 删除（匹配误差）
  3. 保留的 → 降级为 low + 标注"需人工判断"
"""
import json, sys, re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# ── Patterns ──
DOI_PATTERN = re.compile(r'10\.\d{4,}/')
DATE_EN = re.compile(
    r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
    re.IGNORECASE)
REF_SECTION = re.compile(r'(References|REFERENCES|参考文献|Bibliography)', re.IGNORECASE)
REF_RANGE = re.compile(r'\b\d{2,4}[-–]\d{1,4}\b')


def local_context(text, value, window=80):
    idx = text.find(value)
    if idx < 0:
        return ''
    return text[max(0, idx - window):idx + len(value) + window]


def filter_issues(issues_path, pdf_path, docx_path, output_path, auto_remove=False):
    import fitz
    from docx import Document

    pdf_text = ''
    if pdf_path:
        doc = fitz.open(pdf_path)
        for page in doc:
            pdf_text += page.get_text()
        doc.close()

    docx_text = ''
    if docx_path:
        docx = Document(docx_path)
        docx_text = '\n'.join(p.text for p in docx.paragraphs)

    issues = json.loads(Path(issues_path).read_text(encoding='utf-8'))

    removed_pattern = 0
    removed_present = 0
    kept_count = 0
    result = []

    for iss in issues:
        typ = iss.get('type', '')
        if typ not in ('number_missing', 'decimal_mismatch'):
            result.append(iss)
            continue

        sv = iss.get('source_value', '')
        if not sv:
            result.append(iss)
            continue

        # Layer 1: Pattern-based filtering
        ctx = local_context(pdf_text, sv) if pdf_text else ''

        # DOI check
        if DOI_PATTERN.search(ctx):
            removed_pattern += 1
            continue

        # Date check
        if DATE_EN.search(ctx):
            removed_pattern += 1
            continue

        # Reference page number check
        try:
            int_val = int(sv)
            if 1 <= int_val <= 2000:
                if REF_RANGE.search(ctx):
                    removed_pattern += 1
                    continue
                # Check if in reference section
                idx = pdf_text.find(sv)
                if idx > 0:
                    preceding = pdf_text[max(0, idx - 500):idx]
                    if REF_SECTION.search(preceding):
                        removed_pattern += 1
                        continue
        except ValueError:
            pass

        # Layer 2: Presence check — number exists in DOCX
        if docx_text and sv in docx_text:
            removed_present += 1
            continue

        # Also try stripped version (e.g. "05" → "5")
        stripped = sv.lstrip('0') or '0'
        if stripped != sv and docx_text and stripped in docx_text:
            removed_present += 1
            continue

        # Layer 3: Keep but downgrade
        if auto_remove:
            removed_pattern += 1  # count as removed
            continue

        iss['severity'] = 'low'
        iss['check'] = iss.get('check', '') + '（已通过 pattern + presence 过滤，保留供人工判断）'
        result.append(iss)
        kept_count += 1

    Path(output_path).write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'Number/decimal filtering:')
    print(f'  Pattern (DOI/date/ref): {removed_pattern} removed')
    print(f'  Presence (in DOCX):     {removed_present} removed')
    print(f'  Kept:                   {kept_count}')
    print(f'  Total issues after:     {len(result)}')
    print(f'Output: {output_path}')


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--issues', required=True)
    p.add_argument('--pdf', help='Source PDF')
    p.add_argument('--docx', help='Target DOCX')
    p.add_argument('--output', required=True)
    p.add_argument('--auto-remove', action='store_true',
                   help='Remove ALL (keep none for human review)')
    args = p.parse_args()
    filter_issues(args.issues, args.pdf, args.docx, args.output, args.auto_remove)
