#!/usr/bin/env python3
"""
事后清洗：按三层过滤规则删除假阳性 glossary_violation。

过滤逻辑：
1. 源术语不在 PDF 原文中 → 删除（术语库太宽泛）
2. 预期译文已在 DOCX 中存在 → 删除（翻译正确，只是术语库没匹配到）
3. 保留的 → 标记为"需人工确认领域适用性"
"""
import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')


def get_pdf_text(pdf_path: str) -> str:
    """Extract full text from PDF."""
    import fitz
    doc = fitz.open(pdf_path)
    text = ''
    for i in range(len(doc)):
        text += doc[i].get_text()
    doc.close()
    return text


def get_docx_text(docx_path: str) -> str:
    """Extract full text from DOCX."""
    from docx import Document
    doc = Document(docx_path)
    return '\n'.join(p.text for p in doc.paragraphs)


def filter_violations(issues_path: str, pdf_text: str, docx_text: str,
                       output_path: str, auto_remove: bool = False):
    """
    Filter glossary_violation issues.

    Args:
        auto_remove: If True, automatically remove all violations that fail
                     any filter layer. If False, keep but downgrade to low
                     with a note.
    """
    issues = json.loads(Path(issues_path).read_text(encoding='utf-8'))

    removed_layer1 = 0   # source term not in PDF
    removed_layer2 = 0   # expected target already in DOCX
    kept = 0
    result = []

    for iss in issues:
        if iss.get('type') != 'glossary_violation':
            result.append(iss)
            continue

        term = iss.get('source_term', '')
        expected = iss.get('expected_target', '')

        # Layer 1: source term must be in PDF
        if term and term not in pdf_text:
            removed_layer1 += 1
            continue  # remove: term irrelevant to this document

        # Layer 2: expected target should NOT already be in DOCX
        if expected and expected in docx_text:
            removed_layer2 += 1
            continue  # remove: translation already exists

        # Layer 3: keep but mark for human review
        if auto_remove:
            # If auto_remove mode and term also not in DOCX, it was
            # correctly translated (just differently) — skip
            if term and term not in docx_text:
                removed_layer2 += 1  # reused counter
                continue

        iss['severity'] = 'low'
        iss['_domain_warning'] = True
        iss['check'] = (iss.get('check', '') +
                        ' [领域待确认：请人工判断此术语在本文语境中的正确译法]')
        result.append(iss)
        kept += 1

    Path(output_path).write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )

    total = removed_layer1 + removed_layer2 + kept
    print(f'Glossary violations filtered:')
    print(f'  Layer 1 (term not in PDF):        {removed_layer1} removed')
    print(f'  Layer 2 (target already in DOCX): {removed_layer2} removed')
    print(f'  Kept (marked for human review):   {kept}')
    print(f'  Total original:                   {total}')
    print(f'  Total after filter:               {len(result)}')
    print(f'Output: {output_path}')


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Filter false positive glossary_violation issues')
    parser.add_argument('--issues', required=True, help='Path to issues JSON')
    parser.add_argument('--pdf', help='Path to source PDF (for Layer 1 check)')
    parser.add_argument('--docx', help='Path to target DOCX (for Layer 2 check)')
    parser.add_argument('--output', required=True, help='Output JSON path')
    parser.add_argument('--auto-remove', action='store_true',
                        help='Auto-remove all violations (not just Layer 1-2)')
    args = parser.parse_args()

    pdf_text = get_pdf_text(args.pdf) if args.pdf else ''
    docx_text = get_docx_text(args.docx) if args.docx else ''

    filter_violations(args.issues, pdf_text, docx_text,
                       args.output, args.auto_remove)


if __name__ == '__main__':
    main()
