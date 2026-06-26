#!/usr/bin/env python3
"""
Phase 4: 逐章校对 — 生成 issues JSON
Agent 逐段执行六维度检查（两轮协议），记录所有疑点。
"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

issues = []

def add(pi, dim, check_item, sev, conf, src, tgt, issue_text, suggestion):
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

# ═══════════════════════════════════════════════════════════
# Ch5 引言
# ═══════════════════════════════════════════════════════════
# P16 — typo + expression issues
add(16, "二.表达规范", "2.1 错别字/衍文", "medium", "high",
    "The continued patient demand for nonsurgical and minimal downtime facial rejuvenation...",
    "患者对对非手术、恢复期极短的面部年轻化治疗的持续需求",
    "「对对」为重复字衍文，应为「对」。此为文本输入错误。",
    "改为：「患者对非手术、恢复期极短的面部年轻化治疗的持续需求」")

add(16, "二.表达规范", "2.15 使/让/令冗余", "medium", "medium",
    "...has resulted in more use of injectable neurotoxins and fillers...",
    "患者对对非手术、恢复期极短的面部年轻化治疗的持续需求，导致注射用神经毒素和填充剂…的应用日益增多",
    "「导致…应用日益增多」句式欧化。中文更自然表述为「使得…应用日益增多」或重组语序：「…持续需求推动了注射用神经毒素…的广泛应用」。",
    "建议：「…持续需求推动了注射用神经毒素和填充剂、皮肤换肤术及紧致治疗的广泛应用。」")

# ═══════════════════════════════════════════════════════════
# Ch6 胶原蛋白变性与新胶原生成
# ═══════════════════════════════════════════════════════════
# P19 — 口语化 + 术语不一致
add(19, "二.表达规范", "2.4 口语化vs书面语", "medium", "high",
    "When collagen is exposed to 60°C to 65°C, it becomes denatured.",
    "当胶原蛋白暴露于60℃至65℃时，它会变性。",
    "「它会变性」口语化。医学文献中应为「会发生变性」或「胶原蛋白即发生变性」。「它」字指代在中文医学文献中不自然。",
    "改为：「当胶原蛋白暴露于60℃至65℃时，即发生变性。」或「…时会发生变性。」")

add(19, "四.术语合规", "4.3 跨段术语统一", "critical", "high",
    "neocollagenesis → Chapter title",
    "章节标题「胶原蛋白变性与新胶原生成」vs 本章正文「新的胶原蛋白合成」vs P22「新胶原生成」",
    "同一概念「neocollagenesis」在全文中混用「新胶原生成」「新的胶原蛋白合成」「新胶原蛋白生成」。此为学术论文核心术语，必须统一。章节标题尤其应使用完整术语。",
    "统一为：「新胶原蛋白合成」（带「蛋白」的全称）。标题改为「胶原蛋白变性与新胶原蛋白合成」。")

# ═══════════════════════════════════════════════════════════
# Ch7 作用机制
# ═══════════════════════════════════════════════════════════
# P22 — 术语 + 翻译腔
add(22, "二.表达规范", "2.6 近义词混淆", "medium", "high",
    "Higher ultrasound frequencies have more superficial tissue effects...",
    "较高的超声频率对表浅组织影响更大",
    "「表浅组织」在医学中文中的标准表述为「浅表组织」。「表浅」非标准医学术语。反义词对：表浅/浅表。",
    "改为：「较高的超声频率对浅表组织影响更大」")

add(22, "二.表达规范", "2.15 使/让/令冗余", "medium", "high",
    "...leaving the surrounding tissue unaffected.",
    "…同时使周围组织不受影响。",
    "「使」字为英文 'leaving X unaffected' 的直译痕迹。删掉「使」字，中文反而更通顺：「…同时周围组织不受影响。」",
    "改为：「…在预定深度形成界限清晰的热损伤区域，同时周围组织不受影响。」")

add(22, "二.表达规范", "2.4 口语化vs书面语", "medium", "medium",
    "At the resulting tissue temperatures, collagen contraction, and denaturation is seen and neocollagenesis is stimulated.",
    "在由此产生的组织温度下，会出现胶原收缩和变性，并刺激新胶原生成。",
    "「会出现…并刺激」为口语化表达。学术文献中应用「可见…并」或「发生…进而」。",
    "建议：「在该组织温度下，可见胶原收缩与变性，进而刺激新胶原蛋白合成。」")

# P23 — MT术语泛化 + 翻译腔
add(23, "二.表达规范", "2.23 MT术语泛化", "medium", "high",
    "MFU is different from RF energy in that it can be microfocused to target deeper tissue without affecting more superficial tissue.",
    "MFU与RF能量的不同之处在于，它可以微聚焦以靶向更深层组织，而不影响更浅层组织。",
    "「靶向」为 MT 直译（target → 靶向）。医学文献中更自然的表述为「作用于」或「针对」。注意：部分学术语境下「靶向」可接受，但此句为非靶向治疗语境，建议改为更通用表述。",
    "建议：「…其能量可微聚焦至更深层组织，作用于深层而不影响浅层。」")

add(23, "二.表达规范", "2.16 对于/关于句首冗余", "medium", "medium",
    "For an RF device to achieve high temperatures, surface cooling is needed to protect the skin.",
    "对于RF设备，要达到高温，需要表面冷却以保护皮肤。",
    "「对于」句首为英文 'For X, Y' 的直译。中文可省略「对于」：'RF设备要达到高温，则需要表面冷却以保护皮肤。'",
    "改为：「RF设备要达到高温，则需要表面冷却以保护皮肤。」")

# ═══════════════════════════════════════════════════════════
# Ch8 ULTHERA微聚焦超声系统
# ═══════════════════════════════════════════════════════════
# P26 — 术语 + 表达
add(26, "二.表达规范", "2.4 口语化vs书面语", "medium", "medium",
    "...is routinely used for panfacial and submental treatments.",
    "…但通常用于全面部和颏下治疗。",
    "「通常用于」将 'routinely used' 译为一般频率描述。原文 'routinely' 在此有「常规用于」之意（已成临床常规），非单纯的「通常」。训练数据中此对近义词反复出现。",
    "改为：「…但现已常规用于全面部和颏下治疗。」")

# P31 — 翻译腔
add(31, "二.表达规范", "2.25 字面直译短语", "medium", "medium",
    "The focal energy delivery in given in predetermined 'lines' results in discrete intervals between 1 mm3 coagulation zones that promote healing.",
    "预定的"线"状聚焦能量传递，导致在1 mm3凝固区之间产生离散间隔，从而促进愈合。",
    "「导致…产生离散间隔」——「导致」在此处搭配不当（含贬义色彩），且'discrete intervals'译为「离散间隔」不够直观。原文描述的是凝固区之间的规则排布促进愈合。",
    "建议：「预定的'线'状聚焦能量传递使1 mm³凝固区之间形成规则间隔，从而促进愈合。」")

# ═══════════════════════════════════════════════════════════
# Ch9 适应症
# ═══════════════════════════════════════════════════════════
# P37 — 翻译错误
add(37, "一.双语忠实度", "1.4 错译", "critical", "high",
    "Improve lines and wrinkles in décolleté",
    "改善肩颈部的细纹和皱纹",
    "「décolleté」指女性颈下/胸前V形区域（法语借词），非一般意义的「肩颈部」。译为「肩颈部」扩大了范围且不够精确。医学美容文献中应译为「前胸/领口区域」或保留 'décolleté' 加注。",
    "改为：「改善前胸（décolleté）区域的细纹和皱纹」")

# ═══════════════════════════════════════════════════════════
# Ch10 组织学研究
# ═══════════════════════════════════════════════════════════
# P40 — 翻译腔 + 表达
add(40, "二.表达规范", "2.24 修饰语位置欧化", "medium", "medium",
    "An early prototype Ulthera device was used on the lateral cheek region in patients who would be undergoing a surgical rhytidectomy within 12 weeks of treatment.",
    "一款早期Ulthera原型设备被用于患者治疗12周内将接受手术除皱术的患者的面颊外侧区域。",
    "语序严重欧化——「患者治疗12周内将接受手术除皱术的患者」定语堆砌且逻辑混乱。中文应重组为「治疗对象为12周内计划接受手术除皱术的患者，在其面颊外侧区域使用…」。",
    "建议重组语序：「治疗对象为计划在12周内接受手术除皱术的患者，在其面颊外侧区域使用了一款早期Ulthera原型设备。」")

add(40, "一.双语忠实度", "1.5 指代", "medium", "medium",
    "Skin histology showed consistent and reproducible thermal injury zones in the dermis, without injury to the epidermis, which was absent by 12 weeks.",
    "皮肤组织学检查显示，真皮出现一致且可重复的热损伤区域，表皮未受损伤，且该损伤在12周时已消失。",
    "「which was absent by 12 weeks」的指代——原文 'which' 指 thermal injury zones（热损伤区在12周时消失），译文「该损伤在12周时已消失」指代正确。但「表皮未受损伤」与「且该损伤在12周时已消失」之间的连接词「且」逻辑不清——前者描述表皮，后者描述热损伤区。",
    "建议：「…真皮出现一致且可重复的热损伤区域（表皮未受损伤），该热损伤区在12周时已消失。」")

add(40, "二.表达规范", "2.4 口语化vs书面语", "medium", "medium",
    "Elastic fibers of the upper and lower dermis were more parallel and straighter.",
    "真皮上部和下部的弹性纤维更加平行和笔直。",
    "「笔直」为口语词，学术文献中应用「平直」或「排列更加平行、有序」。「笔直」常用于口语（如'笔直的路'），在组织学描述中不正式。",
    "改为：「真皮上部和下部的弹性纤维排列更加平行、平直。」")

# ═══════════════════════════════════════════════════════════
# Ch13 具体应用 — 面部与颈部
# ═══════════════════════════════════════════════════════════
# P56 — 术语 + 翻译腔
add(56, "二.表达规范", "2.23 MT术语泛化", "medium", "medium",
    "measured outcomes at 90 days",
    "测量了90天时的结局",
    "「结局」为 'outcomes' 的MT直译。临床试验术语中应为「结局指标」或「治疗结果」。「测量…结局」搭配也不自然。",
    "改为：「评估了90天时的治疗结果」或「测量了90天时的结局指标」")

add(56, "二.表达规范", "2.14 的字堆砌", "medium", "medium",
    "Thirty of 35 patients (86%) had a clinically significant improvement in brow elevation (mean, 1.7 mm).",
    "35例患者中有30例（86%）的眉部提升在临床上获得显著改善（平均提升1.7mm）。",
    "「的」字过多：'35例患者中有30例（86%）的眉部提升在临床上获得显著改善'——该句包含多重定语，可简化。",
    "建议：「35例患者中，30例（86%）眉部提升获得临床上显著改善（平均提升1.7mm）。」删掉两个多余的「的」。")

# P60 — 术语
add(60, "二.表达规范", "2.23 MT术语泛化", "critical", "high",
    "using 1.5 mm and 3.0 mm probes",
    "使用1.5 mm和3.0 mm探头靶向下眼睑皮肤和眶隔后",
    "「探头」为MT直译短词。医疗器械文档中 'probe' 标准译法为「治疗探头」（加领域修饰语）。训练数据中此处修订出现386次。",
    "改为：「…使用1.5 mm和3.0 mm治疗探头…」")

# P63+P70 — 跨段连接问题
add(63, "一.双语忠实度", "1.1 完整性", "critical", "high",
    "Two months after treatment of the face and submental area, all patients demonstrated nasolabial fold and jaw line improvement...",
    "在面部和颏下区域治疗两个  [P70:] 月后，所有患者均显示出鼻唇沟和下颌线的改善",
    "P63段末「治疗两个」与P70段首「月后」之间存在图片插入（图2）导致文字断裂。但原文此段为完整句（'Two months after treatment...'），无断裂。此为排版导致的阅读断裂，非翻译问题，但可标记供人工确认排版意图。",
    "建议人工确认：原文此段为连续段落，图片插入位置是否合理。")

# P73 — 术语
add(73, "四.术语合规", "4.2 段内术语统一", "medium", "medium",
    "SMAS contraction proportional to the amount of energy delivered.",
    "SMAS中出现热损伤区域，且SMAS收缩程度与传递的能量成正比。",
    "段内「SMAS」保留原文，与P29「浅表肌肉腱膜系统(SMAS)」首次出现时不同——首次出现标注了全称，但原文P29不在同一段。P73单独使用「SMAS」无全称前文，对不熟悉该缩写的读者可能不够清晰。",
    "在P73首次出现的段落加注全称：「SMAS（浅表肌肉腱膜系统）」")

# P79 — 翻译腔
add(79, "二.表达规范", "2.17 尽管但结构直译", "medium", "medium",
    "Despite the reported favorable results, the published before and after images show modest improvements.",
    "尽管报道称结果良好，但已发布的术前和术后图像显示改善幅度有限。",
    "「尽管…但」结构完整但稍显翻译腔。中文可简化为「虽然…，…」或直接陈述：「报道结果良好，但…」",
    "可不修改，此为风格偏好。建议：当前译法可接受，但若能简化为「虽报道结果良好，已发布的术前和术后图像却显示改善幅度有限」更简洁。")

# P82 — 翻译腔
add(82, "二.表达规范", "2.16 对于/关于句首冗余", "medium", "low",
    "Chan and colleagues11 reported on 49 Chinese patients...",
    "Chan及其同事11 报告了49例Fitzpatrick皮肤类型为III型和IV型的中国患者",
    "空格在引用编号「11」前面——中文应紧跟前文，不留空格。此问题在多处出现。",
    "全文中引用编号前的空格应统一删除（如「同事11」→「同事¹¹」或按期刊格式调整）。")

# P86 — 表达
add(86, "二.表达规范", "2.4 口语化vs书面语", "medium", "high",
    "One frequent complaint of the Ulthera system is pain during treatment.",
    "Ulthera系统的一个常见抱怨是治疗过程中的疼痛。",
    "「抱怨」为口语词。医学文献中 'complaint' 在患者语境中应译为「主诉」或「不适」。训练数据中此修订出现多次。",
    "改为：「患者对Ulthera系统的一个常见主诉是治疗过程中的疼痛。」")

# P107 — 表达
add(107, "二.表达规范", "2.13 被动语态直译", "medium", "low",
    "A review of the literature focusing on the safety of MFU confirmed that side effects are generally mild and transient in nature.",
    "一篇聚焦于MFU安全性的文献综述证实，副作用通常性质轻微且短暂。",
    "「性质轻微且短暂」——'mild and transient in nature' 的字面直译。中文更自然表述为「副作用通常较为轻微且呈一过性」或「副作用通常轻微且短暂」。「性质」二字冗余。",
    "建议：「…副作用通常轻微且短暂。」")

# ═══════════════════════════════════════════════════════════
# Ch14 结果
# ═══════════════════════════════════════════════════════════
# P110 — MT术语泛化
add(110, "二.表达规范", "2.23 MT术语泛化", "critical", "high",
    "Because ideal candidates tend to have mild to moderate aging...",
    "由于理想候选人通常呈现轻度至中度衰老",
    "「候选人」为 'candidates' 的字面直译。医学美容文献中应译为「适应证患者」或「适合治疗的患者」。",
    "改为：「由于适合治疗的患者通常表现为轻度至中度皮肤老化」")

# P111 — MT术语泛化
add(111, "二.表达规范", "2.23 MT术语泛化", "medium", "high",
    "it is likely that a higher response is possible if more aggressive treatment protocols are used.",
    "如果采用更激进的治疗方案，可能会获得更高的响应。",
    "「响应」为 'response' 的MT直译。临床试验术语中应为「反应率」或「有效率」。",
    "改为：「…可能会获得更高的反应率。」")

# P120 — 错译 (critical!)
add(120, "一.双语忠实度", "1.4 错译", "critical", "high",
    "It is possible that a higher treatment density (more lines) and assessment at 6 to 9 months may have shown more favorable responses.",
    "在更高的治疗密度（更多疗程）和6至9个月时的评估下，可能会显示出更有利的反应。",
    "「更多疗程」为严重错译——原文 'more lines' 指更多治疗线数（treatment lines），非治疗疗程（sessions）。'疗程'（一个疗程含多次治疗）是完全不同的临床概念。",
    "改为：「若采用更高的治疗密度（更多治疗线）并在6至9个月时进行评估，可能获得更有利的治疗反应率。」")

add(120, "一.双语忠实度", "1.4 错译", "critical", "high",
    "body mass index of 30 mg/kg2 or less",
    "体重指数≤30mg/kg2 的患者",
    "BMI单位错译——原文 '30 kg/m²' 在译文中写成 '30mg/kg²'。mg（毫克）vs kg（千克）相差一百万倍，且BMI单位应为 kg/m² 而非 mg/kg²。这是严重的单位错误。",
    "改为：「体重指数≤30 kg/m²的患者」。注意：原文前句 '30 kg/m2' 和后句 '30 mg/kg2' 已有矛盾（应为作者的笔误，但译文应统一为正确单位 kg/m²）。")

# P123 — 翻译腔
add(123, "二.表达规范", "2.23 MT术语泛化", "medium", "medium",
    "energy-derived skin tightening devices",
    "能量源皮肤紧致设备",
    "「能量源设备」为 'energy-derived devices' 的直译。中文更自然表述为「能量类设备」或「能量型设备」。",
    "建议：「…能量类皮肤紧致设备的长期效果仍缺乏数据支持。」")

# P126 — 翻译腔
add(126, "二.表达规范", "2.25 字面直译短语", "medium", "medium",
    "Physicians may administer the treatments themselves, but in most cases, nurses or trained aestheticians provide the service.",
    "医生可以自行实施治疗，但在大多数情况下，由护士或经过培训的美容师提供服务。",
    "「由护士…提供服务」的「服务」为英文 'provide the service' 的字面直译。在医疗语境下，中文更自然表述为「由护士…执行治疗」或「由护士…进行操作」。",
    "改为：「…但在大多数情况下，由护士或经过培训的美容师执行治疗。」")

# ═══════════════════════════════════════════════════════════
# Ch15 治疗方案变更
# ═══════════════════════════════════════════════════════════
# P128 — 翻译腔
add(128, "二.表达规范", "2.12 当时冗余", "medium", "medium",
    "Experienced Ulthera user consensus group participants reported high rates of efficacy when using 600 to 800 lines per treatment.",
    "经验丰富的Ulthera用户共识组参与者报告称，每次治疗使用600至800条线时，疗效显著。",
    "当前句式可接受。但「用户共识组参与者」定语链过长且不自然——'consensus group participants' → 可简化为「专家共识组成员」。",
    "建议：「经验丰富的Ulthera专家共识组成员报告，每次治疗使用600至800条线时疗效显著。」")

# P133 — 缺失标点导致句意混乱
add(133, "一.双语忠实度", "1.1 完整性", "critical", "high",
    "Facial and neck skin tightening can also be achieved by a variety of energy devices, including RF\n\nInjectable fillers and fat grafts can result in mid and lower face elevation",
    "面部和颈部皮肤紧致也可以通过多种能量设备实现，包括射频注射填充材料和脂肪移植，可导致中下面部提升",
    "句子缺少标点分隔——原文是两个独立要点（RF设备、注射填充材料/脂肪移植），译文将二者合并为一句「包括射频注射填充材料和脂肪移植」，将RF设备与注射填充材料混在一起，且句号缺失导致与下句粘连。此为排版错误导致的严重句意混乱。",
    "改为两条独立要点：\n「• 面部和颈部皮肤紧致也可以通过多种能量设备实现，包括RF」\n「• 注射填充材料和脂肪移植可实现中下面部提升」")

# P136 — 标点
add(136, "二.表达规范", "2.2 标点体系", "low", "high",
    "deoxycholic acid (Kybella) injections",
    "注射去氧胆酸(Kybella)来减少",
    "中文括号应使用全角：'去氧胆酸（Kybella）'。当前使用半角括号。",
    "改为：「注射去氧胆酸（Kybella）来减少」")

# ═══════════════════════════════════════════════════════════
# Ch16 摘要
# ═══════════════════════════════════════════════════════════
# P141 — 表达
add(141, "二.表达规范", "2.6 近义词混淆", "medium", "medium",
    "variability in patient response needs to be considered",
    "需考虑患者反应的差异性",
    "「差异性」在统计学语境下合适，但此句指个体患者反应不一。「variability」在此译为「个体差异」或「变异性」比「差异性」更精确。",
    "建议：「需考虑患者反应的个体差异性」或「需考虑患者反应存在的变异性」。")

# ═══════════════════════════════════════════════════════════
# 跨章一致性问题
# ═══════════════════════════════════════════════════════════
# 范围表达一致性
add(0, "三.数字符号单位", "3.2 范围表达", "low", "medium",
    "",
    "全文中混合使用「至」「到」和「-」表示范围：如P9「3到6个月」、P19「60℃至65℃」、P23「60℃到70℃」、P47「30到60分钟」、P56「0.75–1.2J」。",
    "范围表达全文不统一：「至」(P19, P23)、「到」(P9, P23, P47)、「–」(P56)混用。学术论文中建议统一用「至」或「～」。",
    "建议：数值范围统一使用「至」（如「3至6个月」「60℃至65℃」），能量/剂量范围使用「～」（如「0.75～1.2 J」）。")

# ═══════════════════════════════════════════════════════════
# Checks that haven't been covered but I should also flag:
# - 2.25: 字面直译 — additional spots
# - 2.19: 单读测试 — a few more areas
# ═══════════════════════════════════════════════════════════

# Additional expression issues found during Round 2 (单读检查):
# P56 — 的字堆砌
# Already covered above.

# P56 — more issues
add(56, "二.表达规范", "2.19 单读测试", "medium", "high",
    "Ultrasound pulses were administered every 1.5 mm along each treatment line with 3 to 5 mm between treatment lines.",
    "超声脉冲沿每条治疗线每隔1.5mm施加一次，治疗线之间的间距为3至5mm。",
    "单独读译文：「超声脉冲沿每条治疗线每隔1.5mm施加一次」——「施加」搭配不自然。超声脉冲应搭配「发射」或「给予」而非「施加」（后者常用于力/压力）。",
    "改为：「超声脉冲沿每条治疗线每隔1.5 mm发射一次」")

# P76 — 翻译腔
add(76, "二.表达规范", "2.25 字面直译短语", "medium", "medium",
    "Standardized blinded assessment and patient satisfaction was measured.",
    "测量了标准化的设盲评估和患者满意度。",
    "「测量了标准化的设盲评估」——「测量…评估」搭配不当。应译为「进行了标准化的盲法评估和患者满意度调查」。「测量」不搭配「评估」。",
    "改为：「进行了标准化的盲法评估和患者满意度调查。」")

# P110 — more issues
add(110, "二.表达规范", "2.5 褒贬色彩", "medium", "medium",
    "those with more severe aging, sagging skin, and platysmal bands are likely to be better served by surgical treatment.",
    "那些衰老程度更重、皮肤松弛且出现颈阔肌带的人群，可能更适合通过手术治疗。",
    "「那些…的人群」为英文 'those with...' 的直译结构。中文可简化为「衰老程度更重、皮肤松弛且出现颈阔肌带的患者」。此外「人群」在此语境下不如「患者」准确。",
    "改为：「而衰老程度更重、皮肤松弛且出现颈阔肌带的患者，可能更适合通过手术治疗。」")

# P120 — BMI units issue
# Already covered above.

# P128 — 致使
add(128, "二.表达规范", "2.19 单读测试", "medium", "medium",
    "Because not all patients may not respond to treatments, there is room for increasing the treatment line density.",
    "由于并非所有患者都可能对治疗产生反应，因此存在增加治疗线密度的空间。",
    "「存在增加…的空间」为英文 'there is room for' 的字面直译。中文更自然表述为「仍有增加…的余地」或「仍可进一步增加…」。",
    "建议：「…因此仍可进一步增加治疗线密度。」")

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

print(f"Total issues: {len(issues)}")
print(f"By severity: {output['summary']['by_severity']}")
print(f"By dimension: {output['summary']['by_dimension']}")
