#!/usr/bin/env python3
"""
Phase 1: 文件发现与配对
扫描目录，按"原文无语言后缀 + 译文有语言后缀"规则配对。
支持原文: .pdf / .docx / .xlsx
支持译文: .docx / .xlsx（文件名含 _CHN / _ENG 等译入语后缀）
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 译入语后缀映射
LANG_SUFFIXES = {
    # 中文
    '_CHN': 'zh', '_ZH': 'zh', '_ZHO': 'zh', '_CN': 'zh',
    '_CHS': 'zh', '_CHT': 'zh',
    # 英文
    '_ENG': 'en', '_EN': 'en', '_ENU': 'en', '_EN_US': 'en',
    '_EN_GB': 'en',
    # 日文
    '_JPN': 'ja', '_JA': 'ja', '_JP': 'ja',
    # 韩文
    '_KOR': 'ko', '_KO': 'ko', '_KR': 'ko',
    # 法文
    '_FRA': 'fr', '_FR': 'fr', '_FRE': 'fr',
    # 德文
    '_DEU': 'de', '_DE': 'de', '_GER': 'de',
    # 西班牙文
    '_ESP': 'es', '_ES': 'es', '_SPA': 'es',
    # 葡萄牙文
    '_POR': 'pt', '_PT': 'pt', '_PRT': 'pt',
    # 俄文
    '_RUS': 'ru', '_RU': 'ru',
    # 阿拉伯文
    '_ARA': 'ar', '_AR': 'ar',
}

# 译文格式
TRANSLATION_FORMATS = {'.docx', '.xlsx'}

# 原文格式
ORIGINAL_FORMATS = {'.pdf', '.docx', '.xlsx'}

# 被忽略的文件模式
IGNORE_PATTERNS = [
    re.compile(r'^~\$'),          # Word 临时文件
    re.compile(r'^\.'),            # 隐藏文件
    re.compile(r'\.tmp$'),         # 临时文件
    re.compile(r'校对稿'),          # 已校对过的文件
    re.compile(r'校对报告'),        # 校对报告
]


def extract_lang_suffix(filename: str) -> tuple[str, str] | None:
    """从文件名提取语言后缀。返回 (语言代码, 去掉后缀的基础名) 或 None"""
    name_no_ext = Path(filename).stem

    # 按后缀长度降序排序，优先匹配长的（_EN_US 优先于 _EN）
    sorted_suffixes = sorted(LANG_SUFFIXES.keys(), key=len, reverse=True)
    for suffix in sorted_suffixes:
        if name_no_ext.endswith(suffix):
            base_name = name_no_ext[:-len(suffix)]
            return (LANG_SUFFIXES[suffix], base_name)

    # Also try hyphen variants: -CN, -CHN, -ENG, etc.
    # Convert underscore suffixes to hyphen: _CN → -CN, _EN_US → -EN-US
    for suffix in sorted_suffixes:
        hyphen_suffix = suffix.replace('_', '-')
        if name_no_ext.endswith(hyphen_suffix):
            base_name = name_no_ext[:-len(hyphen_suffix)]
            return (LANG_SUFFIXES[suffix], base_name)
    return None


def lang_code_to_direction(lang_code: str) -> str:
    """语言代码转校对方向描述"""
    lang_names = {
        'zh': '中文', 'en': '英文', 'ja': '日文', 'ko': '韩文',
        'fr': '法文', 'de': '德文', 'es': '西班牙文', 'pt': '葡萄牙文',
        'ru': '俄文', 'ar': '阿拉伯文'
    }
    return lang_names.get(lang_code, lang_code)


def scan_directory(input_dir: str) -> dict:
    """扫描目录，分类文件"""
    path = Path(input_dir)
    if not path.is_dir():
        return {'error': f'目录不存在: {input_dir}'}

    all_files = [f for f in path.iterdir() if f.is_file()]
    originals = []   # 原文（无语言后缀）
    translations = [] # 译文（有语言后缀）
    ignored = []

    for f in all_files:
        fname = f.name
        if any(p.search(fname) for p in IGNORE_PATTERNS):
            ignored.append(fname)
            continue

        ext = f.suffix.lower()
        lang_info = extract_lang_suffix(fname)

        if lang_info:
            lang_code, base_name = lang_info
            if ext in TRANSLATION_FORMATS:
                translations.append({
                    'filename': fname,
                    'fullpath': str(f.resolve()),
                    'lang_code': lang_code,
                    'lang_name': lang_code_to_direction(lang_code),
                    'base_name': base_name,
                    'format': ext[1:],  # 去掉点
                })
        else:
            if ext in ORIGINAL_FORMATS:
                originals.append({
                    'filename': fname,
                    'fullpath': str(f.resolve()),
                    'format': ext[1:],
                    'stem': Path(fname).stem,  # 用于配对的基础名
                })

    return {
        'originals': originals,
        'translations': translations,
        'ignored': ignored,
        'total_scanned': len(all_files)
    }


def pair_files(originals: list[dict], translations: list[dict]) -> dict:
    """配对原文和译文"""
    pairs = []
    orphan_translations = []  # 无原文对应的译文
    orphan_originals = []     # 无译文对应的原文
    duplicate_pairs = []      # 一个原文对应多个译文

    # 为每个原文找译文
    matched_trans = set()

    for orig in originals:
        candidates = [
            t for t in translations
            if t['base_name'] == orig['stem'] and t['fullpath'] not in matched_trans
        ]
        if len(candidates) == 1:
            t = candidates[0]
            matched_trans.add(t['fullpath'])
            pairs.append({
                'source': orig,
                'target': t,
            })
        elif len(candidates) > 1:
            # 一个原文多个译文，全配对
            for t in candidates:
                matched_trans.add(t['fullpath'])
                pairs.append({
                    'source': orig,
                    'target': t,
                })
            duplicate_pairs.append({
                'source': orig['filename'],
                'translations': [t['filename'] for t in candidates]
            })
        else:
            orphan_originals.append(orig)

    # 未匹配的译文
    for t in translations:
        if t['fullpath'] not in matched_trans:
            orphan_translations.append(t)

    return {
        'pairs': pairs,
        'orphan_originals': orphan_originals,
        'orphan_translations': orphan_translations,
        'duplicate_pairs': duplicate_pairs,
        'stats': {
            'total_pairs': len(pairs),
            'orphan_originals': len(orphan_originals),
            'orphan_translations': len(orphan_translations),
        }
    }


def main():
    parser = argparse.ArgumentParser(description='文件发现与配对')
    parser.add_argument('--input-dir', '-i', required=True, help='输入目录路径')
    parser.add_argument('--output', '-o', help='输出 JSON 文件路径（可选）')
    args = parser.parse_args()

    scan_result = scan_directory(args.input_dir)
    if 'error' in scan_result:
        result = scan_result
    else:
        pairing_result = pair_files(scan_result['originals'], scan_result['translations'])
        result = {
            **pairing_result,
            'ignored': scan_result['ignored'],
            'total_scanned': scan_result['total_scanned'],
        }

    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output_json, encoding='utf-8')
        print(f'已写入: {args.output}')
    else:
        sys.stdout.reconfigure(encoding='utf-8')
        print(output_json)


if __name__ == '__main__':
    main()
