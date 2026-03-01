#!/usr/bin/env python3
"""
Find public domain music from Internet Archive for Time Slices podcasts.

Usage:
    python3 scripts/find-music.py --era medieval --mood contemplative
    python3 scripts/find-music.py --query "baroque harpsichord"
    python3 scripts/find-music.py --era renaissance --region italy

Outputs JSON config ready to paste into MUSIC_SOURCES in generate-podcast.py.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import urllib.parse
import re
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# ERA/MOOD → SEARCH TERMS MAPPING
# ═══════════════════════════════════════════════════════════════════════════════

ERA_TERMS = {
    "ancient": ["ancient music", "greek music", "roman music", "lyre", "aulos"],
    "medieval": ["gregorian chant", "medieval music", "plainchant", "troubadour", "early music"],
    "renaissance": ["renaissance music", "lute music", "madrigal", "polyphony", "16th century music"],
    "baroque": ["baroque music", "harpsichord", "bach", "vivaldi", "handel", "17th century music"],
    "classical": ["classical period", "mozart", "haydn", "18th century music", "classical piano"],
    "romantic": ["romantic music", "chopin", "liszt", "brahms", "19th century music"],
    "early-modern": ["early 20th century", "debussy", "ravel", "satie", "impressionist music"],
    "modern": ["20th century classical", "stravinsky", "bartok", "modern classical"],
}

REGION_TERMS = {
    "europe": ["european classical", "western classical"],
    "italy": ["italian music", "italian baroque", "italian renaissance"],
    "france": ["french music", "french baroque", "french classical"],
    "germany": ["german music", "bach", "beethoven", "german romantic"],
    "spain": ["spanish music", "spanish guitar", "flamenco classical"],
    "england": ["english music", "english baroque", "purcell"],
    "middle-east": ["arabic music", "oud", "persian music", "ottoman music", "islamic music"],
    "byzantine": ["byzantine chant", "orthodox chant", "greek orthodox"],
    "india": ["indian classical", "raga", "sitar"],
    "china": ["chinese classical", "guqin", "chinese traditional"],
    "japan": ["japanese classical", "koto", "shakuhachi"],
}

MOOD_TERMS = {
    "contemplative": ["meditation", "peaceful", "calm", "ambient classical"],
    "dramatic": ["dramatic classical", "powerful", "epic orchestral"],
    "melancholic": ["sad classical", "melancholy", "minor key"],
    "triumphant": ["triumphant", "victorious", "celebratory classical"],
    "sacred": ["sacred music", "religious", "liturgical", "church music"],
    "courtly": ["court music", "dance", "elegant", "refined"],
    "pastoral": ["pastoral", "nature", "peaceful countryside"],
    "dark": ["dark classical", "ominous", "mysterious"],
}

INSTRUMENT_TERMS = {
    "piano": ["piano solo", "piano classical"],
    "organ": ["organ music", "church organ", "bach organ"],
    "harpsichord": ["harpsichord", "clavichord"],
    "lute": ["lute music", "renaissance lute"],
    "guitar": ["classical guitar", "spanish guitar"],
    "strings": ["string quartet", "violin", "cello"],
    "orchestra": ["orchestral", "symphony"],
    "choir": ["choral", "choir", "vocal ensemble"],
    "oud": ["oud", "arabic lute"],
}


# Collections/identifiers to reject (78rpm records have surface noise)
REJECT_PATTERNS = [
    r'78_',           # 78rpm record identifiers start with "78_"
    r'78rpm',
    r'georgeblood',   # George Blood's 78rpm transfers
    r'gbia\d+',       # Great 78 Project identifiers
]


def search_archive(query, max_results=20):
    """Search Internet Archive for audio files."""
    # Build search query - focus on audio, public domain, classical/traditional
    # Exclude 78rpm collections (surface noise)
    search_terms = f'({query}) AND mediatype:audio AND NOT collection:podcasts AND NOT collection:78rpm AND NOT collection:georgeblood'
    
    params = {
        'q': search_terms,
        'fl[]': ['identifier', 'title', 'description', 'creator'],
        'rows': max_results,
        'page': 1,
        'output': 'json',
    }
    
    url = 'https://archive.org/advancedsearch.php?' + urllib.parse.urlencode(params, doseq=True)
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return data.get('response', {}).get('docs', [])
    except Exception as e:
        print(f"Search error: {e}", file=sys.stderr)
        return []


def get_item_files(identifier):
    """Get audio files from an Archive.org item."""
    url = f'https://archive.org/metadata/{identifier}/files'
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            # Filter for MP3 files of reasonable size (500KB - 50MB)
            audio_files = []
            for f in data.get('result', []):
                if f.get('format') == 'VBR MP3' or f.get('name', '').endswith('.mp3'):
                    size = int(f.get('size', 0))
                    if 500_000 < size < 50_000_000:
                        audio_files.append({
                            'name': f['name'],
                            'size': size,
                            'length': f.get('length', ''),
                            'title': f.get('title', f['name']),
                        })
            return audio_files
    except Exception as e:
        print(f"Metadata error for {identifier}: {e}", file=sys.stderr)
        return []


def verify_audio(url, min_duration=60):
    """Download a sample and verify it has actual audio content."""
    try:
        # Download first 500KB to check
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Range': 'bytes=0-512000'
        })
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp_path = tmp.name
            with urllib.request.urlopen(req, timeout=20) as resp:
                tmp.write(resp.read())
        
        # Check duration
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', tmp_path],
            capture_output=True, text=True
        )
        
        # Check volume (not silent)
        vol_result = subprocess.run(
            ['ffmpeg', '-i', tmp_path, '-t', '30', '-af', 'volumedetect', '-f', 'null', '-'],
            capture_output=True, text=True
        )
        
        os.unlink(tmp_path)
        
        # Parse volume
        match = re.search(r'mean_volume: ([-\d.]+) dB', vol_result.stderr)
        if match:
            mean_vol = float(match.group(1))
            if mean_vol < -50:
                return False, "silent"
        
        return True, "ok"
        
    except Exception as e:
        try:
            os.unlink(tmp_path)
        except:
            pass
        return False, str(e)


def find_good_start_time(url):
    """Find a good start time by detecting where audio actually begins."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Range': 'bytes=0-1024000'  # First ~1MB
        })
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp_path = tmp.name
            with urllib.request.urlopen(req, timeout=30) as resp:
                tmp.write(resp.read())
        
        # Detect silence
        result = subprocess.run(
            ['ffmpeg', '-i', tmp_path, '-af', 'silencedetect=noise=-30dB:d=0.5',
             '-f', 'null', '-'],
            capture_output=True, text=True
        )
        
        os.unlink(tmp_path)
        
        # Find first silence_end (where audio starts)
        matches = re.findall(r'silence_end: ([\d.]+)', result.stderr)
        if matches:
            start = float(matches[0])
            return round(start, 1) if start < 30 else 0
        
        return 0
        
    except Exception as e:
        try:
            os.unlink(tmp_path)
        except:
            pass
        return 0


def build_query(era=None, region=None, mood=None, instrument=None, query=None):
    """Build search query from parameters."""
    terms = []
    
    if query:
        terms.append(query)
    if era and era in ERA_TERMS:
        terms.extend(ERA_TERMS[era][:2])  # Top 2 terms
    if region and region in REGION_TERMS:
        terms.extend(REGION_TERMS[region][:2])
    if mood and mood in MOOD_TERMS:
        terms.extend(MOOD_TERMS[mood][:1])
    if instrument and instrument in INSTRUMENT_TERMS:
        terms.extend(INSTRUMENT_TERMS[instrument][:1])
    
    # Default fallback
    if not terms:
        terms = ["classical music public domain"]
    
    return ' OR '.join(f'"{t}"' for t in terms[:4])


def main():
    parser = argparse.ArgumentParser(description='Find public domain music from Internet Archive')
    parser.add_argument('--era', choices=list(ERA_TERMS.keys()), help='Historical era')
    parser.add_argument('--region', choices=list(REGION_TERMS.keys()), help='Geographic region')
    parser.add_argument('--mood', choices=list(MOOD_TERMS.keys()), help='Mood/atmosphere')
    parser.add_argument('--instrument', choices=list(INSTRUMENT_TERMS.keys()), help='Primary instrument')
    parser.add_argument('--query', '-q', help='Custom search query')
    parser.add_argument('--verify', action='store_true', default=True, help='Verify tracks are audible')
    parser.add_argument('--no-verify', dest='verify', action='store_false', help='Skip verification')
    parser.add_argument('--limit', type=int, default=5, help='Max results to return')
    parser.add_argument('--json', action='store_true', help='Output raw JSON')
    
    args = parser.parse_args()
    
    if not any([args.era, args.region, args.mood, args.instrument, args.query]):
        parser.print_help()
        print("\nExamples:")
        print("  python3 scripts/find-music.py --era medieval --mood sacred")
        print("  python3 scripts/find-music.py --era baroque --instrument harpsichord")
        print("  python3 scripts/find-music.py --query 'debussy piano'")
        print("  python3 scripts/find-music.py --region middle-east --mood contemplative")
        sys.exit(1)
    
    query = build_query(args.era, args.region, args.mood, args.instrument, args.query)
    print(f"🔍 Searching: {query}", file=sys.stderr)
    
    items = search_archive(query, max_results=30)
    
    if not items:
        print("No results found.", file=sys.stderr)
        sys.exit(1)
    
    print(f"📦 Found {len(items)} items, scanning for tracks...", file=sys.stderr)
    
    results = []
    checked = 0
    
    for item in items:
        if len(results) >= args.limit:
            break
        
        identifier = item['identifier']
        
        # Skip 78rpm records (noisy surface crackle)
        if any(re.search(pat, identifier, re.IGNORECASE) for pat in REJECT_PATTERNS):
            continue
            
        files = get_item_files(identifier)
        
        for f in files[:3]:  # Check up to 3 files per item
            if len(results) >= args.limit:
                break
            
            url = f"https://archive.org/download/{identifier}/{urllib.parse.quote(f['name'])}"
            
            checked += 1
            print(f"  [{checked}] Checking: {f['title'][:50]}...", file=sys.stderr, end=' ')
            
            if args.verify:
                ok, reason = verify_audio(url)
                if not ok:
                    print(f"❌ ({reason})", file=sys.stderr)
                    continue
                print("✓", file=sys.stderr)
            else:
                print("(unverified)", file=sys.stderr)
            
            # Find good start time
            start_time = find_good_start_time(url) if args.verify else 0
            
            # Build result
            safe_name = re.sub(r'[^\w\-]', '-', f['name'].rsplit('.', 1)[0].lower())[:40]
            
            result = {
                'url': url,
                'filename': f"{safe_name}.mp3",
                'description': f"{item.get('creator', 'Unknown')} — {f['title'][:60]}",
                'start_time': start_time,
                'source_item': identifier,
                'source_title': item.get('title', ''),
            }
            results.append(result)
    
    if not results:
        print("\n❌ No suitable tracks found. Try different search terms.", file=sys.stderr)
        sys.exit(1)
    
    print(f"\n✅ Found {len(results)} suitable track(s):\n", file=sys.stderr)
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for i, r in enumerate(results, 1):
            print(f"── Track {i} ──")
            print(f"Description: {r['description']}")
            print(f"Source: {r['source_title'][:60]}")
            print()
            print("# Add to MUSIC_SOURCES in generate-podcast.py:")
            print(f'"YOUR-ENTRY-ID": {{')
            print(f'    "url": "{r["url"]}",')
            print(f'    "filename": "{r["filename"]}",')
            print(f'    "description": "{r["description"]}",')
            print(f'    "start_time": {r["start_time"]},')
            print(f'}},')
            print()


if __name__ == '__main__':
    main()
