"""
翻译历史管理 — 记录/查询/清理
"""
import os, json, shutil, time, glob

HISTORY_DIR = os.path.join(os.path.dirname(__file__), '..', 'history')
INDEX_FILE = os.path.join(HISTORY_DIR, 'index.json')

def _load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def _save_index(data):
    os.makedirs(HISTORY_DIR, exist_ok=True)
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_record(filename, file_type, mono_path='', docx_path='', glossary_snapshot='', stats=None):
    """添加翻译记录"""
    records = _load_index()
    record_id = str(int(time.time()))
    record = {
        'id': record_id,
        'filename': filename,
        'file_type': file_type,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'mono_path': mono_path,
        'docx_path': docx_path,
        'glossary_snapshot': glossary_snapshot,
        'stats': stats or {},
    }
    records.insert(0, record)
    _save_index(records)
    return record_id

def get_records(limit=50):
    records = _load_index()
    # 清理无效记录
    valid = []
    for r in records:
        mono_ok = not r.get('mono_path') or os.path.exists(r['mono_path'])
        docx_ok = not r.get('docx_path') or os.path.exists(r['docx_path'])
        if mono_ok or docx_ok:
            valid.append(r)
    if len(valid) != len(records):
        _save_index(valid)
    return valid[:limit]

def get_record(record_id):
    for r in _load_index():
        if r['id'] == record_id:
            return r
    return None

def delete_record(record_id):
    records = _load_index()
    for r in records:
        if r['id'] == record_id:
            # 删除关联文件
            for key in ['mono_path', 'docx_path', 'glossary_snapshot']:
                path = r.get(key)
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass  # 文件可能已被删除或无权限
            break
    records = [r for r in records if r['id'] != record_id]
    _save_index(records)

def clean_old(days=7):
    """清理 N 天前的记录"""
    cutoff = time.time() - days * 86400
    records = _load_index()
    to_delete = [r for r in records if int(r['id']) < cutoff]
    for r in to_delete:
        delete_record(r['id'])
    return len(to_delete)

def clean_all():
    records = _load_index()
    for r in records:
        delete_record(r['id'])
    _save_index([])

def get_storage_size():
    """获取历史文件总大小"""
    total = 0
    for f in glob.glob(os.path.join(HISTORY_DIR, '**'), recursive=True):
        if os.path.isfile(f):
            total += os.path.getsize(f)
    return total

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} GB'
