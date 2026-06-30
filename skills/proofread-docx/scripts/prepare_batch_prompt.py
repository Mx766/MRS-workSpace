#!/usr/bin/env python3
"""
Phase 4 前置：Batch 数据富化

读取 Phase 2 的 batch 数据和 Phase 3.5 的 context，为每个 batch 注入：
  - domain_context: 领域信息
  - key_terminology: 相关的高频术语
  - mandatory_checks: 不可跳过的检查项
  - high_risk_flags: 该 batch 中的高风险段落标记

输出: cache/batch_N_prompt.json (供 Phase 4 Agent 直接使用)
"""

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


def load_json(filepath: str) -> dict | list | None:
    """安全加载 JSON 文件。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        sys.stderr.write(f"[prepare_batch] 无法加载 {filepath}: {e}\n")
        return None


def find_relevant_terms(
    batch_paras: list[dict],
    key_terminology: list[dict],
) -> list[dict]:
    """找出在该 batch 中出现的术语。

    Args:
        batch_paras: [{index, text, ...}]
        key_terminology: inject_context 输出的关键术语列表

    Returns:
        在 batch 中至少出现一次的关键术语（精简版，只含字段）
    """
    # 拼接 batch 全部文本
    batch_text = " ".join(p.get("text", p.get("target_text", "")) for p in batch_paras).lower()

    relevant = []
    for term in key_terminology:
        src = term.get("source", "").lower()
        if src and src in batch_text:
            relevant.append({
                "source": term["source"],
                "required_target": term["required_target"],
                "is_critical": term.get("is_critical", False),
                "translation_status": term.get("translation_status", "unknown"),
                "count_in_document": term.get("count", 0),
            })

    # 按 is_critical 优先，然后按 count 降序
    relevant.sort(key=lambda t: (not t["is_critical"], -t["count_in_document"]))
    return relevant


def find_high_risk_in_batch(
    batch_paras: list[dict],
    high_risk_paragraphs: list[dict],
) -> list[dict]:
    """找出该 batch 中的高风险段落。

    Args:
        batch_paras: [{index, ...}]
        high_risk_paragraphs: inject_context 输出的高风险段落列表

    Returns:
        该 batch 中的高风险段落列表
    """
    batch_indices = {p.get("index", p.get("paragraph_index", -1)) for p in batch_paras}
    return [p for p in high_risk_paragraphs if p.get("paragraph_index") in batch_indices]


def build_batch_prompt_context(
    batch_data: dict,
    context: dict,
) -> dict:
    """为单个 batch 构建富化的 prompt 数据。

    Args:
        batch_data: 原始 batch 数据 {batch_id, paragraphs: [{index, target_text, ...}]}
        context: phase4_context.json 内容

    Returns:
        富化后的 batch 数据
    """
    batch_paras = batch_data.get("paragraphs", [])
    batch_indices = [p.get("index", p.get("paragraph_index", -1)) for p in batch_paras]

    # 找出相关术语
    relevant_terms = find_relevant_terms(batch_paras, context.get("key_terminology", []))

    # 找出高风险段落
    high_risk = find_high_risk_in_batch(batch_paras, context.get("high_risk_paragraphs", []))

    # 构建 domain_context 摘要
    domain = context.get("domain", {})
    domain_context = {
        "primary": domain.get("primary", "通用"),
        "notes": domain.get("domain_notes", ""),
        "confidence": domain.get("confidence", 0),
    }

    # 构建 mandatory_checks 摘要
    mandatory_checks = context.get("mandatory_checks", [])

    # 构建结构相关项
    structure_items = []
    for s in context.get("structure_checklist", []):
        s_type = s.get("type", "")
        if s_type == "cross_format_note" or s_type == "cross_format_figure_captions":
            structure_items.append(s.get("note", ""))
        elif s_type == "cross_format_broken_paragraphs":
            # 检查该 batch 是否有断段
            broken_in_batch = [
                idx for idx in s.get("paragraph_indices", [])
                if idx in batch_indices
            ]
            if broken_in_batch:
                structure_items.append(
                    f"本批有 {len(broken_in_batch)} 个不以标点结尾的段落（可能为跨格式断段）: {broken_in_batch}"
                )

    # 构建 meta（跨格式标志等）
    meta = context.get("meta", {})
    is_cross_format = meta.get("is_cross_format", False)

    enriched = dict(batch_data)  # 复制原数据
    enriched["_prompt_context"] = {
        "domain_context": domain_context,
        "key_terminology": relevant_terms,
        "mandatory_checks": mandatory_checks,
        "high_risk_paragraphs": high_risk,
        "structure_notes": structure_items,
        "is_cross_format": is_cross_format,
        "cross_format_warning": (
            "原文为 PDF 格式，本模式使用逐页匹配，所有机械检查结果仅供参考，可能存在误报。"
            if is_cross_format else ""
        ),
    }

    return enriched


def main():
    parser = argparse.ArgumentParser(
        description="Phase 4 前置：为每个 batch 注入 domain context 和 mandatory checks"
    )
    parser.add_argument("--batch-data", required=True, help="单个 batch 数据文件 (batch_N_data.json)")
    parser.add_argument("--context", required=True, help="phase4_context.json 路径")
    parser.add_argument("--output", "-o", required=True, help="输出路径 (batch_N_prompt.json)")
    args = parser.parse_args()

    # 加载
    batch_data = load_json(args.batch_data)
    context = load_json(args.context)

    if batch_data is None:
        sys.stderr.write(f"[prepare_batch] 无法加载 batch 数据: {args.batch_data}\n")
        sys.exit(1)
    if context is None:
        sys.stderr.write(f"[prepare_batch] 无法加载 context: {args.context}\n")
        sys.exit(1)

    # 富化
    enriched = build_batch_prompt_context(batch_data, context)

    # 输出
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    batch_id = batch_data.get("batch_id", "?")
    n_paras = len(batch_data.get("paragraphs", []))
    n_terms = len(enriched["_prompt_context"]["key_terminology"])
    n_risk = len(enriched["_prompt_context"]["high_risk_paragraphs"])

    print(f"Batch {batch_id}: {n_paras} 段, {n_terms} 相关术语, {n_risk} 高风险")
    print(f"输出: {args.output}")


if __name__ == "__main__":
    main()
