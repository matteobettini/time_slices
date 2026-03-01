#!/usr/bin/env python3
"""
List available Edge TTS voices for Time Slices podcasts.

Usage:
    python3 scripts/get-voices.py              # List all voices
    python3 scripts/get-voices.py --lang en    # Filter by language (en, it, fr, etc.)
    python3 scripts/get-voices.py --json       # Output as JSON
"""

import argparse
import subprocess
import sys


def get_all_voices():
    """Get all voices from edge-tts --list-voices."""
    result = subprocess.run(
        ["edge-tts", "--list-voices"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return []
    
    voices = []
    lines = result.stdout.strip().split("\n")
    
    # Skip header lines (first 2 lines: header + separator)
    for line in lines[2:]:
        parts = line.split()
        if len(parts) >= 2:
            name = parts[0]
            gender = parts[1] if len(parts) > 1 else ""
            # Rest is categories and personalities
            voices.append({
                "name": name,
                "gender": gender,
            })
    
    return voices


def main():
    parser = argparse.ArgumentParser(description="List available Edge TTS voices")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--lang", help="Filter by language code (e.g., en, it, fr, de)")
    args = parser.parse_args()

    voices = get_all_voices()
    
    if not voices:
        print("Failed to get voices. Make sure edge-tts is installed: pip install edge-tts")
        sys.exit(1)
    
    # Filter by language if specified
    if args.lang:
        lang_prefix = f"{args.lang.lower()}-"
        voices = [v for v in voices if v["name"].lower().startswith(lang_prefix)]

    if args.json:
        import json
        print(json.dumps(voices, indent=2))
    else:
        print(f"Available Edge TTS voices ({len(voices)} total):\n")
        print("| Voice                              | Gender |")
        print("|------------------------------------|--------|")
        for v in voices:
            print(f"| {v['name']:<34} | {v['gender']:<6} |")
        
        print(f"\n💡 Filter by language: --lang en, --lang it, --lang fr, etc.")
        print("⚠️  Edge TTS does NOT support style instructions. Voice personality is determined by voice choice.")


if __name__ == "__main__":
    main()
