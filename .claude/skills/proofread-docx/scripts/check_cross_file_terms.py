#!/usr/bin/env python3
"""
跨文件术语一致性检查。

收集同一批次所有文件的术语索引，找出同一英文术语在不同文件中译法不一致的情况。

用法:
  python check_cross_file_terms.py \
    --index-dir "cache/" \
    --glossary "glossaries/glossary.json" \
    --output "cache/cross_file_issues.json"
"""

import argparse, json, sys, os
from collections import defaultdict
from pathlib import Path


def load_term_indexes(index_dir: str) -> dict[str, dict]:
    """加载所有 term_index_*.json 文件。
    返回: {filename: {source_term: {target, count, first_para}}}
    """
    indexes = {}
    pattern = os.path.join(index_dir, 'term_index_*.json')
    for path in sorted(Path(index_dir).glob('term_index_*.json')):
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            filename = data.get('file', path.stem.replace('term_index_', ''))
            terms = data.get('terms', {})
            if terms:
                indexes[filename] = terms
                print(f'  加载: {path.name} → {filename} ({len(terms)} 术语)')
        except (json.JSONDecodeError, KeyError) as e:
            print(f'  跳过: {path.name} ({e})')
    return indexes


def load_glossary_multi_translations(glossary_path: str) -> set:
    """从术语库中提取允许有多种译法的术语（处理方式=可替换/两者均可）。"""
    multi = set()
    if not glossary_path or not os.path.exists(glossary_path):
        return multi

    try:
        data = json.loads(Path(glossary_path).read_text(encoding='utf-8'))
        terms = data.get('terms', {})
        for key, term in terms.items():
            action = term.get('action', term.get('处理方式', ''))
            if action in ('可替换', '两者均可', 'alternative', 'both'):
                multi.add(term['source'].strip().lower())
        print(f'  术语库多译法白名单: {len(multi)} 条')
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    return multi


def compare(indexes: dict[str, dict], multi_ok: set) -> list[dict]:
    """比对跨文件术语译法，返回不一致列表。"""
    # 按 source_term 分组: {source_term_lower: {filename: term_info}}
    by_source = defaultdict(dict)
    for filename, terms in indexes.items():
        for src, info in terms.items():
            src_key = src.strip().lower()
            by_source[src_key][filename] = {
                'original': src,
                'target': info.get('target', ''),
                'count': info.get('count', 0),
                'first_para': info.get('first_para', -1),
                'intra_file_conflict': info.get('intra_file_conflict', False),
            }

    issues = []
    for src_key, file_mappings in sorted(by_source.items()):
        if len(file_mappings) < 2:
            continue  # 只在一个文件中出现，无需比对

        # 判断是否有多于一种译法
        translations = defaultdict(list)
        for fname, info in file_mappings.items():
            translations[info['target']].append(fname)

        if len(translations) <= 1:
            continue  # 所有文件译法一致

        # 排除术语库白名单
        if src_key in multi_ok:
            continue

        # 构建 issue
        files_detail = {fname: info['target'] for fname, info in file_mappings.items()}

        # 推荐译法：选出现次数最多的
        best_target = max(translations.items(), key=lambda x: sum(
            file_mappings[f]['count'] for f in x[1]
        ))
        recommendation = f"统一为'{best_target[0]}'（{', '.join(best_target[1])} 使用，共 {sum(file_mappings[f]['count'] for f in best_target[1])} 次）"

        # 原始大小写
        original_spellings = list(set(
            info['original'] for info in file_mappings.values()
        ))

        issues.append({
            'type': 'cross_file_term_mismatch',
            'severity': 'critical',
            'source_term': original_spellings[0] if len(original_spellings) == 1 else original_spellings,
            'files': files_detail,
            'file_details': {
                fname: {
                    'target': info['target'],
                    'count': info['count'],
                    'first_para': info['first_para'],
                    'intra_file_conflict': info['intra_file_conflict'],
                }
                for fname, info in file_mappings.items()
            },
            'recommendation': recommendation,
            'check_id': 'cross_file.term',
        })

    return issues


def main():
    parser = argparse.ArgumentParser(description='跨文件术语一致性检查')
    parser.add_argument('--index-dir', '-d', required=True,
                        help='包含 term_index_*.json 的目录')
    parser.add_argument('--glossary', '-g',
                        help='术语库 JSON（用于排除多译法白名单）')
    parser.add_argument('--output', '-o', required=True,
                        help='输出 JSON 路径')
    parser.add_argument('--dry-run', action='store_true',
                        help='仅打印，不写文件')
    args = parser.parse_args()

    print('=== 跨文件术语一致性检查 ===\n')

    # 1. 加载术语索引
    print('[1/3] 加载术语索引...')
    indexes = load_term_indexes(args.index_dir)
    if len(indexes) < 2:
        print(f'\n仅 {len(indexes)} 个文件的术语索引，无需跨文件比对。')
        # 写空输出
        Path(args.output).write_text(
            json.dumps({'issues': [], 'files_compared': len(indexes)},
                       ensure_ascii=False, indent=2),
            encoding='utf-8')
        return
    print(f'  共 {len(indexes)} 个文件，{sum(len(t) for t in indexes.values())} 条术语映射')

    # 2. 加载多译法白名单
    print('\n[2/3] 加载多译法白名单...')
    multi_ok = set()
    if args.glossary:
        multi_ok = load_glossary_multi_translations(args.glossary)

    # 3. 比对
    print('\n[3/3] 跨文件比对...')
    issues = compare(indexes, multi_ok)

    print(f'\n=== 结果 ===')
    print(f'不一致术语: {len(issues)} 条')

    if issues:
        print()
        for i, issue in enumerate(issues, 1):
            src = issue['source_term']
            src_display = src if isinstance(src, str) else ' / '.join(src)
            print(f'  {i}. {src_display}')
            for fname, target in issue['files'].items():
                detail = issue['file_details'][fname]
                conflict_mark = ' ⚠️ 文件内不一致' if detail['intra_file_conflict'] else ''
                print(f'     {fname}: "{target}" ({detail["count"]}次){conflict_mark}')
            print(f'     → {issue["recommendation"]}')

    output = {
        'issues': issues,
        'files_compared': len(indexes),
        'files': list(indexes.keys()),
        'total_terms_checked': sum(len(terms) for terms in indexes.values()),
    }

    if not args.dry_run:
        Path(args.output).write_text(
            json.dumps(output, ensure_ascii=False, indent=2),
            encoding='utf-8')
        print(f'\n已写入: {args.output}')
    else:
        print('\n(dry-run, 未写入文件)')


if __name__ == '__main__':
    main()
