#!/usr/bin/env python3
"""
List available Edge TTS voices for Time Slices podcasts.

Usage:
    python3 scripts/get-voices.py          # List recommended voices
    python3 scripts/get-voices.py --all    # List all 300+ voices
    python3 scripts/get-voices.py --json   # Output as JSON
"""

import argparse
import json

# Recommended voices for Time Slices podcasts
# These are high-quality neural voices that work well for narration

VOICES_EN = [
    # US English
    {"name": "en-US-GuyNeural", "gender": "Male", "accent": "US", "notes": "Casual, friendly"},
    {"name": "en-US-JennyNeural", "gender": "Female", "accent": "US", "notes": "Friendly, warm"},
    {"name": "en-US-AriaNeural", "gender": "Female", "accent": "US", "notes": "Professional, clear"},
    {"name": "en-US-ChristopherNeural", "gender": "Male", "accent": "US", "notes": "Clear, authoritative"},
    {"name": "en-US-MichelleNeural", "gender": "Female", "accent": "US", "notes": "Warm, engaging"},
    {"name": "en-US-EricNeural", "gender": "Male", "accent": "US", "notes": "Neutral"},
    {"name": "en-US-RogerNeural", "gender": "Male", "accent": "US", "notes": "Deep, storytelling"},
    {"name": "en-US-AvaNeural", "gender": "Female", "accent": "US", "notes": "Young, dynamic"},
    {"name": "en-US-BrianNeural", "gender": "Male", "accent": "US", "notes": "Conversational"},
    {"name": "en-US-AndrewMultilingualNeural", "gender": "Male", "accent": "US", "notes": "Multilingual capable"},
    # UK English
    {"name": "en-GB-RyanNeural", "gender": "Male", "accent": "UK", "notes": "British, professional"},
    {"name": "en-GB-SoniaNeural", "gender": "Female", "accent": "UK", "notes": "British, warm"},
    {"name": "en-GB-LibbyNeural", "gender": "Female", "accent": "UK", "notes": "British, clear"},
    {"name": "en-GB-ThomasNeural", "gender": "Male", "accent": "UK", "notes": "British, authoritative"},
    # Australian
    {"name": "en-AU-NatashaNeural", "gender": "Female", "accent": "AU", "notes": "Australian"},
    {"name": "en-AU-WilliamNeural", "gender": "Male", "accent": "AU", "notes": "Australian"},
]

VOICES_IT = [
    {"name": "it-IT-DiegoNeural", "gender": "Male", "notes": "Clear, professional"},
    {"name": "it-IT-IsabellaNeural", "gender": "Female", "notes": "Warm, engaging"},
    {"name": "it-IT-ElsaNeural", "gender": "Female", "notes": "Clear, neutral"},
    {"name": "it-IT-GiuseppeMultilingualNeural", "gender": "Male", "notes": "Multilingual capable"},
]

# Default voices for Time Slices
DEFAULTS = {
    "en": "en-GB-RyanNeural",  # British voice suits historical narration well
    "it": "it-IT-DiegoNeural",
}


def main():
    parser = argparse.ArgumentParser(description="List available Edge TTS voices")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--all", action="store_true", help="Show all voices (run edge-tts --list-voices)")
    args = parser.parse_args()

    if args.all:
        import subprocess
        # Edge TTS can list all voices but our wrapper doesn't support it
        # Just show the curated list with a note
        print("Edge TTS has 300+ voices. Here are the recommended ones for Time Slices.\n")
        print("For the full list, see: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support\n")

    if args.json:
        print(json.dumps({
            "english": VOICES_EN,
            "italian": VOICES_IT,
            "defaults": DEFAULTS,
        }, indent=2))
    else:
        print("Recommended voices for Time Slices podcasts:\n")
        
        print("🇺🇸🇬🇧 ENGLISH VOICES:")
        print("| Voice                           | Gender | Accent | Notes              |")
        print("|---------------------------------|--------|--------|--------------------|")
        for v in VOICES_EN:
            print(f"| {v['name']:<31} | {v['gender']:<6} | {v.get('accent', ''):<6} | {v['notes']:<18} |")
        
        print(f"\n🇮🇹 ITALIAN VOICES:")
        print("| Voice                           | Gender | Notes              |")
        print("|---------------------------------|--------|--------------------|")
        for v in VOICES_IT:
            print(f"| {v['name']:<31} | {v['gender']:<6} | {v['notes']:<18} |")
        
        print(f"\n📌 DEFAULTS:")
        print(f"   English: {DEFAULTS['en']}")
        print(f"   Italian: {DEFAULTS['it']}")
        
        print("\n⚠️  Edge TTS does NOT support style instructions like OpenAI TTS.")
        print("   Voice personality is determined entirely by the voice choice.")
        print("\nUsage: --voice <voice-name>")


if __name__ == "__main__":
    main()
