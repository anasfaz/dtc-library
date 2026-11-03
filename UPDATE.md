# DTC Component Library – how to update

Layout
- `site/` – the static website (index.html, style.css, app.js, data.json, img/<brand-slug>/<component>-<device>.jpg). This folder is what gets published.
- `data/brands.json` – one entry per brand: name, url, country, region (`India` | `International`), category, agency (`Unknown` unless verified from the agency's own case study/portfolio), agency_source (URL), platform, added (YYYY-MM-DD, IST), why (notes), optional tags.
- `data/component_types.json` – component vocabulary (label, search tags, default "why it converts" note).
- `data/notes.json` – optional brand-specific note per component: `{ "<slug>": { "<component>": "note" } }`.
- `scripts/capture.py` – Playwright capture (desktop 1440×900 + iPhone 13).
- `scripts/build.py` – scans `site/img/*/*.jpg` + data files → `site/data.json`.
- `scripts/deploy.sh` – build + git commit + push (host auto-deploys).

## Add a brand (daily run)
1. Pick brand; verify agency only from the agency's case study / portfolio page (put URL in `agency_source`). Otherwise `"agency": "Unknown"`.
2. Add it to `data/brands.json` with `"added": "<today IST>"` (items <8 days old show in "New this week").
3. Capture: `cd /workspace/dtc-library && python3 scripts/capture.py <slug> <home_url> [pdp_url]`
   Produces hero, header, product-card, footer, pdp, pdp-details, reviews (desktop+mobile) and sticky-atc (mobile).
   Pass a pdp_url when the homepage has no `/products/` links (headless sites, e.g. Snitch).
4. Check the shots (popups / blank captures): delete bad files from `site/img/<slug>/`.
5. Extra components (bundle builder, quiz, mega menu, cart drawer…): save manually as `site/img/<slug>/<component>-<desktop|mobile|combined>.jpg` using a key from `component_types.json` (add a new key there if needed), and add a specific note in `data/notes.json`.
6. `python3 scripts/build.py` → preview: `cd site && python3 -m http.server 8765`.
7. Deploy: `scripts/deploy.sh` (push to `main`; Render static site / GitHub Pages redeploys automatically).

## Hosting (live)
- Live URL: https://dtc-library.onrender.com
- Repo: https://github.com/anasfaz/dtc-library (public, branch `main`), pushed with `gh` logged in as anasfaz on the box.
- Render static site `dtc-library` (srv-dbl3jp0u01pc739kb390, workspace "My Workspace"), publish dir `site`, auto-deploys on every push to `main`. Deploys usually take about 1–2 minutes.
- Daily: `scripts/deploy.sh` runs the build, commits and pushes, and Render redeploys. Check with `curl -s https://dtc-library.onrender.com/data.json | head -c 200` (the `built` field should show the new time).
