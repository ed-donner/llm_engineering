#!/usr/bin/env python3
"""
Fetch OWASP CheatSheetSeries cheatsheets and sync them into the kb_articles folder.
"""

import os
import shutil
import subprocess
import hashlib
import json
from pathlib import Path

KB_DIR = "kb_articles"
STATE_FILE = "kb_state.json"   # stores hash of each file
REPO_URL = "https://github.com/OWASP/CheatSheetSeries.git"
CHEATSHEETS_SUBDIR = "cheatsheets"
TEMP_CLONE_DIR = "/tmp/owasp_cheatsheets_temp"  # can be any location

def get_file_hash(filepath):
    """Return SHA256 hash of file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

def load_state():
    """Load the saved file hashes."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    """Save the current file hashes."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def update_knowledge_base():
    """
    Clone/pull the OWASP repo and copy cheatsheets into KB_DIR.
    Returns a list of new/updated files.
    """
    # Ensure KB_DIR exists
    os.makedirs(KB_DIR, exist_ok=True)

    # Clone or update the repo
    if not os.path.exists(TEMP_CLONE_DIR):
        print("Cloning OWASP CheatSheetSeries repository...")
        subprocess.run(["git", "clone", "--depth", "1", REPO_URL, TEMP_CLONE_DIR], check=True)
    else:
        print("Updating existing repository...")
        subprocess.run(["git", "-C", TEMP_CLONE_DIR, "pull"], check=True)

    # Path to the cheatsheets directory
    source_dir = os.path.join(TEMP_CLONE_DIR, CHEATSHEETS_SUBDIR)
    if not os.path.isdir(source_dir):
        raise FileNotFoundError(f"Cheatsheets directory not found in {TEMP_CLONE_DIR}")

    # Load previous state
    state = load_state()
    updated_files = []

    # Iterate over .md files in the source
    for filename in os.listdir(source_dir):
        if not filename.endswith(".md"):
            continue
        src_path = os.path.join(source_dir, filename)
        dst_path = os.path.join(KB_DIR, filename)

        # Compute hash of the source file
        new_hash = get_file_hash(src_path)

        # If the file is new or has changed, copy it
        if filename not in state or state[filename] != new_hash:
            print(f"Updating {filename}")
            shutil.copy2(src_path, dst_path)
            state[filename] = new_hash
            updated_files.append(filename)

    # Save updated state
    save_state(state)

    # Clean up temp directory if desired (optional)
    # shutil.rmtree(TEMP_CLONE_DIR, ignore_errors=True)

    return updated_files

if __name__ == "__main__":
    update_knowledge_base()