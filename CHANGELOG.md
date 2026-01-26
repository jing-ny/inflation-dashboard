# Changelog

All notable changes to the Inflation Dashboard project are documented here.

---

## [1.0.0] - 2026-01-26

### 🎉 Initial Release

The first complete version of the Inflation Dashboard, tracking official inflation statistics and central bank forecasts across 9 major economies.

### Countries Covered
- 🇺🇸 United States (Fed)
- 🇪🇺 Euro Area (ECB)
- 🇬🇧 United Kingdom (BoE)
- 🇨🇦 Canada (BoC)
- 🇦🇺 Australia (RBA)
- 🇳🇿 New Zealand (RBNZ)
- 🇿🇦 South Africa (SARB)
- 🇯🇵 Japan (BoJ)
- 🇨🇳 China (PBoC/NBS)

### Features
- **Overview Page**: Current inflation table, Central Bank Outlook table, Policy Rates grid
- **Country Pages**: 10-year historical charts, forecast comparisons (CB vs IMF), target information, official sources
- **Data Architecture**: JSON-based data files for easy updates
  - `historical_cpi.json` - 10-year CPI history per country
  - `cb_forecasts.json` - Central bank projections and policy rates
  - `imf_forecasts.json` - IMF World Economic Outlook data
- **Policy Change Tracking**: Alert boxes, timeline sections, and "NEW" badges for recent target changes

### Data Sources
- FRED API (St. Louis Fed)
- BLS API (US Bureau of Labor Statistics)
- ECB Data Portal (Euro Area HICP)
- Official central bank publications
- IMF World Economic Outlook

---

## [1.0.1] - 2026-01-26

### Changed
- **South Africa**: Updated inflation target from 4.5% (3-6% range) to **3.0%** (2-4% range)
  - First target change in 25 years, announced November 12, 2025
  - Added Policy Updates timeline section to za.html
  - Added "NEW" badge on index page target column
  - Added policy change alert box in target info section

### Added
- **Japan (JP)**: Full integration
  - Country page (jp.html)
  - 10-year historical CPI data
  - BoJ forecasts (January 2026 Outlook)
  - Policy rate: 0.75%

---

## Roadmap

### Planned Features
- [ ] Email subscription for quarterly newsletter
- [ ] Automated data updates via GitHub Actions
- [ ] Additional countries (Switzerland, Germany, Singapore, India)
- [ ] RSS feed for policy changes

### Under Consideration
- [ ] Dark mode
- [ ] Data export (CSV download)
- [ ] Comparison charts across countries
- [ ] Mobile app wrapper

---

## Versioning

This project uses [Semantic Versioning](https://semver.org/):
- **Major** (1.x.x): New countries, major feature additions
- **Minor** (x.1.x): New data visualizations, UI improvements
- **Patch** (x.x.1): Data updates, bug fixes, target changes

---

## Links

- **Live Site**: https://jing-ny.github.io/inflation-dashboard/
- **Repository**: https://github.com/jing-ny/inflation-dashboard
- **Issues**: https://github.com/jing-ny/inflation-dashboard/issues
