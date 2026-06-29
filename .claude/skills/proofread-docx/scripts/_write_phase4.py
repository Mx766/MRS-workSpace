#!/usr/bin/env python3
"""Write Phase 4 issues to cache with proper JSON encoding."""
import json

issues = [
  {
    "chapter": "Ch5",
    "paragraph_index": 16,
    "dimension": "二.表达规范",
    "check_item": "2.1 错别字",
    "severity": "critical",
    "confidence": "high",
    "source_quote": "The continued patient demand for nonsurgical and minimal downtime facial rejuvenation has resulted in more use of injectable neurotoxins and fillers",
    "target_quote": "患者对对非手术、恢复期极短的面部年轻化治疗的持续需求，导致注射用神经毒素和填充剂",
    "issue": "“患者对对”出现叠字错误，“对”重复了一次。应为“患者对”。",
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
    "issue": "“导致”带有贬义（导致问题/事故），原文“has resulted in”为中性陈述。学术语境中宜用中性表达。",
    "suggestion": "改为：推动了注射用神经毒素和填充剂、皮肤换肤及紧致治疗的广泛应用"
  },
  {
    "chapter": "Ch6",
    "paragraph_index": 19,
    "dimension": "二.表达规范",
    "check_item": "2.4 口语化",
    "severity": "medium",
    "confidence": "high",
    "source_quote": "When collagen is exposed to 60°C to 65°C, it becomes denatured.",
    "target_quote": "当胶原蛋白暴露于60℃至65℃时，它会变性。",
    "issue": "“它会变性”偏口语化，医学文献应用书面语。",
    "suggestion": "改为：当胶原蛋白暴露于60℃至65℃时，会发生变性。"
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
    "issue": "“被微聚焦”是英文被动语态的直译，中文可用话题-述题结构替代“被”字。",
    "suggestion": "改为：当超声波微聚焦到活体组织中的某一点时（去掉“被”字）"
  },
  {
    "chapter": "Ch7",
    "paragraph_index": 22,
    "dimension": "二.表达规范",
    "check_item": "2.15 “使”字冗余",
    "severity": "medium",
    "confidence": "high",
    "source_quote": "leaving the surrounding tissue unaffected",
    "target_quote": "同时使周围组织不受影响",
    "issue": "“使”字是英文“leaving...unaffected”结构的直译冗余。去掉“使”字中文更通顺。",
    "suggestion": "改为：同时周围组织不受影响"
  },
  {
    "chapter": "Ch7",
    "paragraph_index": 22,
    "dimension": "二.表达规范",
    "check_item": "2.G3 语义冗余",
    "severity": "low",
    "confidence": "medium",
    "source_quote": "collagen contraction, and denaturation is seen and neocollagenesis is stimulated",
    "target_quote": "会出现胶原收缩和变性，并刺激新胶原生成。",
    "issue": "“会出现”为冗余动词。中文可直接陈述，更简洁。",
    "suggestion": "改为：可见胶原收缩与变性，并刺激新胶原生成。"
  },
  {
    "chapter": "Ch7",
    "paragraph_index": 22,
    "dimension": "二.表达规范",
    "check_item": "2.8 修饰语-名词搭配",
    "severity": "low",
    "confidence": "medium",
    "source_quote": "well-defined thermal injury zones",
    "target_quote": "界限清晰的热损伤区域",
    "issue": "“界限清晰”可接受，但医学文献中“边界清晰”搭配更常见、更自然。",
    "suggestion": "改为：边界清晰的热损伤区域"
  },
  {
    "chapter": "Ch8",
    "paragraph_index": 31,
    "dimension": "二.表达规范",
    "check_item": "2.6 近义词混淆",
    "severity": "medium",
    "confidence": "high",
    "source_quote": "a monitor allows direct visualization of where the energy will be delivered",
    "target_quote": "监视器允许直观显示能量传递的位置",
    "issue": "“允许直观显示”是“allows visualization”的字面翻译。中文“允许”暗示授权/许可，此处用“可”更自然。",
    "suggestion": "改为：监视器可直观显示能量传递的位置"
  },
  {
    "chapter": "Ch8",
    "paragraph_index": 31,
    "dimension": "二.表达规范",
    "check_item": "2.5 褒贬色彩",
    "severity": "medium",
    "confidence": "high",
    "source_quote": "The focal energy delivery in given in predetermined lines results in discrete intervals",
    "target_quote": "预定的“线”状聚焦能量传递，导致在1 mm³凝固区之间产生离散间隔",
    "issue": "“导致”带有贬义——能量传递形成离散间隔不是负面后果。",
    "suggestion": "改为：预定的“线”状聚焦能量传递在1 mm³凝固区之间形成离散间隔"
  },
  {
    "chapter": "Ch10",
    "paragraph_index": 40,
    "dimension": "一.双语忠实度",
    "check_item": "1.1 完整性/1.4 错译",
    "severity": "critical",
    "confidence": "high",
    "source_quote": "An early prototype Ulthera device was used on the lateral cheek region in patients who would be undergoing a surgical rhytidectomy within 12 weeks of treatment.",
    "target_quote": "一款早期Ulthera原型设备被用于患者治疗12周内将接受手术除皱术的患者的面颊外侧区域。",
    "issue": "译文句式杂糅、逻辑混乱，出现两次“患者”。“within 12 weeks of treatment”修饰的是“surgical rhytidectomy”（治疗后12周内接受除皱术），译文误将“患者治疗”与“12周”连在一起。读一遍无法理解原文含义。",
    "suggestion": "改为：使用一款早期Ulthera原型设备，对治疗后12周内将接受手术除皱术的患者面颊外侧区域进行了治疗。"
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
    "issue": "“激进”在中文中有鲁莽/不理性之义。原文“aggressiveness”在此为中性描述治疗方案强度。",
    "suggestion": "改为：治疗方案的强度"
  },
  {
    "chapter": "Ch13",
    "paragraph_index": 56,
    "dimension": "二.表达规范",
    "check_item": "2.14 “的”字堆砌",
    "severity": "medium",
    "confidence": "medium",
    "source_quote": "Thirty of 35 patients (86%) had a clinically significant improvement in brow elevation",
    "target_quote": "35例患者中有30例（86%）的眉部提升在临床上获得显著改善",
    "issue": "“35例患者中有30例（86%）的”——长定语中用“的”使得主语不清晰。去掉“的”更通顺。",
    "suggestion": "改为：35例患者中30例（86%）眉部提升获得临床上显著改善"
  },
  {
    "chapter": "Ch13",
    "paragraph_index": 59,
    "dimension": "二.表达规范",
    "check_item": "2.F4 字面翻译 vs 语境翻译",
    "severity": "medium",
    "confidence": "high",
    "source_quote": "Direct treatment of eyelids over the eye itself is not indicated.",
    "target_quote": "对眼睛上方的眼睑直接治疗并不适用。",
    "issue": "“not indicated”在医学语境中应为“非适应证”或“不属于适应证”，而非“不适用”。失去了医学术语的精确性。",
    "suggestion": "改为：对眼睛上方的眼睑进行直接治疗并非适应证。"
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
    "issue": "“抱怨”为日常口语用词，医学文献中应用更正式的表述。",
    "suggestion": "改为：Ulthera系统的一个常见主诉是治疗过程中的疼痛。"
  },
  {
    "chapter": "Ch14",
    "paragraph_index": 110,
    "dimension": "二.表达规范",
    "check_item": "2.G1 成分残缺",
    "severity": "medium",
    "confidence": "high",
    "source_quote": "There is also mild edema that contributes to the early aesthetic improvement seen by patients.",
    "target_quote": "还有轻度水肿有助于患者看到的早期美学改善。",
    "issue": "句子缺少完整的谓语结构。“有助于”后面应跟动词短语，但“患者看到的早期美学改善”是名词短语。语法不通。",
    "suggestion": "改为：此外，轻度水肿也有助于产生患者所观察到的早期美容改善。"
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
    "issue": "单位错误：原文为“kg/m²”（千克/平方米），BMI的标准国际单位。译文误写为“mg/kg²”（毫克/千克²），这在物理上不是BMI的单位。此为严重事实错误。",
    "suggestion": "改为：体重指数 ≤ 30 kg/m²"
  },
  {
    "chapter": "Ch15",
    "paragraph_index": 133,
    "dimension": "一.双语忠实度",
    "check_item": "1.1 完整性/1.4 错译",
    "severity": "critical",
    "confidence": "high",
    "source_quote": "Facial and neck skin tightening can also be achieved by a variety of energy devices, including RF. Injectable fillers and fat grafts can result in mid and lower face elevation",
    "target_quote": "面部和颈部皮肤紧致也可以通过多种能量设备实现，包括射频注射填充材料和脂肪移植，可导致中下面部提升",
    "issue": "原文是两个独立的条目（RF能量设备 + 注射填充材料/脂肪移植），译文错误地将两条合并为一句，造成“包括射频注射填充材料”的语义错误（RF射频不是填充材料）。",
    "suggestion": "改为两句：面部和颈部皮肤紧致也可以通过包括RF在内的多种能量设备实现。注射填充材料和脂肪移植可实现中下面部提升。"
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
    "issue": "“导致”带有贬义，“中下面部提升”是正面的治疗效果，用“导致”不合适。",
    "suggestion": "改为：可实现中下面部提升"
  },
  {
    "chapter": "Ch7",
    "paragraph_index": 23,
    "dimension": "二.表达规范",
    "check_item": "2.G3 语义冗余",
    "severity": "low",
    "confidence": "medium",
    "source_quote": "MFU is different from RF energy in that it can be microfocused to target deeper tissue",
    "target_quote": "MFU与RF能量的不同之处在于，它可以微聚焦以靶向更深层组织",
    "issue": "“MFU与RF能量的不同之处在于”表达冗长。",
    "suggestion": "改为：MFU与RF的区别在于，可将能量微聚焦到更深层组织"
  },
  {
    "chapter": "Ch9",
    "paragraph_index": 34,
    "dimension": "二.表达规范",
    "check_item": "2.17 翻译腔",
    "severity": "low",
    "confidence": "medium",
    "source_quote": "Although the currently approved indications are listed below, other facial and nonfacial areas have been treated",
    "target_quote": "尽管目前批准的适应症如下所列，但其他面部及非面部区域也已接受治疗：",
    "issue": "“尽管…但”是英文“Although…”结构的直译，中文可以更简洁。",
    "suggestion": "改为：以下为目前获批的适应症，此外还在其他面部及非面部区域开展了治疗应用："
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
