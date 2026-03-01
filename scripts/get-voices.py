#!/usr/bin/env python3
"""
List available Edge TTS voices for Time Slices podcasts.

Usage:
    python3 scripts/get-voices.py          # List all English and Italian voices
    python3 scripts/get-voices.py --json   # Output as JSON
"""

import argparse
import json

# All English and Italian Edge TTS voices
VOICES = [
    # Australian English
    {"name": "en-AU-NatashaNeural", "gender": "Female", "locale": "en-AU", "notes": "Friendly, Positive"},
    {"name": "en-AU-WilliamMultilingualNeural", "gender": "Male", "locale": "en-AU", "notes": "Friendly, Positive"},
    # Canadian English
    {"name": "en-CA-ClaraNeural", "gender": "Female", "locale": "en-CA", "notes": "Friendly, Positive"},
    {"name": "en-CA-LiamNeural", "gender": "Male", "locale": "en-CA", "notes": "Friendly, Positive"},
    # British English
    {"name": "en-GB-LibbyNeural", "gender": "Female", "locale": "en-GB", "notes": "Friendly, Positive"},
    {"name": "en-GB-MaisieNeural", "gender": "Female", "locale": "en-GB", "notes": "Friendly, Positive"},
    {"name": "en-GB-RyanNeural", "gender": "Male", "locale": "en-GB", "notes": "Friendly, Positive"},
    {"name": "en-GB-SoniaNeural", "gender": "Female", "locale": "en-GB", "notes": "Friendly, Positive"},
    {"name": "en-GB-ThomasNeural", "gender": "Male", "locale": "en-GB", "notes": "Friendly, Positive"},
    # Hong Kong English
    {"name": "en-HK-SamNeural", "gender": "Male", "locale": "en-HK", "notes": "Friendly, Positive"},
    {"name": "en-HK-YanNeural", "gender": "Female", "locale": "en-HK", "notes": "Friendly, Positive"},
    # Irish English
    {"name": "en-IE-ConnorNeural", "gender": "Male", "locale": "en-IE", "notes": "Friendly, Positive"},
    {"name": "en-IE-EmilyNeural", "gender": "Female", "locale": "en-IE", "notes": "Friendly, Positive"},
    # Indian English
    {"name": "en-IN-NeerjaExpressiveNeural", "gender": "Female", "locale": "en-IN", "notes": "Friendly, Positive"},
    {"name": "en-IN-NeerjaNeural", "gender": "Female", "locale": "en-IN", "notes": "Friendly, Positive"},
    {"name": "en-IN-PrabhatNeural", "gender": "Male", "locale": "en-IN", "notes": "Friendly, Positive"},
    # Kenyan English
    {"name": "en-KE-AsiliaNeural", "gender": "Female", "locale": "en-KE", "notes": "Friendly, Positive"},
    {"name": "en-KE-ChilembaNeural", "gender": "Male", "locale": "en-KE", "notes": "Friendly, Positive"},
    # Nigerian English
    {"name": "en-NG-AbeoNeural", "gender": "Male", "locale": "en-NG", "notes": "Friendly, Positive"},
    {"name": "en-NG-EzinneNeural", "gender": "Female", "locale": "en-NG", "notes": "Friendly, Positive"},
    # New Zealand English
    {"name": "en-NZ-MitchellNeural", "gender": "Male", "locale": "en-NZ", "notes": "Friendly, Positive"},
    {"name": "en-NZ-MollyNeural", "gender": "Female", "locale": "en-NZ", "notes": "Friendly, Positive"},
    # Philippine English
    {"name": "en-PH-JamesNeural", "gender": "Male", "locale": "en-PH", "notes": "Friendly, Positive"},
    {"name": "en-PH-RosaNeural", "gender": "Female", "locale": "en-PH", "notes": "Friendly, Positive"},
    # Singapore English
    {"name": "en-SG-LunaNeural", "gender": "Female", "locale": "en-SG", "notes": "Friendly, Positive"},
    {"name": "en-SG-WayneNeural", "gender": "Male", "locale": "en-SG", "notes": "Friendly, Positive"},
    # Tanzanian English
    {"name": "en-TZ-ElimuNeural", "gender": "Male", "locale": "en-TZ", "notes": "Friendly, Positive"},
    {"name": "en-TZ-ImaniNeural", "gender": "Female", "locale": "en-TZ", "notes": "Friendly, Positive"},
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
    # South African English
    {"name": "en-ZA-LeahNeural", "gender": "Female", "locale": "en-ZA", "notes": "Friendly, Positive"},
    {"name": "en-ZA-LukeNeural", "gender": "Male", "locale": "en-ZA", "notes": "Friendly, Positive"},
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
        # Group by locale
        en_voices = [v for v in VOICES if v["locale"].startswith("en-")]
        it_voices = [v for v in VOICES if v["locale"].startswith("it-")]
        
        print(f"Available Edge TTS voices ({len(VOICES)} total):\n")
        
        print("🇬🇧🇺🇸 ENGLISH VOICES:")
        print("| Voice                              | Gender | Locale | Notes                     |")
        print("|------------------------------------|--------|--------|---------------------------|")
        for v in en_voices:
            print(f"| {v['name']:<34} | {v['gender']:<6} | {v['locale']:<6} | {v['notes']:<25} |")
        
        print(f"\n🇮🇹 ITALIAN VOICES:")
        print("| Voice                              | Gender | Notes                     |")
        print("|------------------------------------|--------|---------------------------|")
        for v in it_voices:
            print(f"| {v['name']:<34} | {v['gender']:<6} | {v['notes']:<25} |")
        
        print("\n⚠️  Edge TTS does NOT support style instructions.")
        print("   Voice personality is determined entirely by voice choice.")
        print("\nUsage: --voice <voice-name>")


if __name__ == "__main__":
    main()
