#!/usr/bin/env python3
"""
Generate a podcast MP3 for a Time Slice entry.

Usage:
    python3 generate-podcast.py <entry-id>
    python3 generate-podcast.py --all
    python3 generate-podcast.py --download-music

Uses edge-tts (free, no API key) for narration with different voices per epoch,
and period-appropriate background music from Internet Archive (public domain).

Requires: edge-tts, ffmpeg
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
SCRIPTS_DIR = os.path.join(SCRIPT_DIR, "scripts")
MUSIC_DIR = os.path.join(SCRIPT_DIR, "music")
OUTPUT_DIR = SCRIPT_DIR  # audio/{id}.mp3

# Voice assignments per entry — chosen to match the epoch's character.
# Using Microsoft Edge neural voices (free, no API key).
VOICE_MAP = {
    # 762 Baghdad: scholarly, warm — Indian English for a non-Western feel
    "762-baghdad-round-city-of-reason": {
        "voice": "en-IN-PrabhatNeural",
        "rate": "-5%",
        "pitch": "+0Hz",
    },
    # 1347 Florence plague: dark, dramatic — deep British authority
    "1347-florence-beautiful-catastrophe": {
        "voice": "en-GB-RyanNeural",
        "rate": "-8%",
        "pitch": "-2Hz",
    },
    # 1504 Renaissance: confident, vivid — rich American narrative
    "1504-florence-duel-of-giants": {
        "voice": "en-US-GuyNeural",
        "rate": "-3%",
        "pitch": "+0Hz",
    },
    # 1648 Westphalia: grave, weary — authoritative, measured
    "1648-munster-exhaustion-of-god": {
        "voice": "en-US-ChristopherNeural",
        "rate": "-8%",
        "pitch": "-2Hz",
    },
    # 1784 Enlightenment: crisp, rational — clear British female
    "1784-europe-dare-to-know": {
        "voice": "en-GB-SoniaNeural",
        "rate": "-3%",
        "pitch": "+0Hz",
    },
    # 1889 Paris: passionate, expressive — energetic female
    "1889-paris-year-everything-changed": {
        "voice": "en-US-AriaNeural",
        "rate": "+0%",
        "pitch": "+1Hz",
    },
    # 1922 Modernism: staccato, fragmented energy — fast, clipped
    "1922-modernist-explosion": {
        "voice": "en-US-AndrewNeural",
        "rate": "+3%",
        "pitch": "+0Hz",
    },
}

# Mapping from old slug-only IDs to new year-slug IDs (for backward compat)
SLUG_TO_ID = {
    "baghdad-round-city-of-reason": "762-baghdad-round-city-of-reason",
    "florence-beautiful-catastrophe": "1347-florence-beautiful-catastrophe",
    "florence-duel-of-giants": "1504-florence-duel-of-giants",
    "munster-exhaustion-of-god": "1648-munster-exhaustion-of-god",
    "europe-dare-to-know": "1784-europe-dare-to-know",
    "paris-year-everything-changed": "1889-paris-year-everything-changed",
    "modernist-explosion": "1922-modernist-explosion",
}

# Background music sources from Internet Archive (public domain)
MUSIC_SOURCES = {
    "762-baghdad-round-city-of-reason": {
        "url": "https://archive.org/download/gulezyan-aram-1976-exotic-music-of-the-oud-lyrichord-side-a-archive-01/Gulezyan%2C%20Aram%20%281976%29%20-%20Exotic%20Music%20of%20the%20Oud%20Lyrichord%2C%20side%20A%20%28archive%29-01.mp3",
        "filename": "oud-arabic.mp3",
        "description": "Oud — Arabic traditional",
    },
    "1347-florence-beautiful-catastrophe": {
        "url": "https://archive.org/download/lp_grgorian-chant-easter-mass-pieces-from_choeur-des-moines-de-labbaye-saintpierre-d/disc1/01.02.%20Intro%C3%AFt%20%3A%20Resurrexi.mp3",
        "filename": "gregorian-chant.mp3",
        "description": "Gregorian chant — Introït: Resurrexi",
    },
    "1504-florence-duel-of-giants": {
        "url": "https://archive.org/download/lp_italian-songs-16th-and-17th-centuries-spa_hugues-cunod-hermann-leeb_0/disc1/01.02.%20Lute%20Solo%3A%20Fantasia.mp3",
        "filename": "renaissance-lute.mp3",
        "description": "Renaissance lute fantasia",
    },
    "1648-munster-exhaustion-of-god": {
        "url": "https://archive.org/download/canonic_variations_BWV_769a/01_Variation_I_%28Nel_canone_all%E2%80%99_ottava%29.mp3",
        "filename": "bach-organ.mp3",
        "description": "Bach Canonic Variations — Baroque organ",
    },
    "1784-europe-dare-to-know": {
        "url": "https://archive.org/download/lp_piano-music-vol-6_arthur-balsam-wolfgang-amadeus-mozart/disc1/01.01.%20Sonata%20In%20A%20Minor%20K.310.mp3",
        "filename": "mozart-piano.mp3",
        "description": "Mozart Piano Sonata K.310 — Classical",
    },
    "1889-paris-year-everything-changed": {
        "url": "https://archive.org/download/DebussyClairDeLunevirgilFox/07-ClairDeLunefromSuiteBergamasque.mp3",
        "filename": "debussy-clair-de-lune.mp3",
        "description": "Debussy Clair de lune — Impressionist",
    },
    "1922-modernist-explosion": {
        "url": "https://archive.org/download/lp_the-rite-of-spring_igor-stravinsky-antal-dorati-minneapolis-s/disc1/01.01.%20The%20Rite%20Of%20Spring%20-%20Pictures%20Of%20Pagan%20Russia%3A%20Part%20I.mp3",
        "filename": "stravinsky-rite.mp3",
        "description": "Stravinsky Rite of Spring — Modernist",
    },
}


def resolve_id(entry_id):
    """Resolve a slug-only ID to the full year-slug format."""
    return SLUG_TO_ID.get(entry_id, entry_id)


def download_music(entry_id=None):
    """Download background music from Internet Archive."""
    os.makedirs(MUSIC_DIR, exist_ok=True)
    sources = {entry_id: MUSIC_SOURCES[entry_id]} if entry_id else MUSIC_SOURCES

    for eid, src in sources.items():
        outpath = os.path.join(MUSIC_DIR, src["filename"])
        if os.path.exists(outpath) and os.path.getsize(outpath) > 10000:
            print(f"  ✓ {src['filename']} already exists")
            continue
        print(f"  ↓ Downloading {src['description']}...")
        try:
            req = urllib.request.Request(src["url"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                with open(outpath, "wb") as f:
                    f.write(resp.read())
            print(f"  ✓ {src['filename']} ({os.path.getsize(outpath) // 1024}KB)")
        except Exception as e:
            print(f"  ✗ Failed to download {src['filename']}: {e}")
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-t", "180", "-c:a", "libmp3lame", "-q:a", "9", outpath
            ], capture_output=True)
            print(f"  → Created silent placeholder")


async def generate_narration(entry_id, script_text):
    """Generate TTS narration via edge-tts (free, no API key)."""
    import edge_tts

    voice_config = VOICE_MAP.get(entry_id, {
        "voice": "en-US-GuyNeural",
        "rate": "-5%",
        "pitch": "+0Hz",
    })

    print(f"  🎤 Generating narration (voice: {voice_config['voice']})...")

    communicate = edge_tts.Communicate(
        text=script_text,
        voice=voice_config["voice"],
        rate=voice_config["rate"],
        pitch=voice_config["pitch"],
    )

    narration_path = f"/tmp/{entry_id}-narration.mp3"
    await communicate.save(narration_path)

    size = os.path.getsize(narration_path)
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", narration_path],
        capture_output=True, text=True
    )
    duration = float(result.stdout.strip()) if result.stdout.strip() else 0
    print(f"  ✓ Narration: {size // 1024}KB, {duration:.1f}s")

    return narration_path, duration


def mix_audio(narration_path, music_path, output_path, narration_duration):
    """Mix narration with background music using ffmpeg."""
    print(f"  🎵 Mixing with background music...")

    total_duration = narration_duration + 4

    # Music: loop if needed, trim, fade in/out, lower to 12% volume
    # Narration: delay 2s so music establishes first
    filter_complex = (
        f"[1:a]aloop=loop=-1:size=2e+09,atrim=duration={total_duration},"
        f"afade=t=in:st=0:d=3,afade=t=out:st={total_duration - 3}:d=3,"
        f"volume=0.12[music];"
        f"[0:a]adelay=2000|2000[voice];"
        f"[music][voice]amix=inputs=2:duration=longest:dropout_transition=2[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", narration_path,
        "-i", music_path,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:a", "libmp3lame", "-b:a", "128k",
        "-t", str(total_duration),
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ✗ ffmpeg error: {result.stderr[-500:]}")
        print(f"  → Falling back to narration-only")
        subprocess.run(["cp", narration_path, output_path])
        return

    size = os.path.getsize(output_path)
    print(f"  ✓ Final podcast: {size // 1024}KB, ~{total_duration:.0f}s")


def generate_podcast(entry_id):
    """Full pipeline: script → narration → mix → output."""
    entry_id = resolve_id(entry_id)
    print(f"\n🎙️  Generating podcast for: {entry_id}")

    # Try both old slug and new year-slug for script files
    slug = entry_id.split("-", 1)[1] if "-" in entry_id and entry_id.split("-")[0].isdigit() else entry_id
    script_path = os.path.join(SCRIPTS_DIR, f"{entry_id}.txt")
    if not os.path.exists(script_path):
        script_path = os.path.join(SCRIPTS_DIR, f"{slug}.txt")
    if not os.path.exists(script_path):
        print(f"  ✗ No script found for {entry_id}")
        return False

    with open(script_path) as f:
        script_text = f.read().strip()

    print(f"  📝 Script: {len(script_text)} characters")

    # Download music if needed
    if entry_id in MUSIC_SOURCES:
        download_music(entry_id)

    # Generate narration
    narration_path, duration = asyncio.run(generate_narration(entry_id, script_text))

    # Get music path
    music_src = MUSIC_SOURCES.get(entry_id)
    music_path = os.path.join(MUSIC_DIR, music_src["filename"]) if music_src else None

    # Mix
    output_path = os.path.join(OUTPUT_DIR, f"{entry_id}.mp3")
    if music_path and os.path.exists(music_path) and os.path.getsize(music_path) > 10000:
        mix_audio(narration_path, music_path, output_path, duration)
    else:
        subprocess.run(["cp", narration_path, output_path])
        print(f"  ⚠ No music available, narration-only")

    # Clean up temp
    try:
        os.unlink(narration_path)
    except OSError:
        pass

    # Get final duration
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", output_path],
        capture_output=True, text=True
    )
    final_duration = int(float(result.stdout.strip())) if result.stdout.strip() else 0

    return final_duration


def update_json(entry_id, duration):
    """Add podcast field to slices.json."""
    entry_id = resolve_id(entry_id)
    json_path = os.path.join(PROJECT_DIR, "slices.json")
    with open(json_path) as f:
        data = json.load(f)

    for entry in data:
        if entry.get("id") == entry_id:
            entry["podcast"] = {
                "url": f"audio/{entry_id}.mp3",
                "duration": duration,
            }
            break

    with open(json_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  📄 Updated slices.json with podcast field")


def main():
    parser = argparse.ArgumentParser(description="Generate Time Slice podcasts")
    parser.add_argument("entry_id", nargs="?", help="Entry ID to generate")
    parser.add_argument("--all", action="store_true", help="Generate all entries")
    parser.add_argument("--download-music", action="store_true", help="Download music only")
    args = parser.parse_args()

    if args.download_music:
        print("📥 Downloading all background music...")
        download_music()
        return

    if args.all:
        entries = list(VOICE_MAP.keys())
    elif args.entry_id:
        entries = [resolve_id(args.entry_id)]
    else:
        parser.print_help()
        return

    for entry_id in entries:
        duration = generate_podcast(entry_id)
        if duration:
            update_json(entry_id, duration)

    print(f"\n✅ Done!")


if __name__ == "__main__":
    main()
