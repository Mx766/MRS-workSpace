"""
文档翻译工具 — 桌面版 (tkinter)
双击运行，选择 DOCX 文件即可翻译
"""
import sys, os, json, threading, time, uuid, logging, traceback, csv

# 确保 app 和 core 模块可导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.dirname(__file__))

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from config import load_config, save_config, test_connection, SERVICE_PRESETS
from glossary import (search_terms, add_term, delete_term, import_excel,
                       import_csv, export_csv, get_all_domains, get_stats)
from translator import translate_docx_with_quality

OUTPUT_BASE = os.path.join(os.path.dirname(__file__), 'output')

# 配置日志
os.makedirs(os.path.join(os.path.dirname(__file__), 'logs'), exist_ok=True)
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'logs', 'translate_app.log'),
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger('translate_app')


class TranslationError(Exception):
    """翻译错误基类"""
    pass


def classify_error(e: Exception) -> str:
    """分类异常，返回用户友好的提示"""
    msg = str(e).lower()
    if '429' in msg or 'rate limit' in msg:
        return 'API 请求太频繁，请稍后重试（限流）'
    elif '401' in msg or 'unauthorized' in msg:
        return 'API 密钥无效，请在 API 设置中检查'
    elif '402' in msg or 'insufficient' in msg:
        return 'API 余额不足，请充值'
    elif '403' in msg or 'forbidden' in msg:
        return 'API 访问被拒绝，请检查密钥权限'
    elif '400' in msg or 'content' in msg or 'safety' in msg:
        return '文档内容触发安全审核，请联系管理员'
    elif 'timeout' in msg or 'timed out' in msg:
        return '网络连接超时，请检查网络后重试'
    elif 'connection' in msg or 'refused' in msg:
        return '无法连接到 API 服务器，请检查网络和 Base URL'
    else:
        return f'翻译过程出错: {str(e)[:200]}'


class TranslateApp:
    def __init__(self, root):
        self.root = root
        self.root.title('文档翻译工具')
        self.root.geometry('760x620')
        self.root.minsize(680, 500)

        # 状态
        self.input_file = None
        self.translating = False
        self.cfg = load_config()

        self._build_ui()
        self._refresh_status()

    # ═══════════════════════════════════════
    #  UI 构建
    # ═══════════════════════════════════════
    def _build_ui(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill='both', expand=True)

        # ── 标题 ──
        title = ttk.Label(main, text='文档翻译工具', font=('Microsoft YaHei', 16, 'bold'))
        title.pack(pady=(0, 12))

        # ── 文件选择区 ──
        file_frame = ttk.LabelFrame(main, text='选择文件', padding=10)
        file_frame.pack(fill='x', pady=(0, 8))

        file_row = ttk.Frame(file_frame)
        file_row.pack(fill='x')
        self.file_btn = ttk.Button(file_row, text='浏览...', command=self._browse_file, width=10)
        self.file_btn.pack(side='left', padx=(0, 8))
        self.file_label = ttk.Label(file_row, text='未选择文件', foreground='gray')
        self.file_label.pack(side='left', fill='x', expand=True)

        # ── 设置区 ──
        settings = ttk.LabelFrame(main, text='翻译设置', padding=10)
        settings.pack(fill='x', pady=(0, 8))

        row1 = ttk.Frame(settings)
        row1.pack(fill='x')
        ttk.Label(row1, text='领域:').pack(side='left')
        self.domain_var = tk.StringVar(value='医药')
        self.domain_combo = ttk.Combobox(row1, textvariable=self.domain_var, width=14)
        self.domain_combo.pack(side='left', padx=(4, 16))
        self._load_domains()

        ttk.Label(row1, text='模型:').pack(side='left')
        self.model_var = tk.StringVar(value=self.cfg.get('model', 'deepseek-v4-flash'))
        svc = self.cfg.get('service', 'deepseek')
        models = SERVICE_PRESETS.get(svc, {}).get('models', ['deepseek-chat'])
        self.model_combo = ttk.Combobox(row1, textvariable=self.model_var, values=models, width=18)
        self.model_combo.pack(side='left', padx=(4, 16))

        self.glossary_btn = ttk.Button(row1, text='📖 术语管理...', command=self._open_glossary_dialog, width=14)
        self.glossary_btn.pack(side='right', padx=(4, 0))
        self.api_btn = ttk.Button(row1, text='API 设置...', command=self._open_api_dialog, width=12)
        self.api_btn.pack(side='right')

        # ── 进度条 ──
        self.progress = ttk.Progressbar(main, mode='determinate', length=100)
        self.progress.pack(fill='x', pady=(0, 4))
        self.status_label = ttk.Label(main, text='就绪', foreground='gray')
        self.status_label.pack(anchor='w', pady=(0, 8))

        # ── 操作按钮 ──
        btn_row = ttk.Frame(main)
        btn_row.pack(fill='x', pady=(0, 8))
        self.translate_btn = ttk.Button(btn_row, text='▶ 开始翻译', command=self._start_translate, width=16)
        self.translate_btn.pack(side='left', padx=(0, 8))
        self.output_btn = ttk.Button(btn_row, text='打开输出文件夹', command=self._open_output, width=16)
        self.output_btn.pack(side='left')

        # ── 质量报告区 ──
        report_frame = ttk.LabelFrame(main, text='翻译结果', padding=8)
        report_frame.pack(fill='both', expand=True)

        self.report_text = scrolledtext.ScrolledText(
            report_frame, height=10, font=('Consolas', 10),
            wrap=tk.WORD, state='disabled'
        )
        self.report_text.pack(fill='both', expand=True)

        # ── 底部状态栏 ──
        self.statusbar = ttk.Label(main, text='', relief='sunken', anchor='w', padding=(4, 2))
        self.statusbar.pack(fill='x', pady=(4, 0))

    # ═══════════════════════════════════════
    #  交互逻辑
    # ═══════════════════════════════════════
    def _browse_file(self):
        path = filedialog.askopenfilename(
            title='选择要翻译的文档',
            filetypes=[('Word 文档', '*.docx'), ('所有文件', '*.*')]
        )
        if path:
            self.input_file = path
            self.file_label.config(text=os.path.basename(path), foreground='black')
            self._log(f'已选择: {path}')

    def _load_domains(self):
        try:
            domains = get_all_domains()
            if not domains:
                domains = ['通用', '医药', '化工', '器械']
            self.domain_combo['values'] = domains
            self.domain_var.set(domains[0])
        except Exception as e:
            logger.warning(f'Failed to load domains: {e}')
            self.domain_combo['values'] = ['通用', '医药', '化工', '器械']

    def _open_api_dialog(self):
        dialog = ApiDialog(self.root, self.cfg, self._on_api_saved)
        self.root.wait_window(dialog)

    def _open_glossary_dialog(self):
        dialog = GlossaryDialog(self.root, self._on_glossary_changed)
        self.root.wait_window(dialog)

    def _on_api_saved(self, new_cfg):
        self.cfg = new_cfg
        save_config(new_cfg)
        self._log('API 配置已更新')
        self._refresh_status()

    def _on_glossary_changed(self):
        """术语库变更后刷新领域下拉"""
        self._load_domains()
        self._refresh_status()

    def _refresh_status(self):
        if self.cfg.get('api_key'):
            svc = self.cfg.get('service', 'deepseek')
            mdl = self.cfg.get('model', '-')
            total, _ = get_stats()
            self.statusbar.config(text=f'API: {svc} | 模型: {mdl} | 术语库: {total} 条')
        else:
            self.statusbar.config(text='⚠ 请先配置 API 密钥')

    def _open_output(self):
        os.makedirs(OUTPUT_BASE, exist_ok=True)
        os.startfile(OUTPUT_BASE)

    def _log(self, msg):
        self.report_text.config(state='normal')
        self.report_text.insert('end', msg + '\n')
        self.report_text.see('end')
        self.report_text.config(state='disabled')

    # ═══════════════════════════════════════
    #  翻译（后台线程）
    # ═══════════════════════════════════════
    def _start_translate(self):
        if self.translating:
            messagebox.showwarning('提示', '翻译正在进行中')
            return

        if not self.input_file or not os.path.exists(self.input_file):
            messagebox.showwarning('提示', '请先选择要翻译的 DOCX 文件')
            return

        if not self.cfg.get('api_key'):
            messagebox.showwarning('提示', '请先在 API 设置中配置密钥')
            return

        self.translating = True
        self.translate_btn.config(state='disabled')
        self.progress['value'] = 0
        self.report_text.config(state='normal')
        self.report_text.delete('1.0', 'end')
        self.report_text.config(state='disabled')

        thread = threading.Thread(target=self._run_translate, daemon=True)
        thread.start()

    def _run_translate(self):
        """后台线程：翻译主流程。双重异常保护防止 UI 卡死。"""
        try:
            self._run_translate_inner()
        except BaseException as e:
            err_msg = f'严重错误: {e}'
            logger.error(f'Fatal error in translate thread: {e}', exc_info=True)
            self.root.after(0, lambda: self._log(err_msg))
            self.root.after(0, lambda: self.status_label.config(text='严重错误，请查看日志', foreground='red'))
        finally:
            self.translating = False
            self.root.after(0, lambda: self.translate_btn.config(state='normal'))

    def _run_translate_inner(self):
        try:
            fname = os.path.basename(self.input_file)
            doc_id = f'{int(time.time())}_{uuid.uuid4().hex[:8]}'
            out_dir = os.path.join(OUTPUT_BASE, doc_id)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, fname.replace('.docx', '_中文版.docx'))

            api_key = self.cfg['api_key']
            model = self.model_var.get()
            base_url = self.cfg.get('base_url_override', '')
            domain = self.domain_var.get()

            def progress_cb(pct, msg):
                self.root.after(0, lambda: self._update_progress(pct, msg))

            self.root.after(0, lambda: self._log(f'开始翻译: {fname}'))
            self.root.after(0, lambda: self._log(f'领域: {domain} | 模型: {model}'))
            self.root.after(0, lambda: self._log('─' * 50))

            result_path, quality = translate_docx_with_quality(
                self.input_file, out_path, api_key, model, base_url, domain,
                progress_callback=progress_cb
            )

            self.root.after(0, lambda: self._show_quality(quality, result_path))
            self.root.after(0, lambda: self._update_progress(1.0, '完成！'))

        except Exception as e:
            friendly = classify_error(e)
            logger.error(f'Translation failed: {e}', exc_info=True)
            self.root.after(0, lambda: self._log(f'翻译失败: {friendly}'))
            self.root.after(0, lambda: self.status_label.config(text='失败', foreground='red'))

    def _update_progress(self, pct, msg):
        self.progress['value'] = pct * 100
        self.status_label.config(text=msg)

    def _show_quality(self, quality, output_path):
        self._log('─' * 50)
        self._log(f'输出: {output_path}')
        self._log('')

        score = quality['overall_score']
        ga = quality['glossary_applied']
        gv = quality['glossary_violations']
        cv = quality['critical_violations']
        total = quality['total_segments']

        if score >= 0.95:
            grade = '⭐ 优秀'
        elif score >= 0.85:
            grade = '✅ 良好'
        elif score >= 0.70:
            grade = '⚠ 一般'
        else:
            grade = '❌ 需人工校对'

        self._log(f'质量评分: {score:.0%}  {grade}')
        self._log(f'翻译段落: {total}')
        self._log(f'术语强制替换: {ga} 处')
        self._log(f'术语未遵守: {gv} 处')
        self._log(f'关键项丢失: {cv} 处')
        self._log('')

        warnings = quality.get('warnings', [])
        if warnings:
            self._log(f'⚠ 需人工复核 ({len(warnings)} 项):')
            for w in warnings[:15]:
                self._log(f'  • [{w["type"]}] {w["detail"][:100]}')
            if len(warnings) > 15:
                self._log(f'  ... 还有 {len(warnings)-15} 项')
        else:
            self._log('✅ 无需人工复核')

        self._log('')
        self._log(f'详细报告: {output_path.replace(".docx", "_quality_report.json")}')
        self.status_label.config(text=f'完成 — 质量评分 {score:.0%}', foreground='green')


# ═══════════════════════════════════════
#  API 设置对话框
# ═══════════════════════════════════════
class ApiDialog(tk.Toplevel):
    def __init__(self, parent, cfg, callback):
        super().__init__(parent)
        self.cfg = cfg.copy()
        self.callback = callback

        self.title('API 设置')
        self.geometry('480x360')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        main = ttk.Frame(self, padding=16)
        main.pack(fill='both', expand=True)

        ttk.Label(main, text='服务商:').pack(anchor='w')
        svc = cfg.get('service', 'deepseek')
        self.svc_var = tk.StringVar(value=svc)
        choices = [(v['name'], k) for k, v in SERVICE_PRESETS.items()]
        self.svc_combo = ttk.Combobox(
            main, textvariable=self.svc_var,
            values=[c[0] for c in choices], width=30, state='readonly'
        )
        self.svc_combo.pack(fill='x', pady=(2, 8))

        ttk.Label(main, text='API Key:').pack(anchor='w')
        self.key_var = tk.StringVar(value=cfg.get('api_key', ''))
        key_entry = ttk.Entry(main, textvariable=self.key_var, show='*', width=40)
        key_entry.pack(fill='x', pady=(2, 8))

        ttk.Label(main, text='模型:').pack(anchor='w')
        self.model_var = tk.StringVar(value=cfg.get('model', 'deepseek-v4-flash'))
        model_entry = ttk.Entry(main, textvariable=self.model_var, width=40)
        model_entry.pack(fill='x', pady=(2, 8))

        ttk.Label(main, text='Base URL (可选):').pack(anchor='w')
        self.url_var = tk.StringVar(value=cfg.get('base_url_override', ''))
        url_entry = ttk.Entry(main, textvariable=self.url_var, width=40)
        url_entry.pack(fill='x', pady=(2, 8))

        btn_row = ttk.Frame(main)
        btn_row.pack(fill='x', pady=(12, 0))

        test_btn = ttk.Button(btn_row, text='测试连接', command=self._test)
        test_btn.pack(side='left')

        self.test_result = ttk.Label(btn_row, text='', foreground='gray')
        self.test_result.pack(side='left', padx=(8, 0))

        cancel_btn = ttk.Button(btn_row, text='取消', command=self.destroy)
        cancel_btn.pack(side='right', padx=(4, 0))
        save_btn = ttk.Button(btn_row, text='保存', command=self._save)
        save_btn.pack(side='right')

    def _test(self):
        key = self.key_var.get()
        model = self.model_var.get()
        url = self.url_var.get()
        if not key:
            self.test_result.config(text='请先填写 API Key', foreground='red')
            return

        svc_key = {v['name']: k for k, v in SERVICE_PRESETS.items()}.get(self.svc_var.get(), 'custom')
        presets = SERVICE_PRESETS.get(svc_key, SERVICE_PRESETS['custom'])

        ok, msg = test_connection(key, model, url or presets['base_url'])
        if ok:
            self.test_result.config(text='✅ 连接成功', foreground='green')
        else:
            self.test_result.config(text=f'❌ {msg[:80]}', foreground='red')

    def _save(self):
        svc_key = {v['name']: k for k, v in SERVICE_PRESETS.items()}.get(self.svc_var.get(), 'deepseek')
        self.cfg['service'] = svc_key
        self.cfg['api_key'] = self.key_var.get()
        self.cfg['model'] = self.model_var.get()
        self.cfg['base_url_override'] = self.url_var.get()
        save_config(self.cfg)
        self.callback(self.cfg)
        self.destroy()


# ═══════════════════════════════════════
#  术语管理对话框
# ═══════════════════════════════════════
class GlossaryDialog(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback  # 关闭时回调刷新主窗口
        self.current_page = 1
        self.page_size = 50

        self.title('术语库管理')
        self.geometry('700x520')
        self.minsize(600, 400)
        self.transient(parent)
        self.grab_set()

        # 统计栏
        stats_frame = ttk.Frame(self, padding=(12, 8, 12, 0))
        stats_frame.pack(fill='x')
        self.stats_label = ttk.Label(stats_frame, text='', font=('Microsoft YaHei', 10))
        self.stats_label.pack(side='left')

        # Notebook 多标签页
        nb = ttk.Notebook(self, padding=8)
        nb.pack(fill='both', expand=True)

        # ── Tab 1: 浏览搜索 ──
        self._build_browse_tab(nb)
        # ── Tab 2: 添加术语 ──
        self._build_add_tab(nb)
        # ── Tab 3: 批量导入 ──
        self._build_import_tab(nb)
        # ── Tab 4: 导出 ──
        self._build_export_tab(nb)

        self._refresh_stats()
        self._do_search()

    def _refresh_stats(self):
        try:
            total, domains = get_stats()
            d_str = ' | '.join([f'{d}: {c}' for d, c in domains[:8]])
            self.stats_label.config(text=f'总计: {total} 条  |  {d_str}')
        except Exception as e:
            self.stats_label.config(text=f'加载失败: {e}')

    # ── 浏览搜索 ──
    def _build_browse_tab(self, nb):
        frame = ttk.Frame(nb, padding=8)
        nb.add(frame, text='浏览搜索')

        # 搜索栏
        search_row = ttk.Frame(frame)
        search_row.pack(fill='x', pady=(0, 4))
        ttk.Label(search_row, text='搜索:').pack(side='left')
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_row, textvariable=self.search_var, width=30)
        search_entry.pack(side='left', padx=(4, 8))
        search_entry.bind('<Return>', lambda e: self._do_search())
        search_entry.bind('<KP_Enter>', lambda e: self._do_search())

        ttk.Label(search_row, text='领域:').pack(side='left')
        self.filter_domain_var = tk.StringVar(value='全部')
        domain_combo = ttk.Combobox(search_row, textvariable=self.filter_domain_var,
                                     values=['全部'], width=12, state='readonly')
        domain_combo.pack(side='left', padx=(4, 8))

        def refresh_domains():
            try:
                domains = ['全部'] + get_all_domains()
                domain_combo['values'] = domains
            except Exception:
                pass

        search_btn = ttk.Button(search_row, text='搜索', command=self._do_search, width=8)
        search_btn.pack(side='left')
        refresh_domains()

        # 结果列表 — Treeview
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill='both', expand=True)

        cols = ('英文', '中文', '领域', '备注')
        self.term_tree = ttk.Treeview(tree_frame, columns=cols, show='headings',
                                       selectmode='browse', height=12)
        for c in cols:
            self.term_tree.heading(c, text=c)
        self.term_tree.column('英文', width=220)
        self.term_tree.column('中文', width=200)
        self.term_tree.column('领域', width=80)
        self.term_tree.column('备注', width=100)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.term_tree.yview)
        self.term_tree.configure(yscrollcommand=scrollbar.set)
        self.term_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # 翻页
        page_row = ttk.Frame(frame)
        page_row.pack(fill='x', pady=(4, 0))
        prev_btn = ttk.Button(page_row, text='◀ 上一页', command=self._prev_page, width=10)
        prev_btn.pack(side='left')
        self.page_label = ttk.Label(page_row, text='')
        self.page_label.pack(side='left', padx=8)
        next_btn = ttk.Button(page_row, text='下一页 ▶', command=self._next_page, width=10)
        next_btn.pack(side='left')

        # 删除按钮
        del_btn = ttk.Button(page_row, text='删除选中', command=self._delete_term, width=10)
        del_btn.pack(side='right')

    def _do_search(self):
        self.current_page = 1
        self._load_page()

    def _load_page(self):
        query = self.search_var.get()
        domain = self.filter_domain_var.get()
        if domain == '全部':
            domain = ''

        rows, total = search_terms(query, domain, self.current_page, self.page_size)

        self.term_tree.delete(*self.term_tree.get_children())
        for r in rows:
            self.term_tree.insert('', 'end', values=(r['source'], r['target'], r['domain'], r['note']))

        max_page = max(1, (total - 1) // self.page_size + 1)
        self.page_label.config(text=f'第 {self.current_page}/{max_page} 页  (共 {total} 条)')

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._load_page()

    def _next_page(self):
        self.current_page += 1
        self._load_page()

    def _delete_term(self):
        selection = self.term_tree.selection()
        if not selection:
            messagebox.showinfo('提示', '请先选中要删除的术语')
            return
        item = self.term_tree.item(selection[0])
        source, target = item['values'][0], item['values'][1]
        if messagebox.askyesno('确认删除', f'确定要删除 "{source}" → "{target}" 吗？'):
            try:
                # 通过 glossary 模块查找并删除
                from glossary import get_db
                db = get_db()
                db.execute('DELETE FROM terms WHERE source=? AND target=?', (source, target))
                db.commit()
                self._refresh_stats()
                self._load_page()
            except Exception as e:
                messagebox.showerror('错误', f'删除失败: {e}')

    # ── 添加 ──
    def _build_add_tab(self, nb):
        frame = ttk.Frame(nb, padding=16)
        nb.add(frame, text='添加术语')

        ttk.Label(frame, text='英文术语:').pack(anchor='w')
        self.add_src_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.add_src_var, width=50).pack(fill='x', pady=(2, 8))

        ttk.Label(frame, text='中文翻译:').pack(anchor='w')
        self.add_tgt_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.add_tgt_var, width=50).pack(fill='x', pady=(2, 8))

        ttk.Label(frame, text='领域:').pack(anchor='w')
        self.add_domain_var = tk.StringVar(value='通用')
        ttk.Combobox(frame, textvariable=self.add_domain_var,
                      values=['通用', '医药', '化工', '器械', '法律', '电子'],
                      width=20).pack(fill='x', pady=(2, 8))

        ttk.Label(frame, text='备注 (可选):').pack(anchor='w')
        self.add_note_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.add_note_var, width=50).pack(fill='x', pady=(2, 8))

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill='x', pady=(12, 0))
        self.add_result_label = ttk.Label(btn_row, text='', foreground='gray')
        self.add_result_label.pack(side='left')

        add_btn = ttk.Button(btn_row, text='添加', command=self._do_add, width=12)
        add_btn.pack(side='right')

    def _do_add(self):
        src = self.add_src_var.get().strip()
        tgt = self.add_tgt_var.get().strip()
        domain = self.add_domain_var.get().strip()
        note = self.add_note_var.get().strip()

        if not src or not tgt:
            self.add_result_label.config(text='英文和中文不能为空', foreground='red')
            return

        try:
            ok, msg = add_term(src, tgt, domain, note)
            if ok:
                self.add_src_var.set('')
                self.add_tgt_var.set('')
                self.add_note_var.set('')
                self.add_result_label.config(text=f'✅ {msg}', foreground='green')
                self._refresh_stats()
            else:
                self.add_result_label.config(text=f'⚠ {msg}', foreground='orange')
        except Exception as e:
            self.add_result_label.config(text=f'❌ 添加失败: {e}', foreground='red')

    # ── 批量导入 ──
    def _build_import_tab(self, nb):
        frame = ttk.Frame(nb, padding=16)
        nb.add(frame, text='批量导入')

        ttk.Label(frame, text='支持格式: Excel (.xlsx) 或 CSV', font=('Microsoft YaHei', 10)).pack(anchor='w', pady=(0, 4))
        ttk.Label(frame,
            text='列顺序: 英文术语 | 中文翻译 | 领域(可选) | 备注(可选)\n'
                 '第一行为列标题（自动跳过）',
            foreground='gray').pack(anchor='w', pady=(0, 8))

        self.import_path_label = ttk.Label(frame, text='未选择文件', foreground='gray')
        self.import_path_label.pack(anchor='w')

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill='x', pady=(8, 0))
        browse_btn = ttk.Button(btn_row, text='选择文件...', command=self._browse_import)
        browse_btn.pack(side='left')
        import_btn = ttk.Button(btn_row, text='开始导入', command=self._do_import, width=12)
        import_btn.pack(side='right', padx=(8, 0))

        self.import_result_label = ttk.Label(frame, text='', wraplength=500)
        self.import_result_label.pack(fill='x', pady=(8, 0))

    def _browse_import(self):
        path = filedialog.askopenfilename(
            title='选择术语文件',
            filetypes=[('Excel 或 CSV', '*.xlsx *.csv'), ('Excel', '*.xlsx'), ('CSV', '*.csv')]
        )
        if path:
            self._import_path = path
            self.import_path_label.config(text=os.path.basename(path), foreground='black')

    def _do_import(self):
        path = getattr(self, '_import_path', None)
        if not path:
            self.import_result_label.config(text='请先选择文件', foreground='red')
            return

        try:
            if path.endswith('.csv'):
                added, skipped = import_csv(path)
                msg = f'✅ 导入 {added} 条，跳过 {skipped} 条（重复或空行）'
            else:
                added, skipped, msg2 = import_excel(path)
                msg = f'✅ 导入 {added} 条，跳过 {skipped} 条\n{msg2}'

            self.import_result_label.config(text=msg, foreground='green')
            self._refresh_stats()
            if self.callback:
                self.callback()
        except Exception as e:
            self.import_result_label.config(text=f'导入失败: {e}', foreground='red')

    # ── 导出 ──
    def _build_export_tab(self, nb):
        frame = ttk.Frame(nb, padding=16)
        nb.add(frame, text='导出')

        ttk.Label(frame, text='导出术语库为 CSV 文件（兼容 pdf2zh 格式）',
                  font=('Microsoft YaHei', 10)).pack(anchor='w', pady=(0, 12))

        export_btn = ttk.Button(frame, text='导出为 CSV', command=self._do_export, width=16)
        export_btn.pack(anchor='w')

        self.export_result_label = ttk.Label(frame, text='', foreground='gray')
        self.export_result_label.pack(anchor='w', pady=(8, 0))

    def _do_export(self):
        path = filedialog.asksaveasfilename(
            title='导出术语表',
            defaultextension='.csv',
            filetypes=[('CSV 文件', '*.csv')],
            initialfile='glossary_export.csv'
        )
        if not path:
            return

        try:
            n = export_csv(path)
            self.export_result_label.config(text=f'✅ 已导出 {n} 条术语到 {path}', foreground='green')
        except Exception as e:
            self.export_result_label.config(text=f'导出失败: {e}', foreground='red')


# ═══════════════════════════════════════
#  入口
# ═══════════════════════════════════════
if __name__ == '__main__':
    root = tk.Tk()

    try:
        root.iconbitmap(default='')
    except Exception:
        pass

    app = TranslateApp(root)

    # 支持命令行参数直接传文件
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        app.input_file = sys.argv[1]
        app.file_label.config(text=os.path.basename(sys.argv[1]), foreground='black')
        app._log(f'已加载: {sys.argv[1]}')

    root.mainloop()
