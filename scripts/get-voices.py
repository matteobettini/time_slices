#!/usr/bin/env python3
"""
List available Edge TTS voices for Time Slices podcasts.

Usage:
    python3 scripts/get-voices.py          # List recommended voices
    python3 scripts/get-voices.py --json   # Output as JSON
"""

import argparse
import json

# Best natural-sounding Edge TTS voices (curated from community feedback)
VOICES = [
    # English - top picks for natural narration
    {"name": "en-GB-RyanNeural", "gender": "Male", "locale": "en-GB", "notes": "Least robotic, natural flow"},
    {"name": "en-US-AvaNeural", "gender": "Female", "locale": "en-US", "notes": "Expressive, caring, pleasant"},
    {"name": "en-US-AndrewNeural", "gender": "Male", "locale": "en-US", "notes": "Warm, confident, authentic"},
    {"name": "en-US-SteffanNeural", "gender": "Male", "locale": "en-US", "notes": "Rational, clear"},
    # Italian
    {"name": "it-IT-DiegoNeural", "gender": "Male", "locale": "it-IT", "notes": "Natural male Italian"},
    {"name": "it-IT-IsabellaNeural", "gender": "Female", "locale": "it-IT", "notes": "Natural female Italian"},
]


def main():
    parser = argparse.ArgumentParser(description="List available Edge TTS voices")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.json:
        print(json.dumps(VOICES, indent=2))
    else:
        en_voices = [v for v in VOICES if v["locale"].startswith("en-")]
        it_voices = [v for v in VOICES if v["locale"].startswith("it-")]
        
        print(f"Recommended Edge TTS voices ({len(VOICES)} total):\n")
        
        print("🇬🇧🇺🇸 ENGLISH:")
        print("| Voice                | Gender | Notes                        |")
        print("|----------------------|--------|------------------------------|")
        for v in en_voices:
            print(f"| {v['name']:<20} | {v['gender']:<6} | {v['notes']:<28} |")
        
        print(f"\n🇮🇹 ITALIAN:")
        print("| Voice                | Gender | Notes                        |")
        print("|----------------------|--------|------------------------------|")
        for v in it_voices:
            print(f"| {v['name']:<20} | {v['gender']:<6} | {v['notes']:<28} |")
        
        print("\n⚠️  Edge TTS does NOT support style instructions.")
        print("   Voice personality is determined entirely by voice choice.")
        print("\nUsage: --voice <voice-name>")


if __name__ == "__main__":
    main()
