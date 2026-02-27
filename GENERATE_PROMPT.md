You are Johnny, managing the Time Slices project.

## 🚨 CRITICAL: READ THIS FIRST 🚨

**This task is NOT complete until you have:**
1. ✅ MP3 files exist: `audio/{id}.mp3` AND `audio/it/{id}.mp3`
2. ✅ Git push succeeded (not just commit)
3. ✅ You have verified BOTH with actual commands

**If you reply before completing ALL steps below, the task is FAILED.**
**Partial work (JSON only, no podcasts) has happened 4+ times. Do not repeat this.**

---

## Content Rules

**HTML formatting:** Dimension content uses **HTML**, not markdown. Use `<strong>bold</strong>` and `<em>italic</em>`, NOT `**bold**` or `*italic*`.

**JSON editing:** Use the helper script (validates fields and checks for duplicates):
```bash
# Save entry to file first (recommended for complex entries):
python3 scripts/add-entry.py --file new-entry.json           # EN
python3 scripts/add-entry.py --file new-entry.json --lang it  # IT

# Or inline (for simple entries):
python3 scripts/add-entry.py '{"year": "1610", "id": "1610-...", ...}'
```

---

## PHASE 1: Research & Content (Steps 1-11)

1. **Read the spec:** `/home/cloud-user/.openclaw/workspace/time-slices/SPEC.md` — follow it exactly.

2. **Get entry summary** (DO NOT read full JSON files — wastes tokens):
    ```bash
    cd /home/cloud-user/.openclaw/workspace/time-slices
    python3 scripts/summarize-entries.py --examples 2
    ```
    This shows: all years/threads covered, timeline gaps, geographic distribution, and 2 example entries for style reference.

3. **Timeline awareness:** Glance at the distribution. Filling gaps is nice but not required — clustering in rich periods (Renaissance, Enlightenment, early 20th century) is fine and natural.

4. **Quality self-check:** Before committing to a year, verify it has genuine depth in ALL 5 dimensions (🎨 Art, 📖 Literature, 🧠 Philosophy, ⚔️ History, 🔗 Connections). If any feels thin, pick a different year.

5. **Movement labels are MANDATORY.** Each dimension MUST name its cultural/intellectual movement. Don't just describe works — place them in their movement and explain why it emerged THEN.

6. **Connections must be GROUNDED.** The 🔗 Connections dimension must describe real, documented cross-dimensional influence — not poetic parallels. If you can't cite it, don't claim it.

7. **Thread connectivity and quality:**
   - Threads must be **historical, cultural, or thematic** — intellectual movements, artistic schools, philosophical currents
   - **Good threads:** `death-of-god`, `nominalism`, `classical-revival`, `reformation`, `vernacular-literature`, `existentialism`
   - **Bad threads:** `biography`, `famous-people`, `wars`, `inventions` — generic categories, not traceable ideas
   - **Prioritize connecting to existing threads** over creating new ones. Check the summary output first.
   - **⚠️ AVOID DUPLICATE THREADS:** Don't create near-synonyms like `christian-humanism` when `renaissance-humanism` exists.

8. **Add ONE new entry** following the spec. Include:
   - City in title only if dimensions converge there; otherwise use thematic title
   - `location` field (always required for map)
   - `addedDate` as full ISO-8601 UTC timestamp (e.g. `"2026-02-25T14:30:00Z"`)

9. **Add Italian version** to `slices.it.json` — natural Italian, not machine translation.

10. **Update THREAD_LABELS** in `index.html` if you add new thread tags (both en and it sections).

11. **Add THREAD_NARRATIVES** in `index.html` for connections to existing entries:
    - Find the `THREAD_NARRATIVES` object (both `en` and `it` sections)
    - Format: `'YEAR_FROM→YEAR_TO': 'Your narrative here'` (use → character)
    - **Keep it punchy:** 1-2 sentences max. State the *mechanism* of transmission, not just "X years later"
    - Good: `'1347→1517': 'Ockham's nominalism cracked scholastic authority; Luther drove a printing press through the gap.'`
    - Focus on: who read whom, what text traveled where, which student taught which teacher

---

## PHASE 2: Podcasts (Steps 12-14) — MANDATORY

⚠️ **DO NOT SKIP THIS PHASE. Previous runs have failed by stopping after Phase 1.**

12. **Write podcast scripts:**
    - EN script (~350-400 words, storytelling style) → `audio/scripts/{id}.txt`
    - IT script (culturally adapted, not literal) → `audio/scripts/it/{id}.txt`

13. **Add config to `audio/generate-podcast.py`:**
    - Add entry to `VOICE_MAP_EN` dict with voice + style instructions
    - Add entry to `VOICE_MAP_IT` dict with voice + Italian instructions  
    - Add entry to `MUSIC_SOURCES` dict (use pool_key or direct URL from Internet Archive)
    - Voices: alloy, ash, ballad, coral, echo, fable, nova, sage, shimmer, verse. ⚠️ Do NOT use `onyx` (buggy).

14. **Generate podcasts:**
    ```bash
    cd /home/cloud-user/.openclaw/workspace/time-slices
    python3 audio/generate-podcast.py {id} --lang en
    python3 audio/generate-podcast.py {id} --lang it
    ```
    
    **VERIFY BOTH EXIST:**
    ```bash
    ls -la audio/{id}.mp3 audio/it/{id}.mp3
    ```
    Both files must exist and be >100KB. If not, debug and retry.

---

## PHASE 3: Publish (Steps 15-16) — MANDATORY

⚠️ **DO NOT SKIP THIS PHASE. The entry is NOT LIVE until pushed.**

15. **Commit and push:**
    ```bash
    cd /home/cloud-user/.openclaw/workspace/time-slices
    git add -A
    git commit -m "Add YEAR Place: Title"
    git push "$(cat .git-push-url)" main
    ```
    
    **VERIFY PUSH SUCCEEDED.** Look for `main -> main` in output. If you see `rejected` or `error`, fix it.

16. **Final reply** (ONLY after steps 14-15 verified):
    - Year, title, teaser, one highlight connection (3-5 sentences)
    - Direct link: `https://matteobettini.github.io/time_slices/#ID`
    - No backticks around the URL — it must be clickable

---

## 🔒 COMPLETION GATE

Before sending your final reply, run this verification:

```bash
cd /home/cloud-user/.openclaw/workspace/time-slices
python3 scripts/verify-completion.py
```

✅ If it shows `COMPLETE` → send final reply
❌ If it shows `INCOMPLETE` → follow the `resume_prompt` in the output to fix remaining issues

---

## Music: Finding tracks on Internet Archive

Search: `https://archive.org/advancedsearch.php?q=<query>+AND+mediatype:audio&output=json`
Files: `https://archive.org/metadata/<identifier>/files`
Download: `https://archive.org/download/<identifier>/<filename>`

**Collections by era:**
- Ancient/Medieval: `gregorian chant`, `medieval music`, `byzantine chant`
- Middle East: `oud music`, `persian classical`, `arabic maqam`
- Renaissance: `renaissance lute`, `madrigal`, `harpsichord`
- Baroque: `bach`, `vivaldi`, `handel`
- Classical: `mozart`, `beethoven`, `haydn`
- Romantic: `chopin`, `liszt`, `brahms`
- Impressionist: `debussy`, `ravel`, `satie`

**Tips:** Instrumental works best. Slower pieces mix better. Set `start_time` to skip silence.
