# CODEX-SPEC.md — Art Conservation Puzzle Game (Static First Slice)

## 1. Scope and Working Agreement

* **Stack (no external downloads):** Vanilla HTML5, CSS3, ES6 JavaScript, native Canvas 2D, browser `localStorage`, and pre-installed Node.js tools only. GitHub Pages hosts the finished static site.
* **First-slice scope:** local sign up/sign in/sign out; Home, Play, and Results; a saved restoration record; Canvas PNG export; per-layer Strategy rules and a conditional comparison; minimal tests and linting. Do **not** build a dashboard/gallery, timed-mode gameplay, backend/API, database, Docker, or dependencies.
* **Static-site limitation:** account data, session state, scoring, and records are browser-local educational checks, not production authentication or tamper-proof storage. Document this in `PROJECT-RECORD.md`.
* **Before each build step:** inspect only files relevant to that step; propose the smallest needed OOP/SOLID design and strategy functions; discuss it and wait for approval before editing.
* **After each build step:** run the available pre-installed linter and focused checks; do not mark the step complete while lint/test errors remain.
* **Keep it light:** concise readable code; minimum useful tests; no unnecessary frameworks or libraries.

## 2. Fixed Game Rules and Architecture

### Gameplay

* **Grid:** 4 × 4. A layer has 3–5 designated target cells, so the player makes meaningful deductions without repeating 48 moves.
* **Layer order:** Layer 2, Surface Dirt → Layer 1, Overpaint → Layer 0, Aged Varnish. Each layer presents all three clue categories: chemical ratio, tool, and safe-zone/order.
* **Chemicals:** `water_ratio`, `oil_ratio`, `acid_ratio`; tools: `swab`, `brush`, `heat_lamp`.
* **Rules:**
  * Surface Dirt: 70 water / 30 oil / 0 acid; swab; marked low-risk cells.
  * Overpaint: 20 water / 70 oil / 10 acid; brush; central target cells, after Surface Dirt.
  * Aged Varnish: 10 water / 20 oil / 70 acid; heat lamp; border target cells, last.
* **Feedback:** a valid move clears one target cell; a wrong mixture, tool, order, or zone reduces integrity. Final score is 60% integrity and 40% clue deduction.
* **Timed Mode:** visible and disabled, labeled “Coming in Review 3.”

### Module map

* `js/rules.js`: domain models and pure rules: `CellState`, `PaintingGrid`, layer strategies in `LAYER_STRATEGIES`, `evaluateMoveConditional`, and scoring.
* `js/storage.js`: `StorageRepository`, the sole `localStorage` access point for local accounts, active session, and restoration records.
* `js/auth.js`: concise form/session helpers and client-side route guards.
* `js/play.js` and `js/results.js`: screen-specific Canvas/UI wiring only.
* `index.html`, `signup.html`, `login.html`, `play.html`, `results.html`; `css/styles.css`.
* `tests/`: only focused unit tests for rules/storage and one concise browser smoke/manual test record if a preinstalled headless browser runner is available.

### OOP, SOLID, and pattern choice

* `CellState` models one cell; `PaintingGrid` owns grid/layer progression (**SRP**).
* Each layer strategy encapsulates its behavior, allowing another layer without changing the evaluator (**Strategy pattern**, **OCP**).
* `StorageRepository` isolates browser persistence from game/UI code (**SRP**, **DIP-friendly seam** for a future backend).
* Keep `evaluateMoveConditional` only as the explicit simpler comparison, with parity tests against strategy results.

## 3. Build Plan (one approved step at a time)

### Step 0 — Environment Check (no app code)

Confirm Node.js, npm, a JavaScript linter, a test runner, and a browser/headless-browser option already exist. Confirm the 4 × 4 grid, all three clues, fixed rules, disabled Timed Mode, and static GitHub Pages target.

### Step 1 — Static Skeleton and Local Tooling

Create the small HTML/CSS/JS structure, an accessible shared layout, and only the local scripts/configuration supported by installed tooling. No dependencies unless already present.

### Step 2 — Local Account and Session Flow

Implement sign up, sign in, sign out, duplicate/invalid credential checks, protected play/results-page guards, and `StorageRepository`. Never claim this is secure server authentication.

### Step 3 — Pure Game Rules and Strategy Pattern

Implement `CellState`, `PaintingGrid`, the three `LAYER_STRATEGIES`, `evaluateMoveConditional`, move feedback, and 60/40 scoring. Keep rules separate from DOM and storage.

### Step 4 — Accessible Canvas UI

After receiving the screen mockups, implement Home, Play, and Results. Include labels, keyboard-capable controls, integrity meter, layer tracker, disabled timed toggle, kit/tools, mixing bowl, three clue notes, Canvas PNG export, and replay.

### Step 5 — Client-Side Verified Save

When all targets clear, replay the move log through `LAYER_STRATEGIES`, calculate the score, and save one structured record through `StorageRepository`. Associate it with the signed-in local user and render Results.

### Step 6 — Minimal Verification and GitHub Pages

Add only focused tests: valid/invalid strategy moves, strategy/conditional parity, 60/40 scoring, account validation/record isolation, and one concise browser smoke check when tooling permits. Add GitHub Actions to lint/test and deploy static files to GitHub Pages. Create `TEST-NOTES.md` and `PROJECT-RECORD.md`; record AI assistance, design decisions, static-site limitation, and final OOP/SOLID classes here and in this specification.

## 4. Acceptance Criteria

* A visitor can create a valid local account, sign in, and sign out; duplicate/invalid credentials fail.
* Signed-out visitors are redirected from Play and Results; saved records are filtered to the active local user.
* The player uses all three clue categories to choose a solvent, tool, safe zone, and layer order; errors reduce integrity.
* Completing all target cells saves one local restoration record, shows a server-free 60/40 score breakdown, and exports a PNG.
* The published GitHub Pages site is playable without a backend or external runtime dependency.
* `StorageRepository` and the Strategy/conditional comparison are documented; no dashboard/gallery route is present in this slice.
