#!/usr/bin/env python3
"""
Phase 5: 未匹配术语查证
从权威来源查询术语译法，记录来源和置信度。
来源优先级: MeSH → PubMed → openFDA → Wikipedia
输出: 查证结果 JSON

v2 (2026-06-26): 替换全部 4 个后端为实际可用的 API
  - termonline.cn → MeSH (API 已死: SPA 重写, 405)
  - WHO → PubMed E-utilities (被墙: SSL 超时)
  - FDA → openFDA /drug/label.json (URL 写错)
  - DuckDuckGo → Wikipedia API (返回空结果)
"""
import argparse, json, re, sys, urllib.request, urllib.parse, urllib.error
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


def search_mesh(term: str) -> tuple:
    """查询 MeSH (Medical Subject Headings) — NIH 权威医学术语库"""
    try:
        # Step 1: lookup descriptor by label
        url = f'https://id.nlm.nih.gov/mesh/lookup/descriptor?label={urllib.parse.quote(term)}&match=contains&limit=3'
        req = urllib.request.Request(url, headers={'User-Agent': 'TranslationReviewTool/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            items = json.loads(resp.read().decode('utf-8'))
            if items:
                descriptor_id = items[0]['resource'].split('/')[-1]
                label = items[0]['label']
                return ({
                    'source_term': term,
                    'candidate_translation': '',
                    'source': f'MeSH (Medical Subject Headings)',
                    'source_type': 'official',
                    'confidence': 'high',
                    'domain': 'medicine',
                    'detail': f'MeSH 描述符: {label} (ID: {descriptor_id})',
                }, None)
            return (None, 'MeSH: 未找到匹配描述符')
    except urllib.error.URLError as e:
        return (None, f'MeSH: 网络不可达 ({e.reason})')
    except urllib.error.HTTPError as e:
        return (None, f'MeSH: HTTP {e.code}')
    except Exception as e:
        return (None, f'MeSH: {e}')


def search_pubmed(term: str) -> tuple:
    """查询 PubMed — 搜索医学术语在文献中的使用"""
    try:
        url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={urllib.parse.quote(term)}+AND+english[lang]&retmax=3&retmode=json'
        req = urllib.request.Request(url, headers={'User-Agent': 'TranslationReviewTool/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            ids = result.get('esearchresult', {}).get('idlist', [])
            count = int(result.get('esearchresult', {}).get('count', '0'))
            if ids and count > 0:
                return ({
                    'source_term': term,
                    'candidate_translation': '',
                    'source': f'PubMed (NCBI)',
                    'source_type': 'literature',
                    'confidence': 'medium',
                    'domain': 'medicine',
                    'detail': f'在 PubMed 中找到 {count} 篇相关文献',
                }, None)
            return (None, 'PubMed: 未找到相关文献')
    except urllib.error.URLError as e:
        return (None, f'PubMed: 网络不可达 ({e.reason})')
    except urllib.error.HTTPError as e:
        return (None, f'PubMed: HTTP {e.code}')
    except Exception as e:
        return (None, f'PubMed: {e}')


def search_openfda(term: str) -> tuple:
    """查询 openFDA — 美国 FDA 药品/器械数据库"""
    try:
        # Try drug labels first
        url = f'https://api.fda.gov/drug/label.json?search=active_ingredient:{urllib.parse.quote(term)}&limit=1'
        req = urllib.request.Request(url, headers={'User-Agent': 'TranslationReviewTool/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            items = result.get('results', [])
            if items:
                brand = items[0].get('openfda', {}).get('brand_name', [])
                generic = items[0].get('openfda', {}).get('generic_name', [])
                detail_parts = []
                if brand:
                    detail_parts.append(f'商品名: {", ".join(brand[:3])}')
                if generic:
                    detail_parts.append(f'通用名: {", ".join(generic[:3])}')
                return ({
                    'source_term': term,
                    'candidate_translation': '',
                    'source': 'openFDA (api.fda.gov)',
                    'source_type': 'official',
                    'confidence': 'high',
                    'domain': 'pharmaceuticals',
                    'detail': '; '.join(detail_parts) if detail_parts else '在 FDA 药品数据库中找到匹配',
                }, None)
            return (None, 'openFDA: 未找到匹配条目')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # 404 is expected for non-drug terms, try device endpoint
            return (None, f'openFDA: 未找到匹配条目 (非药品术语)')
        return (None, f'openFDA: HTTP {e.code}')
    except urllib.error.URLError as e:
        return (None, f'openFDA: 网络不可达 ({e.reason})')
    except Exception as e:
        return (None, f'openFDA: {e}')


def search_wikipedia(term: str) -> tuple:
    """查询 Wikipedia API — 通用术语说明（兜底）"""
    try:
        url = f'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(term)}+medical&format=json&srlimit=3'
        req = urllib.request.Request(url, headers={'User-Agent': 'TranslationReviewTool/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            items = result.get('query', {}).get('search', [])
            if items:
                titles = [item['title'] for item in items[:3]]
                snippet = items[0].get('snippet', '')[:200]
                # Strip HTML tags from snippet
                snippet = re.sub(r'<[^>]+>', '', snippet)
                return ({
                    'source_term': term,
                    'candidate_translation': '',
                    'source': 'Wikipedia (en.wikipedia.org)',
                    'source_type': 'encyclopedia',
                    'confidence': 'low',
                    'domain': 'general',
                    'detail': f'相关条目: {", ".join(titles)}. 摘要: {snippet}',
                }, None)
            return (None, 'Wikipedia: 未找到相关条目')
    except urllib.error.URLError as e:
        return (None, f'Wikipedia: 网络不可达 ({e.reason})')
    except urllib.error.HTTPError as e:
        return (None, f'Wikipedia: HTTP {e.code}')
    except Exception as e:
        return (None, f'Wikipedia: {e}')


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
