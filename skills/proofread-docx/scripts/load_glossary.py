#!/usr/bin/env python3
"""
Phase 0: 术语库加载与合并
加载 Excel/SQLite 术语库，合并去重，报告冲突。
输出: JSON 格式的合并术语表 + 冲突报告
"""

import argparse
import json
import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def load_excel_glossary(filepath: str) -> list[dict]:
    """从 Excel 加载术语库，自动识别列"""
    try:
        import openpyxl
    except ImportError:
        return _load_csv_fallback(filepath)

    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 2:
        return []

    # 识别表头列
    header = [str(h).strip().lower() if h else '' for h in rows[0]]
    src_col = _find_column(header, ['英文术语', 'source', 'en', 'english', '原文', 'source_term', 'term'])
    tgt_col = _find_column(header, ['中文译法', '中文术语', 'target', 'zh', 'chinese', '译文', 'target_term', 'synonym', 'translation'])
    domain_col = _find_column(header, ['领域', 'domain', 'field', 'category', '分类'])
    action_col = _find_column(header, ['处理方式', 'action', 'type'])
    added_at_col = _find_column(header, ['入库时间', 'added_at', 'add_date', '创建时间'])

    if src_col is None or tgt_col is None:
        # 尝试前两列作为默认
        src_col, tgt_col = 0, 1

    terms = []
    for row in rows[1:]:
        if row is None or len(row) <= max(src_col, tgt_col):
            continue
        src = str(row[src_col]).strip() if src_col < len(row) and row[src_col] else ''
        tgt = str(row[tgt_col]).strip() if tgt_col < len(row) and row[tgt_col] else ''
        domain = str(row[domain_col]).strip() if domain_col is not None and domain_col < len(row) and row[domain_col] else '通用'
        action = str(row[action_col]).strip() if action_col is not None and action_col < len(row) and row[action_col] else ''
        added_at = str(row[added_at_col]).strip() if added_at_col is not None and added_at_col < len(row) and row[added_at_col] else ''

        # Skip keep-as-is terms (品牌名/人名等不翻译的术语)
        if action in ('保留原文', 'keep', 'keep original', 'retain'):
            continue

        if src and tgt:
            terms.append({'source': src, 'target': tgt, 'domain': domain, 'added_at': added_at})

    wb.close()
    return terms


def _find_column(header: list[str], candidates: list[str]) -> int | None:
    for i, h in enumerate(header):
        if h in candidates:
            return i
    # 模糊匹配
    for i, h in enumerate(header):
        for c in candidates:
            if c in h or h in c:
                return i
    return None


def _load_csv_fallback(filepath: str) -> list[dict]:
    """openpyxl 不可用时的 CSV 回退"""
    import csv
    terms = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        rows = list(reader)
    if len(rows) < 2:
        return []
    src_col, tgt_col = 0, 1
    domain_col = 2 if len(rows[0]) > 2 else None
    for row in rows[1:]:
        if len(row) <= max(src_col, tgt_col):
            continue
        src = row[src_col].strip()
        tgt = row[tgt_col].strip()
        domain = row[domain_col].strip() if domain_col and domain_col < len(row) else '通用'
        if src and tgt:
            terms.append({'source': src, 'target': tgt, 'domain': domain, 'added_at': ''})
    return terms


def load_sqlite_glossary(filepath: str) -> list[dict]:
    """从 SQLite 数据库加载术语"""
    import sqlite3
    conn = sqlite3.connect(filepath)
    cur = conn.cursor()
    # 尝试多种表结构
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    terms = []
    for table in tables:
        try:
            cols = [c[1] for c in cur.execute(f"PRAGMA table_info({table})").fetchall()]
            src_col = _find_column(cols, ['source', 'en', 'english', 'src', 'source_term', '英文术语'])
            tgt_col = _find_column(cols, ['target', 'zh', 'chinese', 'tgt', 'target_term', '中文术语'])
            domain_col = _find_column(cols, ['domain', 'field', 'category', '领域'])
            if src_col is None or tgt_col is None:
                continue
            cols_str = ', '.join(f'"{c}"' for c in [cols[src_col], cols[tgt_col]] + ([cols[domain_col]] if domain_col is not None else []))
            rows = cur.execute(f"SELECT {cols_str} FROM {table}").fetchall()
            for row in rows:
                src = str(row[0]).strip()
                tgt = str(row[1]).strip()
                domain = str(row[2]).strip() if len(row) > 2 and row[2] else '通用'
                if src and tgt:
                    terms.append({'source': src, 'target': tgt, 'domain': domain, 'added_at': ''})
        except Exception:
            continue
    conn.close()
    return terms


def load_csv_glossary(filepath: str) -> list[dict]:
    """从 CSV 加载术语库"""
    return _load_csv_fallback(filepath)  # 复用同一解析逻辑


def normalize_key(s: str) -> str:
    """术语归一化（小写 + 去多余空格），用于去重和匹配"""
    return ' '.join(s.lower().split())


def merge_glossaries(all_terms: list[dict], priorities: list[int]) -> dict:
    """
    合并多个术语库。
    priorities: 各库的优先级列表，数值越小优先级越高（冲突时采用优先级高的译法）
    返回: { "terms": {...}, "conflicts": [...], "stats": {...} }
    """
    merged = {}       # normalized_key -> {source, target, domain, from_file, priority}
    conflicts = []    # 冲突记录

    term_idx = 0
    for file_terms in all_terms:
        priority = priorities[term_idx] if term_idx < len(priorities) else term_idx
        term_idx += 1
        for t in file_terms:
            key = normalize_key(t['source'])
            if key in merged:
                existing = merged[key]
                if normalize_key(existing['target']) != normalize_key(t['target']):
                    conflicts.append({
                        'source_term': t['source'],
                        'existing_target': existing['target'],
                        'existing_domain': existing['domain'],
                        'existing_from': existing['from_file'],
                        'conflicting_target': t['target'],
                        'conflicting_domain': t['domain'],
                        'conflicting_from': t['from_file'],
                        'resolution': 'keep_existing' if existing['priority'] <= priority else 'use_new'
                    })
                    if existing['priority'] > priority:
                        # 新术语优先级更高，覆盖
                        merged[key] = {
                            'source': t['source'],
                            'target': t['target'],
                            'domain': t['domain'],
                            'from_file': t.get('from_file', ''),
                            'priority': priority,
                            'added_at': t.get('added_at', '')
                        }
            else:
                merged[key] = {
                    'source': t['source'],
                    'target': t['target'],
                    'domain': t['domain'],
                    'from_file': t.get('from_file', ''),
                    'priority': priority,
                    'added_at': t.get('added_at', '')
                }

    return {
        'terms': {k: {'source': v['source'], 'target': v['target'], 'domain': v['domain'], 'added_at': v.get('added_at', '')} for k, v in merged.items()},
        'conflicts': conflicts,
        'stats': {
            'total_terms': len(merged),
            'conflict_count': len(conflicts),
            'domains': sorted(set(v['domain'] for v in merged.values()))
        }
    }


def scan_glossary_dir(directory: str) -> list[str]:
    """扫描术语库目录，返回所有术语库文件路径"""
    files = []
    path = Path(directory)
    if not path.is_dir():
        return files
    for ext in ['.xlsx', '.xls', '.csv', '.db']:
        for f in sorted(path.glob(f'*{ext}')):
            if not f.name.startswith('~$'):  # 跳过临时文件
                files.append(str(f.resolve()))
    return files


def main():
    parser = argparse.ArgumentParser(description='加载并合并术语库')
    parser.add_argument('--input', '-i', nargs='*', help='术语库文件路径（支持 .xlsx/.db/.csv）。留空则自动扫描')
    parser.add_argument('--glossary-dir', '-d', help='术语库目录（默认: 项目根目录/glossaries/）')
    parser.add_argument('--auto-scan', '-a', action='store_true', default=True,
                        help='自动扫描 glossaries/ 目录和 glossary.db')
    parser.add_argument('--priorities', '-p', nargs='+', type=int, help='各库优先级（数字越小优先级越高）')
    parser.add_argument('--output', '-o', help='输出 JSON 文件路径（可选，默认 stdout）')
    args = parser.parse_args()

    # 收集输入文件
    input_files = list(args.input) if args.input else []

    # 自动扫描术语库目录
    if args.auto_scan:
        # 扫描 skill 自带的 glossaries/ 目录
        skill_root = Path(__file__).resolve().parent.parent  # skills/proofread-docx/
        glossary_dir = args.glossary_dir or str(skill_root / 'glossaries')
        scanned = scan_glossary_dir(glossary_dir)
        for f in scanned:
            if f not in input_files:
                input_files.append(f)

    if not input_files:
        print(json.dumps({'status': 'no_glossary', 'warning': '未找到任何术语库文件，将跳过术语检查。术语库可放入 glossaries/ 目录。'}, ensure_ascii=False))
        sys.exit(0)

    all_terms = []
    valid_priorities = args.priorities or list(range(len(input_files)))

    for filepath in input_files:
        path = Path(filepath)
        if not path.exists():
            sys.stderr.write(json.dumps({'error': f'文件不存在: {filepath}'}, ensure_ascii=False) + '\n')
            continue

        suffix = path.suffix.lower()
        terms = []
        try:
            if suffix in ('.xlsx', '.xls'):
                terms = load_excel_glossary(filepath)
            elif suffix == '.db':
                terms = load_sqlite_glossary(filepath)
            elif suffix == '.csv':
                terms = load_csv_glossary(filepath)
            else:
                sys.stderr.write(json.dumps({'error': f'不支持的格式: {suffix}', 'file': filepath}, ensure_ascii=False) + '\n')
                continue
        except Exception as e:
            sys.stderr.write(json.dumps({'error': f'加载失败: {e}', 'file': filepath}, ensure_ascii=False) + '\n')
            continue

        # 标记来源
        for t in terms:
            t['from_file'] = path.name
        all_terms.append(terms)

    if not all_terms:
        result = {'status': 'no_glossary', 'warning': '未找到术语库文件。将跳过术语检查，仅做其他维度校对。术语库可放入 glossaries/ 目录。'}
    else:
        result = merge_glossaries(all_terms, valid_priorities)
        result['sources'] = [{'file': Path(f).name, 'count': len(t)} for f, t in zip(input_files, all_terms)]
        result['status'] = 'ok'

    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output_json, encoding='utf-8')
        print(f'已写入: {args.output}')
    else:
        sys.stdout.reconfigure(encoding='utf-8')
        print(output_json)


if __name__ == '__main__':
    main()
