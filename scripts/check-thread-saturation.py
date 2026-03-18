#!/usr/bin/env python3
"""
Check thread saturation levels and warn about overused threads.

Usage:
    python3 check-thread-saturation.py [--threshold 0.3] [--json]
    
Flags threads that appear in more than threshold% of all entries.
Default threshold: 30%

Exit codes:
    0 = no saturated threads (or only warning)
    1 = has saturated threads above threshold
"""

import json
import sys
from pathlib import Path
from collections import Counter

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
SLICES_JSON = PROJECT_DIR / "slices.json"

# Threshold for "saturated" - threads appearing in more than this fraction of entries
DEFAULT_THRESHOLD = 0.30


def get_thread_saturation(threshold: float = DEFAULT_THRESHOLD) -> dict:
    """Analyze thread usage and return saturation data."""
    
    with open(SLICES_JSON) as f:
        entries = json.load(f)
    
    total_entries = len(entries)
    threads_counter = Counter()
    
    for entry in entries:
        for thread in entry.get("threads", []):
            threads_counter[thread] += 1
    
    # Calculate saturation
    saturated = []
    warning = []
    healthy = []
    
    for thread, count in threads_counter.most_common():
        ratio = count / total_entries
        thread_info = {
            "thread": thread,
            "count": count,
            "total": total_entries,
            "ratio": ratio,
            "percent": f"{ratio * 100:.1f}%"
        }
        
        if ratio > threshold:
            saturated.append(thread_info)
        elif ratio > threshold * 0.7:  # Warning zone: 70-100% of threshold
            warning.append(thread_info)
        else:
            healthy.append(thread_info)
    
    return {
        "total_entries": total_entries,
        "threshold": threshold,
        "saturated": saturated,
        "warning": warning,
        "healthy": healthy,
        "all_threads": threads_counter.most_common()
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Check thread saturation levels")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                        help=f"Saturation threshold (default: {DEFAULT_THRESHOLD})")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    result = get_thread_saturation(args.threshold)
    
    if args.json:
        print(json.dumps(result, indent=2))
        sys.exit(1 if result["saturated"] else 0)
    
    print("# Thread Saturation Report")
    print()
    print(f"Total entries: {result['total_entries']}")
    print(f"Saturation threshold: {args.threshold * 100:.0f}%")
    print()
    
    if result["saturated"]:
        print("## 🔴 SATURATED THREADS (avoid unless central to entry)")
        print()
        print("These threads appear in too many entries. Do NOT add them unless your entry is *specifically about* this theme.")
        print()
        for t in result["saturated"]:
            print(f"  - `{t['thread']}`: {t['count']}/{t['total']} entries ({t['percent']})")
        print()
    
    if result["warning"]:
        print("## 🟡 WARNING ZONE (approaching saturation)")
        print()
        for t in result["warning"]:
            print(f"  - `{t['thread']}`: {t['count']}/{t['total']} entries ({t['percent']})")
        print()
    
    if result["healthy"]:
        print("## 🟢 HEALTHY THREADS (good candidates for connection)")
        print()
        # Show top 15 healthy threads
        for t in result["healthy"][:15]:
            print(f"  - `{t['thread']}`: {t['count']}/{t['total']} entries ({t['percent']})")
        if len(result["healthy"]) > 15:
            print(f"  ... and {len(result['healthy']) - 15} more")
        print()
    
    # Exit code
    if result["saturated"]:
        print("---")
        print(f"⚠️  {len(result['saturated'])} thread(s) above saturation threshold.")
        sys.exit(1)
    else:
        print("---")
        print("✅ No saturated threads.")
        sys.exit(0)


if __name__ == "__main__":
    main()
