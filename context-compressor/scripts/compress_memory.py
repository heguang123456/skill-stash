#!/usr/bin/env python3
"""
Compress daily memory logs using the "generational compression" strategy.

Hot window (0-3 days):   keep full detail
Warm window (4-7 days):  extract key decisions only
Cold window (8-30 days): compress into single paragraph for CHANGELOG.md
Expired (>30 days):      delete after archiving

Usage:
    python compress_memory.py [--root PROJECT_ROOT] [--dry-run]
"""

import os
import re
from pathlib import Path
from datetime import datetime, timedelta, date
from argparse import ArgumentParser
from typing import NamedTuple


class LogEntry(NamedTuple):
    """Parsed daily log entry."""
    date: date
    path: Path
    content: str
    key_facts: list[str]  # Extracted key decisions/bugs/fixes


# Keywords that indicate important events worth preserving
IMPORTANT_KEYWORDS = [
    r"(完成|实现|修复|解决|发现|决策|决定|确定|确认)(了)?",
    r"(Bug|bug|BUG|缺陷|错误|问题).*(修复|解决|定位|发现)",
    r"(架构|设计|重构|优化|改进).*(决定|确定|完成|实现)",
    r"(技术陷阱|踩坑|注意事项|关键点)",
    r"(Milestone|里程碑|Release|版本|发布)",
    r"测试.*(通过|完成|全部)",
    r"模块.*(完成|✅)",
]

# Patterns to skip (transient, process-only content)
SKIP_PATTERNS = [
    r"^# .{0,30}今日进度.{0,30}$",  # "Today's progress" headers
    r"临时文件|中间结果|工具错误|intermediate",
    r"搜索.*结果|WebSearch|WebFetch",
]


def parse_date_from_filename(filename: str) -> date | None:
    """Extract date from YYYY-MM-DD.md filename."""
    match = re.match(r"(\d{4}-\d{2}-\d{2})\.md", filename)
    if match:
        return datetime.strptime(match.group(1), "%Y-%m-%d").date()
    return None


def extract_key_facts(content: str) -> list[str]:
    """Extract key facts from daily log content."""
    facts = []
    lines = content.strip().split("\n")

    for line in lines:
        # Skip markdown headers and empty lines
        if line.startswith("#") or not line.strip():
            continue
        # Skip transient lines
        if any(re.search(p, line, re.IGNORECASE) for p in SKIP_PATTERNS):
            continue
        # Match important keywords
        if any(re.search(kw, line, re.IGNORECASE) for kw in IMPORTANT_KEYWORDS):
            facts.append(line.strip())

    return facts


def classify_window(log_date: date, today: date) -> str:
    """Classify a log entry into hot/warm/cold/expired."""
    delta = (today - log_date).days
    if delta <= 3:
        return "hot"
    elif delta <= 7:
        return "warm"
    elif delta <= 30:
        return "cold"
    else:
        return "expired"


def compress_cold_logs(logs: list[LogEntry]) -> str:
    """Compress cold window logs into a single paragraph for CHANGELOG."""
    all_facts = []
    for log in logs:
        all_facts.extend(log.key_facts)

    if not all_facts:
        return ""

    # Deduplicate and organize
    unique_facts = list(dict.fromkeys(all_facts))  # Preserve order, remove dupes

    # Generate compressed summary
    lines = ["\n### Development Summary (compressed)\n"]
    for fact in unique_facts[:10]:  # Cap at 10 key facts
        lines.append(f"- {fact}")

    return "\n".join(lines)


def generate_warm_summary(logs: list[LogEntry]) -> str:
    """Generate a brief summary for warm window logs."""
    all_facts = []
    for log in logs:
        all_facts.extend(log.key_facts)

    if not all_facts:
        return ""

    return "\n".join(f"- {f}" for f in all_facts[:8])


def process_logs(memory_dir: Path, dry_run: bool = False) -> dict:
    """Main processing function.

    Returns a dict with:
        - hot_logs: list of LogEntry (keep as-is)
        - warm_summary: str (compressed summary)
        - cold_compressed: str (CHANGELOG-ready paragraph)
        - expired_to_delete: list of paths
        - stats: dict with counts
    """
    today = date.today()

    # Gather all daily logs
    log_entries: list[LogEntry] = []
    for f in sorted(memory_dir.glob("????-??-??.md")):
        log_date = parse_date_from_filename(f.name)
        if log_date is None:
            continue
        content = f.read_text(encoding="utf-8")
        key_facts = extract_key_facts(content)
        log_entries.append(LogEntry(log_date, f, content, key_facts))

    # Classify
    hot, warm, cold, expired = [], [], [], []
    for entry in log_entries:
        window = classify_window(entry.date, today)
        if window == "hot":
            hot.append(entry)
        elif window == "warm":
            warm.append(entry)
        elif window == "cold":
            cold.append(entry)
        else:
            expired.append(entry)

    # Generate compressed outputs
    result = {
        "hot_logs": hot,
        "warm_summary": generate_warm_summary(warm) if warm else "",
        "cold_compressed": compress_cold_logs(cold) if cold else "",
        "expired_to_delete": [e.path for e in expired],
        "stats": {
            "total": len(log_entries),
            "hot": len(hot),
            "warm_compressed": len(warm),
            "cold_archived": len(cold),
            "expired": len(expired),
        },
    }

    return result


def main():
    parser = ArgumentParser(description="Compress vType daily memory logs")
    parser.add_argument(
        "--root",
        default=os.getcwd(),
        help="Project root directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    memory_dir = root / ".workbuddy" / "memory"

    if not memory_dir.exists():
        print(f"Error: memory directory not found: {memory_dir}")
        sys.exit(1)

    result = process_logs(memory_dir, dry_run=args.dry_run)

    # Print summary
    s = result["stats"]
    print(f"Total logs: {s['total']}")
    print(f"  Hot (0-3 days, keep):   {s['hot']}")
    print(f"  Warm (4-7 days, compress): {s['warm_compressed']}")
    print(f"  Cold (8-30 days, archive): {s['cold_archived']}")
    print(f"  Expired (>30 days, delete): {s['expired']}")
    print()

    if result["cold_compressed"]:
        print("=== Compressed CHANGELOG Entry ===")
        print(result["cold_compressed"])
        print()

    if result["expired_to_delete"] and not args.dry_run:
        for p in result["expired_to_delete"]:
            print(f"  Would delete: {p.name}")


if __name__ == "__main__":
    main()
