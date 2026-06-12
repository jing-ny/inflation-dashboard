# Inflation Dashboard - Project Plan & Architecture

**Last Updated:** May 13, 2026
**Purpose:** Reference document to maintain consistency across sessions.

> **For project principles** (no manual entry as a fallback, validation, provenance, staleness visibility, trust the anomaly detector), see **[CLAUDE.md](CLAUDE.md)**. PRs and refactors are gated on those principles, not just on the to-do list below.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Current State](#current-state)
3. [To-Do List](#to-do-list)
4. [Known Bugs](#known-bugs)
5. [Architecture](#architecture)
6. [Data Flow](#data-flow)
7. [File Structure](#file-structure)
8. [Automation](#automation)
9. [Manual Maintenance Tasks](#manual-maintenance-tasks)
10. [Data Sources & Known Limitations](#data-sources--known-limitations)
11. [Session Recovery Guide](#session-recovery-guide)

---

## Project Overview

**Name:** Inflation, Officially
**URL:** https://jing-ny.github.io/inflation-dashboard/
**Repo:** https://github.com/jing-ny/inflation-dashboard
**Newsletter:** https://inflationofficially.substack.com

**Purpose:** A source-first dashboard tracking official CPI inflation data and central bank forecasts across 15 economies.

**Countries Covered:**

| Code | Country | CPI Source | Central Bank | Frequency |
|------|---------|------------|--------------|-----------|
| US | United States | BLS | Federal Reserve | Monthly |
| EA | Euro Area | Eurostat | ECB | Monthly |
| UK | United Kingdom | ONS | Bank of England | Monthly |
| CA | Canada | Statistics Canada | Bank of Canada | Monthly |
| AU | Australia | ABS | RBA | Monthly (new) / Quarterly (historical) |
| NZ | New Zealand | Stats NZ | RBNZ | Quarterly |
| ZA | South Africa | Stats SA | SARB | Monthly |
| JP | Japan | Statistics Bureau | Bank of Japan | Monthly |
| KR | South Korea | KOSTAT | Bank of Korea | Monthly |
| SG | Singapore | DOS | MAS | Monthly |
| IN | India | MOSPI | RBI | Monthly |
| CN | China | NBS | PBOC | Monthly |
| BR | Brazil | IBGE | BCB | Monthly |
| MX | Mexico | INEGI | Banxico | Monthly |
| VE | Venezuela | BCV | BCV | Irregular |

---

## Current State (as of May 13, 2026)

### What Works
- Dashboard fully deployed on GitHub Pages, all 15 country pages render correctly
- `fetch_historical_cpi.py` covers all 15 countries; **US/UK/CA hit official APIs directly** (BLS, ONS, StatCan) bypassing FRED lag; EA on ECB direct; rest on FRED
- `fetch_imf_forecasts.py` covers all 15 countries (EA uses `EURO` group code)
- `auto_scrape_cb_forecasts.py` covers **9/15 central banks** with `--merge` mode and a 1pp anomaly gate that routes large jumps to `cb_forecasts_draft.json` for review. Of the 9, three (UK / NZ / ZA) currently have **extractor disabled** — URL discovery still runs but no projection values are written (see "Scraper status" below)
- 5 GitHub Actions workflows running on schedule; **email notifications are now informative** (per-country diffs, freshness, commit URLs) instead of the previous "changes detected" boilerplate
- `update_cpi.py` and `batch_update_cpi.py` manual tools functional, with anomaly gates (MoM step >1pp + prior-year-match)
- Substack newsletter signup embedded on homepage; AI-assistance disclaimer on all pages and email templates
- CB forecasts and IMF forecasts populated for all 15 countries
- 10-year CPI history with Chart.js visualization on country pages
- **Freshness UI** (CLAUDE.md #4 layer 2): every row in the Current Inflation and Inflation Outlook tables, plus the country-page hero, renders a colored pill aged against the source's expected cadence (45/90d for CPI, 120/180d for forecasts). Footer summarises N current / M stale / K very stale

### Scraper status (auto_scrape_cb_forecasts.py)

| Country | Source | State |
|---|---|---|
| US | Fed SEP | Live ✅ |
| EA | ECB structured-table parser (#21) | Live ✅ |
| JP | BoJ Outlook PDF | Live ✅ |
| BR | BCB Focus API | Live ✅ |
| AU | RBA SMP overview parser (#14) | Live ✅ |
| CA | BoC MPR projections page parser (#16) | Live ✅ |
| UK | BoE | **Disabled** — URL found, structured-table parser pending (#10) |
| NZ | RBNZ | **Disabled** — Cloudflare WAF + HTML restructure + PDF tables (#6) |
| ZA | SARB | **Disabled** — site is JS-rendered, listing widget broken upstream (#12) |

### Data Freshness

**Live site data as of May 13, 2026** (now also visible to readers via the per-row freshness pill):

| Data | Latest | Status |
|------|--------|-------|
| CPI US / EA / UK / CA / BR / MX / CN / IN / KR | Mar 2026 | Amber on dashboard (Apr release awaiting fetch) |
| CPI AU / JP / ZA / SG / VE | Feb 2026 | Red on dashboard (known lagging or quarterly cadence) |
| CPI NZ | 2026-Q1 | Amber (quarterly) |
| CB Forecasts | Most: Apr-May 2026 (auto-merged); UK / NZ / ZA frozen at curated Feb-Jan 2026 | Mixed |
| IMF WEO | April 2026 | Refreshed Apr 22 |

**Ongoing concern (carried forward):** FRED still lags. The auto-fetcher catches up on Mondays. The freshness UI now makes that lag visible to readers rather than implicit.

### Workflow Status

| Workflow | Last Run | Status |
|----------|----------|--------|
| Update Inflation Data | 2026-05-11 | Success |
| Auto-Scrape CB Forecasts | 2026-05-11 | Success (publication_date self-healed on AU + CA + ECB) |
| Monitor & Update Data | 2026-05-11 | Success |
| Newsletter Draft | 2026-05-12 | Success — now embeds full draft in email (#22) |
| Weekly Alert | 2026-05-11 | Success |

---

## To-Do List

### Phase 1: Restore Data Freshness (Priority: Critical)

| # | Task | Details | Status |
|---|------|---------|--------|
| 1.1 | Manual CPI update for all 15 countries | Updated Jan + Feb 2026 values for all 15 countries. Added 5 missing countries (JP, IN, KR, SG, VE) to `historical_cpi.json`. UK/AU have Jan only (Feb releases Mar 25). NZ updated to Q4 2025. | **Done** (Mar 24) |
| 1.2 | Update CB forecasts | Updated 10 central banks to latest meetings: Fed Mar SEP, ECB Mar, BoE Feb MPR, BoC Jan MPR, RBA Feb SoMP, RBNZ Feb MPS, SARB Jan, BoJ Mar, RBI Feb, BOK Feb. Policy rates and projections current. SG/VE/CN unchanged (no new publications). | **Done** (Mar 24) |
| 1.3 | Add direct API sources for key countries | Reduce FRED dependency. Priority: BLS API for US, Stats Canada API for CA, ONS API for UK. Each country 2-3 hours. | To Do |
| 1.4 | Fix Monitor workflow commit failure | Added `permissions: contents: write` (root cause was 403 on push). Also aligned git config and added summary step to match `update-data.yml` pattern. | **Done** (Mar 24) |

### Phase 2: Fix Known Bugs (Priority: High)

| # | Task | Details | Status |
|---|------|---------|--------|
| 2.1 | Clean up `styles.css` duplication | Deduplicated from 1279 → 604 lines. Removed 4 redundant copies of policy change CSS block. | **Done** (Mar 24) |
| 2.2 | Remove `test` text from `index.html` | Removed bare `test` string. | **Done** (Mar 24) |
| 2.3 | Fix `send_weekly_alert.py` data path | Fixed path to `docs/data/historical_cpi.json` and changed key access to read country codes directly from top level. | **Done** (Mar 24) |
| 2.4 | Add argparse to `auto_scrape_cb_forecasts.py` | Added argparse for `--force`, `--country`, `--dry-run`. Wired into scraper logic. | **Done** (Mar 24) |
| 2.5 | Unify FRED series between scripts | Updated `monitor_updates.py` to use same series as `fetch_historical_cpi.py` (US: CPIAUCNS, JP: JPNCPIALLMINMEI). | **Done** (Mar 24) |
| 2.6 | Implement `update_forecast_history()` | Implemented in `monitor_updates.py`. Reads CB forecasts, appends timestamped snapshot to `docs/data/history/cb_forecast_history.json`. | **Done** (Mar 24) |
| 2.7 | Rotate leaked API keys | Rotated FRED, Resend keys. Added Anthropic API key. All GitHub Secrets updated. | **Done** (Mar 25) |

### Phase 3: Newsletter Automation (Priority: Medium)

| # | Task | Details | Status |
|---|------|---------|--------|
| 3.1 | Build change detection script | Already working in `send_weekly_alert.py` (fixed in Phase 2). Detects material changes (≥0.3pp or direction reversal) via snapshot comparison. | **Done** (Mar 24) |
| 3.2 | Claude API draft generation | New `scripts/generate_newsletter.py`. Uses Anthropic SDK (`claude-sonnet-4-20250514`) to generate 300-500 word drafts from CPI changes + CB/IMF forecast context. Supports `--dry-run` and `--output`. | **Done** (Mar 24) |
| 3.3 | GitHub Actions integration | New `newsletter-draft.yml`. Triggers on `historical_cpi.json` changes or manual dispatch. Generates draft, commits to `docs/drafts/`, optional email notification. Requires `ANTHROPIC_API_KEY` secret. | **Done** (Mar 24) |
| 3.4 | Wire weekly alert workflow | Rewired `weekly-alert.yml` to call `send_weekly_alert.py`. Added snapshot commit step, proper env vars, permissions. | **Done** (Mar 24) |

### Phase 5: Data Quality Hardening (Priority: High)

| # | Task | Details | Status |
|---|------|---------|--------|
| 5.1 | Fix BR/MX 2026-01 and 2026-02 miscaptures | Prior-year values (BR 5.06%, MX 3.77%, etc.) from comparison text were stored as current-month readings. Corrected per IBGE/INEGI releases. | **Done** (Apr 22) |
| 5.2 | Add anomaly gate to `update_cpi.py` | Blocks MoM step >1.0pp or exact prior-year-same-period match. `--confirm-anomaly` override. | **Done** (Apr 22) |
| 5.3 | Add anomaly logging to `fetch_historical_cpi.py` | Same two checks; writes `docs/data/cpi_anomalies.json` and exits 2 so CI surfaces them. | **Done** (Apr 22) |
| 5.4 | Fix `fetch_imf_forecasts.py` coverage | Script only fetched 9 countries with wrong EA code (`EMU` → empty) and wrong output dir. Now 15 countries, `EURO` code, `docs/data/` path; preserves curated `note`/`display_order`/`url`. | **Done** (Apr 23) |
| 5.5 | Preserve emoji encoding in `update_cpi.py` | `save_data` now uses `ensure_ascii=False` so raw unicode flags survive, preventing rebase conflicts with bot commits. | **Done** (Apr 22) |
| 5.6 | Deeper BR/MX history audit | Spot-checked 2026-01/02. Full 2025 audit still pending. | To Do |

### Phase 6: Eliminate Manual Updates (Priority: High)

**Status: Tier 1 complete (Apr 23–25). Tier 2 paused — see "Pause rationale" below.**

**Goal:** Drive the manual update surface to near-zero. Today 6/15 central banks and most fresh CPI values still require human entry (down from 9/15 before this phase). Build direct-API fetchers and official-source scrapers so automation catches releases without human intervention.

**Tier 1 — ship first (highest payoff, lowest friction):**

| # | Task | Source | Scope | Status |
|---|------|--------|-------|--------|
| 6.1 | Fed SEP scraper | federalreserve.gov (static HTML table) | Quarterly (Mar/Jun/Sep/Dec). Writes to `cb_forecasts.json[US]`. Integrate into `auto_scrape_cb_forecasts.py`. Also added `--merge` mode so scrapes auto-commit instead of just drafting; 1pp anomaly gate falls through to draft review. | **Done** (Apr 23) |
| 6.2 | BoJ Outlook scraper | boj.or.jp (PDF table, `pypdf`) | Quarterly (Jan/Apr/Jul/Oct). Writes to `cb_forecasts.json[JP]`. Extracts median Policy Board forecast for CPI less fresh food, fiscal-year basis. | **Done** (Apr 24) |
| 6.3 | BCB Focus survey fetcher | BCB Olinda OData API (JSON) | Pulls weekly Focus median IPCA forecasts via `ExpectativasMercadoAnuais` endpoint. Writes to `cb_forecasts.json[BR]`. Selic (policy rate) updates still manual. | **Done** (Apr 25) |
| 6.4 | BLS CPI API fetcher | `api.bls.gov/publicAPI/v2/...` (free tier: 25/day; with key: 500/day) | Monthly. Replaces FRED lag for US; precise within 30 min of BLS release. Extend `fetch_historical_cpi.py`. New `fetch_bls_series()` + US `api: BLS` route; FRED fallback retained for outages. Optional `BLS_API_KEY` env for higher rate limit + full window. | **Done** (Apr 25) |
| 6.5 | Eurostat HICP API fetcher | Eurostat REST JSON | Skipped. Existing ECB API path is fresher (Eurostat `prc_hicp_manr` lagged Dec 2025 when probed Apr 25 2026; ECB feed already had Mar 2026). EA stays on `api: "ECB"`. | **Skipped** (Apr 25) |
| 6.6 | ONS UK CPI API fetcher | ONS Beta API JSON | Monthly. UK now uses series `d7g7` on dataset `mm23` (already YoY). Bonus: confirmed UK Mar 2026 = 3.3% (was pending). | **Done** (Apr 25) |
| 6.7 | StatCan CPI API fetcher | StatCan WDS vector API | Monthly. CA now uses vector V41690973 (NSA index, computes YoY). | **Done** (Apr 25) |

**Tier 2 — paused (medium effort, lower marginal payoff):**

| # | Task | Source | Cadence | Status |
|---|------|--------|---------|--------|
| 6.8 | Banxico scraper | banxico.org.mx Quarterly Inflation Report (PDF) | 4x/year | Paused |
| 6.9 | BOK scraper | bok.or.kr Economic Outlook (PDF) | 4x/year | Paused |
| 6.10 | RBI scraper | rbi.org.in Monetary Policy Report (PDF) | 6x/year | Paused |
| 6.11 | MAS scraper | mas.gov.sg Macroeconomic Review (PDF) | 2x/year | Paused |

**Pause rationale (2026-04-25):** Tier 1 already removed ~80 manual updates per year. The four Tier 2 banks publish 2–6 times per year combined, so finishing Tier 2 only removes ~16 more updates per year — much lower marginal payoff per hour of work than Tier 1. Better to let the new pipeline (BLS / ONS / StatCan / Fed / BoJ / BCB) run for a couple of cycles and prove itself before stacking more PDF parsers on top. Each Tier 2 bank can still be updated after meetings by editing `cb_forecasts.json` through a reviewed PR (`update.sh` was removed in #84); the anomaly gates from Phase 5 prevent the old BR/MX-style miscapture pattern. Revisit Tier 2 if any of these banks turn out to publish more often than expected or the manual cadence becomes annoying.

**Explicit non-goals:**
- **PBoC**: China does not publish numerical inflation forecasts in a standardized schedule. Track policy rate manually; skip forecast scraping.
- **BCV**: Venezuela publishes irregularly and inconsistently. Keep manual.
- ~~CPI manual gate via `update_cpi.py`~~ — removed 2026-06 (#84); per-country direct-source fetchers (#50–#57) replaced it.

**Current automation surface (after Tier 1):**
- **CB forecasts auto-updated**: US, JP, BR, EA, UK, AU, CA, NZ, ZA (9/15)
- **CB forecasts still manual**: CN, IN, KR, SG, MX, VE — but PBoC and BCV are explicit non-goals, so the realistic remaining surface is 4 banks (Banxico, BOK, RBI, MAS).
- **CPI direct-from-source**: US (BLS), EA (ECB), UK (ONS), CA (StatCan) — the four largest economies, no FRED lag.
- **CPI via FRED with lag**: countries not yet migrated to a direct source stay on FRED; lag shows as staleness on the dashboard until the direct fetcher ships (no manual supplement path, CLAUDE.md #1).

**Success criteria (when Phase 6 closes):**
- The automated Mon/Thu workflows pick up 90%+ of release cadence on their own.
- Manual updates are confined to: PBoC + BCV (non-goals), Tier 2 banks until they ship, and CPI for the 11 non-API countries when fresh values are needed before FRED catches up.

### Phase 4: Expansion & Polish (Priority: Low)

| # | Task | Details | Status |
|---|------|---------|--------|
| 4.1 | Add Core CPI + US PCE tracking | Added Core CPI (3.1%), PCE (2.5%), Core PCE (2.6%) as supplementary metrics on US page. Data in `historical_cpi.json` under `supplementary` field. | **Done** (Mar 24) |
| 4.2 | Add Brazil and Mexico | Added BR (IBGE/BCB, 14.25%) and MX (INEGI/Banxico, 9.50%). Country pages, CPI data, CB/IMF forecasts, FRED series. Now 15 countries. | **Done** (Mar 24) |
| 4.3 | Make year columns dynamic in index.html | Outlook table headers now auto-advance based on `new Date().getFullYear()`. | **Done** (Mar 24) |
| 4.4 | Add table sorting on index page | Click column headers to sort/toggle. Visual ▲/▼ indicator. Numeric-aware sorting. | **Done** (Mar 24) |
| 4.5 | Clean up legacy files | Removed 11 legacy scripts, `inflation_data.js`, 4 semi-redundant fetch scripts. | **Done** (Mar 24) |
| 4.6 | Consolidate duplicate workflows | Removed `auto-scrape-forecasts.yml` (kept `auto-scrape-cb-forecasts.yml`). | **Done** (Mar 24) |

### Phase 7: CI Repair + CLAUDE.md Principles + Staleness Automation (Priority: High)

Triggered by the May 7 CI outage report; expanded into a broader correctness/visibility push.

| # | Task | Details | Status |
|---|------|---------|--------|
| 7.1 | Fix CI Auto-Scrape commit step (#2 / PR #2) | Workflow was `git add`-ing `docs/data/scraper_state.json` which the scraper never writes. Also fixed CPI anomaly detector that compared backfill points against `latest` instead of chronologically prior — generated false positives across CA's 2009-2015 history when StatCan widened its window. | **Done** (May 10) |
| 7.2 | CLAUDE.md project principles | 5 principles: no manual entry as fallback, validated-or-marked, provenance on every record, stale data visibly stale, trust the anomaly detector. Saved as both repo doc and global memory so future sessions inherit. | **Done** (May 10) |
| 7.3 | BoE / SARB / RBA / BoC scraper rewrites | PRs #11, #13, #14, #16. URL pattern updates + structured-table parsers where possible (RBA/BoC) + explicit-disabled pattern where not (BoE/SARB pending #10, #12). RBA produces real headline data for the first time in 2+ years. | **Done** (May 10-11) |
| 7.4 | Informative email notifications | PRs #15, #22, #23. Subjects include country codes + short SHA; bodies embed per-country diffs, draft summary, commit URL; newsletter draft email embeds the full draft. Replaces hardcoded "changes detected" boilerplate. | **Done** (May 11-13) |
| 7.5 | `publication_date` actually refreshes on auto-merge (#17) | Layer 1 of staleness automation: `_normalise_publication_date` accepts all scraper formats and writes the result back. Bot self-heals drift on next cron. | **Done** (May 11) |
| 7.6 | ECB structured-table parser (PR #21) | Replaces prose extractor that was silently overwriting curated EA; PR #18 first disabled the unsafe path, #21 lands the real parser. | **Done** (May 12) |
| 7.7 | BoJ row-spanning fix (PR #19) | Handles FY-promoted-to-actual where row boundaries shift. | **Done** (May 12) |
| 7.8 | Freshness UI (#30 / PR #34) | Layer 2 of staleness automation: per-row colored pills + footer summary on both index tables and country-page hero. CPI cadence 45/90d; forecast cadence 120/180d. | **Done** (May 13) |
| 7.9 | "Source disabled" UI treatment (#31) | Layer 3: distinguish scraper-paused (UK/NZ/ZA) from real-world stale so the red signal isn't diluted by known-disabled scrapers. | To Do |
| 7.10 | Workflow-failure email alerts (#28) | All 5 weekly cron workflows currently silent on hard failure; add `if: failure()` step that emails when a run crashes. | To Do |
| 7.11 | Refresh PROJECT_PLAN + METHODOLOGY (#29 / this PR) | ~3 weeks of unrecorded May 2026 work, plus alignment with CLAUDE.md and the new freshness layer. | **Done** (May 13) |

**Open follow-ups from Phase 7:** #6 (RBNZ proper fix), #10 (BoE structured extraction), #12 (SARB AEM/PDF), #24 (RBNZ scraper noise cleanup), #25 (source_date format normalization), #26 (gitignore backup JSONs), #27 (IMF WEO hardcode), #32 (surface draft entries), #33 (extract inline index.html JS).

---

## Known Bugs

### Active

Tracked as GitHub issues — see the [issue list](https://github.com/jing-ny/inflation-dashboard/issues) for current state. As of May 13, 2026:

| # | Issue | Notes |
|---|---|---|
| #6 | RBNZ scraper Cloudflare-walled + page restructured | Deferred. Needs `curl_cffi` + new URL pattern + PDF table extraction. |
| #10 | BoE structured-table extraction | Follow-up after #11 disabled the noisy prose extractor. Likely needs `pdfplumber`. |
| #12 | SARB AEM JSON or PDF parsing | Follow-up after #13 disabled the noisy extractor. Site itself was showing "technical difficulties" at probe time. |
| #24 | `scrape_rbnz` still hits 403 URL each run | Cleanup — align with the disabled-extractor pattern used by BoE/SARB. |
| #25 | `source_date` format inconsistency across scrapers | Fed/BoJ emit YYYY-MM-DD; RBA/BoC emit "Month YYYY"; ECB historic emits "Mon YYYY". `_normalise_publication_date` papers over it but the source-side should be normalized. |
| #26 | `historical_cpi_backup_*.json` checked in | Gitignore the pattern; remove the one stale file. |
| #27 | Hardcoded "IMF WEO April 2026" in index.html footer | Will drift on next WEO release (Oct 2026). Derive from data. |
| #28 | No email alert on workflow **failure** | Notifications only fire on data changes; hard failures silent. |
| #29 | Doc refresh (this PR closes it) | PROJECT_PLAN.md + METHODOLOGY.md alignment. |
| #31 | "Source disabled" UI treatment (layer 3) | Distinguish scraper-paused from real-stale. Depends on #30. |
| #32 | Surface draft entries in the UI | `cb_forecasts_draft.json` pending review still invisible to readers. |
| #33 | Extract inline `<script>` from index.html → docs/index.js | Refactor. Currently ~350 inline LOC. |

### Watch list

| # | Item | Notes |
|---|------|-------|
| W1 | BR/MX 2025 history may have older miscaptures | Only 2026-01/02 were corrected. Values from 2025 should be spot-audited vs IBGE/INEGI archives. |
| W2 | NZ Q2 2026 may spike | RBNZ guidance suggests ~4.2% driven by Mid-East conflict energy pass-through. Watch for anomaly-gate trip. |
| W3 | Tier 2 manual-only banks (Banxico, BOK, RBI, MAS) | Paused per Phase 6 rationale; revisit if cadence becomes annoying. |

### Resolved (since Feb 2026)

| Bug / PR | Resolution | Date |
|-----|-----------|------|
| B1 | CSS deduplicated (1279 → 604 lines) | Mar 2026 |
| B2 | Removed bare `test` text from index.html | Mar 2026 |
| B3 | Fixed send_weekly_alert.py path + key structure | Mar 2026 |
| B4 | Added argparse to auto_scrape_cb_forecasts.py | Mar 2026 |
| B5 | Unified FRED series in monitor_updates.py | Mar 2026 |
| B6 | Implemented update_forecast_history() | Mar 2026 |
| B7 | Monitor workflow commit step guarded with has_changes check | Mar 2026 |
| B8 | Re-enabled SSL verification in CB scraper | Mar 2026 |
| B9 | Removed hardcoded 2024 URLs; scrapers discover latest from index pages | Mar 2026 |
| B10 | Switched JP/KR to COICOP 2018 FRED series with fallback | Mar 2026 |
| B11 | BR/MX 2026-01/02 contaminated with prior-year comparison values; added anomaly gates | Apr 2026 |
| B12 | `fetch_imf_forecasts.py` covered only 9/15 countries, wrong EA code, wrong output dir | Apr 2026 |
| B13 | `update_cpi.py` wrote escaped unicode flags, causing rebase conflicts with bot commits | Apr 2026 |
| PR #2 | CI Auto-Scrape commit step missing-pathspec + CPI anomaly detector backfill false-positives | May 2026 |
| PR #9 | Added CLAUDE.md project principles | May 2026 |
| PR #11 | BoE scraper: URL fix + disabled unsafe prose extractor (closes #4) | May 2026 |
| PR #13 | SARB scraper: working landing page + disabled extractor (closes #7) | May 2026 |
| PR #14 | RBA scraper: SMP overview structured-table parser, first real data in 2+ years (closes #5) | May 2026 |
| PR #15 | Email notifications: informative bodies with per-country diffs + commit URL | May 2026 |
| PR #16 | BoC scraper: new URL pattern + projections page Table-2 parser (closes #8) | May 2026 |
| PR #17 | `publication_date` actually refreshes when projections do (CLAUDE.md #4 layer 1) | May 2026 |
| PR #18 | Disabled ECB prose fallback that was silently overwriting curated EA | May 2026 |
| PR #19 | BoJ row-spanning fix (FY promoted to actual) | May 2026 |
| PR #21 | ECB structured-table parser replaces prose extractor | May 2026 |
| PR #22 | Embed full newsletter draft in notification email | May 2026 |
| PR #23 | Always emit `cb_forecasts_changes.md` after merge run | May 2026 |
| PR #34 | Freshness UI: per-row pills + footer summary (CLAUDE.md #4 layer 2, closes #30) | May 2026 |
| Live site out of sync (2 commits, 8 countries) | Full codebase pushed to GitHub | Feb 2026 |
| Venezuela page "Error loading data" | Null target handling fixed in country.js | Jan 2026 |
| Quarterly date format crash in monitor | Fixed AU/NZ `2025-Q4` format | Jan 2026 |
| Dec 2025 CPI values incorrect for 8 countries | Corrected from official sources | Feb 2026 |
| Data architecture: dual `data/` and `docs/data/` | Consolidated to `docs/data/` as single source | Feb 2026 |

---

## Architecture

### Core Principle: Single Source of Truth

```
Python Scripts (fetch / update data)
        ↓
    docs/data/ JSON Files (single source of truth)
        ↓
    HTML/JS Pages (read and display via fetch())
```

### Data Files (in `docs/data/`)

| File | Contents | Updated By |
|------|----------|------------|
| `historical_cpi.json` | 10-year CPI history + latest/previous readings | `fetch_historical_cpi.py` (auto) |
| `cb_forecasts.json` | Central bank forecasts, policy rates, key quotes | Manual edit after MPC meetings |
| `imf_forecasts.json` | IMF WEO inflation projections | Manual (2x/year: Apr + Oct) |
| `cpi_supplements.json` | Manual CPI supplements when FRED lags | Manual |
| `weekly_snapshots.json` | Weekly alert snapshots for change detection | `send_weekly_alert.py` |
| `history/cb_forecast_history.json` | CB forecast revision tracking | `monitor_updates.py` |
| `history/imf_forecast_history.json` | IMF forecast revision tracking | `monitor_updates.py` |

### Frontend Files (in `docs/`)

| File | Purpose |
|------|---------|
| `index.html` | Overview — Current Inflation table, CB Outlook table, Policy Rates grid. Each table has a per-row freshness pill + footer summary (CLAUDE.md #4). |
| `country.js` | Shared JS module for all 15 country detail pages. Renders the freshness pill on the hero "current value" date. |
| `freshness.js` | Shared helpers — `parsePublicationDate`, `freshnessFor`, `freshnessPill`. Loaded by index.html and each country page. |
| `styles.css` | Shared styles, including `.freshness-{green,amber,red,unknown}` palette. |
| `{code}.html` | Country detail pages (us, ea, uk, ca, au, nz, za, br, mx, jp, kr, sg, in, cn, ve) |

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                  Data Sources                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ FRED API │  │ ECB API  │  │ Official │  │   IMF API    │   │
│  │ (15 ctry)│  │ (EA only)│  │ Websites │  │ (WEO fetch)  │   │
│  └────┬─────┘  └────┬─────┘  └─────┬────┘  └──────┬───────┘   │
└───────┼──────────────┼──────────────┼──────────────┼───────────┘
        │              │              │              │
        ↓              ↓              ↓              ↓
┌────────────────────────────────────────────────────────────────┐
│                    docs/data/ (single source of truth)          │
│  ┌───────────────────┐ ┌────────────────┐ ┌────────────────┐  │
│  │historical_cpi.json│ │cb_forecasts.json│ │imf_forecasts.  │  │
│  │                   │ │                │ │json            │  │
│  └─────────┬─────────┘ └───────┬────────┘ └───────┬────────┘  │
└────────────┼───────────────────┼───────────────────┼───────────┘
             ↓                   ↓                   ↓
┌────────────┴───────────────────┴───────────────────┴───────────┐
│                    GitHub Pages (docs/)                          │
│  ┌─────────────────┐  ┌───────────────────────────────────┐   │
│  │index.html       │  │us.html, ea.html, ... ve.html      │   │
│  │(overview)       │  │(15 country detail pages)           │   │
│  └─────────────────┘  └───────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
inflation-dashboard/
├── README.md
├── PROJECT_PLAN.md              # This file
├── METHODOLOGY.md               # Data methodology documentation
├── CHANGELOG.md
├── LICENSE
├── .env.local                   # Local API keys (gitignored)
├── .gitignore
├── scripts/
│   ├── fetch_historical_cpi.py  # FRED/ECB CPI fetch (all 15 countries)
│   ├── fetch_imf_forecasts.py   # IMF WEO fetch
│   ├── auto_scrape_cb_forecasts.py  # CB forecast scraper (6 banks: ECB, BoE, RBA, BoC, RBNZ, SARB)
│   ├── monitor_updates.py       # FRED freshness check + CB meeting calendar
│   ├── send_notification.py     # Email via Resend API
│   ├── send_weekly_alert.py     # Weekly change detection + email alert
│   ├── generate_newsletter.py   # Claude API newsletter draft generation
│   ├── patch_cpi_supplements.py # Patches FRED gaps
│   └── test_data_sources.py     # Data source testing
│
├── docs/                        # GitHub Pages root
│   ├── index.html               # Overview page
│   ├── {country}.html           # 15 country detail pages
│   ├── styles.css               # Shared styles
│   ├── country.js               # Shared JS for country pages
│   └── data/                    # ★ SINGLE SOURCE OF TRUTH ★
│       ├── historical_cpi.json  # CPI data for all 15 countries
│       ├── cb_forecasts.json    # Central bank forecasts + policy rates
│       ├── imf_forecasts.json   # IMF WEO projections
│       ├── cpi_supplements.json # Manual CPI supplements
│       ├── weekly_snapshots.json
│       └── history/
│           ├── cb_forecast_history.json   # Forecast revision history
│           └── imf_forecast_history.json  # Forecast revision history
│
└── .github/workflows/
    ├── update-data.yml              # Mon 12pm UTC — FRED/ECB fetch + commit
    ├── monitor-updates.yml          # Mon & Thu 9am UTC — freshness check + email
    ├── auto-scrape-cb-forecasts.yml # Mon & Thu 10am UTC — CB forecast scraper
    ├── weekly-alert.yml             # Mon 1pm UTC — change detection + email
    └── newsletter-draft.yml         # 1st of month + on CPI push — Claude API draft
```

---

## Automation

### GitHub Actions Workflows

| Workflow | File | Schedule | Purpose | Status |
|----------|------|----------|---------|--------|
| Update Inflation Data | `update-data.yml` | Mon 12pm UTC | Fetch CPI + IMF from FRED/ECB, commit if changed | Running |
| Monitor & Update Data | `monitor-updates.yml` | Mon & Thu 9am UTC | Check FRED for updates, email alerts | Running |
| Auto-Scrape CB Forecasts | `auto-scrape-cb-forecasts.yml` | Mon & Thu 10am UTC | Scrape CB forecast pages | Running |
| Weekly Alert | `weekly-alert.yml` | Mon 1pm UTC | Change detection + email alert | Running |
| Newsletter Draft | `newsletter-draft.yml` | 1st of month + on CPI push | Claude API draft generation | Running |

### GitHub Secrets Required

| Secret | Purpose | Status |
|--------|---------|--------|
| `FRED_API_KEY` | FRED API access | Configured (rotated Mar 2026) |
| `RESEND_API_KEY` | Email notifications | Configured (rotated Mar 2026) |
| `ANTHROPIC_API_KEY` | Claude API for newsletter drafts | Configured (Mar 2026) |
| `NOTIFICATION_EMAIL` | Recipient email | Configured |

### Automation Coverage

| Task | Automated? | Notes |
|------|-----------|-------|
| CPI data fetch (all 15) | Yes (FRED/ECB) | But FRED lags 1-6 months for most countries |
| CB forecasts (6 banks) | Partial | ECB, BoE, RBA, BoC, RBNZ, SARB — scraper generates drafts |
| CB forecasts (7 banks) | No | Fed, BoJ, BOK, MAS, RBI, PBoC, IMF(VE/CN) — manual only |
| CB meeting reminders | Yes | `monitor_updates.py` |
| IMF WEO reminders | Yes | `monitor_updates.py` (Apr/Oct) |
| Stale data alerts | Yes | `monitor_updates.py` (75-day threshold) |
| Email notifications | Yes | Resend API |
| Weekly material change alert | Yes | `send_weekly_alert.py` via `weekly-alert.yml` |
| Newsletter draft generation | Yes | `generate_newsletter.py` via `newsletter-draft.yml` (monthly + on CPI push) |

---

## Manual Maintenance Tasks

### Monthly: CPI Data Update

CPI ingestion is fully automated (`update-data.yml`, Mon/Thu). There is no
manual-entry path (CLAUDE.md #1, #84): if a country's print is missing past
its expected date (see the dashboard's Release Calendar tab), fix or extend
the fetcher in `scripts/fetch_historical_cpi.py` — don't hand-edit the JSON.
```bash
# Run the fetcher locally for one country
python3 scripts/fetch_historical_cpi.py --country US
```

### After CB Meetings: Forecast Update

**When:** After major MPC meetings with new projections
**Key projection schedules:**

| Country | Bank | Months with Full Projections |
|---------|------|------------------------------|
| US | FOMC | Mar, Jun, Sep, Dec (SEP) |
| EA | ECB | Mar, Jun, Sep, Dec (staff projections) |
| UK | BoE | Feb, May, Aug, Nov (MPR) |
| CA | BoC | Jan, Apr, Jul, Oct (MPR) |
| AU | RBA | Feb, May, Aug, Nov (SoMP) |
| NZ | RBNZ | Feb, May, Aug, Nov (MPS) |
| ZA | SARB | Jan, Mar, May, Jul, Sep, Nov |
| JP | BoJ | Jan, Apr, Jul, Oct (Outlook) |
| KR | BOK | Feb, May, Aug, Nov |
| SG | MAS | Apr, Oct (policy statement) |
| IN | RBI | Feb, Apr, Jun, Aug, Oct, Dec |

**How:** Edit `docs/data/cb_forecasts.json` — update `publication_date`, `projections`, `policy_rate`, `key_quote`.

### Twice Yearly: IMF WEO Update

**When:** April and October
**Source:** https://www.imf.org/external/datamapper/PCPIPCH@WEO
**How:** Edit `docs/data/imf_forecasts.json`

---

## Data Sources & Known Limitations

### FRED API Lag (Core Problem)

FRED OECD series lag official releases significantly:

| Country | FRED Series | Typical Lag | Mitigation |
|---------|-------------|-------------|------------|
| US | CPIAUCNS | 2-4 weeks | BLS publishes ~13th; manual update or add BLS API |
| UK | GBRCPIALLMINMEI | 1-2 months | Manual from ONS |
| CA | CANCPIALLMINMEI | 1-2 months | Manual from StatCan |
| AU | AUSCPIALLQINMEI | 1-2 quarters | Quarterly OECD series; ABS now publishes monthly |
| NZ | NZLCPIALLQINMEI | 1-2 quarters | Quarterly only |
| ZA | ZAFCPIALLMINMEI | 3-6 months | Manual from Stats SA |
| VE | FPCPITOTLZGVEN | 6-12 months | IMF/BCV manual update |

### Discontinued / Broken FRED Series

| Country | Series | Issue | Fallback |
|---------|--------|-------|----------|
| JP | JPNCPALTT01IXNBM | COICOP 2018 (primary) | JPNCPIALLMINMEI (COICOP 1999, discontinued Jun 2021) |
| KR | KORCPALTT01IXNBM | COICOP 2018 (primary) | KORCPIALLMINMEI (COICOP 1999, discontinued Nov 2023) |
| SG | FPCPITOTLZGSGP | World Bank annual only | Manual from SingStat |

### Special Cases

- **Venezuela:** No inflation target (`target: null`). BCV publishes irregularly. Data relies on IMF.
- **Singapore:** MAS uses exchange rate policy (S$NEER band), not interest rates.
- **Australia:** Transitioned from quarterly to monthly CPI in late 2025. FRED still quarterly.
- **South Africa:** Target changed from 3-6% to 2-4% (3% midpoint) in Nov 2025.
- **Euro Area:** Uses ECB SDMX API directly (not FRED) — more timely than FRED.

---

## Session Recovery Guide

### 1. Check Current State
```bash
cd ~/Projects/inflation-dashboard

git log --oneline -5
git status

# Data freshness — see the dashboard freshness pills / Release Calendar tab,
# or inspect the JSON directly:
python3 -c "
import json
d = json.load(open('docs/data/historical_cpi.json'))
for c, v in d.items():
    if isinstance(v, dict) and v.get('latest'):
        print(f\"{c}: {v['latest']['date']} = {v['latest']['value']}\")
"

# CB forecast dates
python3 -c "
import json
with open('docs/data/cb_forecasts.json') as f:
    cb = json.load(f)
for code in cb.get('display_order', []):
    fc = cb['forecasts'].get(code, {})
    print(f\"{code}: {fc.get('publication_date', 'N/A')}\")
"
```

### 2. Check Automation
```bash
# GitHub Actions status
gh run list --limit 10

# Check if data was updated recently
git log --oneline --since="30 days ago" -- docs/data/historical_cpi.json
```

### 3. Test the Site
- Open https://jing-ny.github.io/inflation-dashboard/
- Verify all 15 countries appear in the table
- Check "As Of" dates — should be within the last 1-2 months
- Click Venezuela page (tests null target handling)

### 4. If Data Is Stale
```bash
# Run the automated fetch; if the source itself is broken, fix the fetcher
# or leave the value visibly stale (CLAUDE.md #1 — no manual entry).
python3 scripts/fetch_historical_cpi.py
```

---

## Useful Links

- **Dashboard:** https://jing-ny.github.io/inflation-dashboard/
- **GitHub repo:** https://github.com/jing-ny/inflation-dashboard
- **Actions:** https://github.com/jing-ny/inflation-dashboard/actions
- **Resend:** https://resend.com/emails
- **FRED:** https://fred.stlouisfed.org/
- **IMF DataMapper:** https://www.imf.org/external/datamapper/PCPIPCH@WEO
- **Substack:** https://inflationofficially.substack.com
- **Evaluation Report:** [docs/EVALUATION-REPORT.md](docs/EVALUATION-REPORT.md)

---

*This document should be updated whenever significant architectural changes are made.*
