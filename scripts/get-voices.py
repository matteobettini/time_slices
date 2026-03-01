#!/usr/bin/env python3
"""
List available Edge TTS voices for Time Slices podcasts.

Usage:
    python3 scripts/get-voices.py          # List all UK, US English and Italian voices
    python3 scripts/get-voices.py --json   # Output as JSON
"""

import argparse
import json

# UK, US English and Italian Edge TTS voices
VOICES = [
    # British English
    {"name": "en-GB-LibbyNeural", "gender": "Female", "locale": "en-GB", "notes": "Friendly, Positive"},
    {"name": "en-GB-MaisieNeural", "gender": "Female", "locale": "en-GB", "notes": "Friendly, Positive"},
    {"name": "en-GB-RyanNeural", "gender": "Male", "locale": "en-GB", "notes": "Friendly, Positive"},
    {"name": "en-GB-SoniaNeural", "gender": "Female", "locale": "en-GB", "notes": "Friendly, Positive"},
    {"name": "en-GB-ThomasNeural", "gender": "Male", "locale": "en-GB", "notes": "Friendly, Positive"},
    # US English
    {"name": "en-US-AnaNeural", "gender": "Female", "locale": "en-US", "notes": "Cartoon, Cute"},
    {"name": "en-US-AndrewMultilingualNeural", "gender": "Male", "locale": "en-US", "notes": "Warm, Confident, Authentic"},
    {"name": "en-US-AndrewNeural", "gender": "Male", "locale": "en-US", "notes": "Warm, Confident, Authentic"},
    {"name": "en-US-AriaNeural", "gender": "Female", "locale": "en-US", "notes": "Positive, Confident"},
    {"name": "en-US-AvaMultilingualNeural", "gender": "Female", "locale": "en-US", "notes": "Expressive, Caring, Pleasant"},
    {"name": "en-US-AvaNeural", "gender": "Female", "locale": "en-US", "notes": "Expressive, Caring, Pleasant"},
    {"name": "en-US-BrianMultilingualNeural", "gender": "Male", "locale": "en-US", "notes": "Approachable, Casual, Sincere"},
    {"name": "en-US-BrianNeural", "gender": "Male", "locale": "en-US", "notes": "Approachable, Casual, Sincere"},
    {"name": "en-US-ChristopherNeural", "gender": "Male", "locale": "en-US", "notes": "Reliable, Authority"},
    {"name": "en-US-EmmaMultilingualNeural", "gender": "Female", "locale": "en-US", "notes": "Cheerful, Clear"},
    {"name": "en-US-EmmaNeural", "gender": "Female", "locale": "en-US", "notes": "Cheerful, Clear"},
    {"name": "en-US-EricNeural", "gender": "Male", "locale": "en-US", "notes": "Rational"},
    {"name": "en-US-GuyNeural", "gender": "Male", "locale": "en-US", "notes": "Passion"},
    {"name": "en-US-JennyNeural", "gender": "Female", "locale": "en-US", "notes": "Friendly, Considerate"},
    {"name": "en-US-MichelleNeural", "gender": "Female", "locale": "en-US", "notes": "Friendly, Pleasant"},
    {"name": "en-US-RogerNeural", "gender": "Male", "locale": "en-US", "notes": "Lively"},
    {"name": "en-US-SteffanNeural", "gender": "Male", "locale": "en-US", "notes": "Rational"},
    # Italian
    {"name": "it-IT-DiegoNeural", "gender": "Male", "locale": "it-IT", "notes": "Friendly, Positive"},
    {"name": "it-IT-ElsaNeural", "gender": "Female", "locale": "it-IT", "notes": "Friendly, Positive"},
    {"name": "it-IT-GiuseppeMultilingualNeural", "gender": "Male", "locale": "it-IT", "notes": "Friendly, Positive"},
    {"name": "it-IT-IsabellaNeural", "gender": "Female", "locale": "it-IT", "notes": "Friendly, Positive"},
]


def main():
    parser = argparse.ArgumentParser(description="List available Edge TTS voices")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.json:
        print(json.dumps(VOICES, indent=2))
    else:
        gb_voices = [v for v in VOICES if v["locale"] == "en-GB"]
        us_voices = [v for v in VOICES if v["locale"] == "en-US"]
        it_voices = [v for v in VOICES if v["locale"] == "it-IT"]
        
        print(f"Available Edge TTS voices ({len(VOICES)} total):\n")
        
        print("🇬🇧 UK ENGLISH:")
        print("| Voice                              | Gender | Notes                     |")
        print("|------------------------------------|--------|---------------------------|")
        for v in gb_voices:
            print(f"| {v['name']:<34} | {v['gender']:<6} | {v['notes']:<25} |")
        
        print(f"\n🇺🇸 US ENGLISH:")
        print("| Voice                              | Gender | Notes                     |")
        print("|------------------------------------|--------|---------------------------|")
        for v in us_voices:
            print(f"| {v['name']:<34} | {v['gender']:<6} | {v['notes']:<25} |")
        
        print(f"\n🇮🇹 ITALIAN:")
        print("| Voice                              | Gender | Notes                     |")
        print("|------------------------------------|--------|---------------------------|")
        for v in it_voices:
            print(f"| {v['name']:<34} | {v['gender']:<6} | {v['notes']:<25} |")
        
        print("\n⚠️  Edge TTS does NOT support style instructions.")
        print("   Voice personality is determined entirely by voice choice.")
        print("\nUsage: --voice <voice-name>")


if __name__ == "__main__":
    main()
