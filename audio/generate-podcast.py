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
    # 532 Constantinople: reverent, echoing — fable for narrative warmth with gravitas
    "532-constantinople-the-last-great-building": {
        "voice": "fable",
        "instructions": "Speak as if standing inside a vast echoing space — reverent, measured, with quiet awe. This is about a building that was meant to make you feel the presence of God. Warm but not sentimental, precise but not clinical. Like a historian who genuinely loves what they're describing.",
    },
    # 1610 Padua: curious, precise, awestruck — sage for intellectual clarity with wonder
    "1610-padua-the-star-messenger": {
        "voice": "sage",
        "instructions": "Speak with intellectual curiosity and quiet wonder. This is the moment the telescope revealed new worlds — mountains on the Moon, moons around Jupiter. Precise but not dry, excited but not theatrical. Like a scientist who just saw something impossible.",
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
    "532-constantinople-the-last-great-building": {
        "voice": "fable",
        "instructions": "Parla in italiano con riverenza, come se ti trovassi dentro un vasto spazio che riecheggia. Misurato, con quieta meraviglia. Questo è un edificio concepito per farti sentire la presenza di Dio. Caldo ma non sentimentale, preciso ma non clinico.",
    },
    "1610-padua-the-star-messenger": {
        "voice": "sage",
        "instructions": "Parla in italiano con curiosità intellettuale e quieta meraviglia. Questo è il momento in cui il telescopio rivela nuovi mondi — monti sulla Luna, lune attorno a Giove. Preciso ma non arido, emozionato ma non teatrale. Come uno scienziato che ha appena visto qualcosa di impossibile.",
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
}

VOICE_MAPS = {"en": VOICE_MAP_EN, "it": VOICE_MAP_IT}

# ═══════════════════════════════════════════════════════════════════════════════
# MUSIC POOL — Large catalog of public domain tracks from Internet Archive
# organized by era/region. The cron agent picks from this pool when generating
# new entries. Each track has a verified URL, suggested start_time, and tags.
# ═══════════════════════════════════════════════════════════════════════════════
# Legacy pool for existing entries. New entries should use direct URLs in MUSIC_SOURCES
# (url, filename, description, start_time) — no need to add to this pool.
MUSIC_POOL = {
    # ── ANCIENT / MEDIEVAL (before 1400) ──────────────────────────────────
    "gregorian-chant-resurrexi": {
        "url": "https://archive.org/download/lp_grgorian-chant-easter-mass-pieces-from_choeur-des-moines-de-labbaye-saintpierre-d/disc1/01.02.%20Intro%C3%AFt%20%3A%20Resurrexi.mp3",
        "filename": "gregorian-chant.mp3",
        "description": "Gregorian chant — Introït: Resurrexi (Abbey of Solesmes)",
        "start_time": 10.0,
        "tags": ["medieval", "sacred", "choral", "europe", "monastic"],
    },
    "gregorian-kergonan": {
        "url": "https://archive.org/download/gregorianchantkergonan/01%20-%20Deus%20in%20adjutorium.mp3",
        "filename": "gregorian-kergonan.mp3",
        "description": "Gregorian chant — Deus in adjutorium (Kergonan Abbey)",
        "start_time": 0,
        "tags": ["medieval", "sacred", "choral", "europe", "monastic"],
    },
    "respighi-ancient-airs": {
        "url": "https://archive.org/download/c-2345-6-respighi-ancient-airs-suite-2-iii/C2345-6%20Respighi%20Ancient%20Airs%20Suite%202%20(ii).mp3",
        "filename": "respighi-ancient-airs.mp3",
        "description": "Respighi — Ancient Airs and Dances Suite 2 (evokes Roman/ancient world)",
        "start_time": 1.5,
        "tags": ["ancient", "orchestral", "rome", "neoclassical", "contemplative"],
    },

    # ── MIDDLE EAST / ISLAMIC WORLD ───────────────────────────────────────
    "oud-arabic-gulezyan": {
        "url": "https://archive.org/download/gulezyan-aram-1976-exotic-music-of-the-oud-lyrichord-side-a-archive-01/Gulezyan%2C%20Aram%20%281976%29%20-%20Exotic%20Music%20of%20the%20Oud%20Lyrichord%2C%20side%20A%20%28archive%29-01.mp3",
        "filename": "oud-arabic.mp3",
        "description": "Aram Gulezyan — Exotic Music of the Oud (traditional Arabic)",
        "start_time": 3.0,
        "tags": ["middle-east", "arabic", "oud", "traditional", "meditative"],
    },
    "persian-dinner-music": {
        "url": "https://archive.org/download/beautiful-slow-persian-iranian-dinner-music-192-kbps/Beautiful%20Slow%20Persian%20_%20Iranian%20Dinner%20Music%20-%20%20%D9%85%D9%88%D8%B3%DB%8C%D9%82%DB%8C%20%D8%B2%DB%8C%D8%A8%D8%A7%20%D9%88%20%D9%85%D9%84%D8%A7%DB%8C%D9%85%20%D8%A8%DB%8C%20%DA%A9%D9%84%D8%A7%D9%85%20%D8%A7%DB%8C%D8%B1%D8%A7%D9%86%DB%8C%20%28192%20kbps%29.mp3",
        "filename": "persian-dinner-music.mp3",
        "description": "Slow Persian/Iranian instrumental music — santoor, tar, setar",
        "start_time": 5.0,
        "tags": ["middle-east", "persian", "iran", "meditative", "instrumental"],
    },
    "persian-santoor": {
        "url": "https://archive.org/download/Master-Of-Persian-Santoo/02-Bidad.mp3",
        "filename": "persian-santoor.mp3",
        "description": "Master of Persian Santoor — Bidad",
        "start_time": 0,
        "tags": ["middle-east", "persian", "iran", "santoor", "classical"],
    },

    # ── EAST ASIAN ────────────────────────────────────────────────────────
    "shakuhachi-bell-ringing": {
        "url": "https://archive.org/download/lp_a-bell-ringing-in-the-empty-sky-japanese-s_goro-yamaguchi/disc1/01.01.%20Shika%20No%20T%C3%B4ne.mp3",
        "filename": "shakuhachi-bell-ringing.mp3",
        "description": "Goro Yamaguchi — Shika no Tōne (Japanese shakuhachi flute)",
        "start_time": 0,
        "tags": ["japan", "east-asia", "shakuhachi", "meditative", "traditional"],
    },
    "gamelan-javanese": {
        "url": "https://archive.org/download/SundaJavaneseDegungSulingGamelan/01%20-%20Raga%20Madenda.mp3",
        "filename": "gamelan-javanese.mp3",
        "description": "Javanese Degung Suling Gamelan — Raga Madenda",
        "start_time": 0,
        "tags": ["indonesia", "east-asia", "gamelan", "meditative", "traditional"],
    },

    # ── RENAISSANCE (1400-1600) ───────────────────────────────────────────
    "renaissance-lute-fantasia": {
        "url": "https://archive.org/download/lp_italian-songs-16th-and-17th-centuries-spa_hugues-cunod-hermann-leeb_0/disc1/01.02.%20Lute%20Solo%3A%20Fantasia.mp3",
        "filename": "renaissance-lute.mp3",
        "description": "Renaissance lute fantasia — 16th century Italian",
        "start_time": 14.0,
        "tags": ["renaissance", "lute", "italy", "instrumental", "intimate"],
    },
    "soler-harpsichord": {
        "url": "https://archive.org/download/GilbertRowland-AntonioSoler-SonatasForHarpsichord/01-SonataInFMajor.mp3",
        "filename": "soler-harpsichord.mp3",
        "description": "Antonio Soler — Sonata in F Major (harpsichord)",
        "start_time": 0,
        "tags": ["renaissance", "baroque", "harpsichord", "spain", "lively"],
    },

    # ── BAROQUE (1600-1750) ───────────────────────────────────────────────
    "bach-organ-canonic": {
        "url": "https://archive.org/download/canonic_variations_BWV_769a/01_Variation_I_%28Nel_canone_all%E2%80%99_ottava%29.mp3",
        "filename": "bach-organ.mp3",
        "description": "Bach — Canonic Variations BWV 769 (Baroque organ)",
        "start_time": 3.5,
        "tags": ["baroque", "organ", "germany", "sacred", "complex"],
    },
    "bach-cello-suite-1": {
        "url": "https://archive.org/download/BachCelloSuiteNo.1PreludeYoYoMa/Bach%20Cello%20Suite%20No.1%20-%20Prelude%20%28Yo-Yo%20Ma%29.mp3",
        "filename": "bach-cello-suite-1.mp3",
        "description": "Bach — Cello Suite No. 1 Prelude (Yo-Yo Ma)",
        "start_time": 5,
        "tags": ["baroque", "cello", "germany", "instrumental", "flowing"],
    },
    "vivaldi-four-seasons": {
        "url": "https://archive.org/download/Vivaldi-TheFourSeasonscomplete/01VivaldiSpring1stMovement-Allegro.mp3",
        "filename": "vivaldi-four-seasons-spring.mp3",
        "description": "Vivaldi — Four Seasons: Spring, 1st Movement Allegro",
        "start_time": 0,
        "tags": ["baroque", "violin", "italy", "energetic", "orchestral"],
    },

    # ── CLASSICAL (1750-1820) ─────────────────────────────────────────────
    "mozart-piano-k310": {
        "url": "https://archive.org/download/lp_piano-music-vol-6_arthur-balsam-wolfgang-amadeus-mozart/disc1/01.01.%20Sonata%20In%20A%20Minor%20K.310.mp3",
        "filename": "mozart-piano.mp3",
        "description": "Mozart — Piano Sonata K.310 in A minor",
        "start_time": 45.0,
        "tags": ["classical", "piano", "austria", "dramatic", "enlightenment"],
    },
    "beethoven-moonlight": {
        "url": "https://archive.org/download/LudwigVanBeethovenMoonlightSonataAdagioSostenutogetTune.net/Ludwig_Van_Beethoven_-_Moonlight_Sonata_Adagio_Sostenuto_(get-tune.net).mp3",
        "filename": "beethoven-moonlight.mp3",
        "description": "Beethoven — Moonlight Sonata, Adagio sostenuto",
        "start_time": 0,
        "tags": ["classical", "piano", "germany", "somber", "introspective"],
    },

    # ── ROMANTIC (1820-1900) ──────────────────────────────────────────────
    "chopin-nocturne-op9-1": {
        "url": "https://archive.org/download/FredericChopinNocturneOp.9No.1InBFlatMinor/Frederic%20Chopin%20-%20Nocturne%20Op.%209%2C%20no.%201%20in%20B%20flat%20minor.mp3",
        "filename": "chopin-nocturne-op9-1.mp3",
        "description": "Chopin — Nocturne Op. 9 No. 1 in B-flat minor",
        "start_time": 0,
        "tags": ["romantic", "piano", "poland", "nocturnal", "lyrical"],
    },
    "liszt-liebestraum": {
        "url": "https://archive.org/download/Liebestraum-FranzLiszt/Liebestraum.mp3",
        "filename": "liszt-liebestraum.mp3",
        "description": "Liszt — Liebestraum (Dream of Love)",
        "start_time": 0,
        "tags": ["romantic", "piano", "hungary", "lyrical", "passionate"],
    },
    "schubert-serenade": {
        "url": "https://archive.org/download/SchubertSerenade_441/SchubertSerenade.mp3",
        "filename": "schubert-serenade.mp3",
        "description": "Schubert — Serenade (Ständchen)",
        "start_time": 0,
        "tags": ["romantic", "piano", "austria", "lyrical", "gentle"],
    },
    "grieg-solveig": {
        "url": "https://archive.org/download/EdvardGriegSolveigsSonginstrumental/Edvard%20Grieg%20%2C%20Solveig%27s%20Song%20%28instrumental%29.mp3",
        "filename": "grieg-solveig.mp3",
        "description": "Grieg — Solveig's Song (instrumental, from Peer Gynt)",
        "start_time": 0,
        "tags": ["romantic", "orchestral", "norway", "nordic", "melancholic"],
    },

    # ── IMPRESSIONIST / EARLY MODERN (1880-1930) ──────────────────────────
    "debussy-clair-de-lune": {
        "url": "https://archive.org/download/DebussyClairDeLunevirgilFox/07-ClairDeLunefromSuiteBergamasque.mp3",
        "filename": "debussy-clair-de-lune.mp3",
        "description": "Debussy — Clair de lune (Suite Bergamasque)",
        "start_time": 12.0,
        "tags": ["impressionist", "piano", "france", "dreamy", "nocturnal"],
    },
    "ravel-pavane": {
        "url": "https://archive.org/download/PavanePourUneInfanteDefunte/Pavane%20pour%20une%20infante%20defunte.mp3",
        "filename": "ravel-pavane.mp3",
        "description": "Ravel — Pavane pour une infante défunte (elegant, wistful piano)",
        "start_time": 5.0,
        "tags": ["impressionist", "piano", "france", "belle-epoque", "elegant"],
    },
    "satie-gnossiennes": {
        "url": "https://archive.org/download/ThreeGnossiennesErikSatie/gnossiennes.mp3",
        "filename": "satie-gnossiennes.mp3",
        "description": "Satie — Trois Gnossiennes (mysterious, minimalist piano)",
        "start_time": 0,
        "tags": ["impressionist", "piano", "france", "mysterious", "minimalist"],
    },

    # ── SOUTH ASIAN ───────────────────────────────────────────────────────
    "raga-desh": {
        "url": "https://archive.org/download/AOC33B/AOC33B_04_Desh.mp3",
        "filename": "raga-desh.mp3",
        "description": "Raga Desh — Indian classical sitar",
        "start_time": 0,
        "tags": ["india", "south-asia", "sitar", "raga", "meditative"],
    },
}

# Background music sources from Internet Archive (public domain)
# Maps entry IDs → music track. Can use {"pool_key": "<key>"} for legacy pool entries,
# or direct {"url": "...", "filename": "...", "description": "...", "start_time": 0} for new ones.
MUSIC_SOURCES = {
    "125-rome-dome-of-all-things": {"pool_key": "respighi-ancient-airs"},
    "762-baghdad-round-city-of-reason": {"pool_key": "oud-arabic-gulezyan"},
    "1347-florence-beautiful-catastrophe": {"pool_key": "gregorian-chant-resurrexi"},
    "1504-florence-duel-of-giants": {"pool_key": "renaissance-lute-fantasia"},
    "1648-munster-exhaustion-of-god": {"pool_key": "bach-organ-canonic"},
    "1784-europe-dare-to-know": {"pool_key": "mozart-piano-k310"},
    "1889-paris-year-everything-changed": {"pool_key": "ravel-pavane"},
    "1922-modernist-explosion": {"pool_key": "satie-gnossiennes"},
    "532-constantinople-the-last-great-building": {
        "url": "https://archive.org/download/music-from-the-slavonic-orthodox-liturgy/6%20VELIKO%20SLAVOSLOVIE%20(The%20Great%20Glorification).mp3",
        "filename": "slavonic-great-glorification.mp3",
        "description": "Boris Christoff & Alexander Nevsky Cathedral Choir — The Great Glorification (Slavonic Orthodox Liturgy)",
        "start_time": 5
    },
  # 1610 Padua: early Baroque/transition from Renaissance — harpsichord suits the new science emerging
  "1610-padua-the-star-messenger": {"pool_key": "soler-harpsichord"},
  # 1517 Wittenberg: Renaissance lute — capturing the moment before the split, the last gasp of synthesis
  "1517-wittenberg-hammer-falls": {"pool_key": "renaissance-lute-fantasia"},
  # 1687 London: Bach cello suite — the peak of Baroque, mathematical precision meets emotional depth
  "1687-london-gravity-of-reason": {"pool_key": "bach-cello-suite-1"},
}


def _resolve_music_source(src):
    """Resolve a MUSIC_SOURCES entry, dereferencing pool_key if present."""
    if "pool_key" in src:
        pool_entry = MUSIC_POOL[src["pool_key"]]
        resolved = dict(pool_entry)
        # Allow overrides from the MUSIC_SOURCES entry (e.g. custom start_time)
        for k, v in src.items():
            if k != "pool_key":
                resolved[k] = v
        return resolved
    return src


def download_music(entry_id=None):
    """Download background music from Internet Archive."""
    os.makedirs(MUSIC_DIR, exist_ok=True)
    sources = {entry_id: MUSIC_SOURCES[entry_id]} if entry_id else MUSIC_SOURCES

    for eid, src in sources.items():
        src = _resolve_music_source(src)
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
    - Sidechain-style ducking: music at 20% during intro, ducks to 10% when voice enters
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
    # 5. Volume envelope: 20% intro → duck to 10% when voice enters → 20% outro
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
        f"volume=0.20,"
        f"afade=t=in:st=0:d=2.5,"
        # Duck music when voice is present: fade down at voice entry, fade up at voice exit
        f"volume=enable='between(t,{intro_duration},{voice_end_time})':volume=0.5,"
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


def generate_podcast(entry_id, lang="en", remix=False):
    """Full pipeline: script → narration → mix → output.
    
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

    # Download music if needed
    if entry_id in MUSIC_SOURCES:
        download_music(entry_id)

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

    # Get music path
    music_src = MUSIC_SOURCES.get(entry_id)
    if music_src:
        music_src = _resolve_music_source(music_src)
    music_path = os.path.join(MUSIC_DIR, music_src["filename"]) if music_src else None

    # Mix — Italian outputs go to audio/it/
    if lang == "it":
        it_dir = os.path.join(OUTPUT_DIR, "it")
        os.makedirs(it_dir, exist_ok=True)
        output_path = os.path.join(it_dir, f"{entry_id}.mp3")
    else:
        output_path = os.path.join(OUTPUT_DIR, f"{entry_id}.mp3")
    if music_path and os.path.exists(music_path) and os.path.getsize(music_path) > 10000:
        start_time = music_src.get("start_time", 0)
        
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
    parser.add_argument("--all", action="store_true", help="Generate all entries")
    parser.add_argument("--lang", default="en", choices=["en", "it"], help="Language (en or it)")
    parser.add_argument("--download-music", action="store_true", help="Download music only")
    parser.add_argument("--remix", action="store_true", help="Skip TTS, reuse saved narrations, remix music only")
    args = parser.parse_args()

    if not TTS_TOKEN and not args.remix and not args.download_music:
        print("✗ TIMESLICES_TTS_TOKEN not set in environment. Export it first.")
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
        duration = generate_podcast(entry_id, lang=lang, remix=args.remix)
        if duration:
            update_json(entry_id, duration, lang=lang)

    print(f"\n✅ Done!")


if __name__ == "__main__":
    main()
