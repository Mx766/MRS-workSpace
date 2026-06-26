+ # proofread-docx Skill 代码审查报告
+ 
+ > 审查日期: 2026-06-25
+ > 审查范围: SKILL.md 与 scripts/ 下 7 个 Python 脚本
> 
> **修复状态**: Issues 1-6 已在 2026-06-25 修复。Issue 12 待解决。
> 
> **修复状态**: Issues 1-6 已在 2026-06-25 修复。Issue 12 待解决。
+ 
+ ## 🐛 Bug
+ 
+ ### 1. ✅ `split_docx.py` — `wb.close()` 后访问 `wb.sheetnames`
+ 
+ `split_excel()` 中 `wb.close()` 调用之后，返回语句才读 `wb.sheetnames`。`read_only=True` 模式下 close 可能清空状态，导致空列表或抛异常。
+ 
+ **修复**: 将 `sheetnames` 赋值提前到 `close()` 之前。
+ 
+ ## 🧟 死代码
+ 
+ ### 2. ✅ `write_comments.py` — `_shade_matching_runs()` 从未被调用
+ 
+ 函数用 lxml 操作 run 底色，但 `write_word_comments()` 实际用 python-docx `OxmlElement` 方案。该函数悬空。
+ 
+ **建议**: 删除 `_shade_matching_runs`。
+ 
+ ### 3. ✅ `write_report.py` — `DOCX_AVAILABLE` flag 未使用
+ 
+ 模块级 flag 定义了但没被检查。`generate_report()` 内部做了独立 import。
+ 
+ **建议**: 删除该 flag。
+ 
+ ## 📛 命名不一致
+ 
+ ### 4. ✅ `load_glossary.py` — `_load_excel_fallback()` 实际读 CSV
+ 
+ 函数名含 `excel`，函数体用 `csv.reader`。`load_csv_glossary()` 又调它，绕路。
+ 
+ **建议**: 重命名为 `_load_csv_fallback()`。
+ 
+ ## 🌐 环境兼容性
+ 
+ ### 5. ✅ `search_term.py` — 全部网络 API 在沙箱中必失败
+ 
+ 四个后端（术语在线、WHO、FDA、DuckDuckGo）都依赖 `urllib.request.urlopen`，在受限网络下全挂。
+ 
+ **建议**: SKILL.md Phase 5 注明"需网络；沙箱中自动跳过"。
+ 
+ ## 📄 SKILL.md 问题
+ 
+ ### 6. ✅ 引用了不存在的 extract 脚本
+ 
+ Phase 4.1: "调用 extract 脚本" — `scripts/` 下无 `extract.py`。
+ 
+ **建议**: 只保留"从 Phase 2 输出取"。
+ 
+ ## 🟡 观察项
+ 
+ | ID | 问题 | 文件 | 说明 |
+ |----|------|------|------|
+ | 7 | `_CHS`/`_CHT` 都映射 `zh` | `pair_files.py` | 简繁区分丢失 |
+ | 8 | `check_numbers()` 用 set 去重 | `check_mechanical.py` | 同数字多次出现可能漏检 |
+ | 9 | PDF 拆分只有 page 级 | `split_docx.py` | 与 DOCX 输出结构不一致 |
+ | 10 | Excel 段落用 `|` 拼接 | `check_mechanical.py` | 拼接后检查可能误报 |
+ | 11 | 格式 issue 无 paragraph_index | `check_mechanical.py` | 与 SKILL.md 必填字段冲突 |
+ 
+ ## 优先级
+ 
+ | 优先级 | Issue | 理由 |
+ |--------|-------|------|
+ | P0 | 1 | 运行时可能崩溃 |
+ | P1 | 5, 6 | 误导执行或频报错 |
+ | P2 | 2, 3, 4 | 代码可维护性 |
+ | P3 | 7-11 | 功能影响有限 |

---

## 🐛 12. 高亮底色在 ZIP 重打包后消失（新增，待解决）

> **TL;DR**: python-docx 单独保存的文档高亮正常。但经过 ZIP 重打包注入批注后，高亮消失——XML 中 `w:shd` + `w:highlight` 元素完整存在，Word 就是不渲染。

### 涉及文件
- `scripts/_build_annotated.py`（工作区外的临时脚本）
- `scripts/write_comments.py` — `write_word_comments()`

### 管道

```
第 1 步: python-docx 打开 DOCX → OxmlElement 给 run 加 w:shd + w:highlight
         → doc.save(tmp.docx)                              ✅ 高亮可见

第 2 步: ZIP(tmp.docx) → lxml 解析 document.xml → 加 commentRangeStart/End/Reference
         → 序列化 → 写回输出 ZIP                            ❌ 高亮消失
```

### 已验证的事实

| 测试文件 | 内容 | 高亮结果 |
|----------|------|----------|
| `_test_real_highlight.docx` | python-docx 加高亮 + 直接 save | ✅ Word 可见 |
| `_test_A_highlights_only.docx` | 同上 | ✅ Word 可见 |
| `_test_C_before_zip.docx` | 同上 | ✅ Word 可见 |
| `_test_zip_roundtrip.docx` | 读 ZIP → 原样写回（无修改） | ✅ Word 能打开 |
| `_test_lxml_roundtrip.docx` | lxml 解析/序列化 document.xml（无修改）→ 写回 | ✅ python-docx 可读 |
| `_test_one_comment.docx` | 加 1 条批注（全流程） | ⚠️ 未在 Word 中测试 |
| `v2.docx` | 9 条批注（全流程） | ❌ 文件能打开，批注可见，高亮不显示 |

### 已知排除的因素

1. **XML 结构** — 输出文件的 `w:shd` 和 `w:highlight` 元素存在且属性正确（`w:fill="#FFCCCC"`, `w:highlight="red"` 等）
2. **ZipInfo 元数据** — 已保留每个条目的 `compress_type` / `date_time`
3. **XML 声明/编码** — 与原始文件一致（`<?xml version='1.0' encoding='UTF-8' standalone='yes'?>`）
4. **命名空间** — 原始文件和输出文件的 `xmlns:nsmap` 完全一致
5. **lxml 解析/序列化本身** — 只做 parse + tostring 不做任何修改，roundtrip 不破坏文件结构

### 可疑方向（未验证）

1. **ZIP 内部文件顺序** — OOXML 可能对 `[Content_Types].xml` 或 `.rels` 在 ZIP 中的物理位置有隐含依赖。当前代码用 dict 收集 entries 后遍历写出，打乱了原始顺序。
2. **commentReference 与高亮的交互** — 段落中新增的 `w:commentRangeStart`/`w:commentRangeEnd`/空 `w:r`（含 `w:commentReference`）可能触发 Word 的某种渲染路径，忽略了同段落其他 run 的高亮属性。
3. **段落级别的 `w:rPr` 继承** — 加了批注标记后，Word 的样式继承链可能被中断。
4. **ZIP 压缩级别** — `zipfile.ZIP_DEFLATED` vs 原始文件的压缩方式可能存在细微差异。

### 复现步骤

```bash
cd d:/translation
python scripts/_build_annotated.py
# 打开 proofread/未校对、未排版_CHN_校对稿v2.docx → 看段落 7/34/113 等高亮区域
```

### 关键代码位置

- **高亮添加**: `_build_annotated.py` L63-80（OxmlElement → w:shd + w:highlight）
- **批注注入**: `_build_annotated.py` L100-150（lxml → commentRangeStart/End/Reference）
- **ZIP 写回**: `_build_annotated.py` L200-210（遍历 dict → writestr）

### 临时绕过方案

如果能找到一种不用 ZIP 重打包也能注入 `comments.xml` 的方法（例如 python-docx 的 part 机制，参见 `docx.opc.part`），就可以彻底避开此问题。

---

## ✅ 12. 已解决 (2026-06-26)

### 真正的根因

**不是 ZIP 重打包、不是 lxml namespace 污染、不是 document.xml 被修改。**
**是 Word 的渲染引擎行为：当 `w:commentReference` 位于段落末尾的独立空 `<w:r>` 中时，Word 抑制同段内所有 `w:shd` + `w:highlight` 的渲染。**

### 验证过程

创建了 3 个测试文件，逐一验证：

| 测试 | commentReference 位置 | 高亮 |
|------|----------------------|------|
| test1 | **高亮 run 内部**（和 w:shd 共享 rPr） | ✅ |
| test2 | 文本 run 之间的独立 run | ✅ |
| test3 | 高亮 run 内部，无 commentRangeStart/End | ✅ |
| v2 旧方案 | 段落末尾独立空 run | ❌ |

### 最终方案（v5，`_build_annotated_v4.py`）

1. **commentReference 放在高亮 run 的 rPr 内部**（紧挨 w:shd + w:highlight）
2. **删除 commentRangeStart/End**——不需要，commentReference 直接关联到批注
3. **跨 run 匹配**：先单 run 查，查不到就拼全文定位再找起始 run
4. **lxml 完全不碰 document.xml**：python-docx 处理所有 document.xml 修改 → doc.save() → ZIP 层只添加 comments.xml/rels/CT

### 匹配率

- v2（旧）：23/54 (43%)
- v5（新）：51/54 (94%)
- 剩余 3 条 unmatched 是因为 target_quote 在文档中确实不存在（描述性文字而非原文）

### 构建脚本

`d:/translation/scripts/_build_annotated_v4.py` — 输出到 `proofread/1/v5/`

---

## 🔬 Issue 12 修复：从 v2 → v4 的迭代

### 根因

**高亮丢失的根因不是 ZIP 顺序，也不是 XML 格式，而是"lxml 回读了 document.xml"。**

Claude 的 `_build_annotated.py` 流程：
1. python-docx 加高亮 → `doc.save()` ✅ 高亮完好
2. ZIP 阶段 `etree.fromstring()` 解析 document.xml → 加 commentRangeStart/End/Reference → 序列化回写 ❌ 高亮消失

lxml 的 parse + tostring 过程中，python-docx 写入的 `w:shd` + `w:highlight` 属性虽然肉眼看起来完整，但 lxml 和 python-docx 的 namespace 表示方式有微妙差异，导致 Word 不渲染。

### v4 方案（已验证通过）

```
python-docx 加高亮 + 加 comment 标记 → doc.save() → ZIP 层只替换 comments.xml
                                                       （不碰 document.xml）
```

关键改动：
1. **commentRangeStart/End/Reference 全部用 `OxmlElement`（python-docx）在 save 前写入**
2. **ZIP 阶段删除旧 `word/comments.xml` 再写入新的**，避免重复
3. ZIP 写入按 OOXML 顺序：`[Content_Types].xml` 打头
4. **lxml 完全不接触 document.xml**

### 验证结果

| 版本 | 流程 | 高亮 | 批注 | 重复条目 |
|------|------|------|------|----------|
| v2 | python-docx → lxml 改 document.xml → ZIP | ❌ 丢失 | ✅ | ✅ 无 |
| v3 | OxmlElement + Part 机制 → `doc.save()` | ❌ 重复 | ✅ 可见 | ❌ `comments.xml × 2` |
| **v4** | **OxmlElement 全改 → `doc.save()` → ZIP 只加新文件** | **✅ 17 shd** | **✅ 9 条** | **✅ 无** |
