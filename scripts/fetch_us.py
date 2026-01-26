import requests
from datetime import datetime

SERIES_ID = "CUSR0000SA0"  # CPI-U headline

def fetch_us_cpi_series(months=13):
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    payload = {
        "seriesid": [SERIES_ID],
        "latest": "false"
    }

    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()

    series = data["Results"]["series"][0]["data"]

    # Sort by date descending, take latest N months
    series_sorted = sorted(
        series,
        key=lambda x: (int(x["year"]), int(x["period"][1:])),
        reverse=True
    )

    return series_sorted[:months]


def parse_cpi_entry(entry):
    value = float(entry["value"])
    year = int(entry["year"])
    month = int(entry["period"][1:])
    date = datetime(year, month, 1).date()
    return date, value


def compute_yoy(latest, one_year_ago):
    return (latest - one_year_ago) / one_year_ago * 100


if __name__ == "__main__":
    data = fetch_us_cpi_series(13)

    latest_date, latest_value = parse_cpi_entry(data[0])
    prev_date, prev_value = parse_cpi_entry(data[12])

    yoy = compute_yoy(latest_value, prev_value)

    print("US CPI (Headline)")
    print("-----------------")
    print(f"Date           : {latest_date}")
    print(f"CPI Index      : {latest_value:.2f}")
    print(f"YoY Inflation  : {yoy:.2f}%")
    print("Source         : BLS")
