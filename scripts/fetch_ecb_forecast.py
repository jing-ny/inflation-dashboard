# -*- coding: utf-8 -*-
"""
Fetch European Central Bank (ECB) inflation forecasts via ECB Data Portal API.

Series used:
- SPF: Survey of Professional Forecasters (HICP inflation expectations)
- ICP: Actual HICP inflation for comparison

Source: ECB Data Portal (SDMX API)
API Docs: https://data.ecb.europa.eu/help/api/overview
"""

import requests
from datetime import datetime
import csv
from io import StringIO


# ECB SDMX API endpoint
ECB_API_BASE = 'https://data-api.ecb.europa.eu/service/data'


def fetch_ecb_series_csv(dataflow, series_key, last_n=8):
    """
    Fetch ECB data series using CSV format (most reliable).
    
    Args:
        dataflow: Dataset name (e.g., 'SPF', 'ICP')
        series_key: Series key without dataflow prefix
        last_n: Number of recent observations
    
    Returns:
        List of {period, value} dicts
    """
    url = "{}/{}/{}".format(ECB_API_BASE, dataflow, series_key)
    
    params = {
        'lastNObservations': last_n,
        'format': 'csvdata'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        # Parse CSV
        observations = []
        reader = csv.DictReader(StringIO(response.text))
        for row in reader:
            period = row.get('TIME_PERIOD', '')
            value = row.get('OBS_VALUE', '')
            if period and value:
                try:
                    observations.append({
                        'period': period,
                        'value': float(value)
                    })
                except ValueError:
                    pass
        
        # Sort by period descending
        observations.sort(key=lambda x: x['period'], reverse=True)
        return observations
        
    except Exception as e:
        print("Error fetching {}/{}: {}".format(dataflow, series_key, e))
        return None


def fetch_ecb_spf_inflation_forecast():
    """
    Fetch ECB Survey of Professional Forecasters (SPF) inflation expectations.
    
    Series format: {freq}.U2.HICP.POINT.{horizon}.Q.AVG
    
    Horizons (correct ECB codes):
    - P12M = Target period ends 12 months after survey
    - P24M = Target period ends 24 months after survey  
    - LT = Longer term (5 years ahead)
    
    Updated quarterly after each SPF round.
    """
    results = {}
    
    # Correct ECB series keys
    horizons = {
        '12m_ahead': 'M.U2.HICP.POINT.P12M.Q.AVG',  # Monthly frequency
        '24m_ahead': 'M.U2.HICP.POINT.P24M.Q.AVG',  # Monthly frequency
        'longer_term': 'Q.U2.HICP.POINT.LT.Q.AVG'   # Quarterly frequency
    }
    
    for horizon_name, series_key in horizons.items():
        data = fetch_ecb_series_csv('SPF', series_key, last_n=8)
        if data:
            results[horizon_name] = data
    
    return results if results else None


def fetch_ecb_hicp_actual():
    """
    Fetch actual Euro Area HICP inflation.
    Series: M.U2.N.000000.4.ANR (monthly, euro area, all items, annual rate)
    """
    data = fetch_ecb_series_csv('ICP', 'M.U2.N.000000.4.ANR', last_n=13)
    if data:
        return data[0]  # Most recent
    return None


def get_all_ecb_data():
    """
    Convenience function to get all ECB inflation data in one call.
    """
    return {
        'spf_forecasts': fetch_ecb_spf_inflation_forecast(),
        'actual_hicp': fetch_ecb_hicp_actual(),
        'staff_projections': ECB_STAFF_PROJECTIONS,
        'fetched_at': datetime.utcnow().isoformat() + 'Z'
    }


# Hardcoded ECB Staff Projections (Dec 2025)
# Source: https://www.ecb.europa.eu/press/projections/html/index.en.html
ECB_STAFF_PROJECTIONS = {
    'as_of': '2025-12',
    'hicp': {
        '2025': 2.1,
        '2026': 1.9,
        '2027': 1.8,
        '2028': 2.0
    },
    'core_hicp': {
        '2025': 2.3,
        '2026': 1.9,
        '2027': 1.9,
        '2028': 1.9
    },
    'source': 'ECB Eurosystem Staff Projections, December 2025'
}


def main():
    print("=" * 60)
    print("European Central Bank Inflation Data")
    print("=" * 60)
    
    # Actual HICP
    print("\n1. Current Euro Area HICP Inflation")
    print("-" * 40)
    actual = fetch_ecb_hicp_actual()
    if actual:
        print("  {}: {:.1f}% YoY".format(actual['period'], actual['value']))
    else:
        print("  No data available")
    
    # SPF Forecasts
    print("\n2. Survey of Professional Forecasters (SPF)")
    print("-" * 40)
    spf = fetch_ecb_spf_inflation_forecast()
    if spf:
        for horizon, data in spf.items():
            if data:
                latest = data[0]
                print("  {} ({}): {:.2f}%".format(
                    horizon.replace('_', ' ').title(),
                    latest['period'],
                    latest['value']
                ))
    else:
        print("  No data available")
    
    # Staff projections (hardcoded from official source)
    print("\n3. ECB Staff Projections (Dec 2025)")
    print("-" * 40)
    for year, value in ECB_STAFF_PROJECTIONS['hicp'].items():
        print("  {}: {:.1f}%".format(year, value))
    print("  Source: {}".format(ECB_STAFF_PROJECTIONS['source']))
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
