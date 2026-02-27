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

**HTML formatting:** Dimension content uses HTML, not markdown. Use `<strong>bold</strong>` and `<em>italic</em>`.

**JSON editing:** Use the helper script:
```bash
python3 add-entry.py '{"year": 1610, "id": "1610-...", ...}'           # EN
python3 add-entry.py '{"year": 1610, "id": "1610-...", ...}' --lang it  # IT
```

---

## PHASE 1: Research & Content (Steps 1-10)

1. **Read the spec:** `/home/cloud-user/.openclaw/workspace/time-slices/SPEC.md`

2. **Check existing entries:** Read `slices.json` and `slices.it.json`. Note years covered.

3. **Pick a year** with genuine depth in ALL 5 dimensions. If any feels thin, pick different year.

4. **Movement labels are MANDATORY.** Each dimension MUST name its cultural/intellectual movement.

5. **Connections must be GROUNDED.** Real documented influence, not poetic parallels.

6. **Thread rules:**
   - Prioritize connecting to EXISTING threads (check `slices.json`)
   - Don't create near-synonyms of existing threads
   - Good: `death-of-god`, `rationalism`, `classical-revival`
   - Bad: `biography`, `famous-people`, `wars`

7. **Add ONE new entry** with city in title only if dimensions converge there. Include `location` and `addedDate`.

8. **Add Italian version** — natural Italian, not machine translation.

9. **Update THREAD_LABELS** in `index.html` if you add new thread tags (both en + it).

10. **Add THREAD_NARRATIVES** in `index.html`:
    - Format: `'YEAR_FROM→YEAR_TO': 'Narrative'`
    - Keep punchy: 1-2 sentences. State the mechanism of transmission.
    - Add for BOTH `en` and `it` sections

---

## PHASE 2: Podcasts (Steps 11-13) — MANDATORY

⚠️ **DO NOT SKIP THIS PHASE. Previous runs have failed by stopping after Phase 1.**

11. **Write podcast scripts:**
    - EN: `audio/scripts/{id}.txt` (~350-400 words, storytelling)
    - IT: `audio/scripts/it/{id}.txt` (culturally adapted)

12. **Add config to `audio/generate-podcast.py`:**
    - Add entry to `VOICE_MAP_EN` dict with voice + instructions
    - Add entry to `VOICE_MAP_IT` dict with voice + Italian instructions
    - Add entry to `MUSIC_SOURCES` dict (use pool_key or direct URL)
    - Voices: alloy, ash, ballad, coral, echo, fable, nova, sage, shimmer, verse (NOT onyx)

13. **Generate podcasts:**
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

## PHASE 3: Publish (Steps 14-15) — MANDATORY

⚠️ **DO NOT SKIP THIS PHASE. The entry is NOT LIVE until pushed.**

14. **Commit and push:**
    ```bash
    cd /home/cloud-user/.openclaw/workspace/time-slices
    git add -A
    git commit -m "Add YEAR Place: Title"
    git push "$(cat .git-push-url)" main
    ```
    
    **VERIFY PUSH SUCCEEDED.** Look for `main -> main` in output. If you see `rejected` or `error`, fix it.

15. **Final reply** (ONLY after steps 13-14 verified):
    - Year, title, teaser
    - One highlight connection (3-5 sentences)
    - Direct link: `https://matteobettini.github.io/time_slices/#ID`

---

## 🔒 COMPLETION GATE

Before sending your final reply, run this verification:

```bash
cd /home/cloud-user/.openclaw/workspace/time-slices
echo "=== VERIFICATION ===" && \
ls -la audio/{id}.mp3 && \
ls -la audio/it/{id}.mp3 && \
git log --oneline -1 && \
git status
```

✅ Expected output:
- Two MP3 files >100KB each
- Recent commit with your entry
- Clean git status (nothing to commit, working tree clean)

❌ If ANY of these fail: GO BACK and complete the missing step. Do NOT reply.

---

## Music Reference

Search: `https://archive.org/advancedsearch.php?q=<query>+AND+mediatype:audio&output=json`

**By era:**
- Ancient/Medieval: `gregorian chant`, `medieval music`
- Middle East: `oud music`, `persian classical`
- Renaissance: `renaissance lute`, `harpsichord`
- Baroque: `bach`, `vivaldi`, `handel`
- Classical: `mozart`, `beethoven`
- Romantic: `chopin`, `liszt`
- Impressionist: `debussy`, `ravel`, `satie`
