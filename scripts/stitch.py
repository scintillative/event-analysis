#!/usr/bin/env python3
"""
stitch.py — mechanical assembler for the event-analysis pipeline.

Takes the four subagent outputs (fact sheet, mechanism, historical reference,
consistency check) and concatenates them under a fixed structure into a single
analysis document.

This is deliberately mechanical. The coordinator is NOT allowed to "smooth" the
four pieces into prose itself, because the power to smooth is the power to
quietly re-interpret. A script has no such power. The first three subagents each
write a self-contained section; the consistency-check section is a table. The
script just stacks them under fixed headers, with clean seams.

The script does not edit, summarize, or reorder the section contents. It only
adds section headers. The coordinator appends its own note to the stitched file
afterwards, as a final clearly-marked section; the script itself does not add
it. The four stitched sections are purely the isolated pipeline's product.

The four input files are intermediate pipeline files in a temp directory that is
deleted after the run. The output file is the kept deliverable: it is written
directly to a durable location, named after the event/topic, and is not deleted.

Usage:
    python scripts/stitch.py \
        --facts /tmp/event-analysis-<ts>/fact_sheet.md \
        --mechanism /tmp/event-analysis-<ts>/mechanism.md \
        --historical /tmp/event-analysis-<ts>/historical.md \
        --consistency /tmp/event-analysis-<ts>/consistency.md \
        --title "<事件主题>" \
        --out "<durable-path>/<事件主题>.md"
"""

import argparse
import sys
from pathlib import Path


SECTIONS = [
    (
        "facts",
        "一 · 发生了什么",
        "综合多个来源还原事情经过：哪些大家说法一致、哪里有分歧、"
        "每个来源各自偏向什么。没有哪个来源是“客观”的，这里是把它们拼起来看。",
    ),
    (
        "mechanism",
        "二 · 为什么发生",
        "解释这件事为什么会发生。讲的是背后的机制——一个结构、"
        "一个决定怎样导致了结果。建立在上一节的事实之上。",
    ),
    (
        "historical",
        "三 · 可能的意义",
        "拿过去同类的事情作参照，看这件事可能有多大影响，"
        "以及它和那些先例的关键差别。",
    ),
    (
        "consistency",
        "四 · 交叉检验",
        "把第二节的机制解释和第三节的历史参照摆到一起对照。"
        "哪里对得上、哪里对不上，如实列出，不下结论。",
    ),
]


def read_section(path_str: str, label: str) -> str:
    path = Path(path_str)
    if not path.is_file():
        sys.exit(f"error: {label} file not found: {path_str}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        sys.exit(f"error: {label} file is empty: {path_str}")
    return text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mechanically stitch the four event-analysis sections."
    )
    parser.add_argument("--facts", required=True, help="fact_sheet.md path")
    parser.add_argument("--mechanism", required=True, help="mechanism.md path")
    parser.add_argument("--historical", required=True, help="historical.md path")
    parser.add_argument("--consistency", required=True, help="consistency.md path")
    parser.add_argument("--out", required=True, help="output path for analysis.md")
    parser.add_argument(
        "--title",
        default="事件分析",
        help="optional title for the stitched document",
    )
    args = parser.parse_args()

    inputs = {
        "facts": args.facts,
        "mechanism": args.mechanism,
        "historical": args.historical,
        "consistency": args.consistency,
    }

    parts = [f"# {args.title}", ""]

    for key, header, blurb in SECTIONS:
        body = read_section(inputs[key], key)
        parts.append("---")
        parts.append("")
        parts.append(f"## {header}")
        parts.append("")
        parts.append(f"> {blurb}")
        parts.append("")
        parts.append(body)
        parts.append("")

    out_path = Path(args.out)
    out_path.write_text("\n".join(parts), encoding="utf-8")
    print(f"stitched -> {out_path}")
    print("sections:", ", ".join(k for k, _, _ in SECTIONS))
    print(
        "next: the coordinator reads this file, appends its own note as a "
        "final section, then deletes the temp directory of intermediate files. "
        "The stitched file itself is the kept deliverable."
    )


if __name__ == "__main__":
    main()
