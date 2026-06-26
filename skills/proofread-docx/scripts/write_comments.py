#!/usr/bin/env python3
"""
Phase 6: 批注写入（v2 — 真正的 OOXML Comment）
通过 ZIP + lxml 直接操作 OOXML，添加真正的 Word 批注。
正文内容一字不改，批注以 Word 原生 Comment 形式出现在右侧边距。
"""

import argparse
import json
import shutil
import zipfile
import io
import os
import re
from pathlib import Path
from datetime import datetime

# OOXML 命名空间
NSMAP = {
    'w':   'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r':   'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'mc':  'http://schemas.openxmlformats.org/markup-compatibility/2006',
    'w14': 'http://schemas.microsoft.com/office/word/2010/wordml',
    'wp':  'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a':   'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
}

COMMENTS_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments'
CONTENT_TYPE_COMMENTS = 'application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml'
DOCUMENT_RELS_PATH = 'word/_rels/document.xml.rels'
CONTENT_TYPES_PATH = '[Content_Types].xml'
DOCUMENT_PATH = 'word/document.xml'
COMMENTS_PATH = 'word/comments.xml'


def write_word_comments(filepath: str, issues: list[dict], output_path: str = None) -> dict:
    """混合方案：python-docx 负责高亮 + 保存；lxml+ZIP 负责注入批注。
    python-docx 保存确保高亮可靠渲染，ZIP 层注入 comments.xml 实现原生批注。"""
    try:
        from lxml import etree
        from docx import Document
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
    except ImportError as e:
        return {'status': 'error', 'message': f'缺少依赖: {e}'}

    output = output_path or filepath.replace('.docx', '_校对稿.docx')

    # ═══ 第 1 步: python-docx 打开文档，加高亮 + 批注引用标记 ═══
    doc = Document(filepath)

    highlight_colors = {
        'critical': ('FFCCCC', 'red'),
        'medium': ('FFF9C4', 'yellow'),
        'low': ('C8E6C9', 'green'),
    }

    # 按段落索引分组，按严重度排序
    issues_by_para = {}
    for issue in issues:
        pi = issue.get('paragraph_index', 0)
        if pi < 1:
            continue
        if pi not in issues_by_para:
            issues_by_para[pi] = []
        issues_by_para[pi].append(issue)

    severity_order = {'critical': 0, 'medium': 1, 'low': 2}
    comments_added = 0
    comment_id = 0
    para_count = len(doc.paragraphs)

    # 准备 comments.xml
    comments_tree = etree.Element(f'{{{NSMAP["w"]}}}comments',
                                  nsmap={None: NSMAP['w']})

    for para_idx in sorted(issues_by_para.keys()):
        if para_idx > para_count:
            continue
        para = doc.paragraphs[para_idx - 1]
        sorted_issues = sorted(issues_by_para[para_idx],
                               key=lambda x: severity_order.get(x.get('severity', 'medium'), 1))

        for issue in sorted_issues:
            severity = issue.get('severity', 'medium')
            fill_color, hl_name = highlight_colors.get(severity, ('FFFF00', 'yellow'))
            target_quote = issue.get('target_quote', '').strip()
            date_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

            severity_label = {
                'critical': '🔴 严重（必须修改）',
                'medium': '🟡 中等（建议修改）',
                'low': '🟢 低（格式优化）',
            }.get(severity, '⚪ 未分级')

            # --- A. 高亮匹配的 run（python-docx OxmlElement） ---
            if target_quote:
                for run in para.runs:
                    if not run.text.strip():
                        continue
                    if target_quote[:40] in run.text or run.text in target_quote:
                        rPr = run._r.get_or_add_rPr()
                        # 已有底色就跳过（更严重的先处理）
                        if rPr.find(qn('w:shd')) is not None:
                            continue
                        shd = OxmlElement('w:shd')
                        shd.set(qn('w:val'), 'clear')
                        shd.set(qn('w:color'), 'auto')
                        shd.set(qn('w:fill'), fill_color)
                        rPr.append(shd)
                        hl = OxmlElement('w:highlight')
                        hl.set(qn('w:val'), hl_name)
                        rPr.append(hl)

            # --- B. 添加 commentRange + commentReference（lxml） ---
            crs = etree.Element(f'{{{NSMAP["w"]}}}commentRangeStart')
            crs.set(f'{{{NSMAP["w"]}}}id', str(comment_id))
            # 插在 pPr 之后（如果有的话）
            pPr = para._element.find(f'{{{NSMAP["w"]}}}pPr')
            if pPr is not None:
                pPr.addnext(crs)
            else:
                para._element.insert(0, crs)

            cre = etree.Element(f'{{{NSMAP["w"]}}}commentRangeEnd')
            cre.set(f'{{{NSMAP["w"]}}}id', str(comment_id))
            para._element.append(cre)

            ref_run = etree.SubElement(para._element, f'{{{NSMAP["w"]}}}r')
            ref_rPr = etree.SubElement(ref_run, f'{{{NSMAP["w"]}}}rPr')
            cr = etree.SubElement(ref_rPr, f'{{{NSMAP["w"]}}}commentReference')
            cr.set(f'{{{NSMAP["w"]}}}id', str(comment_id))

            # --- C. 创建 comments.xml 条目 ---
            cmt = etree.SubElement(comments_tree, f'{{{NSMAP["w"]}}}comment')
            cmt.set(f'{{{NSMAP["w"]}}}id', str(comment_id))
            cmt.set(f'{{{NSMAP["w"]}}}author', 'TranslationReview')
            cmt.set(f'{{{NSMAP["w"]}}}date', date_str)
            cmt.set(f'{{{NSMAP["w"]}}}initials', 'TR')

            comment_texts = [
                f'{severity_label}',
                f'【{issue.get("dimension", "")} — {issue.get("check_item", "")}】',
                f'',
                f'原文: {issue.get("source_quote", "")}',
                f'',
                f'问题: {issue.get("issue", "")}',
                f'',
                f'建议: {issue.get("suggestion", "")}',
            ]
            for i, line in enumerate(comment_texts):
                p_elem = etree.SubElement(cmt, f'{{{NSMAP["w"]}}}p')
                pPr_e = etree.SubElement(p_elem, f'{{{NSMAP["w"]}}}pPr')
                if i == 0:
                    rPr_t = etree.SubElement(pPr_e, f'{{{NSMAP["w"]}}}rPr')
                    b_e = etree.SubElement(rPr_t, f'{{{NSMAP["w"]}}}b')
                    sz_e = etree.SubElement(rPr_t, f'{{{NSMAP["w"]}}}sz')
                    sz_e.set(f'{{{NSMAP["w"]}}}val', '18')
                    color_e = etree.SubElement(rPr_t, f'{{{NSMAP["w"]}}}color')
                    color_e.set(f'{{{NSMAP["w"]}}}val',
                                {'critical': 'FF0000', 'medium': 'FF8C00', 'low': '228B22'}.get(severity, '000000'))
                r_e = etree.SubElement(p_elem, f'{{{NSMAP["w"]}}}r')
                t_e = etree.SubElement(r_e, f'{{{NSMAP["w"]}}}t')
                t_e.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
                t_e.text = line

            comment_id += 1
            comments_added += 1

    # ═══ 第 2 步: python-docx 保存到临时文件 ═══
    import tempfile
    tmpfd, tmppath = tempfile.mkstemp(suffix='.docx')
    os.close(tmpfd)
    doc.save(tmppath)

    # ═══ 第 3 步: ZIP 层注入 comments.xml（保留原条目压缩方式和元数据） ═══
    # 序列化 comments
    comments_xml = etree.tostring(comments_tree, xml_declaration=True, encoding='UTF-8',
                                   standalone=True)

    # 读取 rels 和 content types 原始内容
    with zipfile.ZipFile(tmppath, 'r') as zf_in:
        rels_raw = zf_in.read(DOCUMENT_RELS_PATH) if DOCUMENT_RELS_PATH in zf_in.namelist() else None
        ct_raw = zf_in.read(CONTENT_TYPES_PATH) if CONTENT_TYPES_PATH in zf_in.namelist() else None

    # 处理 rels
    if rels_raw:
        rels_tree = etree.fromstring(rels_raw)
    else:
        rels_tree = etree.Element(
            '{http://schemas.openxmlformats.org/package/2006/relationships}Relationships')
    max_rid = 0
    existing = False
    for rel in rels_tree:
        rid = rel.get('Id', '')
        m = re.match(r'rId(\d+)', rid)
        if m:
            max_rid = max(max_rid, int(m.group(1)))
        if rel.get('Type') == COMMENTS_NS:
            existing = True
    if not existing:
        new_rel = etree.SubElement(rels_tree, 'Relationship')
        new_rel.set('Id', f'rId{max_rid + 1}')
        new_rel.set('Type', COMMENTS_NS)
        new_rel.set('Target', 'comments.xml')
    new_rels_xml = etree.tostring(rels_tree, xml_declaration=True, encoding='UTF-8',
                                   standalone=True)

    # 处理 content types
    if ct_raw:
        ct_tree = etree.fromstring(ct_raw)
    else:
        ct_tree = etree.Element(
            '{http://schemas.openxmlformats.org/package/2006/content-types}Types')
    existing_ct = False
    for ov in ct_tree:
        if ov.get('PartName') == f'/{COMMENTS_PATH}':
            existing_ct = True
            break
    if not existing_ct:
        new_ct = etree.SubElement(ct_tree,
            '{http://schemas.openxmlformats.org/package/2006/content-types}Override')
        new_ct.set('PartName', f'/{COMMENTS_PATH}')
        new_ct.set('ContentType', CONTENT_TYPE_COMMENTS)
    new_ct_xml = etree.tostring(ct_tree, xml_declaration=True, encoding='UTF-8',
                                 standalone=True)

    # 写回 ZIP：用 ZipInfo 保留每个条目的压缩方式
    with zipfile.ZipFile(tmppath, 'r') as zf_in:
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf_out:
            for info in zf_in.infolist():
                if info.filename == DOCUMENT_RELS_PATH:
                    zf_out.writestr(info, new_rels_xml)
                elif info.filename == CONTENT_TYPES_PATH:
                    zf_out.writestr(info, new_ct_xml)
                elif info.filename == COMMENTS_PATH:
                    # 原文件可能已有 comments.xml，跳过，后面写入新版本
                    pass
                else:
                    zf_out.writestr(info, zf_in.read(info.filename))
            # 写入新的 comments.xml
            zf_out.writestr(COMMENTS_PATH, comments_xml)

    # 清理临时文件
    try:
        os.unlink(tmppath)
    except Exception:
        pass

    return {
        'status': 'ok',
        'output': str(Path(output).resolve()),
        'comments_added': comments_added,
        'format': 'docx',
    }


# ═══════════════════════════════════════════════════════════
# Excel 批注（不变）
# ═══════════════════════════════════════════════════════════

SEVERITY_COLORS = {
    'critical': {'hex': 'FF0000', 'highlight': 'FFCCCC', 'label': '严重'},
    'medium':    {'hex': 'FF8C00', 'highlight': 'FFF9C4', 'label': '中等'},
    'low':       {'hex': '228B22', 'highlight': 'C8E6C9', 'label': '低'},
}


def write_excel_comments(filepath: str, issues: list[dict], output_path: str = None) -> dict:
    """将疑点写入 Excel 的 Comment 和单元格填充色"""
    try:
        import openpyxl
        from openpyxl.comments import Comment
        from openpyxl.styles import PatternFill
    except ImportError:
        return {'status': 'error', 'message': '需要 openpyxl: pip install openpyxl'}

    wb = openpyxl.load_workbook(filepath)
    comments_added = 0

    for issue in issues:
        severity = issue.get('severity', 'medium')
        color_info = SEVERITY_COLORS.get(severity, SEVERITY_COLORS['medium'])

        sheet_name = issue.get('sheet', wb.sheetnames[0])
        row = issue.get('row', 1)
        col = issue.get('col', 1)

        if sheet_name not in wb.sheetnames:
            continue

        ws = wb[sheet_name]
        cell = ws.cell(row=row, column=col)

        try:
            fill = PatternFill(
                start_color=color_info['highlight'],
                end_color=color_info['highlight'],
                fill_type='solid'
            )
            cell.fill = fill
        except Exception:
            pass

        lines = [
            f'[{color_info["label"]}] {issue.get("dimension", "")} - {issue.get("check_item", "")}',
            f'原文: {issue.get("source_quote", "")}',
            f'译文: {issue.get("target_quote", "")}',
            f'问题: {issue.get("issue", "")}',
            f'建议: {issue.get("suggestion", "")}',
        ]
        comment_text = '\n'.join(lines)

        try:
            comment = Comment(comment_text, 'TranslationReview')
            comment.width = 400
            comment.height = 200
            cell.comment = comment
            comments_added += 1
        except Exception:
            pass

    # 在第一个 Sheet 添加图例行
    try:
        ws = wb[wb.sheetnames[0]]
        ws.insert_rows(1, 4)
        ws.cell(row=1, column=1, value='翻译校对批注 — 颜色说明')
        ws.cell(row=2, column=1, value='红色 = 严重 | 橙色 = 中等 | 绿色 = 低')
        critical_fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
        medium_fill = PatternFill(start_color='FFF9C4', end_color='FFF9C4', fill_type='solid')
        low_fill = PatternFill(start_color='C8E6C9', end_color='C8E6C9', fill_type='solid')
        ws.cell(row=3, column=1).fill = critical_fill
        ws.cell(row=4, column=1).fill = medium_fill
    except Exception:
        pass

    output = output_path or filepath.replace('.xlsx', '_校对稿.xlsx')
    wb.save(output)

    return {
        'status': 'ok',
        'output': str(Path(output).resolve()),
        'comments_added': comments_added,
        'format': 'xlsx',
    }


# ═══════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='批注写入')
    parser.add_argument('--input', '-i', required=True, help='译文文件路径')
    parser.add_argument('--issues', required=True, help='疑点 JSON 文件路径')
    parser.add_argument('--output', '-o', help='输出文件路径')
    args = parser.parse_args()

    issues_data = json.loads(Path(args.issues).read_text(encoding='utf-8'))

    if isinstance(issues_data, list):
        issues = issues_data
    elif isinstance(issues_data, dict):
        issues = issues_data.get('issues', issues_data.get('findings', []))
    else:
        issues = []

    suffix = Path(args.input).suffix.lower()
    if suffix == '.docx':
        result = write_word_comments(args.input, issues, args.output)
    elif suffix in ('.xlsx', '.xls'):
        result = write_excel_comments(args.input, issues, args.output)
    else:
        result = {'status': 'error', 'message': f'不支持的文件类型: {suffix}'}

    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
