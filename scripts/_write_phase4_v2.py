#!/usr/bin/env python3
"""Phase 4 full review: main agent thorough 6-dimension check"""
import json

I = []

def add(ch, pi, dim, ci, sev, conf, sq, tq, iss, sug):
    I.append(dict(chapter=ch, paragraph_index=pi, dimension=dim,
        check_item=ci, severity=sev, confidence=conf,
        source_quote=sq, target_quote=tq, issue=iss, suggestion=sug))

# === Ch5 引言 ===
add("Ch5", 16, "二.表达规范", "2.1 错别字/拼写", "medium", "high",
    "The continued patient demand for nonsurgical and minimal downtime facial rejuvenation...",
    "患者对对非手术、恢复期极短的面部年轻化治疗的持续需求...",
    "“对对”为重复输入错误，第二个“对”字多余。",
    "改为“患者对非手术、恢复期极短的面部年轻化治疗的持续需求...”")

add("Ch5", 16, "二.表达规范", "2.5 褒贬色彩", "medium", "high",
    "...has resulted in more use of injectable neurotoxins and fillers...",
    "...导致注射用神经毒素和填充剂...应用日益增多。",
    "“导致”在中文中带负面色彩，原文“has resulted in”为中性因果关系，应使用中性动词。",
    "改为“促使注射用神经毒素和填充剂...应用日益增多”")

add("Ch5", 16, "二.表达规范", "2.23 术语过于泛化", "low", "medium",
    "...skin resurfacing and tightening treatments.",
    "...皮肤换肤术及紧致治疗...",
    "“皮肤换肤术”中“术”字多余，医学文献中“皮肤换肤”或“皮肤重建”即可。",
    "改为“皮肤换肤及紧致治疗”")

# === Ch6 胶原蛋白变性 ===
add("Ch6", 19, "二.表达规范", "2.4 口语化vs书面语", "low", "medium",
    "When collagen is exposed to 60°C to 65°C, it becomes denatured.",
    "当胶原蛋白暴露于60℃至65℃时，它会变性。",
    "“它会变性”偏口语化，学术论文宜用更正式的表述。",
    "改为“当胶原蛋白暴露于60℃至65℃时，即发生变性”")

# === Ch7 作用机制 ===
add("Ch7", 22, "一.双语忠实度", "1.4 错译", "medium", "high",
    "Higher ultrasound frequencies have more superficial tissue effects and lower frequencies have deeper tissue effects.",
    "较高的超声频率对表浅组织影响更大，较低的频率则对深层组织影响更大。",
    "原文“more superficial”与“deeper”描述效应发生的深度位置，译文“影响更大”将其误解为效应的大小程度。",
    "改为“较高的超声频率作用于更表浅的组织，较低的频率则作用于更深层的组织”")

add("Ch7", 22, "二.表达规范", "2.8 修饰语-名词搭配", "medium", "high",
    "...creating well-defined thermal injury zones at predetermined depths...",
    "...在预定深度形成界限清晰的热损伤区域...",
    "“界限清晰”用于描述热损伤区域的边界不够自然，中文习惯“边界清晰”。",
    "改为“在预定深度形成边界清晰的热损伤区域”")

add("Ch7", 22, "二.表达规范", "2.15 “使/让/令”冗余", "low", "medium",
    "...while leaving the surrounding tissue unaffected.",
    "...同时使周围组织不受影响。",
    "“使”字属英文使役结构直译（leaving → 使），中文可直接用话题-陈述结构。",
    "改为“而周围组织不受影响”")

add("Ch7", 23, "二.表达规范", "2.16 “对于”句首冗余", "low", "medium",
    "For an RF device to achieve high temperatures, surface cooling is needed to protect the skin.",
    "对于RF设备，要达到高温，需要表面冷却以保护皮肤。",
    "“对于”系英文“For”的直译，中文可省略介词直接以话题起句。",
    "改为“RF设备要达到高温，需要表面冷却以保护皮肤”")

# === Ch8 ULTHERA系统 ===
add("Ch8", 26, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "...but is routinely used for panfacial and submental treatments.",
    "...但通常用于全面部和颏下治疗。",
    "“routinely”在医学语境中应译为“常规”。“通常”暗示频率，“常规”强调标准临床做法。",
    "改为“但常规用于全面部和颏下治疗”")

add("Ch8", 27, "五.格式排版", "5.2 格式规范", "low", "low",
    "1.5 mm / 3.0 mm / 4.5 mm",
    "1.5mm / 3.0mm / 4.5mm",
    "数值与单位之间缺少空格，不符合中文科技期刊编排规范（GB/T 3101）。",
    "改为“1.5 mm / 3.0 mm / 4.5 mm”")

add("Ch8", 31, "二.表达规范", "2.7 动词-宾语搭配", "medium", "high",
    '...results in discrete intervals between 1 mm3 coagulation zones that promote healing.',
    "预定的“线”状聚焦能量传递，导致在1 mm3凝固区之间产生离散间隔...",
    "“导致...产生间隔”搭配不自然，“导致”带负面色彩，此处为客观物理结果。",
    "改为“预定的‘线’状聚焦能量传递在1 mm³凝固区之间形成离散间隔，从而促进愈合”")

add("Ch8", 31, "二.表达规范", "2.15 “使/让/令/允许”冗余", "low", "medium",
    "...a monitor allows direct visualization of where the energy will be delivered...",
    "...监视器允许直观显示能量传递的位置...",
    "“允许”系英文“allows”的直译，中文可直接说“可直观显示”。",
    "改为“监视器可直观显示能量传递的位置”")

# === Ch9 适应症 ===
add("Ch9", 37, "一.双语忠实度", "1.4 错译", "critical", "high",
    "Improve lines and wrinkles in décolleté",
    "改善肩颈部的细纹和皱纹",
    "décolleté在医学美容中专指前胸上部/领口暴露区域（锁骨以下），译为“肩颈部”将颈部也包含了进去，解剖位置不符。",
    "改为“改善前胸部（décolleté）的细纹和皱纹”")

# === Ch10 组织学研究 ===
add("Ch10", 40, "二.表达规范", "2.20 长句拆分", "medium", "high",
    "An early prototype Ulthera device was used on the lateral cheek region in patients who would be undergoing a surgical rhytidectomy within 12 weeks of treatment.",
    "一款早期Ulthera原型设备被用于患者治疗12周内将接受手术除皱术的患者的面颊外侧区域。",
    "定语堆叠过长、语序不顺，两个“患者”嵌套导致句子拗口难读。",
    "改为“一款早期Ulthera原型设备被用于即将在治疗后12周内接受手术除皱术的患者面颊外侧区域”")

add("Ch10", 40, "二.表达规范", "2.13 被动语态直译", "low", "medium",
    "An early prototype Ulthera device was used on the lateral cheek region...",
    "一款早期Ulthera原型设备被用于...患者的面颊外侧区域。",
    "“被用于”是英文被动语态的直译，中文可用主动语态表达更自然。",
    "改为“研究者使用一款早期Ulthera原型设备，对即将在治疗后12周内接受手术除皱术的患者面颊外侧区域进行了治疗”")

# === Ch11 治疗时间 ===
add("Ch11", 43, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "...aggressiveness of protocol...",
    "...方案的激进程度...",
    "“激进程度”在医学语境中带贬义，原文“aggressiveness”在此为中性描述治疗强度。",
    "改为“方案的强度”或“治疗强度”")

# === Ch13 具体应用 ===
add("Ch13", 56, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "...measured outcomes at 90 days.",
    "...测量了90天时的结局。",
    "“结局”在中文医学文献中通常指临床试验的终点指标（endpoint），此处为一般性的“结果/效果”。",
    "改为“测量了90天时的结果”")

add("Ch13", 56, "二.表达规范", "2.14 “的”字堆砌", "medium", "medium",
    "Thirty of 35 patients (86%) had a clinically significant improvement in brow elevation (mean, 1.7 mm).",
    "35例患者中有30例（86%）的眉部提升在临床上获得显著改善（平均提升1.7mm）。",
    "“35例患者中有30例（86%）的眉部提升”中“的”字使定语过长，删除后更流畅。",
    "改为“35例患者中30例（86%）眉部提升获得临床上显著改善（平均提升1.7mm）”")

add("Ch13", 59, "二.表达规范", "2.13 被动语态直译", "low", "medium",
    "Upper eyelid improvement can be seen after treatment of the forehead and brow...",
    "由于眉部提升，前额和眉部治疗后可以看到上眼睑的改善。",
    "译文已较好处理被动语态，但“由于眉部提升”的位置使因果关系略显倒置。",
    "改为“前额和眉部治疗后的眉部提升可带来上眼睑改善”")

add("Ch13", 73, "二.表达规范", "2.24 修饰语位置欧化", "medium", "high",
    "A cadaver study of transcutaneous Ulthera energy delivery in the face demonstrated thermal injury zones in the SMAS...",
    "一项关于经皮Ulthera能量在面部传递的尸体研究显示，SMAS中出现热损伤区域...",
    "“经皮Ulthera能量在面部传递”修饰语序列欧化，与中文修饰语前置习惯不符。",
    "改为“一项尸体研究显示，Ulthera经皮能量传递在面部SMAS中产生热损伤区域”")

add("Ch13", 76, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "A single study evaluated ultrasound skin tightening and smoothing of the buttocks.",
    "一项单一研究评估了超声皮肤紧致和臀部平滑效果。",
    "“单一研究”易误解为“过于简单的研究”，应为“单项研究”表示数量。",
    "改为“一项研究评估了超声皮肤紧致和臀部平滑效果”或“单项研究评估了...”")

add("Ch13", 79, "一.双语忠实度", "1.4 错译", "critical", "high",
    "One small study included 6 of each of these areas using 1 (single plane) or 2 (dual treatment depths) treatment passes.",
    "一项小型研究对每个区域进行了6次治疗，采用1次（单平面）或2次（双重治疗深度）治疗遍数。",
    "原文“6 of each of these areas”指每个区域纳入6名患者/受试者，译文误解为“6次治疗”，改变了研究设计含义。",
    "改为“一项小型研究在每个区域各纳入6名受试者，采用1次（单平面）或2次（双重治疗深度）治疗遍数”")

add("Ch13", 82, "四.术语合规", "4.5 跨领域区分", "low", "medium",
    "postinflammatory hyperpigmentation",
    "炎症后色素沉着过度",
    "中国皮肤科学界标准术语为“炎症后色素沉着”，“过度”虽对应“hyper-”前缀但在中文术语中属冗余。",
    "改为“炎症后色素沉着”（中国皮肤科标准术语）")

add("Ch13", 104, "二.表达规范", "2.20 长句/冗余", "medium", "high",
    "...the Ulthera system can be considered to have no down time and a minimal recovery period.",
    "...Ulthera系统可被视为无恢复期且恢复时间极短。",
    "“无恢复期”与“恢复时间极短”语义重复（no down time ≈ minimal recovery period），连用造成冗余。",
    "改为“Ulthera系统可被视为几乎无恢复期，恢复时间极短”或取其一“Ulthera系统恢复期极短”")

add("Ch13", 107, "三.数字符号单位", "3.1 引用编号位置", "low", "low",
    "...transient bruising, skin pigment changes,9 and neuropathic pain...",
    "...短暂性瘀伤、皮肤色素改变、9 以及持续长达3个月的神经性疼痛。",
    "引用编号“9”插入位置打断了中文的并列结构，应移至句末或调整位置。",
    "改为“...短暂性瘀伤、皮肤色素改变以及持续长达3个月的神经性疼痛。9”")

add("Ch13", 110, "二.表达规范", "2.19 单读测试", "low", "medium",
    "There is also mild edema that contributes to the early aesthetic improvement seen by patients.",
    "还有轻度水肿有助于患者看到的早期美学改善。",
    "“还有”句首偏口语化；“有助于患者看到的”句式拗口，像翻译体。",
    "改为“此外，轻度水肿也有助于患者观察到的早期美学改善”")

# === Ch14 结果 ===
add("Ch14", 111, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "...the overall positive response was 61%.",
    "...总体阳性反应率为61%。",
    "“阳性反应率”在医学文献中通常指实验室检测结果，此处指患者治疗有效比例，应为“有效率”。",
    "改为“总体有效率为61%”")

add("Ch14", 111, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "...it is likely that a higher response is possible...",
    "...可能会获得更高的响应...",
    "“响应”用在医学统计中不够规范，“反应率”或“有效率”更标准。",
    "改为“可能会获得更高的反应率”")

add("Ch14", 120, "一.双语忠实度", "1.4 错译", "critical", "high",
    "...a higher treatment density (more lines)...",
    "...在更高的治疗密度（更多疗程）...",
    "“lines”指治疗线数量（密度），并非“疗程”（treatment sessions）。二者临床概念完全不同。",
    "改为“在更高的治疗密度（更多治疗线数）”")

add("Ch14", 120, "二.表达规范", "2.20 长句拆分", "medium", "high",
    "In the largest Ulthera sponsored study with qualitative and quantitative imaging assessment, 58% of 93 patients...",
    "在Ulthera赞助的、最大规模，通过定性和定量影像学评估的研究中，16 经设盲评审者判定，93例患者中有58%在3个月后皮肤松弛得到改善。",
    "句首定语堆叠（赞助的、最大规模、通过...评估的）造成阅读障碍。",
    "改为“在Ulthera赞助的最大规模研究（采用定性和定量影像学评估）中，16 经设盲评审者判定...”")

add("Ch14", 123, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "Although no skin tightening procedure can claim permanent results...",
    "尽管没有任何皮肤紧致程序能声称永久效果...",
    "“程序”在中文中主要指软件程序或操作步骤，医学语境中procedure应译为“治疗”或“术式”。",
    "改为“尽管没有任何皮肤紧致治疗能声称永久效果”")

# === Ch15 治疗方案变更 ===
add("Ch15", 132, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "Brow elevation can be achieved with neuromodulators and injectable fillers",
    "眉部提升可通过神经调节剂和注射填充材料实现。",
    "“注射填充材料”偏重材料本身，医学美容术语应为“注射填充剂”。",
    "改为“眉部提升可通过神经调节剂和注射填充剂实现”")

add("Ch15", 133, "一.双语忠实度", "1.1 完整性", "medium", "high",
    "Facial and neck skin tightening can also be achieved by a variety of energy devices, including RF; Injectable fillers and fat grafts can result in mid and lower face elevation",
    "面部和颈部皮肤紧致也可以通过多种能量设备实现，包括射频注射填充材料和脂肪移植，可导致中下面部提升",
    "原文为两个独立句子（分号分隔），译文将其合并导致“注射填充材料和脂肪移植”被误归类为“能量设备”的子项。",
    "改为“面部和颈部皮肤紧致也可以通过多种能量设备实现，包括RF；注射填充剂和脂肪移植可实现中下面部提升”")

add("Ch15", 128, "二.表达规范", "2.17 句式直译", "low", "medium",
    "Because not all patients may not respond to treatments, there is room for increasing the treatment line density.",
    "由于并非所有患者都可能对治疗产生反应，因此存在增加治疗线密度的空间。",
    "原文存在双重否定（not all...may not），译文纠正为单次否定是正确的处理。但“存在...空间”为英文“there is room for”的直译。",
    "改为“正因并非所有患者都会对治疗产生反应，因此可以适当增加治疗线密度”")

# === Ch16 摘要 ===
add(“Ch16”, 141, “四.术语合规”, “4.3 跨段术语统一”, “low”, “medium”,
    “...minimal down time (in Ch5 as very short recovery; here short recovery time)”,
    “MFU是一种非侵入性面部皮肤紧致技术，恢复时间短...”,
    “同一概念 minimal down time 在文中出现三次：Ch5译作 恢复期极短、Ch13译作 无恢复期、此处译作 恢复时间短，译法不统一。”,
    “建议全文统一为 恢复期极短 或 几乎无恢复期”)

# Write output
with open('cache/issues_phase4_new.json', 'w', encoding='utf-8') as f:
    json.dump(I, f, ensure_ascii=False, indent=2)

print(f'Written {len(I)} issues')
sevs = {}
for i in I:
    sevs[i['severity']] = sevs.get(i['severity'], 0) + 1
print(f'Severity: {sevs}')
