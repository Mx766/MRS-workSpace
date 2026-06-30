#!/usr/bin/env python3
"""
Phase 4.35: 输出 schema 硬校验网关（v2.15 新增，v2.16 强化）

在 Phase 4 结束后、Phase 4.4 校准前运行。
验证 issues_phase4.json 的结构完整性：
  - 顶层结构（必须是 dict，不是 list）
  - dimension_coverage（50 项全覆蓋，checked 状态）
  - paragraph_coverage（100% 段落覆盖）
  - issues（必填字段完整，枚举值合法）
  - phase3_verdicts（全部 Phase 3 发现逐条判决，explanation ≥ 20 字）

不通过 → 阻断 pipeline，打印具体错误清单。
通过 → 输出 validation_report，允许进入 Phase 4.4。

目的：防止 AI 输出残缺数据被下游脚本静默接受（龙虾问题根因 #1）。
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# ══════════════════════════════════════════════════════════════
# 常量定义（与 calibrate_severity.py 保持一致）
# ══════════════════════════════════════════════════════════════

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

VALID_SEVERITIES = {"critical", "medium", "low"}
VALID_JUSTIFICATIONS = {
    "changes_meaning",
    "missing_unit_conversion",
    "breaks_sentence_structure",
    "terminology_inconsistency",
    "connotation_mismatch",
    "unnatural_expression",
    "style_preference",
    "format_deviation",
}
VALID_CONFIDENCES = {"high", "medium", "low"}
VALID_VERDICTS = {"confirmed", "false_positive", "needs_context", "unverifiable"}

ISSUE_REQUIRED_FIELDS = [
    "paragraph_index", "dimension", "check_item", "severity",
    "severity_justification", "confidence",
    "source_quote", "target_quote", "issue", "suggestion",
]

# Phase 3 sub-types → relevant dimension mappings for cross-validation
PHASE3_TO_DIMENSION = {
    "glossary_violations": ["4.1", "4.2", "4.3"],
    "client_glossary_violations": ["0.客户术语合规"],
    "number_mismatches": ["3.1", "3.2"],
    "symbol_issues": ["3.3", "3.4"],
    "format_issues": ["5.1", "5.2"],
    "unit_issues": ["3.3"],
}


def load_json(filepath: str):
    """安全加载 JSON 文件。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return {"_error": str(e)}


def count_chinese_chars(text: str) -> int:
    """统计字符串中的中文字符数。"""
    return len(re.findall(r'[一-鿿]', text))


# ══════════════════════════════════════════════════════════════
# 校验函数
# ══════════════════════════════════════════════════════════════

def validate_top_level(issues_data) -> list[dict]:
    """校验顶层结构。

    Returns:
        错误列表
    """
    errors = []

    if isinstance(issues_data, dict):
        # OK: dict format
        required_top = ["dimension_coverage", "paragraph_coverage", "issues"]
        for key in required_top:
            if key not in issues_data:
                errors.append({
                    "check": "top_level_structure",
                    "severity": "error",
                    "message": f"issues_phase4.json 缺少顶层键 '{key}'。v2.15 起强制使用 "
                               f'{{"dimension_coverage": ..., "paragraph_coverage": ..., "issues": ...}} 格式。',
                })
    elif isinstance(issues_data, list):
        errors.append({
            "check": "top_level_structure",
            "severity": "error",
            "message": "issues_phase4.json 是纯列表格式，v2.15 起不再接受。"
                       "必须使用 dict 格式：{dimension_coverage, paragraph_coverage, issues, phase3_verdicts}。",
        })
    else:
        errors.append({
            "check": "top_level_structure",
            "severity": "error",
            "message": f"issues_phase4.json 类型错误：期望 dict，实际 {type(issues_data).__name__}。",
        })

    return errors


def validate_dimension_coverage(dim_cov: dict, phase3_issues: dict | None = None) -> tuple[list[dict], list[dict]]:
    """校验 dimension_coverage。

    Returns:
        (errors, warnings)
    """
    errors = []
    warnings = []

    if not isinstance(dim_cov, dict):
        errors.append({
            "check": "dimension_coverage",
            "severity": "error",
            "message": "dimension_coverage 必须是一个 JSON 对象（dict）。",
        })
        return errors, warnings

    # 检查所有 check_id 是否存在
    missing_ids = []
    unchecked_count = 0

    for check_id in ALL_CHECK_IDS:
        if check_id not in dim_cov:
            missing_ids.append(check_id)
            continue
        cov = dim_cov[check_id]
        if not isinstance(cov, dict):
            errors.append({
                "check": "dimension_coverage",
                "severity": "error",
                "message": f"dimension_coverage['{check_id}'] 必须是对象，实际 {type(cov).__name__}。",
            })
            continue
        if not cov.get("checked"):
            unchecked_count += 1
        elif cov.get("issues_found", 0) == 0:
            # 检查 Phase 3 是否在该维度有发现
            if phase3_issues:
                relevant_dims = set()
                for sub_type, dims in PHASE3_TO_DIMENSION.items():
                    if check_id in dims:
                        items = phase3_issues.get(sub_type, [])
                        if items:
                            relevant_dims.add(sub_type)
                if relevant_dims:
                    warnings.append({
                        "check": "dimension_coverage",
                        "severity": "warning",
                        "message": (
                            f"dimension_coverage['{check_id}']: issues_found=0，"
                            f"但 Phase 3 在相关子类型中有发现: {relevant_dims}"
                        ),
                    })

    if missing_ids:
        errors.append({
            "check": "dimension_coverage",
            "severity": "error",
            "message": f"dimension_coverage 缺少 {len(missing_ids)} 个检查项: {missing_ids[:10]}{'...' if len(missing_ids) > 10 else ''}",
        })

    if unchecked_count >= 3:
        errors.append({
            "check": "dimension_coverage",
            "severity": "error",
            "message": f"有 {unchecked_count} 个维度的 checked=false（≥3），Phase 4 审核不完整。",
        })

    return errors, warnings


def extract_paragraph_indices(split_target) -> set[int]:
    """从 split_target 中提取所有段落索引（兼容多种格式）。

    支持格式:
      - 纯列表: [{"index": 1, ...}, {"index": 2, ...}]
      - 字典 + chapters: {"chapters": [{"paragraphs": [{"index": 1}, ...]}]}
    """
    indices = set()
    if isinstance(split_target, list):
        for item in split_target:
            if isinstance(item, dict):
                pi = item.get("index", item.get("paragraph_index"))
                if pi is not None:
                    indices.add(pi)
    elif isinstance(split_target, dict):
        chapters = split_target.get("chapters", [])
        for ch in chapters:
            if isinstance(ch, dict):
                paras = ch.get("paragraphs", ch.get("target_paragraphs", []))
                for p in paras:
                    if isinstance(p, dict):
                        pi = p.get("index", p.get("paragraph_index"))
                        if pi is not None:
                            indices.add(pi)
    return indices


def validate_paragraph_coverage(para_cov: list, split_target=None) -> tuple[list[dict], list[dict], int]:
    """校验 paragraph_coverage。

    Returns:
        (errors, warnings, has_issue_count)
    """
    errors = []
    warnings = []

    if not isinstance(para_cov, list):
        errors.append({
            "check": "paragraph_coverage",
            "severity": "error",
            "message": f"paragraph_coverage 必须是列表，实际 {type(para_cov).__name__}。",
        })
        return errors, warnings, 0

    if not para_cov:
        errors.append({
            "check": "paragraph_coverage",
            "severity": "error",
            "message": "paragraph_coverage 为空——没有覆盖任何段落。",
        })
        return errors, warnings, 0

    # 统计
    covered_indices = set()
    has_issue_indices = set()
    status_errors = []

    for entry in para_cov:
        if not isinstance(entry, dict):
            continue
        pi = entry.get("paragraph_index")
        if pi is None:
            continue
        covered_indices.add(pi)
        status = entry.get("status", "")
        if status == "has_issue":
            has_issue_indices.add(pi)
        elif status != "clean":
            status_errors.append(str(pi))

    if status_errors:
        errors.append({
            "check": "paragraph_coverage",
            "severity": "error",
            "message": f"段落 {', '.join(status_errors[:10])} 的 status 不是 'clean' 或 'has_issue'。",
        })

    # 与 split_target 对比
    if split_target:
        expected_indices = extract_paragraph_indices(split_target)
        missing = expected_indices - covered_indices
        extra = covered_indices - expected_indices
        coverage_pct = round(len(covered_indices & expected_indices) / max(len(expected_indices), 1) * 100, 1)

        if missing:
            errors.append({
                "check": "paragraph_coverage",
                "severity": "error",
                "message": f"覆盖率 {coverage_pct}%（缺 {len(missing)} 段: {sorted(missing)[:10]}{'...' if len(missing) > 10 else ''}）——必须 100%。",
            })
        if extra:
            warnings.append({
                "check": "paragraph_coverage",
                "severity": "warning",
                "message": f"paragraph_coverage 包含 {len(extra)} 个 split_target 中不存在的段落索引。",
            })
    else:
        coverage_pct = 100.0

    # 铁律 E：has_issue 总数必须 > 0
    if len(has_issue_indices) == 0:
        errors.append({
            "check": "iron_law_E",
            "severity": "error",
            "message": "铁律 E 违反：全文档没有一段标记为 has_issue。Phase 4 语义审查等于空跑。必须换模型重审。",
        })

    return errors, warnings, len(has_issue_indices)


def validate_issues(issues: list) -> tuple[list[dict], list[dict]]:
    """校验 issues 列表。

    Returns:
        (errors, warnings)
    """
    errors = []
    warnings = []

    if not isinstance(issues, list):
        errors.append({
            "check": "issues",
            "severity": "error",
            "message": f"issues 必须是列表，实际 {type(issues).__name__}。",
        })
        return errors, warnings

    issues_missing_fields = []
    issues_bad_severity = []
    issues_bad_justification = []
    issues_bad_confidence = []

    for i, iss in enumerate(issues):
        if not isinstance(iss, dict):
            issues_missing_fields.append(f"[{i}] 不是对象（{type(iss).__name__}）")
            continue

        # 必填字段
        missing = [f for f in ISSUE_REQUIRED_FIELDS if not iss.get(f)]
        if missing:
            issues_missing_fields.append(f"[P{iss.get('paragraph_index', '?')}] 缺: {missing}")

        # severity
        sev = iss.get("severity", "")
        if sev and sev not in VALID_SEVERITIES:
            issues_bad_severity.append(f"[P{iss.get('paragraph_index', '?')}] severity='{sev}'")

        # severity_justification
        just = iss.get("severity_justification", "")
        if just and just not in VALID_JUSTIFICATIONS:
            issues_bad_justification.append(f"[P{iss.get('paragraph_index', '?')}] justification='{just}'")

        # confidence
        conf = iss.get("confidence", "")
        if conf and conf not in VALID_CONFIDENCES:
            issues_bad_confidence.append(f"[P{iss.get('paragraph_index', '?')}] confidence='{conf}'")

    if issues_missing_fields:
        errors.append({
            "check": "issues",
            "severity": "error",
            "message": f"{len(issues_missing_fields)} 条 issue 缺少必填字段: {issues_missing_fields[:5]}{'...' if len(issues_missing_fields) > 5 else ''}",
        })
    if issues_bad_severity:
        errors.append({
            "check": "issues",
            "severity": "error",
            "message": f"非法 severity 值: {issues_bad_severity[:5]}",
        })
    if issues_bad_justification:
        errors.append({
            "check": "issues",
            "severity": "error",
            "message": f"非法 severity_justification 值: {issues_bad_justification[:5]}",
        })
    if issues_bad_confidence:
        warnings.append({
            "check": "issues",
            "severity": "warning",
            "message": f"非法 confidence 值: {issues_bad_confidence[:5]}",
        })

    # 密度检查：issues 总数 < 段落数的 2%
    # （此处只做统计，阈值判断在 calibrate_severity.py 的 flag 阶段）
    if len(issues) == 0:
        warnings.append({
            "check": "issues",
            "severity": "warning",
            "message": "issues 列表为空——没有发现任何问题。如果文档较长，这极不正常。",
        })

    return errors, warnings


def validate_phase3_verdicts(
    verdicts: list[dict],
    verdict_sheet: dict | None,
) -> tuple[list[dict], list[dict]]:
    """校验 phase3_verdicts：Phase 3 每条 finding 是否都有判决。

    Returns:
        (errors, warnings)
    """
    errors = []
    warnings = []

    if verdict_sheet is None:
        # 没有 verdict sheet → 无法校验
        warnings.append({
            "check": "phase3_verdicts",
            "severity": "warning",
            "message": "未提供 --verdict-sheet，跳过 Phase 3 verdict 完整性校验。",
        })
        return errors, warnings

    expected_ids = {v["verdict_id"] for v in verdict_sheet.get("verdicts", [])}
    if not expected_ids:
        # Phase 3 没发现任何问题，不需要 verdicts
        return errors, warnings

    if not isinstance(verdicts, list):
        errors.append({
            "check": "phase3_verdicts",
            "severity": "error",
            "message": "phase3_verdicts 必须是数组，但 Phase 4 输出中缺少此字段或格式错误。",
        })
        return errors, warnings

    actual_ids = set()
    bad_verdicts = []
    short_explanations = []
    confirmed_count = 0

    for v in verdicts:
        if not isinstance(v, dict):
            continue
        vid = v.get("verdict_id", "")
        actual_ids.add(vid)

        # verdict 枚举
        verdict = v.get("verdict", "")
        if verdict not in VALID_VERDICTS:
            bad_verdicts.append(f"{vid}: '{verdict}'")
        if verdict == "confirmed":
            confirmed_count += 1

        # explanation 长度
        expl = v.get("explanation", "")
        cn_count = count_chinese_chars(expl)
        if cn_count < 20:
            short_explanations.append(f"{vid}: {cn_count} 个中文字（要求 ≥20）")

    # 完整性
    missing_ids = expected_ids - actual_ids
    extra_ids = actual_ids - expected_ids

    if missing_ids:
        errors.append({
            "check": "phase3_verdicts",
            "severity": "error",
            "message": f"有 {len(missing_ids)} 条 Phase 3 发现未被 Phase 4 判决: {sorted(missing_ids)[:5]}{'...' if len(missing_ids) > 5 else ''}",
        })
    if extra_ids:
        warnings.append({
            "check": "phase3_verdicts",
            "severity": "warning",
            "message": f"phase3_verdicts 包含 {len(extra_ids)} 个不在 verdict_sheet 中的 ID（可能为新增）。",
        })
    if bad_verdicts:
        errors.append({
            "check": "phase3_verdicts",
            "severity": "error",
            "message": f"非法 verdict 值: {bad_verdicts[:5]}（合法值: {sorted(VALID_VERDICTS)}）",
        })
    if short_explanations:
        errors.append({
            "check": "phase3_verdicts",
            "severity": "error",
            "message": f"{len(short_explanations)} 条判决的解释不足 20 个中文字: {short_explanations[:3]}{'...' if len(short_explanations) > 3 else ''}",
        })

    # 全部 dismiss → ERROR（v2.16 升级：从 warning 改为 error）
    total = len(expected_ids)
    if total > 0 and confirmed_count == 0:
        errors.append({
            "check": "phase3_verdicts_all_dismissed",
            "severity": "error",
            "message": (
                f"Phase 3 的 {total} 条发现全部被判为误报（confirmed=0/{total}）。"
                f"统计上不可能——即使在最精确的术语库中，也不会有 0% 的机械发现成立。"
                f"AI 用笼统理由批量 dismiss 了所有发现。必须逐条重判，至少确认部分发现。"
            ),
        })
    elif total > 0 and confirmed_count / total < 0.05:
        warnings.append({
            "check": "phase3_verdicts_near_zero",
            "severity": "warning",
            "message": (
                f"Phase 3 发现的确认率仅 {round(confirmed_count/total*100, 1)}% "
                f"（{confirmed_count}/{total}）。异常偏低，建议抽查 5 条。"
            ),
        })

    return errors, warnings


# ══════════════════════════════════════════════════════════════
# v2.16 新增：内容质量校验
# ══════════════════════════════════════════════════════════════

def validate_verdict_uniqueness(
    verdicts: list[dict],
    verdict_sheet: dict | None = None,
) -> tuple[list[dict], list[dict]]:
    """V6: 检测判决解释的模板化复制粘贴（v2.16 新增）。

    如果大量 verdict 使用相同/高度相似的 explanation，
    说明 AI 没有逐条审查，而是用模板回复批量处理。

    Returns:
        (errors, warnings)
    """
    errors = []
    warnings = []

    if not verdicts or not isinstance(verdicts, list):
        return errors, warnings

    # 提取所有非空 explanation
    explanations = []
    for v in verdicts:
        if isinstance(v, dict):
            expl = v.get("explanation", "").strip()
            if expl:
                explanations.append(expl)

    total = len(explanations)
    if total < 3:
        return errors, warnings

    # 精确匹配检测
    from collections import Counter
    counter = Counter(explanations)
    unique_count = len(counter)
    uniqueness_pct = unique_count / total

    if uniqueness_pct < 0.3:
        most_common_expl, most_common_count = counter.most_common(1)[0]
        errors.append({
            "check": "verdict_copy_paste",
            "severity": "error",
            "message": (
                f"V6 模板化检测：{total} 条判决中仅 {unique_count} 种不同解释 "
                f"（唯一率 {uniqueness_pct:.0%}，阈值 30%）。"
                f"最常见解释重复 {most_common_count}/{total} 次: "
                f"\"{most_common_expl[:60]}{'...' if len(most_common_expl) > 60 else ''}\""
                f" ——AI 用模板回复批量处理，未逐条审查。必须重新逐条判决，"
                f"每条给出针对该术语/数字的具体理由。"
            ),
        })
    elif uniqueness_pct < 0.5:
        warnings.append({
            "check": "verdict_low_uniqueness",
            "severity": "warning",
            "message": (
                f"判决解释唯一率仅 {uniqueness_pct:.0%}（{unique_count}/{total}），"
                f"可能存在模板化倾向，建议抽查。"
            ),
        })

    return errors, warnings


def validate_issue_quantity(
    issues: list,
    total_paragraphs: int,
) -> tuple[list[dict], list[dict]]:
    """V7: 检测异常低的 issue 数量（v2.16 新增）。

    如果总 issue 数远低于文档规模对应的合理下限，
    说明 AI 没有认真审查。

    阈值设计：
      - 0 issues 任何情况 → ERROR（翻译文档不可能完全无问题）
      - 1 issue + >30 段 → ERROR（仅发现一个明显错别字 = 敷衍）
      - < 3 issues + >50 段 → ERROR
      - 密度 < 2% → WARNING

    Returns:
        (errors, warnings)
    """
    errors = []
    warnings = []

    if total_paragraphs <= 0:
        return errors, warnings

    n_issues = len(issues) if isinstance(issues, list) else 0
    density_pct = round(n_issues / total_paragraphs * 100, 1)

    if n_issues == 0:
        errors.append({
            "check": "zero_issues",
            "severity": "error",
            "message": (
                f"V7 零 issue 检测：{total_paragraphs} 段文档中 issues 数为 0。"
                f"任何翻译文档都不可能完全没有问题。Phase 4 等于空跑。必须换模型重审。"
            ),
        })
    elif n_issues == 1 and total_paragraphs > 30:
        errors.append({
            "check": "single_issue",
            "severity": "error",
            "message": (
                f"V7 单 issue 检测：{total_paragraphs} 段文档仅发现 1 条 issue。"
                f"这极可能是 AI 敷衍（如仅发现一个明显错别字而忽略所有翻译质量问题）。"
                f"必须重新审查全部段落。"
            ),
        })
    elif n_issues < 3 and total_paragraphs > 50:
        errors.append({
            "check": "too_few_issues",
            "severity": "error",
            "message": (
                f"V7 issue 数量异常：{total_paragraphs} 段文档仅发现 {n_issues} 条 issue "
                f"（< 3 条）。Phase 4 审查不完整。必须重审。"
            ),
        })
    elif n_issues < max(5, total_paragraphs * 0.02):
        warnings.append({
            "check": "low_issue_density",
            "severity": "warning",
            "message": (
                f"Issue 密度 = {density_pct}%（{n_issues} 条 / {total_paragraphs} 段），"
                f"低于建议阈值。建议换模型复核。"
            ),
        })

    return errors, warnings


# ══════════════════════════════════════════════════════════════
# 主校验逻辑
# ══════════════════════════════════════════════════════════════

def validate_all(
    issues_data,
    verdict_sheet: dict | None = None,
    split_target: list[dict] | None = None,
    phase3_issues: dict | None = None,
) -> dict:
    """执行所有校验，返回完整的 validation report。

    Args:
        issues_data: issues_phase4.json 的内容
        verdict_sheet: phase3_verdict_sheet.json 的内容
        split_target: split_target.json 的内容
        phase3_issues: issues_mechanical.json 的内容

    Returns:
        {
            "passed": bool,
            "errors": [...],
            "warnings": [...],
            "stats": {...},
            "action_required": str or None
        }
    """
    all_errors = []
    all_warnings = []

    # 1. 顶层结构
    all_errors.extend(validate_top_level(issues_data))

    # 如果是列表格式，直接返回（后续校验无意义）
    if not isinstance(issues_data, dict):
        passed = len(all_errors) == 0
        return {
            "passed": passed,
            "errors": all_errors,
            "warnings": all_warnings,
            "stats": {"phase": "4.35", "version": "2.16"},
            "action_required": "issues_phase4.json 顶层结构错误。修复后重新验证。" if not passed else None,
        }

    # 2. dimension_coverage
    dim_errors, dim_warnings = validate_dimension_coverage(
        issues_data.get("dimension_coverage", {}), phase3_issues
    )
    all_errors.extend(dim_errors)
    all_warnings.extend(dim_warnings)

    # 3. paragraph_coverage
    para_errors, para_warnings, has_issue_count = validate_paragraph_coverage(
        issues_data.get("paragraph_coverage", []), split_target
    )
    all_errors.extend(para_errors)
    all_warnings.extend(para_warnings)

    # 4. issues
    issues = issues_data.get("issues", [])
    para_cov = issues_data.get("paragraph_coverage", [])

    # total_paras 必须从 split_target 的 total_paragraphs 字段获取
    # （split_target 本身是 dict，len(split_target) 返回的是顶层 key 数而非段落数）
    if isinstance(split_target, dict):
        total_paras = split_target.get("total_paragraphs", len(para_cov))
    elif isinstance(split_target, list):
        total_paras = len(split_target)
    else:
        total_paras = len(para_cov)

    issue_errors, issue_warnings = validate_issues(issues)
    all_errors.extend(issue_errors)
    all_warnings.extend(issue_warnings)

    # 5. phase3_verdicts（含 v2.16 confirmed=0 ERROR 升级）
    verdict_errors, verdict_warnings = validate_phase3_verdicts(
        issues_data.get("phase3_verdicts", []), verdict_sheet
    )
    all_errors.extend(verdict_errors)
    all_warnings.extend(verdict_warnings)

    # 6. verdict 解释唯一性（v2.16 新增 — 检测 copy-paste 模板化）
    uniq_errors, uniq_warnings = validate_verdict_uniqueness(
        issues_data.get("phase3_verdicts", []), verdict_sheet
    )
    all_errors.extend(uniq_errors)
    all_warnings.extend(uniq_warnings)

    # 7. issue 数量检测（v2.16 新增 — 检测异常低的 issue 数）
    issue_qty_errors, issue_qty_warnings = validate_issue_quantity(
        issues, max(total_paras, 1)
    )
    all_errors.extend(issue_qty_errors)
    all_warnings.extend(issue_qty_warnings)

    # 统计
    stats = {
        "phase": "4.35",
        "version": "2.16",
        "total_paragraphs": max(total_paras, 1),
        "covered_paragraphs": len(para_cov),
        "has_issue_paragraphs": has_issue_count,
        "total_issues": len(issues),
        "severity_distribution": {
            "critical": len([i for i in issues if i.get("severity") == "critical"]),
            "medium": len([i for i in issues if i.get("severity") == "medium"]),
            "low": len([i for i in issues if i.get("severity") == "low"]),
        },
        "dimension_coverage_check_ids": len(issues_data.get("dimension_coverage", {})),
        "expected_check_ids": len(ALL_CHECK_IDS),
        "phase3_verdict_count": len(issues_data.get("phase3_verdicts", [])),
        "expected_verdict_count": len(verdict_sheet.get("verdicts", [])) if verdict_sheet else 0,
    }

    # v2.16 统计: 解释唯一性
    verdicts_for_stats = issues_data.get("phase3_verdicts", [])
    if isinstance(verdicts_for_stats, list) and verdicts_for_stats:
        from collections import Counter
        expl_counter = Counter(
            v.get("explanation", "").strip()
            for v in verdicts_for_stats
            if isinstance(v, dict) and v.get("explanation", "").strip()
        )
        stats["unique_explanations"] = len(expl_counter)
        stats["total_explanations"] = sum(expl_counter.values())
        stats["explanation_uniqueness_pct"] = round(
            len(expl_counter) / max(sum(expl_counter.values()), 1) * 100, 1
        )
    else:
        stats["unique_explanations"] = 0
        stats["total_explanations"] = 0
        stats["explanation_uniqueness_pct"] = 0.0

    passed = len(all_errors) == 0
    action = None if passed else "修复以上 error 后再运行 validate_phase4_output.py。全部通过后才能进入 Phase 4.4。"

    return {
        "passed": passed,
        "errors": all_errors,
        "warnings": all_warnings,
        "stats": stats,
        "action_required": action,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Phase 4.35: 硬校验 issues_phase4.json 的结构完整性"
    )
    parser.add_argument("--issues", required=True,
                        help="Phase 4 输出 (issues_phase4.json)")
    parser.add_argument("--verdict-sheet",
                        help="Phase 3 判决书 (phase3_verdict_sheet.json) — 可选，用于校验 phase3_verdicts 完整性")
    parser.add_argument("--split-target",
                        help="拆分后的目标文档 (split_target.json) — 可选，用于校验段落覆盖率")
    parser.add_argument("--phase3-issues",
                        help="Phase 3 机械检查输出 (issues_mechanical.json) — 可选，用于交叉验证")
    parser.add_argument("--output", "-o", required=True,
                        help="输出验证报告路径 (phase4_validation_report.json)")
    args = parser.parse_args()

    # 加载输入
    issues_data = load_json(args.issues)
    if isinstance(issues_data, dict) and "_error" in issues_data:
        print(f"ERROR: 无法加载 issues 文件: {issues_data['_error']}")
        # 输出失败报告
        report = {
            "passed": False,
            "errors": [{"check": "file_load", "severity": "error",
                        "message": f"无法加载 {args.issues}: {issues_data['_error']}"}],
            "warnings": [],
            "stats": {},
            "action_required": f"确认 {args.issues} 文件存在且为有效 JSON。",
        }
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        sys.exit(1)

    verdict_sheet = None
    if args.verdict_sheet:
        verdict_sheet = load_json(args.verdict_sheet)
        if isinstance(verdict_sheet, dict) and "_error" in verdict_sheet:
            print(f"WARNING: 无法加载 verdict-sheet: {verdict_sheet['_error']}，将跳过 Phase 3 verdict 校验。")
            verdict_sheet = None

    split_target = None
    if args.split_target:
        split_target = load_json(args.split_target)
        if isinstance(split_target, dict) and "_error" in split_target:
            print(f"WARNING: 无法加载 split-target: {split_target['_error']}，将跳过段落覆盖校验。")
            split_target = None

    phase3_issues = None
    if args.phase3_issues:
        phase3_issues = load_json(args.phase3_issues)
        if isinstance(phase3_issues, dict) and "_error" in phase3_issues:
            print(f"WARNING: 无法加载 phase3-issues: {phase3_issues['_error']}，将跳过交叉验证。")
            phase3_issues = None

    # 执行校验
    report = validate_all(issues_data, verdict_sheet, split_target, phase3_issues)

    # 输出
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 终端摘要
    n_err = len(report["errors"])
    n_warn = len(report["warnings"])
    if report["passed"]:
        print(f"✅ 校验通过（{n_warn} 条警告）")
    else:
        print(f"❌ 校验失败：{n_err} 条错误，{n_warn} 条警告")
        print()
        for err in report["errors"]:
            print(f"  [{err['check']}] {err['message'][:120]}")
        print()
        if report["action_required"]:
            print(f"→ {report['action_required']}")

    print(f"报告: {args.output}")
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
