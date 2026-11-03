#!/usr/bin/env bash
# Rebuild data.json and push to the GitHub repo that Render / GitHub Pages serves (auto-deploys on push).
set -e; cd "$(dirname "$0")/.."
python3 scripts/build.py
git add -A && git commit -qm "Library update $(TZ=Asia/Kolkata date +%F)" || echo "nothing to commit"
git push origin main
