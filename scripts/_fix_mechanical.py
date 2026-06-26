#!/usr/bin/env python3
"""
Phase 3 机械检查增强：添加假阳性过滤模式。
修复三类已知问题：
  1. 参考文献页码误报（"164"、"262-9" 等）
  2. DOI/标识符误报（"10.1016"、"2016.03.012" 等）
  3. 日期成分误报（"July 27" → 中文日期不含 "27"）

直接修改 check_mechanical.py 的 _check_fulltext_numbers 函数。
"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

# ── 假阳性识别模式 ──

# DOI 模式：10.XXXX/...
DOI_PATTERN = re.compile(r'10\.\d{4,}/')

# 日期英文模式：Month DD, YYYY
DATE_EN_PATTERNS = [
    re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}', re.IGNORECASE),
    re.compile(r'\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4}', re.IGNORECASE),
]

# 参考文献页码模式：连续的数字范围（如 "164-71", "262-9"）
REF_PAGE_RANGE = re.compile(r'\b\d{2,4}[-–]\d{1,4}\b')

# 参考文献特征：出现大量 "数字-数字" 模式的区域
REF_SECTION_MARKER = re.compile(r'(References|REFERENCES|参考文献|Bibliography)', re.IGNORECASE)


def is_doi_context(text: str, number: str, window: int = 80) -> bool:
    """检查数字的局部上下文是否包含 DOI 模式"""
    idx = text.find(number)
    if idx < 0:
        return False
    local = text[max(0, idx - window):idx + len(number) + window]
    return bool(DOI_PATTERN.search(local))


def is_date_context(text: str, number: str, window: int = 80) -> bool:
    """检查数字的局部上下文是否是日期"""
    idx = text.find(number)
    if idx < 0:
        return False
    local = text[max(0, idx - window):idx + len(number) + window]
    for pat in DATE_EN_PATTERNS:
        if pat.search(local):
            return True
    return False


def is_reference_section(text: str) -> bool:
    """检测文本是否为参考文献区域"""
    return bool(REF_SECTION_MARKER.search(text))


def is_reference_page_number(number: str, full_text: str) -> bool:
    """
    判断数字是否为参考文献页码（局部上下文检查）。
    """
    try:
        int_val = int(number)
    except ValueError:
        return False

    if not (1 <= int_val <= 2000):
        return False

    idx = full_text.find(number)
    if idx < 0:
        return False

    # Check local context (~100 chars) for page-range patterns
    local = full_text[max(0, idx - 100):idx + len(number) + 100]

    # Check if this number is part of a page range like "164–71"
    for m in REF_PAGE_RANGE.finditer(local):
        try:
            parts = re.split(r'[-–]', m.group())
            range_start = int(parts[0])
            range_end = int(parts[1])
            if int_val == range_start or int_val == range_end:
                return True
        except (ValueError, IndexError):
            continue

    # Check if in reference section (look back 500 chars)
    preceding = full_text[max(0, idx - 500):idx]
    if is_reference_section(preceding):
        return True

    return False


def should_skip_number(number: str, full_text: str) -> tuple[bool, str]:
    """
    判断数字是否应跳过（假阳性）。
    返回 (skip, reason)。
    """
    # 已有机审：跳过 >500 的整数
    try:
        if int(number) > 500:
            return (True, '>500 (likely page number)')
    except ValueError:
        pass

    # DOI 上下文 (local, not whole-document)
    if is_doi_context(full_text, number):
        return (True, 'DOI/reference identifier')

    # 日期上下文 (local)
    if is_date_context(full_text, number):
        return (True, 'date component')

    # 参考文献页码
    if is_reference_page_number(number, full_text):
        return (True, 'reference page number')

    return (False, '')


def print_analysis(issues_file: str):
    """打印假阳性分析报告"""
    import json
    from pathlib import Path

    issues = json.loads(Path(issues_file).read_text(encoding='utf-8'))

    num_issues = [i for i in issues if i.get('type') == 'number_missing']
    dec_issues = [i for i in issues if i.get('type') == 'decimal_mismatch']

    # Load PDF for context
    import fitz
    pdf_files = list(Path('proofread/1/').glob('*.pdf'))
    pdf_text = ''
    if pdf_files:
        doc = fitz.open(str(pdf_files[0]))
        for page in doc:
            pdf_text += page.get_text()
        doc.close()

    print('=== Number Analysis ===')
    skipped = 0
    kept = 0
    for iss in num_issues:
        sv = iss.get('source_value', '')
        skip, reason = should_skip_number(sv, pdf_text)
        status = f'SKIP ({reason})' if skip else 'KEEP'
        if skip:
            skipped += 1
        else:
            kept += 1
        print(f'  {sv:12s} → {status}')

    print(f'\n  Skip: {skipped}, Keep: {kept}')

    print('\n=== Decimal Analysis ===')
    skipped = 0
    kept = 0
    for iss in dec_issues:
        sv = iss.get('source_value', '')
        skip, reason = should_skip_number(sv, pdf_text)
        status = f'SKIP ({reason})' if skip else 'KEEP'
        if skip:
            skipped += 1
        else:
            kept += 1
        print(f'  {sv:12s} → {status}')

    print(f'\n  Skip: {skipped}, Keep: {kept}')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--analyze', help='Analyze existing issues JSON for false positives')
    args = parser.parse_args()

    if args.analyze:
        print_analysis(args.analyze)
    else:
        print('Usage: python _fix_mechanical.py --analyze <issues.json>')
        print()
        print('This script provides the filtering logic for check_mechanical.py.')
        print('To apply fixes, integrate should_skip_number() into _check_fulltext_numbers().')
