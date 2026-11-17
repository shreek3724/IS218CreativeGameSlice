# CODEX-SPEC.md — Art Conservation Puzzle Game (Review 2 First Slice)

## 1. Operating Rules & Scope Guardrails

* **Stack:** Python OOP backend (Flask, Flask-Login, Werkzeug, Flask-WTF CSRF), SQLite in root `.gitignored` `instance/`, vanilla HTML5/CSS3/ES6/Canvas 2D, and ESLint for frontend development.
* **Strict scope:** sign up/in/out, Home, Untimed Restoration, Results, server-verified save, Strategy versus conditional comparison, and `app/services.py` stubs. Do **not** build a dashboard/account UI, active timed multipliers, Docker, or a static GitHub Pages clone.
* **Before each step:** read only relevant files, propose the smallest OOP/SOLID design and needed strategy functions, discuss it, and wait for approval before code.
* **After each step:** run Ruff and focused checks; do not mark it complete with lint, spelling, or test errors.

## 2. Architecture Contracts & Fixed Defaults

### Modules

* `app/__init__.py`: Flask application factory and configuration.
* `app/db.py`: SQLite connection, schema initialization, and database lifecycle only.
* `app/rules.py`: pure domain models (`CellState`, `PaintingGrid`), `LAYER_STRATEGIES`, conditional comparison, and 60/40 scoring; no Flask/HTML imports.
* `app/services.py`: Review 3 stubs: `AccountSyncService`, `DashboardQueryService`.
* `app/templates/` and `app/static/`: accessible Flask templates, CSS, and vanilla Canvas JavaScript.
* `tests/test_app.py`: concise user-story tests.

### Gameplay

* A 4 × 4 grid has three removable layers: Layer 2 Surface Dirt → Layer 1 Overpaint → Layer 0 Aged Varnish.
* Each layer uses all three clues: chemical ratio, tool selection, and safe-zone/order.
* Chemicals: `water_ratio`, `oil_ratio`, `acid_ratio`; tools: `swab`, `brush`, `heat_lamp`.
* Surface Dirt: 70/30/0 with swab on low-risk cells; Overpaint: 20/70/10 with brush on central cells after dirt; Aged Varnish: 10/20/70 with heat lamp on border cells last.
* Valid moves lower dirt; wrong solvent, tool, zone, or order lowers integrity. Score = 60% integrity + 40% clue deduction. Timed Mode is visible but disabled as “Coming in Review 3.”

### Persistence

`DATABASE_PATH` and `SECRET_KEY` come from config/environment. `instance/art_conservator.db` contains:

* `user_accounts`: `user_id` PK, unique `username`, `display_name`, `password_hash`, `total_paintings_restored` default 0, `unlocked_artworks`, `unlocked_tools`, `created_at`.
* `login_sessions`: `session_id` PK, `user_id` FK, `session_token`, `is_active`, `created_at`.
* `restoration_matches`: `match_id` PK, `user_id` FK, `artwork_id`, `mode`, integrity/clue/final scores, layers restored, elapsed time, Base64 PNG, `created_at`.

### OOP, SOLID, and pattern choice

* `CellState` models a cell and `PaintingGrid` owns grid progression (**SRP**).
* Layer strategy functions encapsulate layer behavior (**Strategy**, **OCP**); `evaluate_move_conditional` remains the simpler comparison.
* Database code is isolated in `app/db.py`; routes depend on narrow functions rather than schema details (**SRP**, **DIP**).

## 3. Build Plan (one approved step at a time)

### Step 0 — Environment Check

Confirm Python tooling, linter, tests, and Chrome option; confirm grid/rules/timed-toggle defaults.

### Step 1 — Flask Skeleton & SQLite Database

Create `app/`, `app/templates/`, `app/static/`, `.gitignored` root `instance/`, configuration, and all three schema tables.

### Step 2 — Server-Side Auth, CSRF & Revocable Sessions

Build signup/login/logout with Flask-Login, Werkzeug password hashing, Flask-WTF CSRF, and revocable `login_sessions`; enforce ownership and protected routes.

### Step 3 — Pure OOP Rules & Strategy Pattern

Implement domain models, three layer strategies, conditional parity function, and server-side 60/40 scoring.

### Step 4 — Screens & Accessible Canvas UI

After receiving mockups, build Home, Play, and Results with keyboard-accessible controls, Canvas, integrity meter, clues, kit/tools, mixing controls, disabled Timed Mode, and PNG export.

### Step 5 — Server-Verified Save & Review 3 Stubs

Implement CSRF-protected `POST /api/restorations`, replay moves server-side, save idempotently in a transaction, and add service stubs.

### Step 6 — Minimum Tests, CI & Records

Add concise unit/integration tests and one Chrome smoke test when available; add CI, `TEST-NOTES.md`, `PROJECT-RECORD.md`, and final OOP/SOLID class documentation.
