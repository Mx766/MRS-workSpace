#!/usr/bin/env python3
"""
Phase 4 前置：标准化 batch 构建脚本 v2.23

连接 split_target.json/split_source.json → prepare_batch_prompt.py 的桥梁。
消除 Agent 手动构造 batch 导致的 paragraph_index 错位和 trigger 缺失。

输入:
  - cache/split_target.json (Phase 2 产物)
  - cache/split_source.json (Phase 2 产物)
  - cache/phase4_context.json (Phase 3.5 产物, optional)

输出:
  - cache/batch_01_data.json, batch_02_data.json, ...

格式对齐:
  - 段落条目: {index, source_text, target_text, style, heading_level}
    index = split_target.json 中的全局 index，已对齐 doc.paragraphs (1-based)
  - 表格单元格条目: {index, target_text, source_text, is_table_cell: true, table_index, row, col}
    index 从 total_paragraphs+1 递增，与 write_comments.py _build_table_cell_map() 一致
"""

import argparse
import json
import os
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


def load_json(filepath: str) -> dict | list | None:
    """加载 JSON 文件，处理常见错误。"""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        sys.stderr.write(f"[build_batches] 无法加载 {filepath}: {e}\n")
        return None


def collect_all_entries(target_data: dict, source_data: dict = None) -> list[dict]:
    """从 split JSON 收集所有段落 + 表格单元格条目。

    返回列表，每个条目含:
      - index: 全局段落索引 (1-based, 对齐 doc.paragraphs)
      - source_text: 源文文本
      - target_text: 译文文本
      - style: 段落样式
      - heading_level: 标题级别 (None = 非标题)
      - is_table_cell: 是否为表格单元格 (bool)
      - table_index, row, col: 表格单元格元数据 (仅 is_table_cell=True)

    表格单元格的 index 从 total_paragraphs+1 开始递增，与
    write_comments.py 的 _build_table_cell_map() 逻辑一致。
    """
    entries = []
    total_paras = 0

    # ── 第一遍：计算总段落数 + 收集段落条目 ──
    if "chapters" in target_data:
        for ch in target_data["chapters"]:
            total_paras += len(ch.get("paragraphs", []))

    # ── 第二遍：收集段落条目 ──
    if "chapters" in target_data:
        for ch in target_data["chapters"]:
            chapter_name = ch.get("chapter", "")
            for para in ch.get("paragraphs", []):
                idx = para.get("index", len(entries) + 1)
                entries.append({
                    "index": idx,
                    "chapter": chapter_name,
                    "source_text": para.get("source_text", ""),
                    "target_text": para.get("text", ""),
                    "style": para.get("style", "Normal"),
                    "heading_level": para.get("heading_level"),
                    "is_table_cell": False,
                })
    elif "pages" in target_data:
        # PDF 模式：按页切分
        for page in target_data.get("pages", []):
            page_num = page.get("page_num", 0)
            page_text = page.get("text", "")
            for i, line in enumerate(page_text.split("\n")):
                line = line.strip()
                if line:
                    entries.append({
                        "index": len(entries) + 1,
                        "page": page_num,
                        "source_text": "",
                        "target_text": line,
                        "style": "Normal",
                        "heading_level": None,
                        "is_table_cell": False,
                    })
    elif isinstance(target_data, list):
        # 扁平列表模式
        for i, item in enumerate(target_data):
            entries.append({
                "index": i + 1,
                "source_text": item.get("source_text", ""),
                "target_text": item.get("text", item.get("target_text", "")),
                "style": item.get("style", "Normal"),
                "heading_level": item.get("heading_level"),
                "is_table_cell": False,
            })

    # ── 合并源文数据（如果有 source_data） ──
    if source_data and isinstance(source_data, dict) and "chapters" in source_data:
        _merge_source_texts(entries, source_data)

    # ── 第三遍：收集表格单元格条目 ──
    cell_idx = total_paras + 1  # 表格单元格索引起点
    if isinstance(target_data, dict) and "chapters" in target_data:
        for ch in target_data["chapters"]:
            for table in ch.get("tables", []):
                ti = table.get("table_index", 0)
                rows_data = table.get("data", table.get("rows", []))
                for ri, row in enumerate(rows_data):
                    if not isinstance(row, list):
                        continue
                    for ci, cell in enumerate(row):
                        cell_text = ""
                        if isinstance(cell, dict):
                            cell_text = cell.get("text", "")
                        elif isinstance(cell, str):
                            cell_text = cell
                        if cell_text.strip():
                            entries.append({
                                "index": cell_idx,
                                "chapter": ch.get("chapter", ""),
                                "source_text": "",  # 表格单元格源文由 source_data 补充
                                "target_text": cell_text.strip(),
                                "style": "TABLE_CELL",
                                "heading_level": None,
                                "is_table_cell": True,
                                "table_index": ti,
                                "row": ri + 1,
                                "col": ci + 1,
                            })
                            cell_idx += 1

    return entries


def _merge_source_texts(entries: list[dict], source_data: dict):
    """将 source_data 的文本合并到 entries 中（按 index 匹配）。

    仅更新 source_text 为空的 entry（避免覆盖已有数据）。
    """
    # 构建 source_data 的 index → text 映射
    source_map = {}
    for ch in source_data.get("chapters", []):
        for para in ch.get("paragraphs", []):
            source_map[para.get("index", -1)] = para.get("text", "")

    for entry in entries:
        idx = entry.get("index", -1)
        if idx in source_map and not entry.get("source_text"):
            entry["source_text"] = source_map[idx]


def split_into_batches(entries: list[dict], batch_size: int = 15) -> list[dict]:
    """将条目列表按 batch_size 切分，返回 batch 列表。"""
    batches = []
    total = len(entries)
    total_batches = (total + batch_size - 1) // batch_size

    for batch_num in range(total_batches):
        start = batch_num * batch_size
        end = min(start + batch_size, total)
        batch_entries = entries[start:end]

        # 确定段落范围（只统计非表格条目）
        para_entries = [e for e in batch_entries if not e.get("is_table_cell")]
        if para_entries:
            first_idx = para_entries[0]["index"]
            last_idx = para_entries[-1]["index"]
            para_range = f"{first_idx}-{last_idx}"
        else:
            para_range = "tables-only"

        batch = {
            "batch_id": batch_num + 1,
            "total_batches": total_batches,
            "paragraph_range": para_range,
            "paragraph_count": len(para_entries),
            "table_cell_count": len(batch_entries) - len(para_entries),
            "total_items": len(batch_entries),
            "paragraphs": batch_entries,
        }
        batches.append(batch)

    return batches


def inject_context(batches: list[dict], context: dict) -> list[dict]:
    """将 phase4_context.json 中的术语/高风险标记注入到 batch 中。

    修改 batch["paragraphs"] 中的条目，添加:
      - is_high_risk: bool
      - relevant_terms: list
    """
    if not context:
        return batches

    high_risk_indices = set()
    for hr in context.get("high_risk_paragraphs", []):
        if isinstance(hr, dict):
            high_risk_indices.add(hr.get("index", hr.get("paragraph_index", -1)))
        elif isinstance(hr, (int, float)):
            high_risk_indices.add(int(hr))

    for batch in batches:
        for entry in batch["paragraphs"]:
            idx = entry.get("index", -1)
            if idx in high_risk_indices:
                entry["is_high_risk"] = True

    return batches


def main():
    parser = argparse.ArgumentParser(
        description="build_batches v2.23 — 从 split JSON 构建标准化 batch 数据"
    )
    parser.add_argument(
        "--target-split", required=True,
        help="split_target.json 路径 (Phase 2 产物)"
    )
    parser.add_argument(
        "--source-split", default=None,
        help="split_source.json 路径 (Phase 2 产物, optional)"
    )
    parser.add_argument(
        "--context", default=None,
        help="phase4_context.json 路径 (Phase 3.5 产物, optional)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=15,
        help="每批段落数 (默认: 15)"
    )
    parser.add_argument(
        "--output-dir", default=".",
        help="输出目录 (默认: 当前目录)"
    )

    args = parser.parse_args()

    # 加载数据
    target_data = load_json(args.target_split)
    if target_data is None:
        sys.stderr.write(f"[build_batches] 错误: 无法加载 {args.target_split}\n")
        sys.exit(1)

    source_data = None
    if args.source_split:
        source_data = load_json(args.source_split)

    context = None
    if args.context:
        context = load_json(args.context)

    # 收集所有条目
    entries = collect_all_entries(target_data, source_data)

    # 切分批次
    batches = split_into_batches(entries, args.batch_size)

    # 注入上下文
    if context:
        batches = inject_context(batches, context)

    # 写出 batch 文件
    os.makedirs(args.output_dir, exist_ok=True)
    for batch in batches:
        batch_id = batch["batch_id"]
        total = batch["total_batches"]
        fname = f"batch_{batch_id:02d}_data.json"
        fpath = os.path.join(args.output_dir, fname)
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(batch, f, ensure_ascii=False, indent=2)
        print(f"[build_batches] batch {batch_id}/{total} → {fpath} "
              f"({batch['paragraph_count']} paras + {batch['table_cell_count']} cells, "
              f"range: {batch['paragraph_range']})")

    # 汇总输出
    total_paras = sum(b["paragraph_count"] for b in batches)
    total_cells = sum(b["table_cell_count"] for b in batches)
    print(f"\n[build_batches] 完成: {len(batches)} batches, "
          f"{total_paras} paragraphs + {total_cells} table cells "
          f"(batch_size={args.batch_size})")


if __name__ == "__main__":
    main()
