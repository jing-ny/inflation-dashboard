# CPI Data Verification Guide

## Quick Reference - Official Sources

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
| JP | JPNCPIALLMINMEI | Japan CPI |
| CN | CHNCPIALLMINMEI | China CPI |
| IN | INDCPIALLMINMEI | India CPI |
| KR | KORCPIALLMINMEI | South Korea CPI |
| SG | SGPCPIALLMINMEI | Singapore CPI |

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

## Monthly Update Workflow

1. Check release calendar at start of month
2. As each country releases, verify and update
3. After all major countries updated, commit changes
4. Push to deploy

## Release Calendar Template

```
January 2026:
  1st: KR (Dec 2025)
  9th: CN (Dec 2025)
  12th: IN (Dec 2025)
  13th: US (Dec 2025)
  15th: UK (Dec 2025)
  17th: CA (Dec 2025)
  19th: EA (Dec 2025 final), ZA (Dec 2025), JP (Dec 2025)
  22nd: NZ (Q4 2025)
  23rd: SG (Dec 2025)
  28th: AU (Dec 2025)
```
