#!/usr/bin/env python3
"""Apply new Phase 4 checklist (v2.1) to proofread/1 document"""
import json

issues = []

def add(chapter, pi, dim, check_item, sev, conf, src, tgt, issue_text, suggestion):
    issues.append({
        "chapter": chapter, "paragraph_index": pi,
        "dimension": dim, "check_item": check_item,
        "severity": sev, "confidence": conf,
        "source_quote": src, "target_quote": tgt,
        "issue": issue_text, "suggestion": suggestion
    })

# ===== ROUND 1: FIDELITY + NUMBERS + TERMINOLOGY =====

# --- P10: "看不到改善" is colloquial ---
add("Ch1", 10, "二.表达规范", "2.4 口语化vs书面语", "medium", "high",
    "Based on individual patient response... some patients may not see improvement.",
    "部分患者治疗后可能看不到改善。",
    "「看不到改善」过于口语化，医学文献标准表述为「无明显改善」或「未观察到改善」。",
    "改为：「部分患者治疗后可能无明显改善。」")

# --- P16: Paragraph-level issues beyond the double-对 ---
add("Ch1", 16, "二.表达规范", "2.5 褒贬色彩", "medium", "high",
    "The continued patient demand... leading to increased use of...",
    "患者对对非手术、恢复期极短的面部年轻化治疗的持续需求，导致注射用神经毒素和填充剂...的应用日益增多。",
    "「导致」在中文中带贬义色彩（导致问题/事故），此处原文为中性因果关系，应使用「推动」「促使」或「使得」。",
    "「导致」改为「推动了」。同时「对对」→「对」（衍文）。")

add("Ch1", 16, "二.表达规范", "2.6 近义词混淆", "medium", "medium",
    "can all be part of an overall treatment plan for tightening skin and even lifting facial structures",
    "都可以成为整体治疗方案的一部分，用于紧致皮肤甚至提升面部结构。",
    "「都可以」过于口语化，学术文献应用「均可」；「用于」措辞较弱，「以促进/以实现」更佳；「甚至」→「乃至」更正式。",
    "改为：「均可作为整体治疗方案的一部分，以促进皮肤紧致乃至面部结构提升。」")

add("Ch1", 16, "二.表达规范", "2.14 「的」字堆砌", "medium", "low",
    "", "患者对对非手术、恢复期极短的面部年轻化治疗的持续需求...",
    "前半句含三个「的」字形成长定语链（XX的XX的XX的XX），中文医学文献应避免此类嵌套结构。",
    "建议拆分或简化，如：「患者对非手术、恢复期极短的面部年轻化治疗的需求持续增长，推动了…」")

# --- P19: Already caught but the "当…时" redundancy is separate ---
add("Ch1", 19, "二.表达规范", "2.12 「当…时」冗余", "medium", "high",
    "When collagen is exposed to 60C to 65C, it becomes denatured.",
    "当胶原蛋白暴露于60℃至65℃时，它会变性。",
    "中文「当…时」结构在此处冗余，直接陈述更自然。此为典型英文「When X, Y」结构的翻译惯性。",
    "改为：「胶原蛋白暴露于60℃至65℃时会发生变性。」删「当」和「它会」。")

# --- P22: Multiple expression issues ---
add("Ch1", 22, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "Higher ultrasound frequencies have a greater effect on more superficial tissues...",
    "较高的超声频率对表浅组织影响更大...",
    "「表浅」词序错误，医学标准术语为「浅表」；「影响」带贬义（负面影响），应为「作用」（中性描述物理效应）。",
    "改为：「较高的超声频率对浅表组织作用更强，较低的频率则对深层组织作用更强。」")

add("Ch1", 22, "二.表达规范", "2.15 「使」字冗余", "medium", "medium",
    "leaving the surrounding tissue unaffected",
    "同时使周围组织不受影响。",
    "「使」字是英文 causative 结构的翻译惯性，中文直接陈述即可。此为翻译腔高发信号。",
    "改为：「同时周围组织不受影响。」（删「使」字）")

add("Ch1", 22, "二.表达规范", "2.8 修饰语-名词搭配", "medium", "medium",
    "creating well-defined thermal injury zones at predetermined depths",
    "在预定深度形成界限清晰的热损伤区域",
    "「界限清晰」不如「边界清晰」自然（「界限」偏抽象如道德界限，「边界」偏物理）。「热损伤区域」术语全文应统一。",
    "改为：「在预定深度形成边界清晰的热损伤区」")

add("Ch1", 22, "二.表达规范", "2.16 句首介词冗余-翻译腔", "medium", "medium",
    "At the resulting tissue temperatures, collagen contraction and denaturation occur...",
    "在由此产生的组织温度下，会出现胶原收缩和变性...",
    "「在…下」是英文「At/Under X」的直译结构。中文重组为话题-述题更自然。",
    "改为：「组织达到相应温度后，会出现胶原蛋白收缩和变性，并刺激新胶原蛋白生成。」")

add("Ch1", 22, "四.术语合规", "4.3 跨段术语统一", "critical", "high",
    "", "…并刺激新胶原生成。（P22）vs 胶原蛋白变性…（P18）",
    "P18 标题使用「胶原蛋白」，P22 末句用「胶原」和「新胶原生成」——同一概念在全文中混用「胶原」和「胶原蛋白」两种写法。",
    "统一为「胶原蛋白」。P22 末句改为「…并刺激新胶原蛋白生成。」")

# --- P23: Multiple expression issues ---
add("Ch1", 23, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "MFU differs from RF energy in that it can be micro-focused to target deeper layers without affecting more superficial tissues.",
    "MFU与RF能量的不同之处在于，它可以微聚焦以靶向更深层组织，而不影响更浅层组织。",
    "「不同之处在于，它可以」措辞冗余。「不影响」中「影响」带消极色彩，应用「损伤」或「伤及」更准确。",
    "改为：「MFU与RF能量不同，其能量可微聚焦至更深层组织，而不损伤浅表组织。」")

add("Ch1", 23, "二.表达规范", "2.16 「对于」句首冗余", "medium", "medium",
    "For RF devices, surface cooling is needed to protect the skin to achieve high temperatures.",
    "对于RF设备，要达到高温，需要表面冷却以保护皮肤。",
    "「对于」是英文「For X」的直译，中文可以省略。这也是翻译腔的典型信号。",
    "改为：「RF设备要达到高温，则需要表面冷却以保护皮肤。」")

# --- P26: Translation artifacts ---
add("Ch1", 26, "二.表达规范", "2.2 标点体系", "medium", "high",
    "Ulthera System (Ultherapy) was FDA approved in 2009...",
    "Ulthera系统(Ultherapy)于2009年获得美国食品药品管理局批准...",
    "中文文本中出现英文半角括号 (Ultherapy)，应使用中文全角括号。同段还有一处相同问题。",
    "改为：「Ulthera系统（Ultherapy）于2009年…」")

add("Ch1", 26, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "but is commonly used for full face and submental treatment",
    "但通常用于全面部和颏下治疗。",
    "「通常用于」（usually used）与原文 commonly/routinely used 有微妙偏差。医学文献中「常规用于」更准确传达 'routine clinical use' 含义。",
    "改为：「但目前常规用于全面部和颏下治疗。」")

add("Ch1", 26, "二.表达规范", "2.7 动词-宾语搭配", "medium", "medium",
    "Depending on device settings, targeted tissues can be set at different depths:",
    "根据设备设置，目标组织可设定为不同深度：",
    "「目标组织可设定为不同深度」搭配不当——组织不能「设定为」深度，是治疗深度可调整。",
    "改为：「通过调整设备设置，可设定以下不同靶组织作用深度：」")

# --- P29: Bracket sinicization ---
add("Ch1", 29, "二.表达规范", "2.2 标点体系", "low", "high",
    "targeting the superficial musculoaponeurotic system (SMAS) and platysma",
    "4.5mm，靶向浅表肌肉腱膜系统(SMAS)和颈阔肌",
    "英文半角括号 (SMAS) 应用于中文时需改为中文全角括号。本文多处存在此问题（P26、P29、P136 等）。",
    "改为：「4.5mm，靶向浅表肌肉腱膜系统（SMAS）和颈阔肌」")

# --- P31: Major translation artifact paragraph ---
add("Ch1", 31, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "the monitor allows visualization of where energy is being delivered",
    "监视器允许直观显示能量传递的位置",
    "「允许」是英文 'allows' 的直译（允许=permit）。中文应使用「可」表示能力/功能。这是最常见的翻译腔信号之一。",
    "改为：「监视器可直观显示能量传递的位置」")

add("Ch1", 31, "二.表达规范", "2.6 近义词混淆", "medium", "medium",
    "thus avoiding specific structures such as bone",
    "从而避免骨骼等特定结构",
    "「避免」用于行为（avoid doing），此处指空间上避开物体，应使用「避开」。",
    "改为：「从而避开骨骼等特定结构」")

add("Ch1", 31, "二.表达规范", "2.19 单读测试-不通顺", "critical", "high",
    "Predetermined 'lines' of focused energy delivery result in discrete spacing between 1 mm³ zones of coagulation, which facilitates healing.",
    "预定的"线"状聚焦能量传递，导致在1 mm3凝固区之间产生离散间隔，从而促进愈合。",
    "整句翻译腔严重，几乎不可读。「预定的线状聚焦能量传递」是英文名词短语直译，中文无法自然理解；「导致…产生离散间隔」搭配生硬。此为第一轮校对中完全遗漏的严重问题。",
    "改为：「能量沿预设治疗线聚焦输出，形成多个独立的1 mm³凝固区，各区之间留有间隙，利于愈合。」")

add("Ch1", 31, "二.表达规范", "2.5 褒贬色彩", "medium", "medium",
    "result in discrete spacing between...",
    "导致在1 mm3凝固区之间产生离散间隔",
    "「导致」带贬义（导致事故/问题），此处描述的是设计性结果，应用中性措辞如「形成」「产生」。",
    "同上条合并修复。")

# --- P34: Translation artifact ---
add("Ch1", 34, "二.表达规范", "2.17 「尽管…但」结构直译", "medium", "high",
    "Although the currently approved indications are listed below, other facial and nonfacial areas have also been treated:",
    "尽管目前批准的适应症如下所列，但其他面部及非面部区域也已接受治疗：",
    "「尽管…但」是英文 'Although X, Y' 的直译结构。中文可省略此让步结构，直接陈述更清晰。",
    "改为：「以下为目前获批的适应症，此外还在其他面部及非面部区域开展了治疗应用：」")

# --- P40: Multiple issues ---
add("Ch1", 40, "一.双语忠实度", "1.4 错译-句式混乱", "critical", "high",
    "An early Ulthera prototype device was used on the lateral cheek area of patients who were to undergo surgical rhytidectomy within 12 weeks of treatment.",
    "一款早期Ulthera原型设备被用于患者治疗12周内将接受手术除皱术的患者的面颊外侧区域。",
    "句子结构严重混乱：「患者治疗12周内将接受手术除皱术的患者」——两个「患者」嵌套、时间状语位置错误。原文含义：患者在治疗后12周内将接受除皱手术 → 设备用于这些患者的面颊外侧。",
    "改为：「早期Ulthera原型设备被用于患者面颊外侧区域，这些患者将在治疗后的12周内接受外科除皱手术。」")

add("Ch1", 40, "二.表达规范", "2.13 被动语态直译", "medium", "medium",
    "An early Ulthera prototype device was used on...",
    "一款早期Ulthera原型设备被用于...",
    "「被用于」是被动直译，但此处中文可接受。主要问题是句式结构（见上条）。",
    "与上条合并。")

# --- P56: Translation artifacts ---
add("Ch1", 56, "二.表达规范", "2.7 动词-宾语搭配", "medium", "medium",
    "measured outcomes at 90 days",
    "测量了90天时的结局",
    "「测量…结局」搭配不当。临床试验中 outcomes 应译为「结局指标」或「结果」，「测量」更适合搭配具体数值。",
    "建议改为：「评估了90天时的治疗结果」或句式重组为「在90天时进行了评估」")

add("Ch1", 56, "二.表达规范", "2.14 「的」字堆砌", "medium", "medium",
    "30 of 35 patients (86%) had clinically significant improvement in brow elevation",
    "35例患者中有30例（86%）的眉部提升在临床上获得显著改善",
    "「35例患者中有30例（86%）的眉部提升」——「的」字导致长定语堆叠，读起来费力。",
    "改为：「35例患者中30例（86%）眉部提升获得临床上显著改善」或「35例患者中有30例（86%）眉部提升获得临床上显著改善」")

# --- P59: Word choice ---
add("Ch1", 59, "二.表达规范", "2.5 褒贬色彩", "medium", "high",
    "Owing to the brow lift, improvements of the upper eyelid can be seen...",
    "由于眉部提升，前额和眉部治疗后可以看到上眼睑的改善。",
    "「由于」是中性因果连词，但此处眉部提升带来了正面效果，「得益于」更准确地传达这种积极的因果关系。",
    "改为：「得益于眉部提升，前额和眉部治疗后可以看到上眼睑的改善。」")

# --- P63: Sentence structure ---
add("Ch1", 63, "二.表达规范", "2.20 长句拆分", "medium", "medium",
    "A prospective, blinded evaluation study of 22 patients assessed the nasolabial folds and jawline...",
    "一项前瞻性、盲法评估研究，纳入22例患者，使用7.5MHz和4.4MHz手柄...评估了鼻唇沟和下颌线。",
    "句式零散——「一项…研究，纳入…患者，使用…，评估了…」，逗号连接过多独立信息，建议重组为主从结构。",
    "改为：「一项纳入22例患者的前瞻性、评估者设盲研究，使用7.5MHz和4.4MHz手柄…评估了鼻唇沟和下颌线的治疗效果。」")

add("Ch1", 63, "二.表达规范", "2.6 近义词混淆", "medium", "low",
    "delivered energy via linear arrays at 3 mm parallel intervals",
    "以3 mm平行间隔的线阵将能量递送至...",
    "「递送」用于能量不够自然，医学文献中「传递」是更通用的搭配。",
    "改为：「以3 mm平行间隔的线阵将能量传递至…」")

# --- P70: Already caught (missing 个) ---

# --- P73: Terminology consistency ---
add("Ch1", 73, "四.术语合规", "4.3 跨段术语统一", "critical", "high",
    "", "...SMAS中出现热损伤区域...（P73）vs ...热损伤区...",
    "P73 使用「热损伤区域」，与前文（如 P22 建议改为「热损伤区」）不一致。全文需统一术语。",
    "统一为「热损伤区」。")

# --- P76: Multiple issues ---
add("Ch1", 76, "二.表达规范", "2.7 动词-宾语搭配", "medium", "high",
    "Standardized blinded assessments and patient satisfaction were measured.",
    "测量了标准化的设盲评估和患者满意度。",
    "「测量…评估和满意度」搭配不当——「评估」和「满意度」不能用「测量」，应使用「记录」或「评估」。此为翻译腔中典型的动词泛化（英文 measured 不只对应 测量）。",
    "改为：「记录了标准化的设盲评估结果和患者满意度。」或「进行了标准化的设盲评估和患者满意度调查。」")

add("Ch1", 76, "二.表达规范", "2.4 口语化vs书面语", "medium", "medium",
    "Focal depth",
    "焦深",
    "「焦深」过于简略，医学文献中规范表述为「聚焦深度」。",
    "改为：「聚焦深度」")

add("Ch1", 76, "二.表达规范", "2.15 「使」字冗余", "low", "low",
    "Improved treatment protocols and patient selection may lead to better results.",
    "改进的治疗方案和患者筛选可能会带来更好的结果。",
    "此处翻译基本可接受。「改进的」→「优化的」会更符合医学文献习惯。",
    "建议：「优化的治疗方案和更严格的患者筛选可能会带来更好的结果。」")

# --- P79: Serious mistranslation (already caught) ---

# --- P93: IMPORTANT missed mistranslation ---
add("Ch1", 93, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "Distraction techniques",
    "分心技术",
    "「分心技术」为严重错译（分心=distracted, negative）。医学/心理学术语 'distraction techniques' 标准译法为「分散注意力技术」。第一轮校对完全遗漏。",
    "改为：「分散注意力技术」")

# --- P98-P99: Conjunction precision ---
add("Ch1", 98, "二.表达规范", "2.9 介词/连词选用", "medium", "high",
    "800 mg ibuprofen with 10 mg hydrocodone/500 mg acetaminophen",
    "在治疗前60分钟给予800mg布洛芬与10mg氢可酮/500mg对乙酰氨基酚",
    "「与」在此语境可能被误解为联合用药（ibuprofen + hydrocodone together）。原文 'with' 可能表示两组对照（ibuprofen vs hydrocodone/acetaminophen）。临床试验语境中应使用「或」以明确表示分组比较。",
    "改为：「在治疗前60分钟给予800mg布洛芬或10mg氢可酮/500mg对乙酰氨基酚」")

add("Ch1", 99, "二.表达规范", "2.9 介词/连词选用", "medium", "high",
    "Topical liposomal lidocaine with placebo control",
    "局部用脂质体利多卡因与安慰剂对照在疼痛缓解方面无差异",
    "同上，临床试验对照语境中 'with' →「或」或「对比」，不应译为「与」。",
    "改为：「局部用脂质体利多卡因或安慰剂对照在疼痛缓解方面无差异」")

# --- P103: Terminology ---
add("Ch1", 103, "二.表达规范", "2.4 口语化vs书面语", "medium", "high",
    "Recovery and Downtime",
    "恢复与停机时间",
    "「停机时间」为机器/设备用语，医学文献中 'downtime' 应译为「停工期」或「恢复期」。「恢复」也应加「期」与「停工期」并列。",
    "改为：「恢复期与停工期」")

# --- P104: Expression ---
add("Ch1", 104, "二.表达规范", "2.6 近义词混淆", "medium", "medium",
    "can be considered to have no recovery period and minimal downtime",
    "Ulthera系统可被视为无恢复期且恢复时间极短。",
    "「可被视为」翻译腔明显（can be considered → 可被视为）。「无恢复期」是误译——原文是 'no recovery period' 指无需专门恢复期/不会导致停工，而非字面意义的没有恢复期。",
    "改为：「Ulthera系统不会导致停工，且恢复时间极短。」")

# --- P107: Accumulated minor issues ---
add("Ch1", 107, "二.表达规范", "2.9 介词/连词选用", "low", "medium",
    "usually mild erythema and edema, which typically resolve after 2 days but no longer than 7 days",
    "通常是轻度红斑和水肿，通常在2天后消退，但不超过7天",
    "「通常…通常」重复。'resolve after 2 days but no longer than 7 days' →「通常在2天后消退，最长不超过7天」更精确传达 'no longer than'。",
    "改为：「通常是轻度红斑和水肿，一般在2天后消退，最长不超过7天。」")

add("Ch1", 107, "二.表达规范", "2.6 近义词混淆", "low", "medium",
    "A literature review focusing on the safety profile of MFU...",
    "一篇聚焦于MFU安全性的文献综述证实...",
    "「聚焦于」略生硬，学术文献多用「关注」「针对」。",
    "改为：「一篇关注MFU安全性的文献综述证实…」")

# --- P110: Translation artifacts ---
add("Ch1", 110, "二.表达规范", "2.6 近义词混淆", "medium", "medium",
    "candidates who present with mild to moderate aging",
    "由于理想候选人通常呈现轻度至中度衰老",
    "「候选人」在美容医学语境中应为「适应证患者」或「适合治疗的患者」。「呈现…衰老」应为「表现为轻度至中度皮肤老化」。",
    "改为：「由于适合治疗的患者通常表现为轻度至中度皮肤老化」")

add("Ch1", 110, "二.表达规范", "2.7 动词-宾语搭配", "medium", "medium",
    "Additionally, mild edema contributes to the early aesthetic improvement seen by patients.",
    "还有轻度水肿有助于患者看到的早期美学改善。",
    "句式破碎——「还有」过于口语化，「有助于患者看到的」缺少连接成分。",
    "改为：「此外，轻度水肿也有助于患者所见的早期美学改善。」或「此外，轻度水肿也参与了患者所见的早期美学改善。」")

# --- P111: Multiple ---
add("Ch1", 111, "二.表达规范", "2.6 近义词混淆", "medium", "medium",
    "higher response might have been obtained with a more aggressive treatment protocol",
    "如果采用更激进的治疗方案，可能会获得更高的响应。",
    "「响应」在此语境不准确——'response' 应为「反应率」或「有效率」。「激进」带有不必要的军事化色彩，可用「强化」或「高密度」。",
    "改为：「如果采用更高密度的治疗方案，可能会获得更高的反应率。」")

add("Ch1", 111, "二.表达规范", "2.6 近义词混淆", "low", "low",
    "the group that included mandibular treatment had lower satisfaction scores",
    "包括下颌治疗的那组满意度评分较低。",
    "「那组」口语化。学术文献应使用「患者组」或「治疗组」。",
    "改为：「接受下颌治疗的患者组满意度评分较低。」")

# --- P119-P120: Multiple issues ---
add("Ch1", 119, "二.表达规范", "2.6 近义词混淆", "medium", "medium",
    "Older patients with lower 'healing potential' may not respond as well as younger patients.",
    "老年患者"愈合潜力"较低，可能不如年轻患者反应良好。",
    "「愈合潜力」译自 'healing potential'——中文「潜力」指未来发展的可能性，而此处指机体实际的修复能力，应译为「愈合能力」。引号也应改为中文引号。",
    "改为：「老年患者"愈合能力"较低，治疗效果可能不如较为年轻的患者。」")

add("Ch1", 120, "一.双语忠实度", "1.9 情态误译", "medium", "medium",
    "higher treatment densities (more treatment lines) and assessment at 6 to 9 months may have shown a more favorable response",
    "在更高的治疗密度（更多疗程）和6至9个月时的评估下，可能会显示出更有利的反应。",
    "「更多疗程」错译——原文 'more treatment lines' 指更多治疗线数，非治疗疗程（sessions）。「可能会显示出」措辞冗余，「可能会」和「显示出」可简化为「可能获得」。",
    "改为：「若采用更高的治疗密度（更多治疗线）并在6至9个月时进行评估，可能获得更有利的治疗反应率。」")

add("Ch1", 119, "二.表达规范", "2.20 长句拆分", "medium", "medium",
    "treatment protocols, delivered energy doses, and individual patient factors make generalizations about expected results difficult",
    "治疗方案、传递的能量剂量以及患者个体因素使得对预期结果进行概括变得困难。",
    "「使得对预期结果进行概括变得困难」是英文 'make X difficult' 的直译结构，中文可简化。",
    "改为：「…患者个体因素各不相同，因此难以对预期结果进行统一概括。」")

# --- P120: Unit error (already caught) ---

# --- P123: Terminology ---
add("Ch1", 123, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "no skin tightening procedure can claim permanent results",
    "尽管没有任何皮肤紧致程序能声称永久效果",
    "「程序」在此语境不通——'procedure' 指医疗/美容治疗，应译为「治疗」或「疗法」。「声称」带贬义（claim falsely），中性译法为「宣称」或「保证」。",
    "改为：「尽管没有任何皮肤紧致治疗能保证永久效果」")

add("Ch1", 123, "二.表达规范", "2.6 近义词混淆", "low", "medium",
    "energy-source skin tightening devices",
    "能量源皮肤紧致设备",
    "「能量源设备」搭配生硬，医学文献常用「能量类设备」或「能量型设备」。",
    "改为：「能量类皮肤紧致设备的长期疗效仍缺乏数据支持。」")

# --- P126: Translation precision ---
add("Ch1", 126, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "specific supervision requirements regarding patient evaluation and physician availability vary by local regulation",
    "关于患者评估和医生可用性的监督具体要求因当地法规而异。",
    "「医生可用性」译自 'physician availability'——中文「可用性」偏重物品/系统的 availability，指人的到场/在岗应用「在场」或「可及性」。",
    "改为：「关于患者评估和医生在场的具体监督要求因当地法规而异。」")

# --- P127: Terminology ---
add("Ch1", 127, "二.表达规范", "2.6 近义词混淆", "medium", "medium",
    "Treatment Protocol Variations",
    "治疗方案变更",
    "「变更」指改变/修改（change），原文 'variations' 指不同方案之间的差异/变化，应译为「差异性」或「多样化」。",
    "改为：「治疗方案差异性」")

# --- P128: Collocation ---
add("Ch1", 128, "二.表达规范", "2.8 修饰语-名词搭配", "medium", "medium",
    "experienced Ulthera user consensus group participants report significant efficacy when using 600 to 800 lines per treatment",
    "经验丰富的Ulthera用户共识组参与者报告称，每次治疗使用600至800条线时，疗效显著。",
    "「疗效显著」作为「报告称」的宾语从句不够紧凑。「条线」→「条治疗线」更清晰。",
    "改为：「…每次治疗使用600至800条治疗线时可获得较高的疗效。」")

add("Ch1", 128, "二.表达规范", "2.6 近义词混淆", "low", "low",
    "Treatment densities up to 1500 lines have been used...",
    "已使用高达1500线的治疗密度",
    "「已使用高达1500线的治疗密度」语序应为「治疗密度已使用高达1500线」或重组。",
    "改为：「已有研究使用高达1500条治疗线的治疗密度」")

# --- P133-P138: Combined paragraph split issue ---
add("Ch1", 133, "五.格式排版", "5.1 段落拆分", "low", "high",
    "Facial and neck skin tightening can also be achieved with a variety of energy devices, including RF. Injectable fillers and fat grafting can result in mid and lower face lifting...",
    "面部和颈部皮肤紧致也可以通过多种能量设备实现，包括射频注射填充材料和脂肪移植，可导致中下面部提升",
    "原文两个独立句子被合并为一个段落。「包括射频」后应分段——射频是能量设备类别，注射填充材料/脂肪移植是另一类别。此外「导致…提升」搭配不当（导致负面结果）。",
    "建议拆分为两段，并将「可导致中下面部提升」改为「可使中下面部获得提升」。")

# --- P140-P141: Summary paragraph ---
add("Ch1", 141, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "with little recovery time",
    "恢复时间短",
    "「恢复时间短」之前全文改译为「停工时间极短」。「摘要」→「总结」更符合中文医学论文习惯。",
    "P140 标题「摘要」改为「总结」；P141「恢复时间短」改为「停工时间极短」以保持全文术语一致。")

add("Ch1", 141, "二.表达规范", "2.7 动词-宾语搭配", "medium", "medium",
    "can complement other noninvasive treatments",
    "可作为其他非侵入性治疗的补充",
    "「可作为…补充」缺少动词宾语标记，加「手段」或「方法」更完整。",
    "建议：「可作为其他非侵入性治疗手段的补充」")

# ===== OUTPUT =====
output = {
    "issues": issues,
    "summary": {
        "total_issues": len(issues),
        "by_severity": {
            "critical": sum(1 for i in issues if i["severity"] == "critical"),
            "medium": sum(1 for i in issues if i["severity"] == "medium"),
            "low": sum(1 for i in issues if i["severity"] == "low")
        },
        "by_dimension": {}
    }
}

for i in issues:
    dim = i["dimension"]
    output["summary"]["by_dimension"][dim] = output["summary"]["by_dimension"].get(dim, 0) + 1

with open("d:/translation/cache/issues_phase4_v2_1.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Total issues: {len(issues)}")
print(f"By severity: {output['summary']['by_severity']}")
print(f"By dimension: {output['summary']['by_dimension']}")
print(f"Original v2.0 had: 9 issues")
print(f"Improvement: {len(issues)} vs 9 = {len(issues)/9:.1f}x")
