# proofread-docx — 翻译校对 Skill

跨 Agent 运行时通用 skill（符合 [agentskills.io](https://agentskills.io) 规范）。

## 功能

英语→中文外包翻译稿的全流程自动化校对：
- PDF ↔ DOCX 跨格式对齐
- 机械检查（术语库违规、数字缺失、格式偏差）
- 六维度 34 项语义审查
- 生成含高亮 + 批注的 Word 校对稿
- 生成结构化校对报告

## 安装

### 方式一：解压到 skills 目录

```bash
# 解压到当前 Agent 的 skills 目录
# Claude Code:
tar -xzf proofread-docx-v1.0.0.tar.gz -C ~/.claude/skills/proofread-docx/
# 或
unzip proofread-docx-v1.0.0.zip -d ~/.claude/skills/proofread-docx/

# Codex:
tar -xzf proofread-docx-v1.0.0.tar.gz -C ~/.codex/skills/proofread-docx/

# Copilot CLI / Gemini CLI:
tar -xzf proofread-docx-v1.0.0.tar.gz -C ~/.agents/skills/proofread-docx/
```

解压后新开会话即自动发现。

### 方式二：git clone + 软链接

```bash
git clone https://github.com/Mx766/d--translation.git
ln -s "$(pwd)/d--translation/skills/proofread-docx" ~/.claude/skills/proofread-docx
```

更新时 `git pull` 即可，无需重新安装。

## Python 依赖

```bash
pip install python-docx openpyxl lxml PyMuPDF
```

## 验证

对方新开 Agent 会话，输入：

> 帮我校对翻译文件

如果 Agent 读取了 SKILL.md 并按 Phase 0→7 的 pipeline 执行，说明安装成功。

## 文件结构

```
proofread-docx/
├── SKILL.md              # 主 skill 定义（frontmatter + 全流程说明）
├── scripts/
│   ├── pair_files.py     # Phase 1: 文件配对
│   ├── split_docx.py     # Phase 2: 段落拆分
│   ├── check_mechanical.py # Phase 3: 机械检查
│   ├── filter_*.py       # Phase 3.4: 假阳性过滤
│   ├── classify_glossary.py # 术语库领域分类
│   ├── check_cross_file_terms.py # Phase 4.5: 跨文件术语一致性
│   ├── write_comments.py # Phase 6: 批注写入
│   ├── write_report.py   # Phase 7: 报告生成
│   ├── fix_target_quotes.py  # 修复 target_quote 定位
│   ├── load_glossary.py  # Phase 0: 术语库加载
│   ├── search_term.py    # Phase 5: 术语查证
│   └── locate_*.py       # 定位辅助
└── glossaries/
    ├── glossary.json     # 医学术语库（2813条）
    └── 术语库_标准格式.xlsx
```

## 版本

v1.0.0 (2026-06-29)
