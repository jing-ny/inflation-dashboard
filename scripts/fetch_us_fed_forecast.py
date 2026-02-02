# -*- coding: utf-8 -*-
"""
Fetch US Federal Reserve (FOMC) inflation forecasts from FRED API.

Series used:
- PCECTPIMD: FOMC PCE Inflation Forecast (Median) - annual projections
- EXPINF1YR: Cleveland Fed 1-Year Expected Inflation - monthly model-based

Source: Federal Reserve via FRED API
"""

import os
import requests
from datetime import datetime

# Try to load from .env.local if available
try:
    from dotenv import load_dotenv
    load_dotenv('.env.local')
except ImportError:
    pass

FRED_API_KEY = os.getenv('FRED_API_KEY')
FRED_BASE_URL = 'https://api.stlouisfed.org/fred/series/observations'


def fetch_fomc_pce_forecast():
    """
    Fetch FOMC Summary of Economic Projections for PCE Inflation (Median).
    This is the Fed's official inflation forecast from the dot plot meetings.
    Updated 4x/year (Mar, Jun, Sep, Dec FOMC meetings).
    
    Returns list of forecasts for different target years.
    """
    params = {
        'series_id': 'PCECTPIMD',
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'sort_order': 'desc',
        'limit': 10
    }
    
    response = requests.get(FRED_BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()
    
    observations = data.get('observations', [])
    if not observations:
        print("No FOMC PCE forecast data found")
        return None
    
    # Parse into structured format
    forecasts = []
    for obs in observations:
        if obs['value'] != '.':
            forecasts.append({
                'target_year': obs['date'][:4],
                'forecast_pct': float(obs['value']),
                'as_of': obs['date']
            })
    
    return forecasts


def fetch_cleveland_fed_expected_inflation():
    """
    Fetch Cleveland Fed 1-Year Expected Inflation (EXPINF1YR).
    Model-based estimate combining Treasury yields, inflation data, and surveys.
    Updated monthly.
    
    Returns most recent 1-year inflation expectation.
    """
    params = {
        'series_id': 'EXPINF1YR',
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'sort_order': 'desc',
        'limit': 13
    }
    
    response = requests.get(FRED_BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()
    
    observations = data.get('observations', [])
    if not observations:
        print("No Cleveland Fed inflation expectations data found")
        return None
    
    # Get most recent non-null value
    latest = None
    for obs in observations:
        if obs['value'] != '.':
            latest = {
                'date': obs['date'],
                'expected_inflation_1yr': float(obs['value'])
            }
            break
    
    return latest


def fetch_longer_run_fomc_target():
    """
    Fetch FOMC Longer-Run PCE Inflation projection (Median).
    This is essentially the Fed's inflation target (typically 2.0%).
    """
    params = {
        'series_id': 'PCECTPIMDLR',
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'sort_order': 'desc',
        'limit': 5
    }
    
    response = requests.get(FRED_BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()
    
    observations = data.get('observations', [])
    if not observations:
        return None
    
    for obs in observations:
        if obs['value'] != '.':
            return {
                'date': obs['date'],
                'longer_run_target': float(obs['value'])
            }
    
    return None


def get_all_fed_forecasts():
    """
    Convenience function to get all Fed forecast data in one call.
    Returns a dictionary with all forecast types.
    """
    return {
        'fomc_projections': fetch_fomc_pce_forecast(),
        'cleveland_fed_1yr': fetch_cleveland_fed_expected_inflation(),
        'longer_run_target': fetch_longer_run_fomc_target(),
        'fetched_at': datetime.utcnow().isoformat() + 'Z'
    }


def main():
    print("=" * 60)
    print("US Federal Reserve Inflation Forecasts")
    print("=" * 60)
    
    # FOMC PCE Projections
    print("\n1. FOMC PCE Inflation Projections (Median)")
    print("-" * 40)
    fomc_forecasts = fetch_fomc_pce_forecast()
    if fomc_forecasts:
        for f in fomc_forecasts[:5]:
            print("  Target Year {}: {:.1f}%".format(f['target_year'], f['forecast_pct']))
    else:
        print("  No data available")
    
    # Cleveland Fed Expected Inflation
    print("\n2. Cleveland Fed 1-Year Expected Inflation")
    print("-" * 40)
    cleveland = fetch_cleveland_fed_expected_inflation()
    if cleveland:
        print("  As of {}: {:.2f}%".format(cleveland['date'], cleveland['expected_inflation_1yr']))
    else:
        print("  No data available")
    
    # Longer-run target
    print("\n3. FOMC Longer-Run Inflation Target")
    print("-" * 40)
    longer_run = fetch_longer_run_fomc_target()
    if longer_run:
        print("  As of {}: {:.1f}%".format(longer_run['date'], longer_run['longer_run_target']))
    else:
        print("  No data available")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
