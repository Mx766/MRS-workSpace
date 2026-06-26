#!/usr/bin/env python3
"""
Phase 5: 未匹配术语查证
从权威来源查询术语译法，记录来源和置信度。
来源优先级: 术语在线 → WHO → FDA/NMPA → 文献 → 专业词典
输出: 查证结果 JSON
"""
import argparse, json, re, sys, urllib.request, urllib.parse, urllib.error
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


def search_termonline(term: str) -> tuple:
    """查询术语在线 (termonline.cn) — 全国科学技术名词审定委员会"""
    try:
        url = 'https://www.termonline.cn/api/search'
        data = json.dumps({'keyword': term, 'size': 5}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={
            'Content-Type': 'application/json',
            'User-Agent': 'TranslationReviewTool/1.0',
        })
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            items = result.get('data', {}).get('items', [])
            if items:
                item = items[0]
                return ({
                    'source_term': term,
                    'candidate_translation': item.get('translation', item.get('nameCn', '')),
                    'source': '术语在线 (termonline.cn)',
                    'source_type': 'official',
                    'confidence': 'high',
                    'domain': item.get('discipline', ''),
                    'detail': item.get('definition', '')[:200] if item.get('definition') else '',
                }, None)
            return (None, '术语在线: 未找到匹配条目')
    except urllib.error.URLError as e:
        return (None, f'术语在线: 网络不可达 ({e.reason})')
    except urllib.error.HTTPError as e:
        return (None, f'术语在线: HTTP {e.code}')
    except Exception as e:
        return (None, f'术语在线: {e}')


def search_who_terms(term: str) -> tuple:
    """查询 WHO 术语库"""
    try:
        query = urllib.parse.quote(f'{term} site:who.int')
        url = f'https://www.who.int/api/search?query={query}&limit=3'
        req = urllib.request.Request(url, headers={'User-Agent': 'TranslationReviewTool/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            items = result.get('items', [])
            if items:
                return ({
                    'source_term': term,
                    'candidate_translation': '',
                    'source': 'WHO (who.int)',
                    'source_type': 'official',
                    'confidence': 'medium',
                    'detail': items[0].get('title', '')[:200],
                }, None)
            return (None, 'WHO: 未找到匹配条目')
    except urllib.error.URLError as e:
        return (None, f'WHO: 网络不可达 ({e.reason})')
    except urllib.error.HTTPError as e:
        return (None, f'WHO: HTTP {e.code}')
    except Exception as e:
        return (None, f'WHO: {e}')


def search_fda_nmpa(term: str) -> tuple:
    """查询 FDA 术语"""
    try:
        query = urllib.parse.quote(f'{term} site:fda.gov')
        url = f'https://api.fda.gov/other/substance?search={query}&limit=1'
        req = urllib.request.Request(url, headers={'User-Agent': 'TranslationReviewTool/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            items = result.get('results', [])
            if items:
                return ({
                    'source_term': term,
                    'candidate_translation': '',
                    'source': 'FDA (fda.gov)',
                    'source_type': 'official',
                    'confidence': 'medium',
                    'detail': '在 FDA 物质数据库中匹配到相关条目',
                }, None)
            return (None, 'FDA: 未找到匹配条目')
    except urllib.error.URLError as e:
        return (None, f'FDA: 网络不可达 ({e.reason})')
    except urllib.error.HTTPError as e:
        return (None, f'FDA: HTTP {e.code}')
    except Exception as e:
        return (None, f'FDA: {e}')


def search_general(term: str) -> tuple:
    """通用搜索 — DuckDuckGo Instant Answer API（兜底）"""
    try:
        query = urllib.parse.quote(f'{term} 翻译 中文')
        url = f'https://api.duckduckgo.com/?q={query}&format=json&no_html=1'
        req = urllib.request.Request(url, headers={'User-Agent': 'TranslationReviewTool/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            abstract = result.get('AbstractText', '')
            if abstract:
                return ({
                    'source_term': term,
                    'candidate_translation': '',
                    'source': '通用搜索 (DuckDuckGo)',
                    'source_type': 'search',
                    'confidence': 'low',
                    'detail': abstract[:300],
                }, None)
            return (None, '通用搜索: 未找到相关信息')
    except urllib.error.URLError as e:
        return (None, f'通用搜索: 网络不可达 ({e.reason})')
    except urllib.error.HTTPError as e:
        return (None, f'通用搜索: HTTP {e.code}')
    except Exception as e:
        return (None, f'通用搜索: {e}')


def search_term(term: str, offline: bool = False) -> dict:
    """按优先级逐源查证术语。返回包含查证结果和错误诊断的 dict。"""
    errors = []
    result = None

    if offline:
        return {
            'source_term': term,
            'candidate_translation': '',
            'source': '离线模式',
            'source_type': 'manual',
            'confidence': 'low',
            'detail': '离线模式：跳过所有网络查证，建议人工确认',
            'unreachable_backends': ['离线模式：所有网络后端已跳过'],
        }

    # 优先级1: 术语在线
    result, err = search_termonline(term)
    if result:
        return result
    if err:
        errors.append(err)

    # 优先级2: WHO
    result, err = search_who_terms(term)
    if result and result.get('candidate_translation'):
        return result
    if err:
        errors.append(err)

    # 优先级3: FDA
    result, err = search_fda_nmpa(term)
    if result and result.get('candidate_translation'):
        return result
    if err:
        errors.append(err)

    # 优先级4: 通用搜索
    result, err = search_general(term)
    if result:
        result['unreachable_backends'] = errors
        return result
    if err:
        errors.append(err)

    # 全部失败
    return {
        'source_term': term,
        'candidate_translation': '',
        'source': '无可用来源',
        'source_type': 'none',
        'confidence': 'low',
        'detail': '所有查证后端均不可达，建议人工查证',
        'unreachable_backends': errors,
    }


def batch_search(terms: list[str], output_file: str = None, offline: bool = False) -> list[dict]:
    """批量查证术语"""
    results = []
    for term in terms:
        result = search_term(term, offline=offline)
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
        unreachable = r.get('unreachable_backends', [])

        conf_label = {'high': '高', 'medium': '中', 'low': '低'}.get(confidence, '低')
        lines.append(f'{i+1}. **{term}** → {trans}')
        lines.append(f'   来源: {source} | 置信度: {conf_label} | 领域: {domain}')
        if detail:
            lines.append(f'   备注: {detail}')
        if unreachable:
            lines.append(f'   ⚠️ 不可达后端: {", ".join(unreachable)}')
        lines.append('')

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='术语查证')
    parser.add_argument('--terms', '-t', nargs='+', required=True, help='待查证术语列表')
    parser.add_argument('--output', '-o', help='输出 JSON 路径')
    parser.add_argument('--format', '-f', choices=['json', 'text'], default='json', help='输出格式')
    parser.add_argument('--offline', action='store_true',
                        help='离线模式：跳过所有网络请求，直接标记为"建议人工确认"')
    args = parser.parse_args()

    results = batch_search(args.terms, output_file=args.output if args.format == 'json' else None,
                          offline=args.offline)

    if args.format == 'text':
        print(format_for_user_review(results))
    else:
        output_json = json.dumps(results, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(output_json, encoding='utf-8')
            print(f'已写入: {args.output}')
        else:
            print(output_json)


if __name__ == '__main__':
    main()
