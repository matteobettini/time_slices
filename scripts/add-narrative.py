#!/usr/bin/env python3
"""
Add a thread narrative to thread-narratives.json.

Usage:
    python3 scripts/add-narrative.py <thread> <year_from> <year_to> "<en_text>" "<it_text>"
    
Example:
    python3 scripts/add-narrative.py death-of-god 1274 1347 "Aquinas died..." "Tommaso morì..."
    
Or interactively:
    python3 scripts/add-narrative.py --interactive
"""

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
NARRATIVES_FILE = PROJECT_DIR / "thread-narratives.json"


def load_narratives():
    with open(NARRATIVES_FILE) as f:
        return json.load(f)


def save_narratives(data):
    with open(NARRATIVES_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {NARRATIVES_FILE}")


def add_narrative(thread: str, year_from: int, year_to: int, en_text: str, it_text: str):
    """Add a narrative for a thread connection."""
    data = load_narratives()
    key = f"{year_from}→{year_to}"
    
    # Ensure thread exists in both languages
    if thread not in data['en']:
        data['en'][thread] = {}
    if thread not in data['it']:
        data['it'][thread] = {}
    
    # Check if already exists
    if key in data['en'].get(thread, {}):
        print(f"⚠️  Narrative {thread} {key} already exists (EN), overwriting...")
    
    data['en'][thread][key] = en_text
    data['it'][thread][key] = it_text
    
    save_narratives(data)
    print(f"✓ Added {thread}: {key}")


def list_missing():
    """Show missing thread narratives based on entries in slices.json."""
    with open(PROJECT_DIR / "slices.json") as f:
        entries = json.load(f)
    
    data = load_narratives()
    
    # Build thread->years map
    thread_years = {}
    for e in entries:
        for t in e.get('threads', []):
            if t not in thread_years:
                thread_years[t] = set()
            thread_years[t].add(int(e['year']))
    
    # Find missing consecutive pairs
    missing = []
    for thread, years in sorted(thread_years.items()):
        years = sorted(years)
        if len(years) < 2:
            continue
        for i in range(len(years) - 1):
            key = f"{years[i]}→{years[i+1]}"
            if key not in data['en'].get(thread, {}):
                missing.append((thread, years[i], years[i+1]))
    
    if missing:
        print(f"Missing {len(missing)} consecutive thread narratives:\n")
        for thread, y1, y2 in missing:
            print(f"  {thread}: {y1}→{y2}")
    else:
        print("✓ All consecutive thread narratives present!")
    
    return missing


def interactive_mode():
    """Interactively add missing narratives."""
    missing = list_missing()
    if not missing:
        return
    
    print("\n" + "="*60)
    for thread, y1, y2 in missing:
        print(f"\n📝 {thread}: {y1}→{y2}")
        print("Enter EN narrative (or 'skip' to skip, 'quit' to exit):")
        en = input("> ").strip()
        if en.lower() == 'quit':
            break
        if en.lower() == 'skip':
            continue
        
        print("Enter IT narrative:")
        it = input("> ").strip()
        if it.lower() == 'quit':
            break
        if it.lower() == 'skip':
            continue
        
        add_narrative(thread, y1, y2, en, it)


def main():
    if len(sys.argv) == 2 and sys.argv[1] == '--missing':
        list_missing()
    elif len(sys.argv) == 2 and sys.argv[1] == '--interactive':
        interactive_mode()
    elif len(sys.argv) == 6:
        thread = sys.argv[1]
        year_from = int(sys.argv[2])
        year_to = int(sys.argv[3])
        en_text = sys.argv[4]
        it_text = sys.argv[5]
        add_narrative(thread, year_from, year_to, en_text, it_text)
    else:
        print(__doc__)
        print("\nQuick commands:")
        print("  --missing      List missing consecutive narratives")
        print("  --interactive  Add missing narratives interactively")
        sys.exit(1)


if __name__ == "__main__":
    main()
