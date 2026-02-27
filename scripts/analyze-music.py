#!/usr/bin/env python3
"""
Analyze music files to find optimal start times (skip silence/noise).

Usage:
    python3 scripts/analyze-music.py                    # analyze all music files
    python3 scripts/analyze-music.py bach-cello-suite-1 # analyze specific file
    python3 scripts/analyze-music.py --fix              # update generate-podcast.py with suggestions

Detects:
- Initial silence (< -30dB)
- Weak/quiet openings (< -25dB mean)
- Suggests start_time where music becomes salient
"""

import subprocess
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
MUSIC_DIR = PROJECT_DIR / "audio" / "music"
GENERATE_PODCAST_PY = PROJECT_DIR / "audio" / "generate-podcast.py"

# Thresholds
SILENCE_THRESHOLD_DB = -30  # Below this is considered silence
SALIENT_THRESHOLD_DB = -25  # Music should be at least this loud to be "salient"
MIN_SALIENT_DURATION = 1.0  # Need at least 1s of salient audio


def analyze_file(filepath: Path) -> dict:
    """Analyze a music file and return suggested start_time."""
    
    if not filepath.exists():
        return {"error": f"File not found: {filepath}"}
    
    # Get duration
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(filepath)],
        capture_output=True, text=True
    )
    duration = float(result.stdout.strip()) if result.returncode == 0 else 0
    
    # Detect silence periods
    result = subprocess.run(
        ["ffmpeg", "-i", str(filepath), "-af", 
         f"silencedetect=noise={SILENCE_THRESHOLD_DB}dB:d=0.3",
         "-f", "null", "-"],
        capture_output=True, text=True
    )
    
    silence_periods = []
    for line in result.stderr.split('\n'):
        if 'silence_end' in line:
            match = re.search(r'silence_end: ([\d.]+)', line)
            if match:
                silence_periods.append(float(match.group(1)))
    
    # Find first silence end (where audio actually starts)
    first_audio_start = silence_periods[0] if silence_periods else 0
    
    # Analyze volume in 2-second windows to find salient section
    best_start = first_audio_start
    best_volume = -100
    
    for t in range(int(first_audio_start), min(int(first_audio_start) + 30, int(duration) - 5), 2):
        result = subprocess.run(
            ["ffmpeg", "-i", str(filepath), "-ss", str(t), "-t", "3",
             "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True
        )
        
        match = re.search(r'mean_volume: ([-\d.]+) dB', result.stderr)
        if match:
            mean_vol = float(match.group(1))
            if mean_vol > best_volume and mean_vol > SALIENT_THRESHOLD_DB:
                best_volume = mean_vol
                best_start = t
                # If we found good audio, check if earlier is also good
                if mean_vol > -20:  # Very good audio
                    break
    
    # Round to nearest 0.5s
    suggested_start = round(best_start * 2) / 2
    
    return {
        "file": filepath.name,
        "duration": round(duration, 1),
        "first_audio": round(first_audio_start, 1),
        "suggested_start": suggested_start,
        "volume_at_start": round(best_volume, 1),
        "has_silence_intro": first_audio_start > 0.5,
    }


def get_current_start_times() -> dict:
    """Parse generate-podcast.py to get current start_times."""
    content = GENERATE_PODCAST_PY.read_text()
    
    # Extract MUSIC_POOL entries
    pool_match = re.search(r'MUSIC_POOL\s*=\s*\{(.+?)\n\}', content, re.DOTALL)
    if not pool_match:
        return {}
    
    start_times = {}
    # Find each entry with filename and start_time
    for match in re.finditer(r'"([^"]+)":\s*\{[^}]*"filename":\s*"([^"]+)"[^}]*"start_time":\s*([\d.]+)', content):
        key, filename, start_time = match.groups()
        start_times[filename] = {
            "key": key,
            "current_start": float(start_time)
        }
    
    return start_times


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("track", nargs="?", help="Specific track to analyze (filename without .mp3)")
    parser.add_argument("--fix", action="store_true", help="Show commands to fix start_times")
    args = parser.parse_args()
    
    current_times = get_current_start_times()
    
    if args.track:
        # Analyze specific track
        filepath = MUSIC_DIR / f"{args.track}.mp3"
        if not filepath.exists():
            # Try without extension
            filepath = MUSIC_DIR / args.track
        result = analyze_file(filepath)
        print(json.dumps(result, indent=2))
        return
    
    # Analyze all tracks
    print("# Music Track Analysis")
    print()
    print("| Track | Duration | Current Start | Suggested | Volume | Issue |")
    print("|-------|----------|---------------|-----------|--------|-------|")
    
    issues = []
    
    for mp3_file in sorted(MUSIC_DIR.glob("*.mp3")):
        result = analyze_file(mp3_file)
        if "error" in result:
            continue
        
        filename = mp3_file.name
        current_info = current_times.get(filename, {})
        current_start = current_info.get("current_start", 0)
        suggested = result["suggested_start"]
        
        # Determine if there's an issue
        issue = ""
        if result["has_silence_intro"] and current_start < result["first_audio"]:
            issue = "⚠️ Starts in silence"
            issues.append((filename, current_info.get("key", "?"), current_start, suggested))
        elif suggested - current_start > 2:
            issue = "⚠️ Could start later"
            issues.append((filename, current_info.get("key", "?"), current_start, suggested))
        elif result["volume_at_start"] < SALIENT_THRESHOLD_DB:
            issue = "⚠️ Quiet opening"
            issues.append((filename, current_info.get("key", "?"), current_start, suggested))
        else:
            issue = "✅"
        
        print(f"| {filename[:30]:30} | {result['duration']:6.1f}s | {current_start:13.1f} | {suggested:9.1f} | {result['volume_at_start']:5.1f}dB | {issue} |")
    
    if issues and args.fix:
        print()
        print("## Suggested Fixes")
        print()
        print("Update these entries in `audio/generate-podcast.py`:")
        print()
        for filename, key, current, suggested in issues:
            print(f"- `{key}`: change start_time from {current} → {suggested}")


if __name__ == "__main__":
    main()
