#!/usr/bin/env python3
"""
Generate a podcast MP3 for a Time Slice entry.

Usage:
    python3 generate-podcast.py <entry-id> --lang en --voice en-GB-RyanNeural
    python3 generate-podcast.py <entry-id> --lang it --voice it-IT-DiegoNeural
    python3 generate-podcast.py <entry-id> --remix  # Reuse saved narration, remix music only

Uses Edge TTS (Microsoft's free neural TTS) for narration via ~/bin/edge-tts wrapper,
and period-appropriate background music from Internet Archive (public domain).

Requires: ffmpeg, ~/bin/edge-tts (node-edge-tts wrapper)

═══════════════════════════════════════════════════════════════════════════════
MUSIC — Pass via CLI: --music-url <url> --music-start <seconds>
Use scripts/find-music.py to discover tracks from Internet Archive

Finding music on Internet Archive:
  Search: https://archive.org/advancedsearch.php?q=<query>+AND+mediatype:audio&output=json
  Files:  https://archive.org/metadata/<identifier>/files
  Download: https://archive.org/download/<identifier>/<filename>

Collections by era:
  - Ancient/Medieval: gregorian chant, medieval music, byzantine chant
  - Middle East: oud music, persian classical, arabic maqam
  - Renaissance: renaissance lute, madrigal, harpsichord
  - Baroque: bach, vivaldi, handel
  - Classical: mozart, beethoven, haydn
  - Romantic: chopin, liszt, brahms
  - Impressionist: debussy, ravel, satie

Tips:
  - Instrumental works best
  - Slower pieces mix better with narration
  - Set start_time to skip silence (many tracks have 2-10s of silence at start)
  - Use find-music.py for easy discovery

⚠️  MUSIC START_TIME IS CRITICAL
Many tracks have silence or noise at the beginning. The podcast intro is only
3.5s — the music must be immediately salient. When using a new track:
  1. Download and listen to the first 10-15 seconds
  2. Set --music-start to skip silence/weak opening (usually 2-10 seconds)
  3. If unsure: ffmpeg -i track.mp3 -af "silencedetect=noise=-30dB:d=0.3" -f null -
═══════════════════════════════════════════════════════════════════════════════
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
AUDIO_DIR = os.path.join(PROJECT_DIR, "audio")
SCRIPTS_DIR = os.path.join(AUDIO_DIR, "scripts")
MUSIC_DIR = os.path.join(SCRIPT_DIR, "music")

# Edge TTS wrapper script
EDGE_TTS_BIN = os.path.expanduser("~/bin/edge-tts")

# Default voices for each language
DEFAULT_VOICE_EN = "en-GB-RyanNeural"  # British voice suits historical narration
DEFAULT_VOICE_IT = "it-IT-DiegoNeural"


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


def _tts_edge(text, voice, out_path, retries=2):
    """Call Edge TTS via the wrapper script. Returns True on success."""
    import time as _time
    
    for attempt in range(1, retries + 1):
        try:
            result = subprocess.run(
                [EDGE_TTS_BIN, text, voice, out_path],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                return True
            else:
                print(f"    ⚠ Attempt {attempt}/{retries} failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"    ⚠ Attempt {attempt}/{retries} timed out")
        except Exception as e:
            print(f"    ⚠ Attempt {attempt}/{retries} failed: {e}")
        
        if attempt < retries:
            _time.sleep(2 * attempt)  # backoff: 2s, 4s
    
    return False


# Threshold in chars: scripts longer than this are split into paragraph chunks
_CHUNK_THRESHOLD = 2000


def generate_narration(entry_id, script_text, lang="en", voice=None):
    """Generate TTS narration via Edge TTS.

    For short scripts (≤ _CHUNK_THRESHOLD chars), sends a single request.
    For longer scripts, splits by paragraph, generates each chunk, and
    concatenates with ffmpeg.
    
    Args:
        voice: Edge TTS voice name (e.g., en-GB-RyanNeural, it-IT-DiegoNeural)
    """
    # Use provided voice or defaults
    if voice is None:
        voice = DEFAULT_VOICE_EN if lang == "en" else DEFAULT_VOICE_IT

    print(f"  🎤 Generating narration (voice: {voice}, {len(script_text)} chars)...")

    narration_path = f"/tmp/{entry_id}-narration.mp3"

    # --- Decide: single call or chunked ---
    if len(script_text) <= _CHUNK_THRESHOLD:
        # Short script — single TTS call
        if not _tts_edge(script_text, voice, narration_path, retries=2):
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
            if not _tts_edge(para, voice, part_path, retries=2):
                print(f"  ✗ TTS failed on chunk {i+1}")
                return None, 0
            part_paths.append(part_path)
            if i < len(paragraphs) - 1:
                _time.sleep(0.5)  # small delay between calls

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


def mix_audio(narration_path, music_path, output_path, narration_duration, start_time=0, voice=None, entry_id=None):
    """Mix narration with background music using ffmpeg.
    
    Improvements over basic mix:
    - Music starts from a curated timestamp (skip silence/weak openings)
    - Low-pass filter at 4kHz to avoid competing with voice frequencies
    - Sidechain-style ducking: music at 35% during intro/outro, ducks to 20% during narration
    - Longer 3.5s music intro to establish mood before narration
    - Gentle compression to even out music dynamics
    - Embeds voice used in MP3 metadata (comment field)
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

    # Build metadata args
    metadata_args = []
    if voice:
        metadata_args.extend(["-metadata", f"comment=voice:{voice}"])
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


NARRATIONS_DIR = os.path.join(AUDIO_DIR, "narrations")


def generate_podcast(entry_id, lang="en", remix=False, music_url=None, music_start=0, voice=None):
    """Full pipeline: script → narration → mix → output.
    
    Args:
        entry_id: The slice entry ID
        lang: "en" or "it"  
        remix: If True, skip TTS and reuse saved narration
        music_url: URL to download background music from (optional)
        music_start: Start time in seconds for music track
        voice: Edge TTS voice (e.g., en-GB-RyanNeural, it-IT-DiegoNeural)
    
    If remix=True, skip TTS and reuse saved narration from audio/narrations/.
    If no saved narration exists, extract voice from existing podcast MP3
    (strips old 3.5s music intro).
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
            existing_mp3 = os.path.join(AUDIO_DIR, "it", f"{entry_id}.mp3")
        else:
            existing_mp3 = os.path.join(AUDIO_DIR, f"{entry_id}.mp3")
        if os.path.exists(existing_mp3):
            print(f"  🔧 Extracting voice from existing podcast (stripping old 3.5s intro)...")
            # Current mix has 3.5s music intro; trim it to get narration-start-aligned audio
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", existing_mp3, "-ss", "3.5",
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
        narration_path, duration = generate_narration(entry_id, script_text, lang=lang, voice=voice)
        if not narration_path:
            return False
        # Save narration for future remixes
        subprocess.run(["cp", narration_path, saved_narration])
        cleanup_narration = True

    # Mix — Italian outputs go to audio/it/
    if lang == "it":
        it_dir = os.path.join(AUDIO_DIR, "it")
        os.makedirs(it_dir, exist_ok=True)
        output_path = os.path.join(it_dir, f"{entry_id}.mp3")
    else:
        output_path = os.path.join(AUDIO_DIR, f"{entry_id}.mp3")
    if music_path and os.path.exists(music_path) and os.path.getsize(music_path) > 10000:
        start_time = music_start
        
        # Validate music isn't silent at start_time
        music_ok, suggested_start = validate_music_start(music_path, start_time)
        if not music_ok:
            print(f"  ⚠️  Using suggested start_time {suggested_start}s instead of {start_time}s")
            start_time = suggested_start
        
        mix_audio(narration_path, music_path, output_path, duration, start_time=start_time, voice=voice, entry_id=entry_id)
    else:
        # Even for narration-only, embed metadata
        subprocess.run([
            "ffmpeg", "-y", "-i", narration_path,
            "-c:a", "libmp3lame", "-b:a", "128k",
            "-metadata", f"comment=voice:{voice or 'unknown'}",
            "-metadata", f"title={entry_id}",
            output_path
        ], capture_output=True)
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

    # Return duration and the voice that was used
    return final_duration, voice


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
    parser.add_argument("--voice", help="Edge TTS voice (e.g., en-GB-RyanNeural, it-IT-DiegoNeural)")
    args = parser.parse_args()

    # Check edge-tts is available
    if not os.path.exists(EDGE_TTS_BIN) and not args.remix:
        print(f"✗ Edge TTS wrapper not found at {EDGE_TTS_BIN}")
        sys.exit(1)

    lang = args.lang

    if args.entry_id:
        result = generate_podcast(
            args.entry_id, 
            lang=lang, 
            remix=args.remix,
            music_url=args.music_url,
            music_start=args.music_start,
            voice=args.voice
        )
        if result:
            duration, voice_used = result
            update_json(args.entry_id, duration, lang=lang)
    else:
        parser.print_help()
        return

    print(f"\n✅ Done!")


if __name__ == "__main__":
    main()
