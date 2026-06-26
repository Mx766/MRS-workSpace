#!/usr/bin/env python3
"""Generate Phase 4 issues JSON from semantic review."""

import json, sys

sys.stdout.reconfigure(encoding='utf-8')

issues = [
    # ═══ CRITICAL (must fix) ═══

    # P16: 衍文 - double 对
    {
        "chapter": "Ch5", "paragraph_index": 16,
        "dimension": "二.表达规范", "check_item": "2.1 错别字/拼写",
        "severity": "critical", "confidence": "high",
        "source_quote": "The continued patient demand for nonsurgical and minimal downtime facial rejuvenation has resulted in more use of injectable neurotoxins and fillers, and skin resurfacing and tightening treatments.",
        "target_quote": "患者对对非手术、恢复期极短的面部年轻化治疗的持续需求，导致注射用神经毒素和填充剂、皮肤换肤术及紧致治疗的应用日益增多。",
        "issue": "衍文（多字）：目标文本中出现了重复的「对」字——「患者对对非手术」应为「患者对非手术」",
        "suggestion": "删除多余的「对」字：患者对非手术、恢复期极短的面部年轻化治疗的持续需求……"
    },

    # P37: decollete mistranslation
    {
        "chapter": "Ch9", "paragraph_index": 37,
        "dimension": "一.双语忠实度", "check_item": "1.4 错译",
        "severity": "critical", "confidence": "high",
        "source_quote": "Improve lines and wrinkles in decollete",
        "target_quote": "改善肩颈部的细纹和皱纹",
        "issue": "错译：decollete 指胸口/前胸/乳沟区域（低领口暴露部位），而非「肩颈部」（shoulder and neck）。这是解剖位置错误，会误导临床操作部位。",
        "suggestion": "改善前胸（decollete区）的细纹和皱纹"
    },

    # P120: BMI unit error
    {
        "chapter": "Ch14", "paragraph_index": 120,
        "dimension": "三.数字符号单位", "check_item": "3.3 单位缩写",
        "severity": "critical", "confidence": "high",
        "source_quote": "patients with a body mass index of 30 mg/kg2 or less",
        "target_quote": "体重指数30mg/kg2的患者",
        "issue": "单位错误：BMI 的正确单位是 kg/m2，而非 mg/kg2。mg/kg2 是一个无意义的单位。虽原文本身存在笔误，译文应标注纠正而非照搬。",
        "suggestion": "体重指数30 kg/m2 的患者（原文作 mg/kg2，疑为原文笔误）"
    },

    # P133: Garbled sentence - merging two bullet points
    {
        "chapter": "Ch15", "paragraph_index": 133,
        "dimension": "一.双语忠实度", "check_item": "1.1 完整性 / 1.4 错译",
        "severity": "critical", "confidence": "high",
        "source_quote": "Facial and neck skin tightening can also be achieved by a variety of energy devices, including RF / Injectable fillers and fat grafts can result in mid and lower face elevation",
        "target_quote": "面部和颈部皮肤紧致也可以通过多种能量设备实现，包括射频注射填充材料和脂肪移植，可导致中下面部提升",
        "issue": "句意混乱：原文两个独立的治疗手段被错误合并为一句——RF设备属于能量设备（第一点），而注射填充材料和脂肪移植是独立类别（第二点）。译文将其混为一谈。",
        "suggestion": "面部和颈部皮肤紧致也可通过多种能量设备实现，包括RF；注射填充材料和脂肪移植可实现中下面部提升"
    },

    # P120: more lines mistranslated as more sessions
    {
        "chapter": "Ch14", "paragraph_index": 120,
        "dimension": "一.双语忠实度", "check_item": "1.4 错译",
        "severity": "critical", "confidence": "high",
        "source_quote": "It is possible that a higher treatment density (more lines) and assessment at 6 to 9 months may have shown more favorable responses.",
        "target_quote": "在更高的治疗密度（更多疗程）和6至9个月时的评估下，可能会显示出更有利的反应。",
        "issue": "错译：more lines 指更多治疗线数（Ultherapy单次治疗的参数），而非「更多疗程」（more treatment sessions）。线数是单次治疗内的密度参数，疗程是治疗次数——两者完全不同。",
        "suggestion": "在更高的治疗密度（更多线数）和6至9个月时的评估下，可能会显示出更有利的反应。"
    },

    # P104: down time mistranslated as computer terminology
    {
        "chapter": "Ch13", "paragraph_index": 104,
        "dimension": "二.表达规范", "check_item": "2.23 术语过于泛化（MT直译）",
        "severity": "critical", "confidence": "high",
        "source_quote": "Recovery and Down Time",
        "target_quote": "恢复与停机时间",
        "issue": "术语错用：停机时间为计算机/工业术语（machine downtime），在医学语境中 down time 指患者术后恢复/休工期。此为机器翻译直译的典型残留。",
        "suggestion": "恢复与休工期"
    },

    # ═══ MEDIUM (should fix) ═══

    # P22: well-defined boundaries
    {
        "chapter": "Ch7", "paragraph_index": 22,
        "dimension": "二.表达规范", "check_item": "2.8 修饰语-名词搭配",
        "severity": "medium", "confidence": "high",
        "source_quote": "creating well-defined thermal injury zones at predetermined depths",
        "target_quote": "在预定深度形成界限清晰的热损伤区域",
        "issue": "修饰语-名词搭配不当：界限清晰一般用于抽象概念或人际关系，形容物理区域应用「边界清晰」。",
        "suggestion": "在预定深度形成边界清晰的热损伤区域"
    },

    # P22: 使字冗余
    {
        "chapter": "Ch7", "paragraph_index": 22,
        "dimension": "二.表达规范", "check_item": "2.15 使/让/令冗余",
        "severity": "medium", "confidence": "high",
        "source_quote": "leaving the surrounding tissue unaffected",
        "target_quote": "同时使周围组织不受影响",
        "issue": "使字冗余，可直接删除。中文习惯话题-述题结构，无需使役标记。",
        "suggestion": "同时周围组织不受影响"
    },

    # P19: 当…时 redundant
    {
        "chapter": "Ch6", "paragraph_index": 19,
        "dimension": "二.表达规范", "check_item": "2.12 当…时冗余",
        "severity": "medium", "confidence": "high",
        "source_quote": "When collagen is exposed to 60C to 65C, it becomes denatured.",
        "target_quote": "当胶原蛋白暴露于60℃至65℃时，它会变性。",
        "issue": "当…时结构冗余，且「它」指代可省略。中文此句型通常不需要当…时框架。",
        "suggestion": "胶原蛋白暴露于60℃至65℃时会发生变性。"
    },

    # P40: elastic fibers straighter
    {
        "chapter": "Ch10", "paragraph_index": 40,
        "dimension": "二.表达规范", "check_item": "2.7 动词-宾语/修饰语搭配",
        "severity": "medium", "confidence": "medium",
        "source_quote": "Elastic fibers of the upper and lower dermis were more parallel and straighter.",
        "target_quote": "真皮上部和下部的弹性纤维更加平行和笔直。",
        "issue": "修饰语搭配不当：笔直一般形容线条、道路等宏观物体，形容微观纤维的结构排列应用「平直」或「整齐」。",
        "suggestion": "真皮上部和下部的弹性纤维更加平行和整齐。"
    },

    # P43: aggressiveness of protocol
    {
        "chapter": "Ch11", "paragraph_index": 43,
        "dimension": "二.表达规范", "check_item": "2.5 褒贬色彩",
        "severity": "medium", "confidence": "high",
        "source_quote": "aggressiveness of protocol",
        "target_quote": "方案的激进程度",
        "issue": "褒贬色彩不当：激进在中文中有明显的负面色彩（冒进、偏激），医学语境中 aggressiveness of protocol 指治疗方案的强度/力度，应用中性词。",
        "suggestion": "方案的强度"
    },

    # P56: 的字堆砌
    {
        "chapter": "Ch13", "paragraph_index": 56,
        "dimension": "二.表达规范", "check_item": "2.14 的字堆砌",
        "severity": "medium", "confidence": "high",
        "source_quote": "Thirty of 35 patients (86%) had a clinically significant improvement in brow elevation (mean, 1.7 mm).",
        "target_quote": "35例患者中有30例（86%）的眉部提升在临床上获得显著改善（平均提升1.7mm）。",
        "issue": "的字堆砌：短短一句含3个「的」（患者的、86%的、提升的），定语层层嵌套导致句子累赘。",
        "suggestion": "35例患者中30例（86%）眉部提升获得临床上显著改善（平均提升1.7 mm）。"
    },

    # P86: complaint → 抱怨
    {
        "chapter": "Ch13", "paragraph_index": 86,
        "dimension": "二.表达规范", "check_item": "2.4 口语化vs书面语",
        "severity": "medium", "confidence": "high",
        "source_quote": "One frequent complaint of the Ulthera system is pain during treatment.",
        "target_quote": "Ulthera系统的一个常见抱怨是治疗过程中的疼痛。",
        "issue": "口语化：抱怨为日常口语用词（如顾客投诉），医学文献中应用「主诉」或「常见问题」。",
        "suggestion": "Ulthera系统的一个常见主诉是治疗过程中的疼痛。"
    },

    # P76: transducer → 换能器
    {
        "chapter": "Ch13", "paragraph_index": 76,
        "dimension": "二.表达规范", "check_item": "2.23 术语过于泛化（MT直译）",
        "severity": "medium", "confidence": "high",
        "source_quote": "Using transducers with 3.0- and 4.5-mm focal depths",
        "target_quote": "使用焦深为3.0mm和4.5mm的换能器",
        "issue": "术语不当：换能器是工程学术语（energy transducer），在医学美容语境中应译为「治疗探头」或「探头」。机器翻译直译残留。",
        "suggestion": "使用聚焦深度为3.0 mm和4.5 mm的治疗探头"
    },

    # P79: treatment passes
    {
        "chapter": "Ch13", "paragraph_index": 79,
        "dimension": "二.表达规范", "check_item": "2.25 字面直译短语",
        "severity": "medium", "confidence": "medium",
        "source_quote": "using 1 (single plane) or 2 (dual treatment depths) treatment passes",
        "target_quote": "采用1次（单平面）或2次（双重治疗深度）治疗遍数",
        "issue": "治疗遍数表述不自然。pass 在此指治疗的遍次/回合，可简化为「治疗次数」或「治疗回合」。",
        "suggestion": "采用1次（单平面）或2次（双重治疗深度）治疗"
    },

    # P97: pilot trials
    {
        "chapter": "Ch13", "paragraph_index": 97,
        "dimension": "二.表达规范", "check_item": "2.25 字面直译短语",
        "severity": "medium", "confidence": "medium",
        "source_quote": "Based on small pilot trials",
        "target_quote": "基于小型试点试验",
        "issue": "试点试验是MT直译（pilot=试点, trials=试验），中文医学文献标准用语为「初步试验」或「预试验」。",
        "suggestion": "基于小型初步试验"
    },

    # P110: ideal candidates
    {
        "chapter": "Ch14", "paragraph_index": 110,
        "dimension": "二.表达规范", "check_item": "2.6 近义词混淆",
        "severity": "medium", "confidence": "high",
        "source_quote": "ideal candidates tend to have mild to moderate aging",
        "target_quote": "理想候选人通常呈现轻度至中度衰老",
        "issue": "近义词误用：候选人（candidate）在中文中多用于职位/选举语境，医学语境中应译为「适用人群」「适应证患者」或「最佳适用对象」。",
        "suggestion": "理想适用人群通常呈现轻度至中度衰老"
    },

    # P112: positive response
    {
        "chapter": "Ch14", "paragraph_index": 112,
        "dimension": "二.表达规范", "check_item": "2.6 近义词混淆",
        "severity": "medium", "confidence": "medium",
        "source_quote": "the overall positive response was 61%",
        "target_quote": "总体阳性反应率为61%",
        "issue": "阳性反应率偏向诊断/检验语境（positive test result），美容治疗中 positive response 应译为「总有效率」或「总改善率」。",
        "suggestion": "总体有效率为61%"
    },

    # P133: 导致 → 可实现
    {
        "chapter": "Ch15", "paragraph_index": 133,
        "dimension": "二.表达规范", "check_item": "2.5 褒贬色彩",
        "severity": "medium", "confidence": "high",
        "source_quote": "can result in mid and lower face elevation",
        "target_quote": "可导致中下面部提升",
        "issue": "褒贬色彩不当：导致表负面结果（导致疾病/问题），面部提升是正面效果，应用「可实现」或「可产生」。",
        "suggestion": "可实现中下面部提升"
    },

    # P16: 导致 → 推动了
    {
        "chapter": "Ch5", "paragraph_index": 16,
        "dimension": "二.表达规范", "check_item": "2.5 褒贬色彩",
        "severity": "medium", "confidence": "high",
        "source_quote": "The continued patient demand … has resulted in more use of …",
        "target_quote": "患者对对非手术、恢复期极短的面部年轻化治疗的持续需求，导致注射用神经毒素和填充剂、皮肤换肤术及紧致治疗的应用日益增多。",
        "issue": "褒贬色彩不当：导致带负面色彩（导致问题），描述需求推动应用增长应用中性词如「推动了」「促进了」。",
        "suggestion": "将「导致」改为「推动了」或「促进了」"
    },

    # P56: outcomes → 结局
    {
        "chapter": "Ch13", "paragraph_index": 56,
        "dimension": "二.表达规范", "check_item": "2.23 术语过于泛化",
        "severity": "medium", "confidence": "medium",
        "source_quote": "measured outcomes at 90 days",
        "target_quote": "测量了90天时的结局",
        "issue": "结局在临床试验语境中不如「结果指标」或「疗效终点」准确。",
        "suggestion": "测量了90天时的疗效指标"
    },

    # ═══ LOW (style improvement) ═══

    # P22: passive voice
    {
        "chapter": "Ch7", "paragraph_index": 22,
        "dimension": "二.表达规范", "check_item": "2.13 被动语态直译",
        "severity": "low", "confidence": "high",
        "source_quote": "When ultrasound waves are microfocused to a point in living tissue",
        "target_quote": "当超声波被微聚焦到活体组织中的某一点时",
        "issue": "被微聚焦保留英文被动结构，中文中「被」字带消极色彩且在此处不必要。",
        "suggestion": "当超声波微聚焦于活体组织中的某一点时"
    },

    # P79: 通常+通常 redundancy
    {
        "chapter": "Ch13", "paragraph_index": 79,
        "dimension": "二.表达规范", "check_item": "2.10 程度副词冗余",
        "severity": "low", "confidence": "high",
        "source_quote": "patients (usually women) commonly seek skin tightening of the upper arms",
        "target_quote": "患者（通常是女性）通常寻求对上臂、大腿内侧以及膝盖正上方区域进行皮肤紧致治疗",
        "issue": "副词重复：通常是和通常寻求在相邻位置使用了同一副词，读感累赘。",
        "suggestion": "患者（通常是女性）常寻求对上臂、大腿内侧以及膝盖正上方区域进行皮肤紧致治疗"
    },

    # P34: although pattern
    {
        "chapter": "Ch9", "paragraph_index": 34,
        "dimension": "二.表达规范", "check_item": "2.17 尽管…但结构直译",
        "severity": "low", "confidence": "medium",
        "source_quote": "Although the currently approved indications are listed below, other facial and nonfacial areas have been treated",
        "target_quote": "尽管目前批准的适应症如下所列，但其他面部及非面部区域也已接受治疗",
        "issue": "尽管…但保留英文让步结构，中文可更简洁。",
        "suggestion": "以下为目前获批的适应症，此外还在其他面部及非面部区域开展了治疗应用"
    },

    # P104: no down time + minimal recovery contradiction
    {
        "chapter": "Ch13", "paragraph_index": 104,
        "dimension": "二.表达规范", "check_item": "2.19 单读测试",
        "severity": "low", "confidence": "medium",
        "source_quote": "the Ulthera system can be considered to have no down time and a minimal recovery period.",
        "target_quote": "Ulthera系统可被视为无恢复期且恢复时间极短。",
        "issue": "无恢复期与恢复时间极短语义重叠且略显矛盾（既说无恢复期又说有极短恢复期）。原文意为 no down time（无需停工）+ minimal recovery（恢复期极短），两项并非同一概念。",
        "suggestion": "Ulthera系统可被视为无需休工期，且恢复时间极短。"
    },

    # P128: clinical return → 临床收益
    {
        "chapter": "Ch15", "paragraph_index": 128,
        "dimension": "二.表达规范", "check_item": "2.23 术语过于泛化",
        "severity": "low", "confidence": "medium",
        "source_quote": "there seems to be little clinical return after 1200 to 1500 lines",
        "target_quote": "超过1200至1500线后，临床收益似乎不大",
        "issue": "收益偏向经济/财务语境（economic return），医学中 clinical return 应译为「临床效益」或「临床获益」。",
        "suggestion": "超过1200至1500线后，临床获益似乎不大"
    },

    # P123: energy-derived
    {
        "chapter": "Ch14", "paragraph_index": 123,
        "dimension": "二.表达规范", "check_item": "2.8 修饰语-名词搭配",
        "severity": "low", "confidence": "medium",
        "source_quote": "energy-derived skin tightening devices",
        "target_quote": "能量源皮肤紧致设备",
        "issue": "能量源搭配生硬，应用「能量类」「基于能量的」或「能量型」。",
        "suggestion": "基于能量的皮肤紧致设备"
    },

    # P141: SUMMARY in medical context
    {
        "chapter": "Ch16", "paragraph_index": 141,
        "dimension": "二.表达规范", "check_item": "2.23 术语过于泛化",
        "severity": "low", "confidence": "medium",
        "source_quote": "SUMMARY",
        "target_quote": "摘要",
        "issue": "摘要在医学论文中通常指文章开头的abstract，结尾的SUMMARY一般译为「总结」或「结论」更准确。",
        "suggestion": "总结"
    },

    # P87: nitrous oxide
    {
        "chapter": "Ch13", "paragraph_index": 87,
        "dimension": "二.表达规范", "check_item": "2.23 术语过于泛化",
        "severity": "low", "confidence": "medium",
        "source_quote": "Nitrous oxide gas",
        "target_quote": "一氧化二氮气体",
        "issue": "一氧化二氮是化学系统命名，医学临床语境中更常用「氧化亚氮」或俗称「笑气」。",
        "suggestion": "氧化亚氮（笑气）"
    },

    # P128: term consistency
    {
        "chapter": "Ch15", "paragraph_index": 128,
        "dimension": "四.术语合规", "check_item": "4.3 跨段术语统一",
        "severity": "low", "confidence": "medium",
        "source_quote": "treatment line density … treatment densities",
        "target_quote": "治疗线密度 … 治疗密度",
        "issue": "同段内同一概念前后用词不一致（「治疗线密度」→「治疗密度」），建议统一。",
        "suggestion": "全文统一使用「治疗线密度」"
    },

    # P131: armamentarium
    {
        "chapter": "Ch15", "paragraph_index": 131,
        "dimension": "二.表达规范", "check_item": "2.23 术语过于泛化",
        "severity": "low", "confidence": "low",
        "source_quote": "Ulthera is only 1 option in the facial rejuvenation armamentarium.",
        "target_quote": "Ulthera只是面部年轻化治疗手段中的一种选择。",
        "issue": "armamentarium译为「治疗手段」可接受，但「治疗体系」更传神。此条为可选建议。",
        "suggestion": "Ulthera只是面部年轻化治疗体系中的一种选择。"
    },
]

# Deduplicate by (paragraph_index, check_item)
seen = set()
unique = []
for i in issues:
    key = (i["paragraph_index"], i["check_item"])
    if key not in seen:
        seen.add(key)
        unique.append(i)

with open("cache/issues_phase4_new.json", "w", encoding="utf-8") as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)

# Stats
sev = {}
dims = {}
for i in unique:
    s = i["severity"]
    sev[s] = sev.get(s, 0) + 1
    d = i["dimension"]
    dims[d] = dims.get(d, 0) + 1

print(f"Total issues: {len(unique)}")
print(f"By severity: {json.dumps(sev, ensure_ascii=False)}")
print(f"By dimension: {json.dumps(dims, ensure_ascii=False)}")
