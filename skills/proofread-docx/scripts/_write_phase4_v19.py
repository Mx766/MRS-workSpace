#!/usr/bin/env python3
"""Write Phase 4 v19 issues with all batch findings (10 batches, 148 paragraphs)."""
import json

issues = [
    # ===== BATCH 1 (paras 1-15): Front matter =====
    {
        "chapter": "Ch2",
        "paragraph_index": 5,
        "dimension": "二.表达规范",
        "check_item": "2.1 错别字",
        "severity": "low",
        "confidence": "high",
        "source_quote": "Noninvasive skin tightening / Ulthera / Microfocused ultrasound / Thermal injury zones",
        "target_quote": "非侵入性皮肤紧致 Ulthera  微聚焦超声 热损伤区",
        "issue": "关键词行中「Ulthera」与「微聚焦超声」之间存在双空格，其他关键词间均为单空格，间距不一致。",
        "suggestion": "删除Ulthera后的多余空格：非侵入性皮肤紧致 Ulthera 微聚焦超声 热损伤区"
    },

    # ===== BATCH 2 (paras 16-30): Introduction, Collagen, Mechanism, Ulthera =====
    {
        "chapter": "Ch5",
        "paragraph_index": 16,
        "dimension": "二.表达规范",
        "check_item": "2.1 错别字",
        "severity": "critical",
        "confidence": "high",
        "source_quote": "The continued patient demand for nonsurgical and minimal downtime facial rejuvenation",
        "target_quote": "患者对对非手术、恢复期极短的面部年轻化治疗的持续需求",
        "issue": "「对对」为重复输入错误（衍文），应为单字「对」。",
        "suggestion": "改为：患者对非手术、恢复期极短的面部年轻化治疗的持续需求"
    },
    {
        "chapter": "Ch5",
        "paragraph_index": 16,
        "dimension": "二.表达规范",
        "check_item": "2.5 褒贬色彩",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "has resulted in more use of injectable neurotoxins and fillers, and skin resurfacing and tightening treatments",
        "target_quote": "导致注射用神经毒素和填充剂、皮肤换肤术及紧致治疗的应用日益增多",
        "issue": "「导致」在中文中引出负面结果，此处「更多应用」为中性/正面发展，应换用中性动词。",
        "suggestion": "改为：推动了注射用神经毒素和填充剂、皮肤换肤及紧致治疗的广泛应用"
    },
    {
        "chapter": "Ch5",
        "paragraph_index": 16,
        "dimension": "二.表达规范",
        "check_item": "2.G3 语义冗余",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "Tissue heating either by radiofrequency (RF) or microfocused ultrasound (MFU) can be part of the overall treatment plan",
        "target_quote": "通过射频(RF)或微聚焦超声(MFU)进行的组织加热",
        "issue": "「进行」为弱动词赘余，「通过…的组织加热」即可表达同一含义。",
        "suggestion": "改为：通过射频(RF)或微聚焦超声(MFU)的组织加热，均可作为整体治疗方案的一部分"
    },
    {
        "chapter": "Ch6",
        "paragraph_index": 19,
        "dimension": "二.表达规范",
        "check_item": "2.12 \"当…时\"冗余",
        "severity": "low",
        "confidence": "high",
        "source_quote": "When collagen is exposed to 60°C to 65°C, it becomes denatured.",
        "target_quote": "当胶原蛋白暴露于60℃至65℃时，它会变性。",
        "issue": "「当…时」为欧化条件句式，可将条件融入句子主干。",
        "suggestion": "改为：胶原蛋白暴露于60℃至65℃时即发生变性。"
    },
    {
        "chapter": "Ch6",
        "paragraph_index": 19,
        "dimension": "二.表达规范",
        "check_item": "2.4 口语化",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "it becomes denatured",
        "target_quote": "当胶原蛋白暴露于60℃至65℃时，它会变性",
        "issue": "代词「它」在正式医学文献中偏口语化，宜省略。",
        "suggestion": "改为：胶原蛋白暴露于60℃至65℃时即发生变性。"
    },
    {
        "chapter": "Ch7",
        "paragraph_index": 22,
        "dimension": "二.表达规范",
        "check_item": "2.13 被动语态直译",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "When ultrasound waves are microfocused to a point in living tissue",
        "target_quote": "当超声波被微聚焦到活体组织中的某一点时",
        "issue": "「被微聚焦」直接对应英文被动语态，中文可用主动句式隐含被动语义。",
        "suggestion": "改为：将超声波微聚焦于活体组织中某一点，会产生分子振动并生成热量"
    },
    {
        "chapter": "Ch7",
        "paragraph_index": 22,
        "dimension": "二.表达规范",
        "check_item": "2.15 \"使\"字冗余",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "leaving the surrounding tissue unaffected",
        "target_quote": "同时使周围组织不受影响",
        "issue": "「使」为弱使令动词，可直接改为描述性表达。",
        "suggestion": "改为：同时周围组织不受影响"
    },
    {
        "chapter": "Ch7",
        "paragraph_index": 23,
        "dimension": "二.表达规范",
        "check_item": "2.6 近义词混淆",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "MFU can heat deeper tissue to between 60°C and 70°C without damaging the skin",
        "target_quote": "MFU可以加热更深层组织至60℃到70℃之间",
        "issue": "「到」偏口语化，正式科技文献数值范围宜用「至」；「至…之间」搭配略重复。",
        "suggestion": "改为：MFU可以加热更深层组织至60℃至70℃，而不会损伤皮肤"
    },
    {
        "chapter": "Ch7",
        "paragraph_index": 23,
        "dimension": "二.表达规范",
        "check_item": "2.16 \"对于\"句首冗余",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "For an RF device to achieve high temperatures, surface cooling is needed to protect the skin.",
        "target_quote": "对于RF设备，要达到高温，需要表面冷却以保护皮肤",
        "issue": "「对于」为英文「For」的直接翻译，中文可省略，直接将主语前置。",
        "suggestion": "改为：RF设备要达到高温，需通过表面冷却来保护皮肤。"
    },
    {
        "chapter": "Ch7",
        "paragraph_index": 23,
        "dimension": "二.表达规范",
        "check_item": "2.G4 逻辑连接断裂",
        "severity": "medium",
        "confidence": "medium",
        "source_quote": "MFU is different from RF energy in that it can be microfocused to target deeper tissue without affecting more superficial tissue. Unlike RF energy, MFU can heat deeper tissue...",
        "target_quote": "MFU与RF能量的不同之处在于，它可以微聚焦以靶向更深层组织，而不影响更浅层组织。与RF能量不同，MFU可以加热更深层组织",
        "issue": "相邻两句均以「不同」为核心信息——第一句「不同之处在于…」，第二句以「与RF能量不同」起头——语义重复导致句间衔接冗余。",
        "suggestion": "合并精简：MFU有别于RF，可微聚焦靶向深层组织而不影响浅层，且可将深层组织加热至60–70℃而不损伤皮肤。"
    },
    {
        "chapter": "Ch8",
        "paragraph_index": 29,
        "dimension": "三.数字符号单位",
        "check_item": "3.3 单位格式",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "4.5 mm, which targets the superficial muscular aponeurotic system (SMAS) and platysma",
        "target_quote": "4.5mm，靶向浅表肌肉腱膜系统(SMAS)和颈阔肌",
        "issue": "数值「4.5mm」缺少数字与单位间的空格（1.5mm/3.0mm同理），中文科技规范应加空格。",
        "suggestion": "统一改为：4.5 mm；1.5 mm；3.0 mm"
    },

    # ===== BATCH 3 (paras 31-45): Indications, Histology, Treatment Times =====
    {
        "chapter": "Ch8",
        "paragraph_index": 31,
        "dimension": "二.表达规范",
        "check_item": "2.6 近义词混淆",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "a monitor allows direct visualization of where the energy will be delivered",
        "target_quote": "监视器允许直观显示能量传递的位置",
        "issue": "「允许」暗示授权/许可，原文「allows」表示功能性「使能够」，应译为「可」。",
        "suggestion": "改为：监视器可直观显示能量传递的位置"
    },
    {
        "chapter": "Ch8",
        "paragraph_index": 31,
        "dimension": "二.表达规范",
        "check_item": "2.5 褒贬色彩",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "The focal energy delivery in given in predetermined \"lines\" results in discrete intervals between 1 mm³ coagulation zones that promote healing.",
        "target_quote": "预定的\"线\"状聚焦能量传递，导致在1 mm³凝固区之间产生离散间隔，从而促进愈合。",
        "issue": "「导致」带有贬义——能量传递形成离散间隔并促进愈合是积极的生理机制，非负面后果。",
        "suggestion": "改为：预定的\"线\"状聚焦能量传递在1 mm³凝固区之间形成离散间隔"
    },
    {
        "chapter": "Ch9",
        "paragraph_index": 34,
        "dimension": "二.表达规范",
        "check_item": "2.17 \"尽管…但\"直译",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "Although the currently approved indications are listed below, other facial and nonfacial areas have been treated",
        "target_quote": "尽管目前批准的适应症如下所列，但其他面部及非面部区域也已接受治疗",
        "issue": "「尽管…但」为英文Although…的逐字仿译，中文可更简洁。",
        "suggestion": "改为：除以下获批适应症外，其他面部及非面部区域也已接受治疗："
    },
    {
        "chapter": "Ch9",
        "paragraph_index": 37,
        "dimension": "一.双语忠实度",
        "check_item": "1.4 错译",
        "severity": "critical",
        "confidence": "high",
        "source_quote": "Improve lines and wrinkles in décolleté",
        "target_quote": "改善肩颈部的细纹和皱纹",
        "issue": "「décolleté」指前胸低领区域（锁骨以下胸廓上方），非「肩颈部」。译文中「肩颈部」错误包含了肩部区域，与原文解剖部位不符。",
        "suggestion": "改为：改善颈胸部（低领区）的细纹和皱纹"
    },
    {
        "chapter": "Ch10",
        "paragraph_index": 40,
        "dimension": "一.双语忠实度",
        "check_item": "1.1 完整性 / 1.4 错译",
        "severity": "critical",
        "confidence": "high",
        "source_quote": "An early prototype Ulthera device was used on the lateral cheek region in patients who would be undergoing a surgical rhytidectomy within 12 weeks of treatment.",
        "target_quote": "一款早期Ulthera原型设备被用于患者治疗12周内将接受手术除皱术的患者的面颊外侧区域。",
        "issue": "句式杂糅，「患者治疗…的患者」定语嵌套混乱，出现两次「患者」且修饰关系不清。原文「within 12 weeks of treatment」修饰的是手术治疗（治疗后12周内接受除皱术）。",
        "suggestion": "改为：使用一款早期Ulthera原型设备，对治疗后12周内将接受手术除皱术的患者面颊外侧区域进行了治疗。"
    },
    {
        "chapter": "Ch10",
        "paragraph_index": 40,
        "dimension": "二.表达规范",
        "check_item": "2.5 褒贬色彩",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "resulting in a mean increase in dermal thickening from 1.32 to 1.63 mm",
        "target_quote": "导致真皮厚度平均从1.32 mm增加到1.63 mm",
        "issue": "「导致」用于正面结果（真皮增厚是治疗效果），应用中性表达。",
        "suggestion": "改为：使真皮厚度平均从1.32 mm增加至1.63 mm"
    },
    {
        "chapter": "Ch11",
        "paragraph_index": 43,
        "dimension": "二.表达规范",
        "check_item": "2.5 褒贬色彩",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "aggressiveness of protocol",
        "target_quote": "方案的激进程度",
        "issue": "「激进」在中文中为贬义词（激进分子/手段激进），用于医学文献描述治疗方案强度不当。原文指积极治疗程度。",
        "suggestion": "改为：治疗方案的强度"
    },

    # ===== BATCH 4 (paras 46-60): Pretreatment, Face/Neck, Periorbital =====
    {
        "chapter": "Ch12",
        "paragraph_index": 51,
        "dimension": "四.术语合规",
        "check_item": "4.1 术语库一致",
        "severity": "critical",
        "confidence": "high",
        "source_quote": "Topical betacaine/lidocaine/procaine cream for 60 minutes",
        "target_quote": "局部用贝他卡因/利多卡因/普鲁卡因乳膏60分钟",
        "issue": "「贝他卡因」为betacaine的音译。Betacaine即benzocaine（苯佐卡因），中国药典标准译名为「苯佐卡因」。非标准音译名可能导致医务人员无法识别药物。",
        "suggestion": "改为：局部用苯佐卡因/利多卡因/普鲁卡因乳膏60分钟"
    },
    {
        "chapter": "Ch13",
        "paragraph_index": 56,
        "dimension": "二.表达规范",
        "check_item": "2.14 \"的\"字堆砌",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "Thirty of 35 patients (86%) had a clinically significant improvement in brow elevation",
        "target_quote": "35例患者中有30例（86%）的眉部提升在临床上获得显著改善",
        "issue": "数量修饰语「30例（86%）的眉部提升」中「的」将数字短语与名词强行组合为偏正结构，中文表达不自然。",
        "suggestion": "改为：35例患者中，30例（86%）眉部提升在临床上获得显著改善"
    },
    {
        "chapter": "Ch13",
        "paragraph_index": 56,
        "dimension": "二.表达规范",
        "check_item": "2.F1 词义范围偏差",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "measured outcomes at 90 days",
        "target_quote": "测量了90天时的结局",
        "issue": "「结局」（outcome）在临床研究中通常指最终终点事件（如死亡率），此处测量的是90天这一中间时间点的观察指标，译为「结果」更准确。",
        "suggestion": "改为：测量了90天时的结果"
    },
    {
        "chapter": "Ch13",
        "paragraph_index": 56,
        "dimension": "三.数字符号单位",
        "check_item": "3.3 单位格式",
        "severity": "low",
        "confidence": "high",
        "source_quote": "4 MHz, 4.5-mm focal depth ... 7 MHz, 4.5-mm focal depth",
        "target_quote": "4MHz、4.5mm焦距（源能量0.75–1.2J），7MHz、4.5 mm焦距",
        "issue": "同一句内空格不统一：「4.5mm焦距」无空格，「4.5 mm焦距」有空格。原文均用空格，应统一。",
        "suggestion": "统一为数字与单位间加空格：4.5 mm焦距"
    },
    {
        "chapter": "Ch13",
        "paragraph_index": 59,
        "dimension": "一.双语忠实度",
        "check_item": "1.4 错译 / 2.F4 语境翻译",
        "severity": "critical",
        "confidence": "high",
        "source_quote": "Direct treatment of eyelids over the eye itself is not indicated.",
        "target_quote": "对眼睛上方的眼睑直接治疗并不适用。",
        "issue": "「not indicated」在医学语境中含义为「非适应证」（不属于批准的/推荐的临床适应证），而非「不适用」（not applicable）。两者含义不同：某项治疗技术上可以实施（适用），但医学上不建议（非适应证）。",
        "suggestion": "改为：对眼睛上方的眼睑进行直接治疗并非适应证。"
    },
    {
        "chapter": "Ch13",
        "paragraph_index": 60,
        "dimension": "二.表达规范",
        "check_item": "2.G1 成分残缺",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "Quantitative improvement was seen after targeting the lower eyelid skin and orbital septum with 1.5-mm and 3.0-mm probes in a small series of 7 patients.",
        "target_quote": "在一项针对7例患者的小型研究中，使用1.5 mm和3.0 mm探头靶向下眼睑皮肤和眶隔后，观察到定量改善。",
        "issue": "全句缺少明确主语：「使用」和「观察到」的动作主体未出现，读者需自行推断。",
        "suggestion": "改为：一项针对7例患者的小型研究使用1.5 mm和3.0 mm探头靶向下眼睑皮肤和眶隔，观察到定量改善。"
    },

    # ===== BATCH 5 (paras 61-75): Nasolabial, SMAS, Buttocks =====
    {
        "chapter": "Ch13",
        "paragraph_index": 63,
        "dimension": "一.双语忠实度",
        "check_item": "1.1 完整性",
        "severity": "critical",
        "confidence": "high",
        "source_quote": "A prospective, blinded evaluator study of 22 patients ... evaluated the nasolabial folds and jaw line.",
        "target_quote": "一项前瞻性、盲法评估研究，纳入22例患者，使用7.5MHz和4.4MHz手柄...评估了鼻唇沟和下颌线。4 在面部和颏下区域治疗两个",
        "issue": "段末「治疗两个」为断句残文。原文句子被PDF分页截断，下落「月后，所有患者均…」出现在第70段。需合并63段和70段，恢复完整句子。",
        "suggestion": "将第63段尾部与第70段开头的「月后，所有患者均…」合并为一段。"
    },
    {
        "chapter": "Ch13",
        "paragraph_index": 70,
        "dimension": "一.双语忠实度",
        "check_item": "1.1 完整性",
        "severity": "critical",
        "confidence": "high",
        "source_quote": "Two months after treatment ... all patients demonstrated nasolabial fold and jaw line improvement",
        "target_quote": "月后，所有患者均显示出鼻唇沟和下颌线的改善，分别有77%和73%的患者主观报告\"显著改善\"。",
        "issue": "「月后」为第63段断句的残余——续上文「…治疗两个」为「…治疗两个月后」。独立成段导致阅读断裂。需与第63段合并。",
        "suggestion": "与第63段合并为完整段落。"
    },
    {
        "chapter": "Ch13",
        "paragraph_index": 70,
        "dimension": "二.表达规范",
        "check_item": "2.F1 词义范围偏差",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "77% and 73% of patients subjectively reported \"much improvement\"",
        "target_quote": "分别有77%和73%的患者主观报告\"显著改善\"",
        "issue": "「much improvement」为标准GAIS量表评级（介于improved与very much improved之间），中文标准对应「明显改善」。「显著改善」对应「very much improved/significantly improved」，过度强调了改善程度。",
        "suggestion": "改为：分别有77%和73%的患者主观报告\"明显改善\""
    },
    {
        "chapter": "Ch13",
        "paragraph_index": 73,
        "dimension": "二.表达规范",
        "check_item": "2.17 翻译腔",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "the aesthetic improvements seen after treatment",
        "target_quote": "治疗后所观察到的美学改善",
        "issue": "「所观察到的」中「所」字为古汉语残留，现代医学文献中多余。",
        "suggestion": "改为：治疗后观察到的美学改善"
    },

    # ===== BATCH 6 (paras 76-90): Buttocks, Arms/Thighs, Ethnic Groups, Pain =====
    {
        "chapter": "Ch13",
        "paragraph_index": 76,
        "dimension": "二.表达规范",
        "check_item": "2.7 动宾搭配",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "Standardized blinded assessment and patient satisfaction was measured.",
        "target_quote": "测量了标准化的设盲评估和患者满意度。",
        "issue": "动词「测量」不能搭配「评估」——可测量数值/满意度，但不能测量评估行为本身。应改为「进行了…评估并测量了…满意度」。",
        "suggestion": "改为：进行了标准化的设盲评估，并测量了患者满意度。"
    },
    {
        "chapter": "Ch13",
        "paragraph_index": 79,
        "dimension": "一.双语忠实度",
        "check_item": "1.4 错译",
        "severity": "critical",
        "confidence": "high",
        "source_quote": "One small study included 6 of each of these areas using 1 (single plane) or 2 (dual treatment depths) treatment passes.",
        "target_quote": "对每个区域进行了6次治疗",
        "issue": "原文意为研究纳入了每个解剖区域各6例（共6例上臂+6例大腿+6例膝盖=18例），而非「对每个区域进行了6次治疗」。混淆了病例数与治疗次数。",
        "suggestion": "改为：该小型研究纳入了上述各区域各6例"
    },
    {
        "chapter": "Ch13",
        "paragraph_index": 82,
        "dimension": "二.表达规范",
        "check_item": "2.G3 语义冗余",
        "severity": "low",
        "confidence": "high",
        "source_quote": "postinflammatory hyperpigmentation",
        "target_quote": "炎症后色素沉着过度",
        "issue": "「炎症后色素沉着」已是完整的中文皮肤科标准术语，「过度」为冗余。",
        "suggestion": "改为：炎症后色素沉着"
    },
    {
        "chapter": "Ch13",
        "paragraph_index": 83,
        "dimension": "二.表达规范",
        "check_item": "2.6 近义词混淆",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "whitish wheals or striations",
        "target_quote": "白色风团或条纹",
        "issue": "「whitish」意为发白/带白色的（不完全白色），「白色」为纯白。皮肤科描述应保留程度差异。",
        "suggestion": "改为：发白的风团或条纹"
    },
    {
        "chapter": "Ch13",
        "paragraph_index": 86,
        "dimension": "二.表达规范",
        "check_item": "2.4 口语化",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "One frequent complaint of the Ulthera system is pain during treatment.",
        "target_quote": "Ulthera系统的一个常见抱怨是治疗过程中的疼痛。",
        "issue": "「抱怨」为日常口语用词，医学文献中应更正式。注意：此处complaint指设备不足，非患者「主诉」。",
        "suggestion": "改为：Ulthera系统常被反映的一个问题是治疗过程中的疼痛。"
    },

    # ===== BATCH 7 (paras 91-105): Pain Management, Recovery, Side Effects =====
    {
        "chapter": "Ch13",
        "paragraph_index": 97,
        "dimension": "二.表达规范",
        "check_item": "2.12 \"当…时\"冗余",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "Based on small pilot trials, the following was found during Ulthera treatments:",
        "target_quote": "基于小规模试点试验，Ulthera治疗过程中发现以下情况：",
        "issue": "译文通顺，无显著问题。审查通过。",
        "suggestion": ""
    },
    {
        "chapter": "Ch13",
        "paragraph_index": 101,
        "dimension": "二.表达规范",
        "check_item": "2.20 长句拆分",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "Although inflammation is a necessary component of neocollagenesis after Ulthera treatment, it is unknown if chronic nonsteroidal anti-inflammatory medication use may interfere with the final outcome.",
        "target_quote": "尽管炎症是Ulthera治疗后新胶原生成的必要组成部分，但尚不清楚长期使用非甾体抗炎药是否可能干扰最终结果。",
        "issue": "译文准确但句子偏长（44字），可考虑拆分以提升可读性。",
        "suggestion": "可拆为：炎症是Ulthera治疗后新胶原生成的必要组成部分，但长期使用非甾体抗炎药是否干扰最终结果，目前尚不清楚。"
    },
    {
        "chapter": "Ch14",
        "paragraph_index": 104,
        "dimension": "二.表达规范",
        "check_item": "2.F4 语境翻译",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "the Ulthera system can be considered to have no down time and a minimal recovery period",
        "target_quote": "Ulthera系统可被视为无停机时间和极短的恢复期",
        "issue": "「停机时间」为设备/工程术语（machine downtime），用于医学美容指「无需恢复期/无停工休养时间」不当，应为「恢复期」或「停工休养时间」。",
        "suggestion": "改为：Ulthera系统可被视为无恢复期、休养时间极短"
    },

    # ===== BATCH 8 (paras 106-120): Side Effects (cont), Results =====
    {
        "chapter": "Ch13",
        "paragraph_index": 107,
        "dimension": "二.表达规范",
        "check_item": "2.17 翻译腔",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "side effects are generally mild and transient in nature",
        "target_quote": "副作用通常性质轻微且短暂",
        "issue": "「性质」为英文「in nature」的机械直译，中文无需此词。「性质轻微」搭配也不自然——应为「程度轻微」。",
        "suggestion": "改为：副作用通常较为轻微且短暂"
    },
    {
        "chapter": "Ch14",
        "paragraph_index": 110,
        "dimension": "二.表达规范",
        "check_item": "2.G1 成分残缺",
        "severity": "critical",
        "confidence": "high",
        "source_quote": "There is also mild edema that contributes to the early aesthetic improvement seen by patients.",
        "target_quote": "还有轻度水肿有助于患者看到的早期美学改善。",
        "issue": "句子结构破碎：「有助于」后面应跟动词短语，但「患者看到的早期美学改善」是名词短语——缺乏谓语成分。读一遍无法理解。",
        "suggestion": "改为：此外，轻度水肿也有助于产生患者可观察到的早期美学改善。"
    },
    {
        "chapter": "Ch14",
        "paragraph_index": 110,
        "dimension": "二.表达规范",
        "check_item": "2.F3 语域一致性",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "Because ideal candidates tend to have mild to moderate aging",
        "target_quote": "由于理想候选人通常呈现轻度至中度衰老",
        "issue": "「候选人」在中文中关联选举/求职场景，用于医学语境极不得体。应为「适应证患者」或「适宜人群」。",
        "suggestion": "改为：由于理想适应证患者通常呈轻度至中度衰老"
    },
    {
        "chapter": "Ch14",
        "paragraph_index": 110,
        "dimension": "二.表达规范",
        "check_item": "2.5 褒贬色彩",
        "severity": "medium",
        "confidence": "medium",
        "source_quote": "may result in an initial tissue \"lift\"",
        "target_quote": "可能导致组织的初步\"提升\"",
        "issue": "「导致」用于正面治疗效果不当。",
        "suggestion": "改为：可能带来组织的初步\"提升\""
    },
    {
        "chapter": "Ch14",
        "paragraph_index": 111,
        "dimension": "二.表达规范",
        "check_item": "2.F1 词义范围偏差",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "the overall positive response was 61%",
        "target_quote": "总体阳性反应率为61%",
        "issue": "「阳性反应率」在医学语境中通常用于诊断试验或病理结果，用于美容治疗效果评估不当。应为「改善率」或「有效率」。",
        "suggestion": "改为：总体改善率为61%"
    },
    {
        "chapter": "Ch14",
        "paragraph_index": 111,
        "dimension": "二.表达规范",
        "check_item": "2.7 动宾搭配",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "had a quantitative improvement in tissue lift...had a qualitative improvement",
        "target_quote": "在3个月后颏下区域的组织提升出现了量化改善",
        "issue": "「出现了…改善」搭配生硬，「出现」通常搭配负面事物（出现问题/并发症）。",
        "suggestion": "改为：在3个月后颏下区域的组织提升取得了量化改善"
    },
    {
        "chapter": "Ch14",
        "paragraph_index": 112,
        "dimension": "二.表达规范",
        "check_item": "2.G2 句式杂糅",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "One independent study of 10 patients with standardized photography and blinded, experienced clinician evaluators found that...",
        "target_quote": "一项独立研究，纳入10例患者，采用标准化摄影和盲法、由经验丰富的临床医生评估后发现",
        "issue": "「采用标准化摄影和盲法」将名词「摄影」与方法概念「盲法」并列于「采用」之后，语法类别不一致，结构混杂。",
        "suggestion": "改为：一项独立研究纳入10例患者，采用标准化摄影，并由经验丰富的临床医生进行盲法评估后发现"
    },
    {
        "chapter": "Ch14",
        "paragraph_index": 119,
        "dimension": "二.表达规范",
        "check_item": "2.20 长句拆分",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "treatment protocols, the amount of energy delivered, and individual patient factors make generalizations on expected outcomes difficult.",
        "target_quote": "治疗方案、传递的能量剂量以及患者个体因素使得对预期结果进行概括变得困难",
        "issue": "「传递的能量」——「delivered energy」医学语境中常用「施加的能量」或「输出的能量」，「传递」偏工程用语。",
        "suggestion": "改为：治疗方案、施加的能量剂量及患者个体因素，使得预期结果难以概括"
    },
    {
        "chapter": "Ch14",
        "paragraph_index": 120,
        "dimension": "三.数字符号单位",
        "check_item": "3.1 数值/单位错误",
        "severity": "critical",
        "confidence": "high",
        "source_quote": "a body mass index of 30 kg/m² or less",
        "target_quote": "体重指数≤30mg/kg2",
        "issue": "BMI单位严重错误：原文为「kg/m²」（千克/平方米，BMI标准国际单位），译文误写为「mg/kg²」（毫克/千克²），这在物理学上不是BMI的单位。同一句前半部分「体重指数大于30kg/m2」已正确使用kg/m²，前后矛盾进一步证实此处为错误。",
        "suggestion": "改为：体重指数 ≤ 30 kg/m²"
    },
    {
        "chapter": "Ch14",
        "paragraph_index": 120,
        "dimension": "一.双语忠实度",
        "check_item": "1.4 错译",
        "severity": "critical",
        "confidence": "high",
        "source_quote": "It is possible that a higher treatment density (more lines) and assessment at 6 to 9 months may have shown more favorable responses.",
        "target_quote": "在更高的治疗密度（更多疗程）和6至9个月时的评估下，可能会显示出更有利的应答。",
        "issue": "「更多疗程」严重误译。原文「more lines」指超声治疗的「线数」（每治疗区域发射的超声波线条数量），而非「疗程」（treatment sessions/courses）。「疗程」意味着多次就诊，完全改变了原文含义。前文「约295条线」已正确将lines译为「线」，此处却译为「疗程」，前后不一致。",
        "suggestion": "改为：若采用更高的治疗密度（更多线数）并在6至9个月时进行评估，可能会显示出更有利的应答。"
    },

    # ===== BATCH 9 (paras 121-135): Duration, Physician, Protocol Variation, Other Options =====
    {
        "chapter": "Ch14",
        "paragraph_index": 123,
        "dimension": "二.表达规范",
        "check_item": "2.6 近义词混淆",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "Although no skin tightening procedure can claim permanent results",
        "target_quote": "尽管没有任何皮肤紧致程序能声称永久效果",
        "issue": "「procedure」在此医学语境中应译为「治疗」或「疗法」，而非「程序」——「程序」在中文中指软件流程或步骤安排。",
        "suggestion": "改为：尽管没有任何皮肤紧致治疗能声称具有永久效果"
    },
    {
        "chapter": "Ch15",
        "paragraph_index": 128,
        "dimension": "二.表达规范",
        "check_item": "2.F1 词义范围偏差",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "high rates of efficacy when using 600 to 800 lines per treatment",
        "target_quote": "每次治疗使用600至800条线时，疗效显著",
        "issue": "「high rates of efficacy」指治疗有效率较高（定量比例），「疗效显著」为定性描述，丢失了原文的量化含义。",
        "suggestion": "改为：每次治疗使用600至800条线时，有效率较高"
    },
    {
        "chapter": "Ch15",
        "paragraph_index": 128,
        "dimension": "二.表达规范",
        "check_item": "2.6 近义词混淆",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "there seems to be little clinical return after 1200 to 1500 lines",
        "target_quote": "但超过1200至1500线后，临床收益似乎不大",
        "issue": "「clinical return」在医学语境中指临床获益/效果回报，「收益」带有经济/财务色彩（如投资收益）。",
        "suggestion": "改为：临床获益似乎不大"
    },
    {
        "chapter": "Ch15",
        "paragraph_index": 132,
        "dimension": "二.表达规范",
        "check_item": "2.23 术语过于泛化",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "Brow elevation can be achieved with neuromodulators and injectable fillers",
        "target_quote": "眉部提升可通过神经调节剂和注射填充材料实现。",
        "issue": "「注射填充材料」偏原材料描述，医学文献更规范表述为「注射填充剂」或「皮肤填充剂」。",
        "suggestion": "改为：眉部提升可通过神经调节剂和注射填充剂实现。"
    },
    {
        "chapter": "Ch15",
        "paragraph_index": 133,
        "dimension": "一.双语忠实度",
        "check_item": "1.1 完整性 / 1.4 错译",
        "severity": "critical",
        "confidence": "high",
        "source_quote": "Facial and neck skin tightening can also be achieved by a variety of energy devices, including RF.\n\nInjectable fillers and fat grafts can result in mid and lower face elevation",
        "target_quote": "面部和颈部皮肤紧致也可以通过多种能量设备实现，包括射频注射填充材料和脂肪移植，可导致中下面部提升",
        "issue": "【段落合并错误】原文为两个独立项目：(1)能量设备（含RF）用于皮肤紧致；(2)注射填充剂和脂肪移植用于中下面部提升。译文将两句合并，导致「射频」（RF，能量设备）与「注射填充材料」「脂肪移植」并列于「能量设备」列举中，产生「射频注射填充材料」这一不存在的概念——RF是能量源设备，不是填充材料。",
        "suggestion": "拆分为两句：(1)面部和颈部皮肤紧致也可通过包括RF在内的多种能量设备实现。(2)注射填充剂和脂肪移植可实现中下面部提升。"
    },
    {
        "chapter": "Ch15",
        "paragraph_index": 133,
        "dimension": "二.表达规范",
        "check_item": "2.5 褒贬色彩",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "can result in mid and lower face elevation",
        "target_quote": "可导致中下面部提升",
        "issue": "「导致」在中文中几乎固定带有消极色彩，中下面部提升为正面美学效果。",
        "suggestion": "改为：可实现中下面部提升"
    },
    {
        "chapter": "Ch15",
        "paragraph_index": 134,
        "dimension": "二.表达规范",
        "check_item": "2.F4 语境翻译",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "Lower facial skin laxity and jowls have been treated with conservative laser-assisted liposuction",
        "target_quote": "下面部皮肤松弛和下颌赘肉已通过保守性激光辅助吸脂术进行治疗",
        "issue": "「conservative」在此语境中意为「低强度/小范围」（描述手术技术强度），但中文「保守」在医学中固定对应「conservative treatment」（保守治疗=非手术）。「保守性激光辅助吸脂术」构成自相矛盾——吸脂术属手术，非保守治疗。",
        "suggestion": "改为：下面部皮肤松弛和下颌赘肉已通过低强度激光辅助吸脂术进行治疗"
    },

    # ===== BATCH 10 (paras 136-148): Summary, References =====
    {
        "chapter": "Ch15",
        "paragraph_index": 136,
        "dimension": "一.双语忠实度",
        "check_item": "1.4 错译",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "Submental fullness can be reduced with deoxycholic acid (Kybella) injections",
        "target_quote": "颏下饱满感可通过注射去氧胆酸(Kybella)来减少",
        "issue": "「饱满感」中「感」字将客观体征译为患者主观感受。原文「submental fullness」指颏下区域客观存在的脂肪饱满外观，为临床体征。此外，英文半角括号在中文正文中应改用全角。",
        "suggestion": "改为：颏下饱满可通过注射去氧胆酸（Kybella）减少"
    },
    {
        "chapter": "Ch15",
        "paragraph_index": 136,
        "dimension": "二.表达规范",
        "check_item": "2.4 口语化",
        "severity": "low",
        "confidence": "high",
        "source_quote": "can be reduced with deoxycholic acid (Kybella) injections",
        "target_quote": "可通过注射去氧胆酸(Kybella)来减少",
        "issue": "「来减少」中「来」字为口语化表达，正式医学文献中多余。",
        "suggestion": "去掉「来」字：可通过注射去氧胆酸（Kybella）减少"
    },
    {
        "chapter": "Ch15",
        "paragraph_index": 138,
        "dimension": "一.双语忠实度",
        "check_item": "1.4 错译",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "More invasive and surgical options should always be discussed with patients as more severe aging may be less responsive to noninvasive treatments.",
        "target_quote": "应始终与患者讨论更具侵入性的手术选择，因为更严重的衰老可能对非侵入性治疗反应较差。",
        "issue": "「更具侵入性的手术选择」将原文并列的两个范畴——「more invasive options」（侵入性更强的非手术方案）和「surgical options」（手术方案）——错误压缩为一个范畴，读起来像是仅指不同程度侵入性的外科手术。",
        "suggestion": "改为：应始终与患者讨论侵入性更强的治疗方案及手术方案，因为更严重的衰老可能对非侵入性治疗反应较差。"
    },
    {
        "chapter": "Ch16",
        "paragraph_index": 141,
        "dimension": "三.数字符号单位",
        "check_item": "3.3 单位格式",
        "severity": "low",
        "confidence": "high",
        "source_quote": "a body mass index of 30 kg/m² or less",
        "target_quote": "体重指数为30 kg/m2 或以下",
        "issue": "「m2」中数字2应为上标「²」，为BMI标准医学书写格式。",
        "suggestion": "改为：体重指数为30 kg/m²或以下"
    },
    {
        "chapter": "Ch16",
        "paragraph_index": 141,
        "dimension": "二.表达规范",
        "check_item": "2.13 翻译腔",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "variability in patient response needs to be considered and future improvements in treatment protocols may improve response rates.",
        "target_quote": "然而，需考虑患者反应的差异性，未来治疗方案的改进可能会提高反应率。",
        "issue": "「需考虑患者反应的差异性」为英文抽象名词「variability」的直译结构，生硬。中文更适合用主谓结构：患者反应存在差异。",
        "suggestion": "改为：然而，需注意患者对治疗的反应存在差异，未来优化治疗方案后，反应率有望提高。"
    },
    {
        "chapter": "Ch16",
        "paragraph_index": 141,
        "dimension": "二.表达规范",
        "check_item": "2.F1 词义范围偏差",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "MFU is a noninvasive facial skin tightening technology with minimal down time that can complement other noninvasive treatments.",
        "target_quote": "MFU是一种非侵入性面部皮肤紧致技术，恢复时间短，可作为其他非侵入性治疗的补充。",
        "issue": "「minimal down time」强调极短/近乎于无，而「短」是相对程度描述，未能完全传达「几乎无恢复期」的含义。",
        "suggestion": "改为：MFU是一种非侵入性面部皮肤紧致技术，几乎无恢复期，可作为其他非侵入性治疗的补充。"
    }
]

with open('skills/proofread-docx/cache/issues_phase4.json', 'w', encoding='utf-8') as f:
    json.dump(issues, f, ensure_ascii=False, indent=2)

with open('skills/proofread-docx/cache/issues_merged.json', 'w', encoding='utf-8') as f:
    json.dump(issues, f, ensure_ascii=False, indent=2)

crit = sum(1 for i in issues if i['severity'] == 'critical')
med = sum(1 for i in issues if i['severity'] == 'medium')
low = sum(1 for i in issues if i['severity'] == 'low')
print(f'Written: {len(issues)} issues (critical={crit}, medium={med}, low={low})')

# Verify
with open('skills/proofread-docx/cache/issues_phase4.json', 'r', encoding='utf-8') as f:
    v = json.load(f)
print(f'Verified: {len(v)} issues parse OK')
