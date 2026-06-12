#!/usr/bin/env python3
"""
Monitor data freshness and fetch updates for inflation dashboard.
Checks FRED API, IMF WEO, and tracks central bank meeting schedules.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import requests

FRED_API_KEY = os.environ.get('FRED_API_KEY')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# FRED series for each country
FRED_SERIES = {
    'US': 'CPIAUCNS',              # CPI-U All Urban Consumers, NSA (index)
    'EA': 'CP0000EZ19M086NEST',
    'UK': 'GBRCPIALLMINMEI',
    'CA': 'CANCPIALLMINMEI',
    'AU': 'AUSCPIALLQINMEI',
    'NZ': 'NZLCPIALLQINMEI',
    'ZA': 'ZAFCPIALLMINMEI',
    'JP': 'JPNCPIALLMINMEI',       # COICOP 1999 index (alt: FPCPITOTLZGJPN)
    'KR': 'KORCPIALLMINMEI',       # COICOP 1999 - discontinued Nov 2023, monitor anyway
    'SG': 'FPCPITOTLZGSGP',        # World Bank annual (OECD series broken)
    'IN': 'INDCPIALLMINMEI',
    'CN': 'CHNCPIALLMINMEI',
    'VE': 'FPCPITOTLZGVEN'
}

# Central bank meeting schedules (approximate)
CB_MEETINGS = {
    'US': {'bank': 'FOMC', 'frequency': 8, 'months': [1, 3, 5, 6, 7, 9, 11, 12]},
    'EA': {'bank': 'ECB', 'frequency': 8, 'months': [1, 3, 4, 6, 7, 9, 10, 12]},
    'UK': {'bank': 'BoE', 'frequency': 8, 'months': [2, 3, 5, 6, 8, 9, 11, 12]},
    'CA': {'bank': 'BoC', 'frequency': 8, 'months': [1, 3, 4, 6, 7, 9, 10, 12]},
    'AU': {'bank': 'RBA', 'frequency': 8, 'months': [2, 3, 5, 6, 8, 9, 11, 12]},
    'NZ': {'bank': 'RBNZ', 'frequency': 7, 'months': [2, 4, 5, 7, 8, 10, 11]},
    'ZA': {'bank': 'SARB', 'frequency': 6, 'months': [1, 3, 5, 7, 9, 11]},
    'JP': {'bank': 'BoJ', 'frequency': 8, 'months': [1, 3, 4, 6, 7, 9, 10, 12]},
    'KR': {'bank': 'BOK', 'frequency': 8, 'months': [1, 2, 4, 5, 7, 8, 10, 11]},
    'SG': {'bank': 'MAS', 'frequency': 2, 'months': [4, 10]},
    'IN': {'bank': 'RBI', 'frequency': 6, 'months': [2, 4, 6, 8, 10, 12]},
}

# IMF WEO release months
IMF_WEO_MONTHS = [4, 10]  # April and October


class DataMonitor:
    def __init__(self):
        self.updates = []
        self.alerts = []
        self.errors = []
        
    def load_current_data(self):
        """Load current historical_cpi.json"""
        path = os.path.join(BASE_DIR, 'docs/data/historical_cpi.json')
        with open(path, 'r') as f:
            return json.load(f)
    
    def save_data(self, data, filename):
        """Save updated data to JSON file"""
        path = os.path.join(BASE_DIR, f'docs/data/{filename}')
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def fetch_fred_latest(self, series_id):
        """Fetch latest data point from FRED"""
        if not FRED_API_KEY:
            self.errors.append("FRED_API_KEY not set")
            return None
            
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            'series_id': series_id,
            'api_key': FRED_API_KEY,
            'file_type': 'json',
            'sort_order': 'desc',
            'limit': 2,
            'units': 'pc1'  # Percent change from year ago
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'observations' in data and len(data['observations']) > 0:
                obs = data['observations'][0]
                if obs['value'] != '.':
                    return {
                        'date': obs['date'][:7],  # YYYY-MM
                        'value': round(float(obs['value']), 2),
                        # Per-record provenance (CLAUDE.md #3, #83) — this
                        # point is appended to history/latest by the monitor
                        'source': 'FRED',
                        'fetch_date': datetime.now().strftime('%Y-%m-%d')
                    }
        except Exception as e:
            self.errors.append(f"FRED fetch error for {series_id}: {str(e)}")
        
        return None
    
    def check_cpi_freshness(self):
        """Check if CPI data is fresh and update if needed"""
        current_data = self.load_current_data()
        today = datetime.now()
        updated = False
        
        for country_code, series_id in FRED_SERIES.items():
            if country_code not in current_data:
                continue
                
            current_latest = current_data[country_code].get('latest', {})
            current_date = current_latest.get('date', '2000-01')
            
            # Fetch from FRED
            fred_latest = self.fetch_fred_latest(series_id)
            
            if fred_latest and fred_latest['date'] > current_date:
                # New data available
                self.updates.append({
                    'type': 'CPI',
                    'country': country_code,
                    'old_date': current_date,
                    'new_date': fred_latest['date'],
                    'new_value': fred_latest['value']
                })
                
                # Update the data
                current_data[country_code]['previous'] = current_data[country_code]['latest']
                current_data[country_code]['latest'] = fred_latest
                current_data[country_code]['history'].append(fred_latest)
                updated = True
                # Staleness below must judge the refreshed date, not the one
                # this run just replaced (a malformed old date would otherwise
                # report an error the update already repaired).
                current_date = fred_latest['date']
            
            # Check for stale data (more than 2 months old)
            # Handle monthly (2025-12), quarterly (2025-Q4), and full-date
            # (2025-12-15) formats
            try:
                if '-Q' in current_date:
                    # Quarterly format: 2025-Q4 -> 2025-12
                    year, quarter = current_date.split('-Q')
                    month = int(quarter) * 3
                    latest_date = datetime(int(year), month, 1)
                elif len(current_date) == 10:
                    # Full date (2025-12-15) — keep the day so ages near the
                    # 75-day threshold aren't overstated by up to a month
                    latest_date = datetime.strptime(current_date, '%Y-%m-%d')
                else:
                    latest_date = datetime.strptime(current_date, '%Y-%m')
            except ValueError:
                # An unparseable date means the staleness check can't run for
                # this country. Surface it as an error (non-zero exit + email)
                # instead of skipping silently — CLAUDE.md #4: "no signal" is
                # not a valid state for a broken source.
                self.errors.append(
                    f"Unparseable latest date for {country_code}: "
                    f"{current_date!r} — staleness check skipped"
                )
                continue
                
            if (today - latest_date) > timedelta(days=75):
                self.alerts.append({
                    'type': 'STALE_DATA',
                    'country': country_code,
                    'last_update': current_date,
                    'days_old': (today - latest_date).days
                })
        
        if updated:
            current_data['metadata'] = current_data.get('metadata', {})
            current_data['metadata']['last_updated'] = today.strftime('%Y-%m-%d')
            self.save_data(current_data, 'historical_cpi.json')
        
        return updated
    
    def check_cb_meetings(self):
        """Check for upcoming central bank meetings that may update forecasts"""
        today = datetime.now()
        
        for country_code, schedule in CB_MEETINGS.items():
            for month in schedule['months']:
                # Check meetings in current and next month
                meeting_date = datetime(today.year, month, 15)  # Approximate mid-month
                
                if meeting_date < today:
                    # Check if it was this month (just passed)
                    if meeting_date.month == today.month and today.day <= 20:
                        self.alerts.append({
                            'type': 'CB_MEETING_RECENT',
                            'country': country_code,
                            'bank': schedule['bank'],
                            'date': meeting_date.strftime('%Y-%m'),
                            'message': f"{schedule['bank']} likely released new forecasts - please review"
                        })
                elif (meeting_date - today).days <= 7:
                    # Upcoming meeting within a week
                    self.alerts.append({
                        'type': 'CB_MEETING_UPCOMING',
                        'country': country_code,
                        'bank': schedule['bank'],
                        'date': meeting_date.strftime('%Y-%m'),
                        'message': f"{schedule['bank']} meeting coming up - forecasts may need updating"
                    })
    
    def check_imf_weo(self):
        """Check if IMF WEO release is due"""
        today = datetime.now()
        
        for month in IMF_WEO_MONTHS:
            weo_date = datetime(today.year, month, 15)
            
            if weo_date.month == today.month:
                self.alerts.append({
                    'type': 'IMF_WEO_RELEASE',
                    'date': weo_date.strftime('%Y-%m'),
                    'message': 'IMF World Economic Outlook release expected this month - update imf_forecasts.json'
                })
    
    def update_forecast_history(self):
        """Snapshot current forecasts to history files if changed"""
        today = datetime.now().strftime('%Y-%m-%d')

        # Load current forecasts
        cb_path = os.path.join(BASE_DIR, 'docs/data/cb_forecasts.json')
        cb_history_path = os.path.join(BASE_DIR, 'docs/data/history/cb_forecast_history.json')

        # Read current cb_forecasts.json
        if not os.path.exists(cb_path):
            self.errors.append("cb_forecasts.json not found")
            return

        with open(cb_path, 'r') as f:
            cb_data = json.load(f)

        # Read or initialize history
        os.makedirs(os.path.dirname(cb_history_path), exist_ok=True)
        if os.path.exists(cb_history_path):
            with open(cb_history_path, 'r') as f:
                history = json.load(f)
        else:
            history = {
                "metadata": {
                    "description": "Historical record of central bank inflation forecast revisions",
                    "frequency": "Updated after major monetary policy meetings"
                },
                "snapshots": []
            }

        # Build a compact snapshot: just projections and policy rates per country
        snapshot_forecasts = {}
        for country_code, forecast in cb_data.get('forecasts', {}).items():
            entry = {
                "source": forecast.get('source', '') + ' ' + forecast.get('publication_date', ''),
                "projections": forecast.get('projections', {}),
                "policy_rate": forecast.get('policy_rate', {}).get('rate', '')
            }
            if forecast.get('note'):
                entry["note"] = forecast['note']
            snapshot_forecasts[country_code] = entry

        if not snapshot_forecasts:
            return

        # Skip if the most recent snapshot is from today
        if history["snapshots"] and history["snapshots"][-1].get("date") == today:
            return

        # Append new snapshot
        history["snapshots"].append({
            "date": today,
            "note": f"Auto-snapshot by monitor_updates.py",
            "forecasts": snapshot_forecasts
        })

        # Update metadata
        history["metadata"]["last_updated"] = today

        # Write back
        with open(cb_history_path, 'w') as f:
            json.dump(history, f, indent=2)
    
    def run(self):
        """Run all monitoring checks"""
        print("=" * 60)
        print(f"Inflation Dashboard Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 60)
        
        # Check CPI data freshness
        print("\n📊 Checking CPI data freshness...")
        cpi_updated = self.check_cpi_freshness()
        
        # Check central bank meetings
        print("\n🏦 Checking central bank meeting schedule...")
        self.check_cb_meetings()
        
        # Check IMF WEO releases
        print("\n🌍 Checking IMF WEO release schedule...")
        self.check_imf_weo()
        
        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        if self.updates:
            print(f"\n✅ UPDATES APPLIED ({len(self.updates)}):")
            for update in self.updates:
                print(f"   {update['country']}: {update['old_date']} → {update['new_date']} ({update['new_value']}%)")
        
        if self.alerts:
            print(f"\n⚠️  ALERTS ({len(self.alerts)}):")
            for alert in self.alerts:
                if alert['type'] == 'STALE_DATA':
                    print(f"   {alert['country']}: Data is {alert['days_old']} days old (last: {alert['last_update']})")
                else:
                    print(f"   {alert.get('country', 'IMF')}: {alert['message']}")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   {error}")
        
        if not self.updates and not self.alerts and not self.errors:
            print("\n✨ All data is up to date. No action needed.")
        
        # Write summary to file for email notification
        summary = {
            'timestamp': datetime.now().isoformat(),
            'updates': self.updates,
            'alerts': self.alerts,
            'errors': self.errors
        }
        
        summary_path = os.path.join(BASE_DIR, 'data/monitor_summary.json')
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Exit with error code if there were errors
        if self.errors:
            sys.exit(1)
        
        return summary


if __name__ == '__main__':
    monitor = DataMonitor()
    monitor.run()
