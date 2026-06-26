"""
PDF 段落级翻译 — 分组段落 → API翻译 → 背景填充+插入中文
比行级翻译连贯性好很多，格式尽量保留
"""
import sys, io, os, json, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pymupdf
import httpx
from pathlib import Path

# ── API 配置 ──（优先环境变量，回退到 config.py）
API_KEY = os.environ.get('ANTHROPIC_AUTH_TOKEN', '')
BASE_URL = os.environ.get('ANTHROPIC_BASE_URL', '')
MODEL = os.environ.get('ANTHROPIC_MODEL', '')

if not API_KEY:
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))
        from config import load_config
        cfg = load_config()
        API_KEY = cfg.get('api_key', '')
        BASE_URL = cfg.get('base_url_override', '') or 'https://api.deepseek.com'
        MODEL = cfg.get('model', 'deepseek-chat')
    except Exception:
        BASE_URL = BASE_URL or 'https://api.deepseek.com/anthropic'
        MODEL = MODEL or 'deepseek-v4-flash'
else:
    BASE_URL = BASE_URL or 'https://api.deepseek.com/anthropic'
    MODEL = MODEL or 'deepseek-v4-flash'

# ── 缓存 ──
def text_key(text):
    return hashlib.sha256(text.strip().encode()).hexdigest()

def load_cache(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(path, cache):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)

def api_translate(texts, lang_in='en', lang_out='zh'):
    """分批调用 API 翻译段落"""
    BATCH = 30
    SEP = '\n<<<SEP>>>\n'
    cache = {}
    total = (len(texts) - 1) // BATCH + 1

    for bi in range(0, len(texts), BATCH):
        batch = texts[bi:bi+BATCH]
        bn = bi // BATCH + 1
        print(f'  Batch {bn}/{total}: translating {len(batch)} paragraphs...', end=' ', flush=True)
        combined = SEP.join(batch)
        try:
            resp = httpx.post(
                f'{BASE_URL}/v1/messages',
                headers={'x-api-key': API_KEY, 'anthropic-version': '2023-06-01',
                         'content-type': 'application/json'},
                json={
                    'model': MODEL, 'max_tokens': 8192, 'temperature': 0.1,
                    'system': f'你是专业翻译引擎。将以下{len(batch)}段文本逐段从{lang_in}翻译为{lang_out}。每段用"<<<SEP>>>"分隔。只输出译文，不解释。保留数字、符号、专有名词。',
                    'messages': [{'role': 'user', 'content': combined}]
                }, timeout=300
            )
            data = resp.json()
            blocks = [b for b in data.get('content', []) if b.get('type') == 'text']
            if blocks:
                results = [r.strip() for r in blocks[0]['text'].split(SEP)]
                for src, zh in zip(batch, results):
                    if zh and zh != src:
                        cache[text_key(src)] = zh
                print(f'OK ({len(results)} results)')
            else:
                print(f'no text block')
        except Exception as e:
            print(f'error: {e}')
    return cache

def group_into_paragraphs(page):
    """
    将页面中的文本块按行分组为段落。
    同一段内的行 y 间距小，不同段之间间距大。
    返回: [(paragraph_text, [line_bboxes], avg_font_size, avg_color), ...]
    """
    lines = []
    for b in page.get_text('dict')['blocks']:
        if b['type'] != 0:
            continue
        for l in b['lines']:
            text = ' '.join([s['text'] for s in l['spans']]).strip()
            if not text or len(text) <= 1:
                continue
            bbox = l['bbox']
            font_size = max(s['size'] for s in l['spans'])
            color = l['spans'][0]['color']
            font_name = l['spans'][0].get('font', '')
            flags = l['spans'][0].get('flags', 0)
            is_bold = bool(flags & 2) or 'bold' in font_name.lower()
            lines.append({
                'text': text,
                'bbox': bbox,
                'font_size': font_size,
                'color': color,
                'is_bold': is_bold,
            })

    if not lines:
        return []

    # 按 y 坐标分组（同一段的行 y 接近）
    GAP_THRESHOLD = 6  # 同一段内行间距阈值
    paragraphs = []
    current_para_lines = [lines[0]]

    for i in range(1, len(lines)):
        prev = lines[i-1]
        curr = lines[i]
        y_gap = curr['bbox'][1] - prev['bbox'][3]  # 当前行顶部 - 前行底部
        x_overlap = min(prev['bbox'][2], curr['bbox'][2]) - max(prev['bbox'][0], curr['bbox'][0])

        if y_gap < GAP_THRESHOLD and x_overlap > 10:
            # 同一段
            current_para_lines.append(curr)
        else:
            # 新段落
            paragraphs.append(current_para_lines)
            current_para_lines = [curr]

    if current_para_lines:
        paragraphs.append(current_para_lines)

    # 合并每个段落的文本和元数据
    result = []
    for para_lines in paragraphs:
        para_text = ' '.join([l['text'] for l in para_lines])
        # 段落整体的 bbox
        x0 = min(l['bbox'][0] for l in para_lines)
        y0 = min(l['bbox'][1] for l in para_lines)
        x1 = max(l['bbox'][2] for l in para_lines)
        y1 = max(l['bbox'][3] for l in para_lines)
        para_bbox = (x0, y0, x1, y1)
        avg_font_size = sum(l['font_size'] for l in para_lines) / len(para_lines)
        avg_color = para_lines[0]['color']
        is_bold = para_lines[0]['is_bold']

        result.append({
            'text': para_text,
            'bbox': para_bbox,
            'font_size': avg_font_size,
            'color': avg_color,
            'is_bold': is_bold,
        })

    return result

def sample_bg_color(page, bbox, margin=2):
    """采样文本区域左上角的背景色"""
    try:
        x0, y0, x1, y1 = bbox
        clip = pymupdf.Rect(max(0, x0-margin), max(0, y0-margin),
                            min(page.rect.width, x1+margin), min(page.rect.height, y1+margin))
        pix = page.get_pixmap(dpi=30, clip=clip)
        samples = pix.samples
        if len(samples) >= 3:
            r, g, b = samples[0], samples[1], samples[2]
            return (r << 16) | (g << 8) | b
    except:
        pass
    return 0xFFFFFF

# 全局中文字体（首次使用时初始化）
_CN_FONT = None
_CN_FONT_PATH = os.environ.get('WINDIR', '') + '/Fonts/simhei.ttf'

def get_cn_font(page):
    """确保页面注册了中文字体，返回字体名称字符串"""
    global _CN_FONT
    if _CN_FONT is None:
        try:
            _ = page.insert_font(fontname='SimHei', fontfile=_CN_FONT_PATH)
            _CN_FONT = 'SimHei'
        except:
            _CN_FONT = 'china-ss'
    else:
        try:
            page.insert_font(fontname='SimHei', fontfile=_CN_FONT_PATH)
        except:
            pass
    return _CN_FONT

def erase_and_insert(page, bbox, zh_text, font_size, color, is_bold):
    """擦除原文 + 插入中文，使用真实中文字体"""
    x0, y0, x1, y1 = bbox

    # 注册中文字体
    cn_font = get_cn_font(page)

    # 采样背景色并覆盖原文
    bg = sample_bg_color(page, bbox)
    cover_rect = pymupdf.Rect(x0-2, y0-2, x1+2, y1+2)
    shape = page.new_shape()
    shape.draw_rect(cover_rect)
    shape.finish(fill=pymupdf.sRGB_to_pdf(bg), color=None, width=0)
    shape.commit()

    # 字号自适应：中文更紧凑，可以略大
    en_len = (x1 - x0) / (font_size * 0.5)
    zh_len = len(zh_text)
    if en_len > 0 and zh_len > en_len * 0.6:
        adj_size = font_size * 0.88
    else:
        adj_size = font_size

    # 用 textbox 自动换行
    try:
        rc = page.insert_textbox(
            pymupdf.Rect(x0, y0-1, x1 + 25, y1 + font_size * 3),
            zh_text,
            fontname=cn_font,
            fontsize=adj_size,
            color=pymupdf.sRGB_to_pdf(color),
            align=0,
        )
        if rc < 0:
            page.insert_textbox(
                pymupdf.Rect(x0, y0-1, x1 + 50, y1 + font_size * 5),
                zh_text,
                fontname=cn_font,
                fontsize=adj_size * 0.78,
                color=pymupdf.sRGB_to_pdf(color),
                align=0,
            )
    except:
        page.insert_text(
            (x0, y1 - font_size * 0.15),
            zh_text,
            fontname=cn_font,
            fontsize=adj_size,
            color=pymupdf.sRGB_to_pdf(color),
        )

    # 粗体模拟：仅 SimHei 已有粗体，轻度叠加
    if is_bold:
        try:
            page.insert_text(
                (x0 + 0.35, y1 - font_size * 0.15),
                zh_text,
                fontname=cn_font,
                fontsize=adj_size,
                color=pymupdf.sRGB_to_pdf(color),
            )
        except:
            pass

def translate_pdf(input_path, output_path):
    print(f'\n{"="*60}')
    print(f'Translating: {input_path}')
    print(f'{"="*60}')

    doc = pymupdf.open(input_path)
    cache_dir = Path('cache')
    cache_path = cache_dir / (Path(input_path).stem + '_para_cache.json')
    cache = load_cache(str(cache_path))

    # ── 收集所有段落 ──
    all_paragraphs = {}  # text_key -> paragraph_info
    page_paragraphs = {}  # page_num -> [paragraph_info]

    for page_num in range(len(doc)):
        page = doc[page_num]
        paras = group_into_paragraphs(page)
        page_paragraphs[page_num] = paras
        for p in paras:
            k = text_key(p['text'])
            if k not in all_paragraphs:
                all_paragraphs[k] = p

    total_paras = len(all_paragraphs)
    print(f'Total unique paragraphs: {total_paras}')

    # ── 翻译未缓存的 ──
    pending = []
    for k, p in all_paragraphs.items():
        if k not in cache:
            pending.append((k, p['text']))

    if pending:
        print(f'Translating {len(pending)}/{total_paras} paragraphs via API...')
        new_translations = api_translate([t for _, t in pending])
        cache.update(new_translations)
        save_cache(str(cache_path), cache)
    else:
        print('All paragraphs already cached')

    # ── 渲染 PDF ──
    replaced = 0
    for page_num in range(len(doc)):
        page = doc[page_num]
        paras = page_paragraphs.get(page_num, [])

        for p in paras:
            k = text_key(p['text'])
            zh = cache.get(k)
            if not zh or zh == p['text']:
                continue

            erase_and_insert(page, p['bbox'], zh,
                           p['font_size'], p['color'], p['is_bold'])
            replaced += 1

        if (page_num + 1) % 10 == 0:
            print(f'  Rendered {page_num+1}/{len(doc)} pages ({replaced} replacements)')

    print(f'  Total: {replaced} paragraphs replaced')

    # ── 保存 ──
    output_dir = Path('output/pdf2zh')
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / (Path(input_path).stem + '_中文版.pdf')
    doc.save(str(out_path), garbage=4, deflate=True)
    doc.close()
    print(f'Saved: {out_path}\n')
    return str(out_path)

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='PDF段落级翻译')
    ap.add_argument('input', help='输入PDF')
    ap.add_argument('-o', '--output', default=None)
    args = ap.parse_args()

    output = args.output or f'output/pdf2zh/{Path(args.input).stem}_中文版.pdf'
    translate_pdf(args.input, output)
