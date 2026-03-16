#!/usr/bin/env python3
"""
Show 2-3 entries nearest to a given year to check for content overlap.

Usage:
    python3 nearby-entries.py <year>
    python3 nearby-entries.py 1517
    python3 nearby-entries.py 1517 --count 3

Output: Full content of nearby entries so the agent can avoid duplication.
"""

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
SLICES_JSON = PROJECT_DIR / "slices.json"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Show entries nearest to a given year")
    parser.add_argument("year", type=int, help="Target year to find neighbors for")
    parser.add_argument("--count", type=int, default=3, help="Number of nearby entries to show (default: 3)")
    args = parser.parse_args()
    
    target_year = args.year
    count = args.count
    
    with open(SLICES_JSON) as f:
        entries = json.load(f)
    
    # Parse years and calculate distances
    entries_with_distance = []
    for entry in entries:
        year_str = entry["year"]
        try:
            year_int = int(year_str)
            distance = abs(year_int - target_year)
            entries_with_distance.append((distance, year_int, entry))
        except ValueError:
            continue
    
    # Sort by distance, then by year
    entries_with_distance.sort(key=lambda x: (x[0], x[1]))
    
    # Get nearest entries (excluding exact match if it exists)
    nearby = []
    for distance, year_int, entry in entries_with_distance:
        if distance == 0:
            print(f"⚠️  Year {target_year} already has an entry: {entry['id']}")
            print()
            continue
        nearby.append((distance, year_int, entry))
        if len(nearby) >= count:
            break
    
    if not nearby:
        print(f"No nearby entries found for year {target_year}")
        return
    
    print(f"# Entries Near {target_year}")
    print()
    print(f"Showing {len(nearby)} nearest entries. Review these to avoid content overlap.")
    print()
    
    for distance, year_int, entry in nearby:
        print(f"## {entry['year']} — {entry['title']} ({distance} years away)")
        print()
        print(f"**ID:** `{entry['id']}`")
        print(f"**Teaser:** {entry['teaser']}")
        print(f"**Location:** {entry.get('location', {}).get('place', 'Unknown')}")
        print(f"**Threads:** {', '.join(entry.get('threads', []))}")
        print()
        
        dims = entry.get("dimensions", {})
        for key in ["art", "lit", "phil", "hist", "conn"]:
            if key in dims:
                dim = dims[key]
                content = dim.get("content", "")
                print(f"### {dim.get('label', key)}")
                print(content)
                print()
        
        if "conn" in dims and dims["conn"].get("funFact"):
            print(f"**Fun Fact:** {dims['conn']['funFact']}")
            print()
        
        print("---")
        print()
    
    # Summary of key themes to avoid
    print("## Key Themes in Nearby Entries (avoid duplicating)")
    print()
    all_threads = set()
    key_figures = set()
    for _, _, entry in nearby:
        all_threads.update(entry.get("threads", []))
        # Extract bold names from content
        dims = entry.get("dimensions", {})
        for key in dims:
            content = dims[key].get("content", "")
            # Find <strong>...</strong> patterns
            import re
            names = re.findall(r'<strong>([^<]+)</strong>', content)
            key_figures.update(names)
    
    print(f"**Threads:** {', '.join(sorted(all_threads))}")
    print()
    print(f"**Key figures mentioned:** {', '.join(sorted(key_figures)[:20])}")
    if len(key_figures) > 20:
        print(f"  _(and {len(key_figures) - 20} more)_")
    print()


if __name__ == "__main__":
    main()
