#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4: Generate issues by referencing paragraph indices.
Reads source from split_source.json and target from phase4_input.json.
"""
import json, sys

with open('cache/phase4_input.json', 'r', encoding='utf-8') as f:
    pdata = json.load(f)
with open('cache/split_source.json', 'r', encoding='utf-8') as f:
    sdata = json.load(f)

paras = {p['global_index']: p['target_text'] for p in pdata['paragraphs']}
full_src = pdata['source_full_text']

issues = []

def add(pi, dim, check_item, sev, conf, src, tgt_key, issue_text, suggestion):
    """tgt_key: either a string (literal target_quote) or int (paragraph_index to look up)"""
    if isinstance(tgt_key, int):
        tgt = paras.get(tgt_key, '')
    else:
        tgt = tgt_key
    issues.append({
        "chapter": "Ch1",
        "paragraph_index": pi,
        "dimension": dim,
        "check_item": check_item,
        "severity": sev,
        "confidence": conf,
        "source_quote": src,
        "target_quote": tgt,
        "issue": issue_text,
        "suggestion": suggestion
    })

# ═══════════════════════════════════
# Ch5: Introduction (P16)
# ═══════════════════════════════════
add(16, "二.表达规范", "2.1 错别字/衍文", "medium", "high",
    "The continued patient demand for nonsurgical and minimal downtime facial rejuvenation...",
    16,
    "「对对」为重复字衍文（患者对对非手术），应为「对」。此为文本输入错误。",
    "改为：「患者对非手术、恢复期极短的面部年轻化治疗的持续需求」")

# ═══════════════════════════════════
# Ch6: Collagen Denaturation (P19)
# ═══════════════════════════════════
add(19, "二.表达规范", "2.4 口语化vs书面语", "medium", "high",
    "When collagen is exposed to 60°C to 65°C, it becomes denatured.",
    19,
    "「它会变性」口语化。医学文献中应为「会发生变性」或「即发生变性」。「它」字指代在中文医学文献中不自然。",
    "改为：「当胶原蛋白暴露于60℃至65℃时，即发生变性。」")

add(19, "四.术语合规", "4.3 跨段术语统一", "critical", "high",
    "neocollagenesis → appears in chapter title and body text",
    19,
    "同一概念「neocollagenesis」在全文中混用——章节标题用「新胶原生成」、P19正文用「新的胶原蛋白合成」、P22用「新胶原生成」。此为学术论文核心术语，必须统一。",
    "统一为：「新胶原蛋白合成」（保留「蛋白」全称）。标题改为「胶原蛋白变性与新胶原蛋白合成」。")

# ═══════════════════════════════════
# Ch7: Mechanism of Action (P22, P23)
# ═══════════════════════════════════
add(22, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "Higher ultrasound frequencies have more superficial tissue effects...",
    22,
    "「表浅组织」在医学中文中的标准表述为「浅表组织」。「表浅」非标准医学术语（应为「浅表」）。",
    "改为：「较高的超声频率对浅表组织影响更大」")

add(22, "二.表达规范", "2.15 使/让/令冗余", "medium", "high",
    "...leaving the surrounding tissue unaffected.",
    22,
    "「使」字为英文 leaving X unaffected 的直译痕迹。删掉「使」字后中文更通顺。",
    "改为：「…同时周围组织不受影响。」（删「使」字）")

add(22, "二.表达规范", "2.4 口语化vs书面语", "medium", "medium",
    "At the resulting tissue temperatures, collagen contraction, and denaturation is seen...",
    22,
    "「会出现…并刺激」为口语化表达。学术文献中建议用「可见…进而」。",
    "改为：「在该组织温度下，可见胶原收缩与变性，进而刺激新胶原蛋白合成。」")

add(23, "二.表达规范", "2.23 MT术语泛化", "medium", "high",
    "MFU is different from RF energy in that it can be microfocused to target deeper tissue...",
    23,
    "「靶向」为 target 的MT直译。此句为非靶向治疗语境，建议改为更通用的「作用于」或「针对」。",
    "建议：「…其能量可微聚焦至更深层组织，作用于深层而不影响浅层。」")

add(23, "二.表达规范", "2.16 对于/关于句首冗余", "medium", "medium",
    "For an RF device to achieve high temperatures, surface cooling is needed...",
    23,
    "「对于」句首为英文 For X, Y 的直译。中文可省略「对于」。",
    "改为：「RF设备要达到高温，则需要表面冷却以保护皮肤。」")

# ═══════════════════════════════════
# Ch8: Ulthera System (P26, P31)
# ═══════════════════════════════════
add(26, "二.表达规范", "2.6 近义词混淆", "medium", "medium",
    "...is routinely used for panfacial and submental treatments.",
    26,
    "「通常用于」将 routinely 译为一般频率描述。原文 routinely 有「常规用于」之意（已成临床常规），非单纯的「通常」。训练数据中此对近义词反复出现。",
    "改为：「…但现已常规用于全面部和颏下治疗。」")

add(31, "二.表达规范", "2.25 字面直译短语", "medium", "medium",
    "The focal energy delivery in given in predetermined lines results in discrete intervals between 1 mm3 coagulation zones that promote healing.",
    31,
    "「导致…产生离散间隔」中「导致」含贬义色彩（应中性描述治疗机制），且 discrete intervals 译为「离散间隔」不够直观。",
    "建议：「预定的线状聚焦能量传递使1 mm³凝固区之间形成规则间隔，从而促进愈合。」")

# ═══════════════════════════════════
# Ch9: Indications (P37)
# ═══════════════════════════════════
add(37, "一.双语忠实度", "1.4 错译", "critical", "high",
    "Improve lines and wrinkles in decollete",
    37,
    "「decollete」指女性颈下/胸前V形区域（法语借词），非「肩颈部」。医学美容文献中应译为「前胸/领口区域」。",
    "改为：「改善前胸（decollete）区域的细纹和皱纹」")

# ═══════════════════════════════════
# Ch10: Histologic Studies (P40)
# ═══════════════════════════════════
add(40, "二.表达规范", "2.24 修饰语位置欧化", "medium", "medium",
    "An early prototype Ulthera device was used on the lateral cheek region in patients who would be undergoing a surgical rhytidectomy within 12 weeks of treatment.",
    40,
    "语序严重欧化——「患者治疗12周内将接受手术除皱术的患者」定语堆砌且逻辑混乱。",
    "建议重组语序：「治疗对象为计划在12周内接受手术除皱术的患者，在其面颊外侧区域使用了一款早期Ulthera原型设备。」")

add(40, "二.表达规范", "2.4 口语化vs书面语", "medium", "medium",
    "Elastic fibers of the upper and lower dermis were more parallel and straighter.",
    40,
    "「笔直」为口语词，学术文献中应用「平直」或「排列更加平行、有序」。",
    "改为：「真皮上部和下部的弹性纤维排列更加平行、平直。」")

add(40, "一.双语忠实度", "1.5 指代/逻辑连接", "medium", "medium",
    "...without injury to the epidermis, which was absent by 12 weeks.",
    40,
    "「表皮未受损伤，且该损伤在12周时已消失」——连接词「且」导致逻辑不清（前者描述表皮，后者描述热损伤区）。",
    "建议：「…真皮出现一致且可重复的热损伤区域（表皮未受损伤），该热损伤区在12周时已消失。」")

# ═══════════════════════════════════
# Ch13: Specific Applications
# ═══════════════════════════════════
# P56
add(56, "二.表达规范", "2.23 MT术语泛化", "medium", "medium",
    "measured outcomes at 90 days",
    56,
    "「结局」为 outcomes 的MT直译。临床试验术语中应为「结局指标」或「治疗结果」。「测量…结局」搭配也不自然。",
    "改为：「评估了90天时的治疗结果」")

add(56, "二.表达规范", "2.14 的字堆砌", "medium", "medium",
    "Thirty of 35 patients (86%) had a clinically significant improvement in brow elevation",
    56,
    "「的」字过多，句中有3个「的」连用，影响阅读流畅度。",
    "建议：「35例患者中，30例（86%）眉部提升获得临床上显著改善（平均提升1.7mm）。」")

add(56, "二.表达规范", "2.19 单读测试", "medium", "high",
    "Ultrasound pulses were administered every 1.5 mm along each treatment line",
    56,
    "「施加」搭配不自然——超声脉冲应搭配「发射」或「给予」，而非「施加」（后者常用于力/压力）。",
    "改为：「超声脉冲沿每条治疗线每隔1.5 mm发射一次」")

# P60
add(60, "二.表达规范", "2.23 MT术语泛化", "critical", "high",
    "using 1.5 mm and 3.0 mm probes",
    60,
    "「探头」为MT直译短词。医疗器械文档中 probe 标准译法为「治疗探头」（加领域修饰语）。训练数据中此修订出现386次。",
    "改为：「…使用1.5 mm和3.0 mm治疗探头…」")

# P63/P70 text split
add(63, "一.双语忠实度", "1.1 完整性", "critical", "high",
    "Two months after treatment of the face and submental area, all patients demonstrated...",
    63,
    "P63段末「治疗两个」与P70段首「月后」之间因图片插入（图2）导致文字断裂。原文为连续段落，无断裂。建议人工确认排版意图。",
    "建议人工确认：原文为完整句，图片插入位置是否合理，或将段首「月后」移至P63段末。")

# P73
add(73, "四.术语合规", "4.3 跨段术语统一", "medium", "medium",
    "SMAS contraction proportional to the amount of energy delivered.",
    73,
    "P73单独使用缩写「SMAS」但前文（P29首次出现）距离较远。对不熟悉该缩写的读者可能不够清晰。",
    "在P73首次出现的段落加注全称：「SMAS（浅表肌肉腱膜系统）」")

# P76
add(76, "二.表达规范", "2.25 字面直译短语", "medium", "medium",
    "Standardized blinded assessment and patient satisfaction was measured.",
    76,
    "「测量了标准化的设盲评估」——「测量…评估」搭配不当。应为「进行了标准化的盲法评估和患者满意度调查」。",
    "改为：「进行了标准化的盲法评估和患者满意度调查。」")

# P79
add(79, "二.表达规范", "2.17 尽管但结构", "low", "low",
    "Despite the reported favorable results, the published before and after images show modest improvements.",
    79,
    "「尽管…但」结构可接受，但稍显翻译腔。可简化为更紧凑的中文表达。",
    "建议（可选）：虽报道结果良好，已发布的术前和术后图像却显示改善幅度有限。")

# P86
add(86, "二.表达规范", "2.4 口语化vs书面语", "medium", "high",
    "One frequent complaint of the Ulthera system is pain during treatment.",
    86,
    "「抱怨」为口语词。医学文献中 complaint 在患者语境中应译为「主诉」或「不适」。训练数据中此修订出现多次。",
    "改为：「患者对Ulthera系统的一个常见主诉是治疗过程中的疼痛。」")

# P107
add(107, "二.表达规范", "2.13 被动/直译", "medium", "low",
    "side effects are generally mild and transient in nature.",
    107,
    "「性质轻微且短暂」——mild and transient in nature 的字面直译。「性质」二字冗余。",
    "改为：「…副作用通常轻微且短暂。」")

# ═══════════════════════════════════
# Ch14: Results
# ═══════════════════════════════════
add(110, "二.表达规范", "2.23 MT术语泛化", "critical", "high",
    "Because ideal candidates tend to have mild to moderate aging...",
    110,
    "「候选人」为 candidates 的字面直译。医学美容文献中应译为「适应证患者」或「适合治疗的患者」。",
    "改为：「由于适合治疗的患者通常表现为轻度至中度皮肤老化」")

add(110, "二.表达规范", "2.5 褒贬色彩", "medium", "medium",
    "those with more severe aging... are likely to be better served by surgical treatment.",
    110,
    "「那些…的人群」为英文 those with... 的直译结构。中文可简化为「…的患者」。",
    "改为：「而衰老程度更重、皮肤松弛且出现颈阔肌带的患者，可能更适合通过手术治疗。」")

add(111, "二.表达规范", "2.23 MT术语泛化", "medium", "high",
    "it is likely that a higher response is possible...",
    111,
    "「响应」为 response 的MT直译。临床试验术语中应为「反应率」或「有效率」。",
    "改为：「…可能会获得更高的反应率。」")

add(120, "一.双语忠实度", "1.4 错译", "critical", "high",
    "higher treatment density (more lines)",
    120,
    "「更多疗程」为严重错译——原文 more lines 指更多治疗线数，非治疗疗程（sessions）。「疗程」是完全不同的临床概念。",
    "改为：「若采用更高的治疗密度（更多治疗线）并在6至9个月时进行评估，可能获得更有利的治疗反应率。」")

add(120, "一.双语忠实度", "1.4 错译（单位）", "critical", "high",
    "body mass index of 30 mg/kg2 or less",
    120,
    "BMI单位严重错误——原文有矛盾（前句30 kg/m²，后句30 mg/kg²），译文照搬了错误的 mg/kg²。mg vs kg 相差一百万倍，且BMI单位应为 kg/m²。",
    "改为：「体重指数≤30 kg/m²的患者」。注意原文前后句单位不一致（应为作者笔误），译文应统一为正确单位 kg/m²。")

add(123, "二.表达规范", "2.23 MT术语泛化", "medium", "medium",
    "energy-derived skin tightening devices",
    123,
    "「能量源设备」为 energy-derived devices 的直译。中文更自然表述为「能量类设备」或「能量型设备」。",
    "建议：「…能量类皮肤紧致设备的长期效果仍缺乏数据支持。」")

add(126, "二.表达规范", "2.25 字面直译短语", "medium", "medium",
    "nurses or trained aestheticians provide the service.",
    126,
    "「提供服务」的「服务」为英文 service 的字面直译。医疗语境下应译为「执行治疗」或「进行操作」。",
    "改为：「…由护士或经过培训的美容师执行治疗。」")

# ═══════════════════════════════════
# Ch15: Treatment Protocol Variation
# ═══════════════════════════════════
add(128, "二.表达规范", "2.12 当时/翻译腔", "medium", "medium",
    "Experienced Ulthera user consensus group participants reported...",
    128,
    "「用户共识组参与者」定语链过长。consensus group participants 可简化为「专家共识组成员」。",
    "建议：「经验丰富的Ulthera专家共识组成员报告，每次治疗使用600至800条线时疗效显著。」")

add(128, "二.表达规范", "2.19 单读测试", "medium", "medium",
    "Because not all patients may not respond to treatments, there is room for increasing the treatment line density.",
    128,
    "「存在增加…的空间」为英文 there is room for 的字面直译。中文更自然表述为「仍可进一步增加…」或「仍有…余地」。",
    "改为：「…因此仍可进一步增加治疗线密度。」")

add(133, "一.双语忠实度", "1.1 完整性/句意混乱", "critical", "high",
    "Facial and neck skin tightening can also be achieved by a variety of energy devices, including RF. Injectable fillers and fat grafts can result in mid and lower face elevation",
    133,
    "原文为两个独立要点（RF设备 / 注射填充材料+脂肪移植），译文将二者合并为一句，导致「包括射频注射填充材料和脂肪移植」——RF设备与注射填充材料被混为一谈。句号缺失也导致与下句粘连。",
    "改为两个独立要点：① 面部和颈部皮肤紧致也可以通过多种能量设备实现，包括RF；② 注射填充材料和脂肪移植可实现中下面部提升。")

add(136, "二.表达规范", "2.2 标点体系", "low", "high",
    "deoxycholic acid (Kybella) injections",
    136,
    "中文中应使用全角括号：去氧胆酸（Kybella）。当前使用半角括号。",
    "改为：「注射去氧胆酸（Kybella）来减少」")

# ═══════════════════════════════════
# Ch16: Summary (P141)
# ═══════════════════════════════════
add(141, "二.表达规范", "2.6 近义词混淆", "medium", "medium",
    "variability in patient response needs to be considered",
    141,
    "「差异性」在统计学语境下合适，但此句指个体患者反应不一。variability 译为「个体差异」或「变异性」比「差异性」更精确。",
    "建议：「需考虑患者反应的个体差异性」")

# ═══════════════════════════════════
# Cross-chapter issues
# ═══════════════════════════════════
add(0, "三.数字符号单位", "3.2 范围表达统一性", "low", "medium",
    "Full document range expression audit",
    "全文中混合使用「至」「到」和「–」表示范围：P9「3到6个月」、P19「60℃至65℃」、P23「60℃到70℃」、P47「30到60分钟」、P56「0.75–1.2J」。",
    "学术论文中范围表达不统一：混用「至」「到」「–」三种形式。",
    "建议：全文数值范围统一使用「至」（如「3至6个月」「60℃至65℃」），能量/剂量范围可保留「–」（如「0.75–1.2 J」）。")

# Sort by paragraph_index
issues.sort(key=lambda x: (x['paragraph_index'], x['severity']))

# Summary
output = {
    "issues": issues,
    "summary": {
        "total_issues": len(issues),
        "by_severity": {
            "critical": sum(1 for i in issues if i['severity'] == 'critical'),
            "medium": sum(1 for i in issues if i['severity'] == 'medium'),
            "low": sum(1 for i in issues if i['severity'] == 'low')
        },
        "by_dimension": {}
    }
}
for i in issues:
    dim = i['dimension']
    output['summary']['by_dimension'][dim] = output['summary']['by_dimension'].get(dim, 0) + 1

with open('cache/issues_phase4_new.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Phase 4 complete: {len(issues)} issues")
print(f"  critical: {output['summary']['by_severity']['critical']}")
print(f"  medium: {output['summary']['by_severity']['medium']}")
print(f"  low: {output['summary']['by_severity']['low']}")
print(f"Dimensions: {output['summary']['by_dimension']}")
