#!/usr/bin/env python3
"""
Time Slices completion verifier.

Run after the cron agent finishes to verify the entry is actually live.
If verification fails, outputs what's missing so the agent can be respawned.

Usage:
    python3 verify-completion.py [--date YYYY-MM-DD]
    
Checks:
1. A new entry was added today (by addedDate)
2. Both MP3 files exist for that entry
3. Entry is committed and pushed (exists on GitHub)

Exit codes:
    0 = complete
    1 = incomplete (outputs what's missing)
"""

import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SLICES_JSON = SCRIPT_DIR / "slices.json"
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
    """Check if local files exist."""
    issues = []
    
    # Check MP3s
    en_mp3 = SCRIPT_DIR / "audio" / f"{entry_id}.mp3"
    it_mp3 = SCRIPT_DIR / "audio" / "it" / f"{entry_id}.mp3"
    
    if not en_mp3.exists():
        issues.append(f"Missing EN podcast: audio/{entry_id}.mp3")
    elif en_mp3.stat().st_size < 100000:
        issues.append(f"EN podcast too small (<100KB): audio/{entry_id}.mp3")
        
    if not it_mp3.exists():
        issues.append(f"Missing IT podcast: audio/it/{entry_id}.mp3")
    elif it_mp3.stat().st_size < 100000:
        issues.append(f"IT podcast too small (<100KB): audio/it/{entry_id}.mp3")
    
    # Check scripts
    en_script = SCRIPT_DIR / "audio" / "scripts" / f"{entry_id}.txt"
    it_script = SCRIPT_DIR / "audio" / "scripts" / "it" / f"{entry_id}.txt"
    
    if not en_script.exists():
        issues.append(f"Missing EN script: audio/scripts/{entry_id}.txt")
    if not it_script.exists():
        issues.append(f"Missing IT script: audio/scripts/it/{entry_id}.txt")
    
    # Check image
    for ext in [".jpg", ".png", ".webp"]:
        img_path = SCRIPT_DIR / "images" / f"{entry_id.split('-')[0]}*"
        # Use glob to find image
        images = list((SCRIPT_DIR / "images").glob(f"{entry_id.split('-')[0]}*"))
        if images:
            break
    else:
        issues.append(f"Missing image for {entry_id}")
    
    return {"ok": len(issues) == 0, "issues": issues}


def check_git_status() -> dict:
    """Check if there are uncommitted changes."""
    issues = []
    
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=SCRIPT_DIR,
        capture_output=True,
        text=True
    )
    
    if result.stdout.strip():
        issues.append(f"Uncommitted changes:\n{result.stdout.strip()}")
    
    return {"ok": len(issues) == 0, "issues": issues}


def check_pushed(entry_id: str) -> dict:
    """Check if entry exists on GitHub (i.e., was pushed)."""
    issues = []
    
    try:
        req = urllib.request.Request(GITHUB_RAW_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            remote_entries = json.loads(resp.read().decode())
        
        remote_ids = {e.get("id") for e in remote_entries}
        if entry_id not in remote_ids:
            issues.append(f"Entry {entry_id} not found on GitHub - push may have failed")
    except Exception as e:
        issues.append(f"Could not verify GitHub: {e}")
    
    return {"ok": len(issues) == 0, "issues": issues}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Check for entry added on this date (YYYY-MM-DD)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    # Find today's entry
    entry = get_today_entry(args.date)
    
    if not entry:
        result = {
            "complete": False,
            "entry_id": None,
            "issues": ["No entry found for today - content not created"],
            "resume_action": "Create new entry from scratch"
        }
    else:
        entry_id = entry["id"]
        all_issues = []
        
        # Check local files
        local = check_local_files(entry_id)
        all_issues.extend(local["issues"])
        
        # Check git status
        git = check_git_status()
        all_issues.extend(git["issues"])
        
        # Check pushed
        pushed = check_pushed(entry_id)
        all_issues.extend(pushed["issues"])
        
        # Determine resume action
        if all_issues:
            if any("podcast" in i.lower() or "script" in i.lower() for i in all_issues):
                resume_action = "Generate podcasts and push"
            elif any("uncommitted" in i.lower() for i in all_issues):
                resume_action = "Commit and push"
            elif any("github" in i.lower() or "push" in i.lower() for i in all_issues):
                resume_action = "Push to GitHub"
            else:
                resume_action = "Review and fix issues"
        else:
            resume_action = None
        
        result = {
            "complete": len(all_issues) == 0,
            "entry_id": entry_id,
            "entry_year": entry.get("year"),
            "entry_title": entry.get("title"),
            "issues": all_issues,
            "resume_action": resume_action
        }
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["complete"]:
            print(f"✅ COMPLETE: {result.get('entry_year')} — {result.get('entry_title')}")
            print(f"   Entry ID: {result['entry_id']}")
        else:
            print(f"❌ INCOMPLETE")
            if result["entry_id"]:
                print(f"   Entry: {result.get('entry_year')} — {result.get('entry_title')} ({result['entry_id']})")
            print(f"\n   Issues:")
            for issue in result["issues"]:
                print(f"   - {issue}")
            print(f"\n   Resume action: {result['resume_action']}")
    
    sys.exit(0 if result["complete"] else 1)


if __name__ == "__main__":
    main()
