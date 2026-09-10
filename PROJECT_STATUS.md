# Campus Spatial Decision Support System — Project Status

Last updated: current session. This file exists so you (or anyone picking this
project back up) can see everything that's actually built, working, and still
outstanding, in one place — without re-reading every source file.

---

## 1. What this project is

A campus IT decision-support tool that answers: *"which machines can run which
OS or software, where are they, and why?"* — combining four techniques into
one pipeline:

- **NLP** — parses a plain-language question into intent + entities
- **GIS** — resolves entities against a spatially-indexed hardware inventory
- **MCDM (TOPSIS)** — ranks OS options per machine on 6 weighted criteria
- **XAI (SHAP)** — explains *why* a machine scored the way it did

---

## 2. Data — ✅ complete, validated

| File | Rows | Notes |
|---|---|---|
| `hardware_inventory.csv` | 500 | one row per physical machine |
| `os_requirements.csv` | 67 | OS min specs, TPM/Secure Boot flags, EOL dates |
| `software_requirements.csv` | 72 | curated software titles, 21 categories |
| `software_cache.csv` | 50 | Tier 2 dynamically-enriched entries |
| `campus_spatial_data.csv` | 36 | locations across 6 blocks x 6 lab types |
| `nlp_query_dataset_10000.csv` | 10,000 | labeled queries for NLP training/eval |

Cross-consistency confirmed: spatial dataset asset counts match hardware
inventory exactly, zero discrepancies.

---

## 3. Backend (FastAPI + PostgreSQL/PostGIS) — ✅ built, ✅ extended this session

Base infrastructure: `models.py` (SQLAlchemy schema), `database.py`
(connection), `load_data.py` (loads all 6 CSVs).

### Endpoints

| Endpoint | Status | What it does |
|---|---|---|
| `GET /locations` | ✅ original | all 36 locations with coordinates + asset counts |
| `GET /assets?block=&lab=` | ✅ original | filterable hardware list (no filters = all 500) |
| `GET /assets/{id}/os-compatibility?os_id=` | ✅ original | binary rule-based pass/fail vs one OS |
| `GET /explain/{asset_id}/{os_id}` | ✅ original | SHAP feature-contribution breakdown |
| `GET /software/{id}/compatible-assets` | ✅ original | Tier 1 (curated) then Tier 2 (cache) then live Wikipedia enrichment |
| `POST /query` | ✅ original | full NLP → intent → routed pipeline |
| `GET /assets/{id}/rank?weight_profile=` | 🆕 added this session | full TOPSIS ranking of every compatible OS for one machine, with 6-criteria breakdown; `weight_profile` optional (`default` / `security_focused` / `performance_focused`), previously computed internally but never exposed |
| `GET /fleet/os-readiness?os_id=` | 🆕 added this session | fleet-wide %: how many of all 500 assets meet a given OS's minimum requirements, plus a tally of the most common blocking reason |

The rule-based compatibility check was refactored into a shared
`_rule_based_check()` helper so `/os-compatibility` and `/fleet/os-readiness`
can't drift out of sync with each other.

---

## 4. MCDM (TOPSIS) ranking engine — ✅ built, now ✅ reachable

- 6 weighted criteria per (machine, OS) pair: RAM, storage, CPU cores, CPU
  clock, TPM, Secure Boot
- Fixed-bound normalization — a genuine fix for a division-by-zero bug present
  in standard dynamic-bound TOPSIS; documented as a paper contribution
- Contextual weight profiles (`weights_config.py`): `DEFAULT`,
  `SECURITY_FOCUSED`, `PERFORMANCE_FOCUSED`, auto-selected by lab type
- Stress-tested across all 500 assets with zero errors
- **Previously**: this only ran internally, e.g. inside the `/query`
  `os_recommendation` intent, which only returned a `top_3`. **Now**: fully
  exposed via `/assets/{id}/rank`, with weight-profile override, from both
  the API and the frontend

---

## 5. NLP module — ✅ built

- Intent classifier (TF-IDF + Logistic Regression, 6 intent classes)
- Entity extractor (location/OS/software/numeric conditions) with a
  shorthand-alias correction layer ("Win11" → "Windows 11")
- **Results**: 100% intent accuracy on synthetic test data, **50% on
  hand-written adversarial queries** — a real, disclosed generalization gap,
  not swept under the rug
- Entity extraction: 100% / 100% / 97.5% (location / OS / software)

---

## 6. XAI (SHAP) module — ✅ built

- Random Forest classifier trained on the 6 criteria across all 33,500
  (asset, OS) pairs
- SHAP TreeExplainer generating per-feature contribution values
- Qualitatively validated on representative cases; no formal comprehension
  study run yet (see §9)

---

## 7. Frontend dashboard — ✅ fully rebuilt this session

Single-file `frontend/index.html`, wired to the live backend at
`localhost:8000`, no build step. Five views:

| View | What it shows |
|---|---|
| **Overview** | fleet stat cards, assets-per-block, TPM 2.0/1.2/none readiness, current OS footprint, **and a live fleet OS-readiness widget** (Windows 11 / Windows 10 / Ubuntu 24.04 readiness %, using the new `/fleet/os-readiness` endpoint) |
| **Query Assistant** | NLP query box, parsed intent/entities, SHAP-backed results, side map |
| **Asset Explorer** | filterable/searchable table of all 500 machines; click a row to open a detail panel with (a) a rule-based compatibility check + SHAP explanation, and (b) a **full TOPSIS ranking of every compatible OS**, with a **weight-profile selector** (default / security-focused / performance-focused / auto) |
| **Campus Map** | full map, marker size scaled by machine count, click-through to the filtered Asset Explorer |
| **Software** 🆕 | pick from the 72-title Tier 1 catalog or type any software name for a live Tier 2 lookup; shows which tier answered, confidence, and the list of compatible machines |

Design notes: dark blue-black base (not generic near-black), teal system
accent + amber stat-callout accent, Inter (UI) + JetBrains Mono (data/IDs)
type pairing — a deliberate "terminal readout" feel matched to an IT-ops tool.
Every view shows a clear error banner (not a silent failure) if the API is
unreachable.

The OS and software catalogs shown in dropdowns are hand-curated from the
project's own `os_requirements.csv` / `software_requirements.csv` files,
since the API has no `/os` or `/software` list endpoint — everything else on
screen comes from live API calls.

---

## 8. Research paper draft — 🟡 substantial, not final

`paper/draft.md` has Abstract, Introduction, Related Work, System
Architecture, Dataset Construction, Evaluation, Discussion/Limitations, and
Conclusion all drafted. Still has bracketed placeholders:

1. Author name(s), institution, contact email
2. Architecture diagram (Figure 1, §3.1)
3. §3.3.1 — write-up of the weight profiles (now easier to describe since
   they're user-facing in the UI)
4. §3.5 — description of the dashboard (now much richer — worth rewriting
   this section to reflect the 5-view build, not the original single page)
5. §4.1 — real hardware inventory numbers (real vs. augmented split)
6. §4.3 — Tier 2 software lookup's honest status (built, functional, not
   formally evaluated at scale)
7. §6 — dataset composition disclosure (real vs. synthetic)
8. References — format the OS vendor citations from `source_url` columns
9. Appendix A — insert the weight tables
10. Appendix B — insert the 40-query stress test table

---

## 9. What's explicitly NOT done yet

### 🔴 Critical — the one real piece of missing experimental work
**Independent MCDM validation.** `evaluation/expert_validation_sample.csv`
was filled in using the system's own rule (circular) — flagged in
`EVALUATION_SUMMARY.md` as unusable as-is. Needs 2–3 people who did **not**
build the system to fill it in blind (45 asset/OS pairs, judging only from
visible specs), then `python mcdm_validation_sample.py --score` to compute
real agreement.

### 🟢 Optional, strengthens but not required
- SHAP comprehension survey (10–15 people, rate 5–6 example explanations)
- Broader Tier 2 software lookup accuracy evaluation
- NLP training data diversification (already named as future work in the
  paper itself)

---

## 10. Suggested order of attack from here

1. Run the independent MCDM validation (§9) — the only real research gap left
2. Rewrite paper §3.5 to describe the actual 5-view dashboard
3. Fill in the remaining bracketed placeholders (§8)
4. Decide how much detail to give the Tier 2 software lookup in §4.3 given
   it now has a full UI but still no formal accuracy evaluation
