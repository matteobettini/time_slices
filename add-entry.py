#!/usr/bin/env python3
"""
Add a new entry to slices.json or slices.it.json atomically.

Usage:
    python3 add-entry.py <entry_json>              # adds to slices.json
    python3 add-entry.py <entry_json> --lang it    # adds to slices.it.json
    python3 add-entry.py --file new-entry.json     # read entry from file
    python3 add-entry.py --file new-entry.json --lang it

The entry JSON must be a valid JSON object with at minimum: year, id, title, teaser.
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

def main():
    parser = argparse.ArgumentParser(description="Add entry to Time Slices JSON")
    parser.add_argument("entry", nargs="?", help="Entry as JSON string")
    parser.add_argument("--file", "-f", help="Read entry from JSON file")
    parser.add_argument("--lang", default="en", choices=["en", "it"], help="Target language (default: en)")
    args = parser.parse_args()

    # Determine target file
    target = SCRIPT_DIR / ("slices.it.json" if args.lang == "it" else "slices.json")

    # Get entry from arg or file
    if args.file:
        entry = json.loads(Path(args.file).read_text())
    elif args.entry:
        entry = json.loads(args.entry)
    else:
        print("Error: provide entry as argument or --file", file=sys.stderr)
        sys.exit(1)

    # Validate required fields
    required = ["year", "id", "title", "teaser"]
    missing = [f for f in required if f not in entry]
    if missing:
        print(f"Error: missing required fields: {missing}", file=sys.stderr)
        sys.exit(1)

    # Read existing entries
    data = json.loads(target.read_text())

    # Check for duplicate year or id
    existing_years = {e["year"] for e in data}
    existing_ids = {e["id"] for e in data}
    
    if entry["year"] in existing_years:
        print(f"Error: year {entry['year']} already exists", file=sys.stderr)
        sys.exit(1)
    if entry["id"] in existing_ids:
        print(f"Error: id '{entry['id']}' already exists", file=sys.stderr)
        sys.exit(1)

    # Append and write
    data.append(entry)
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    print(f"Added {entry['year']} '{entry['title']}' to {target.name}")
    print(f"Total entries: {len(data)}")

if __name__ == "__main__":
    main()
