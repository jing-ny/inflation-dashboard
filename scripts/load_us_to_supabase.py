import os
from supabase import create_client

from fetch_us import fetch_us_cpi_series, parse_cpi_entry, compute_yoy

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL or SUPABASE_KEY not set")

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Fetch CPI data
    data = fetch_us_cpi_series(13)
    latest_date, latest_index = parse_cpi_entry(data[0])
    _, prev_index = parse_cpi_entry(data[12])

    yoy = compute_yoy(latest_index, prev_index)

    record = {
        "country": "US",
        "date": latest_date.isoformat(),
        "cpi_index": round(latest_index, 2),
        "yoy_inflation": round(yoy, 2),
        "measure": "headline",
        "source": "BLS",
    }

    # Try UPDATE first
    update_resp = (
        supabase
        .table("inflation_actuals")
        .update({
            "cpi_index": record["cpi_index"],
            "yoy_inflation": record["yoy_inflation"],
            "source": record["source"],
        })
        .eq("country", record["country"])
        .eq("date", record["date"])
        .eq("measure", record["measure"])
        .execute()
    )

    # If no rows updated, INSERT
    if not update_resp.data:
        supabase.table("inflation_actuals").insert(record).execute()

    print("Inserted / updated record:")
    print(record)


if __name__ == "__main__":
    main()
