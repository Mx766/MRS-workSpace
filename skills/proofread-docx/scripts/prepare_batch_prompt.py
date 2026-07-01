#!/usr/bin/env python3
"""
Phase 4 前置：Batch 数据富化

读取 Phase 2 的 batch 数据和 Phase 3.5 的 context，为每个 batch 注入：
  - domain_context: 领域信息
  - key_terminology: 相关的高频术语
  - mandatory_checks: 不可跳过的检查项
  - high_risk_flags: 该 batch 中的高风险段落标记

输出: cache/batch_N_prompt.json (供 Phase 4 Agent 直接使用)
"""

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


def load_json(filepath: str) -> dict | list | None:
    """安全加载 JSON 文件。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        sys.stderr.write(f"[prepare_batch] 无法加载 {filepath}: {e}\n")
        return None


def find_relevant_terms(
    batch_paras: list[dict],
    key_terminology: list[dict],
) -> list[dict]:
    """找出在该 batch 中出现的术语。

    Args:
        batch_paras: [{index, text, ...}]
        key_terminology: inject_context 输出的关键术语列表

    Returns:
        在 batch 中至少出现一次的关键术语（精简版，只含字段）
    """
    # 拼接 batch 全部文本
    batch_text = " ".join(p.get("text", p.get("target_text", "")) for p in batch_paras).lower()

    relevant = []
    for term in key_terminology:
        src = term.get("source", "").lower()
        if src and src in batch_text:
            relevant.append({
                "source": term["source"],
                "required_target": term["required_target"],
                "is_critical": term.get("is_critical", False),
                "translation_status": term.get("translation_status", "unknown"),
                "count_in_document": term.get("count", 0),
            })

    # 按 is_critical 优先，然后按 count 降序
    relevant.sort(key=lambda t: (not t["is_critical"], -t["count_in_document"]))
    return relevant


def find_high_risk_in_batch(
    batch_paras: list[dict],
    high_risk_paragraphs: list[dict],
) -> list[dict]:
    """找出该 batch 中的高风险段落。

    Args:
        batch_paras: [{index, ...}]
        high_risk_paragraphs: inject_context 输出的高风险段落列表

    Returns:
        该 batch 中的高风险段落列表
    """
    batch_indices = {p.get("index", p.get("paragraph_index", -1)) for p in batch_paras}
    return [p for p in high_risk_paragraphs if p.get("paragraph_index") in batch_indices]


def build_batch_prompt_context(
    batch_data: dict,
    context: dict,
) -> dict:
    """为单个 batch 构建富化的 prompt 数据。

    Args:
        batch_data: 原始 batch 数据 {batch_id, paragraphs: [{index, target_text, ...}]}
        context: phase4_context.json 内容

    Returns:
        富化后的 batch 数据
    """
    batch_paras = batch_data.get("paragraphs", [])
    batch_indices = [p.get("index", p.get("paragraph_index", -1)) for p in batch_paras]

    # 找出相关术语（v2.21: 合并高频 + 低频关键术语）
    all_terms = context.get("key_terminology", []) + context.get("critical_low_freq_terms", [])
    relevant_terms = find_relevant_terms(batch_paras, all_terms)

    # 分离低频关键术语（在 batch 中出现的），单独标注以引起 AI 注意
    critical_low_freq_in_batch = [
        t for t in relevant_terms
        if t.get("importance_reason", "") not in ("", "frequency", "high_frequency")
        and t.get("count", 0) < 3
    ]

    # 找出高风险段落
    high_risk = find_high_risk_in_batch(batch_paras, context.get("high_risk_paragraphs", []))

    # 构建 domain_context 摘要
    domain = context.get("domain", {})
    domain_context = {
        "primary": domain.get("primary", "通用"),
        "notes": domain.get("domain_notes", ""),
        "confidence": domain.get("confidence", 0),
    }

    # 构建 mandatory_checks 摘要
    mandatory_checks = context.get("mandatory_checks", [])

    # 构建结构相关项
    structure_items = []
    for s in context.get("structure_checklist", []):
        s_type = s.get("type", "")
        if s_type == "cross_format_note" or s_type == "cross_format_figure_captions":
            structure_items.append(s.get("note", ""))
        elif s_type == "cross_format_broken_paragraphs":
            # 检查该 batch 是否有断段
            broken_in_batch = [
                idx for idx in s.get("paragraph_indices", [])
                if idx in batch_indices
            ]
            if broken_in_batch:
                structure_items.append(
                    f"本批有 {len(broken_in_batch)} 个不以标点结尾的段落（可能为跨格式断段）: {broken_in_batch}"
                )

    # 构建 meta（跨格式标志等）
    meta = context.get("meta", {})
    is_cross_format = meta.get("is_cross_format", False)

    # v2.20: 根据检测到的文档领域选择翻译模式指南
    domain_info = context.get("domain", {})
    domain_guide = get_domain_guide(domain_info)

    enriched = dict(batch_data)  # 复制原数据
    enriched["_prompt_context"] = {
        "domain_context": domain_context,
        "key_terminology": relevant_terms,
        "critical_low_freq_terms": critical_low_freq_in_batch,
        "mandatory_checks": mandatory_checks,
        "high_risk_paragraphs": high_risk,
        "structure_notes": structure_items,
        "is_cross_format": is_cross_format,
        "cross_format_warning": (
            "原文为 PDF 格式，本模式使用逐页匹配，所有机械检查结果仅供参考，可能存在误报。"
            if is_cross_format else ""
        ),
        # v2.17: 嵌入压缩触发清单
        # v2.20: Round 2 末尾追加领域特定翻译模式指南
        "checklist_round1": build_checklist_section(for_round=1),
        "checklist_round2": build_checklist_section(for_round=2, domain_guide=domain_guide),
        "expected_findings_hint": EXPECTED_FINDINGS_HINT_BASE,
    }

    return enriched


# ══════════════════════════════════════════════════════════════
# v2.17: 压缩触发清单 — 嵌入 batch prompt，消除外部文档依赖
# ══════════════════════════════════════════════════════════════

# 每维度 1-2 行：(check_id, 维度名, 触发问题, 期望发现量提示)
CHECKLIST_ROUND1 = [   # 表面错误扫描 — 快速，每段 ~30 秒
    # 一、双语忠实度
    ("1.1", "完整性", "逐词对照：有无漏词/漏句/漏数字？整段是否缺译？"),
    ("1.2", "增译", "译文中有无原文不存在的解释性文字？"),
    ("1.3", "减译", "only/approximately/at least/shall not 等限定词是否译出？"),
    ("1.4", "错译", "核心概念/因果关系/条件关系是否正确？数值含义是否被曲解？"),
    ("1.5", "指代", "it/this/that/其/该 指代对象是否正确？"),
    ("1.6", "双重否定", "双重否定是否误判为肯定？"),
    ("1.7", "部分否定", "not all 是否误译为\"都不\"？"),
    ("1.8", "时态", "过去/现在/将来/完成时是否在译文中正确传达？"),
    ("1.9", "情态", "must/shall(强制) vs should(建议) vs may/can(允许) 是否准确区分？"),
    # 二、错别字与标点
    ("2.1", "错别字", "逐字扫读：有无错字/别字/多字/漏字/繁简混用？英文拼写错误？"),
    ("2.2", "标点体系", "中文用，。；：、\"\"''「」——英文括号/引号是否混入中文句？"),
    ("2.3", "标点多余", "句末漏句号？引号不成对？书名号用于非书名？"),
    # 三、数字符号单位
    ("3.1", "数值一致", "阿拉伯数字/百分比/小数——译文与原文是否完全一致？"),
    ("3.2", "范围表达", "1-5 / 1至5 / from 1 to 5——表达是否准确且全文统一？"),
    ("3.3", "单位符号", "单位缩写是否正确？特别注意复合单位如 mg/kg² vs kg/m²"),
    ("3.4", "专有名词", "人名/公司/机构/产品名/产品代号/参考文献是否保留不译？数字后面的单位是否保留原文？特别注意：产品名+代号组合（如\"DWP431介质\"）——代号不应翻译，单位不应汉化（如\"mg/kg\"非\"毫克/千克\"）"),
    ("3.5", "法规编号", "ISO/ICH/FDA/§ 编号是否完整未变？"),
    ("3.6", "公式变量", "上下标/符号/变量含义是否匹配原文？"),
    ("3.7", "地址翻译", "地名/地址/机构地址是否按规范翻译或保留原文？外文地址不应逐字翻译；中文地址省市区县是否完整？"),
    # 五、格式异常
    ("5.8", "句中断行", "段落中是否有不正常的换行？中文句子是否被错误切成多行？每行结尾是否为完整句或正常断句？PDF提取文本尤需注意——检查每行末是否有句号/分号/逗号收尾"),  # v2.19
]

CHECKLIST_ROUND2 = [  # 翻译质量深度审查 — 仔细，每段 ~2-3 分钟
    # 二、用词准确性（逐词审视）
    ("2.4", "口语vs书面", "每个词问：这是书面语吗？\"看不到改善\"→\"无明显改善\"，\"没了\"→\"消失\"。技术文档必须使用书面语，避免口语化表达。领域专业用语规范见下方领域特定翻译模式指南"),
    ("2.5", "褒贬色彩", "claim→\"声称\"(质疑)还是\"主张\"？leading to→\"导致\"(贬)还是\"推动\"(中)？due to→\"得益于\"(褒)？"),
    ("2.6", "近义词混淆", "避免vs避开、影响vs作用、允许vs可、程序vs治疗手段——每个易错对检查。根据文档领域判断近义词的正确译法——不同领域有完全不同的惯用搭配。常见陷阱见下方领域特定翻译模式指南"),
    ("2.7", "动宾搭配", "每个动宾结构读一遍：\"测量了…满意度\"——测量能搭配满意度吗？"),
    ("2.8", "修饰-名词搭配", "\"界限清晰的热损伤区域\"→中文习惯\"边界清晰\"。每个修饰语读一遍"),
    ("2.9", "介词连词", "and/or/with/versus 译法是否正确？\"与\"vs\"或\"——逐句确认"),
    ("2.10", "程度副词", "可能有所/显著/略微——原文的程度修饰是否在译文中保留？"),
    ("2.11", "范畴词", "改善→改善效果？传递→传递过程？医学文本适当加范畴词更自然"),
    # 二.C、翻译腔（每句读一遍，用中文语感判断）
    ("2.12", "\"当…时\"冗余", "每个\"当…时\"问一句：删掉是否更通顺？\">90%的情况可以删"),
    ("2.13", "被动直译", "每个\"被\"字句检查：能否去掉\"被\"？\"设备被用于治疗\"→\"设备用于治疗\""),
    ("2.14", "\"的\"字堆砌", "每个段落数\"的\"字数量——>3个\"的\"的句子重点审查，删掉多余的"),
    ("2.15", "\"使/让/令\"冗余", "\"使周围组织不受影响\"→删\"使\"字。\"使\"字多是翻译腔强信号"),
    ("2.16", "\"对于/关于\"冗余", "\"对于RF设备，要达到高温\"→\"RF设备要达到高温\"。句首介词常可删"),
    ("2.17", "\"尽管…但\"直译", "\"Although X, Y\"→中文有时适合\"X，但Y\"或直接陈述"),
    ("2.18", "\"不同的\"冗余", "\"可设定为不同深度\"→\"可设定以下深度\"。\"不同的\"常可删"),
    # 二.D、句法流畅度
    ("2.19", "单读测试", "遮蔽原文，逐句读译文——每句至少读2遍：第1遍正常速度，第2遍慢速。读起来别扭→必然有问题→必须标记！读不懂需要回看的句子→标记。不要因为\"语法对\"就放过——\"语法对但中国人不这么写\"就是翻译腔"),
    ("2.20", "长句拆分", "中文单句>60字或>4个逗号→大概率是欧化从句堆砌→标记需要拆分。\"当…时，…，…，…，…\"→典型欧化，应断开。需要反复读才能理解→标记"),
    ("2.21", "主语话题一致", "连续小句频繁切换主语？\"设备…。较高频率…。较低频率…\"→话题断裂"),
    ("2.22", "连接词自然度", "因此/然而/此外/另一方面——是否过多？中文偏好意合（靠语义），非形合（靠连接词）"),
    # 二.E、MT残留
    ("2.23", "术语泛化", "每个短名词问：该领域是否有更规范的全称？\"探头\"→\"治疗探头\""),
    ("2.24", "修饰语欧化", "\"接种试验Endozime的产品\"→语序不通。多字定语前置时逐词检查"),
    ("2.25", "字面直译", "每个短句读一遍，不通顺就标——不需要对照英文。MT常见陷阱：专业术语字面直译而非使用领域标准译法。该领域常见字面直译案例见下方领域特定翻译模式指南"),
    ("2.26", "英文残留", "逐段扫读：有无孤立英文单词/标号/数字残留？"),
    # 二.F、用词精确度
    ("2.F1", "词义范围偏差", "改善vs改进vs提升vs增强——每个\"improve\"译法检查；显示vs表明vs呈现vs证明——每个\"show\"译法检查"),
    ("2.F2", "抽象名词直译", "\"XX的YY\"结构中YY是动作名词→转动词。\"X的应用导致\"→\"施加X使\""),
    ("2.F3", "语域一致性", "段落内用语正式程度一致吗？患者/求美者/受试者混用？连接词风格突变？"),
    ("2.F4", "字面vs语境翻译", "contact=联系方式(MSDS)还是接触(日常)？safety=安全性(数据)还是安全(操作)？"),
    # 二.G、不通顺增强
    ("2.G1", "成分残缺", "每个句子提取主谓宾主干——不只是正文句子，标题/表格名/图注/列表项等短文本同样需要完整成分。\"DWP431在SD大鼠中2周重复给药毒性研究\"→缺少\"的\"字或动词。缺任何一个成分→标记"),
    ("2.G2", "句式杂糅", "搜索\"是为了/是由于/基于/涉及到\"——前后是否重复表达同一逻辑？常见杂糅模式：\"是…的\"与\"为…\"混用（\"X是重要的\"+\"X为重要\"→\"X是为重要的\"），\"由于…所致\"与\"因为…所以\"混用，\"基于…认为\"与\"根据…判断\"混用。读起来别扭的中文句式→标记"),
    ("2.G3", "语义冗余", "每句问：删掉\"进行/实现/发生/存在/具有\"后更通顺？是→标记redundant_word"),
    ("2.G4", "逻辑连接断裂", "遮蔽原文，连续读3-5句译文。中间有\"为什么会说到这个\"的困惑→标记logic_gap"),
    # 二.H、论证与逻辑（v2.19 新增）
    ("2.27", "论证逻辑/因果方向", "\"基于X，认为Y不具有显著性\"→真正含义是否是\"Y系X所致，故不具有显著性\"？因果关系方向是否被翻译反转？特别是\"因此/所以/基于…认为/由于…导致\"开头的句子——仔细核对因果方向是否与原文一致"),
    # 三、领域惯例（v2.19 新增 — 深层领域知识，放在 ROUND2）
    ("3.8", "领域惯例一致", "检查每个涉及专业概念的词——该领域是否有约定俗成的规范化用语？对象称呼、操作动词、实验类型术语是否符合该领域惯例？具体对照下方领域特定翻译模式指南中的约定术语"),
    # 四、术语合规
    ("4.1", "术语库一致", "术语库规定的译法是否遵守？无术语库时按文档类型主动判断译法规范。逐词核实该领域的标准译法——不同领域对同一英文词有完全不同的规范译法。具体对照下方领域特定翻译模式指南"),
    ("4.2", "段内术语统一", "同一段内同一英文术语出现多次→中文译法必须一致。thermal injury zone≠前句\"热损伤区域\"后句\"热损伤区\""),
    ("4.3", "跨段术语统一", "核心概念在不同段落中译法一致吗？每段校对完记录术语映射，发现不一致→critical"),
    ("4.4", "缩写规范", "首次出现标注\"全称(ABBR)\"了吗？后续出现是否保持缩写形式一致？不可首次用\"全称(ABBR)\"后文又变回全称或不同缩写"),
    ("4.5", "跨领域区分", "多义术语是否按文档领域选对译法？同一英文词在不同领域有完全不同的约定译法——对照下方领域特定指南，逐词确认译法选择"),
    # 五、格式与表格（v2.18 新增）
    ("5.4", "表格完整性", "表格中所有单元格是否已翻译？有无漏译单元格？表头是否翻译？"),
    ("5.5", "表格术语一致", "表格中术语译法是否与正文一致？同一列/行术语是否统一？"),
    ("5.6", "表格数值一致", "表格中数字/百分比/单位是否与原文完全一致？特别注意小数点位置"),
    ("5.7", "格式保真", "加粗/斜体/下划线/字体样式是否与原文一致？重点标记是否保留？"),
]

# v2.17: 期望发现量——帮助模型校准期望（通用基线，领域模式见下方指南）
EXPECTED_FINDINGS_HINT_BASE = (  # v2.20: 去医学化，领域特定模式移入 DOMAIN_TRANSLATION_GUIDES
    "EXPECTED FINDINGS CALIBRATION: A typical technical translation document contains:\n"
    "  - 忠实度问题 (1.x): 3-8 处（漏译/错译/情态/指代）\n"
    "  - 错别字/标点 (2.1-2.3): 2-5 处\n"
    "  - 翻译腔 (2.12-2.18): 8-20 处（\"当…时\"/被动/\"的\"字堆砌最常见）\n"
    "  - 用词准确度 (2.4-2.11, 2.F, 2.G, 2.27): 10-25 处（动宾搭配/词义偏差/语义冗余最常见）\n"
    "  - 术语合规 (4.x): 3-10 处\n"
    "  - 数字/单位 (3.x): 1-5 处\n"
    "  - 论证逻辑 (2.27): 1-4 处（因果倒置/逻辑方向错误）\n"
    "  - 领域惯例 (3.8): 2-6 处（领域术语/对象称呼/操作动词）\n"
    "  - 格式异常 (5.8): 0-3 处（断行，PDF提取场景较多）\n"
    "If your review finds fewer than these ranges, you are likely missing issues — re-examine.\n"
    "For domain-specific failure patterns, see the DOMAIN-SPECIFIC TRANSLATION PATTERNS section below.\n"
)

# v2.18: 单段多问题强制指令
MULTI_ISSUE_INSTRUCTION = (
    "MULTI-ISSUE PER PARAGRAPH REQUIREMENT (v2.18):\n"
    "  Finding one issue in a paragraph does NOT mean the paragraph is done.\n"
    "  After finding ANY issue, you MUST continue checking ALL remaining dimensions\n"
    "  for that SAME paragraph. A single paragraph can have:\n"
    "    - A terminology violation (4.x) AND a wrong number (3.x)\n"
    "    - An awkward expression (2.12) AND a missing translation (1.1)\n"
    "    - A punctuation error (2.2) AND a subject-switching issue (2.21)\n"
    "  The per-paragraph check is COMPLETE only after you have explicitly considered\n"
    "  every single dimension against that paragraph — not just the first one that\n"
    "  produced a hit. This is the #1 reason human translators say reviews are shallow.\n"
)


# ══════════════════════════════════════════════════════════════
# v2.20: 领域特定翻译模式指南
# 根据 inject_context.py 检测到的文档领域自动选择并注入到 Round 2
# ══════════════════════════════════════════════════════════════

DOMAIN_TRANSLATION_GUIDES = {
    "medical_clinical": """════════════════════════════════════════════════
DOMAIN-SPECIFIC TRANSLATION PATTERNS — MEDICAL/CLINICAL
════════════════════════════════════════════════
The following are high-frequency pitfalls in Chinese medical/clinical
translation. Check EVERY paragraph for these domain-specific issues.

── TERMINOLOGY TRAPS ──
  test substance/article → 受试物 (NOT 测试物质/测试物品)
  clinical dose → 临床剂量 (NOT 临床用量)
  expected clinical dose → 预期临床剂量

── ANIMAL STUDIES ──
  雄/雌 (NOT 男/女) for animal sex
  动物/受试动物 (NOT 病人) for test subjects
  给药 (NOT 摄入) — especially for injection/gavage routes
  经口给予 (NOT 吃/摄入) — formal oral administration

── CLINICAL TRIALS ──
  受试者 vs 患者 vs 健康志愿者 — distinct roles, do not conflate
  site → 研究中心 (NOT 部位, in clinical context)
  protocol → 研究方案/试验方案 (NOT 测试方案/协议)
  AE → 不良事件 (NOT 副作用, unless specifically side effect)

── IN VITRO / LAB ──
  medium → 培养基 (cell) or 基质 (analytical matrix) — context-dependent
  vehicle → 溶媒/赋形剂 (NOT 介质)
  solution → 溶液 (liquid) vs 解决方案 (problem-solving)

── NEAR-SYNONYM TRAPS ──
  容量(volume) vs 体积(bulk), 测试(assay) vs 试验(trial)
  显著性(statistical) vs 意义(importance), 改善(symptom) vs 改进(design)

── ANATOMICAL PRECISION ──
  视网膜(retina) ≠ 眼底(fundus), 前部段 ≠ 眼前节(anterior chamber)

── MEDICAL DEVICE ──
  intended use → 预期用途, handpiece → 手持件 (NOT 手机)""",

    "legal_regulatory": """════════════════════════════════════════════════
DOMAIN-SPECIFIC TRANSLATION PATTERNS — LEGAL/REGULATORY
════════════════════════════════════════════════
The following are high-frequency pitfalls in legal/regulatory translations.
Check EVERY paragraph for these domain-specific issues.

── MODAL VERBS (LEGALLY BINDING) ──
  shall/must → 应当/必须 (mandatory)
  should → 宜/应当 (recommendation, non-binding)
  may/can → 可以/可 (permission or capability)
  shall not → 不得/禁止 (prohibition)
  Each modal must be verified against source for legal precision.

── PATENT SCOPE ──
  comprising → 包括 (open-ended)
  consisting of → 由…组成 (closed scope)
  said/the + [noun] → 所述/该 + [名词] (DO NOT OMIT in claims)
  wherein/thereby/thereof → 其中/由此/其

── SDS/GHS DOCUMENTS ──
  H-code/P-code → GHS official Chinese translation (DO NOT PARAPHRASE)
  安全数据表 (NOT 安全技术说明书, GB/T 16483)
  CAS No./EC No./UN No. → EXACT preservation
  LD50/LC50 values with units → verify precision

── REGULATORY FORMULAS ──
  including but not limited to → 包括但不限于
  without prejudice to → 在不影响…的情况下
  pursuant to / in accordance with → 根据/依照
  ISO/IEC/ASTM/EN standard numbers → EXACT preservation
  Dates, filing numbers, registration numbers → exact match""",

    "technical_cybersecurity": """════════════════════════════════════════════════
DOMAIN-SPECIFIC TRANSLATION PATTERNS — TECHNICAL/CYBERSECURITY
════════════════════════════════════════════════
The following are high-frequency pitfalls in technical/cybersecurity
translations. Check EVERY paragraph for these domain-specific issues.

── SECURITY TERMINOLOGY (CRITICAL) ──
  penetration test → 渗透测试 (NOT 穿刺测试)
  vulnerability → 漏洞 (NOT 脆弱性)
  exploit → 漏洞利用 (NOT 开发/开拓)
  brute-force → 暴力破解 (NOT 暴力)
  attack vector → 攻击向量
  privilege escalation → 权限提升/特权提升
  DoS/DDoS → 拒绝服务/分布式拒绝服务
  authentication(认证) vs authorization(授权) — DO NOT CONFLATE

── DO NOT TRANSLATE (PRESERVE EXACTLY) ──
  IP addresses, MAC addresses
  Port numbers, protocol version strings (e.g., "OpenSSH 8.9p1")
  Hashes (MD5, SHA-1, SHA-256), CVE-YYYY-NNNNN, CVSS scores
  File paths, registry keys, command-line examples

── ORGANIZATIONS/STANDARDS ──
  OWASP, NIST, CVE, CVSS — do not translate organization names
  TLS → 传输层安全协议 (first mention) / TLS (subsequent)
  SSH → 安全外壳协议 (first mention) / SSH (subsequent)

── COMMON MT TRAPS ──
  attack → 攻击 (NOT 袭击, which is physical)
  secure → 安全的/保护 (NOT 保密)
  compromise → 攻破/入侵 (NOT 妥协)
  key → 密钥 (cryptographic, NOT 关键)
  certificate → 证书 (digital, NOT 证明/凭证)
  scan → 扫描 (NOT 浏览/查看)
  Black-box/White-box → 黑盒/白盒 (testing methodology)""",

    "generic_technical": """════════════════════════════════════════════════
DOMAIN-SPECIFIC TRANSLATION PATTERNS — GENERIC TECHNICAL
════════════════════════════════════════════════
This is a generic guide for documents that do not match a specific domain.
Focus on universal technical writing principles.

── UNIVERSAL PRINCIPLES ──
  Unit symbols → preserve original form (mg/kg NOT 毫克/千克, 5 mm NOT 5 毫米)
  Product codes / model numbers / part numbers → DO NOT TRANSLATE
  Formulas, equations, mathematical expressions → EXACT match required
  Acronyms: spell out on first occurrence as "Full Name (ACRONYM)"
  Table/figure numbers and cross-references → exact match with source

── TERMINOLOGY CONSISTENCY ──
  Each technical term → ONE Chinese translation throughout the document
  Text and table terminology → MUST be identical
  Section headings → consistent terminology with body text

── MT ARTIFACT DETECTION ──
  Overly literal "for" → unnecessary 对于 at sentence start
  English word-order in Chinese: long pre-modifiers before head noun
  Missing topic-comment structure: sentences as rigid SVO
  Unnatural "的" stacking: >3 的 in one sentence → restructure

── NUMBERS/UNITS (UNIVERSAL) ──
  Decimal precision → exact match (0.05 ≠ 0.050)
  Ranges → 1 to 5 = 1~5 or 1至5 but CONSISTENT throughout
  Percentages → 5% NOT 百分之五 (in technical documents)""",
}

# inject_context.py domain.primary → guide key 映射
DOMAIN_TO_GUIDE_MAP = {
    "医疗器械注册": "medical_clinical",
    "药物临床": "medical_clinical",
    "网络安全评估": "technical_cybersecurity",
    "安全数据表": "legal_regulatory",
    "专利文献": "legal_regulatory",
    "通用技术文档": "generic_technical",
}


def get_domain_guide(domain_info: dict) -> str:
    """根据检测到的文档领域，选择对应的翻译模式指南。

    Args:
        domain_info: inject_context 输出的 domain 字典
                     {primary, secondary, confidence, domain_notes, ...}

    Returns:
        领域特定的翻译模式指南文本。未匹配到已知领域时返回通用指南。
    """
    primary = domain_info.get("primary", "通用技术文档") if domain_info else "通用技术文档"
    guide_key = DOMAIN_TO_GUIDE_MAP.get(primary, "generic_technical")
    return DOMAIN_TRANSLATION_GUIDES.get(
        guide_key,
        DOMAIN_TRANSLATION_GUIDES["generic_technical"]
    )


def build_checklist_section(for_round: int = 1, domain_guide: str = "") -> str:
    """构建压缩触发清单文本块，嵌入 batch prompt。

    Args:
        for_round: 1=表面错误扫描, 2=翻译质量深度审查
        domain_guide: 领域特定的翻译模式指南（v2.20, 仅 Round 2 使用）

    Returns:
        格式化的清单文本
    """
    if for_round == 1:
        items = CHECKLIST_ROUND1
        header = "SURFACE ERROR SCAN — Quick check (~30s per paragraph)"
    else:
        items = CHECKLIST_ROUND2
        header = "TRANSLATION QUALITY DEEP REVIEW — Careful check (~2-3 min per paragraph)"

    lines = [header, "-" * len(header), ""]
    for check_id, name, trigger in items:
        lines.append(f"  [{check_id}] {name}: {trigger}")

    if for_round == 2:
        lines.append("")
        lines.append(EXPECTED_FINDINGS_HINT_BASE)  # v2.20: 替换为领域中性基线
        lines.append("")
        lines.append(MULTI_ISSUE_INSTRUCTION)
        if domain_guide:                           # v2.20: 追加领域特定翻译模式指南
            lines.append("")
            lines.append(domain_guide)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Phase 4 前置：为每个 batch 注入 domain context、mandatory checks 和触发清单"
    )
    parser.add_argument("--batch-data", required=True, help="单个 batch 数据文件 (batch_N_data.json)")
    parser.add_argument("--context", required=True, help="phase4_context.json 路径")
    parser.add_argument("--output", "-o", required=True, help="输出路径 (batch_N_prompt.json)")
    parser.add_argument("--embed-checklist", action="store_true", default=True,
                        help="嵌入压缩触发清单（默认开启，v2.17）")
    parser.add_argument("--no-embed-checklist", action="store_false", dest="embed_checklist",
                        help="不嵌入触发清单（回退到 v2.16 行为）")
    args = parser.parse_args()

    # 加载
    batch_data = load_json(args.batch_data)
    context = load_json(args.context)

    if batch_data is None:
        sys.stderr.write(f"[prepare_batch] 无法加载 batch 数据: {args.batch_data}\n")
        sys.exit(1)
    if context is None:
        sys.stderr.write(f"[prepare_batch] 无法加载 context: {args.context}\n")
        sys.exit(1)

    # 富化
    enriched = build_batch_prompt_context(batch_data, context)

    # 输出
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    batch_id = batch_data.get("batch_id", "?")
    n_paras = len(batch_data.get("paragraphs", []))
    n_terms = len(enriched["_prompt_context"]["key_terminology"])
    n_risk = len(enriched["_prompt_context"]["high_risk_paragraphs"])
    r1_items = len(CHECKLIST_ROUND1)
    r2_items = len(CHECKLIST_ROUND2)

    print(f"Batch {batch_id}: {n_paras} 段, {n_terms} 相关术语, {n_risk} 高风险, "
          f"清单 R1={r1_items}项 R2={r2_items}项")
    print(f"输出: {args.output}")


if __name__ == "__main__":
    main()
