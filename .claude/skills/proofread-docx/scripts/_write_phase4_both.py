"""Write Phase 4 issues for batch 2 (SAR Tables) and batch 3 (DSS Combined)."""
import json, sys

# ============================================================
# Batch 2: SAR Tables
# ============================================================
issues_2 = [
    # --- Critical ---
    {
        "chapter": "Ch1",
        "paragraph_index": 16,
        "dimension": "一.双语忠实度",
        "check_item": "1.4 错译",
        "severity": "critical",
        "confidence": "high",
        "source_quote": "without the written permission of CLASSYS Inc.",
        "target_quote": "未经CLASSYS Inc.书面允许，不得发表或披露文中所含的信息",
        "issue": "\"permission\"译为"允许"不当。\"书面允许\"是日常用语，正式法律/商业语境应译为"书面许可"",
        "suggestion": "改为"未经CLASSYS Inc.书面许可，不得发表或披露文中所含的信息""
    },
    {
        "chapter": "Ch1",
        "paragraph_index": 168,
        "dimension": "四.术语合规",
        "check_item": "4.3 跨段术语统一",
        "severity": "critical",
        "confidence": "high",
        "source_quote": "adverse events related to the investigational device",
        "target_quote": "与试验器械相关不良事件严重程度",
        "issue": "同一文档中\"investigational device\"与\"test device\"中文译法不一致。TOC中\"test device\"译为"研究器械"(para 71)，\"investigational device\"译为"试验器械"(para 74)，两处英文含义相同但译文交换了对应关系",
        "suggestion": "统一译法：\"test device\"和\"investigational device\"在本临床试验语境下均指受试器械，建议统一为"试验器械"或"受试器械"，并在全文中保持一致"
    },
    {
        "chapter": "Ch1",
        "paragraph_index": 71,
        "dimension": "四.术语合规",
        "check_item": "4.3 跨段术语统一",
        "severity": "critical",
        "confidence": "high",
        "source_quote": "Analysis of adverse events and adverse events related to the test device",
        "target_quote": "不良事件及与研究器械相关不良事件分析",
        "issue": "\"test device\"译为"研究器械"，但后文(para 74)\"investigational device\"却译为"试验器械"。两个英文术语指代同一概念，中文译法却互换且不一致",
        "suggestion": "统一术语：全文使用"试验器械"作为\"investigational device\"/\"test device\"的统一译法"
    },
    # --- Medium ---
    {
        "chapter": "Ch1",
        "paragraph_index": 169,
        "dimension": "二.表达规范",
        "check_item": "2.1 错别字/语法",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "Relationship between adverse events and the investigational device",
        "target_quote": "不良事件的与试验器械的关系",
        "issue": "语法错误：\"的\"字位置放错。\"不良事件的与试验器械的关系\"不通顺",
        "suggestion": "改为"不良事件与试验器械的关系""
    },
    {
        "chapter": "Ch1",
        "paragraph_index": 88,
        "dimension": "四.术语合规",
        "check_item": "4.1 术语库一致",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "Analysis of incidence of local adverse reactions at the treatment site",
        "target_quote": "治疗部位局部副反应发生情况分析",
        "issue": "\"adverse reactions\"译为"副反应"非中国GCP标准用语。中国临床试验法规体系使用"不良反应"作为标准术语（如《医疗器械临床试验质量管理规范》）",
        "suggestion": "全文将"副反应"统一改为"不良反应""
    },
    {
        "chapter": "Ch1",
        "paragraph_index": 89,
        "dimension": "四.术语合规",
        "check_item": "4.1 术语库一致",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "Analysis of incidence of local adverse reactions at the treatment site",
        "target_quote": "治疗部位局部副反应发生率分析",
        "issue": "同上，\"副反应\"应为"不良反应"（GCP标准用语）",
        "suggestion": "改为"不良反应""
    },
    {
        "chapter": "Ch1",
        "paragraph_index": 90,
        "dimension": "四.术语合规",
        "check_item": "4.1 术语库一致",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "Analysis of local adverse reactions at the treatment site by symptom duration",
        "target_quote": "治疗部位局部副反应按症状持续时间分析",
        "issue": "同上，\"副反应\"应为"不良反应"",
        "suggestion": "改为"不良反应""
    },
    {
        "chapter": "Ch1",
        "paragraph_index": 24,
        "dimension": "四.术语合规",
        "check_item": "4.1 术语库一致",
        "severity": "medium",
        "confidence": "medium",
        "source_quote": "Analysis of protocol deviations",
        "target_quote": "受试者方案偏离分析",
        "issue": "\"protocol deviation\"译为"方案偏离"。中国GCP常用"方案违背"，虽"偏离"也可接受但"违背"在监管文档中更标准",
        "suggestion": "考虑使用"方案违背"（更贴近中国GCP标准用语）或保持"方案偏离"（如全文一致）"
    },
    # --- Low ---
    {
        "chapter": "Ch1",
        "paragraph_index": 7,
        "dimension": "五.格式",
        "check_item": "5.1 标题层级",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "Tables",
        "target_quote": "Tables",
        "issue": "副标题\"Tables\"保留英文未翻译，中文文档中建议译为"表格"以保持语言一致性",
        "suggestion": "考虑改为"表格"（如文档其余部分均为中文）"
    },
    {
        "chapter": "Ch1",
        "paragraph_index": 3,
        "dimension": "二.表达规范",
        "check_item": "2.4 口语化vs书面语",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "for Eyebrow Lifting",
        "target_quote": "用于眉毛提拉",
        "issue": "\"眉毛提拉\"偏日常用语。临床试验标题中建议使用更正式的"眉部提升"",
        "suggestion": "考虑使用"眉部提升"（临床学术用语）"
    },
    {
        "chapter": "Ch1",
        "paragraph_index": 86,
        "dimension": "四.术语合规",
        "check_item": "4.3 跨段术语统一",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "Table 4.4.1 Analysis of incidence of local adverse reactions at the treatment site",
        "target_quote": "表4.4.1治疗部位局部副反应发生情况分析",
        "issue": "表4.4.1与表4.4.2在英文源文件中标题相同（\"Analysis of incidence of local adverse reactions at the treatment site\"），但中文翻译做了区分（"发生情况"vs"发生率"）。虽然区分有助于理解，但与源文件不一致",
        "suggestion": "核对两个表格实际内容是否不同。如表4.4.1为发生例数、表4.4.2为发生率，则中文区分合理；否则应与源文件保持一致"
    },
]

# ============================================================
# Batch 3: DSS Combined
# ============================================================
issues_3 = [
    # --- Medium ---
    {
        "chapter": "Ch1",
        "paragraph_index": 14,
        "dimension": "二.表达规范",
        "check_item": "2.F3 语域一致性",
        "severity": "medium",
        "confidence": "medium",
        "source_quote": "No part of this publication may be reproduced and/or published by print, photo print, microfilm or any other means without the previous written consent of SGS.",
        "target_quote": "未经SGS事先书面许可，不得以印刷、影印、缩微胶片或任何其他方式复制和/或出版本出版物的任何部分",
        "issue": "\"and/or\"译为"和/或"——\"和/或\"是英文法律文本直译，中文正式文件中通常用"或"即可涵盖两者含义",
        "suggestion": "改为"不得以印刷、影印、缩微胶片或任何其他方式复制或出版本出版物的任何部分""
    },
    {
        "chapter": "Ch1",
        "paragraph_index": 24,
        "dimension": "二.表达规范",
        "check_item": "2.12 \"当…时\"冗余",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "With over 300 associated companies in more than 140 countries, employing over 100,000 people...",
        "target_quote": "集团在全球140多个国家拥有300多家关联公司，员工超过10万名，办事处和实验室超过1600家。SGS集团成立于1878年，凭借其地理覆盖范围和全面的服务能力，在国际技术服务领域独树一帜",
        "issue": "\"SGS集团\"在连续两句中重复出现（前句已确立话题为"集团"），第二句可省略主语或用"其"替代，避免重复",
        "suggestion": "\"SGS集团成立于1878年\"→可改为"集团成立于1878年"或"自1878年成立以来"，与前句保持话题连贯"
    },
    {
        "chapter": "Ch2",
        "paragraph_index": 146,
        "dimension": "四.术语合规",
        "check_item": "4.1 术语库一致",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "brute force attacks",
        "target_quote": "将对其执行暴力破解攻击",
        "issue": "\"brute force attacks\"在网络安全领域标准译法为"暴力破解攻击"或"蛮力攻击"。\"暴力破解\"本身已包含\"攻击\"含义，\"暴力破解攻击\"存在语义冗余",
        "suggestion": "改为"将对其执行暴力破解"或"将对其进行蛮力攻击""
    },
    {
        "chapter": "Ch29",
        "paragraph_index": 313,
        "dimension": "二.表达规范",
        "check_item": "2.20 长句拆分",
        "severity": "medium",
        "confidence": "high",
        "source_quote": "(long paragraph about user permissions)",
        "target_quote": "评估人员直接使用该用户账户登录，并确认权限配置存在问题。此账户被授予了过度权限，允许其查看和修改其他用户的主目录和文件，其中包含许多敏感文件，如脚本，包括start.sh和shutdown.sh。如果这些脚本被篡改，例如将连接重定向到攻击者控制的服务器或下载恶意软件和后门程序，可能导致严重的安全影响。然而，目前用户名已更改为非通用值，SSH端口已禁用，密码已配置为具有足够长度和复杂性",
        "issue": "末句转折\"然而\"与上下文逻辑不够连贯——前面描述的安全风险（脚本可被篡改）与后面描述的安全措施（用户名/SSH/密码配置）之间存在逻辑跳跃，读者需要自行推断\"这些措施已降低了前述风险\"",
        "suggestion": "建议在\"然而\"前增加过渡句如\"针对上述风险，已采取了以下缓解措施：\""
    },
    # --- Low ---
    {
        "chapter": "Ch1",
        "paragraph_index": 109,
        "dimension": "二.表达规范",
        "check_item": "2.G3 语义冗余",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "the results in this assessment report are bound to the given time constraints",
        "target_quote": "本评估报告中的所有结果均受限于给定的时间约束",
        "issue": "\"给定的时间约束\"中的"给定的"略显冗余，中文中"受限于时间约束"已足够表达",
        "suggestion": "可简化为"受限于时间约束""
    },
    {
        "chapter": "Ch1",
        "paragraph_index": 111,
        "dimension": "二.表达规范",
        "check_item": "2.13 被动语态直译",
        "severity": "low",
        "confidence": "medium",
        "source_quote": "attention is drawn to the limitation of liability, indemnification and jurisdiction issues defined therein",
        "target_quote": "提请注意其中定义的责任限制、赔偿和司法管辖问题",
        "issue": "\"提请注意\"是\"attention is drawn to\"的直译，中文正式文件中更自然的表达是"请注意"或"敬请留意"",
        "suggestion": "改为"敬请留意其中规定的责任限制、赔偿和司法管辖问题""
    },
]

# Write issues for batch 2
with open("cache/issues_phase4_2.json", "w", encoding="utf-8") as f:
    json.dump(issues_2, f, ensure_ascii=False, indent=2)
print(f"Batch 2 (SAR Tables): {len(issues_2)} issues written to cache/issues_phase4_2.json")

# Write issues for batch 3
with open("cache/issues_phase4_3.json", "w", encoding="utf-8") as f:
    json.dump(issues_3, f, ensure_ascii=False, indent=2)
print(f"Batch 3 (DSS Combined): {len(issues_3)} issues written to cache/issues_phase4_3.json")

# Count by severity
for label, issues in [("SAR Tables", issues_2), ("DSS Combined", issues_3)]:
    sev = {}
    for i in issues:
        sev[i["severity"]] = sev.get(i["severity"], 0) + 1
    print(f"  {label}: critical={sev.get('critical',0)}, medium={sev.get('medium',0)}, low={sev.get('low',0)}")
