"""
PDF翻译 v5 — 按行合并翻译，解决断句和间距问题
"""
import sys, io, json, os, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pymupdf, httpx
from tqdm import tqdm

API_KEY = os.environ.get('ANTHROPIC_AUTH_TOKEN', '')
BASE_URL = os.environ.get('ANTHROPIC_BASE_URL', 'https://api.deepseek.com/anthropic')
MODEL = os.environ.get('ANTHROPIC_MODEL', 'deepseek-v4-flash')

def text_key(text):
    return hashlib.md5(text.strip().encode()).hexdigest()[:12]

def load_cache(path):
    return json.load(open(path, 'r', encoding='utf-8')) if os.path.exists(path) else {}

def save_cache(path, cache):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)

def api_translate(texts):
    BATCH, SEP = 50, '\n<<<SEP>>>\n'
    cache = {}
    for i in tqdm(range(0, len(texts), BATCH), desc='API Translating', unit='batch'):
        batch = texts[i:i+BATCH]
        combined = SEP.join(batch)
        try:
            resp = httpx.post(
                f'{BASE_URL}/v1/messages',
                headers={'x-api-key': API_KEY, 'anthropic-version': '2023-06-01',
                         'content-type': 'application/json'},
                json={'model': MODEL, 'max_tokens': 8192, 'temperature': 0.1,
                      'system': f'逐条翻译{len(batch)}条文本为简体中文。每条译文用"<<<SEP>>>"分隔。只输出译文。保留数字、符号、专有名词。',
                      'messages': [{'role': 'user', 'content': combined}]},
                timeout=300)
            data = resp.json()
            blocks = [b for b in data.get('content', []) if b.get('type') == 'text']
            if blocks:
                results = [r.strip() for r in blocks[0]['text'].split(SEP)]
                for src, zh in zip(batch, results):
                    if zh and zh != src:
                        cache[text_key(src)] = zh
        except Exception as e:
            tqdm.write(f'  API error: {e}')
    return cache

def translate_pdf(input_path, output_path):
    print(f'Input: {input_path}')
    doc = pymupdf.open(input_path)
    cache_path = os.path.join(os.path.dirname(input_path) or '.',
        os.path.basename(input_path).rsplit('.', 1)[0] + '_cache.json')
    cache = load_cache(cache_path)

    # ── 按行收集文本 ──
    all_lines = set()
    for page in doc:
        for b in page.get_text('dict')['blocks']:
            if b['type'] != 0: continue
            for l in b['lines']:
                line_text = ' '.join([s['text'] for s in l['spans']]).strip()
                if line_text and len(line_text) > 1:
                    all_lines.add(line_text)

    print(f'Unique lines: {len(all_lines)}')

    # ── API翻译 ──
    pending = [t for t in all_lines if text_key(t) not in cache]
    if pending:
        print(f'Translating {len(pending)} lines via API...')
        cache.update(api_translate(pending))
        save_cache(cache_path, cache)
    else:
        print('All lines cached')

    # ── 按行原位替换 ──
    replaced = 0
    for page_num in tqdm(range(len(doc)), desc='Rendering PDF', unit='page'):
        page = doc[page_num]
        for b in page.get_text('dict')['blocks']:
            if b['type'] != 0: continue
            for l in b['lines']:
                # 合并整行文本
                line_text = ' '.join([s['text'] for s in l['spans']]).strip()
                if not line_text or len(line_text) <= 1: continue

                k = text_key(line_text)
                zh = cache.get(k)
                if not zh or zh == line_text: continue

                # 用行边界框
                bbox = l['bbox']
                # 取第一个span的字号作为参考
                font_size = l['spans'][0]['size']
                color = l['spans'][0]['color']
                font_name = l['spans'][0].get('font', '')
                flags = l['spans'][0].get('flags', 0)
                is_bold = bool(flags & 2) or 'bold' in font_name.lower()

                # 无填充redact整行
                page.add_redact_annot(bbox)
                page.apply_redactions()

                # 字号适配
                ratio = len(zh) / max(len(line_text), 1)
                adj = font_size * 0.85 if ratio > 1.5 else font_size

                # 插入整行中文
                pos = (bbox[0], bbox[3] - font_size * 0.15)
                page.insert_text(pos, zh, fontname='china-ss', fontsize=adj,
                                 color=pymupdf.sRGB_to_pdf(color))
                if is_bold:
                    page.insert_text((pos[0]+0.3, pos[1]), zh, fontname='china-ss',
                                     fontsize=adj, color=pymupdf.sRGB_to_pdf(color))
                replaced += 1

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    print(f'Saved: {output_path} ({replaced} lines replaced)')
    return output_path

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='PDF翻译 v5 - 按行翻译解决断句间距')
    ap.add_argument('input')
    ap.add_argument('-o', '--output', default=None)
    args = ap.parse_args()
    translate_pdf(args.input, args.output or args.input.rsplit('.',1)[0]+'_中文版.pdf')
