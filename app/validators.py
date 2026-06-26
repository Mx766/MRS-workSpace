"""
翻译准确性验证器 — 数字/符号/化学式/单位保护

用法:
    from validators import extract_critical_items, verify_preservation

    items = extract_critical_items("Vapour pressure < 0.001 mm Hg @25°C")
    violations = verify_preservation(items, "蒸汽压 < 0.001 mm Hg @25°C")
    # violations = [] (所有关键项都保留了)

    violations = verify_preservation(items, "蒸汽压在25度时小于0.001毫米汞柱")
    # violations = ["数字 0.001", "符号 <", "单位 mm Hg", "温度 @25°C"]
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional

# ═══════════════════════════════════════
# 关键项类型与正则
# ═══════════════════════════════════════

@dataclass
class CriticalItem:
    """翻译中不应消失的内容"""
    category: str       # number, temperature, chemical, cas, regulation, email, phone, symbol, unit
    value: str          # 原始字符串
    position: int = 0   # 在原文中的位置

# 各类正则模式
PATTERNS = {
    'temperature': r'\d+\s*[°℃]\s*[CF](?:\s*\(\d+\s*[°℃]\s*[CF]\))?|\d+\s*[°℃](?:\s*[CF])?',  # 25°C, 77 F, 350 °C / 662F
    'cas_number': r'\b\d{2,7}-\d{2}-\d\b',  # CAS 26007-43-2
    'email': r'\S+@\S+\.\S+',  # info@topas.com
    'phone': r'\+\d[\d\s\-\(\)\.]{6,20}',  # +1.703.527.3887
    'regulation': r'§\s*\d+(?:\.\d+)*(?:\s*CFR\s*\d+(?:\.\d+)*)?|\d+\s*CFR\s*\d+(?:\.\d+)*',  # §1910.1200, 29CFR 1910.1200
    'chemical': r'\b(?:[A-Z][a-z]?\d*){2,}\b',  # CO2, NaOH, H2SO4 (2个以上大写字母开头的组合)

    # 非化学式的常见缩写（排除列表）
    'NON_CHEMICAL': {
        'THE', 'AND', 'FOR', 'NOT', 'ARE', 'WAS', 'HAS', 'ALL', 'USE', 'USA', 'ISO', 'EN',
        'GHS', 'US', 'NIOSH', 'OSHA', 'HMIS', 'NFPA', 'ANSI', 'VOC', 'TSCA', 'SDS', 'MSDS',
        'CAS', 'TOPAS', 'IAF', 'IMDG', 'DOT', 'ICAO', 'TI', 'EC', 'JP', 'NZ', 'TW', 'KR',
        'CN', 'CA', 'AU', 'EU', 'UN', 'NO', 'OK', 'MI', 'TX', 'OH', 'PA', 'VA', 'ID',
        'TOP', 'END', 'NEW', 'OLD', 'LOW', 'HOT', 'DRY', 'WET', 'CUT', 'SET', 'GET', 'PUT',
        'RUN', 'FIT', 'SIT', 'HIT', 'BIT', 'TIN', 'ZIP', 'OEM', 'IF', 'OR', 'IN', 'ON',
        'AT', 'BY', 'TO', 'AS', 'SO', 'BE', 'DO', 'GO', 'NO', 'WE', 'HE', 'IT', 'IS',
    },
    'percentage': r'\d+(?:\.\d+)?\s*%',  # 0.5 %, 95%
    'number_with_unit': r'\d+(?:\.\d+)?\s*(?:mm\s*Hg|g/l|mg|kg|ml|L|℃|°C|°F|ppm|ppb|m/s|kPa|bar|atm|h|min|s)\b',  # 数字+单位
    'decimal_number': r'(?<!\w)\d+\.\d+(?!\w)',  # 0.001, 75.5 (纯小数，不含日期)
    'special_symbol': r'[<>≤≥±≈×÷]',  # 数学/比较符号
    'version_code': r'\bV\d+(?:\.\d+)*\b',  # V8.00
}

# 复合温度模式 — 最高优先级
TEMPERATURE_DETAILED = re.compile(
    r'\d+\s*[°℃]\s*[CF]\s*(?:\(\s*\d+\s*[°℃]\s*[CF]\s*\))?|'  # 25°C (77 F)
    r'\d+\s*[°℃](?:\s*[CF])?|'                                    # 25°C or 25°C F
    r'@\s*\d+\s*[°℃](?:\s*[CF])?'                                  # @25°C
)

def extract_critical_items(text: str) -> List[CriticalItem]:
    """从原文中提取所有不应在翻译中丢失的关键项"""
    if not text:
        return []

    items = []
    seen_positions = set()  # 避免同一位置重复匹配

    # 1. 温度 — 最高优先级，避免被其他模式错误匹配
    for m in TEMPERATURE_DETAILED.finditer(text):
        start, end = m.start(), m.end()
        if not any(start <= p < end for p in seen_positions):
            items.append(CriticalItem('temperature', m.group(), start))
            seen_positions.add(start)

    # 2. 法规号
    for m in re.finditer(PATTERNS['regulation'], text):
        start, end = m.start(), m.end()
        if not any(start <= p < end for p in seen_positions):
            items.append(CriticalItem('regulation', m.group(), start))
            for pos in range(start, end):
                seen_positions.add(pos)

    # 3. CAS号
    for m in re.finditer(PATTERNS['cas_number'], text):
        start, end = m.start(), m.end()
        if not any(start <= p < end for p in seen_positions):
            items.append(CriticalItem('cas_number', m.group(), start))
            for pos in range(start, end):
                seen_positions.add(pos)

    # 4. 邮箱/电话
    for category in ['email', 'phone']:
        for m in re.finditer(PATTERNS[category], text):
            start, end = m.start(), m.end()
            if not any(start <= p < end for p in seen_positions):
                items.append(CriticalItem(category, m.group(), start))
                # 覆盖整个范围，防止内部数字被重复匹配
                for pos in range(start, end):
                    seen_positions.add(pos)

    # 5. 数字+单位
    for m in re.finditer(PATTERNS['number_with_unit'], text):
        if not any(m.start() <= p < m.end() for p in seen_positions):
            items.append(CriticalItem('number_with_unit', m.group(), m.start()))
            seen_positions.add(m.start())

    # 6. 纯小数（排除已匹配位置）
    for m in re.finditer(PATTERNS['decimal_number'], text):
        val = m.group()
        # 排除：属于CAS号、电话号码、法规号的一部分
        if any(m.start() <= p < m.end() for p in seen_positions):
            continue
        # 排除电话号里的片段
        if m.start() > 0 and text[m.start() - 1] == '+':
            continue
        items.append(CriticalItem('decimal_number', val, m.start()))
        seen_positions.add(m.start())

    # 7. 百分比
    for m in re.finditer(PATTERNS['percentage'], text):
        if not any(m.start() <= p < m.end() for p in seen_positions):
            items.append(CriticalItem('percentage', m.group(), m.start()))
            seen_positions.add(m.start())

    # 8. 特殊符号
    for m in re.finditer(PATTERNS['special_symbol'], text):
        if not any(m.start() <= p < m.end() for p in seen_positions):
            items.append(CriticalItem('symbol', m.group(), m.start()))
            seen_positions.add(m.start())

    # 9. 化学式 (简单)
    for m in re.finditer(PATTERNS['chemical'], text):
        val = m.group()
        if val.upper() in PATTERNS['NON_CHEMICAL']:
            continue
        if not any(m.start() <= p < m.end() for p in seen_positions):
            items.append(CriticalItem('chemical', val, m.start()))
            seen_positions.add(m.start())

    # 10. 版本号
    for m in re.finditer(PATTERNS['version_code'], text):
        if not any(m.start() <= p < m.end() for p in seen_positions):
            items.append(CriticalItem('version', m.group(), m.start()))
            seen_positions.add(m.start())

    return items

# ═══════════════════════════════════════
# 验证
# ═══════════════════════════════════════

HIGH_PRIORITY = {'temperature', 'cas_number', 'regulation', 'number_with_unit', 'decimal_number', 'percentage'}
MEDIUM_PRIORITY = {'email', 'phone', 'version', 'symbol', 'chemical'}

def verify_preservation(items: List[CriticalItem], translated_text: str) -> List[dict]:
    """
    验证关键项是否在译文中保留
    返回: [{'category': 'temperature', 'value': '25°C', 'severity': 'high', 'found': False}, ...]
    """
    violations = []
    for item in items:
        found = item.value in translated_text
        # 对于数字+单位，只检查数字部分是否保留
        if not found and item.category == 'number_with_unit':
            # 提取数字部分检查
            num_match = re.search(r'(\d+(?:\.\d+)?)', item.value)
            if num_match and num_match.group(1) in translated_text:
                found = True

        if not found:
            severity = 'high' if item.category in HIGH_PRIORITY else 'medium'
            violations.append({
                'category': item.category,
                'value': item.value,
                'severity': severity,
                'found': False
            })
    return violations

def validate_translation(source_text: str, translated_text: str) -> dict:
    """
    完整验证：提取 → 验证 → 返回报告
    """
    items = extract_critical_items(source_text)
    violations = verify_preservation(items, translated_text)

    return {
        'total_items': len(items),
        'violations': violations,
        'violation_count': len(violations),
        'high_count': sum(1 for v in violations if v['severity'] == 'high'),
        'pass_rate': 1.0 - (len(violations) / max(len(items), 1)),
        'items_by_category': _group_by_category(items),
    }

def _group_by_category(items: List[CriticalItem]) -> dict:
    result = {}
    for item in items:
        if item.category not in result:
            result[item.category] = []
        result[item.category].append(item.value)
    return result
