#!/usr/bin/env python3
"""
Phase 4.4: 严重度校准

Phase 4 所有批次完成后、pattern propagation 之前运行。
使用确定性规则对 Phase 4 的 issue 进行:
  1. 严重度归一化 — 同类 check_item 统一严重度
  2. 领域升级 — 按领域规则提升特定类型 issue 的严重度
  3. 维度覆盖检测 — 检出零 issue 的维度
  4. 异常检测 — 检出高风险遗漏、批间异常、严重度矛盾

输出:
  - cache/issues_phase4_calibrated.json — 校准后的 issues
  - cache/phase4_flags.json — 红旗清单（供 Agent 决定是否重审）
"""

import argparse
import json
import re
import sys
import math
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


# ══════════════════════════════════════════════════════════════
# 严重度决策表（14 条规则，按优先级匹配，命中即停）
# ══════════════════════════════════════════════════════════════

# 每条规则: (条件函数, 目标严重度)
# 条件函数接收 issue dict，返回 bool

def _rule_is_number_error(issue: dict) -> bool:
    """规则 1: 数值/单位错误"""
    ci = issue.get("check_item", "")
    iss = issue.get("issue", "")
    return (
        "数值" in ci or "单位" in ci or "3.1" in ci or "3.2" in ci or
        "数字" in ci or "number" in ci.lower() or
        "数值" in iss or "单位" in iss or "测量" in iss
    )

def _rule_is_meaning_error(issue: dict) -> bool:
    """规则 2: 医学/安全/法律含义改变"""
    ci = issue.get("check_item", "")
    iss = issue.get("issue", "")
    return (
        "错译" in ci or "1.4" in ci or
        "含义" in iss or "偏离" in iss or "误译为" in iss or
        "严重偏离" in iss or "改变" in iss
    )

def _rule_is_client_term(issue: dict) -> bool:
    """规则 3: 客户术语要求未满足"""
    ci = issue.get("check_item", "")
    return "客户术语" in ci or "0." in ci or "client" in ci.lower()

def _rule_is_term_inconsistency(issue: dict) -> bool:
    """规则 4: 术语前后不一致"""
    ci = issue.get("check_item", "")
    iss = issue.get("issue", "")
    return (
        "术语不一致" in iss or "术语统一" in ci or "4.3" in ci or "4.2" in ci or
        "同一概念" in iss or "混用" in iss or "不同译法" in iss
    )

def _rule_is_unreadable(issue: dict) -> bool:
    """规则 5: 句子结构破碎导致无法理解"""
    iss = issue.get("issue", "")
    ci = issue.get("check_item", "")
    # 排除明显不是不可理解的类型
    if "标点" in ci or "格式" in ci or "冗余" in ci or "空格" in ci:
        return False
    return (
        "无法理解" in iss or "不通顺" in iss or "难以理解" in iss or
        "结构破碎" in iss or "不可读" in iss
    )

def _rule_is_connotation(issue: dict) -> bool:
    """规则 6: 褒贬色彩不当"""
    ci = issue.get("check_item", "")
    return "2.5" in ci or "褒贬" in ci or "connotation" in ci.lower()

def _rule_is_translationese(issue: dict) -> bool:
    """规则 7: 翻译腔"""
    ci = issue.get("check_item", "")
    iss = issue.get("issue", "")
    return (
        "翻译腔" in ci or "2.12" in ci or "被动直译" in ci or "2.13" in ci or
        "字面直译" in ci or "2.25" in ci or
        ("直译" in iss and "翻译腔" in iss)
    )

def _rule_is_near_synonym(issue: dict) -> bool:
    """规则 8: 近义词混淆"""
    ci = issue.get("check_item", "")
    return "近义词" in ci or "2.6" in ci or "词义范围" in ci or "2.F1" in ci

def _rule_is_incomplete(issue: dict) -> bool:
    """规则 9: 成分残缺/句式杂糅（但仍可理解）"""
    iss = issue.get("issue", "")
    return (
        ("缺失" in iss or "残缺" in iss or "杂糅" in iss or "不完整" in iss) and
        not ("无法理解" in iss)
    )

def _rule_is_term_overgeneralized(issue: dict) -> bool:
    """规则 10: 术语过于泛化"""
    ci = issue.get("check_item", "")
    iss = issue.get("issue", "")
    # 排除风格/冗余类
    if "冗余" in ci or "标点" in ci or "格式" in ci:
        return False
    return (
        "2.23" in ci or "术语泛化" in ci or "MT术语" in ci or
        ("泛化" in iss and "术语" in iss)
    )

def _rule_is_punctuation(issue: dict) -> bool:
    """规则 11: 标点风格"""
    ci = issue.get("check_item", "")
    iss = issue.get("issue", "")
    return (
        "标点" in ci or "2.2" in ci or "2.3" in ci or
        "标点混用" in iss or "标点缺失" in iss or "标点多余" in iss or
        "括号" in iss or "引号" in iss
    )

def _rule_is_colloquial(issue: dict) -> bool:
    """规则 12: 口语化表达"""
    iss = issue.get("issue", "")
    return "口语" in iss or "过于口语" in iss or "书面语" in iss

def _rule_is_format(issue: dict) -> bool:
    """规则 13: 格式微调"""
    ci = issue.get("check_item", "")
    iss = issue.get("issue", "")
    return (
        "格式" in ci or "5.1" in ci or "5.2" in ci or "5.3" in ci or
        "空格" in ci or "字体" in ci or "行距" in ci or
        ("空格" in iss and "格式" not in ci)
    )

def _rule_is_optional_modifier(issue: dict) -> bool:
    """规则 14: 可有可无的修饰词"""
    ci = issue.get("check_item", "")
    iss = issue.get("issue", "")
    return (
        "增译" in ci or "1.2" in ci or "2.18" in ci or
        "不同的" in ci or "冗余" in ci or "2.G3" in ci or
        "可有可无" in iss
    )


# 规则列表: 按优先级排列
SEVERITY_RULES = [
    (_rule_is_number_error,       "critical"),
    (_rule_is_meaning_error,      "critical"),
    (_rule_is_client_term,        "critical"),
    (_rule_is_term_inconsistency, "critical"),
    (_rule_is_unreadable,         "critical"),
    (_rule_is_connotation,        "medium"),
    (_rule_is_translationese,     "medium"),
    (_rule_is_near_synonym,       "medium"),
    (_rule_is_incomplete,         "medium"),
    (_rule_is_term_overgeneralized,"medium"),
    (_rule_is_punctuation,        "low"),
    (_rule_is_colloquial,         "low"),
    (_rule_is_format,             "low"),
    (_rule_is_optional_modifier,  "low"),
]


def apply_severity_rules(issue: dict) -> str:
    """按 14 条规则顺序匹配，返回标准严重度。

    返回: "critical" | "medium" | "low"
    """
    # 预检: 某些 check_item 类别天然上限为 medium（不可升 critical）
    ci = issue.get("check_item", "")
    style_only = any(x in ci for x in [
        "2.3", "2.18", "2.19", "2.G3", "标点", "空格", "格式",
    ])

    for rule_fn, target_severity in SEVERITY_RULES:
        try:
            if rule_fn(issue):
                # 风格类 issue 不允许升为 critical
                if style_only and target_severity == "critical":
                    return "medium"
                return target_severity
        except Exception:
            continue

    # 未匹配任何规则，保留原严重度
    return issue.get("severity", "medium")


# ══════════════════════════════════════════════════════════════
# 1. 严重度归一化
# ══════════════════════════════════════════════════════════════

def normalize_severity(issues: list[dict]) -> list[dict]:
    """严重度归一化。

    逻辑:
      - 按 14 条规则重新计算每条 issue 的期望严重度
      - check_item 含"错译" → 强制 critical
      - confidence=low 且 severity=critical → 降为 medium
      - 同类 check_item 中，少数派严重度统一为多数派
    """
    if not issues:
        return []

    calibrated = []
    for iss in issues:
        iss_copy = dict(iss)
        original_severity = iss.get("severity", "medium")
        confidence = iss.get("confidence", "medium")
        check_item = iss.get("check_item", "")

        # Step 1: 按规则计算期望严重度
        rule_severity = apply_severity_rules(iss_copy)

        # Step 2: 强制规则
        if "错译" in check_item:
            rule_severity = "critical"

        # Step 3: 低置信度降级
        if confidence == "low" and rule_severity == "critical":
            rule_severity = "medium"

        # Step 4: 记录变化
        if rule_severity != original_severity:
            iss_copy["_calibration"] = {
                "original_severity": original_severity,
                "calibrated_severity": rule_severity,
                "reason": f"规则匹配: 期望={rule_severity}, 原始={original_severity}",
            }
        else:
            iss_copy["_calibration"] = {
                "original_severity": original_severity,
                "calibrated_severity": rule_severity,
                "reason": "无需调整",
            }

        iss_copy["severity"] = rule_severity
        calibrated.append(iss_copy)

    # Step 5: 同类 check_item 多数派归一化
    # 按 check_item 分组
    groups = {}
    for iss in calibrated:
        ci = iss["check_item"]
        if ci not in groups:
            groups[ci] = []
        groups[ci].append(iss)

    for ci, group in groups.items():
        if len(group) < 3:
            continue
        # 统计多数派严重度
        sev_counts = Counter(iss["severity"] for iss in group)
        majority_sev = sev_counts.most_common(1)[0][0]
        # 如果多数派占 > 60%，统一少数派
        if sev_counts[majority_sev] / len(group) > 0.6:
            for iss in group:
                if iss["severity"] != majority_sev:
                    old = iss["severity"]
                    iss["severity"] = majority_sev
                    iss["_calibration"]["reason"] += (
                        f"; 同类归一化: {old} → {majority_sev} "
                        f"(同组 {sev_counts[majority_sev]}/{len(group)} 为此严重度)"
                    )

    return calibrated


# ══════════════════════════════════════════════════════════════
# 2. 领域严重度升级
# ══════════════════════════════════════════════════════════════

def apply_domain_escalation(
    issues: list[dict],
    domain_escalation_rules: dict,
    key_terminology: list[dict] | None = None,
) -> list[dict]:
    """按领域升级规则提升严重度。

    逻辑:
      - 医疗器械文档中涉及术语库术语的 issue → 升一级
      - 具体规则来自 phase4_context.json 的 domain_escalation_rules

    升级规则: low → medium, medium → critical, critical 不变
    """
    if not domain_escalation_rules:
        return issues

    SEVERITY_ORDER = {"low": 0, "medium": 1, "critical": 2}

    # 构建术语 source 集合（用于术语相关检测）
    term_sources = set()
    if key_terminology:
        for t in key_terminology:
            term_sources.add(t.get("source", "").lower())

    calibrated = []
    for iss in issues:
        iss_copy = dict(iss)
        issue_text = (iss.get("issue", "") + " " + iss.get("source_quote", "")).lower()
        check_item = iss.get("check_item", "")
        source_quote = iss.get("source_quote", "").lower()

        should_escalate = False
        escalate_reason = ""

        # 检查是否涉及关键术语
        for src in term_sources:
            if len(src) >= 4 and src in issue_text:
                should_escalate = True
                escalate_reason = f"涉及领域术语 '{src}'"
                break

        # 检查 check_item 是否触发升级规则
        if not should_escalate:
            for error_type, target in domain_escalation_rules.items():
                if error_type == "medical_term_error" and ("术语" in check_item or "4.1" in check_item):
                    if any(term in source_quote for term in term_sources if len(term) >= 4):
                        should_escalate = True
                        escalate_reason = f"医疗器械术语错误触发升级 ({error_type})"
                        break

        if should_escalate:
            current = iss_copy.get("severity", "medium")
            current_level = SEVERITY_ORDER.get(current, 1)
            if current_level < 2:  # critical 不变
                new_severity = "medium" if current == "low" else "critical"
                iss_copy["severity"] = new_severity
                if "_calibration" in iss_copy:
                    iss_copy["_calibration"]["reason"] += f"; 领域升级: {current} → {new_severity} ({escalate_reason})"
                iss_copy["_calibration"]["domain_escalated"] = True

        calibrated.append(iss_copy)

    return calibrated


# ══════════════════════════════════════════════════════════════
# 3. 维度覆盖检测
# ══════════════════════════════════════════════════════════════

# 所有 34+1 个检查项 ID
ALL_CHECK_IDS = [
    "0.客户术语合规",
    "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9",
    "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7",
    "2.11", "2.12", "2.13",
    "2.18", "2.19", "2.20", "2.21",
    "2.23", "2.24", "2.25", "2.26",
    "2.F1", "2.F2", "2.F3", "2.F4",
    "2.G1", "2.G2", "2.G3", "2.G4",
    "3.1", "3.2", "3.3", "3.4", "3.5", "3.6",
    "4.1", "4.2", "4.3", "4.4", "4.5",
    "5.1", "5.2", "5.3",
]

# 维度分组
DIMENSION_GROUPS = {
    "零.客户术语合规": ["0.客户术语合规"],
    "一.双语忠实度": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9"],
    "二.表达规范": [
        "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7",
        "2.11", "2.12", "2.13", "2.18", "2.19", "2.20", "2.21",
        "2.23", "2.24", "2.25", "2.26",
        "2.F1", "2.F2", "2.F3", "2.F4",
        "2.G1", "2.G2", "2.G3", "2.G4",
    ],
    "三.数字符号单位": ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6"],
    "四.术语合规": ["4.1", "4.2", "4.3", "4.4", "4.5"],
    "五.格式排版": ["5.1", "5.2", "5.3"],
}


def detect_missing_dimensions(
    issues: list[dict],
    dimension_coverage: dict | None = None,
    phase3_issues: dict | None = None,
) -> list[dict]:
    """检测维度覆盖缺口。

    Args:
        issues: Phase 4 issue 列表
        dimension_coverage: Phase 4 输出的 dimension_coverage (如果有)
        phase3_issues: Phase 3 的 mechanical issues (用于交叉验证)

    Returns:
        红旗列表 [{dimension, issue_count, severity, recommendation}]
    """
    flags = []

    if dimension_coverage:
        # 从 coverage 中找零 issue 的维度
        for check_id in ALL_CHECK_IDS:
            cov = dimension_coverage.get(check_id, {})
            if isinstance(cov, dict) and cov.get("checked") and cov.get("issues_found", 0) == 0:
                pass  # 正常：检查了但无问题
            elif isinstance(cov, dict) and not cov.get("checked"):
                flags.append({
                    "type": "unchecked_dimension",
                    "dimension": check_id,
                    "severity": "high",
                    "recommendation": f"检查项 {check_id} 未被标记为已检查，Phase 4 未覆盖此维度",
                })
    else:
        # 没有 coverage 数据 → 从 issues 反推覆盖情况
        covered_ids = set()
        for iss in issues:
            ci = iss.get("check_item", "")
            for check_id in ALL_CHECK_IDS:
                if check_id in ci:
                    covered_ids.add(check_id)

        # 检查大维度覆盖
        for dim_name, dim_ids in DIMENSION_GROUPS.items():
            covered_in_dim = covered_ids & set(dim_ids)
            if not covered_in_dim:
                severity = "high" if "一" in dim_name or "四" in dim_name else "medium"
                flags.append({
                    "type": "empty_dimension",
                    "dimension": dim_name,
                    "issue_count": 0,
                    "severity": severity,
                    "recommendation": f"维度 {dim_name} 零 issue。{'重点维度不应为零' if severity == 'high' else '建议检查是否遗漏'}。",
                })

    # 交叉验证: Phase 3 发现数字问题但 Phase 4 维度 3 零 issue
    if phase3_issues and isinstance(phase3_issues, dict):
        n_numbers = len(phase3_issues.get("number_mismatches", []))
        if n_numbers > 5:
            dim3_issues = [i for i in issues if "3." in i.get("check_item", "")]
            if not dim3_issues:
                flags.append({
                    "type": "phase3_phase4_mismatch",
                    "dimension": "三.数字符号单位",
                    "phase3_count": n_numbers,
                    "phase4_count": 0,
                    "severity": "high",
                    "recommendation": f"Phase 3 发现 {n_numbers} 处数字问题，但 Phase 4 维度三零 issue。Phase 4 可能未审查数字/符号。",
                })

    return flags


# ══════════════════════════════════════════════════════════════
# 4. 异常检测
# ══════════════════════════════════════════════════════════════

def flag_outliers(
    issues: list[dict],
    high_risk_paragraphs: list[dict] | None = None,
) -> list[dict]:
    """检测异常。

    检出:
      - 高风险段落零 issue (可能漏报)
      - severity_justification 与 severity 矛盾
      - 批间 issue 数异常 (需要 batch_id 信息)

    Returns:
        红旗列表
    """
    flags = []

    # 4a. 高风险段落零 issue 检测
    if high_risk_paragraphs:
        covered_indices = set()
        for iss in issues:
            pi = iss.get("paragraph_index", iss.get("paragraph_index", -1))
            if pi > 0:
                covered_indices.add(pi)

        missed_high_risk = []
        for hr in high_risk_paragraphs:
            pi = hr.get("paragraph_index", -1)
            if pi > 0 and pi not in covered_indices:
                missed_high_risk.append({
                    "paragraph_index": pi,
                    "risk_reason": hr.get("reason", ""),
                    "score": hr.get("score", 0),
                })

        if missed_high_risk:
            # 只取 top 10 条高分未覆盖
            missed_sorted = sorted(missed_high_risk, key=lambda x: x["score"], reverse=True)[:10]
            flags.append({
                "type": "high_risk_missed",
                "count": len(missed_high_risk),
                "paragraphs": missed_sorted,
                "severity": "high",
                "recommendation": f"{len(missed_high_risk)} 个高风险段落在 Phase 4 中零 issue，可能漏报。建议重审 top 段。",
            })

    # 4b. 严重度与 justification 矛盾检测
    SEVERITY_JUSTIFICATION_MAP = {
        "critical": {"changes_meaning", "missing_unit_conversion", "breaks_sentence_structure",
                      "terminology_inconsistency"},
        "medium": {"connotation_mismatch", "unnatural_expression"},
        "low": {"style_preference", "format_deviation"},
    }

    for iss in issues:
        sev = iss.get("severity", "")
        just = iss.get("severity_justification", "")
        if just and sev:
            expected_sevs = [s for s, justs in SEVERITY_JUSTIFICATION_MAP.items() if just in justs]
            if expected_sevs and sev not in expected_sevs:
                flags.append({
                    "type": "severity_justification_mismatch",
                    "paragraph_index": iss.get("paragraph_index", -1),
                    "check_item": iss.get("check_item", ""),
                    "severity": sev,
                    "justification": just,
                    "expected": expected_sevs,
                    "severity": "medium",
                    "recommendation": f"P{iss.get('paragraph_index', '?')}: severity={sev} 但 justification={just} 不匹配，期望 {expected_sevs}。",
                })

    return flags


# ══════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Phase 4.4: 严重度校准 — 归一化、领域升级、覆盖检测"
    )
    parser.add_argument("--issues", required=True, help="Phase 4 issues JSON (issues_phase4.json)")
    parser.add_argument("--context", help="phase4_context.json 路径 (用于领域升级和异常检测)")
    parser.add_argument("--phase3-issues", help="Phase 3 issues_mechanical.json (用于交叉验证)")
    parser.add_argument("--output", "-o", required=True, help="校准后输出 (issues_phase4_calibrated.json)")
    parser.add_argument("--flags-output", help="红旗输出 (phase4_flags.json)，默认 output 同目录")
    args = parser.parse_args()

    # ── 加载 ──
    with open(args.issues, "r", encoding="utf-8") as f:
        issues = json.load(f)

    # issues 可能是 {issues: [...]} 或 纯 list
    dimension_coverage = None
    if isinstance(issues, dict):
        dimension_coverage = issues.get("dimension_coverage")
        issues = issues.get("issues", [])
    if not isinstance(issues, list):
        issues = []

    context = None
    if args.context:
        try:
            with open(args.context, "r", encoding="utf-8") as f:
                context = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    phase3_issues = None
    if args.phase3_issues:
        try:
            with open(args.phase3_issues, "r", encoding="utf-8") as f:
                phase3_issues = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    # ── 校准 ──
    print(f"输入: {len(issues)} 条 issue")

    # Step 1: 严重度归一化
    calibrated = normalize_severity(issues)
    n_changed = sum(1 for iss in calibrated
                    if iss.get("_calibration", {}).get("original_severity") != iss["severity"])
    print(f"严重度归一化: {n_changed} 条调整")

    # Step 2: 领域升级
    if context:
        escalation_rules = context.get("domain_escalation_rules", {})
        key_terms = context.get("key_terminology", [])
        calibrated = apply_domain_escalation(calibrated, escalation_rules, key_terms)
        n_escalated = sum(1 for iss in calibrated
                         if iss.get("_calibration", {}).get("domain_escalated"))
        print(f"领域升级: {n_escalated} 条")

    # Step 3: 维度覆盖检测
    dimension_flags = detect_missing_dimensions(calibrated, dimension_coverage, phase3_issues)
    print(f"维度覆盖问题: {len(dimension_flags)} 个")

    # Step 4: 异常检测
    high_risk = context.get("high_risk_paragraphs", []) if context else []
    outlier_flags = flag_outliers(calibrated, high_risk)
    print(f"异常检测: {len(outlier_flags)} 个")

    all_flags = dimension_flags + outlier_flags

    # ── 输出 ──
    # 统计
    sev_counts = Counter(iss["severity"] for iss in calibrated)
    print(f"输出严重度分布: critical={sev_counts.get('critical',0)}, "
          f"medium={sev_counts.get('medium',0)}, low={sev_counts.get('low',0)}")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(calibrated, f, ensure_ascii=False, indent=2)
    print(f"校准后 issues: {args.output}")

    # 红旗输出
    flags_path = args.flags_output or str(Path(args.output).parent / "phase4_flags.json")
    flags_output = {
        "total_flags": len(all_flags),
        "flags": all_flags,
        "severity_summary": dict(sev_counts),
        "recommendation": "无问题" if not all_flags else f"共 {len(all_flags)} 个红旗，建议复核",
    }
    with open(flags_path, "w", encoding="utf-8") as f:
        json.dump(flags_output, f, ensure_ascii=False, indent=2)
    print(f"红旗清单: {flags_path}")


if __name__ == "__main__":
    main()
