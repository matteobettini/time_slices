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
# ⚠️ TIMESLICES_TTS_TOKEN is ONLY for Time Slices TTS generation. Do not use elsewhere.
TTS_API_URL = "https://api.wearables-ape.io/models/v1/audio/speech"
TTS_TOKEN = os.environ.get("TIMESLICES_TTS_TOKEN", "")
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
        "instructions": "Speak as a historian contemplating an empire at its peak — deep, measured, with quiet authority. Unhurried, as if the dome itself has all the time in the world. Keep it conversational, not theatrical.",
    },
    # 762 Baghdad: warm, storytelling — fable has a narrative quality
    "762-baghdad-round-city-of-reason": {
        "voice": "fable",
        "instructions": "Speak as a warm storyteller narrating ancient history. Measured pace, a hint of wonder. Conversational, not performative.",
    },
    # 1347 Florence plague: somber, dramatic — ash for deep gravitas
    "1347-florence-beautiful-catastrophe": {
        "voice": "ash",
        "instructions": "Speak with gravity. This is about plague, death, and the strange beauty that emerged from catastrophe. Somber but not monotone — understated drama, not theatrical.",
    },
    # 1504 Renaissance: confident, vivid — echo has clarity and presence
    "1504-florence-duel-of-giants": {
        "voice": "echo",
        "instructions": "Speak with confidence. Leonardo and Michelangelo in competition — genius against genius. Vivid but grounded, like a good podcast host telling a great story.",
    },
    # 1648 Westphalia: weary, reflective — ash for gravitas
    "1648-munster-exhaustion-of-god": {
        "voice": "ash",
        "instructions": "Speak with weariness and hard-won wisdom. Thirty years of war have exhausted Europe. Reflective, with a thread of hope — but keep the emotion restrained.",
    },
    # 1784 Enlightenment: crisp, intellectual — sage for measured clarity
    "1784-europe-dare-to-know": {
        "voice": "sage",
        "instructions": "Speak with intellectual clarity and a touch of excitement. The Enlightenment — reason overthrowing tradition. Crisp and precise, conversational not declamatory.",
    },
    # 1889 Paris: passionate, expressive — nova for warmth and energy
    "1889-paris-year-everything-changed": {
        "voice": "nova",
        "instructions": "Speak with warmth and wonder. Paris in 1889 — the Tower rising, art exploding. Let the excitement come through naturally, not forced.",
    },
    # 1922 Modernism: staccato, urgent — coral for dynamic energy
    "1922-modernist-explosion": {
        "voice": "coral",
        "instructions": "Speak with energy and pace. 1922 — Ulysses, The Waste Land, jazz, Bauhaus, everything shattering and reassembling. Quick but not breathless.",
    },
    # 1517 Wittenberg: dramatic, pivotal — ash for gravitas at a world-historical turning point
    "1517-wittenberg-hammer-falls": {
        "voice": "ash",
        "instructions": "Speak with measured drama. This is the moment Western Christianity splits — a hammer blow that echoes for centuries. Authoritative but not bombastic. Let the weight of the moment speak for itself.",
    },
    # 1687 London: precise, authoritative — sage for intellectual clarity at the dawn of modern science
    "1687-london-gravity-of-reason": {
        "voice": "sage",
        "instructions": "Speak with crisp intellectual precision. This is Newton's moment — the universe becoming an equation. Authoritative but with a thread of wonder. Like a historian who still marvels at what Newton achieved.",
    },
    # 1141 Sens: dramatic, scholarly — ash for gravitas at a turning point between faith and reason
    "1141-sens-duel-of-reason-and-faith": {
        "voice": "ash",
        "instructions": "Speak with measured drama and scholarly weight. This is the medieval confrontation between faith and reason — Bernard versus Abelard. Deep and contemplative, with understated tension. Let the intellectual stakes speak for themselves.",
    },
}

# Italian voices — same voice palette but with Italian-language style instructions
VOICE_MAP_IT = {
    "125-rome-dome-of-all-things": {
        "voice": "ash",
        "instructions": "Parla in italiano come uno storico che contempla un impero al suo apice — voce profonda, misurata, con quieta autorità. Senza fretta. Tono conversazionale, non teatrale.",
    },
    "762-baghdad-round-city-of-reason": {
        "voice": "fable",
        "instructions": "Parla in italiano con il tono di un cantastorie. Ritmo misurato, un accenno di meraviglia. Conversazionale, non declamatorio.",
    },
    "1347-florence-beautiful-catastrophe": {
        "voice": "ash",
        "instructions": "Parla in italiano con gravità. Peste, morte, e la strana bellezza che emerge dalla catastrofe. Cupo ma non monotono — dramma contenuto, non teatrale.",
    },
    "1504-florence-duel-of-giants": {
        "voice": "echo",
        "instructions": "Parla in italiano con sicurezza. Leonardo e Michelangelo in competizione — genio contro genio. Vivido ma con i piedi per terra, come un buon conduttore di podcast.",
    },
    "1648-munster-exhaustion-of-god": {
        "voice": "ash",
        "instructions": "Parla in italiano con stanchezza e saggezza conquistata. Trent'anni di guerra hanno esaurito l'Europa. Riflessivo, con un filo di speranza — ma emozione contenuta.",
    },
    "1784-europe-dare-to-know": {
        "voice": "sage",
        "instructions": "Parla in italiano con chiarezza intellettuale e un tocco di entusiasmo. L'Illuminismo — la ragione che rovescia la tradizione. Nitido, preciso, conversazionale.",
    },
    "1889-paris-year-everything-changed": {
        "voice": "nova",
        "instructions": "Parla in italiano con calore e meraviglia. Parigi nel 1889 — la Torre che si innalza, l'arte che esplode. Lascia che l'emozione emerga naturalmente, senza forzare.",
    },
    "1922-modernist-explosion": {
        "voice": "coral",
        "instructions": "Parla in italiano con energia e ritmo. Il 1922 — Ulisse, La terra desolata, jazz, Bauhaus, tutto si frantuma e si ricompone. Veloce ma non affannato.",
    },
    # 1517 Wittenberg: dramatic, pivotal
    "1517-wittenberg-hammer-falls": {
        "voice": "ash",
        "instructions": "Parla in italiano con dramma contenuto. Questo è il momento in cui il cristianesimo occidentale si divide — un colpo di martello che riecheggia per secoli. Autorevole ma non pomposo. Lascia che il peso del momento parli da solo.",
    },
    # 1687 London: precise, authoritative
    "1687-london-gravity-of-reason": {
        "voice": "sage",
        "instructions": "Parla in italiano con precisione intellettuale nitida. Questo è il momento di Newton — l'universo che diventa un'equazione. Autorevole ma con un filo di meraviglia. Come uno storico che ancora si stupisce di ciò che Newton realizzò.",
    },
    # 1141 Sens: dramatic, scholarly
    "1141-sens-duel-of-reason-and-faith": {
        "voice": "ash",
        "instructions": "Parla in italiano con dramma misurato e peso intellettuale. Questo è lo scontro medievale tra fede e ragione — Bernardo contro Abelardo. Profondo e contemplativo, con tensione sottile. Lascia che la posta in gioco intellettuale parli da sola.",
    },
}

VOICE_MAPS = {"en": VOICE_MAP_EN, "it": VOICE_MAP_IT}

# ═══════════════════════════════════════════════════════════════════════════════
# MUSIC — Downloaded on-demand via CLI args (--music-url)
# Use scripts/find-music.py to discover tracks from Internet Archive
# ═══════════════════════════════════════════════════════════════════════════════

# Legacy mappings for existing entries (used when --music-url not provided)
# Format: entry_id -> (url, filename, start_time)

# ═══════════════════════════════════════════════════════════════════════════════
# MUSIC — Pass via CLI: --music-url <url> --music-start <seconds>
# Use scripts/find-music.py to discover tracks from Internet Archive
# ═══════════════════════════════════════════════════════════════════════════════

def _verify_music_has_audio(filepath):
    """Check that a music file actually contains audio (not silence). Returns True if OK."""
    result = subprocess.run(
        ["ffmpeg", "-i", filepath, "-t", "30", "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True
    )
    import re
    match = re.search(r'mean_volume: ([-\d.]+) dB', result.stderr)
    if match and float(match.group(1)) < -50:
        return False  # Essentially silent
    return True


def download_music_track(url, filename):
    """Download a single music track from URL. Returns path or None on failure."""
    os.makedirs(MUSIC_DIR, exist_ok=True)
    outpath = os.path.join(MUSIC_DIR, filename)
    
    if os.path.exists(outpath) and os.path.getsize(outpath) > 10000:
        if _verify_music_has_audio(outpath):
            print(f"  ✓ {filename} already exists")
            return outpath
        else:
            print(f"  ⚠️  {filename} exists but is silent, re-downloading...")
            os.remove(outpath)
    
    print(f"  ↓ Downloading music: {filename}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            with open(outpath, "wb") as f:
                f.write(resp.read())
        if not _verify_music_has_audio(outpath):
            os.remove(outpath)
            raise ValueError("Downloaded file is silent/corrupt")
        print(f"  ✓ {filename} ({os.path.getsize(outpath) // 1024}KB)")
        return outpath
    except Exception as e:
        print(f"  ✗ FAILED: {filename}: {e}")
        print(f"  🚨 Music download failed — use find-music.py to get a different track!")
        return None


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
        "Authorization": f"Bearer {TTS_TOKEN}",
        "Content-Type": "application/json",
    }
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(TTS_API_URL, data=payload.encode("utf-8"), headers=req_headers)
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

        # Concatenate parts with ffmpeg, adding small gaps and normalizing volume
        list_file = f"/tmp/{entry_id}-parts.txt"
        
        # First, normalize each part to the same loudness and add silence padding
        normalized_paths = []
        silence_gap = 0.4  # seconds of silence between paragraphs
        
        for i, p in enumerate(part_paths):
            norm_path = f"/tmp/{entry_id}-part{i}-norm.mp3"
            # Normalize to -16 LUFS (podcast standard) and add silence at end
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", p,
                 "-af", f"loudnorm=I=-16:TP=-1.5:LRA=11,apad=pad_dur={silence_gap}",
                 "-c:a", "libmp3lame", "-b:a", "128k", norm_path],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                normalized_paths.append(norm_path)
            else:
                # Fallback to original if normalization fails
                normalized_paths.append(p)
        
        with open(list_file, "w") as f:
            for p in normalized_paths:
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
        for p in part_paths + normalized_paths:
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


def validate_music_start(music_path, start_time):
    """Check that music at start_time is not silent. Returns (ok, suggested_start)."""
    # Check volume at the specified start time
    result = subprocess.run(
        ["ffmpeg", "-i", music_path, "-ss", str(start_time), "-t", "3",
         "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True
    )
    
    import re
    match = re.search(r'mean_volume: ([-\d.]+) dB', result.stderr)
    if not match:
        return True, start_time  # Can't detect, assume ok
    
    mean_vol = float(match.group(1))
    
    # If very quiet (< -35dB), try to find a better start
    if mean_vol < -35:
        print(f"  ⚠️  Music at {start_time}s is quiet ({mean_vol:.1f}dB), searching for better start...")
        
        # Detect silence periods
        result = subprocess.run(
            ["ffmpeg", "-i", music_path, "-af", "silencedetect=noise=-30dB:d=0.3",
             "-f", "null", "-"],
            capture_output=True, text=True
        )
        
        # Find first silence_end after start_time
        for line in result.stderr.split('\n'):
            if 'silence_end' in line:
                match = re.search(r'silence_end: ([\d.]+)', line)
                if match:
                    end_time = float(match.group(1))
                    if end_time > start_time:
                        suggested = round(end_time * 2) / 2  # Round to 0.5s
                        print(f"  💡 Suggested start_time: {suggested}s")
                        return False, suggested
        
        # If no silence detected, just add 2 seconds
        return False, start_time + 2
    
    return True, start_time


def mix_audio(narration_path, music_path, output_path, narration_duration, start_time=0):
    """Mix narration with background music using ffmpeg.
    
    Improvements over basic mix:
    - Music starts from a curated timestamp (skip silence/weak openings)
    - Low-pass filter at 4kHz to avoid competing with voice frequencies
    - Sidechain-style ducking: music at 35% during intro/outro, ducks to 20% during narration
    - Longer 3.5s music intro to establish mood before narration
    - Gentle compression to even out music dynamics
    """
    print(f"  🎵 Mixing with background music (start={start_time}s)...")

    intro_duration = 3.5     # seconds of music before voice starts
    outro_pad = 3.0          # seconds of music after voice ends
    total_duration = narration_duration + intro_duration + outro_pad
    
    # Voice starts after intro_duration
    voice_start_ms = int(intro_duration * 1000)
    
    # When voice enters, duck music. When voice ends, bring music back up.
    voice_end_time = intro_duration + narration_duration
    
    # Music chain:
    # 1. Seek to start_time in source
    # 2. Loop if needed, trim to total duration
    # 3. Low-pass at 4kHz to clear voice frequency space
    # 4. Gentle compression to tame dynamics
    # 5. Volume envelope: 35% intro → duck to 20% when voice enters → 35% outro
    # 6. Fade in at start, fade out at end
    # 7. amix with normalize=0 to prevent automatic halving of inputs
    # 8. Final loudnorm pass to hit podcast-standard -16 LUFS
    filter_complex = (
        # Music processing
        # First normalize music to -20 LUFS so all tracks start at same loudness
        # THEN apply our volume envelope — this prevents quiet tracks from disappearing
        f"[1:a]atrim=start={start_time},asetpts=PTS-STARTPTS,"
        f"aloop=loop=-1:size=2e+09,atrim=duration={total_duration},"
        f"loudnorm=I=-20:TP=-2:LRA=7,"
        f"lowpass=f=4000:p=1,"
        f"acompressor=threshold=-25dB:ratio=3:attack=20:release=200,"
        f"volume=0.35,"
        f"afade=t=in:st=0:d=2.5,"
        # Duck music when voice is present: fade down to ~57% of base (0.20/0.35) during narration
        f"volume=enable='between(t,{intro_duration},{voice_end_time})':volume=0.57,"
        f"afade=t=out:st={total_duration - 2.5}:d=2.5"
        f"[music];"
        # Voice: delay to start after music intro
        f"[0:a]adelay={voice_start_ms}|{voice_start_ms}[voice];"
        # Mix — normalize=0 prevents amix from halving input volumes
        f"[music][voice]amix=inputs=2:duration=longest:dropout_transition=2:normalize=0[mixed];"
        # Loudness normalization to podcast standard (-16 LUFS)
        f"[mixed]loudnorm=I=-16:TP=-1.5:LRA=11[out]"
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


NARRATIONS_DIR = os.path.join(SCRIPT_DIR, "narrations")


def generate_podcast(entry_id, lang="en", remix=False, music_url=None, music_start=0):
    """Full pipeline: script → narration → mix → output.
    
    Args:
        entry_id: The slice entry ID
        lang: "en" or "it"  
        remix: If True, skip TTS and reuse saved narration
        music_url: URL to download background music from (optional)
        music_start: Start time in seconds for music track
    
    If remix=True, skip TTS and reuse saved narration from audio/narrations/.
    If no saved narration exists, extract voice from existing podcast MP3
    (strips old 2s music intro).
    """
    lang_label = f" [{lang.upper()}]" if lang != "en" else ""
    print(f"\n🎙️  Generating podcast for: {entry_id}{lang_label}" + (" [REMIX]" if remix else ""))

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

    # Download music if URL provided
    music_path = None
    if music_url:
        # Generate filename from URL
        import hashlib
        url_hash = hashlib.md5(music_url.encode()).hexdigest()[:8]
        music_filename = f"track-{url_hash}.mp3"
        music_path = download_music_track(music_url, music_filename)

    # Narration: generate or reuse
    narration_subdir = os.path.join(NARRATIONS_DIR, "it") if lang == "it" else NARRATIONS_DIR
    os.makedirs(narration_subdir, exist_ok=True)
    saved_narration = os.path.join(narration_subdir, f"{entry_id}.mp3")

    if remix and os.path.exists(saved_narration):
        # Reuse saved narration
        narration_path = saved_narration
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", narration_path],
            capture_output=True, text=True
        )
        duration = float(result.stdout.strip()) if result.stdout.strip() else 0
        print(f"  ✓ Reusing saved narration: {os.path.getsize(narration_path) // 1024}KB, {duration:.1f}s")
        cleanup_narration = False
    elif remix:
        # No saved narration — extract from existing podcast MP3
        if lang == "it":
            existing_mp3 = os.path.join(OUTPUT_DIR, "it", f"{entry_id}.mp3")
        else:
            existing_mp3 = os.path.join(OUTPUT_DIR, f"{entry_id}.mp3")
        if os.path.exists(existing_mp3):
            print(f"  🔧 Extracting voice from existing podcast (stripping old 2s intro)...")
            # Old mix had 2s music intro; trim it to get narration-start-aligned audio
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", existing_mp3, "-ss", "2",
                 "-c:a", "libmp3lame", "-b:a", "128k", saved_narration],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"  ✗ Extraction failed: {result.stderr[-300:]}")
                return False
            narration_path = saved_narration
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", narration_path],
                capture_output=True, text=True
            )
            duration = float(result.stdout.strip()) if result.stdout.strip() else 0
            print(f"  ✓ Extracted narration: {os.path.getsize(narration_path) // 1024}KB, {duration:.1f}s")
            cleanup_narration = False
        else:
            print(f"  ✗ No existing podcast to extract from and --remix specified. Run without --remix first.")
            return False
    else:
        # Normal TTS generation
        narration_path, duration = generate_narration(entry_id, script_text, lang=lang)
        if not narration_path:
            return False
        # Save narration for future remixes
        subprocess.run(["cp", narration_path, saved_narration])
        cleanup_narration = True

    # Mix — Italian outputs go to audio/it/
    if lang == "it":
        it_dir = os.path.join(OUTPUT_DIR, "it")
        os.makedirs(it_dir, exist_ok=True)
        output_path = os.path.join(it_dir, f"{entry_id}.mp3")
    else:
        output_path = os.path.join(OUTPUT_DIR, f"{entry_id}.mp3")
    if music_path and os.path.exists(music_path) and os.path.getsize(music_path) > 10000:
        start_time = music_start
        
        # Validate music isn't silent at start_time
        music_ok, suggested_start = validate_music_start(music_path, start_time)
        if not music_ok:
            print(f"  ⚠️  Using suggested start_time {suggested_start}s instead of {start_time}s")
            start_time = suggested_start
        
        mix_audio(narration_path, music_path, output_path, duration, start_time=start_time)
    else:
        subprocess.run(["cp", narration_path, output_path])
        print(f"  ⚠ No music available, narration-only")

    # Clean up temp narration (but not saved narrations)
    if cleanup_narration:
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
    parser.add_argument("--lang", default="en", choices=["en", "it"], help="Language (en or it)")
    parser.add_argument("--remix", action="store_true", help="Skip TTS, reuse saved narrations, remix music only")
    parser.add_argument("--music-url", help="URL to download background music from")
    parser.add_argument("--music-start", type=float, default=0, help="Start time in seconds for music track")
    parser.add_argument("--all", action="store_true", help="Generate all entries (uses no music)")
    args = parser.parse_args()

    if not TTS_TOKEN and not args.remix:
        print("✗ TIMESLICES_TTS_TOKEN not set in environment. Export it first.")
        sys.exit(1)

    lang = args.lang

    if args.all:
        entries = list(VOICE_MAPS.get(lang, VOICE_MAP_EN).keys())
        for entry_id in entries:
            duration = generate_podcast(entry_id, lang=lang, remix=args.remix)
            if duration:
                update_json(entry_id, duration, lang=lang)
    elif args.entry_id:
        duration = generate_podcast(
            args.entry_id, 
            lang=lang, 
            remix=args.remix,
            music_url=args.music_url,
            music_start=args.music_start
        )
        if duration:
            update_json(args.entry_id, duration, lang=lang)
    else:
        parser.print_help()
        return

    print(f"\n✅ Done!")


if __name__ == "__main__":
    main()
