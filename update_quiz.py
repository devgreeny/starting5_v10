#!/usr/bin/env python3
import os
import random
import shutil
import sys

# ─── CONFIGURATION ─────────────────────────────────────────────────────────────
# Change these if your folder layout differs
PROJECT_ROOT   = os.path.abspath(os.path.dirname(__file__))  # /home/devgreeny/starting5_v3
PRELOADED_DIR  = os.path.join(PROJECT_ROOT, "app", "static", "preloaded_quizzes")
CURRENT_DIR    = os.path.join(PROJECT_ROOT, "app", "static", "current_quiz")
# ────────────────────────────────────────────────────────────────────────────────

def main():
    # 1) Ensure the current_quiz folder exists
    os.makedirs(CURRENT_DIR, exist_ok=True)

    # 2) Remove any existing file in CURRENT_DIR
    existing = [f for f in os.listdir(CURRENT_DIR) if f.lower().endswith(".json")]
    for old_file in existing:
        old_path = os.path.join(CURRENT_DIR, old_file)
        try:
            os.remove(old_path)
            print(f"🗑️ Removed old quiz: {old_file}")
        except Exception as e:
            print(f"⚠️ Could not remove '{old_file}': {e}", file=sys.stderr)

    # 3) List all remaining quizzes in PRELOADED_DIR
    all_quizzes = [f for f in os.listdir(PRELOADED_DIR) if f.lower().endswith(".json")]
    if not all_quizzes:
        print("❌ No quizzes found in preloaded_quizzes. Nothing to do.", file=sys.stderr)
        sys.exit(1)

    # 4) Pick one at random
    chosen = random.choice(all_quizzes)
    src_path = os.path.join(PRELOADED_DIR, chosen)
    dest_path = os.path.join(CURRENT_DIR, chosen)

    # 5) Move it (cut & paste)
    try:
        shutil.move(src_path, dest_path)
        print(f"✅ Moved '{chosen}' → current_quiz")
    except Exception as e:
        print(f"❌ Failed to move '{chosen}': {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
