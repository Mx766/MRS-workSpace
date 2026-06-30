#!/usr/bin/env python3
"""
Phase 3.6: 判决书生成（v2.15 新增）

将 Phase 3 机械检查的每一条 finding 转成 Phase 4 的必答问卷。
Phase 4 AI 必须对每条 finding 给出判决：confirmed / false_positive / needs_context / unverifiable

目的：防止 AI 用一句笼统的"全部假阳性" dismiss Phase 3 的所有发现。

输入: cache/issues_mechanical.json（Phase 3 输出）
输出: cache/phase3_verdict_sheet.json（Phase 4 必答问卷）
"""

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 判决选项枚举
VERDICT_OPTIONS = ["confirmed", "false_positive", "needs_context", "unverifiable"]

# Phase 3 finding 子类型 → 前缀映射（兼容复数形式）
TYPE_PREFIX = {
    "glossary_violation": "term",
    "glossary_violations": "term",
    "number_missing": "num",
    "number_mismatches": "num",
    "decimal_mismatch": "num",
    "symbol_missing": "sym",
    "symbol_issues": "sym",
    "cas_missing": "sym",
    "regulation_missing": "sym",
    "punctuation_mixed": "sym",
    "temperature_mismatch": "num",
    "full_unit_untranslated": "unit",
    "unit_issues": "unit",
    "format_issue": "fmt",
    "format_issues": "fmt",
    "client_glossary_violation": "cterm",
    "client_glossary_violations": "cterm",
}

# Phase 3 finding 字段映射（不同子类型有不同字段名）
FINDING_KEY_FIELDS = {
    "source_term": "source_term",
    "source_value": "source_value",
    "expected_target": "expected_target",
    "check": "check",
}


def load_json(filepath: str):
    """安全加载 JSON 文件。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        sys.stderr.write(f"[build_phase3_verdicts] 无法加载 {filepath}: {e}\n")
        return None


def extract_findings(mechanical_data: dict) -> list[dict]:
    """从 Phase 3 机械检查数据中提取所有 finding。

    Args:
        mechanical_data: issues_mechanical.json 的内容

    Returns:
        所有 finding 的列表（扁平化）
    """
    all_findings = []

    # 按子类型遍历
    sub_types = [
        "glossary_violations",
        "client_glossary_violations",
        "number_mismatches",
        "symbol_issues",
        "format_issues",
        "unit_issues",
    ]

    for sub_type in sub_types:
        items = mechanical_data.get(sub_type, [])
        if not items:
            continue
        for item in items:
            all_findings.append({
                **item,
                "_sub_type": sub_type,
            })

    return all_findings


def generate_verdict_id(sub_type: str, index: int) -> str:
    """生成唯一的 verdict_id。

    Args:
        sub_type: 子类型名称（如 glossary_violation）
        index: 在该类型中的序号（从 1 开始）

    Returns:
        如 "term_001", "num_005"
    """
    prefix = TYPE_PREFIX.get(sub_type, "unk")
    return f"{prefix}_{index:03d}"


def build_verdict_sheet(findings: list[dict]) -> dict:
    """从 finding 列表构建判决书。

    Args:
        findings: 所有 Phase 3 finding

    Returns:
        {
            "total_findings": N,
            "by_type": {...},
            "by_paragraph": {...},
            "verdicts": [{verdict_id, type, paragraph_index, ...}]
        }
    """
    verdicts = []
    type_counts = {}
    by_paragraph = {}

    # 按子类型分组计数
    type_indices = {}

    for finding in findings:
        sub_type = finding.get("_sub_type", "unknown")

        # 计数
        if sub_type not in type_indices:
            type_indices[sub_type] = 0
        type_indices[sub_type] += 1
        verdict_id = generate_verdict_id(sub_type, type_indices[sub_type])

        # 构建 verdict 条目
        verdict_entry = {
            "verdict_id": verdict_id,
            "type": sub_type,
            "paragraph_index": finding.get("paragraph_index", 0),
            "severity": finding.get("severity", "medium"),
            # 以下由 Phase 4 AI 填写
            "verdict": None,
            "explanation": None,
            "severity_if_confirmed": None,
        }

        # 复制原文/术语相关字段
        for field in ["source_term", "source_value", "expected_target",
                        "source_quote", "target_quote", "check",
                        "domain", "source_page"]:
            if field in finding and finding[field]:
                verdict_entry[field] = finding[field]

        # 生成人类可读的 Phase 3 判断描述
        verdict_entry["phase3_judgment"] = _format_judgment(finding, sub_type)

        verdicts.append(verdict_entry)

        # 统计
        type_counts[sub_type] = type_counts.get(sub_type, 0) + 1

        # 按段落分组
        pi = finding.get("paragraph_index", 0)
        if pi not in by_paragraph:
            by_paragraph[pi] = []
        by_paragraph[pi].append(verdict_id)

    # 按段落索引排序 by_paragraph
    by_paragraph = {k: by_paragraph[k] for k in sorted(by_paragraph.keys())}

    return {
        "version": "2.15",
        "total_findings": len(verdicts),
        "verdict_options": VERDICT_OPTIONS,
        "verdict_requirements": {
            "explanation_min_chars": 20,
            "explanation_language": "Chinese",
            "must_cover_all": True,
            "note": "每一条 Phase 3 发现都必须有对应的判决。禁止用笼统理由（如'跨领域匹配'、'全部假阳性'）批量 dismiss。",
        },
        "by_type": type_counts,
        "by_paragraph": by_paragraph,
        "verdicts": verdicts,
    }


def _format_judgment(finding: dict, sub_type: str) -> str:
    """生成人类可读的 Phase 3 判断描述。"""

    severity_str = {"critical": "严重", "medium": "中等", "low": "轻微"}.get(
        finding.get("severity", "medium"), "中等"
    )

    if sub_type == "glossary_violation":
        src = finding.get("source_term", "?")
        exp = finding.get("expected_target", "?")
        domain = finding.get("domain", "")
        domain_str = f"（领域：{domain}）" if domain else ""
        check = finding.get("check", "")
        # 如果 check 字段已经包含完整描述，直接用
        if check:
            return f"[{severity_str}] {check}"
        return f"[{severity_str}] 术语 \"{src}\" 术语库要求译为 \"{exp}\"{domain_str}"

    elif sub_type == "client_glossary_violation":
        src = finding.get("source_term", "?")
        exp = finding.get("expected_target", "?")
        check = finding.get("check", "")
        if check:
            return f"[{severity_str}] 客户术语违规 — {check}"
        return f"[{severity_str}] 客户术语 \"{src}\" 要求译为 \"{exp}\""

    elif sub_type in ("number_missing", "decimal_mismatch", "temperature_mismatch"):
        check = finding.get("check", "")
        sv = finding.get("source_value", "")
        if check:
            return f"[{severity_str}] 数字问题 — {check}"
        return f"[{severity_str}] 数字不一致：原文有 \"{sv}\""

    elif sub_type in ("symbol_missing", "cas_missing", "regulation_missing",
                       "punctuation_mixed"):
        check = finding.get("check", "")
        if check:
            return f"[{severity_str}] 符号问题 — {check}"
        return f"[{severity_str}] 符号/标点问题"

    elif sub_type == "full_unit_untranslated":
        check = finding.get("check", "")
        if check:
            return f"[{severity_str}] 单位问题 — {check}"
        return f"[{severity_str}] 单位缩写未翻译"

    elif sub_type == "format_issue":
        check = finding.get("check", "")
        if check:
            return f"[{severity_str}] 格式问题 — {check}"
        return f"[{severity_str}] 格式不一致"

    # fallback
    check = finding.get("check", "?")
    return f"[{severity_str}] {check}"


def extract_for_batch(verdict_sheet: dict, paragraph_indices: list[int]) -> list[dict]:
    """提取指定段落范围内的 verdicts（供 prepare_batch_prompt.py 使用）。

    这是一个工具函数，可在其他脚本中复用。

    Args:
        verdict_sheet: build_verdict_sheet 的输出
        paragraph_indices: 该 batch 的段落索引列表

    Returns:
        该 batch 相关的 verdicts 列表
    """
    by_para = verdict_sheet.get("by_paragraph", {})
    relevant_ids = set()
    for pi in paragraph_indices:
        pi_str = str(pi)
        if pi in by_para:
            relevant_ids.update(by_para[pi])
        elif pi_str in by_para:
            relevant_ids.update(by_para[pi_str])

    # 添加 paragraph_index=0 的（跨格式模式下，位置不确定）
    if 0 in by_para:
        relevant_ids.update(by_para[0])

    verdicts = verdict_sheet.get("verdicts", [])
    return [v for v in verdicts if v["verdict_id"] in relevant_ids]


def main():
    parser = argparse.ArgumentParser(
        description="Phase 3.6: 将 Phase 3 机械检查发现转为 Phase 4 必答问卷"
    )
    parser.add_argument("--mechanical", required=True,
                        help="Phase 3 机械检查输出 (issues_mechanical.json)")
    parser.add_argument("--output", "-o", required=True,
                        help="输出路径 (phase3_verdict_sheet.json)")
    parser.add_argument("--min-explanation-chars", type=int, default=20,
                        help="explanation 最少字符数（默认 20）")
    args = parser.parse_args()

    # 加载
    mechanical = load_json(args.mechanical)
    if mechanical is None:
        sys.exit(1)

    # 验证输入格式
    if not isinstance(mechanical, dict):
        sys.stderr.write(f"[build_phase3_verdicts] 输入必须为 JSON 对象（dict），不是列表\n")
        sys.exit(1)

    # 提取所有 finding
    findings = extract_findings(mechanical)
    if not findings:
        print("Phase 3 未发现任何问题，无需生成判决书。")
        # 输出空的 verdict sheet
        empty = {
            "version": "2.15",
            "total_findings": 0,
            "verdict_options": VERDICT_OPTIONS,
            "verdict_requirements": {},
            "by_type": {},
            "by_paragraph": {},
            "verdicts": [],
        }
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(empty, f, ensure_ascii=False, indent=2)
        print(f"输出（空）: {args.output}")
        return

    # 构建判决书
    sheet = build_verdict_sheet(findings)
    sheet["verdict_requirements"]["explanation_min_chars"] = args.min_explanation_chars

    # 输出
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(sheet, f, ensure_ascii=False, indent=2)

    print(f"Phase 3 → 4 判决书已生成:")
    print(f"  总发现: {sheet['total_findings']} 条")
    for t, c in sheet["by_type"].items():
        print(f"    {t}: {c} 条")
    print(f"  段落覆盖: {len(sheet['by_paragraph'])} 段")
    print(f"  输出: {args.output}")


if __name__ == "__main__":
    main()
