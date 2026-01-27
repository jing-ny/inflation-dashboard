# Inflation Dashboard - Maintenance Guide

This guide covers the manual updates needed to keep the dashboard current.

## Automation Status

**Automated (runs Mon & Thu 9am UTC):**
- ✅ CPI data updates from FRED
- ✅ Stale data alerts
- ✅ CB meeting reminders
- ✅ IMF WEO release reminders
- ✅ Email notifications via Resend

**Manual (you do these):**
- Central bank forecast updates after MPC meetings
- IMF forecast updates (April & October)

---

## Manual Task 1: Central Bank Forecast Updates

### When to Update
After major central bank meetings that include new projections:

| Country | Bank | Typical Schedule |
|---------|------|------------------|
| 🇺🇸 US | FOMC | Mar, Jun, Sep, Dec (with SEP) |
| 🇪🇺 EA | ECB | Mar, Jun, Sep, Dec (staff projections) |
| 🇬🇧 UK | BoE | Feb, May, Aug, Nov (MPR) |
| 🇨🇦 CA | BoC | Jan, Apr, Jul, Oct (MPR) |
| 🇦🇺 AU | RBA | Feb, May, Aug, Nov (SoMP) |
| 🇳🇿 NZ | RBNZ | Feb, May, Aug, Nov (MPS) |
| 🇿🇦 ZA | SARB | Jan, Mar, May, Jul, Sep, Nov |
| 🇯🇵 JP | BoJ | Jan, Apr, Jul, Oct (Outlook Report) |
| 🇰🇷 KR | BOK | Feb, May, Aug, Nov |
| 🇸🇬 SG | MAS | Apr, Oct (policy statement) |
| 🇮🇳 IN | RBI | Feb, Apr, Jun, Aug, Oct, Dec |

### How to Update

1. **Find the new forecast** on the central bank's website
2. **Edit `docs/data/cb_forecasts.json`**
3. **Update these fields** for the country:

```json
"US": {
  "source": "FOMC",
  "source_full": "Federal Reserve",
  "publication_date": "December 2025",      // ← Update this
  "source_url": "https://...",
  "forecast_type": "Median SEP Projection",
  "projections": {
    "2025": 2.8,                              // ← Update these
    "2026": 2.5,
    "2027": 2.2,
    "longer_run": 2.0
  },
  "policy_rate": {
    "rate": "4.25-4.50%",                    // ← Update if changed
    "last_change": "↓ 25bp Dec 2025"         // ← Update if changed
  },
  "key_quote": "...",                         // ← Update quote
  "note": "FOMC SEP, December 2025"          // ← Update date
}
```

4. **Commit and push:**
```bash
cd ~/Projects/inflation-dashboard
git add docs/data/cb_forecasts.json
git commit -m "Update [COUNTRY] CB forecast after [MONTH] meeting"
git push
```

### Optional: Update Forecast History

After updating cb_forecasts.json, append to `docs/data/history/cb_forecast_history.json`:

```json
{
  "snapshot_date": "2026-02-15",
  "source": "Post-FOMC February 2026",
  "forecasts": {
    "US": {
      "2026": 2.4,
      "2027": 2.1,
      "policy_rate": "4.00-4.25%"
    }
  }
}
```

---

## Manual Task 2: IMF Forecast Updates

### When to Update
Twice per year when IMF releases World Economic Outlook:
- **April** (Spring WEO)
- **October** (Fall WEO)

### How to Update

1. **Go to:** https://www.imf.org/external/datamapper/PCPIPCH@WEO/WEOWORLD
2. **Select each country** and note the forecast values for 2025-2029
3. **Edit `docs/data/imf_forecasts.json`:**

```json
{
  "source": "IMF World Economic Outlook",
  "version": "April 2026",                    // ← Update this
  "retrieved": "2026-04-15",                  // ← Update this
  "url": "https://www.imf.org/external/datamapper/PCPIPCH@WEO",
  "countries": {
    "US": {
      "name": "United States",
      "forecasts": {
        "2025": 2.8,                          // ← Update all values
        "2026": 2.4,
        "2027": 2.2,
        "2028": 2.1,
        "2029": 2.0
      }
    },
    // ... repeat for all 13 countries
  }
}
```

4. **Commit and push:**
```bash
cd ~/Projects/inflation-dashboard
git add docs/data/imf_forecasts.json
git commit -m "Update IMF WEO forecasts (April 2026)"
git push
```

---

## Quick Reference: File Locations

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `docs/data/historical_cpi.json` | CPI data | Auto (FRED) |
| `docs/data/cb_forecasts.json` | Central bank forecasts | After MPC meetings |
| `docs/data/imf_forecasts.json` | IMF forecasts | April & October |
| `docs/data/history/cb_forecast_history.json` | CB forecast snapshots | Optional |
| `docs/data/history/imf_forecast_history.json` | IMF forecast snapshots | Optional |

---

## Troubleshooting

### Venezuela page not loading
- Check `target: null` handling in country.js
- VE has no inflation target, code must handle null

### FRED data not updating
- Some series (JP, SG) have API limitations
- Check FRED website directly for latest data
- Manual update: edit `historical_cpi.json`

### Email notifications not arriving
- Check Resend dashboard for delivery status
- Verify `NOTIFICATION_EMAIL` GitHub secret
- Check spam folder

### GitHub Actions failing
- Check Actions tab for error logs
- Common issue: quarterly date format (2025-Q4)

---

## Useful Links

- **Dashboard:** https://jing-ny.github.io/inflation-dashboard/
- **GitHub repo:** https://github.com/jing-ny/inflation-dashboard
- **Actions:** https://github.com/jing-ny/inflation-dashboard/actions
- **Resend:** https://resend.com/emails
- **FRED:** https://fred.stlouisfed.org/
- **IMF DataMapper:** https://www.imf.org/external/datamapper/PCPIPCH@WEO
