# Data Update Guide

This is the single reference for all manual data updates: CPI, central bank forecasts, and IMF forecasts.

---

## CPI: Official Sources

| Country | Agency | URL | Release Day |
|---------|--------|-----|-------------|
| US | Bureau of Labor Statistics | https://www.bls.gov/cpi/ | ~13th |
| EA | Eurostat | https://ec.europa.eu/eurostat/ | ~17th-19th |
| UK | ONS | https://www.ons.gov.uk/economy/inflationandpriceindices | ~15th |
| CA | Statistics Canada | https://www150.statcan.gc.ca/n1/daily-quotidien/index-eng.htm | ~17th |
| AU | ABS | https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/ | ~28th |
| NZ | Stats NZ | https://www.stats.govt.nz/indicators/consumers-price-index-cpi/ | Quarterly |
| ZA | Stats SA | https://www.statssa.gov.za/ | ~19th |
| JP | Statistics Bureau | https://www.stat.go.jp/english/data/cpi/ | ~19th |
| CN | NBS | https://www.stats.gov.cn/english/ | ~9th |
| IN | MOSPI | https://www.mospi.gov.in/ | ~12th |
| KR | KOSTAT | https://kostat.go.kr/ | ~1st |
| SG | SingStat | https://www.singstat.gov.sg/ | ~23rd |
| BR | IBGE | https://www.ibge.gov.br/en/statistics/economic/prices-and-costs.html | ~10th |
| MX | INEGI | https://www.inegi.org.mx/temas/inpc/ | ~9th |
| VE | BCV | https://www.bcv.org.ve/ | Irregular |

## FRED Series (for automated fetching)

These FRED series can be used for automated data retrieval, but note that FRED data may lag official releases by days or weeks.

| Country | FRED Series | Notes |
|---------|-------------|-------|
| US | CPIAUCNS | CPI for All Urban Consumers |
| EA | CP0000EZ19M086NEST | Euro Area HICP |
| UK | GBRCPIALLMINMEI | UK CPI All Items |
| CA | CANCPIALLMINMEI | Canada CPI All Items |
| AU | AUSCPIALLQINMEI | Australia CPI (was quarterly, now monthly) |
| NZ | NZLCPIALLQINMEI | New Zealand CPI (quarterly) |
| ZA | ZAFCPIALLMINMEI | South Africa CPI |
| JP | JPNCPALTT01IXNBM | Japan CPI (COICOP 2018) |
| CN | CHNCPIALLMINMEI | China CPI |
| IN | INDCPIALLMINMEI | India CPI |
| KR | KORCPALTT01IXNBM | South Korea CPI (COICOP 2018) |
| SG | FPCPITOTLZGSGP | Singapore CPI (World Bank annual) |
| BR | BRACPIALLMINMEI | Brazil CPI |
| MX | MEXCPIALLMINMEI | Mexico CPI |

## Verification Checklist

When updating CPI data:

1. [ ] Go to the official source URL
2. [ ] Find the press release for the target month
3. [ ] Locate the headline YoY inflation rate
4. [ ] Note: US uses CPI-U, UK uses CPI (not CPIH), EA uses HICP
5. [ ] Update using: `python3 update_cpi.py -c XX -d YYYY-MM -v X.X`
6. [ ] Verify the dashboard displays correctly

## Common Gotchas

### United States
- Oct 2025 data missing due to government shutdown
- BLS reports CPI-U (all urban consumers) - this is what we track
- Core CPI (excludes food & energy) is different from headline

### Euro Area
- We track HICP (Harmonized Index of Consumer Prices)
- Flash estimates come early (~end of month), final data ~17th
- EA composition changed (Croatia joined 2023, Poland 2025)

### United Kingdom
- Track CPI, not CPIH (which includes owner-occupier housing costs)
- ONS releases both - we want the CPI figure

### Australia
- Transitioned to monthly CPI in late 2025
- Historical data is quarterly
- Target is 2-3% band, midpoint 2.5%

### New Zealand
- Still quarterly releases
- Target is 1-3% band, midpoint 2%

### South Africa
- SARB changed target to 3% in 2025 (from 3-6% range)

### India
- Very volatile due to food weights (~46% of basket)
- RBI target is 4% with +/-2% tolerance

### China
- Government target is "around 3%" but rarely binding
- Often near zero or negative in recent years

## CPI Monthly Update Workflow

1. Check release calendar at start of month
2. As each country releases, verify and update
3. After all major countries updated, commit and push

```bash
# Recommended: use update.sh (handles commit + push automatically)
./update.sh cpi
> US 2026-03 2.5
> UK 2026-02 2.9
> done

# Or manually:
python3 update_cpi.py -c US -d 2026-03 -v 2.5
git add docs/data/historical_cpi.json
git commit -m "Update CPI data: US Mar 2026"
git push
```

---

## Central Bank Forecast Updates

**When:** After major MPC meetings with new projections.

| Country | Bank | Months with Projections |
|---------|------|------------------------|
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

**How:** Edit `docs/data/cb_forecasts.json` — update `publication_date`, `projections`, `policy_rate`, `key_quote`, `note`.

```bash
git add docs/data/cb_forecasts.json
git commit -m "Update US CB forecast after Mar 2026 FOMC"
git push
```

---

## IMF Forecast Updates

**When:** April and October (WEO releases).

**Source:** https://www.imf.org/external/datamapper/PCPIPCH@WEO

**How:** Edit `docs/data/imf_forecasts.json` — update `version`, `retrieved`, and all country forecast values.

```bash
git add docs/data/imf_forecasts.json
git commit -m "Update IMF WEO forecasts (April 2026)"
git push
```

---

## Troubleshooting

- **FRED data not updating:** FRED OECD series lag 1-6 months. Use `update_cpi.py` with official source values.
- **Venezuela page not loading:** Check `target: null` handling in country.js.
- **Email notifications not arriving:** Check Resend dashboard, verify `NOTIFICATION_EMAIL` GitHub secret.
- **GitHub Actions failing:** Check Actions tab. Common issue: quarterly date format (2025-Q4).

---

## Release Calendar Template

```
Monthly pattern:
  1st:  KR
  9th:  CN, MX
  10th: BR
  12th: IN
  13th: US
  15th: UK
  17th: CA, EA (final)
  19th: ZA, JP
  23rd: SG
  28th: AU
  Quarterly: NZ (mid-month of Jan/Apr/Jul/Oct)
```
