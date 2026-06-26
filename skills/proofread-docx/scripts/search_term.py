#!/usr/bin/env python3
"""
Phase 5: 未匹配术语查证
从权威来源查询术语译法，记录来源和置信度。
来源优先级: 术语在线 → WHO → FDA/NMPA → 文献 → 专业词典
输出: 查证结果 JSON
"""

import argparse
import json
import re
import sys
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path


def search_termonline(term: str) -> dict | None:
    """
    查询术语在线 (termonline.cn) — 全国科学技术名词审定委员会
    API: https://www.termonline.cn/api/search
    """
    try:
        url = 'https://www.termonline.cn/api/search'
        data = json.dumps({'keyword': term, 'size': 5}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={
            'Content-Type': 'application/json',
            'User-Agent': 'TranslationReviewTool/1.0',
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            items = result.get('data', {}).get('items', [])
            if items:
                item = items[0]
                return {
                    'source_term': term,
                    'candidate_translation': item.get('translation', item.get('nameCn', '')),
                    'source': '术语在线 (termonline.cn)',
                    'source_type': 'official',
                    'confidence': 'high',
                    'domain': item.get('discipline', ''),
                    'detail': item.get('definition', '')[:200] if item.get('definition') else '',
                }
    except Exception:
        pass
    return None


def search_who_terms(term: str) -> dict | None:
    """
    查询 WHO 术语库 — 通过公开搜索
    使用 Google CSE 或其他公开接口间接搜索
    """
    try:
        # 尝试 WHO 网站搜索
        query = urllib.parse.quote(f'{term} site:who.int')
        url = f'https://www.who.int/api/search?query={query}&limit=3'
        req = urllib.request.Request(url, headers={'User-Agent': 'TranslationReviewTool/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            items = result.get('items', [])
            if items:
                return {
                    'source_term': term,
                    'candidate_translation': '',  # 需要从页面内容进一步提取
                    'source': 'WHO (who.int)',
                    'source_type': 'official',
                    'confidence': 'medium',
                    'detail': items[0].get('title', '')[:200],
                }
    except Exception:
        pass
    return None


def search_fda_nmpa(term: str) -> dict | None:
    """查询 FDA 术语"""
    try:
        query = urllib.parse.quote(f'{term} site:fda.gov')
        url = f'https://api.fda.gov/other/substance?search={query}&limit=1'
        req = urllib.request.Request(url, headers={'User-Agent': 'TranslationReviewTool/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            items = result.get('results', [])
            if items:
                return {
                    'source_term': term,
                    'candidate_translation': '',  # 需要人工确认
                    'source': 'FDA (fda.gov)',
                    'source_type': 'official',
                    'confidence': 'medium',
                    'detail': f'在 FDA 物质数据库中匹配到相关条目',
                }
    except Exception:
        pass
    return None


def search_general(term: str) -> dict | None:
    """
    通用搜索 — 通过公开搜索引擎获取可能的译法
    这是最后的兜底方案
    """
    suggestions = []

    # 尝试 DuckDuckGo Instant Answer API（无需 API key）
    try:
        query = urllib.parse.quote(f'{term} 翻译 中文')
        url = f'https://api.duckduckgo.com/?q={query}&format=json&no_html=1'
        req = urllib.request.Request(url, headers={'User-Agent': 'TranslationReviewTool/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            abstract = result.get('AbstractText', '')
            if abstract:
                suggestions.append(abstract[:300])
    except Exception:
        pass

    return {
        'source_term': term,
        'candidate_translation': '',
        'source': '通用搜索',
        'source_type': 'search',
        'confidence': 'low',
        'detail': ' | '.join(suggestions) if suggestions else '未找到明确译法，建议人工查证',
    }


def search_term(term: str) -> dict:
    """
    按优先级逐源查证术语。
    返回包含查证结果的 dict。
    """
    # 优先级1: 术语在线
    result = search_termonline(term)
    if result:
        return result

    # 优先级2: WHO（医疗/公共卫生领域）
    result = search_who_terms(term)
    if result and result['candidate_translation']:
        return result

    # 优先级3: FDA（医药/器械领域）
    result = search_fda_nmpa(term)
    if result and result['candidate_translation']:
        return result

    # 优先级4: 通用搜索（兜底）
    return search_general(term)


def batch_search(terms: list[str], output_file: str = None) -> list[dict]:
    """批量查证术语"""
    results = []
    for term in terms:
        result = search_term(term)
        results.append(result)

    if output_file:
        Path(output_file).write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

    return results


def format_for_user_review(results: list[dict]) -> str:
    """格式化查证结果供用户审阅"""
    lines = ['以下术语已查证建议译法：\n']
    for i, r in enumerate(results):
        term = r['source_term']
        trans = r.get('candidate_translation', '(未找到译法)')
        source = r.get('source', '未知来源')
        confidence = r.get('confidence', 'low')
        domain = r.get('domain', '')
        detail = r.get('detail', '')

        conf_label = {'high': '高', 'medium': '中', 'low': '低'}.get(confidence, '低')
        lines.append(f'{i+1}. **{term}** → {trans}')
        lines.append(f'   来源: {source} | 置信度: {conf_label} | 领域: {domain}')
        if detail:
            lines.append(f'   备注: {detail}')
        lines.append('')

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='术语查证')
    parser.add_argument('--terms', '-t', nargs='+', required=True, help='待查证术语列表')
    parser.add_argument('--output', '-o', help='输出 JSON 路径')
    parser.add_argument('--format', '-f', choices=['json', 'text'], default='json', help='输出格式')
    args = parser.parse_args()

    results = batch_search(args.terms, args.output if args.format == 'json' else None)

    if args.format == 'text':
        print(format_for_user_review(results))
    else:
        output_json = json.dumps(results, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(output_json, encoding='utf-8')
            print(f'已写入: {args.output}')
        else:
            sys.stdout.reconfigure(encoding='utf-8')
            print(output_json)


if __name__ == '__main__':
    main()
