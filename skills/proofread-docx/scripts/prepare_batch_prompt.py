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

    # 找出相关术语
    relevant_terms = find_relevant_terms(batch_paras, context.get("key_terminology", []))

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

    enriched = dict(batch_data)  # 复制原数据
    enriched["_prompt_context"] = {
        "domain_context": domain_context,
        "key_terminology": relevant_terms,
        "mandatory_checks": mandatory_checks,
        "high_risk_paragraphs": high_risk,
        "structure_notes": structure_items,
        "is_cross_format": is_cross_format,
        "cross_format_warning": (
            "原文为 PDF 格式，本模式使用逐页匹配，所有机械检查结果仅供参考，可能存在误报。"
            if is_cross_format else ""
        ),
        # v2.17: 嵌入压缩触发清单，消除外部文档依赖
        "checklist_round1": build_checklist_section(for_round=1),
        "checklist_round2": build_checklist_section(for_round=2),
        "expected_findings_hint": EXPECTED_FINDINGS_HINT,
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
    ("3.4", "专有名词", "人名/公司/机构/产品名是否保留不译？"),
    ("3.5", "法规编号", "ISO/ICH/FDA/§ 编号是否完整未变？"),
    ("3.6", "公式变量", "上下标/符号/变量含义是否匹配原文？"),
    ("3.7", "地址翻译", "地名/地址/机构地址是否按规范翻译或保留原文？外文地址不应逐字翻译；中文地址省市区县是否完整？"),
]

CHECKLIST_ROUND2 = [  # 翻译质量深度审查 — 仔细，每段 ~2-3 分钟
    # 二、用词准确性（逐词审视）
    ("2.4", "口语vs书面", "每个词问：这是书面语吗？\"看不到改善\"→\"无明显改善\"，\"没了\"→\"消失\""),
    ("2.5", "褒贬色彩", "claim→\"声称\"(质疑)还是\"主张\"？leading to→\"导致\"(贬)还是\"推动\"(中)？due to→\"得益于\"(褒)？"),
    ("2.6", "近义词混淆", "避免vs避开、影响vs作用、允许vs可、程序vs治疗手段——每个易错对检查"),
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
    ("2.19", "单读测试", "遮蔽原文，逐句读译文。读起来别扭→必然有问题→必须标记！不要因为\"语法对\"就放过"),
    ("2.20", "长句拆分", "中文单句>60字→是否含英文嵌套？需要反复读才能理解→标记"),
    ("2.21", "主语话题一致", "连续小句频繁切换主语？\"设备…。较高频率…。较低频率…\"→话题断裂"),
    ("2.22", "连接词自然度", "因此/然而/此外/另一方面——是否过多？中文偏好意合（靠语义），非形合（靠连接词）"),
    # 二.E、MT残留
    ("2.23", "术语泛化", "每个短名词问：该领域是否有更规范的全称？\"探头\"→\"治疗探头\""),
    ("2.24", "修饰语欧化", "\"接种试验Endozime的产品\"→语序不通。多字定语前置时逐词检查"),
    ("2.25", "字面直译", "每个短句读一遍，不通顺就标——不需要对照英文"),
    ("2.26", "英文残留", "逐段扫读：有无孤立英文单词/标号/数字残留？"),
    # 二.F、用词精确度
    ("2.F1", "词义范围偏差", "改善vs改进vs提升vs增强——每个\"improve\"译法检查；显示vs表明vs呈现vs证明——每个\"show\"译法检查"),
    ("2.F2", "抽象名词直译", "\"XX的YY\"结构中YY是动作名词→转动词。\"X的应用导致\"→\"施加X使\""),
    ("2.F3", "语域一致性", "段落内用语正式程度一致吗？患者/求美者/受试者混用？连接词风格突变？"),
    ("2.F4", "字面vs语境翻译", "contact=联系方式(MSDS)还是接触(日常)？safety=安全性(数据)还是安全(操作)？"),
    # 二.G、不通顺增强
    ("2.G1", "成分残缺", "每个句子提取主谓宾主干——缺任何一个成分→标记。\"通过对组织进行加热\"→谁加热？"),
    ("2.G2", "句式杂糅", "搜索\"是为了/是由于/基于/涉及到\"——前后是否重复表达同一逻辑？"),
    ("2.G3", "语义冗余", "每句问：删掉\"进行/实现/发生/存在/具有\"后更通顺？是→标记redundant_word"),
    ("2.G4", "逻辑连接断裂", "遮蔽原文，连续读3-5句译文。中间有\"为什么会说到这个\"的困惑→标记logic_gap"),
    # 四、术语合规
    ("4.1", "术语库一致", "术语库规定的译法是否遵守？无术语库时按文档类型主动判断（器械→监管用语，MSDS→GB标准）"),
    ("4.2", "段内术语统一", "同一段内同一英文术语出现多次→中文译法必须一致。thermal injury zone≠前句\"热损伤区域\"后句\"热损伤区\""),
    ("4.3", "跨段术语统一", "核心概念在不同段落中译法一致吗？每段校对完记录术语映射，发现不一致→critical"),
    ("4.4", "缩写规范", "首次出现标注\"全称(ABBR)\"了吗？后续出现是否保持缩写形式一致？不可首次用\"全称(ABBR)\"后文又变回全称或不同缩写"),
    ("4.5", "跨领域区分", "多义术语是否按文档领域选对译法？site=研究中心(临床)还是部位(解剖)？"),
    # 五、格式与表格（v2.18 新增）
    ("5.4", "表格完整性", "表格中所有单元格是否已翻译？有无漏译单元格？表头是否翻译？"),
    ("5.5", "表格术语一致", "表格中术语译法是否与正文一致？同一列/行术语是否统一？"),
    ("5.6", "表格数值一致", "表格中数字/百分比/单位是否与原文完全一致？特别注意小数点位置"),
    ("5.7", "格式保真", "加粗/斜体/下划线/字体样式是否与原文一致？重点标记是否保留？"),
]

# v2.17: 期望发现量——帮助模型校准期望（148段医学论文的典型值）
EXPECTED_FINDINGS_HINT = (
    "EXPECTED FINDINGS CALIBRATION: A 148-paragraph medical translation typically contains:\n"
    "  - 忠实度问题 (1.x): 3-8 处（漏译/错译/情态/指代）\n"
    "  - 错别字/标点 (2.1-2.3): 2-5 处\n"
    "  - 翻译腔 (2.12-2.18): 8-20 处（\"当…时\"/被动/\"的\"字堆砌最常见）\n"
    "  - 用词准确度 (2.4-2.11, 2.F, 2.G): 10-25 处（动宾搭配/词义偏差/语义冗余最常见）\n"
    "  - 术语合规 (4.x): 3-10 处\n"
    "  - 数字/单位 (3.x): 1-5 处\n"
    "If your review finds fewer than these ranges, you are likely missing issues — re-examine.\n"
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


def build_checklist_section(for_round: int = 1) -> str:
    """构建压缩触发清单文本块，嵌入 batch prompt。

    Args:
        for_round: 1=表面错误扫描, 2=翻译质量深度审查

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
        lines.append(EXPECTED_FINDINGS_HINT)
        lines.append("")
        lines.append(MULTI_ISSUE_INSTRUCTION)  # v2.18

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
