#!/usr/bin/env python3
"""
Phase 3.5: 上下文注入 — 分析文档，生成 Phase 4 注意力锚点

在 Phase 3（机械检查）之后、Phase 4（语义审查）之前运行。
分析源文+译文+术语库+Phase 3 结果，输出 cache/phase4_context.json，
供 Phase 4 的 batch prompt 使用，确保不同模型关注相同的重点。

输出包含:
  - domain: 文档领域检测结果
  - key_terminology: 高频术语 + 必须验证的译法
  - high_risk_paragraphs: 高风险段落（含数字/术语/复杂结构）
  - structure_checklist: 结构完整性检查项
  - mandatory_checks: 不可跳过的检查项
  - domain_escalation_rules: 领域特定的严重度升级规则
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


# ══════════════════════════════════════════════════════════════
# 领域检测关键词模式
# ══════════════════════════════════════════════════════════════

DOMAIN_PATTERNS = {
    "医疗器械注册": {
        "keywords": [
            r'\bFDA\b', r'\bCE\s?[Mm]ark', r'\bMDR\b', r'\bISO\s*13485\b',
            r'\bclinical\s+trial\b', r'\bclinical\s+evaluation\b', r'\bmedical\s+device\b',
            r'\bintended\s+use\b', r'\bIFU\b', r'\binstructions\s+for\s+use\b',
            r'\b biocompatib', r'\bsteril', r'\bimplant\b', r'\bcatheter\b',
            r'\bultrasound\b', r'\bhandpiece', r'\btransducer\b', r'\bdermal\b',
            r'\bcollagen\b', r'\bepidermis\b', r'\bdermis\b', r'\bsubcutaneous\b',
            r'\btreatment\s+area\b', r'\bpatient\b', r'\badverse\s+event',
        ],
        "domain_notes": "医疗器械技术文档。术语应遵循医疗器械行业标准（ISO 13485/14971），临床术语使用 GCP 规范译法。"
    },
    "药物临床": {
        "keywords": [
            r'\bphase\s+[I]{1,3}\b', r'\brandomi[sz]ed\b', r'\bplacebo\b',
            r'\bdouble.?blind\b', r'\bpharmacokinetic', r'\bpharmacodynamic',
            r'\bCmax\b', r'\bAUC\b', r'\bhalf.?life\b', r'\bdosage\b',
            r'\bmg/kg\b', r'\bQD\b', r'\bBID\b', r'\bcontraindication',
            r'\bNCT\d{8}\b', r'\bINN\b', r'\binvestigational\s+drug\b',
        ],
        "domain_notes": "药物临床试验文档。术语应遵循 ICH-GCP 规范，药品名称使用 INN 中文译名。"
    },
    "网络安全评估": {
        "keywords": [
            r'\bpenetration\s+test', r'\bvulnerability\b', r'\bexploit\b',
            r'\bCVSS\b', r'\bCVE\b', r'\bOWASP\b', r'\bNIST\b',
            r'\bbrute.?force\b', r'\bfuzz\b', r'\battack\s+vector\b',
            r'\bprivilege\s+escalation\b', r'\bSSH\b', r'\bTLS\b',
            r'\bauthentication\b', r'\bauthori[sz]ation\b', r'\bencrypt',
            r'\bTOE\b', r'\btarget\s+of\s+evaluation\b', r'\bsecurity\s+assessment\b',
            r'\bBlack.?box\b', r'\bport\s+scan', r'\bUSB\s+fuzz',
        ],
        "domain_notes": "网络安全渗透测试报告。术语应遵循 OWASP/NIST 规范，CVSS 评分术语使用标准译法。"
    },
    "安全数据表": {
        "keywords": [
            r'\bMSDS\b', r'\bSDS\b', r'\bCAS\s*No', r'\bGHS\b',
            r'\bH\d{3}\b', r'\bP\d{3}\b', r'\bhazard\s+statement',
            r'\bprecautionary\s+statement', r'\bLD50\b', r'\bLC50\b',
            r'\bflammable\b', r'\bcorrosive\b', r'\btoxic\b', r'\bcarcinogen',
        ],
        "domain_notes": "安全数据表。术语应遵循 GHS 分类和标签规范（GB/T 16483）。CAS 号、H/P 语句保持原文格式。"
    },
    "专利文献": {
        "keywords": [
            r'\bclaims?\b', r'\bembodiment\b', r'\bprior\s+art\b',
            r'\bherein\b', r'\bthereof\b', r'\bwhereby\b', r'\bwherein\b',
            r'\binvention\b', r'\bpatent\b', r'\bUS\d{7}', r'\bWO\d{8}',
            r'\bsaid\s+\w+\b', r'\bapparatus\b', r'\bconfigured\s+to\b',
        ],
        "domain_notes": "专利文献。权利要求术语必须保持法律精确性，功能性语言不可意译。"
    },
}

# ══════════════════════════════════════════════════════════════
# 领域→强制检查项映射
# ══════════════════════════════════════════════════════════════

DOMAIN_MANDATORY_CHECKS = {
    "医疗器械注册": [
        {"check_id": "2.23", "name": "术语过于泛化", "reason": "医疗器械术语有严格行业译法，MT 容易泛化（如探头、手柄、治疗头）"},
        {"check_id": "4.3", "name": "跨段术语统一", "reason": "器械名称、部件名称、测量指标必须在全文中保持一致"},
        {"check_id": "3.1", "name": "数值单位", "reason": "医疗器械文档含大量测量值和单位（mm, J, MHz, kg/m^2），单位换算风险高"},
        {"check_id": "1.4", "name": "错译", "reason": "器械部件名（handpiece, transducer, probe）易被误译为日常词汇"},
        {"check_id": "2.5", "name": "褒贬色彩", "reason": "医疗器械安全性描述中 result in/due to/lead to 容易译出负面色彩"},
    ],
    "药物临床": [
        {"check_id": "3.1", "name": "数值单位", "reason": "临床试验含大量统计学数值和剂量单位，错误可能影响安全性判断"},
        {"check_id": "4.1", "name": "术语库一致", "reason": "药品名、终点指标、AE 术语必须与标准术语库一致"},
        {"check_id": "2.23", "name": "术语过于泛化", "reason": "MT 倾向将临床术语泛化为日常表达（如 adverse reaction→副作用）"},
        {"check_id": "1.4", "name": "错译", "reason": "临床终点、统计方法术语专业性强，容易译错"},
        {"check_id": "2.6", "name": "近义词混淆", "reason": "临床文档中 efficacy/effectiveness、safety/tolerability 等近义词容易混淆"},
    ],
    "网络安全评估": [
        {"check_id": "4.1", "name": "术语库一致", "reason": "网络安全术语有标准译法（CVE/NIST/OWASP），不可随意翻译"},
        {"check_id": "2.23", "name": "术语过于泛化", "reason": "安全评估术语容易泛化（penetration→渗透而非穿刺，attack→攻击而非袭击）"},
        {"check_id": "1.4", "name": "错译", "reason": "安全机制名称（TLS, SSH, brute-force）有固定译法，不能字面翻译"},
        {"check_id": "2.12", "name": "翻译腔", "reason": "英文安全报告多用被动语态，中文需转换为主动/无主语句"},
        {"check_id": "3.3", "name": "符号格式", "reason": "版本号、IP 地址、端口号、哈希值等符号序列必须完全一致"},
    ],
    "安全数据表": [
        {"check_id": "4.1", "name": "术语库一致", "reason": "GHS 危害/防范说明有法定译法，不可意译"},
        {"check_id": "3.1", "name": "数值单位", "reason": "浓度、温度、压力等数值错误可能导致安全事故"},
        {"check_id": "3.4", "name": "CAS 号/标准号", "reason": "CAS 号、EC 号等标识符必须精确匹配"},
        {"check_id": "1.2", "name": "增译", "reason": "SDS 是法定文件，不可增加原文没有的警告或说明"},
        {"check_id": "1.4", "name": "错译", "reason": "危害/防范说明（H/P statements）有 GHS 官方中文译法"},
    ],
    "专利文献": [
        {"check_id": "1.1", "name": "完整性", "reason": "权利要求中的限定词（comprising, consisting of）有法律含义差异"},
        {"check_id": "2.25", "name": "字面直译", "reason": "said/the/present 等定冠词直译会产生中式法律英语"},
        {"check_id": "1.4", "name": "错译", "reason": "专利术语有法律约束力，一词之差可能改变保护范围"},
        {"check_id": "4.3", "name": "跨段术语统一", "reason": "同一发明特征在全文中必须使用统一译名"},
    ],
}

# ══════════════════════════════════════════════════════════════
# 领域→严重度升级规则
# ══════════════════════════════════════════════════════════════

DOMAIN_ESCALATION_RULES = {
    "医疗器械注册": {
        "medical_term_error": "critical",
        "unit_conversion_error": "critical",
        "safety_related_error": "critical",
        "connotation_error": "medium",
        "punctuation_style": "low",
    },
    "药物临床": {
        "dose_error": "critical",
        "endpoint_error": "critical",
        "ae_term_error": "critical",
        "statistical_error": "critical",
        "terminology_inconsistency": "medium",
    },
    "网络安全评估": {
        "vulnerability_misclassification": "critical",
        "cvss_scoring_error": "critical",
        "authentication_bypass": "critical",
        "port_protocol_error": "medium",
        "terminology_inconsistency": "medium",
    },
    "安全数据表": {
        "hazard_misstatement": "critical",
        "cas_number_error": "critical",
        "concentration_error": "critical",
        "first_aid_error": "critical",
    },
    "专利文献": {
        "claim_scope_error": "critical",
        "legal_term_mistranslation": "critical",
        "figure_reference_error": "medium",
    },
}

# 默认升级规则（未匹配到具体领域时使用）
DEFAULT_ESCALATION_RULES = {
    "outright_mistranslation": "critical",
    "unit_conversion_error": "critical",
    "number_mismatch": "critical",
    "client_term_violation": "critical",
    "terminology_inconsistency": "medium",
    "connotation_error": "medium",
    "unnatural_expression": "low",
    "punctuation_style": "low",
}


# ══════════════════════════════════════════════════════════════
# 1. 领域检测
# ══════════════════════════════════════════════════════════════

def detect_domain(source_text: str, glossary: dict | None = None) -> dict:
    """检测文档领域。

    通过关键词模式匹配统计各领域的命中数，选占比最高者。

    Args:
        source_text: 源文全部文本
        glossary: 术语库字典 (可选，用于加权)

    Returns:
        {primary, secondary, confidence, evidence_keywords, domain_notes}
    """
    source_lower = source_text.lower()
    domain_scores = {}

    for domain_name, config in DOMAIN_PATTERNS.items():
        hits = 0
        matched_keywords = []
        for pattern in config["keywords"]:
            matches = re.findall(pattern, source_lower, re.IGNORECASE)
            if matches:
                hits += len(matches)
                if len(matched_keywords) < 10:
                    matched_keywords.append(pattern.strip(r'\b'))
        domain_scores[domain_name] = {
            "hits": hits,
            "matched_keywords": matched_keywords,
            "notes": config["domain_notes"],
        }

    # 如果有术语库，用术语库领域分布加权
    if glossary and isinstance(glossary, dict) and 'terms' in glossary:
        glossary_terms = glossary['terms']
        term_domains = Counter()
        for key, info in glossary_terms.items():
            key_lower = key.lower().strip()
            if len(key_lower) >= 4 and key_lower in source_lower:
                domain = info.get('domain', '通用') if isinstance(info, dict) else '通用'
                term_domains[domain] += 1

        # 将术语库领域映射到 DOMAIN_PATTERNS 的领域
        for term_domain, count in term_domains.most_common():
            for pattern_domain in DOMAIN_PATTERNS:
                if any(word in term_domain for word in ['医学', '器械', '临床', '药物', '皮肤', '解剖', '影像']):
                    if '医疗器械' in pattern_domain or '药物' in pattern_domain:
                        domain_scores[pattern_domain]["hits"] += count

    # 排序
    ranked = sorted(domain_scores.items(), key=lambda x: x[1]["hits"], reverse=True)

    if not ranked or ranked[0][1]["hits"] == 0:
        return {
            "primary": "通用技术文档",
            "secondary": [],
            "confidence": 0.0,
            "evidence_keywords": [],
            "domain_notes": "未能自动识别领域。请根据文档类型手动指定领域。",
        }

    primary_name, primary_data = ranked[0]
    total_hits = sum(d["hits"] for _, d in ranked)
    confidence = primary_data["hits"] / max(total_hits, 1)

    secondary = []
    for name, data in ranked[1:3]:
        if data["hits"] > primary_data["hits"] * 0.3:
            secondary.append(name)

    return {
        "primary": primary_name,
        "secondary": secondary,
        "confidence": round(confidence, 2),
        "evidence_keywords": primary_data["matched_keywords"][:15],
        "domain_notes": primary_data["notes"],
    }


# ══════════════════════════════════════════════════════════════
# 2. 关键术语提取
# ══════════════════════════════════════════════════════════════

def extract_key_terminology(
    source_text: str,
    target_text: str,
    glossary: dict | None = None,
    min_occurrences: int = 3,
) -> list[dict]:
    """找出源文中出现 ≥min_occurrences 次的术语库术语，标注必须验证。

    交叉检查目标文：如果某术语的规范译法在目标文中不存在，标记 translation_status: missing。

    Args:
        source_text: 源文全部文本（按页或按段拼接）
        target_text: 译文全部文本
        glossary: 术语库字典 (terms key)
        min_occurrences: 最少出现次数阈值

    Returns:
        [{source, required_target, domain, count, is_critical, translation_status}]
    """
    if not glossary or not isinstance(glossary, dict) or 'terms' not in glossary:
        return []

    source_lower = source_text.lower()
    target_lower = target_text.lower()
    glossary_terms = glossary['terms']

    results = []
    for key, info in glossary_terms.items():
        term_src = info.get('source', key) if isinstance(info, dict) else key
        term_tgt = info.get('target', '') if isinstance(info, dict) else info
        domain = info.get('domain', '通用') if isinstance(info, dict) else '通用'

        if not term_src or not term_tgt:
            continue

        # 在源文中统计出现次数
        term_lower = term_src.lower().strip()
        if len(term_lower) < 4:  # 跳过太短的术语（容易大量误匹配）
            continue

        # 用词边界匹配
        pattern = re.compile(r'\b' + re.escape(term_lower) + r'\b', re.IGNORECASE)
        source_matches = pattern.findall(source_lower)
        count = len(source_matches)

        if count < min_occurrences:
            continue

        # 检查目标文中是否存在规范译法
        tgt_lower = term_tgt.lower().strip()
        translation_status = "present" if tgt_lower in target_lower else "missing"

        # 在标题或关键位置出现 → is_critical
        is_critical = (
            count >= 10 or
            translation_status == "missing" or
            bool(re.search(r'(?i)(?:heading|title|caption|table\s+\d+|figure\s+\d+).*' + re.escape(term_lower), source_text[:5000]))
        )

        results.append({
            "source": term_src,
            "required_target": term_tgt,
            "domain": domain,
            "count": count,
            "is_critical": is_critical,
            "translation_status": translation_status,
        })

    # 按出现次数降序，最多 30 条
    results.sort(key=lambda x: x["count"], reverse=True)
    return results[:30]


# ══════════════════════════════════════════════════════════════
# 3. 高风险段落识别
# ══════════════════════════════════════════════════════════════

def identify_high_risk_paragraphs(
    source_paras: list[dict],
    target_paras: list[dict],
    key_terminology: list[dict] | None = None,
    top_pct: float = 0.15,
) -> list[dict]:
    """对每段打分，识别高风险段落。

    评分因子:
      - 数字个数 × 3
      - 术语命中数 × 2
      - 超长句(>200 字) × 1
      - 比较逻辑标记 × 2
      - 单位缩写 × 1

    Args:
        source_paras: 源文段落列表 [{index, text}, ...]
        target_paras: 译文段落列表 [{index, text}, ...]
        key_terminology: 关键术语列表（用于术语命中计数）
        top_pct: 返回 top X% 的段落

    Returns:
        [{paragraph_index, score, reason, ...}]
    """
    if not source_paras or not target_paras:
        return []

    # 建立 index -> text 映射
    src_map = {p.get("index", i): p.get("text", "") for i, p in enumerate(source_paras)}
    tgt_map = {p.get("index", i): p.get("text", "") for i, p in enumerate(target_paras)}

    # 收集术语 source 列表用于匹配
    term_sources = set()
    if key_terminology:
        term_sources = {t["source"].lower() for t in key_terminology}

    # 比较逻辑标记
    comparison_pattern = re.compile(
        r'\b(?:versus|vs\.?|compared\s+(?:with|to)|rather\s+than|'
        r'instead\s+of|contrary\s+to|as\s+opposed\s+to|unlike)\b',
        re.IGNORECASE
    )
    unit_pattern = re.compile(
        r'\b\d+\s*(?:mm|cm|m|kg|g|mg|mL|L|MHz|kHz|Hz|J|W|kV|V|mA|A|°C|°F|%)\b',
        re.IGNORECASE
    )
    number_pattern = re.compile(r'\b\d+(?:\.\d+)?\b')

    scored = []
    for index in sorted(set(list(src_map.keys()) + list(tgt_map.keys()))):
        src_text = src_map.get(index, "")
        tgt_text = tgt_map.get(index, "")

        # 跳过长空段落
        combined = src_text + tgt_text
        if len(combined.strip()) < 20:
            continue

        score = 0
        reasons = []

        # 数字
        num_count = len(number_pattern.findall(src_text)) + len(number_pattern.findall(tgt_text))
        if num_count >= 3:
            score += num_count * 3
            reasons.append(f"含 {num_count} 个数字")
        elif num_count > 0:
            score += num_count * 1
            reasons.append(f"含 {num_count} 个数字")

        # 术语
        term_hits = 0
        src_lower = src_text.lower()
        for term in term_sources:
            if term in src_lower:
                term_hits += 1
        if term_hits >= 2:
            score += term_hits * 2
            reasons.append(f"含 {term_hits} 个关键术语")

        # 超长句
        if len(src_text) > 200 or len(tgt_text) > 200:
            score += 1
            reasons.append("超长句")

        # 比较逻辑
        if comparison_pattern.search(src_text):
            score += 2
            reasons.append("含比较逻辑")

        # 单位缩写
        if unit_pattern.search(src_text):
            score += 1
            reasons.append("含测量单位")

        if score > 0:
            scored.append({
                "paragraph_index": index,
                "score": score,
                "reason": "; ".join(reasons),
            })

    # 排序取 top_pct
    scored.sort(key=lambda x: x["score"], reverse=True)
    cutoff = max(5, int(len(scored) * top_pct))
    return scored[:cutoff]


# ══════════════════════════════════════════════════════════════
# 4. 结构检查清单
# ══════════════════════════════════════════════════════════════

def build_structure_checklist(
    source_paras: list[dict],
    target_paras: list[dict],
    source_type: str = "docx",
    target_type: str = "docx",
    pair_info: dict | None = None,
) -> list[dict]:
    """构建结构完整性检查项。

    统计标题数、表格数、检测跨格式断段。
    """
    checklist = []

    # 标题数对比
    src_headings = [p for p in source_paras if p.get("heading_level") or p.get("style", "").startswith("Heading")]
    tgt_headings = [p for p in target_paras if p.get("heading_level") or p.get("style", "").startswith("Heading")]
    if src_headings and tgt_headings:
        if len(src_headings) != len(tgt_headings):
            checklist.append({
                "type": "heading_count_mismatch",
                "source_count": len(src_headings),
                "target_count": len(tgt_headings),
                "note": f"原文 {len(src_headings)} 个标题，译文 {len(tgt_headings)} 个标题，数量不一致",
            })
        else:
            checklist.append({
                "type": "heading_count",
                "expected": len(src_headings),
                "actual": len(tgt_headings),
                "status": "ok",
            })

    # 表格数对比
    src_tables = sum(1 for p in source_paras if p.get("style") == "Table" or p.get("is_table"))
    tgt_tables = sum(1 for p in target_paras if p.get("style") == "Table" or p.get("is_table"))
    if src_tables or tgt_tables:
        if src_tables != tgt_tables:
            checklist.append({
                "type": "table_count_mismatch",
                "source_count": src_tables,
                "target_count": tgt_tables,
                "note": f"原文 {src_tables} 个表格，译文 {tgt_tables} 个表格，数量不一致",
            })

    # 跨格式(PDF→DOCX)断段检测
    is_cross_format = (source_type == "pdf" and target_type == "docx")
    if is_cross_format:
        # 检测不以标点结尾的段（可能是 PDF 提取时的断段）
        terminal_punct = re.compile(r'[。！？\.\!\?…—\)）""]$')
        broken_paras = []
        for p in target_paras:
            text = p.get("text", "").strip()
            if text and not terminal_punct.search(text):
                broken_paras.append(p.get("index", 0))
        if broken_paras:
            checklist.append({
                "type": "cross_format_broken_paragraphs",
                "count": len(broken_paras),
                "paragraph_indices": broken_paras[:20],  # 最多 20 个
                "note": f"跨格式(PDF→DOCX)检测到 {len(broken_paras)} 个不以标点结尾的段，可能是 PDF 提取断段",
            })
        # 标题/题注缺失提醒
        checklist.append({
            "type": "cross_format_figure_captions",
            "note": "PDF → DOCX 转换可能导致图表标题/题注缺失，Phase 4 需检查图表标题完整性",
        })
        checklist.append({
            "type": "cross_format_note",
            "note": "跨格式校对模式，所有查找结果标记 [全文匹配，仅供参考]。注意：PDF 文本提取可能遗漏表格、图片中的文字。",
        })

    return checklist


# ══════════════════════════════════════════════════════════════
# 5. 必检项推导
# ══════════════════════════════════════════════════════════════

def derive_mandatory_checks(
    domain_info: dict,
    phase3_issues: dict | None = None,
) -> list[dict]:
    """根据领域和 Phase 3 结果，推导必检项。

    Args:
        domain_info: detect_domain() 的输出
        phase3_issues: Phase 3 的 issues_mechanical.json 内容

    Returns:
        [{check_id, name, reason}]
    """
    primary = domain_info.get("primary", "")

    # 从领域映射获取基础必检项
    checks = []
    for domain_key, domain_checks in DOMAIN_MANDATORY_CHECKS.items():
        if domain_key in primary:
            checks.extend(domain_checks)
            break
    else:
        # 未匹配到具体领域，使用通用必检项
        checks = [
            {"check_id": "1.4", "name": "错译", "reason": "错译是最常见的翻译质量问题，应在所有文档中重点检查"},
            {"check_id": "2.12", "name": "翻译腔", "reason": "英文→中文最常见的结构性问题"},
            {"check_id": "3.1", "name": "数值单位", "reason": "数值错误可能导致严重后果"},
            {"check_id": "4.1", "name": "术语库一致", "reason": "术语一致性是专业翻译的基本要求"},
        ]

    # 根据 Phase 3 结果补充
    if phase3_issues and isinstance(phase3_issues, dict):
        n_numbers = len(phase3_issues.get("number_mismatches", []))
        n_glossary = len(phase3_issues.get("glossary_violations", []))
        n_symbol = len(phase3_issues.get("symbol_issues", []))
        n_format = len(phase3_issues.get("format_issues", []))

        # 数字问题多 → 强化 3.1
        if n_numbers > 20 and not any(c["check_id"] == "3.1" for c in checks):
            checks.append({"check_id": "3.1", "name": "数值单位", "reason": f"Phase 3 发现 {n_numbers} 处数字问题，Phase 4 必须重点审查"})

        # 术语违规多 → 强化 4.1
        if n_glossary > 10 and not any(c["check_id"] == "4.1" for c in checks):
            checks.append({"check_id": "4.1", "name": "术语库一致", "reason": f"Phase 3 发现 {n_glossary} 处术语违规，Phase 4 必须重点审查"})

        # 符号问题 → 强化 3.3
        if n_symbol > 0 and not any(c["check_id"] == "3.3" for c in checks):
            checks.append({"check_id": "3.3", "name": "符号格式", "reason": f"Phase 3 发现 {n_symbol} 处符号问题"})

        # 格式问题 → 强化 5.1
        if n_format > 0 and not any(c["check_id"] == "5.1" for c in checks):
            checks.append({"check_id": "5.1", "name": "标题层级", "reason": f"Phase 3 发现 {n_format} 处格式问题"})

    return checks


# ══════════════════════════════════════════════════════════════
# 6. 领域严重度升级规则
# ══════════════════════════════════════════════════════════════

def build_domain_escalation_rules(domain_info: dict) -> dict:
    """返回领域特定的严重度升级规则。

    Args:
        domain_info: detect_domain() 的输出

    Returns:
        {error_type: target_severity, ...}
    """
    primary = domain_info.get("primary", "")

    for domain_key, rules in DOMAIN_ESCALATION_RULES.items():
        if domain_key in primary:
            return rules

    return DEFAULT_ESCALATION_RULES


# ══════════════════════════════════════════════════════════════
# 辅助：文本收集
# ══════════════════════════════════════════════════════════════

def _collect_text(data: dict) -> str:
    """从 split JSON 中收集全部文本。

    支持两种格式:
      - 按段落: {chapters: [{paragraphs: [{index, text}]}]}  (target)
      - 按页面: {pages: [{page_num, text}]}  (source PDF)
    """
    text_parts = []

    if "pages" in data:
        for page in data["pages"]:
            text_parts.append(page.get("text", ""))
    elif "chapters" in data:
        for ch in data["chapters"]:
            for para in ch.get("paragraphs", []):
                text_parts.append(para.get("text", ""))
    elif isinstance(data, list):
        for item in data:
            text_parts.append(item.get("text", ""))
    elif isinstance(data, dict) and "text" in data:
        text_parts.append(data["text"])

    return "\n".join(text_parts)


def _collect_paragraphs(data: dict) -> list[dict]:
    """从 split JSON 中收集段落列表。"""
    paragraphs = []

    if "chapters" in data:
        for ch in data["chapters"]:
            for para in ch.get("paragraphs", []):
                paragraphs.append({
                    "index": para.get("index", len(paragraphs) + 1),
                    "text": para.get("text", ""),
                    "style": para.get("style", "Normal"),
                    "heading_level": para.get("heading_level"),
                })
    elif "pages" in data:
        for page in data["pages"]:
            # PDF 页面按段拆分（以换行分隔）
            page_text = page.get("text", "")
            for i, line in enumerate(page_text.split("\n")):
                line = line.strip()
                if line:
                    paragraphs.append({
                        "index": len(paragraphs) + 1,
                        "text": line,
                        "style": "Normal",
                        "heading_level": None,
                        "_page": page.get("page_num"),
                    })
    elif isinstance(data, list):
        for i, item in enumerate(data):
            paragraphs.append({
                "index": i + 1,
                "text": item.get("text", ""),
                "style": item.get("style", "Normal"),
                "heading_level": item.get("heading_level"),
            })

    return paragraphs


# ══════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Phase 3.5: 上下文注入 — 分析文档，生成 Phase 4 注意力锚点"
    )
    parser.add_argument("--split-source", required=True, help="cache/split_source.json 路径")
    parser.add_argument("--split-target", required=True, help="cache/split_target.json 路径")
    parser.add_argument("--glossary", help="术语库 glossary.json 路径（可选）")
    parser.add_argument("--client-glossary", help="客户术语文件路径（可选）")
    parser.add_argument("--pair-info", help="cache/pair_info.json 路径（可选，用于获取源文格式信息）")
    parser.add_argument("--issues-mech", help="cache/issues_mechanical.json 路径（可选）")
    parser.add_argument("--output", "-o", required=True, help="输出 JSON 文件路径 (cache/phase4_context.json)")
    parser.add_argument("--min-term-occurrences", type=int, default=3,
                        help="术语最少出现次数阈值 (default: 3)")
    args = parser.parse_args()

    # ── 1. 加载数据 ──
    with open(args.split_source, "r", encoding="utf-8") as f:
        source_data = json.load(f)
    with open(args.split_target, "r", encoding="utf-8") as f:
        target_data = json.load(f)

    source_text = _collect_text(source_data)
    target_text = _collect_text(target_data)
    source_paras = _collect_paragraphs(source_data)
    target_paras = _collect_paragraphs(target_data)

    # 源文格式检测
    pair_info = None
    if args.pair_info:
        try:
            with open(args.pair_info, "r", encoding="utf-8") as f:
                pair_info = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    source_type = "pdf" if source_data.get("pages") else "docx"
    if pair_info and "pairs" in pair_info and pair_info["pairs"]:
        source_type = pair_info["pairs"][0].get("source", {}).get("format", source_type)
    target_type = "docx"

    # ── 2. 加载术语库和 Phase 3 结果 ──
    glossary = None
    if args.glossary:
        try:
            with open(args.glossary, "r", encoding="utf-8") as f:
                glossary = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            sys.stderr.write(f"[inject_context] 术语库加载失败，跳过: {args.glossary}\n")

    phase3_issues = None
    if args.issues_mech:
        try:
            with open(args.issues_mech, "r", encoding="utf-8") as f:
                phase3_issues = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    # ── 3. 分析 ──
    domain_info = detect_domain(source_text, glossary)
    key_terminology = extract_key_terminology(
        source_text, target_text, glossary, args.min_term_occurrences
    )
    high_risk_paras = identify_high_risk_paragraphs(
        source_paras, target_paras, key_terminology
    )
    structure = build_structure_checklist(
        source_paras, target_paras, source_type, target_type, pair_info
    )
    mandatory_checks = derive_mandatory_checks(domain_info, phase3_issues)
    escalation_rules = build_domain_escalation_rules(domain_info)

    # ── 4. 输出 ──
    output = {
        "meta": {
            "source_file": args.split_source,
            "target_file": args.split_target,
            "source_type": source_type,
            "target_type": target_type,
            "total_source_paragraphs": len(source_paras),
            "total_target_paragraphs": len(target_paras),
            "is_cross_format": source_type != target_type,
        },
        "domain": domain_info,
        "key_terminology": key_terminology,
        "high_risk_paragraphs": high_risk_paras,
        "structure_checklist": structure,
        "mandatory_checks": mandatory_checks,
        "domain_escalation_rules": escalation_rules,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # ── 5. 摘要输出 ──
    print(f"领域: {domain_info['primary']} (置信度 {domain_info['confidence']:.0%})")
    print(f"关键术语: {len(key_terminology)} 个")
    print(f"高风险段落: {len(high_risk_paras)} 个")
    print(f"必检项: {len(mandatory_checks)} 个")
    print(f"结构检查项: {len(structure)} 个")
    print(f"输出: {args.output}")


if __name__ == "__main__":
    main()
