#!/usr/bin/env python3
"""
Manual CPI Update Script for Inflation Dashboard
=================================================

Usage:
  python3 update_cpi.py --country US --date 2025-12 --value 2.7
  python3 update_cpi.py --country UK --date 2025-12 --value 3.4 --previous-value 3.2
  python3 update_cpi.py --show US  # Show current values for a country
  python3 update_cpi.py --show-all  # Show all countries

This script updates the historical_cpi.json file with new CPI values.
Always verify values against official sources before updating.

Official Sources:
  US: https://www.bls.gov/cpi/
  EA: https://ec.europa.eu/eurostat/
  UK: https://www.ons.gov.uk/economy/inflationandpriceindices
  CA: https://www.statcan.gc.ca/
  AU: https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/
  NZ: https://www.stats.govt.nz/indicators/consumers-price-index-cpi/
  ZA: https://www.statssa.gov.za/
  JP: https://www.stat.go.jp/english/data/cpi/
  CN: https://www.stats.gov.cn/english/
  IN: https://www.mospi.gov.in/
  KR: https://kostat.go.kr/
  SG: https://www.singstat.gov.sg/
  VE: https://www.bcv.org.ve/
"""

import json
import argparse
import sys
from datetime import datetime
from pathlib import Path

# Path to the data file
DATA_FILE = Path(__file__).parent / "docs" / "data" / "historical_cpi.json"

COUNTRY_CODES = ["US", "EA", "UK", "CA", "AU", "NZ", "ZA", "JP", "CN", "IN", "KR", "SG", "VE"]


def load_data():
    """Load the CPI data file."""
    with open(DATA_FILE, 'r') as f:
        return json.load(f)


def save_data(data):
    """Save the CPI data file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(f"✓ Data saved to {DATA_FILE}")


def show_country(data, country_code):
    """Display current values for a country."""
    if country_code not in data:
        print(f"Error: Country '{country_code}' not found")
        return
    
    c = data[country_code]
    print(f"\n{'='*50}")
    print(f"{c.get('flag', '')} {c['name']} ({country_code})")
    print(f"{'='*50}")
    print(f"Target: {c.get('target', 'N/A')}%")
    print(f"Source: {c.get('source', 'N/A')} - {c.get('source_url', '')}")
    print(f"Frequency: {c.get('frequency', 'monthly')}")
    print(f"\nLatest: {c['latest']['value']}% ({c['latest']['date']})")
    print(f"Previous: {c['previous']['value']}% ({c['previous']['date']})")
    
    if c.get('notes'):
        print(f"\nNotes: {c['notes']}")
    
    print(f"\nRecent history (last 6):")
    for h in c.get('history', [])[-6:]:
        print(f"  {h['date']}: {h['value']}%")


def show_all(data):
    """Show summary for all countries."""
    print(f"\n{'Country':<25} {'Latest':>8} {'Date':>10} {'Previous':>8} {'Target':>8}")
    print("-" * 65)
    for code in COUNTRY_CODES:
        if code in data:
            c = data[code]
            latest = c['latest']
            prev = c['previous']
            target = c.get('target', 'N/A')
            target_str = f"{target}%" if target else "N/A"
            print(f"{c.get('flag','')} {c['name']:<22} {latest['value']:>7}% {latest['date']:>10} {prev['value']:>7}% {target_str:>8}")


STEP_THRESHOLD_PP = 1.0  # YoY inflation rarely shifts >1pp month-over-month; flag if it does


def _prior_year_value(history, date):
    """Return the history value for the same month/quarter in the prior year, or None."""
    if '-Q' in date:
        year, q = date.split('-Q')
        prior = f"{int(year) - 1}-Q{q}"
    else:
        year, month = date.split('-')
        prior = f"{int(year) - 1}-{month}"
    for h in history:
        if h['date'] == prior:
            return h['value']
    return None


def check_anomaly(country_code, date, value, current_latest, history):
    """Return a list of (severity, message) for suspicious updates."""
    warnings = []
    if current_latest and isinstance(current_latest.get('value'), (int, float)):
        delta = abs(value - current_latest['value'])
        if delta > STEP_THRESHOLD_PP:
            warnings.append(
                (
                    'step',
                    f"MoM step {value - current_latest['value']:+.2f}pp "
                    f"({current_latest['value']}% → {value}%) exceeds {STEP_THRESHOLD_PP}pp threshold",
                )
            )
    prior_year = _prior_year_value(history, date)
    if prior_year is not None and abs(value - prior_year) < 0.01:
        warnings.append(
            (
                'prior_year_match',
                f"Value {value}% exactly matches prior-year same-period ({prior_year}%) — "
                f"possible miscapture of comparison-text figure",
            )
        )
    return warnings


def update_country(data, country_code, date, value, previous_value=None, confirm_anomaly=False):
    """Update CPI value for a country."""
    if country_code not in data:
        print(f"Error: Country '{country_code}' not found")
        return False

    c = data[country_code]
    old_latest = c['latest'].copy()

    warnings = check_anomaly(country_code, date, value, old_latest, c.get('history', []))
    if warnings and not confirm_anomaly:
        print(f"\n⚠  Anomaly detected updating {c['name']} ({country_code}) {date} = {value}%:")
        for _, msg in warnings:
            print(f"   - {msg}")
        print(f"\n   Re-run with --confirm-anomaly to proceed, or double-check the official source.")
        return False
    if warnings and confirm_anomaly:
        print(f"\n⚠  Anomaly noted (proceeding with --confirm-anomaly):")
        for _, msg in warnings:
            print(f"   - {msg}")

    # Update previous with old latest (if not explicitly provided)
    if previous_value is None:
        c['previous'] = old_latest
    else:
        c['previous'] = {"date": c['latest']['date'], "value": previous_value}

    # Update latest
    c['latest'] = {"date": date, "value": value}
    
    # Add to history if not already present
    history_dates = [h['date'] for h in c.get('history', [])]
    if date not in history_dates:
        c['history'].append({"date": date, "value": value})
        # Sort history by date
        c['history'].sort(key=lambda x: x['date'])
    else:
        # Update existing history entry
        for h in c['history']:
            if h['date'] == date:
                h['value'] = value
                break
    
    # Update metadata
    data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\n✓ Updated {c['name']} ({country_code}):")
    print(f"  Latest: {value}% ({date})")
    print(f"  Previous: {c['previous']['value']}% ({c['previous']['date']})")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Update CPI values in the inflation dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--country', '-c', type=str, help='Country code (e.g., US, UK, EA)')
    parser.add_argument('--date', '-d', type=str, help='Date (e.g., 2025-12 or 2025-Q4)')
    parser.add_argument('--value', '-v', type=float, help='CPI value (e.g., 2.7)')
    parser.add_argument('--previous-value', '-p', type=float, help='Previous value (optional, defaults to old latest)')
    parser.add_argument('--show', '-s', type=str, help='Show current values for a country')
    parser.add_argument('--show-all', '-a', action='store_true', help='Show summary for all countries')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without saving')
    parser.add_argument('--confirm-anomaly', action='store_true', help='Proceed even when anomaly checks fire')
    
    args = parser.parse_args()
    
    # Load data
    data = load_data()
    
    # Handle show commands
    if args.show:
        show_country(data, args.show.upper())
        return
    
    if args.show_all:
        show_all(data)
        return
    
    # Handle update
    if args.country and args.date and args.value is not None:
        country = args.country.upper()
        if update_country(data, country, args.date, args.value, args.previous_value, confirm_anomaly=args.confirm_anomaly):
            if args.dry_run:
                print("\n[DRY RUN - Changes not saved]")
            else:
                save_data(data)
                print("\n✓ Update complete!")
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python3 update_cpi.py --show US")
        print("  python3 update_cpi.py --show-all")
        print("  python3 update_cpi.py -c US -d 2026-01 -v 2.8")
        print("  python3 update_cpi.py -c UK -d 2026-01 -v 3.5 -p 3.4")


if __name__ == "__main__":
    main()
