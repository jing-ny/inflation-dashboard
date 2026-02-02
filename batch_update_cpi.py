#!/usr/bin/env python3
"""
Batch CPI Update Script - For Monthly Data Releases
====================================================

This script provides a structured way to update all countries when new CPI data is released.

Typical Release Schedule:
-------------------------
- US: ~13th of month (for previous month)
- UK: ~15th of month (for previous month)
- EA: ~17th-19th of month (for previous month)
- CA: ~17th of month (for previous month)
- AU: Monthly now, ~28th of month
- NZ: Quarterly (~Jan 22, Apr 22, Jul 22, Oct 22)
- ZA: ~19th of month
- JP: ~19th of month (for previous month)
- CN: ~9th of month (for previous month)
- IN: ~12th of month (for previous month)
- KR: ~1st of month (for previous month)
- SG: ~23rd of month (for previous month)
- VE: Irregular

Usage:
------
1. Edit the UPDATES dict below with new values
2. Run: python3 batch_update_cpi.py
3. Review changes and confirm
"""

import json
from datetime import datetime
from pathlib import Path

# Path to the data file
DATA_FILE = Path(__file__).parent / "docs" / "data" / "historical_cpi.json"

# ============================================================================
# EDIT THIS SECTION WITH NEW DATA
# ============================================================================
# Format: "COUNTRY_CODE": {"date": "YYYY-MM", "value": X.X, "previous": Y.Y}
# previous is optional - if omitted, uses old latest value

UPDATES = {
    # Example - uncomment and modify:
    # "US": {"date": "2026-01", "value": 2.8},
    # "UK": {"date": "2026-01", "value": 3.5, "previous": 3.4},
    # "EA": {"date": "2026-01", "value": 2.1},
}

# For quarterly countries (AU, NZ), use format "YYYY-QN"
# Example: "NZ": {"date": "2026-Q1", "value": 3.2}

# ============================================================================
# DO NOT EDIT BELOW THIS LINE
# ============================================================================

def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def apply_updates(data, updates, dry_run=True):
    """Apply updates to data."""
    changes = []
    
    for country_code, update in updates.items():
        if country_code not in data:
            print(f"⚠ Warning: Country '{country_code}' not found, skipping")
            continue
        
        c = data[country_code]
        old_latest = c['latest'].copy()
        
        # Determine previous value
        if 'previous' in update:
            new_previous = {"date": old_latest['date'], "value": update['previous']}
        else:
            new_previous = old_latest
        
        # New latest
        new_latest = {"date": update['date'], "value": update['value']}
        
        # Record change
        changes.append({
            'country': country_code,
            'name': c['name'],
            'old_latest': old_latest,
            'new_latest': new_latest,
            'new_previous': new_previous
        })
        
        if not dry_run:
            c['previous'] = new_previous
            c['latest'] = new_latest
            
            # Add to history
            history_dates = [h['date'] for h in c.get('history', [])]
            if update['date'] not in history_dates:
                c['history'].append({"date": update['date'], "value": update['value']})
                c['history'].sort(key=lambda x: x['date'])
            else:
                for h in c['history']:
                    if h['date'] == update['date']:
                        h['value'] = update['value']
                        break
    
    if not dry_run:
        data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    
    return changes

def print_changes(changes):
    """Print formatted change summary."""
    print("\n" + "="*70)
    print("PROPOSED CHANGES")
    print("="*70)
    
    for ch in changes:
        print(f"\n{ch['name']} ({ch['country']}):")
        print(f"  Old: {ch['old_latest']['value']}% ({ch['old_latest']['date']})")
        print(f"  New: {ch['new_latest']['value']}% ({ch['new_latest']['date']})")
        print(f"  Previous will be: {ch['new_previous']['value']}% ({ch['new_previous']['date']})")

def main():
    if not UPDATES:
        print("No updates defined. Edit the UPDATES dict in this script.")
        print("\nExample:")
        print('UPDATES = {')
        print('    "US": {"date": "2026-01", "value": 2.8},')
        print('    "UK": {"date": "2026-01", "value": 3.5},')
        print('}')
        return
    
    data = load_data()
    
    # Dry run first
    changes = apply_updates(data, UPDATES, dry_run=True)
    print_changes(changes)
    
    # Confirm
    print("\n" + "="*70)
    response = input("Apply these changes? (y/n): ").strip().lower()
    
    if response == 'y':
        # Reload and apply for real
        data = load_data()
        apply_updates(data, UPDATES, dry_run=False)
        save_data(data)
        print("\n✓ All updates applied successfully!")
        print(f"✓ Data saved to {DATA_FILE}")
    else:
        print("\n✗ Cancelled - no changes made")

if __name__ == "__main__":
    main()
