#!/usr/bin/env python3
"""
Generate a podcast MP3 for a Time Slice entry.

USAGE:
    python3 generate-podcast.py <entry-id> --lang en
    python3 generate-podcast.py <entry-id> --lang it
    python3 generate-podcast.py <entry-id> --remix       # Reuse saved narration
    python3 generate-podcast.py --voices                 # List available voices
    python3 generate-podcast.py --credits                # Check ElevenLabs credits

TTS PROVIDERS:
    - ElevenLabs (preferred): Higher quality, uses eleven_flash_v2_5 model
      Automatically selected if ELEVENLABS_API_KEY is set and credits available
    - Edge TTS (fallback): Free Microsoft neural TTS via ~/bin/edge-tts

The script auto-selects provider based on:
    1. If --provider is specified, use that
    2. If ElevenLabs key exists and has >MIN_CREDITS chars remaining, use ElevenLabs
    3. Otherwise fall back to Edge TTS

VOICES:
    Run with --voices to see available voices for each provider.
    Voices are randomly selected from curated pools to add variety.
    Use --voice to force a specific voice.

Requires: ffmpeg, ~/bin/edge-tts (for Edge fallback)
"""

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import time
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
AUDIO_DIR = os.path.join(PROJECT_DIR, "audio")
SCRIPTS_DIR = os.path.join(AUDIO_DIR, "scripts")
MUSIC_DIR = os.path.join(SCRIPT_DIR, "music")
NARRATIONS_DIR = os.path.join(AUDIO_DIR, "narrations")

# Edge TTS wrapper script
EDGE_TTS_BIN = os.path.expanduser("~/bin/edge-tts")

# Minimum ElevenLabs credits to use it (reserve some buffer)
MIN_ELEVENLABS_CREDITS = 500

# ═══════════════════════════════════════════════════════════════════════════════
# VOICE POOLS - Curated voices for variety
# ═══════════════════════════════════════════════════════════════════════════════

# ElevenLabs voices (voice_id, name, description)
# Using premade voices that work with eleven_flash_v2_5
ELEVENLABS_VOICES_EN = [
    ("21m00Tcm4TlvDq8ikWAM", "Rachel", "calm, young female, American"),
    ("TxGEqnHWrfWFTfGW9XjX", "Josh", "deep, young male, American"),
    ("EXAVITQu4vr4xnSDxMaL", "Sarah", "soft, young female, American"),
    ("pNInz6obpgDQGcFmaJgB", "Adam", "deep male, American, narration"),
    ("Xb7hH8MSUJpSbSDYk0k2", "Alice", "confident female, British"),
    ("ErXwobaYiN019PkySvjV", "Antoni", "young male, American, versatile"),
    ("VR6AewLTigWG4xSOukaG", "Arnold", "crisp middle-aged male, American"),
    ("onwK4e9ZLuTAKqWW03F9", "Daniel", "deep middle-aged male, British"),
    ("ThT5KcBeYPX3keUQqHPh", "Dorothy", "pleasant young female, British"),
    ("XrExE9yKIg1WjnnlVkGX", "Matilda", "warm young female, American"),
]

ELEVENLABS_VOICES_IT = [
    # ElevenLabs multilingual voices work for Italian with eleven_multilingual_v2
    # But flash model is English-optimized; for IT we use multilingual model
    ("21m00Tcm4TlvDq8ikWAM", "Rachel", "calm female (multilingual)"),
    ("TxGEqnHWrfWFTfGW9XjX", "Josh", "deep male (multilingual)"),
    ("EXAVITQu4vr4xnSDxMaL", "Sarah", "soft female (multilingual)"),
    ("pNInz6obpgDQGcFmaJgB", "Adam", "deep male (multilingual)"),
    ("Xb7hH8MSUJpSbSDYk0k2", "Alice", "confident female (multilingual)"),
    ("ErXwobaYiN019PkySvjV", "Antoni", "young male (multilingual)"),
    ("VR6AewLTigWG4xSOukaG", "Arnold", "crisp male (multilingual)"),
    ("onwK4e9ZLuTAKqWW03F9", "Daniel", "deep male (multilingual)"),
    ("ThT5KcBeYPX3keUQqHPh", "Dorothy", "pleasant female (multilingual)"),
    ("XrExE9yKIg1WjnnlVkGX", "Matilda", "warm female (multilingual)"),
]

# Edge TTS voices (voice_name, description)
EDGE_VOICES_EN = [
    ("en-GB-RyanNeural", "British male, natural flow"),
    ("en-US-AvaNeural", "American female, expressive"),
    ("en-US-AndrewNeural", "American male, warm"),
    ("en-US-SteffanNeural", "American male, clear"),
    ("en-GB-SoniaNeural", "British female, professional"),
    ("en-US-JennyNeural", "American female, friendly"),
    ("en-US-GuyNeural", "American male, casual"),
    ("en-AU-WilliamNeural", "Australian male, warm"),
    ("en-GB-ThomasNeural", "British male, authoritative"),
    ("en-US-AriaNeural", "American female, professional"),
]

EDGE_VOICES_IT = [
    ("it-IT-DiegoNeural", "Italian male, natural"),
    ("it-IT-IsabellaNeural", "Italian female, natural"),
    ("it-IT-ElsaNeural", "Italian female, warm"),
    ("it-IT-GiuseppeNeural", "Italian male, expressive"),
    ("it-IT-BenignoNeural", "Italian male, calm"),
    ("it-IT-CalimeroNeural", "Italian male, friendly"),
    ("it-IT-CataldoNeural", "Italian male, mature"),
    ("it-IT-FabiolaNeural", "Italian female, bright"),
    ("it-IT-FiammaNeural", "Italian female, energetic"),
    ("it-IT-ImeldaNeural", "Italian female, professional"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# ELEVENLABS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_elevenlabs_key():
    """Get ElevenLabs API key from environment."""
    return os.environ.get("ELEVENLABS_API_KEY")


def check_elevenlabs_credits():
    """Check remaining ElevenLabs credits. Returns (remaining, limit) or (None, None) on error."""
    api_key = get_elevenlabs_key()
    if not api_key:
        return None, None
    
    try:
        req = urllib.request.Request(
            "https://api.elevenlabs.io/v1/user/subscription",
            headers={"xi-api-key": api_key}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            used = data.get("character_count", 0)
            limit = data.get("character_limit", 0)
            remaining = limit - used if limit else 0
            return remaining, limit
    except Exception as e:
        return None, None


def elevenlabs_tts(text, voice_id, output_path, lang="en"):
    """Generate TTS via ElevenLabs API. Returns True on success."""
    api_key = get_elevenlabs_key()
    if not api_key:
        return False
    
    # Use flash model for English (fastest/cheapest), multilingual for other languages
    model_id = "eleven_flash_v2_5" if lang == "en" else "eleven_multilingual_v2"
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = json.dumps({
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        }
    }).encode()
    
    try:
        req = urllib.request.Request(url, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as resp:
            with open(output_path, "wb") as f:
                f.write(resp.read())
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            return True
        return False
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        print(f"    ✗ ElevenLabs API error: {e.code} - {error_body[:200]}")
        return False
    except Exception as e:
        print(f"    ✗ ElevenLabs error: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# EDGE TTS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def edge_tts(text, voice, output_path, retries=2):
    """Generate TTS via Edge TTS wrapper. Returns True on success."""
    for attempt in range(1, retries + 1):
        try:
            result = subprocess.run(
                [EDGE_TTS_BIN, text, voice, output_path],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                return True
            else:
                print(f"    ⚠ Attempt {attempt}/{retries} failed: {result.stderr[:100]}")
        except subprocess.TimeoutExpired:
            print(f"    ⚠ Attempt {attempt}/{retries} timed out")
        except Exception as e:
            print(f"    ⚠ Attempt {attempt}/{retries} failed: {e}")
        
        if attempt < retries:
            time.sleep(2 * attempt)
    
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# PROVIDER SELECTION
# ═══════════════════════════════════════════════════════════════════════════════

def select_provider(script_length, force_provider=None):
    """Select TTS provider based on availability and credits.
    
    Returns: ("elevenlabs" | "edge", reason_string)
    """
    if force_provider:
        return force_provider, "forced via --provider"
    
    # Check ElevenLabs availability
    api_key = get_elevenlabs_key()
    if not api_key:
        return "edge", "no ELEVENLABS_API_KEY"
    
    remaining, limit = check_elevenlabs_credits()
    if remaining is None:
        return "edge", "couldn't check ElevenLabs credits"
    
    # Need enough credits for the script plus buffer
    needed = script_length + MIN_ELEVENLABS_CREDITS
    if remaining < needed:
        return "edge", f"ElevenLabs credits low ({remaining} remaining, need {needed})"
    
    return "elevenlabs", f"ElevenLabs has {remaining} chars remaining"


def select_voice(provider, lang, force_voice=None):
    """Select a voice for the given provider and language.
    
    Returns: (voice_id_or_name, display_name)
    """
    if force_voice:
        return force_voice, force_voice
    
    if provider == "elevenlabs":
        pool = ELEVENLABS_VOICES_EN if lang == "en" else ELEVENLABS_VOICES_IT
        voice_id, name, _ = random.choice(pool)
        return voice_id, name
    else:
        pool = EDGE_VOICES_EN if lang == "en" else EDGE_VOICES_IT
        voice_name, _ = random.choice(pool)
        return voice_name, voice_name

# ═══════════════════════════════════════════════════════════════════════════════
# MUSIC FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _verify_music_has_audio(filepath):
    """Check that a music file actually contains audio (not silence)."""
    result = subprocess.run(
        ["ffmpeg", "-i", filepath, "-t", "30", "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True
    )
    import re
    match = re.search(r'mean_volume: ([-\d.]+) dB', result.stderr)
    if match and float(match.group(1)) < -50:
        return False
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
        return None


def validate_music_start(music_path, start_time):
    """Check that music at start_time is not silent. Returns (ok, suggested_start)."""
    result = subprocess.run(
        ["ffmpeg", "-i", music_path, "-ss", str(start_time), "-t", "3",
         "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True
    )
    
    import re
    match = re.search(r'mean_volume: ([-\d.]+) dB', result.stderr)
    if not match:
        return True, start_time
    
    mean_vol = float(match.group(1))
    
    if mean_vol < -35:
        print(f"  ⚠️  Music at {start_time}s is quiet ({mean_vol:.1f}dB), searching for better start...")
        
        result = subprocess.run(
            ["ffmpeg", "-i", music_path, "-af", "silencedetect=noise=-30dB:d=0.3",
             "-f", "null", "-"],
            capture_output=True, text=True
        )
        
        for line in result.stderr.split('\n'):
            if 'silence_end' in line:
                match = re.search(r'silence_end: ([\d.]+)', line)
                if match:
                    end_time = float(match.group(1))
                    if end_time > start_time:
                        suggested = round(end_time * 2) / 2
                        print(f"  💡 Suggested start_time: {suggested}s")
                        return False, suggested
        
        return False, start_time + 2
    
    return True, start_time


# ═══════════════════════════════════════════════════════════════════════════════
# NARRATION GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

_CHUNK_THRESHOLD = 2000  # Split scripts longer than this


def generate_narration(entry_id, script_text, lang="en", provider="edge", voice=None):
    """Generate TTS narration using selected provider.
    
    Returns: (narration_path, duration, voice_used) or (None, 0, None) on failure
    """
    voice_id, voice_name = select_voice(provider, lang, voice)
    
    print(f"  🎤 Generating narration ({provider}: {voice_name}, {len(script_text)} chars)...")
    
    narration_path = f"/tmp/{entry_id}-narration.mp3"
    
    # For short scripts, single call
    if len(script_text) <= _CHUNK_THRESHOLD:
        if provider == "elevenlabs":
            success = elevenlabs_tts(script_text, voice_id, narration_path, lang)
        else:
            success = edge_tts(script_text, voice_id, narration_path)
        
        if not success:
            print(f"  ✗ TTS failed for {entry_id}")
            return None, 0, None
    else:
        # Long script — chunk by paragraph
        paragraphs = [p.strip() for p in script_text.split("\n\n") if p.strip()]
        print(f"  📄 Splitting into {len(paragraphs)} chunks...")
        part_paths = []
        
        for i, para in enumerate(paragraphs):
            part_path = f"/tmp/{entry_id}-part{i}.mp3"
            print(f"    Chunk {i+1}/{len(paragraphs)} ({len(para)} chars)...")
            
            if provider == "elevenlabs":
                success = elevenlabs_tts(para, voice_id, part_path, lang)
            else:
                success = edge_tts(para, voice_id, part_path)
            
            if not success:
                print(f"  ✗ TTS failed on chunk {i+1}")
                return None, 0, None
            
            part_paths.append(part_path)
            if i < len(paragraphs) - 1:
                time.sleep(0.5)
        
        # Concatenate with normalization
        normalized_paths = []
        silence_gap = 0.4
        
        for i, p in enumerate(part_paths):
            norm_path = f"/tmp/{entry_id}-part{i}-norm.mp3"
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", p,
                 "-af", f"loudnorm=I=-16:TP=-1.5:LRA=11,apad=pad_dur={silence_gap}",
                 "-c:a", "libmp3lame", "-b:a", "128k", norm_path],
                capture_output=True, text=True,
            )
            normalized_paths.append(norm_path if result.returncode == 0 else p)
        
        list_file = f"/tmp/{entry_id}-parts.txt"
        with open(list_file, "w") as f:
            for p in normalized_paths:
                f.write(f"file '{p}'\n")
        
        result = subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
             "-c:a", "libmp3lame", "-b:a", "128k", narration_path],
            capture_output=True, text=True,
        )
        
        if result.returncode != 0:
            print(f"  ✗ ffmpeg concat failed")
            return None, 0, None
        
        # Cleanup
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
    
    return narration_path, duration, voice_name

# ═══════════════════════════════════════════════════════════════════════════════
# AUDIO MIXING
# ═══════════════════════════════════════════════════════════════════════════════

def mix_audio(narration_path, music_path, output_path, narration_duration, start_time=0, voice=None, entry_id=None, provider=None):
    """Mix narration with background music using ffmpeg."""
    print(f"  🎵 Mixing with background music (start={start_time}s)...")

    intro_duration = 3.5
    outro_pad = 3.0
    total_duration = narration_duration + intro_duration + outro_pad
    voice_start_ms = int(intro_duration * 1000)
    voice_end_time = intro_duration + narration_duration
    
    filter_complex = (
        f"[1:a]atrim=start={start_time},asetpts=PTS-STARTPTS,"
        f"aloop=loop=-1:size=2e+09,atrim=duration={total_duration},"
        f"loudnorm=I=-20:TP=-2:LRA=7,"
        f"lowpass=f=4000:p=1,"
        f"acompressor=threshold=-25dB:ratio=3:attack=20:release=200,"
        f"volume=0.35,"
        f"afade=t=in:st=0:d=2.5,"
        f"volume=enable='between(t,{intro_duration},{voice_end_time})':volume=0.57,"
        f"afade=t=out:st={total_duration - 2.5}:d=2.5"
        f"[music];"
        f"[0:a]adelay={voice_start_ms}|{voice_start_ms}[voice];"
        f"[music][voice]amix=inputs=2:duration=longest:dropout_transition=2:normalize=0[mixed];"
        f"[mixed]loudnorm=I=-16:TP=-1.5:LRA=11[out]"
    )

    metadata_args = []
    if voice:
        comment = f"voice:{voice}"
        if provider:
            comment += f",provider:{provider}"
        metadata_args.extend(["-metadata", f"comment={comment}"])
    if entry_id:
        metadata_args.extend(["-metadata", f"title={entry_id}"])

    cmd = [
        "ffmpeg", "-y",
        "-i", narration_path,
        "-i", music_path,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:a", "libmp3lame", "-b:a", "128k",
        *metadata_args,
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


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def generate_podcast(entry_id, lang="en", remix=False, music_url=None, music_start=0, voice=None, provider=None):
    """Full pipeline: script → narration → mix → output."""
    lang_label = f" [{lang.upper()}]" if lang != "en" else ""
    print(f"\n🎙️  Generating podcast for: {entry_id}{lang_label}" + (" [REMIX]" if remix else ""))

    # Find script
    if lang == "it":
        script_path = os.path.join(SCRIPTS_DIR, "it", f"{entry_id}.txt")
    else:
        script_path = os.path.join(SCRIPTS_DIR, f"{entry_id}.txt")
    
    if not os.path.exists(script_path):
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

    # Select provider
    selected_provider, reason = select_provider(len(script_text), provider)
    print(f"  🔊 TTS provider: {selected_provider} ({reason})")

    # Download music if URL provided
    music_path = None
    if music_url:
        url_hash = hashlib.md5(music_url.encode()).hexdigest()[:8]
        music_filename = f"track-{url_hash}.mp3"
        music_path = download_music_track(music_url, music_filename)

    # Narration: generate or reuse
    narration_subdir = os.path.join(NARRATIONS_DIR, "it") if lang == "it" else NARRATIONS_DIR
    os.makedirs(narration_subdir, exist_ok=True)
    saved_narration = os.path.join(narration_subdir, f"{entry_id}.mp3")

    if remix and os.path.exists(saved_narration):
        narration_path = saved_narration
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", narration_path],
            capture_output=True, text=True
        )
        duration = float(result.stdout.strip()) if result.stdout.strip() else 0
        print(f"  ✓ Reusing saved narration: {os.path.getsize(narration_path) // 1024}KB, {duration:.1f}s")
        voice_used = "cached"
        cleanup_narration = False
    elif remix:
        # Extract from existing podcast
        if lang == "it":
            existing_mp3 = os.path.join(AUDIO_DIR, "it", f"{entry_id}.mp3")
        else:
            existing_mp3 = os.path.join(AUDIO_DIR, f"{entry_id}.mp3")
        if os.path.exists(existing_mp3):
            print(f"  🔧 Extracting voice from existing podcast...")
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", existing_mp3, "-ss", "3.5",
                 "-c:a", "libmp3lame", "-b:a", "128k", saved_narration],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"  ✗ Extraction failed")
                return False
            narration_path = saved_narration
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", narration_path],
                capture_output=True, text=True
            )
            duration = float(result.stdout.strip()) if result.stdout.strip() else 0
            voice_used = "extracted"
            cleanup_narration = False
        else:
            print(f"  ✗ No existing podcast to extract from")
            return False
    else:
        # Generate new narration
        narration_path, duration, voice_used = generate_narration(
            entry_id, script_text, lang=lang, provider=selected_provider, voice=voice
        )
        if not narration_path:
            return False
        subprocess.run(["cp", narration_path, saved_narration])
        cleanup_narration = True

    # Output path
    if lang == "it":
        it_dir = os.path.join(AUDIO_DIR, "it")
        os.makedirs(it_dir, exist_ok=True)
        output_path = os.path.join(it_dir, f"{entry_id}.mp3")
    else:
        output_path = os.path.join(AUDIO_DIR, f"{entry_id}.mp3")

    # Mix
    if music_path and os.path.exists(music_path) and os.path.getsize(music_path) > 10000:
        music_ok, suggested_start = validate_music_start(music_path, music_start)
        if not music_ok:
            print(f"  ⚠️  Using suggested start_time {suggested_start}s")
            music_start = suggested_start
        
        mix_audio(narration_path, music_path, output_path, duration, 
                  start_time=music_start, voice=voice_used, entry_id=entry_id, provider=selected_provider)
    else:
        subprocess.run([
            "ffmpeg", "-y", "-i", narration_path,
            "-c:a", "libmp3lame", "-b:a", "128k",
            "-metadata", f"comment=voice:{voice_used or 'unknown'},provider:{selected_provider}",
            "-metadata", f"title={entry_id}",
            output_path
        ], capture_output=True)
        print(f"  ⚠ No music available, narration-only")

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

    return final_duration, voice_used


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
    print(f"  📄 Updated {'slices.it.json' if lang == 'it' else 'slices.json'}")

# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def print_voices():
    """Print available voices for both providers."""
    print("\n🎤 Available TTS Voices\n")
    print("=" * 70)
    
    print("\n📡 ELEVENLABS (higher quality, uses credits)")
    print("-" * 70)
    
    print("\n  🇬🇧🇺🇸 English (eleven_flash_v2_5):")
    for voice_id, name, desc in ELEVENLABS_VOICES_EN:
        print(f"    {name:<12} - {desc}")
    
    print("\n  🇮🇹 Italian (eleven_multilingual_v2):")
    for voice_id, name, desc in ELEVENLABS_VOICES_IT:
        print(f"    {name:<12} - {desc}")
    
    print("\n" + "=" * 70)
    print("\n🆓 EDGE TTS (free, Microsoft neural voices)")
    print("-" * 70)
    
    print("\n  🇬🇧🇺🇸 English:")
    for voice_name, desc in EDGE_VOICES_EN:
        print(f"    {voice_name:<22} - {desc}")
    
    print("\n  🇮🇹 Italian:")
    for voice_name, desc in EDGE_VOICES_IT:
        print(f"    {voice_name:<22} - {desc}")
    
    print("\n" + "=" * 70)
    print("\nVoices are randomly selected from pools for variety.")
    print("Use --voice <name> to force a specific voice.")
    print("Use --provider edge|elevenlabs to force a provider.\n")


def print_credits():
    """Print ElevenLabs credit status."""
    print("\n💰 ElevenLabs Credit Status\n")
    
    api_key = get_elevenlabs_key()
    if not api_key:
        print("  ✗ No ELEVENLABS_API_KEY found in environment")
        return
    
    remaining, limit = check_elevenlabs_credits()
    if remaining is None:
        print("  ✗ Could not check credits (API error)")
        return
    
    used = limit - remaining
    pct = (used / limit * 100) if limit else 0
    
    print(f"  Tier:      Free")
    print(f"  Used:      {used:,} / {limit:,} characters ({pct:.1f}%)")
    print(f"  Remaining: {remaining:,} characters")
    print()
    
    if remaining < MIN_ELEVENLABS_CREDITS:
        print(f"  ⚠️  Below minimum threshold ({MIN_ELEVENLABS_CREDITS}), will use Edge TTS")
    else:
        avg_script = 2000
        podcasts_left = remaining // avg_script
        print(f"  ✓ Enough for ~{podcasts_left} podcasts (avg {avg_script} chars each)")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Generate Time Slice podcasts with ElevenLabs or Edge TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    python3 generate-podcast.py 1504-florence --lang en
    python3 generate-podcast.py 1504-florence --lang it --provider elevenlabs
    python3 generate-podcast.py 1504-florence --remix --music-url "URL" --music-start 5
    python3 generate-podcast.py --voices
    python3 generate-podcast.py --credits
        """
    )
    parser.add_argument("entry_id", nargs="?", help="Entry ID to generate")
    parser.add_argument("--lang", default="en", choices=["en", "it"], help="Language")
    parser.add_argument("--remix", action="store_true", help="Reuse saved narration, remix music only")
    parser.add_argument("--music-url", help="URL for background music")
    parser.add_argument("--music-start", type=float, default=0, help="Music start time in seconds")
    parser.add_argument("--voice", help="Force specific voice")
    parser.add_argument("--provider", choices=["edge", "elevenlabs"], help="Force TTS provider")
    parser.add_argument("--voices", action="store_true", help="List available voices")
    parser.add_argument("--credits", action="store_true", help="Check ElevenLabs credits")
    args = parser.parse_args()

    if args.voices:
        print_voices()
        return
    
    if args.credits:
        print_credits()
        return

    if not args.entry_id:
        parser.print_help()
        return

    # Check Edge TTS is available as fallback
    if not os.path.exists(EDGE_TTS_BIN) and args.provider != "elevenlabs":
        print(f"⚠️  Edge TTS wrapper not found at {EDGE_TTS_BIN}")
        if not get_elevenlabs_key():
            print("✗ No TTS provider available")
            sys.exit(1)

    result = generate_podcast(
        args.entry_id,
        lang=args.lang,
        remix=args.remix,
        music_url=args.music_url,
        music_start=args.music_start,
        voice=args.voice,
        provider=args.provider
    )
    
    if result:
        duration, voice_used = result
        update_json(args.entry_id, duration, lang=args.lang)
        print(f"\n✅ Done!")
    else:
        print(f"\n✗ Failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
