"""
术语强制应用引擎

双层保障：
1. 翻译后：强制替换译文中残留的源术语（英文未翻译的）
2. 翻译后：验证目标术语是否出现在译文中

用法:
    from glossary_enforcer import enforce_glossary, verify_glossary

    matches = [("self-contained breathing apparatus", "自给式呼吸器"), ...]
    fixed, applied = enforce_glossary("消防员防护应包括self-contained breathing apparatus", matches)
    # fixed = "消防员防护应包括自给式呼吸器"
    # applied = [("self-contained breathing apparatus", "自给式呼吸器")]

    violations = verify_glossary(fixed, matches)
    # violations = [("自给式呼吸器", False)]  if target term not found
"""
import re
from typing import List, Tuple, Dict

# ═══════════════════════════════════════
# 术语强制替换
# ═══════════════════════════════════════

def enforce_glossary(
    translated_text: str,
    glossary_matches: List[Tuple[str, str]],
    case_sensitive: bool = False
) -> Tuple[str, List[Tuple[str, str]]]:
    """
    在译文中搜索残留的源术语（英文），强制替换为目标术语（中文）

    参数:
        translated_text: 模型翻译的文本
        glossary_matches: [(source, target), ...] 从 match_glossary() 获取
        case_sensitive: 是否区分大小写，默认不区分

    返回:
        (fixed_text, applied_terms): 修正后的文本, 实际被应用的术语列表
    """
    if not glossary_matches or not translated_text:
        return translated_text, []

    applied = []
    fixed = translated_text

    # 按源术语长度降序排列 — 长术语优先，避免部分匹配
    # e.g. "self-contained breathing apparatus" 应该在 "breathing apparatus" 之前
    sorted_terms = sorted(glossary_matches, key=lambda x: len(x[0]), reverse=True)

    for source, target in sorted_terms:
        if not source or not target:
            continue

        # 在译文中搜索源术语（英文）
        flags = 0 if case_sensitive else re.IGNORECASE
        if re.search(re.escape(source), fixed, flags):
            # 替换
            count_before = len(re.findall(re.escape(source), fixed, flags))
            fixed = re.sub(re.escape(source), target, fixed, flags=flags)
            count_after = len(re.findall(re.escape(source), fixed, flags))
            if count_before > count_after:
                applied.append((source, target, count_before - count_after))

    return fixed, applied


# ═══════════════════════════════════════
# 术语验证
# ═══════════════════════════════════════

def verify_glossary(
    translated_text: str,
    glossary_matches: List[Tuple[str, str]],
    case_sensitive: bool = False
) -> List[dict]:
    """
    验证目标术语是否出现在译文中

    返回: [{'source': 'xxx', 'expected': 'yyy', 'found': True/False}, ...]
    """
    violations = []
    flags = 0 if case_sensitive else re.IGNORECASE

    for source, target in glossary_matches:
        if not source or not target:
            continue

        # 检查1: 源术语（英文）是否还在译文中 — 不应该出现
        source_still_present = bool(re.search(re.escape(source), translated_text, flags))

        # 检查2: 目标术语（中文）是否在译文中 — 应该出现
        target_found = target in translated_text

        if source_still_present or not target_found:
            violations.append({
                'source': source,
                'target': target,
                'source_still_present': source_still_present,
                'target_found': target_found,
                'severity': 'high' if source_still_present else 'medium'
            })

    return violations


# ═══════════════════════════════════════
# 综合：翻译后处理流水线
# ═══════════════════════════════════════

def post_process_translation(
    source_text: str,
    translated_text: str,
    glossary_matches: List[Tuple[str, str]]
) -> Dict:
    """
    翻译后处理：术语强制替换 + 验证

    返回:
        {
            'final_text': str,           # 修正后的译文
            'terms_applied': int,        # 强制替换的术语数
            'terms_applied_list': list,  # 强制替换的术语详情
            'term_violations': list,     # 术语违规
            'violation_count': int,      # 总违规数
            'perfect': bool,             # 是否完美（0违规）
        }
    """
    # Step 1: 强制替换
    fixed_text, applied = enforce_glossary(translated_text, glossary_matches)

    # Step 2: 验证
    violations = verify_glossary(fixed_text, glossary_matches)

    return {
        'final_text': fixed_text,
        'terms_applied': len(applied),
        'terms_applied_list': applied,
        'term_violations': violations,
        'violation_count': len(violations),
        'perfect': len(violations) == 0,
    }
