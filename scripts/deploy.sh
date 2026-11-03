#!/usr/bin/env bash
# Rebuild data.json and push to the GitHub repo that Render / GitHub Pages serves (auto-deploys on push).
set -e; cd "$(dirname "$0")/.."
python3 scripts/build.py
git -c user.name="Grok Bot" -c user.email="bot@dtc-library" add -A && git -c user.name="Grok Bot" -c user.email="bot@dtc-library" commit -qm "Library update $(TZ=Asia/Kolkata date +%F)" || echo "nothing to commit"
gh auth setup-git >/dev/null 2>&1 || true
git push origin main
echo "Pushed. Render auto-deploys to https://dtc-library.onrender.com (~1-2 min)."
