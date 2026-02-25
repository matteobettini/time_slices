#!/usr/bin/env python3
"""
Generate a podcast MP3 for a Time Slice entry.

Usage:
    python3 generate-podcast.py <entry-id>
    python3 generate-podcast.py --all
    python3 generate-podcast.py --download-music

Uses gpt-4o-mini-tts via the ape API (OpenAI-compatible) for narration,
and period-appropriate background music from Internet Archive (public domain).

Requires: ffmpeg, curl (or requests)
"""

import argparse
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

# API configuration
APE_API_URL = "https://api.wearables-ape.io/models/v1/audio/speech"
APE_TOKEN = os.environ.get("APE_TOKEN", "")
TTS_MODEL = "gpt-4o-mini-tts"

# Voice assignments per entry — OpenAI TTS voices.
# gpt-4o-mini-tts voices: alloy, ash, ballad, coral, echo, fable, nova, sage, shimmer, verse
# ❌ onyx is excluded — produces buggy/glitchy output

# ⚠️ Do NOT use "onyx" — it produces buggy/glitchy audio with gpt-4o-mini-tts.
# English voices
VOICE_MAP_EN = {
    # 125 Rome: authoritative, architectural — ash for deep resonance and gravitas
    "125-rome-dome-of-all-things": {
        "voice": "ash",
        "instructions": "Speak as a historian contemplating an empire at its peak — deep, measured, with the authority of carved stone. Let the weight of Roman engineering and Stoic philosophy resonate. Unhurried, as if the dome itself has all the time in the world.",
    },
    # 762 Baghdad: warm, storytelling — fable has a narrative quality
    "762-baghdad-round-city-of-reason": {
        "voice": "fable",
        "instructions": "Speak as a warm storyteller narrating ancient history. Measured pace, slight wonder in the voice. This is a tale of a golden age.",
    },
    # 1347 Florence plague: somber, dramatic — ash for deep gravitas
    "1347-florence-beautiful-catastrophe": {
        "voice": "ash",
        "instructions": "Speak with gravity and weight. This is about plague, death, and the strange beauty that emerged from catastrophe. Somber but not monotone — let the drama come through.",
    },
    # 1504 Renaissance: confident, vivid — echo has clarity and presence
    "1504-florence-duel-of-giants": {
        "voice": "echo",
        "instructions": "Speak with confidence and vivid energy. This is about Leonardo and Michelangelo in competition — genius against genius. Bring the rivalry to life.",
    },
    # 1648 Westphalia: weary, reflective — ash for gravitas
    "1648-munster-exhaustion-of-god": {
        "voice": "ash",
        "instructions": "Speak with weariness and hard-won wisdom. Thirty years of religious war have exhausted Europe. The tone is reflective, almost elegiac, but with a thread of hope at the emergence of the modern state system.",
    },
    # 1784 Enlightenment: crisp, intellectual — sage for measured clarity
    "1784-europe-dare-to-know": {
        "voice": "sage",
        "instructions": "Speak with intellectual clarity and a touch of revolutionary excitement. This is the Enlightenment — reason overthrowing tradition. Crisp, precise, but with underlying passion.",
    },
    # 1889 Paris: passionate, expressive — nova for warmth and energy
    "1889-paris-year-everything-changed": {
        "voice": "nova",
        "instructions": "Speak with passion and wonder. Paris in 1889 — the Eiffel Tower rising, the world on display, art exploding in new directions. Let the excitement of a transformative moment come through.",
    },
    # 1922 Modernism: staccato, urgent — coral for dynamic energy
    "1922-modernist-explosion": {
        "voice": "coral",
        "instructions": "Speak with urgency and modernist energy. This is 1922 — Ulysses, The Waste Land, jazz, Bauhaus, everything shattering and reassembling. Quick-paced, electric, a world remaking itself.",
    },
}

# Italian voices — same voice palette but with Italian-language style instructions
VOICE_MAP_IT = {
    "125-rome-dome-of-all-things": {
        "voice": "ash",
        "instructions": "Parla in italiano come uno storico che contempla un impero al suo apice — voce profonda, misurata, con l'autorità della pietra scolpita. Lascia che il peso dell'ingegneria romana e della filosofia stoica risuoni. Senza fretta, come se la cupola stessa avesse tutto il tempo del mondo.",
    },
    "762-baghdad-round-city-of-reason": {
        "voice": "fable",
        "instructions": "Parla in italiano con il tono di un cantastorie che narra una storia antica. Ritmo misurato, un senso di meraviglia nella voce. Questa è la storia di un'età dell'oro.",
    },
    "1347-florence-beautiful-catastrophe": {
        "voice": "ash",
        "instructions": "Parla in italiano con gravità e peso. Questa storia parla di peste, morte e della strana bellezza che emerge dalla catastrofe. Cupo ma non monotono — lascia trapelare il dramma.",
    },
    "1504-florence-duel-of-giants": {
        "voice": "echo",
        "instructions": "Parla in italiano con sicurezza ed energia vivida. Questa è la storia di Leonardo e Michelangelo in competizione — genio contro genio. Dai vita alla rivalità.",
    },
    "1648-munster-exhaustion-of-god": {
        "voice": "ash",
        "instructions": "Parla in italiano con stanchezza e saggezza duramente conquistata. Trent'anni di guerre di religione hanno esaurito l'Europa. Il tono è riflessivo, quasi elegiaco, ma con un filo di speranza.",
    },
    "1784-europe-dare-to-know": {
        "voice": "sage",
        "instructions": "Parla in italiano con chiarezza intellettuale e un tocco di entusiasmo rivoluzionario. Questo è l'Illuminismo — la ragione che rovescia la tradizione. Nitido, preciso, ma con passione sottostante.",
    },
    "1889-paris-year-everything-changed": {
        "voice": "nova",
        "instructions": "Parla in italiano con passione e meraviglia. Parigi nel 1889 — la Torre Eiffel che si innalza, il mondo in mostra, l'arte che esplode in nuove direzioni. Lascia trasparire l'emozione di un momento trasformativo.",
    },
    "1922-modernist-explosion": {
        "voice": "coral",
        "instructions": "Parla in italiano con urgenza ed energia modernista. Questo è il 1922 — Ulisse, La terra desolata, jazz, Bauhaus, tutto si frantuma e si ricompone. Ritmo rapido, elettrico, un mondo che si rifà da capo.",
    },
}

VOICE_MAPS = {"en": VOICE_MAP_EN, "it": VOICE_MAP_IT}

# Background music sources from Internet Archive (public domain)
MUSIC_SOURCES = {
    "125-rome-dome-of-all-things": {
        "url": "https://archive.org/download/c-2345-6-respighi-ancient-airs-suite-2-iii/C2345-6%20Respighi%20Ancient%20Airs%20Suite%202%20(ii).mp3",
        "filename": "respighi-ancient-airs.mp3",
        "description": "Respighi Ancient Airs and Dances — Danza rustica (1930)",
    },
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


def _tts_chunk(text, voice, instructions, out_path, timeout=120, retries=2):
    """Call the TTS API for a single chunk of text. Returns True on success."""
    import time as _time
    payload = json.dumps({
        "model": TTS_MODEL,
        "input": text,
        "voice": voice,
        "instructions": instructions or "",
        "response_format": "mp3",
    })
    req_headers = {
        "Authorization": f"Bearer {APE_TOKEN}",
        "Content-Type": "application/json",
    }
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(APE_API_URL, data=payload.encode("utf-8"), headers=req_headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                with open(out_path, "wb") as f:
                    f.write(resp.read())
            return True
        except Exception as e:
            print(f"    ⚠ Attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                _time.sleep(3 * attempt)  # backoff: 3s, 6s
    return False


# Threshold in chars: scripts longer than this are split into paragraph chunks
_CHUNK_THRESHOLD = 1500


def generate_narration(entry_id, script_text, lang="en"):
    """Generate TTS narration via gpt-4o-mini-tts through the ape API.

    For short scripts (≤ _CHUNK_THRESHOLD chars), sends a single request.
    For longer scripts, splits by paragraph, generates each chunk, and
    concatenates with ffmpeg. This avoids 504 gateway timeouts on the
    upstream TTS provider.
    """
    voice_map = VOICE_MAPS.get(lang, VOICE_MAP_EN)
    voice_config = voice_map.get(entry_id, {
        "voice": "alloy",
        "instructions": "Speak as a knowledgeable narrator telling a historical story." if lang == "en" else "Parla come un narratore esperto che racconta una storia storica.",
    })

    voice = voice_config["voice"]
    instructions = voice_config.get("instructions", "")

    print(f"  🎤 Generating narration (voice: {voice}, model: {TTS_MODEL}, {len(script_text)} chars)...")

    narration_path = f"/tmp/{entry_id}-narration.mp3"

    # --- Decide: single call or chunked ---
    if len(script_text) <= _CHUNK_THRESHOLD:
        # Short script — single TTS call
        if not _tts_chunk(script_text, voice, instructions, narration_path, timeout=120, retries=2):
            print(f"  ✗ TTS failed for {entry_id}")
            return None, 0
    else:
        # Long script — split into paragraphs and generate each separately
        import time as _time
        paragraphs = [p.strip() for p in script_text.split("\n\n") if p.strip()]
        print(f"  📄 Splitting into {len(paragraphs)} chunks for chunked TTS...")
        part_paths = []
        for i, para in enumerate(paragraphs):
            part_path = f"/tmp/{entry_id}-part{i}.mp3"
            print(f"    Chunk {i+1}/{len(paragraphs)} ({len(para)} chars)...")
            if not _tts_chunk(para, voice, instructions, part_path, timeout=120, retries=2):
                print(f"  ✗ TTS failed on chunk {i+1}")
                return None, 0
            part_paths.append(part_path)
            if i < len(paragraphs) - 1:
                _time.sleep(1)  # small delay between API calls

        # Concatenate parts with ffmpeg
        list_file = f"/tmp/{entry_id}-parts.txt"
        with open(list_file, "w") as f:
            for p in part_paths:
                f.write(f"file '{p}'\n")

        result = subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
             "-c:a", "libmp3lame", "-b:a", "128k", narration_path],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"  ✗ ffmpeg concat failed: {result.stderr[-300:]}")
            return None, 0

        # Clean up temp parts
        for p in part_paths:
            try:
                os.remove(p)
            except OSError:
                pass
        try:
            os.remove(list_file)
        except OSError:
            pass

    # Measure output
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


def generate_podcast(entry_id, lang="en"):
    """Full pipeline: script → narration → mix → output."""
    lang_label = f" [{lang.upper()}]" if lang != "en" else ""
    print(f"\n🎙️  Generating podcast for: {entry_id}{lang_label}")

    # Find script file — Italian scripts in scripts/it/ subfolder
    if lang == "it":
        script_path = os.path.join(SCRIPTS_DIR, "it", f"{entry_id}.txt")
    else:
        script_path = os.path.join(SCRIPTS_DIR, f"{entry_id}.txt")
    if not os.path.exists(script_path):
        # Try slug-only (strip year prefix)
        slug = entry_id.split("-", 1)[1] if "-" in entry_id and entry_id.split("-")[0].lstrip("-").isdigit() else entry_id
        if lang == "it":
            script_path = os.path.join(SCRIPTS_DIR, "it", f"{slug}.txt")
        else:
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
    narration_path, duration = generate_narration(entry_id, script_text, lang=lang)
    if not narration_path:
        return False

    # Get music path
    music_src = MUSIC_SOURCES.get(entry_id)
    music_path = os.path.join(MUSIC_DIR, music_src["filename"]) if music_src else None

    # Mix — Italian outputs go to audio/it/
    if lang == "it":
        it_dir = os.path.join(OUTPUT_DIR, "it")
        os.makedirs(it_dir, exist_ok=True)
        output_path = os.path.join(it_dir, f"{entry_id}.mp3")
    else:
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


def update_json(entry_id, duration, lang="en"):
    """Add podcast field to slices.json or slices.it.json."""
    if lang == "it":
        json_path = os.path.join(PROJECT_DIR, "slices.it.json")
        url_prefix = "audio/it/"
    else:
        json_path = os.path.join(PROJECT_DIR, "slices.json")
        url_prefix = "audio/"
    with open(json_path) as f:
        data = json.load(f)

    for entry in data:
        if entry.get("id") == entry_id:
            entry["podcast"] = {
                "url": f"{url_prefix}{entry_id}.mp3",
                "duration": duration,
            }
            break

    with open(json_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  📄 Updated {'slices.it.json' if lang == 'it' else 'slices.json'} with podcast field")


def main():
    parser = argparse.ArgumentParser(description="Generate Time Slice podcasts")
    parser.add_argument("entry_id", nargs="?", help="Entry ID to generate")
    parser.add_argument("--all", action="store_true", help="Generate all entries")
    parser.add_argument("--lang", default="en", choices=["en", "it"], help="Language (en or it)")
    parser.add_argument("--download-music", action="store_true", help="Download music only")
    args = parser.parse_args()

    if not APE_TOKEN:
        print("✗ APE_TOKEN not set in environment. Export it first.")
        sys.exit(1)

    if args.download_music:
        print("📥 Downloading all background music...")
        download_music()
        return

    lang = args.lang

    if args.all:
        entries = list(VOICE_MAPS.get(lang, VOICE_MAP_EN).keys())
    elif args.entry_id:
        entries = [args.entry_id]
    else:
        parser.print_help()
        return

    for entry_id in entries:
        duration = generate_podcast(entry_id, lang=lang)
        if duration:
            update_json(entry_id, duration, lang=lang)

    print(f"\n✅ Done!")


if __name__ == "__main__":
    main()
