#!/usr/bin/env python3
"""
List available TTS voices for Time Slices podcasts.

Usage:
    python3 scripts/get-voices.py          # List all voices
    python3 scripts/get-voices.py --json   # Output as JSON
"""

import argparse
import json

# OpenAI TTS voices available for gpt-4o-mini-tts
# ❌ onyx is excluded — produces buggy/glitchy output
VOICES = [
    {"name": "alloy", "description": "Neutral, balanced, versatile"},
    {"name": "ash", "description": "Deep, authoritative, gravitas"},
    {"name": "ballad", "description": "Warm, expressive, storytelling"},
    {"name": "coral", "description": "Dynamic, energetic, engaging"},
    {"name": "echo", "description": "Clear, confident, presence"},
    {"name": "fable", "description": "Warm, narrative, storyteller quality"},
    {"name": "nova", "description": "Warm, friendly, enthusiastic"},
    {"name": "sage", "description": "Measured, intellectual, precise"},
    {"name": "shimmer", "description": "Bright, clear, optimistic"},
    {"name": "verse", "description": "Expressive, poetic, nuanced"},
]

# DO NOT USE
EXCLUDED = ["onyx"]  # Buggy/glitchy output


def main():
    parser = argparse.ArgumentParser(description="List available TTS voices")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.json:
        print(json.dumps({"voices": VOICES, "excluded": EXCLUDED}, indent=2))
    else:
        print("Available voices for Time Slices podcasts:\n")
        print("| Voice   | Description                        |")
        print("|---------|-----------------------------------|")
        for v in VOICES:
            print(f"| {v['name']:<7} | {v['description']:<35} |")
        print(f"\n⚠️  Do NOT use: {', '.join(EXCLUDED)} (buggy)")
        print("\nUsage: --voice <name> --style \"Your style instructions\"")


if __name__ == "__main__":
    main()
