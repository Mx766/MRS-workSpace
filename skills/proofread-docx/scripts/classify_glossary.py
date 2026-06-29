#!/usr/bin/env python3
"""
术语库领域自动分类。

基于中英文关键词规则，将"通用"术语自动归入医学子领域。
未匹配任何规则的术语保留"通用"标记。

用法:
  python classify_glossary.py --glossary cache/glossary.json --output cache/glossary_classified.json
  python classify_glossary.py --glossary cache/glossary.json --output cache/glossary_classified.json --dry-run
"""

import argparse, json, sys
from collections import Counter
from pathlib import Path

# ── 领域定义 ──
# 格式: (领域名, [(权重, 关键词), ...])
# 权重: 3=强信号(几乎确定), 2=中等信号, 1=弱信号
# 匹配阈值: 总分 >= 3 则归类

DOMAIN_RULES = {
    '医学-影像': {
        'en': [
            (3, 'mri'), (3, 'magnetic resonance'), (3, 'spin echo'), (3, 'gradient echo'),
            (3, 't1-weighted'), (3, 't2-weighted'), (3, 'pulse sequence'), (3, 'echo time'),
            (3, 'repetition time'), (3, 'flip angle'), (3, 'k-space'), (3, 'field of view'),
            (2, 'imaging'), (2, 'b-scan'), (2, 'a-scan'), (2, 'tomography'),
            (2, 'ultrasound'), (2, 'sonograph'), (2, 'doppler'),
            (2, 'x-ray'), (2, 'radiograph'), (2, 'fluoroscopy'),
            (1, 'scan'), (1, 'image'), (1, 'signal intensity'), (1, 'contrast'),
            (1, 'resolution'), (1, 'slice'), (1, 'reconstruction'),
            (1, 'artifact'), (1, 'aliasing'), (1, 'truncation'),
            (1, 'fourier'), (1, '2dft'), (1, 'spectroscopy'),
        ],
        'zh': [
            (3, '磁共振'), (3, '自旋回波'), (3, '梯度回波'), (3, 'T1加权'), (3, 'T2加权'),
            (3, '脉冲序列'), (3, 'K空间'), (3, '视野'), (3, '傅里叶变换'),
            (2, '成像'), (2, '扫描'), (2, '断层'), (2, '超声'), (2, '多普勒'),
            (2, 'X射线'), (2, '放射'), (2, '荧光透视'),
            (1, '回波'), (1, '信噪比'), (1, '伪影'), (1, '空间分辨'),
            (1, '对比度'), (1, '层厚'), (1, '重建'), (1, '波谱'),
        ],
    },
    '医学-器械': {
        'en': [
            (3, 'gauge'), (3, 'cannula'), (3, 'trocar'), (3, 'handpiece'),
            (3, 'light pipe'), (3, 'knife assembly'), (3, 'infusion'),
            (3, 'stopcock'), (3, 'catheter'), (3, 'syringe'), (3, 'needle'),
            (2, 'probe'), (2, 'fiber'), (2, 'laser'), (2, 'optical'),
            (2, 'endoscope'), (2, 'surgical'), (2, 'assembly'),
            (2, 'connector'), (2, 'adapter'), (2, 'tubing'),
            (1, 'instrument'), (1, 'device'), (1, 'equipment'),
            (1, 'g'), (1, 'mm'), (1, 'cm'),
        ],
        'zh': [
            (3, '套管'), (3, '穿刺器'), (3, '手柄'), (3, '导管'),
            (3, '注射器'), (3, '缝合'), (3, '手术器械'),
            (2, '探头'), (2, '光纤'), (2, '内窥镜'), (2, '光源'),
            (2, '接头'), (2, '适配器'), (2, '管路'),
            (1, '装置'), (1, '设备'), (1, '仪器'),
            (1, 'Ga'), (1, 'G'),
        ],
    },
    '医学-药物': {
        'en': [
            (3, 'injection'), (3, 'solution'), (3, 'suspension'),
            (3, 'tablet'), (3, 'capsule'), (3, 'oral'),
            (3, 'dose'), (3, 'mg'), (3, 'ml'), (3, 'concentration'),
            (3, 'intravenous'), (3, 'subcutaneous'), (3, 'topical'),
            (2, 'pharmac'), (2, 'drug'), (2, 'medication'),
            (2, 'formulation'), (2, 'excipient'),
            (1, 'agent'), (1, 'compound'), (1, 'sodium'),
            (1, 'chloride'), (1, 'acid'),
        ],
        'zh': [
            (3, '注射液'), (3, '片剂'), (3, '胶囊'), (3, '口服'),
            (3, '剂量'), (3, '浓度'), (3, '静脉'), (3, '皮下'),
            (2, '溶液'), (2, '悬浮液'), (2, '配方'),
            (1, '钠'), (1, '氯化'), (1, '酸'), (1, '盐'),
        ],
    },
    '医学-临床试验': {
        'en': [
            (3, 'clinical trial'), (3, 'endpoint'), (3, 'efficacy'),
            (3, 'cohort'), (3, 'randomiz'), (3, 'placebo'),
            (3, 'informed consent'), (3, 'inclusion criteria'),
            (3, 'exclusion criteria'), (3, 'adverse event'),
            (2, 'protocol'), (2, 'investigat'), (2, 'subject'),
            (2, 'enrollment'), (2, 'baseline'), (2, 'follow-up'),
            (2, 'outcome'), (2, 'responder'), (2, 'arm'),
            (1, 'study'), (1, 'trial'), (1, 'assessment'),
            (1, 'evaluat'), (1, 'monitor'), (1, 'safety'),
        ],
        'zh': [
            (3, '临床试验'), (3, '终点'), (3, '疗效'), (3, '队列'),
            (3, '随机'), (3, '安慰剂'), (3, '知情同意'),
            (3, '入组标准'), (3, '排除标准'), (3, '不良事件'),
            (2, '方案'), (2, '受试者'), (2, '基线'), (2, '随访'),
            (2, '结局'), (2, '有效性'), (2, '安全性'),
            (1, '研究'), (1, '评估'),
        ],
    },
    '医学-实验室': {
        'en': [
            (3, 'electrophoresis'), (3, 'assay'), (3, 'reagent'),
            (3, 'buffer'), (3, 'stain'), (3, 'culture'),
            (3, 'antibod'), (3, 'antigen'), (3, 'elisa'),
            (3, 'pcr'), (3, 'western blot'), (3, 'immunohistochem'),
            (2, 'enzyme'), (2, 'substrate'), (2, 'incubate'),
            (2, 'centrifuge'), (2, 'pipette'), (2, 'specimen'),
            (2, 'serum'), (2, 'plasma'), (2, 'biopsy'),
            (1, 'laboratory'), (1, 'lab'), (1, 'test'),
            (1, 'detect'), (1, 'measure'),
        ],
        'zh': [
            (3, '电泳'), (3, '测定'), (3, '试剂'), (3, '缓冲液'),
            (3, '染色'), (3, '培养'), (3, '抗体'), (3, '抗原'),
            (2, '酶'), (2, '底物'), (2, '孵育'), (2, '离心'),
            (2, '标本'), (2, '血清'), (2, '血浆'), (2, '活检'),
            (1, '检测'), (1, '测量'),
        ],
    },
    '医学-解剖': {
        'en': [
            (3, 'artery'), (3, 'vein'), (3, 'nerve'), (3, 'muscle'),
            (3, 'bone'), (3, 'tendon'), (3, 'ligament'),
            (3, 'cartilage'), (3, 'fascia'), (3, 'dermis'),
            (3, 'epidermis'), (3, 'subcutaneous tissue'),
            (2, 'vessel'), (2, 'tissue'), (2, 'organ'),
            (2, 'gland'), (2, 'duct'), (2, 'follicle'),
            (2, 'cavity'), (2, 'membrane'),
            (1, 'skin'), (1, 'cell'), (1, 'layer'),
            (1, 'anterior'), (1, 'posterior'), (1, 'lateral'), (1, 'medial'),
        ],
        'zh': [
            (3, '动脉'), (3, '静脉'), (3, '神经'), (3, '肌肉'),
            (3, '骨骼'), (3, '肌腱'), (3, '韧带'), (3, '软骨'),
            (3, '筋膜'), (3, '真皮'), (3, '表皮'), (3, '皮下组织'),
            (2, '血管'), (2, '组织'), (2, '器官'),
            (2, '腺体'), (2, '导管'), (2, '毛囊'),
            (2, '腔'), (2, '膜'),
            (1, '皮肤'), (1, '细胞'),
        ],
    },
    '医学-手术': {
        'en': [
            (3, 'resection'), (3, 'incision'), (3, 'excision'),
            (3, 'suture'), (3, 'implant'), (3, 'graft'),
            (3, 'transplant'), (3, 'puncture'), (3, 'biopsy'),
            (2, 'dissection'), (2, 'ablation'), (2, 'coagulation'),
            (2, 'anastomosis'), (2, 'ligation'),
            (1, 'surgery'), (1, 'procedure'), (1, 'operative'),
            (1, 'remove'), (1, 'repair'),
        ],
        'zh': [
            (3, '切除术'), (3, '切开'), (3, '缝合'), (3, '植入'),
            (3, '移植'), (3, '穿刺'), (3, '吻合'),
            (2, '剥离'), (2, '消融'), (2, '凝固'), (2, '结扎'),
            (1, '手术'), (1, '操作'),
        ],
    },
    '医学-皮肤美容': {
        'en': [
            (3, 'collagen'), (3, 'elastin'), (3, 'rejuvenation'),
            (3, 'wrinkle'), (3, 'rhytid'), (3, 'pigmentation'),
            (3, 'melasma'), (3, 'freckle'), (3, 'lentigo'),
            (3, 'hair removal'), (3, 'photo'), (3, 'ipl'),
            (3, 'radiofrequency'), (3, 'microneedling'),
            (3, 'neocollagenesis'), (3, 'fibroblast'),
            (2, 'laser'), (2, 'peel'), (2, 'filler'),
            (2, 'botulinum'), (2, 'toxin'), (2, 'hyaluronic'),
            (2, 'aesthetic'), (2, 'cosmetic'), (2, 'dermatolog'),
            (2, 'epidermal'), (2, 'dermal'),
            (2, 'tightening'), (2, 'lifting'), (2, 'contouring'),
            (2, 'scar'), (2, 'pore'), (2, 'texture'),
            (1, 'skin'), (1, 'face'), (1, 'facial'),
            (1, 'tone'), (1, 'treat'),
        ],
        'zh': [
            (3, '胶原蛋白'), (3, '弹性蛋白'), (3, '嫩肤'), (3, '除皱'),
            (3, '色斑'), (3, '黄褐斑'), (3, '雀斑'), (3, '光子'),
            (3, '射频'), (3, '微针'), (3, '脱毛'),
            (3, '新胶原生成'), (3, '成纤维细胞'),
            (2, '激光'), (2, '焕肤'), (2, '填充剂'),
            (2, '肉毒'), (2, '透明质酸'),
            (2, '美容'), (2, '皮肤科'),
            (2, '紧致'), (2, '提升'), (2, '塑形'),
            (2, '疤痕'), (2, '毛孔'),
            (1, '皮肤'), (1, '面部'),
            (1, '治疗'),
        ],
    },
    '医学-不良反应': {
        'en': [
            (3, 'edema'), (3, 'erythema'), (3, 'pruritus'),
            (3, 'ecchymosis'), (3, 'hematoma'), (3, 'purpura'),
            (3, 'blister'), (3, 'crust'), (3, 'hyperpigmentation'),
            (3, 'hypopigmentation'), (3, 'infection'),
            (2, 'pain'), (2, 'swelling'), (2, 'burning'),
            (2, 'tingling'), (2, 'numbness'), (2, 'discomfort'),
            (2, 'irritation'), (2, 'rash'), (2, 'allerg'),
            (1, 'side effect'), (1, 'complication'), (1, 'adverse'),
            (1, 'transient'), (1, 'temporary'), (1, 'resolved'),
        ],
        'zh': [
            (3, '水肿'), (3, '红斑'), (3, '瘙痒'), (3, '瘀斑'),
            (3, '血肿'), (3, '紫癜'), (3, '水疱'), (3, '结痂'),
            (3, '色素沉着'), (3, '色素减退'), (3, '感染'),
            (2, '疼痛'), (2, '肿胀'), (2, '烧灼感'), (2, '刺痛'),
            (2, '麻木'), (2, '不适'), (2, '刺激'), (2, '皮疹'),
            (2, '过敏'),
            (1, '副作用'), (1, '并发症'), (1, '一过性'), (1, '消退'),
        ],
    },
    '医学-治疗': {
        'en': [
            (3, 'therapy'), (3, 'treatment regimen'),
            (2, 'treatment'), (2, 'management'), (2, 'intervention'),
            (2, 'rehabilitation'), (2, 'physical therapy'),
            (1, 'care'), (1, 'approach'), (1, 'strategy'),
        ],
        'zh': [
            (3, '治疗方案'), (2, '治疗'), (2, '管理'), (2, '干预'),
            (2, '康复'), (1, '护理'),
        ],
    },
}


def classify_term(source: str, target: str) -> tuple[str, int, str]:
    """
    基于中英文关键词对术语进行领域分类。
    返回: (domain_name, score, matched_keywords_summary)
    """
    source_lower = source.lower()
    target_lower = target.lower()

    best_domain = '通用'
    best_score = 0
    best_reason = ''

    for domain, rules in DOMAIN_RULES.items():
        score = 0
        reasons = []

        # 英文关键词
        for weight, keyword in rules.get('en', []):
            if keyword.lower() in source_lower:
                score += weight
                reasons.append(f'en:{keyword}({weight})')

        # 中文关键词
        for weight, keyword in rules.get('zh', []):
            if keyword.lower() in target_lower:
                score += weight
                reasons.append(f'zh:{keyword}({weight})')

        if score > best_score:
            best_score = score
            best_domain = domain
            best_reason = '; '.join(reasons[:5])  # top 5 signals

    # Only classify if confidence threshold met
    if best_score >= 3:
        return best_domain, best_score, best_reason
    return '通用', best_score, best_reason


def main():
    parser = argparse.ArgumentParser(description='术语库领域自动分类')
    parser.add_argument('--glossary', '-g', required=True, help='术语库 JSON 文件')
    parser.add_argument('--output', '-o', required=True, help='输出 JSON 路径')
    parser.add_argument('--dry-run', action='store_true', help='仅统计，不改变文件')
    args = parser.parse_args()

    data = json.loads(Path(args.glossary).read_text(encoding='utf-8'))
    terms = data.get('terms', {})

    before = Counter(t.get('domain', '通用') for t in terms.values())
    changed = 0
    by_domain = Counter()

    for key, term in terms.items():
        old_domain = term.get('domain', '通用')
        if old_domain == '通用':
            new_domain, score, reason = classify_term(term['source'], term['target'])
            if new_domain != '通用':
                if not args.dry_run:
                    term['domain'] = new_domain
                changed += 1
                by_domain[new_domain] += 1
        else:
            by_domain[old_domain] += 1

    by_domain['通用'] = len(terms) - changed - sum(
        v for k, v in by_domain.items() if k != '通用')
    by_domain['通用'] = max(0, by_domain['通用'])

    print(f'总术语数: {len(terms)}')
    print(f'自动分类: {changed} 条 ({100*changed/len(terms):.1f}%)')
    print()
    print('分类后领域分布:')
    for domain, count in by_domain.most_common():
        pct = 100 * count / len(terms)
        bar = '█' * int(pct / 2)
        print(f'  {domain:20s}: {count:5d} ({pct:4.1f}%) {bar}')

    if not args.dry_run:
        # Update metadata
        data['_classified_at'] = '2026-06-29'
        data['_classified_count'] = changed
        Path(args.output).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8')
        print(f'\n已写入: {args.output}')
    else:
        print('\n(dry-run, 未写入文件)')


if __name__ == '__main__':
    main()
