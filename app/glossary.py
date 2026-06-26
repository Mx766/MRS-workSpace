"""
术语库管理 — SQLite + Excel导入 + 搜索 + 导出CSV
"""
import sqlite3, os, csv, io, re

DB_FILE = os.path.join(os.path.dirname(__file__), '..', 'glossary.db')

def get_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute('''CREATE TABLE IF NOT EXISTS terms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        target TEXT NOT NULL,
        domain TEXT DEFAULT '通用',
        note TEXT DEFAULT '',
        is_regex INTEGER DEFAULT 0,
        case_sensitive INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_source ON terms(source)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_domain ON terms(domain)')
    conn.commit()
    return conn

# ── 查询 ──
def search_terms(query='', domain='', page=1, page_size=50):
    db = get_db()
    where, params = [], []
    if query:
        where.append('(source LIKE ? OR target LIKE ?)')
        params.extend([f'%{query}%', f'%{query}%'])
    if domain and domain != '全部':
        where.append('domain = ?')
        params.append(domain)
    w = ('WHERE ' + ' AND '.join(where)) if where else ''
    total = db.execute(f'SELECT COUNT(*) FROM terms {w}', params).fetchone()[0]
    rows = db.execute(f'SELECT * FROM terms {w} ORDER BY id DESC LIMIT ? OFFSET ?',
                      params + [page_size, (page-1)*page_size]).fetchall()
    return [dict(r) for r in rows], total

def get_all_domains():
    db = get_db()
    return [r[0] for r in db.execute('SELECT DISTINCT domain FROM terms ORDER BY domain').fetchall()]

def add_term(source, target, domain='通用', note='', is_regex=0, case_sensitive=0):
    db = get_db()
    # 去重检查
    exist = db.execute('SELECT id FROM terms WHERE source=? AND target=?', (source.strip(), target.strip())).fetchone()
    if exist:
        return False, f'术语 "{source}" → "{target}" 已存在'
    db.execute('INSERT INTO terms (source,target,domain,note,is_regex,case_sensitive) VALUES (?,?,?,?,?,?)',
               (source.strip(), target.strip(), domain, note, is_regex, case_sensitive))
    db.commit()
    return True, '添加成功'

def delete_term(term_id):
    db = get_db()
    db.execute('DELETE FROM terms WHERE id=?', (term_id,))
    db.commit()

def update_term(term_id, source, target, domain='通用', note=''):
    db = get_db()
    db.execute('UPDATE terms SET source=?,target=?,domain=?,note=? WHERE id=?',
               (source.strip(), target.strip(), domain, note, term_id))
    db.commit()

def import_excel(file_path):
    """从 Excel 批量导入"""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path)
        ws = wb.active
    except ImportError:
        return 0, 0, '缺少 openpyxl 库，无法读取 Excel 文件'
    except Exception as e:
        return 0, 0, f'读取文件失败: {e}'

    db = get_db()
    added, skipped = 0, 0
    errors = []

    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row or not row[0]: continue
        source = str(row[0]).strip() if row[0] else ''
        target = str(row[1]).strip() if len(row) > 1 and row[1] else ''
        domain = str(row[2]).strip() if len(row) > 2 and row[2] else '通用'
        note = str(row[3]).strip() if len(row) > 3 and row[3] else ''

        if not source or not target:
            skipped += 1
            continue

        exist = db.execute('SELECT id FROM terms WHERE source=? AND target=?', (source, target)).fetchone()
        if exist:
            skipped += 1
            continue

        db.execute('INSERT INTO terms (source,target,domain,note) VALUES (?,?,?,?)',
                   (source, target, domain, note))
        added += 1

    db.commit()
    return added, skipped, f'导入 {added} 条，跳过 {skipped} 条（重复或空行）'

def import_csv(file_path):
    """从 CSV 导入"""
    db = get_db()
    added, skipped = 0, 0
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if not row: continue
            source = row[0].strip() if row[0] else ''
            target = row[1].strip() if len(row) > 1 else ''
            domain = row[2].strip() if len(row) > 2 and row[2] else '通用'
            if not source or not target:
                skipped += 1
                continue
            exist = db.execute('SELECT id FROM terms WHERE source=? AND target=?', (source, target)).fetchone()
            if exist:
                skipped += 1
                continue
            db.execute('INSERT INTO terms (source,target,domain) VALUES (?,?,?)', (source, target, domain))
            added += 1
    db.commit()
    return added, skipped

def export_csv(output_path):
    """导出为 CSV（兼容 pdf2zh 格式）"""
    db = get_db()
    rows = db.execute('SELECT source, target FROM terms ORDER BY domain, id').fetchall()
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['source', 'target', 'tgt_lng'])
        for r in rows:
            writer.writerow([r[0], r[1], 'zh-CN'])
    return len(rows)

def export_glossary_for_pdf2zh(output_path, domain=''):
    """导出 pdf2zh 兼容格式的术语表 CSV"""
    db = get_db()
    if domain:
        rows = db.execute('SELECT source, target FROM terms WHERE domain=? ORDER BY id', (domain,)).fetchall()
    else:
        rows = db.execute('SELECT source, target FROM terms ORDER BY id').fetchall()
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['source', 'target', 'tgt_lng'])
        for r in rows:
            writer.writerow([r[0], r[1], 'zh-CN'])
    return len(rows)

# ── 术语匹配（供翻译引擎调用） ──
# ── 预编译正则缓存 ──
_compiled_regex = {}

def match_glossary(text, domain=''):
    """从文本中匹配术语，返回 [(source, target), ...]"""
    db = get_db()
    if domain:
        rows = db.execute('SELECT source, target, is_regex, case_sensitive FROM terms WHERE domain=? ORDER BY LENGTH(source) DESC', (domain,)).fetchall()
    else:
        rows = db.execute('SELECT source, target, is_regex, case_sensitive FROM terms ORDER BY LENGTH(source) DESC').fetchall()

    matches = []
    for r in rows:
        src, tgt, is_regex, case_sensitive = r
        if not src or not tgt:
            continue
        if is_regex:
            cache_key = (src, case_sensitive)
            if cache_key not in _compiled_regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                _compiled_regex[cache_key] = re.compile(src, flags)
            if _compiled_regex[cache_key].search(text):
                matches.append((src, tgt))
        else:
            if case_sensitive:
                if src in text:
                    matches.append((src, tgt))
            else:
                if src.lower() in text.lower():
                    matches.append((src, tgt))
    return matches

def build_glossary_prompt(text, domain=''):
    """构建术语注入 prompt"""
    matches = match_glossary(text, domain)
    if not matches:
        return ''
    lines = ['\n【术语表 - 必须按以下翻译】']
    for src, tgt in matches[:30]:  # 最多30条
        lines.append(f'  "{src}" → "{tgt}"')
    return '\n'.join(lines)

def get_stats():
    """术语库统计"""
    db = get_db()
    total = db.execute('SELECT COUNT(*) FROM terms').fetchone()[0]
    domains = db.execute('SELECT domain, COUNT(*) as c FROM terms GROUP BY domain ORDER BY c DESC').fetchall()
    return total, [(d, c) for d, c in domains]
