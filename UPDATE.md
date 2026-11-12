# DTC Component Library – how to update

Layout
- `site/` – the static website (index.html, style.css, app.js, data.json, img/<brand-slug>/<component>-<device>.jpg). This folder is what gets published.
- `data/brands.json` – one entry per brand: name, url, country, region (`India` | `International`), category, agency (`Unknown` unless verified from the agency's own case study/portfolio), agency_source (URL), platform, added (YYYY-MM-DD, IST), why (notes), optional tags.
- `data/component_types.json` – component vocabulary (label, search tags, default "why it converts" note).
- `data/notes.json` – optional brand-specific note per component: `{ "<slug>": { "<component>": "note" } }`.
- `scripts/capture.py` – Playwright capture of one brand, every component separately (desktop 1440×900 + iPhone 13).
- `scripts/build.py` – scans `site/img/*/*.jpg` + data files → `site/data.json`.
- `scripts/deploy.sh` – build + git commit + push (host auto-deploys).

## Daily rule: ONE website per day, every component separately
One brand per day is enough. Capture that brand completely — every component as its own labelled screenshot (desktop + mobile) — instead of thin partial captures of several brands. Then build + deploy.

1. Pick the brand; verify agency only from the agency's case study / portfolio page (URL in `agency_source`), otherwise `"agency": "Unknown"`.
2. Add it to `data/brands.json` with `"added": "<today IST>"` (shows a NEW badge for 8 days).
3. Capture everything in one run:
   `cd /workspace/dtc-library && python3 scripts/capture.py <slug> <home_url> [pdp_url] [--collection URL] [--query WORD] [--checkout]`
   - Menu tab: `announcement-bar` and `header` as two separate clips; `mega-menu` (desktop nav item hovered/clicked open); `mobile-nav` (burger opened on iPhone 13).
   - Search tab: `search` (opened, empty) and `search-results` (typed query; falls back to `/search?q=`).
   - Home tab: `hero`, `category-tiles`, `footer` (+ `comparison` / `bundle-builder` / `quiz` found by heading text).
   - Collection tab: `collection` (full PLP page) and `product-card` (clipped grid, separate from the page).
   - Product tab: `pdp`, `pdp-details`, `variant-selector`, `subscribe-save`, `delivery-check`, `sticky-atc` (mobile, only if a sticky bar exists), `reviews`, `cross-sell`.
   - Cart tab: `cart-drawer` (after add to cart), `free-gift` (if visible), `cart-page` (`/cart`).
   - Checkout tab: `checkout` only with `--checkout`, and only if the first checkout step opens without sign-in. Nothing is typed, nothing is paid; otherwise it is skipped quietly.
   - `--only header,mobile-nav` re-shoots just some components; `--device mobile` runs one device. `pdp_url` is needed for headless sites with no `/products/` links.
   The script only saves what it actually detects and skips blank shots. Missing components stay missing — never fake them.
4. Check every shot in `site/img/<slug>/` (popups, wrong element, blank). Delete bad files. Extra components can be saved by hand as `site/img/<slug>/<component>-<desktop|mobile|combined>.jpg` using a key from `data/component_types.json`; add a brand-specific note in `data/notes.json`.
5. `python3 scripts/build.py` → preview: `cd site && python3 -m http.server 8765` → open http://localhost:8765/#/brand/<slug>.
6. Deploy: `scripts/deploy.sh`, then trigger the Render deploy (see Hosting).

## Component types and site routes
- Types live in `data/component_types.json`: `label` (full), `short` (card label), `group` (tab), `order` (page-flow order on brand pages), `tags`, `note`.
  New in Nov 2026: `announcement-bar`, `mobile-nav`, `search`, `search-results`, `collection`, `cart-page`, `checkout`. Old keys stay valid (`header` captures before Nov 2026 include the announcement bar; `mega-menu` is the desktop dropdown).
- Tabs (one per page type): `#/` Home · `#/collection` · `#/product` · `#/search` · `#/menu` · `#/cart` · `#/checkout`, plus `#/all` and `#/saved` (bookmarks, stored in the browser).
  Type filter inside a tab: `#/<tab>/<component>`, e.g. `#/menu/mobile-nav`, `#/product/sticky-atc`.
- Brand page: `#/brand/<slug>` (every component, page-flow order). Component lightbox: `#/brand/<slug>/<component>` (notes, Copy notes, downloads).
- `#/brands`, `#/agencies`. Search box searches everything (brand, component, tags, agency, notes) and opens `#/all`.
- Filters: Desktop/Mobile, All/India/International, agency, industry (derived from category in build.py), sort Latest / Brand A–Z.
- `scripts/shoot_redesign.py` takes preview screenshots of the local site into `screens/`.

## Hosting (live)
- Live URL: https://dtc-library.onrender.com
- Repo: https://github.com/anasfaz/dtc-library (public, branch `main`), pushed with `gh` logged in as anasfaz on the box.
- Render static site `dtc-library` (srv-dbl3jp0u01pc739kb390, workspace "My Workspace"), publish dir `site`, is set to auto-deploy on push, BUT pushes did not trigger a deploy in testing (the Render GitHub app isn't linked to the repo). Always trigger the deploy explicitly: Render connector `trigger_deploy` with serviceId `srv-dbl3jp0u01pc739kb390` and workspaceId `tea-da27r837uimc739pqseg`, or export `RENDER_DEPLOY_HOOK=<Deploy Hook URL from Render dashboard → Settings>` and deploy.sh will call it. A deploy takes about 1 minute.
- Daily: run `scripts/deploy.sh` (build, commit, push), then trigger the deploy as above. Check with `curl -s https://dtc-library.onrender.com/data.json | head -c 200` (the `built` field should show the new time).

## Agencies
- `data/agencies.json`: name, url, focus (as seen on the agency's own site), clients (brand slugs). Shown at `#/agencies`.
- Add a client only with proof from the agency's own portfolio, case study or testimonial page; put that URL in the brand's `agency_source`.
