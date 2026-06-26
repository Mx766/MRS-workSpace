#!/usr/bin/env python3
"""
通过 PDF 页码 → DOCX 段落对齐，将 pi=0 机械问题定位到原文对应位置。

方法：
1. 提取 PDF 每页文本
2. 每页文本与 DOCX 段落做滑动窗口相似度匹配 → page→paragraph_range 映射
3. 机械问题的 source_value 在 PDF 中搜索 → 确定来源页码
4. 来源页码 → 映射到 DOCX 段落
"""
import json, sys, re
from pathlib import Path
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding='utf-8')


def extract_pdf_pages(pdf_path: str) -> list[str]:
    """Extract text per page from PDF."""
    import fitz
    doc = fitz.open(pdf_path)
    pages = []
    for i in range(len(doc)):
        text = doc[i].get_text()
        pages.append(text)
    doc.close()
    return pages


def extract_docx_paragraphs(docx_path: str) -> list[tuple[int, str]]:
    """Extract (1-based index, text) for non-empty paragraphs."""
    from docx import Document
    doc = Document(docx_path)
    result = []
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if text:
            result.append((i + 1, text))
    return result


def similarity(a: str, b: str) -> float:
    """Text similarity 0-1."""
    return SequenceMatcher(None, a, b).ratio()


def build_page_para_map(pdf_pages: list[str], docx_paras: list[tuple[int, str]]) -> dict[int, list[int]]:
    """
    Build mapping: PDF page index (0-based) → list of DOCX paragraph indices (1-based).

    Uses a sliding window: for each page, slide a window of paragraphs and find the
    best-matching range. The window size adapts to the page/para count ratio.
    """
    n_paras = len(docx_paras)
    if n_paras == 0:
        return {}

    # Typical paragraphs per page: total_paras / total_pages
    window = max(2, n_paras // max(1, len(pdf_pages)))

    page_map = {}  # page_idx → [para_idx, ...]

    for page_idx, page_text in enumerate(pdf_pages):
        if not page_text.strip():
            # Empty page (images only, etc.) — inherit previous page's range
            if page_idx > 0 and page_idx - 1 in page_map:
                page_map[page_idx] = page_map[page_idx - 1]
            else:
                page_map[page_idx] = []
            continue

        best_score = 0
        best_start = 0
        best_end = min(window, n_paras)

        # Slide window across paragraphs
        for start in range(0, n_paras, max(1, window // 2)):
            end = min(start + window, n_paras)
            combined = ' '.join(docx_paras[i][1] for i in range(start, end))
            score = similarity(page_text, combined)
            if score > best_score:
                best_score = score
                best_start = start
                best_end = end

        # Assign paragraphs in best window
        assigned = [docx_paras[i][0] for i in range(best_start, best_end)]
        page_map[page_idx] = assigned

    return page_map


def locate_issues(issues_path: str, pdf_pages: list[str], page_map: dict[int, list[int]]) -> list[dict]:
    """Add paragraph_index to pi=0 mechanical issues based on PDF page location."""
    issues = json.loads(Path(issues_path).read_text(encoding='utf-8'))
    n_pages = len(pdf_pages)

    located = 0
    multi_page = 0
    not_found = 0
    page_distrib = {}  # per-page counter for round-robin distribution

    for issue in issues:
        if issue.get('paragraph_index', 0) >= 1:
            continue  # already located
        if not issue.get('type'):
            continue  # not mechanical

        # Get the source value term
        sv = issue.get('source_value') or issue.get('source_term', '')
        if not sv:
            not_found += 1
            continue

        # Find which PDF page(s) contain this value
        found_pages = []
        for page_idx, page_text in enumerate(pdf_pages):
            if sv in page_text:
                found_pages.append(page_idx)

        if not found_pages:
            # Try case-insensitive
            sv_lower = sv.lower()
            for page_idx, page_text in enumerate(pdf_pages):
                if sv_lower in page_text.lower():
                    found_pages.append(page_idx)

        if not found_pages:
            not_found += 1
            continue

        # Pick the best page: prefer pages with good paragraph mapping
        best_page = found_pages[0]
        if len(found_pages) > 1:
            # Pick the page that has the most paragraph mappings
            best_count = 0
            for p in found_pages:
                count = len(page_map.get(p, []))
                if count > best_count:
                    best_count = count
                    best_page = p
            if len(found_pages) > 1:
                multi_page += 1

        # Map page to DOCX paragraph — distribute across page's range
        paras = page_map.get(best_page, [])
        if paras:
            # Distribute: use a counter per page to round-robin across paragraphs
            key = f'_distrib_{best_page}'
            if key not in page_distrib:
                page_distrib[key] = 0
            idx = page_distrib[key] % len(paras)
            page_distrib[key] += 1
            pi = paras[idx]
            issue['paragraph_index'] = pi
            issue['_located_by'] = f'pdf_page={best_page+1} → para={pi} (source="{sv}")'
            located += 1
        else:
            not_found += 1

    return issues, located, multi_page, not_found


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', required=True)
    parser.add_argument('--docx', required=True)
    parser.add_argument('--issues', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    print('Extracting PDF pages...')
    pdf_pages = extract_pdf_pages(args.pdf)
    print(f'  {len(pdf_pages)} pages')

    print('Extracting DOCX paragraphs...')
    docx_paras = extract_docx_paragraphs(args.docx)
    print(f'  {len(docx_paras)} non-empty paragraphs')

    print('Building page→paragraph mapping...')
    page_map = build_page_para_map(pdf_pages, docx_paras)

    # Show mapping summary
    for pidx in range(min(5, len(pdf_pages))):
        paras = page_map.get(pidx, [])
        pstr = f'p{paras[0]}-p{paras[-1]}' if paras else 'none'
        print(f'  PDF page {pidx+1} → DOCX {pstr} ({len(paras)} paras)')
    if len(pdf_pages) > 5:
        print(f'  ... ({len(pdf_pages) - 5} more pages)')

    print('Locating mechanical issues...')
    issues, located, multi_page, not_found = locate_issues(
        args.issues, pdf_pages, page_map
    )

    Path(args.output).write_text(
        json.dumps(issues, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )

    total = located + multi_page + not_found
    print(f'\nResults: {total} mechanical issues')
    print(f'  Located via PDF page:  {located}')
    print(f'  Multi-page (best guess): {multi_page}')
    print(f'  Not found:              {not_found}')
    print(f'\nOutput: {args.output}')


if __name__ == '__main__':
    main()
