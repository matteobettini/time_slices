#!/usr/bin/env python3
"""
Time Slices completion verifier.

Run after the cron agent finishes to verify the entry is actually live.
If verification fails, outputs what's missing and a detailed resume prompt.

Usage:
    python3 verify-completion.py [--date YYYY-MM-DD] [--json]
    
Checks:
1. A new entry was added today (by addedDate)
2. Both MP3 files exist for that entry  
3. Entry is committed and pushed (exists on GitHub)

Exit codes:
    0 = complete
    1 = incomplete (outputs what's missing + resume instructions)
"""

import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent  # scripts/ -> project root
SLICES_JSON = PROJECT_DIR / "slices.json"
SLICES_IT_JSON = PROJECT_DIR / "slices.it.json"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/matteobettini/time_slices/main/slices.json"


def get_today_entry(target_date: str = None):
    """Find entry added today (or on target_date)."""
    if target_date is None:
        target_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    with open(SLICES_JSON) as f:
        entries = json.load(f)
    
    for entry in entries:
        added = entry.get("addedDate", "")
        if added.startswith(target_date):
            return entry
    return None


def check_local_files(entry_id: str) -> dict:
    """Check if local files exist and return detailed status."""
    status = {
        "en_mp3": False,
        "it_mp3": False,
        "en_script": False,
        "it_script": False,
        "image": False,
    }
    issues = []
    
    # Check MP3s
    en_mp3 = PROJECT_DIR / "audio" / f"{entry_id}.mp3"
    it_mp3 = PROJECT_DIR / "audio" / "it" / f"{entry_id}.mp3"
    
    if en_mp3.exists() and en_mp3.stat().st_size >= 100000:
        status["en_mp3"] = True
    elif en_mp3.exists():
        issues.append(f"EN podcast too small (<100KB): audio/{entry_id}.mp3")
    else:
        issues.append(f"Missing EN podcast: audio/{entry_id}.mp3")
        
    if it_mp3.exists() and it_mp3.stat().st_size >= 100000:
        status["it_mp3"] = True
    elif it_mp3.exists():
        issues.append(f"IT podcast too small (<100KB): audio/it/{entry_id}.mp3")
    else:
        issues.append(f"Missing IT podcast: audio/it/{entry_id}.mp3")
    
    # Check scripts
    en_script = PROJECT_DIR / "audio" / "scripts" / f"{entry_id}.txt"
    it_script = PROJECT_DIR / "audio" / "scripts" / "it" / f"{entry_id}.txt"
    
    if en_script.exists():
        status["en_script"] = True
    else:
        issues.append(f"Missing EN script: audio/scripts/{entry_id}.txt")
        
    if it_script.exists():
        status["it_script"] = True
    else:
        issues.append(f"Missing IT script: audio/scripts/it/{entry_id}.txt")
    
    # Check image
    year_prefix = entry_id.split('-')[0]
    images = list((PROJECT_DIR / "images").glob(f"{year_prefix}*"))
    if images:
        status["image"] = True
    else:
        issues.append(f"Missing image for {entry_id}")
    
    return {"status": status, "issues": issues}


def check_italian_entry(entry_id: str) -> dict:
    """Check if Italian translation exists."""
    issues = []
    
    with open(SLICES_IT_JSON) as f:
        it_entries = json.load(f)
    
    it_ids = {e.get("id") for e in it_entries}
    if entry_id not in it_ids:
        issues.append(f"Missing Italian entry in slices.it.json for {entry_id}")
    
    return {"ok": len(issues) == 0, "issues": issues}


def check_git_status() -> dict:
    """Check if there are uncommitted changes."""
    issues = []
    uncommitted = []
    
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True
    )
    
    if result.stdout.strip():
        uncommitted = result.stdout.strip().split('\n')
        issues.append(f"Uncommitted changes: {len(uncommitted)} files")
    
    return {"ok": len(issues) == 0, "issues": issues, "uncommitted": uncommitted}


def check_pushed(entry_id: str) -> dict:
    """Check if entry exists on GitHub (i.e., was pushed)."""
    issues = []
    
    try:
        req = urllib.request.Request(GITHUB_RAW_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            remote_entries = json.loads(resp.read().decode())
        
        remote_ids = {e.get("id") for e in remote_entries}
        if entry_id not in remote_ids:
            issues.append(f"Entry not on GitHub - push failed or pending")
    except Exception as e:
        issues.append(f"Could not verify GitHub: {e}")
    
    return {"ok": len(issues) == 0, "issues": issues}


def check_thread_narratives(entry_id: str) -> dict:
    """Check if all consecutive thread pairs have narratives in index.html."""
    issues = []
    
    # Load all entries to build thread->years map
    with open(SLICES_JSON) as f:
        entries = json.load(f)
    
    thread_years = {}
    for e in entries:
        for t in e.get('threads', []):
            if t not in thread_years:
                thread_years[t] = []
            thread_years[t].append(int(e['year']))
    
    # Sort years for each thread
    for t in thread_years:
        thread_years[t] = sorted(thread_years[t])
    
    # Read index.html to check for narratives and duplicates
    index_path = PROJECT_DIR / "index.html"
    if not index_path.exists():
        return {"ok": True, "issues": [], "missing": []}
    
    content = index_path.read_text()
    
    # Check for duplicate thread keys in THREAD_NARRATIVES
    import re
    # Find all thread keys in the narratives object
    thread_key_pattern = r"'([a-z-]+)':\s*\{"
    matches = re.findall(thread_key_pattern, content)
    
    # Count occurrences (each thread should appear exactly twice: once in en, once in it)
    from collections import Counter
    thread_counts = Counter(matches)
    for thread, count in thread_counts.items():
        # Filter to only threads that are in THREAD_NARRATIVES (not THREAD_LABELS)
        # A thread in narratives will have year→year patterns inside
        if count > 2:
            # Verify it's actually in narratives by checking for arrow pattern nearby
            pattern = rf"'{thread}':\s*\{{[^}}]*'\d+→\d+'"
            if re.search(pattern, content):
                issues.append(f"Duplicate thread '{thread}' in THREAD_NARRATIVES ({count} occurrences, expected 2)")
    
    # Check consecutive pairs for threads with 2+ entries
    missing = []
    for t, years in thread_years.items():
        if len(years) < 2:
            continue
        for i in range(len(years) - 1):
            key = f"{years[i]}→{years[i+1]}"
            if key not in content:
                missing.append(f"{t}: {key}")
    
    if missing:
        issues.append(f"Missing thread narratives: {', '.join(missing)}")
    
    return {"ok": len(issues) == 0, "issues": issues, "missing": missing}


def generate_resume_prompt(entry_id: str, entry_year: str, entry_title: str, 
                           file_status: dict, issues: list) -> str:
    """Generate a detailed prompt for resuming incomplete work."""
    
    lines = [
        f"## Resume Time Slice: {entry_year} — {entry_title}",
        f"Entry ID: `{entry_id}`",
        "",
        "The entry was partially created. Complete the missing steps:",
        ""
    ]
    
    fs = file_status
    
    # Scripts
    if not fs.get("en_script") or not fs.get("it_script"):
        lines.append("### Write Podcast Scripts")
        if not fs.get("en_script"):
            lines.append(f"- [ ] Write EN script → `audio/scripts/{entry_id}.txt` (~350-400 words)")
        if not fs.get("it_script"):
            lines.append(f"- [ ] Write IT script → `audio/scripts/it/{entry_id}.txt`")
        lines.append("")
    
    # Podcasts — use CLI args, no config files needed
    if not fs.get("en_mp3") or not fs.get("it_mp3"):
        lines.append("### Generate Podcasts")
        lines.append("Use `scripts/find-music.py` to find appropriate background music, then generate:")
        lines.append("```bash")
        lines.append("cd /home/cloud-user/.openclaw/workspace/time-slices")
        if not fs.get("en_mp3"):
            lines.append(f'python3 scripts/generate-podcast.py {entry_id} --lang en --voice en-GB-RyanNeural --music-url "<URL>" --music-start <SECONDS>')
        if not fs.get("it_mp3"):
            lines.append(f'python3 scripts/generate-podcast.py {entry_id} --lang it --voice it-IT-DiegoNeural --music-url "<URL>" --music-start <SECONDS>')
        lines.append("```")
        lines.append("")
    
    # Always need to commit and push if there are issues
    lines.append("### Commit and Push")
    lines.append("```bash")
    lines.append("cd /home/cloud-user/.openclaw/workspace/time-slices")
    lines.append("git add -A")
    lines.append(f'git commit -m "Complete {entry_year} {entry_title.split("—")[0].strip()}: podcasts"')
    lines.append('git push "$(cat .git-push-url)" main')
    lines.append("```")
    lines.append("")
    
    lines.append("### Verify Completion")
    lines.append("```bash")
    lines.append("python3 scripts/verify-completion.py")
    lines.append("```")
    lines.append("")
    lines.append("Only reply when verifier shows ✅ COMPLETE.")
    
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Check for entry added on this date (YYYY-MM-DD)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    target_date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Find today's entry
    entry = get_today_entry(target_date)
    
    if not entry:
        result = {
            "complete": False,
            "entry_id": None,
            "target_date": target_date,
            "issues": ["No entry found for target date - content not created"],
            "resume_action": "Create new entry from scratch",
            "resume_prompt": f"No entry exists for {target_date}. Follow /home/cloud-user/.openclaw/workspace/time-slices/GENERATE_PROMPT.md to create a new entry."
        }
    else:
        entry_id = entry["id"]
        entry_year = entry.get("year")
        entry_title = entry.get("title")
        all_issues = []
        
        # Check local files
        local = check_local_files(entry_id)
        all_issues.extend(local["issues"])
        file_status = local["status"]
        
        # Check Italian entry
        italian = check_italian_entry(entry_id)
        all_issues.extend(italian["issues"])
        
        # Check git status
        git = check_git_status()
        all_issues.extend(git["issues"])
        
        # Check pushed
        pushed = check_pushed(entry_id)
        all_issues.extend(pushed["issues"])
        
        # Check thread narratives
        narratives = check_thread_narratives(entry_id)
        all_issues.extend(narratives["issues"])
        
        # Determine resume action (high-level)
        if all_issues:
            if any("script" in i.lower() for i in all_issues):
                resume_action = "Write scripts, generate podcasts, commit and push"
            elif any("podcast" in i.lower() or "mp3" in i.lower() for i in all_issues):
                resume_action = "Generate podcasts, commit and push"
            elif any("uncommitted" in i.lower() for i in all_issues):
                resume_action = "Commit and push"
            elif any("github" in i.lower() or "push" in i.lower() for i in all_issues):
                resume_action = "Push to GitHub"
            else:
                resume_action = "Review and fix issues"
            
            resume_prompt = generate_resume_prompt(
                entry_id, entry_year, entry_title, file_status, all_issues
            )
        else:
            resume_action = None
            resume_prompt = None
        
        result = {
            "complete": len(all_issues) == 0,
            "entry_id": entry_id,
            "entry_year": entry_year,
            "entry_title": entry_title,
            "target_date": target_date,
            "file_status": file_status,
            "issues": all_issues,
            "resume_action": resume_action,
            "resume_prompt": resume_prompt
        }
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["complete"]:
            print(f"✅ COMPLETE: {result.get('entry_year')} — {result.get('entry_title')}")
            print(f"   Entry ID: {result['entry_id']}")
        else:
            print(f"❌ INCOMPLETE")
            if result.get("entry_id"):
                print(f"   Entry: {result.get('entry_year')} — {result.get('entry_title')} ({result['entry_id']})")
            else:
                print(f"   Target date: {result['target_date']}")
            print(f"\n   Issues:")
            for issue in result["issues"]:
                print(f"   - {issue}")
            print(f"\n   Resume action: {result['resume_action']}")
            print(f"\n{'='*60}")
            print("RESUME PROMPT:")
            print('='*60)
            print(result.get("resume_prompt", ""))
    
    sys.exit(0 if result["complete"] else 1)


if __name__ == "__main__":
    main()
