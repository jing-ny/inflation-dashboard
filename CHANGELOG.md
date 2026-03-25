# Changelog

All notable changes to the Inflation Dashboard project are documented here.

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
