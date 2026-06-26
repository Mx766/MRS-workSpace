#!/usr/bin/env python3
"""Write Phase 4 semantic review issues to cache/issues_phase4_new.json"""
import json, sys

issues = []

def add(ch, pi, dim, ci, sev, conf, sq, tq, iss, sug):
    issues.append({
        "chapter": ch,
        "paragraph_index": pi,
        "dimension": dim,
        "check_item": ci,
        "severity": sev,
        "confidence": conf,
        "source_quote": sq,
        "target_quote": tq,
        "issue": iss,
        "suggestion": sug
    })

add("Ch5", 16, "二.表达规范", "2.1 错别字/拼写", "medium", "high",
    "The continued patient demand for nonsurgical and minimal downtime facial rejuvenation...",
    "患者对对非手术、恢复期极短的面部年轻化治疗的持续需求...",
    "“对对”为重复输入错误，第二个“对”字多余。",
    "改为“患者对非手术、恢复期极短的面部年轻化治疗的持续需求...”")

add("Ch7", 22, "一.双语忠实度", "1.4 错译", "medium", "high",
    "Higher ultrasound frequencies have more superficial tissue effects and lower frequencies have deeper tissue effects.",
    "较高的超声频率对表浅组织影响更大，较低的频率则对深层组织影响更大。",
    "原文“more superficial”与“deeper”描述的是效应发生的深度位置（更浅层/更深层），译文“影响更大”将其误解为效应的大小程度，改变了物理含义。",
    "改为“较高的超声频率作用于更表浅的组织，较低的频率则作用于更深层的组织。”")

add("Ch7", 22, "二.表达规范", "2.15 “使/让/令”冗余", "low", "medium",
    "...while leaving the surrounding tissue unaffected",
    "...同时使周围组织不受影响",
    "“使”字句式属英文使役结构直译（leaving → 使），中文可直接用话题-陈述结构表达更自然。",
    "改为“而周围组织不受影响”")

add("Ch7", 23, "二.表达规范", "2.16 “对于/关于/就…而言”句首冗余", "low", "medium",
    "For an RF device to achieve high temperatures, surface cooling is needed to protect the skin.",
    "对于RF设备，要达到高温，需要表面冷却以保护皮肤。",
    "“对于”系英文“For”的直译，中文可省略介词直接以话题起句。",
    "改为“RF设备要达到高温，需要表面冷却以保护皮肤。”")

add("Ch8", 26, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "...but is routinely used for panfacial and submental treatments.",
    "...但通常用于全面部和颏下治疗。",
    "“routinely”在医学语境中应译为“常规”而非“通常”。“通常”暗示频率，“常规”强调标准做法。",
    "改为“但常规用于全面部和颏下治疗。”")

add("Ch8", 27, "五.格式排版", "5.2 格式规范", "low", "low",
    "1.5 mm / 3.0 mm / 4.5 mm",
    "1.5mm / 3.0mm / 4.5mm",
    "数值与单位“mm”之间缺少空格，不符合中文科技期刊编排规范（GB/T 3101）。",
    "改为“1.5 mm”“3.0 mm”“4.5 mm”，数值与单位间加半角空格。")

add("Ch8", 31, "二.表达规范", "2.7 动词-宾语搭配", "medium", "high",
    'The focal energy delivery in given in predetermined "lines" results in discrete intervals between 1 mm3 coagulation zones that promote healing.',
    "预定的“线”状聚焦能量传递，导致在1 mm3凝固区之间产生离散间隔，从而促进愈合。",
    "“导致...产生间隔”搭配不自然。“导致”带负面色彩，应改用中性动词。",
    "改为“预定的“线”状聚焦能量传递在1 mm³凝固区之间形成离散间隔，从而促进愈合。”")

add("Ch9", 37, "一.双语忠实度", "1.4 错译", "critical", "high",
    "Improve lines and wrinkles in décolleté",
    "改善肩颈部的细纹和皱纹",
    "décolleté在医学美容中专指前胸上部/领口暴露区域（锁骨以下、胸部以上），译为“肩颈部”范围偏离，将颈部也包含了进去，与原词解剖位置不符。",
    "改为“改善前胸部（décolleté）的细纹和皱纹”")

add("Ch10", 40, "二.表达规范", "2.20 长句拆分", "medium", "high",
    "An early prototype Ulthera device was used on the lateral cheek region in patients who would be undergoing a surgical rhytidectomy within 12 weeks of treatment.",
    "一款早期Ulthera原型设备被用于患者治疗12周内将接受手术除皱术的患者的面颊外侧区域。",
    "定语堆叠过长导致句子拗口难读，“患者”重复出现，语序不顺，不易理解。",
    "改为“一款早期Ulthera原型设备被用于患者的面颊外侧区域，这些患者将在治疗后12周内接受手术除皱术。”")

add("Ch13", 56, "二.表达规范", "2.14 “的”字堆砌", "medium", "medium",
    "Thirty of 35 patients (86%) had a clinically significant improvement in brow elevation (mean, 1.7 mm).",
    "35例患者中有30例（86%）的眉部提升在临床上获得显著改善（平均提升1.7mm）。",
    "“35例患者中有30例（86%）的眉部提升”中“的”字使定语过长，可删除使之更流畅。",
    "改为“35例患者中30例（86%）眉部提升获得临床上显著改善（平均提升1.7mm）。”")

add("Ch13", 79, "一.双语忠实度", "1.4 错译", "critical", "high",
    "One small study included 6 of each of these areas using 1 (single plane) or 2 (dual treatment depths) treatment passes.",
    "一项小型研究对每个区域进行了6次治疗，采用1次（单平面）或2次（双重治疗深度）治疗遍数。",
    "原文“6 of each of these areas”指每个区域纳入6名患者/受试者，译文“进行了6次治疗”误解为治疗次数，改变了研究设计的含义。",
    "改为“一项小型研究在每个区域各纳入6名受试者，采用1次（单平面）或2次（双重治疗深度）治疗遍数。”")

add("Ch13", 82, "四.术语合规", "4.5 跨领域区分", "low", "medium",
    "postinflammatory hyperpigmentation",
    "炎症后色素沉着过度",
    "中国皮肤科学界标准术语为“炎症后色素沉着”，“过度”虽对应“hyper-”但在中文术语中属冗余。",
    "改为“炎症后色素沉着”（中国皮肤科标准术语）")

add("Ch13", 110, "二.表达规范", "2.19 单读测试", "low", "medium",
    "There is also mild edema that contributes to the early aesthetic improvement seen by patients.",
    "还有轻度水肿有助于患者看到的早期美学改善。",
    "“还有”作为句首偏口语化，学术文体中宜用“此外”/“另外”；“有助于患者看到的”句式拗口。",
    "改为“此外，轻度水肿也有助于患者观察到的早期美学改善。”")

add("Ch14", 120, "一.双语忠实度", "1.4 错译", "critical", "high",
    "It is possible that a higher treatment density (more lines) and assessment at 6 to 9 months may have shown more favorable responses.",
    "在更高的治疗密度（更多疗程）和6至9个月时的评估下，可能会显示出更有利的反应。",
    "“lines”指治疗线的数量（密度），并非“疗程”（treatment sessions/courses）。二者在临床上是完全不同的概念。",
    "改为“在更高的治疗密度（更多治疗线数）和6至9个月时的评估下，可能会显示出更有利的反应。”")

add("Ch15", 133, "一.双语忠实度", "1.1 完整性", "medium", "high",
    "Facial and neck skin tightening can also be achieved by a variety of energy devices, including RF; Injectable fillers and fat grafts can result in mid and lower face elevation",
    "面部和颈部皮肤紧致也可以通过多种能量设备实现，包括射频注射填充材料和脂肪移植，可导致中下面部提升",
    "原文为两个独立的句子/要点（分号分隔）：(1)RF等能量设备紧肤，(2)填充剂/脂肪移植提升中下面部。译文将其合并为一个句子，使“注射填充材料和脂肪移植”被误归类为“能量设备”的子项，改变了原文逻辑。",
    "改为“面部和颈部皮肤紧致也可以通过多种能量设备实现，包括RF；注射填充材料和脂肪移植可实现中下面部提升”")

with open('cache/issues_phase4_new.json', 'w', encoding='utf-8') as f:
    json.dump(issues, f, ensure_ascii=False, indent=2)

print(f'Written {len(issues)} issues to cache/issues_phase4_new.json')
sevs = {}
for i in issues:
    sevs[i['severity']] = sevs.get(i['severity'], 0) + 1
print(f'Severity breakdown: {sevs}')
dims = {}
for i in issues:
    dims[i['dimension']] = dims.get(i['dimension'], 0) + 1
print(f'Dimension breakdown: {dims}')
