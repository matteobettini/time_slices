#!/usr/bin/env python3
"""
Output a compact summary of existing Time Slices entries for the cron agent.

Usage:
    python3 summarize-entries.py [--examples N]

Outputs:
- All years and IDs covered
- Thread saturation warnings (IMPORTANT!)
- All threads used (with frequency)
- Geographic distribution
- N example entries (full content) for reference
"""

import json
import random
from pathlib import Path
from collections import Counter

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent  # scripts/ -> project root
SLICES_JSON = PROJECT_DIR / "slices.json"
SLICES_IT_JSON = PROJECT_DIR / "slices.it.json"
SCRIPTS_DIR = PROJECT_DIR / "audio" / "scripts"

# Thread saturation threshold - warn if thread appears in more than this % of entries
SATURATION_THRESHOLD = 0.30


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--examples", type=int, default=2, help="Number of full examples to show")
    args = parser.parse_args()
    
    with open(SLICES_JSON) as f:
        entries = json.load(f)
    
    # Sort by year
    entries_sorted = sorted(entries, key=lambda e: int(str(e["year"])) if str(e["year"]).lstrip('-').isdigit() else 0)
    
    # Collect data
    years_covered = []
    threads_counter = Counter()
    locations = []
    
    for entry in entries_sorted:
        year = entry["year"]
        eid = entry["id"]
        title = entry["title"]
        loc = entry.get("location", {})
        threads = entry.get("threads", [])
        
        years_covered.append({
            "year": year,
            "id": eid,
            "title": title,
            "place": loc.get("place", "Unknown")
        })
        
        for t in threads:
            threads_counter[t] += 1
        
        if loc:
            locations.append(loc.get("place", "Unknown"))
    
    # Output summary
    print("# Time Slices — Entry Summary")
    print()
    print(f"**Total entries:** {len(entries)}")
    print()
    
    # Years covered
    print("## Years Covered")
    print()
    print("| Year | ID | Title | Place |")
    print("|------|-----|-------|-------|")
    for item in years_covered:
        print(f"| {item['year']} | {item['id']} | {item['title']} | {item['place']} |")
    print()
    
    # Timeline gaps
    print("## Timeline Gaps")
    print()
    years_int = [int(str(e["year"])) for e in entries_sorted if str(e["year"]).lstrip('-').isdigit()]
    years_int.sort()
    gaps = []
    for i in range(len(years_int) - 1):
        gap = years_int[i+1] - years_int[i]
        if gap > 100:
            gaps.append(f"{years_int[i]} → {years_int[i+1]} ({gap} years)")
    if gaps:
        for g in gaps:
            print(f"- {g}")
    else:
        print("No major gaps (>100 years)")
    print()
    
    # Thread Saturation Warning (CRITICAL)
    total_entries = len(entries)
    saturated = []
    warning_zone = []
    for thread, count in threads_counter.most_common():
        ratio = count / total_entries
        if ratio > SATURATION_THRESHOLD:
            saturated.append((thread, count, ratio))
        elif ratio > SATURATION_THRESHOLD * 0.7:
            warning_zone.append((thread, count, ratio))
    
    if saturated:
        print("## ⚠️ SATURATED THREADS — DO NOT USE CASUALLY")
        print()
        print("These threads appear in too many entries. **Do NOT add them to your entry unless it is SPECIFICALLY ABOUT this theme.**")
        print()
        for thread, count, ratio in saturated:
            print(f"- 🔴 `{thread}`: {count}/{total_entries} entries ({ratio*100:.0f}%)")
        print()
    
    if warning_zone:
        print("## 🟡 Warning Zone (approaching saturation)")
        print()
        for thread, count, ratio in warning_zone:
            print(f"- `{thread}`: {count}/{total_entries} entries ({ratio*100:.0f}%)")
        print()
    
    # Threads
    print("## Threads Used")
    print()
    print("| Thread | Count |")
    print("|--------|-------|")
    for thread, count in threads_counter.most_common():
        print(f"| `{thread}` | {count} |")
    print()
    
    # Geographic distribution
    print("## Geographic Distribution")
    print()
    loc_counter = Counter(locations)
    for place, count in loc_counter.most_common():
        print(f"- {place}: {count}")
    print()
    
    # Example entries
    print(f"## Example Entries ({args.examples} samples)")
    print()
    print("Use these as reference for content style, structure, and depth:")
    print()
    
    # Pick diverse examples (different eras if possible)
    if len(entries) <= args.examples:
        examples = entries
    else:
        # Try to get examples from different time periods
        examples = random.sample(entries, args.examples)
    
    for entry in examples:
        print(f"### {entry['year']} — {entry['title']}")
        print()
        print(f"**ID:** `{entry['id']}`")
        print(f"**Teaser:** {entry['teaser']}")
        print(f"**Threads:** {', '.join(entry.get('threads', []))}")
        print()
        
        dims = entry.get("dimensions", {})
        for key in ["art", "lit", "phil", "hist", "conn"]:
            if key in dims:
                dim = dims[key]
                # Truncate long content for examples
                content = dim.get("content", "")
                if len(content) > 500:
                    content = content[:500] + "..."
                print(f"**{dim.get('label', key)}:** {content}")
                print()
        
        if "conn" in dims and "funFact" in dims["conn"]:
            print(f"**Fun Fact:** {dims['conn']['funFact']}")
            print()
        
        print("---")
        print()
    
    # Podcast script examples (using the same examples selected above)
    print(f"## Podcast Script Examples")
    print()
    print("Podcast scripts should be ~350-400 words, storytelling style, evocative but historically accurate.")
    print()
    
    for entry in examples:
        script_path = SCRIPTS_DIR / f"{entry['id']}.txt"
        if script_path.exists():
            print(f"### Script: {entry['year']} — {entry['title']}")
            print(f"File: `audio/scripts/{entry['id']}.txt`")
            print()
            print("```")
            print(script_path.read_text().strip())
            print("```")
            print()


if __name__ == "__main__":
    main()
