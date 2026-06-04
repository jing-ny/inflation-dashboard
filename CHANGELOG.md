# Changelog

All notable changes to the Inflation Dashboard project are documented here.

---

## [Unreleased]

### Fixed
- **Misleading "stale" freshness signal on CN & VE (#43, #44):** the China and Venezuela
  Outlook rows are IMF-sourced (PBoC/BCV publish no standardized inflation forecast), but
  their `publication_date` was a frozen manual string that aged red — implying a broken
  scraper where none exists. These rows now carry `scraper_status: "imf_sourced"` and are
  auto-synced from `imf_forecasts.json` on every IMF refresh (April/October cadence), with
  full provenance (`source_url`, `source_date`) on the record. The Outlook table renders a
  distinct neutral "IMF WEO {edition}" badge instead of a red pill — and still ages to red
  if the IMF pipeline itself stalls. VE's curated 2026 figure (80%) was corrected to the
  current WEO value (387.4%) as a side effect of the sync.

### Added
- **MAS Survey of Professional Forecasters scraper (#42):** new `scrape_mas()` in
  `auto_scrape_cb_forecasts.py` discovers the latest quarterly SPF write-up PDF and
  extracts the headline **CPI-All Items median** from the explicitly-labelled annual
  "Median Mean Min Max" table (via `pdfplumber`), anchoring on that table rather than
  regex-grepping prose. SG is now in `COUNTRY_SCRAPERS`; `pdfplumber` added to the
  workflow deps. MAS's WAF rejects the default UA, so a browser `BROWSER_HEADERS` is
  threaded through the fetch helpers (the other scrapers keep the honest UA). The
  current calendar year — which the write-up only presents in distribution/quarterly
  tables — is preserved by overlaying scraped year(s) onto the existing SG projections,
  so the year-ahead median auto-refreshes each quarter and the row's `publication_date`
  stops drifting amber/red between releases. Validated end-to-end against live MAS via
  the auto-scrape workflow.
- **`fetch_imf_forecasts.py` → `sync_imf_sourced_cb_forecasts()`:** keeps any row flagged
  `scraper_status: "imf_sourced"` in `cb_forecasts.json` in lockstep with the IMF WEO data,
  so IMF-backed CB rows refresh automatically rather than drifting stale (CLAUDE.md #1/#3/#4).
- **`imfSourcedPill()` freshness helper** + `.freshness-imf` style for the new badge.

---

## [1.3.0] - 2026-04-22

### Changed
- **CPI Data:** Advanced all 15 countries to March 2026 where releases were available:
  - **March 2026**: US (3.26% precise), EA 2.6% (final), CA 2.4%, CN 1.0%, IN 3.4%, KR 2.2%, BR 4.14%, MX 4.59%
  - **February 2026 backfill**: UK 3.0% (prior round missed this), AU 3.7% (monthly indicator)
  - **Q1 2026**: NZ 3.1%
  - Still pending at release: UK March, JP (releases Apr 24), SG (~Apr 23), ZA (release lag), VE (irregular)
- **IMF Forecasts:** Updated to WEO April 2026 (released Apr 14). Broad upside revisions driven by Middle East conflict oil-price shock: US +0.8pp, EA +0.7pp, UK +0.7pp, AU/NZ +1.0pp, SG +0.8pp, VE re-rated to 387.4%.

### Fixed
- **BR/MX miscapture (data-quality):** Corrected BR 2026-02 (5.06% → 3.81%) and MX 2026-02 (3.77% → 4.02%). Prior values were the same-month prior-year figures referenced in IBGE/INEGI comparison text, accidentally stored as the current-month reading. BR/MX 2026-01 similarly corrected (BR 4.56% → 4.44%, MX 3.59% → 3.79%).
- **`fetch_imf_forecasts.py`**: covered only 9 countries, used wrong Euro Area code (`EMU` returns empty; correct code is `EURO` group), and wrote to `./data/` instead of `./docs/data/`. Now covers all 15 countries with correct codes and path; preserves curated `note`, `display_order`, and `url` on refresh.
- **`update_cpi.py` emoji encoding:** `save_data` now writes `ensure_ascii=False`, preventing rebase conflicts with automated commits that use raw unicode flag emojis.

### Added
- **Anomaly detection gates (data-quality hardening):**
  - `update_cpi.py` blocks manual updates where MoM step > 1.0pp **or** the new value exactly matches the same month one year earlier (the BR/MX miscapture pattern). Override with `--confirm-anomaly`.
  - `scripts/fetch_historical_cpi.py` logs the same anomalies to `docs/data/cpi_anomalies.json` and exits 2 so CI surfaces bad pulls instead of silently merging them.

---

## [1.2.0] - 2026-03-24

### Changed
- **CPI Data:** Updated all 15 countries to Jan/Feb 2026 (UK/AU to Jan, NZ to Q4 2025)
- **CB Forecasts:** Updated 10 central banks to latest meetings (Fed Mar, ECB Mar, BoE Feb, BoC Jan, RBA Feb+Mar, RBNZ Feb, SARB Jan, BoJ Mar, RBI Feb, BOK Feb)
- **IMF Forecasts:** Updated to WEO January 2026 Update; added 6 missing countries (EA, JP, IN, KR, SG, VE)
- **Homepage:** Renamed "Central Bank Outlook" to "Inflation Outlook" with side-by-side CB vs IMF forecasts and divergence highlighting
- **Australia policy rate:** Corrected to 4.10% after two consecutive hikes (Feb + Mar 2026)
- **South Africa forecast:** Corrected 2026 projection to 3.3% (Jan 2026 QPM revision)

### Fixed
- Deduplicated `styles.css` (1279 → 604 lines; 4 redundant CSS blocks removed)
- Removed stray "test" text from `index.html`
- Fixed `send_weekly_alert.py` data path and key structure (was completely non-functional)
- Added argparse to `auto_scrape_cb_forecasts.py` (`--force`, `--country`, `--dry-run`)
- Unified FRED series between `monitor_updates.py` and `fetch_historical_cpi.py`
- Implemented `update_forecast_history()` in `monitor_updates.py` (was placeholder)
- Fixed monitor workflow commit failure (added `permissions: contents: write`)
- Re-enabled SSL verification in CB scraper (was insecurely disabled)
- Removed hardcoded 2024 fallback URLs from CB scraper (now discovers latest from index pages)
- Updated JP/KR FRED series to COICOP 2018 (JPNCPALTT01IXNBM, KORCPALTT01IXNBM)
- Rotated all API keys (FRED, Resend, Anthropic)

### Added
- IMF forecasts comparison on homepage (CB vs IMF side-by-side)
- Geopolitical context banner (Iran war / Strait of Hormuz impact on forecasts)
- Q1 2026 newsletter draft (`docs/drafts/2026-Q1-newsletter.md`)
- Brazil and Mexico (now 15 countries total)
- Newsletter automation: Claude API draft generation + GitHub Actions (`newsletter-draft.yml`)
- `update.sh` one-command update tool for CPI, CB forecasts, and IMF data
- 5 new countries in `historical_cpi.json`: Japan, India, South Korea, Singapore, Venezuela

### Removed
- Obsolete `docs/project_plan.md` (superseded by `PROJECT_PLAN.md`)
- Empty `docs/data_sources.md`
- `MAINTENANCE.md` (consolidated into `CPI_UPDATE_GUIDE.md`)

---

## [1.1.0] - 2026-02-03

### Changed
- **Data Quality Fix:** Corrected Dec 2025 CPI values for 8 countries using verified official sources
- **Architecture:** Consolidated all data to `docs/data/` (single source of truth)

### Added
- `update_cpi.py` and `batch_update_cpi.py` manual update tools
- `CPI_UPDATE_GUIDE.md` with official source URLs and release schedules

---

## [1.0.1] - 2026-01-26

### Changed
- **South Africa:** Updated inflation target from 4.5% (3-6% range) to 3.0% (2-4% range)
  - First target change in 25 years, announced November 12, 2025
  - Added Policy Updates timeline section to za.html

### Added
- **Japan (JP):** Full integration with country page, 10-year history, BoJ forecasts

---

## [1.0.0] - 2026-01-26

### Initial Release
- Dashboard tracking official CPI inflation and central bank forecasts across 9 economies
- Overview page with inflation table, Central Bank Outlook, Policy Rates grid
- Country detail pages with 10-year charts, forecast comparisons, target info
- JSON-based data architecture (`historical_cpi.json`, `cb_forecasts.json`, `imf_forecasts.json`)
- Data from FRED API, ECB API, and official central bank publications

---

## Links

- **Live Site**: https://jing-ny.github.io/inflation-dashboard/
- **Repository**: https://github.com/jing-ny/inflation-dashboard
- **Issues**: https://github.com/jing-ny/inflation-dashboard/issues
