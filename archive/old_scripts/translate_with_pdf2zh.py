"""
使用 pdf2zh (PDFMathTranslate) 翻译 PDF — 真正保留格式
DeepSeek API 密钥从 config.json 解密，全程内存传递
"""
import sys, os, json, base64
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'PDFMathTranslate'))  # 用本地版

# ── 解密 API Key ──
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

with open('config.json', 'r') as f:
    config = json.load(f)

machine_id = os.environ.get('COMPUTERNAME', '') + os.environ.get('USERNAME', '')
salt = b'doctrans_salt_2026'
kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
api_key = Fernet(key).decrypt(config['api_key'].encode()).decode()

# ── 设置 pdf2zh 所需环境变量 ──
os.environ['DEEPSEEK_API_KEY'] = api_key
os.environ['DEEPSEEK_MODEL'] = config.get('model', 'deepseek-chat')

# ── 调用 pdf2zh 翻译 ──
from pdf2zh.high_level import translate

files = [
    'original/[1].pdf',
    'original/rhBMP-2 (DWP431) Repeat-Dose Toxicity_Rat_2 weeks.pdf',
]

print('Starting pdf2zh translation...')
print(f'Files: {files}')
print(f'Service: deepseek | Model: {os.environ["DEEPSEEK_MODEL"]}')
print()

results = translate(
    files=files,
    output='output/pdf2zh/',
    lang_in='en',
    lang_out='zh',
    service='deepseek',
)

for mono, dual in results:
    print(f'  MONO: {mono}')
    print(f'  DUAL: {dual}')

print('\nDone!')
