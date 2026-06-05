# Inflation, Officially

**Official Data & Central Bank Expectations**

A lightweight, source-first monitor of inflation trends and central bank expectations across major economies.

🔗 **Live Dashboard:** https://jing-ny.github.io/inflation-dashboard/

---

## Why This Exists

Inflation data is everywhere, but it is often difficult to interpret in a consistent way.  
Figures are reported using different definitions, released on different schedules, and frequently mixed with commentary or opinion.

This project exists to cut through that noise.

It aggregates official inflation statistics and central bank projections in one place, with clear source attribution for every number, making cross-country comparison easier and more transparent.

---

## What This Project Does (and Does Not Do)

**What this project does:**

- Collects headline CPI inflation data from official government statistics agencies
- Displays central bank inflation expectations and projections where available
- Compares central bank forecasts with IMF World Economic Outlook projections
- Provides direct source links for every data point

**What this project does not do:**

- Provide analysis or commentary
- Make predictions
- Offer investment advice or policy recommendations

---

## Coverage

This dashboard tracks headline consumer price inflation (year-over-year) across 14 economies:

| Economy | Inflation Measure | Source | Central Bank |
|---------|-------------------|--------|--------------|
| 🇺🇸 United States | CPI (YoY) | Bureau of Labor Statistics | Federal Reserve |
| 🇪🇺 Euro Area | HICP (YoY) | Eurostat | ECB |
| 🇬🇧 United Kingdom | CPI (YoY) | ONS | Bank of England |
| 🇨🇦 Canada | CPI (YoY) | Statistics Canada | Bank of Canada |
| 🇦🇺 Australia | CPI (YoY) | ABS | RBA |
| 🇳🇿 New Zealand | CPI (YoY) | Stats NZ | RBNZ |
| 🇿🇦 South Africa | CPI (YoY) | Stats SA | SARB |
| 🇧🇷 Brazil | IPCA (YoY) | IBGE | BCB |
| 🇲🇽 Mexico | INPC (YoY) | INEGI | Banxico |
| 🇯🇵 Japan | CPI (YoY) | Statistics Bureau | Bank of Japan |
| 🇰🇷 South Korea | CPI (YoY) | KOSTAT | Bank of Korea |
| 🇸🇬 Singapore | CPI (YoY) | DOS | MAS |
| 🇮🇳 India | CPI (YoY) | MOSPI | RBI |
| 🇨🇳 China | CPI (YoY) | NBS | PBOC |

---

## Data Sources and Methodology

All data comes directly from official government statistics agencies or central bank publications.

Data sources are not forced into a single uniform pipeline.  
Instead, each economy uses the most stable and authoritative official source available.  
This approach prioritizes **stability and reproducibility** over uniformity.

Every figure displayed can be traced back to its original source.

Two practical constraints are worth knowing up front (both detailed in [METHODOLOGY.md](METHODOLOGY.md)):

- **Some countries lag.** US, Euro Area, UK, Canada and Australia pull from their primary national APIs and stay current; the rest come through **FRED's OECD relay, which re-publishes national CPI 1–3 months (sometimes more) late**. So a row can read amber/red even though the weekly updater ran fine — the data is simply as fresh as that relay allows.
- **Freshness colors are cadence-aware.** Pills age from the data point's *reference period*, with thresholds matched to monthly vs quarterly release schedules, so green ≈ "latest release", amber ≈ "a release behind", red ≈ "genuinely lagging".

For full detail — including why moving a country onto its national source depends on that API being reachable from GitHub's runners — see [METHODOLOGY.md](METHODOLOGY.md).

---

## Update Frequency

- **CPI Data:** Updated weekly, reflecting the most recent official releases
- **Central Bank Forecasts:** Updated after major monetary policy meetings
- **IMF Forecasts:** Updated twice yearly (April and October WEO releases)

Values may be revised by the original statistical agencies after publication.

---

## Data Architecture

All data is stored in `docs/data/` as the single source of truth:

```
docs/data/
├── historical_cpi.json       # CPI history for all 14 countries
├── cb_forecasts.json         # Central bank inflation forecasts
├── imf_forecasts.json        # IMF WEO projections
├── cpi_supplements.json      # Manual supplements for lagging FRED data
└── history/                  # Forecast revision tracking
```

### Keeping Data Current

Use `update.sh` for all manual updates. One command handles data entry, git commit, and push.

```bash
# Check what's current
./update.sh status

# When new CPI data comes out
./update.sh cpi
> US 2026-03 2.8
> UK 2026-02 2.9
> done
# Commits, pushes, and triggers newsletter draft automatically

# After a CB meeting with new projections
./update.sh forecast
# Opens cb_forecasts.json in your editor — edit, save, close
# Then confirms and pushes

# After IMF WEO release (April & October)
./update.sh imf
# Same flow — opens imf_forecasts.json for editing
```

Set `EDITOR=nano` or `EDITOR=vim` if you don't use VS Code.

### What's Automated

| What | When | How |
|------|------|-----|
| FRED/ECB CPI fetch | Every Monday | `update-data.yml` (commits if new data found) |
| Weekly change alert | Every Monday | `weekly-alert.yml` (emails if ≥0.3pp change) |
| CB forecast scrape | Mon & Thu | `auto-scrape-cb-forecasts.yml` (6 banks) |
| Newsletter draft | 1st of month + on CPI push | `newsletter-draft.yml` (Claude API → `docs/drafts/`) |

FRED lags official releases by 1-6 months for most countries, so manual CPI updates via `./update.sh cpi` remain necessary for timely data.

### Release Calendar

CPI data releases follow a predictable monthly pattern:

```
~1st:  KR          ~15th: UK
~9th:  CN          ~17th: CA, EA
~12th: IN          ~19th: ZA, JP
~13th: US          ~23rd: SG
                   ~28th: AU
Quarterly: NZ (mid-month of Jan/Apr/Jul/Oct)
```

See [CPI_UPDATE_GUIDE.md](CPI_UPDATE_GUIDE.md) for full procedures and official source URLs.

---

## Tech Stack

- **Frontend:** Static HTML/CSS/JavaScript (vanilla, no framework)
- **Hosting:** GitHub Pages
- **Data Fetching:** Python scripts using FRED API
- **Automation:** GitHub Actions (twice weekly checks)
- **Data Storage:** JSON files in `docs/data/`

---

## Local Development

```bash
# Clone the repository
git clone https://github.com/jing-ny/inflation-dashboard.git
cd inflation-dashboard

# View current CPI data
python3 update_cpi.py --show-all

# Start a local server
python3 -m http.server 8000 --directory docs
# Open http://localhost:8000
```

---

## Changelog

### April 2026
- Advanced CPI data to March 2026 for 8 countries; Feb backfill for UK and AU; Q1 2026 for NZ
- Refreshed IMF forecasts to WEO April 2026 (broad upside revisions from Middle East oil shock)
- Fixed BR/MX data contamination where prior-year comparison-text values were stored as current readings
- Added anomaly detection gates in `update_cpi.py` and `scripts/fetch_historical_cpi.py` (MoM step >1pp and exact prior-year match)
- Fixed `fetch_imf_forecasts.py`: 9→15 countries, corrected EA group code (`EURO`), fixed output directory

### March 2026
- Added Brazil and Mexico (now 15 countries)
- Updated all countries to Jan/Feb 2026 CPI data
- Updated CB forecasts to latest meetings (10 central banks)
- Added IMF forecasts side-by-side on homepage with divergence highlighting
- Added Core CPI + PCE tracking on US page
- Added table sorting, dynamic year columns
- Fixed 6 bugs: CSS duplication, broken scripts, FRED series mismatch
- Built newsletter automation (change detection, Claude API drafts, GitHub Actions)
- Added `update.sh` one-command update tool
- Cleaned up 12 legacy files, consolidated duplicate workflows

### February 2026
- Corrected Dec 2025 CPI values for 8 countries
- Consolidated data to `docs/data/` (single source of truth)
- Added `update_cpi.py` and `batch_update_cpi.py` manual update tools

### January 2026
- Added 5 new countries: South Korea, Singapore, India, China, Venezuela
- Implemented central bank forecast tracking and IMF WEO comparison
- Set up automated monitoring via GitHub Actions

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Contributing

Contributions welcome! Please open an issue first to discuss proposed changes.
