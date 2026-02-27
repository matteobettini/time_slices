#!/usr/bin/env python3
"""
Add a new entry to slices.json or slices.it.json atomically.

Usage:
    python3 scripts/add-entry.py <entry_json>              # adds to slices.json
    python3 scripts/add-entry.py <entry_json> --lang it    # adds to slices.it.json
    python3 scripts/add-entry.py --file new-entry.json     # read entry from file
    python3 scripts/add-entry.py --file new-entry.json --lang it

The entry JSON must be a valid JSON object with at minimum: year, id, title, teaser.

Validations:
- Required fields: year, id, title, teaser
- No duplicate years or IDs
- Dimensions must use HTML formatting (warns if markdown detected)
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent  # scripts/ -> project root


def check_html_formatting(entry: dict) -> list:
    """Check if dimensions use HTML instead of markdown."""
    warnings = []
    dims = entry.get("dimensions", {})
    
    for key, dim in dims.items():
        content = dim.get("content", "")
        # Check for markdown bold/italic
        if re.search(r'\*\*[^*]+\*\*', content):
            warnings.append(f"  {key}: found **markdown bold** — use <strong> instead")
        if re.search(r'(?<!\*)\*[^*]+\*(?!\*)', content):
            warnings.append(f"  {key}: found *markdown italic* — use <em> instead")
    
    return warnings


def main():
    parser = argparse.ArgumentParser(description="Add entry to Time Slices JSON")
    parser.add_argument("entry", nargs="?", help="Entry as JSON string")
    parser.add_argument("--file", "-f", help="Read entry from JSON file")
    parser.add_argument("--lang", default="en", choices=["en", "it"], help="Target language (default: en)")
    parser.add_argument("--force", action="store_true", help="Skip duplicate checks (use for updates)")
    args = parser.parse_args()

    # Determine target file
    target = PROJECT_DIR / ("slices.it.json" if args.lang == "it" else "slices.json")

    # Get entry from arg or file
    if args.file:
        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = PROJECT_DIR / file_path
        entry = json.loads(file_path.read_text())
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

    # Check HTML formatting
    format_warnings = check_html_formatting(entry)
    if format_warnings:
        print("⚠️  Formatting warnings (use HTML, not markdown):", file=sys.stderr)
        for w in format_warnings:
            print(w, file=sys.stderr)
        print("", file=sys.stderr)

    # Read existing entries
    data = json.loads(target.read_text())

    # Check for duplicate year or id
    if not args.force:
        existing_years = {e["year"] for e in data}
        existing_ids = {e["id"] for e in data}
        
        if entry["year"] in existing_years:
            print(f"Error: year {entry['year']} already exists (use --force to override)", file=sys.stderr)
            sys.exit(1)
        if entry["id"] in existing_ids:
            print(f"Error: id '{entry['id']}' already exists (use --force to override)", file=sys.stderr)
            sys.exit(1)

    # Append and write
    data.append(entry)
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    print(f"✅ Added {entry['year']} '{entry['title']}' to {target.name}")
    print(f"   Total entries: {len(data)}")
    
    # Remind about Italian version
    if args.lang == "en":
        print(f"\n   Don't forget to add Italian version:")
        print(f"   python3 scripts/add-entry.py --file <italian-entry.json> --lang it")


if __name__ == "__main__":
    main()
