# Time Slices — Project Spec

**Last updated:** 2026-03-01

This is the single source of truth for the Time Slices cron job.
Read this file FIRST before doing anything.

---

## What Is This?

An interactive cross-disciplinary timeline exploring how art, literature, philosophy, and history connect across eras. Each entry ("slice") covers a pivotal moment in (primarily Western) history through 5 dimensions.

**Live site:** https://matteobettini.github.io/time_slices/  
**Repo:** https://github.com/matteobettini/time_slices  
**Project dir:** /home/cloud-user/.openclaw/workspace/time-slices/

## Multilingual

The site supports English and Italian. Content files:
- `slices.json` — English entries (primary)
- `slices.it.json` — Italian entries (must be kept in sync)
- Thread labels in `index.html` — both `en` and `it` objects in `THREAD_LABELS`
- Thread narratives in `index.html` — both `en` and `it` objects in `THREAD_NARRATIVES`

When adding a new entry, **always** add it to BOTH files. Italian translations should feel natural — not literal machine translation. Use Italian Wikipedia for sources where possible.

---

## Helper Scripts

All scripts are in `scripts/` directory:

| Script | Purpose |
|--------|---------|
| `add-entry.py` | Add entry to slices.json/slices.it.json with validation |
| `prep-image.sh` | Download, compress, and format image JSON |
| `find-music.py` | Search Internet Archive for period-appropriate music |
| `generate-podcast.py` | Generate podcast MP3 with TTS + background music (supports ElevenLabs + Edge TTS) |
| `summarize-entries.py` | Get overview of entries + examples for style reference |
| `verify-completion.py` | Check if entry is complete (MP3s, pushed, etc.) |

---

## Entry Schema

Every entry in `slices.json` MUST have this structure:

```json
{
  "year": "1504",
  "id": "1504-florence-duel-of-giants",
  "title": "Florence — The Duel of Giants",
  "teaser": "Short evocative hook, 1-2 sentences.",
  "dimensions": {
    "art":  { "label": "Art",         "content": "HTML string" },
    "lit":  { "label": "Literature",  "content": "HTML string" },
    "phil": { "label": "Philosophy",  "content": "HTML string" },
    "hist": { "label": "History",     "content": "HTML string" },
    "conn": { "label": "Connections", "content": "HTML string", "funFact": "optional" }
  },
  "sources": [
    { "url": "https://...", "title": "Source Name" }
  ],
  "image": {
    "url": "images/1504-david.jpg",
    "width": 800,
    "height": 600,
    "caption": "Description of the image",
    "attribution": "Author, License, via Wikimedia Commons"
  },
  "threads": ["thread-tag-1", "thread-tag-2"],
  "location": {
    "lat": 43.7696,
    "lon": 11.2558,
    "place": "Florence"
  },
  "addedDate": "2026-02-25T14:30:00Z",
  "podcast": {
    "url": "audio/1504-florence-duel-of-giants.mp3",
    "duration": 180
  }
}
```

### Field Details

#### id (mandatory)
- Format: `"{year}-{kebab-case-slug}"` e.g. `"1504-florence-duel-of-giants"`
- Used for podcast file naming, future features, and deduplication
- The slug should be derived from the title (lowercase, hyphens, no special chars)

#### dimensions
- All 5 dimensions are **mandatory**: art, lit, phil, hist, conn
- Each dimension: 2-4 sentences, ~300-500 chars max
- Use `<strong>` and `<em>` tags for emphasis (it's rendered as HTML)
- At most 1-2 `funFact` fields across the WHOLE entry (usually on `conn`)
- Fun facts go in the dimension object: `"funFact": "Text here"`

#### image (mandatory)
- Must be PUBLIC DOMAIN or CC-licensed from Wikimedia Commons
- **Use the prep-image.sh helper:**
  ```bash
  ./scripts/prep-image.sh <url_or_path> <entry-id> "Alt text description"
  ```
- This downloads, compresses (max 1200px, quality 85), and outputs image JSON with dimensions
- Copy the output JSON into your entry — `width` and `height` are included automatically
- Set `"url"` to the **local relative path**: `"images/1504-david.jpg"` (NOT the Wikimedia URL)
- Pick something visually compelling: a painting, building, map, manuscript, photograph

#### threads (mandatory)
- Array of 3-6 kebab-case strings identifying intellectual/cultural threads
- **Threads must be linkable across history** — they should appear in multiple entries and show how ideas transform over time
- **Threads must be historical, cultural, or thematic** — intellectual movements, artistic schools, philosophical currents, political transformations
- **Good threads:** `death-of-god`, `nominalism`, `classical-revival`, `reformation`, `vernacular-literature`, `existentialism`, `baroque`, `enlightenment`
- **Bad threads:** `biography`, `famous-people`, `wars`, `inventions` — generic categories that don't trace transforming ideas
- **REUSE existing thread tags** from other entries where they genuinely apply — prioritize connecting over creating
- New threads are fine if they represent genuine historical currents that other entries can join
- When adding NEW tags: also update `THREAD_LABELS` in `index.html` (see below)

#### location (mandatory)
- Object with `lat`, `lon` (decimal coordinates), and `place` (display name)
- Used for the map view — every entry must have a pin
- Pick the primary location that best represents the entry (where the central events occurred)
- If dimensions span multiple cities, pick the most significant one

#### addedDate (mandatory)
- Full ISO-8601 UTC timestamp: `"2026-02-25T14:30:00Z"`
- Used for the ☕ fresh badge — the entry with the latest `addedDate` gets the badge
- Must include time, not just date (to disambiguate same-day additions)

#### podcast (set by generate-podcast.py)
- Object with `url` (relative path to MP3) and `duration` (seconds)
- Set automatically by `scripts/generate-podcast.py`
- English audio in `audio/{id}.mp3`, Italian audio in `audio/it/{id}.mp3`
- Narrations cached in `audio/narrations/` (EN) and `audio/narrations/it/` (IT)
- `--remix` flag re-mixes with updated music settings without re-generating TTS

#### sources (mandatory)
- 3-5 URLs you actually consulted during research
- Format: `[{"url": "...", "title": "..."}]`

---

## Writing Guidelines

### Scope
- **Primarily Western** history and culture (Europe, Americas, Mediterranean)
- Non-Western entries RARELY — only truly pivotal moments (maybe 1 in 10)
- When a Western entry has non-Western connections, mention them in the Connections dimension

### Tone & Length
- Total entry: ~2000-2800 chars across all dimensions (NOT 4000+)
- Match existing entries in tone: vivid, precise, intellectually exciting
- Write for a curious person, not an academic — but never dumb it down

### Movement Contextualisation (CRITICAL)
Every dimension MUST contextualise within the broader cultural/intellectual MOVEMENT:
- **Art**: Don't just say "X painted Y" — explain the movement (Impressionism, Constructivism, etc.), what it was reacting against, and why it emerged THEN
- **Literature**: Place works in their literary movement, explain what that movement was responding to
- **Philosophy**: Name the school of thought, its predecessors, what problem it was trying to solve
- **History**: Frame events within larger political/economic/social currents
- **Connections**: Show how movements ACROSS dimensions influenced each other — this is the heart of Time Slices. **Every connection MUST be grounded in documented historical fact** — real influence, real correspondence, real patronage, real shared context. Don't invent poetic parallels that sound good but aren't historically attested. If Descartes actually read Montaigne, say so. If two figures just happened to live in the same century with no documented link, don't pretend they were in conversation. The connections should make the reader learn something true, not just feel clever.

### Research (mandatory before writing)
1. Do AT LEAST 3 separate web searches
2. Prefer: Wikipedia, Britannica, Stanford Encyclopedia of Philosophy, .edu sites, museum sites
3. Actually READ pages with web_fetch, don't just skim search snippets
4. If sources disagree, use qualifiers: "c.", "traditionally attributed to", "according to..."
5. Separate legends from documented facts

---

## index.html: Things You May Need to Update

### THREAD_LABELS object
When you add a NEW thread tag, you MUST add a human-readable label to the `THREAD_LABELS` object in `index.html` — in BOTH the `en` and `it` sub-objects. Find it in the `<script>` section:

```javascript
const THREAD_LABELS = {
  en: {
    'renaissance-humanism': 'Renaissance Humanism',
    // ...
  },
  it: {
    'renaissance-humanism': 'Umanesimo rinascimentale',
    // ...
  }
};
```

If a thread tag has no label, it auto-formats from kebab-case, but an explicit label is better.

### THREAD_NARRATIVES object
Add narratives explaining how threads connect entries across time:
```javascript
const THREAD_NARRATIVES = {
  en: {
    '1347→1517': 'Ockham's nominalism cracked scholastic authority; Luther drove a printing press through the gap.',
    // ...
  },
  it: {
    '1347→1517': 'Il nominalismo di Ockham incrinò l'autorità scolastica; Lutero vi fece irrompere la stampa.',
    // ...
  }
};
```
Format: `'YEAR_FROM→YEAR_TO': 'Narrative'` (use → character). Keep punchy: 1-2 sentences max.

### MARKERS array
Reference markers are small date labels on the timeline (e.g., "1453 — Fall of Constantinople"). If your new slice falls in a time period with no nearby markers, consider adding one. Find it in the `<script>` section:

```javascript
const MARKERS = [
  { year: 1453, label: "Fall of Constantinople" },
  // ...
];
```

---

## Deep Links

Entries are addressable via URL hash using the entry's `id`:
- `https://matteobettini.github.io/time_slices/#125-rome-dome-of-all-things`
- Legacy year-only hashes (`#1784`) are still supported as a fallback

DOM element IDs use the `entry-` prefix: `entry-125-rome-dome-of-all-things`.

---

## Podcast Generation

The script auto-selects TTS provider:
- **ElevenLabs** (preferred): Higher quality voices, uses `eleven_flash_v2_5` (EN) or `eleven_multilingual_v2` (IT)
- **Edge TTS** (fallback): Free Microsoft neural voices

Provider is selected automatically based on ELEVENLABS_API_KEY availability and remaining credits.

1. **Write scripts:**
   - EN: `audio/scripts/{id}.txt` (~350-400 words, storytelling style)
   - IT: `audio/scripts/it/{id}.txt` (culturally adapted, not literal)
   
   **⚠️ SPELL OUT ALL NUMBERS!** ElevenLabs mangles numerals. Write "twelve seventy-four" not "1274", "thirteenth century" not "13th century".

2. **Find music:**
   ```bash
   python3 scripts/find-music.py --era baroque --mood contemplative
   ```
   
   **⚠️ NO CHANTING!** Gregorian chant, plainchant, recited prayers compete with narration. Singing (opera, madrigals) is fine.

3. **Check credits (optional):**
   ```bash
   python3 scripts/generate-podcast.py --credits
   python3 scripts/generate-podcast.py --voices
   ```

4. **Generate podcasts:**
   ```bash
   # Auto-selects provider based on credits
   python3 scripts/generate-podcast.py {id} --lang en \
     --music-url "URL" --music-start SECONDS
   
   python3 scripts/generate-podcast.py {id} --lang it \
     --music-url "URL" --music-start SECONDS
   
   # Force a specific provider
   python3 scripts/generate-podcast.py {id} --lang en --provider elevenlabs
   python3 scripts/generate-podcast.py {id} --lang en --provider edge
   
   # Force a specific voice
   python3 scripts/generate-podcast.py {id} --lang en --voice en-GB-RyanNeural
   ```

5. **Verify:**
   ```bash
   ls -la audio/{id}.mp3 audio/it/{id}.mp3  # Both must exist and be >100KB
   ```

**Note:** Voices are randomly selected from curated pools for variety. The ELEVENLABS_API_KEY must be set in the environment (not committed to git).

---

## Deploy Checklist

After writing a new entry:

1. ✅ Read `slices.json`, append new entry, write back (or use `scripts/add-entry.py`)
2. ✅ **Also** add the Italian translation to `slices.it.json` — same structure, all text translated naturally
3. ✅ Ensure `location` (lat/lon/place) and `addedDate` (ISO timestamp) are set
4. ✅ Validate both files are proper JSON (parse them!)
5. ✅ Check for new thread tags → update `THREAD_LABELS` (both `en` and `it` sections) in `index.html`
6. ✅ If you add thread narratives → update both `en` and `it` sections in `THREAD_NARRATIVES`
7. ✅ Check if a new MARKER would help → update `MARKERS` in `index.html`
8. ✅ Generate podcasts (EN + IT) using `scripts/generate-podcast.py`
9. ✅ `git add -A && git commit -m "Add YEAR Place: Title" && git push "$(cat .git-push-url)" main`
10. ✅ Verify with `python3 scripts/verify-completion.py`
11. ✅ Reply with summary: year, title, teaser, one highlight connection (3-5 sentences max)

**DO NOT** deploy, tunnel, or expose anything. Only commit and push to git.

---

## Variety

Pick years/moments NOT already in `slices.json`. Aim for:
- Different centuries
- Different regions (within the Western focus)
- Different kinds of moments (artistic peaks, philosophical ruptures, political turning points)
- Don't cluster in the same era as existing entries
