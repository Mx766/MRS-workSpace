#!/usr/bin/env python3
"""
Phase 4.6: 全文档模式传播
从 Phase 4 已标记的 issues 中提取修正模式（术语替换、格式修正等），
在全文范围内搜索相同问题但未被标记的段落，自动补报。

解决翻译人员反馈："目录里指出 test group 应译为试验组，但后文出现了它就没再指出来"
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


# ── 模式提取 ──────────────────────────────────────────────────

def _extract_replacement(issue: dict) -> tuple[str, str] | None:
    """从 issue 的 suggestion / issue / target_quote 字段提取 (旧文本, 新文本) 替换对。

    实际数据常见模式：
    - "副反应"应为"不良反应"                         → (副反应, 不良反应)
    - 将"副反应"统一改为"不良反应"                    → (副反应, 不良反应)
    - 改为"不良反应"（旧词在 issue 描述"X"中）         → (副反应, 不良反应)
    - "书面允许"…应译为"书面许可"                     → (书面允许, 书面许可)

    返回 (old_text, new_text) 或 None。
    """
    suggestion = issue.get('suggestion', '')
    issue_text = issue.get('issue', '')
    # 拼接全部文本以便跨字段搜索
    all_text = f'{suggestion} {issue_text}'

    # A: 「将"X"统一改为"Y"」/「将"X"改为"Y"」
    m = re.search(r'将[「"]([^「"]+)[」"](?:统[一—]|全部)?改[为譯成][「"]([^「"]+)[」"]', all_text)
    if m and m.group(1) != m.group(2):
        return (m.group(1), m.group(2))

    # B: 「"X"应为"Y"」/「"X"应译为"Y"」/「"X"建议改为"Y"」
    m = re.search(r'[「"]([^「"]+)[」"](?:应为|应译为|建议改为|应改成)[「"]([^「"]+)[」"]', all_text)
    if m and m.group(1) != m.group(2):
        return (m.group(1), m.group(2))

    # C: 「改为"Y"」— 旧词需从 issue_text 推断
    m = re.search(r'(?:改为|改成|修正为)[「"]([^「"]+)[」"]', suggestion)
    if m:
        new_text = m.group(1)
        old = _infer_old_from_issue(issue, new_text)
        if old:
            return (old, new_text)

    # D: 「"X"译为"Y"不当」/「"X"…应译为"Y"」
    m = re.search(r'[「"]([^「"]+)[」"].*?应?译为[「"]([^「"]+)[」"]', issue_text)
    if m:
        return (m.group(1), m.group(2))

    return None


def _infer_old_from_issue(issue: dict, new_text: str) -> str | None:
    """当 suggestion 只给了新词，从 issue 描述或 target_quote 推断旧词。"""
    issue_text = issue.get('issue', '')
    target_quote = issue.get('target_quote', '')

    # 「"X"」（引号括起来的术语）→ 第一个不为 new_text 的引号内容
    quoted = re.findall(r'[「"]([^「"]+)[」"]', issue_text)
    for q in quoted:
        if q != new_text and len(q) >= 2 and len(q) <= 20:
            return q

    # 「"X"不当/错误」
    m = re.search(r'[「"]([^「"]+)[」"](?:不当|错误|不正确|冗余)', issue_text)
    if m and m.group(1) != new_text:
        return m.group(1)

    return None


# ── 全文搜索与补报 ──────────────────────────────────────────────

def find_unflagged_occurrences(target_paras: list[dict],
                                old_text: str,
                                new_text: str,
                                already_flagged: set[int],
                                source_check_id: str,
                                source_severity: str) -> list[dict]:
    """在 target_paras 中搜索 old_text 的所有出现位置，
    排除 already_flagged 中已标记的段落，返回新 issues。
    """
    new_issues = []
    escaped = re.escape(old_text)

    for para in target_paras:
        pi = para.get('index', para.get('paragraph_index', 0))
        if pi in already_flagged:
            continue

        # Handle both dict paragraphs and plain string values
        if isinstance(para, str):
            text = para
            pi = 0  # Can't determine index
        else:
            text = para.get('text', para.get('target_text', ''))
        if not text:
            continue

        if re.search(escaped, text):
            new_issues.append({
                'paragraph_index': pi,
                'chapter': para.get('chapter', ''),
                'dimension': '四.术语合规',
                'check_item': '4.3 跨段术语统一',
                'severity': source_severity,
                'confidence': 'medium',
                'source_quote': '',
                'target_quote': text[:200] + ('…' if len(text) > 200 else ''),
                'issue': f'前文已将「{old_text}」修正为「{new_text}」，此处仍使用旧译法「{old_text}」，应统一',
                'suggestion': f'将「{old_text}」改为「{new_text}」',
                '_propagated': True,
                '_source_pattern': f'{old_text}→{new_text}',
            })
    return new_issues


# ── 主入口 ─────────────────────────────────────────────────────

def propagate(issues: list[dict], target_paras: list[dict],
              min_confidence: str = 'medium') -> list[dict]:
    """从 issues 中提取模式，在 target_paras 中搜索未标记的相同问题。

    Args:
        issues: Phase 4 审查结果（issues_phase4.json 的内容）
        target_paras: 译文段落列表（split_target.json 的 paragraphs 数组）
        min_confidence: 仅传播置信度不低于此值的 issue 中的模式

    Returns:
        新增的补报 issues 列表
    """
    # 收集已标记的段落（按 old_text 分组）
    flagged_by_pattern = {}  # old_text → set of paragraph_index
    patterns = []  # (old_text, new_text, severity)

    for issue in issues:
        repl = _extract_replacement(issue)
        if not repl:
            continue
        old_text, new_text = repl
        if len(old_text) < 2 or old_text == new_text:
            continue

        # Only propagate medium+ confidence
        conf = issue.get('confidence', 'medium')
        conf_rank = {'high': 3, 'medium': 2, 'low': 1}
        if conf_rank.get(conf, 0) < conf_rank.get(min_confidence, 0):
            continue

        pi = issue.get('paragraph_index', -1)
        if old_text not in flagged_by_pattern:
            flagged_by_pattern[old_text] = set()
            patterns.append((old_text, new_text, issue.get('severity', 'medium')))
        flagged_by_pattern[old_text].add(pi)

    # 为每个模式搜索全文
    all_new = []
    for old_text, new_text, severity in patterns:
        flagged = flagged_by_pattern.get(old_text, set())
        new_issues = find_unflagged_occurrences(
            target_paras, old_text, new_text, flagged,
            '4.3', severity
        )
        all_new.extend(new_issues)

    return all_new


def main():
    parser = argparse.ArgumentParser(description='Phase 4.6: 全文档模式传播')
    parser.add_argument('--issues', required=True, help='Phase 4 issues JSON')
    parser.add_argument('--target', required=True, help='split_target.json (全部段落)')
    parser.add_argument('--output', '-o', help='输出补报 issues JSON（默认 stdout）')
    parser.add_argument('--min-confidence', default='medium',
                        choices=['high', 'medium', 'low'],
                        help='最低传播置信度 (default: medium)')
    parser.add_argument('--merge', help='合并到原始 issues 文件（原地更新）')
    args = parser.parse_args()

    issues_path = Path(args.issues)
    target_path = Path(args.target)

    if not issues_path.exists():
        sys.stderr.write(f'Issues file not found: {args.issues}\n')
        sys.exit(1)
    if not target_path.exists():
        sys.stderr.write(f'Target file not found: {args.target}\n')
        sys.exit(1)

    with open(issues_path, 'r', encoding='utf-8') as f:
        issues = json.load(f)

    with open(target_path, 'r', encoding='utf-8') as f:
        target_data = json.load(f)

    # 兼容不同格式：paragraphs 数组可能在顶层或嵌套
    if isinstance(target_data, list):
        target_paras = target_data
    elif isinstance(target_data, dict):
        # 优先从 chapters[i].paragraphs 提取
        chapters = target_data.get('chapters', [])
        if chapters:
            target_paras = []
            for ch in chapters:
                for p in (ch.get('paragraphs', []) or []):
                    if isinstance(p, dict):
                        target_paras.append(p)
        else:
            target_paras = target_data.get('paragraphs', target_data.get('paras', []))
        if not target_paras:
            # 可能在顶层 keys 为整数
            target_paras = []
            for k, v in target_data.items():
                if isinstance(k, str) and k.isdigit():
                    if isinstance(v, str):
                        target_paras.append({'index': int(k), 'text': v})
                    elif isinstance(v, dict):
                        target_paras.append(v)

    new_issues = propagate(issues, target_paras, args.min_confidence)

    output = json.dumps(new_issues, ensure_ascii=False, indent=2)

    if args.merge:
        merged = issues + new_issues
        with open(args.merge, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f'合并完成: {len(issues)} + {len(new_issues)} = {len(merged)} 条 → {args.merge}')
    elif args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f'补报 {len(new_issues)} 条 → {args.output}')
    else:
        print(output)


if __name__ == '__main__':
    main()
