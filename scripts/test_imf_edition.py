#!/usr/bin/env python3
"""Offline checks that the IMF edition page follows the data's WEO edition.

The curated publication_url / note were written for the April 2026 WEO; when
the data moved to October 2026 the dashboard kept linking April's page, and
CN's Outlook row (synced from the IMF) inherited it as its source_url.

    python3 scripts/test_imf_edition.py
"""
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_imf_forecasts as imf  # noqa: E402

FAILS = []
N = 0


def check(name, cond):
    global N
    N += 1
    print(("  ✅ " if cond else "  ❌ ") + name)
    if not cond:
        FAILS.append(name)


APRIL = "https://www.imf.org/en/publications/weo/issues/2026/04/14/world-economic-outlook-april-2026"
OCTOBER = "https://www.imf.org/en/publications/weo/issues/2026/10/14/world-economic-outlook-october-2026"
DATAMAPPER = "https://www.imf.org/external/datamapper/PCPIPCH@WEO"

print("_edition_from_url")
check("April page", imf._edition_from_url(APRIL) == "April 2026")
check("October page", imf._edition_from_url(OCTOBER) == "October 2026")
check("DataMapper link has no edition", imf._edition_from_url(DATAMAPPER) is None)
check("missing URL", imf._edition_from_url(None) is None)


class FakeResp:
    def raise_for_status(self):
        pass

    def json(self):
        return {"values": {"PCPIPCH": {"CHN": {"2026": 1.0, "2027": 1.4}}}}


class FakeNow(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 11, 27)


def run(existing, cb_row=None):
    tmp = Path(tempfile.mkdtemp())
    old_dir, old_get, old_dt = imf.OUTPUT_DIR, imf.requests.get, imf.datetime
    try:
        imf.OUTPUT_DIR = tmp
        imf.requests.get = lambda *a, **k: FakeResp()
        imf.datetime = FakeNow
        (tmp / "imf_forecasts.json").write_text(json.dumps(existing))
        if cb_row is not None:
            (tmp / "cb_forecasts.json").write_text(json.dumps({"forecasts": {"CN": cb_row}}))
        data = imf.fetch_imf_forecasts()
        cb = None
        if cb_row is not None:
            imf.sync_imf_sourced_cb_forecasts(data)
            cb = json.loads((tmp / "cb_forecasts.json").read_text())["forecasts"]["CN"]
        return data, cb
    finally:
        imf.OUTPUT_DIR, imf.requests.get, imf.datetime = old_dir, old_get, old_dt
        shutil.rmtree(tmp)


print("fetch_imf_forecasts on October 2026 data")
cn = {"scraper_status": "imf_sourced", "source_url": APRIL, "projections": {}}
data, cb = run({"version": "October 2026", "url": DATAMAPPER, "publication_url": APRIL,
                "note": "April context"}, dict(cn))
check("version is October 2026", data["version"] == "October 2026")
check("April page no longer linked", "publication_url" not in data)
check("note kept", data.get("note") == "April context")
check("note marked as written for April", data.get("note_edition") == "April 2026")
check("CN row's source_url falls back to the DataMapper", cb["source_url"] == DATAMAPPER)
check("CN row's projections synced", cb["projections"] == {"2026": 1.0, "2027": 1.4})

data, _ = run({"version": "October 2026", "url": DATAMAPPER, "publication_url": OCTOBER,
               "note": "October context"})
check("matching page kept", data.get("publication_url") == OCTOBER)
check("matching note marked October", data.get("note_edition") == "October 2026")

first, _ = run({"version": "October 2026", "url": DATAMAPPER, "publication_url": APRIL,
                "note": "April context"})
data, _ = run(first)
check("second run keeps April: stored edition matches the unchanged note",
      data.get("note_edition") == "April 2026")
recurated = dict(first, note="October context", publication_url=OCTOBER)
data, _ = run(recurated)
check("re-curated note and page without touching note_edition: label clears",
      data.get("note_edition") == "October 2026" and data.get("publication_url") == OCTOBER)

data, _ = run({"version": "October 2026", "url": DATAMAPPER})
check("no note: no note_edition", "note_edition" not in data)

print(f"\n{'FAIL' if FAILS else 'OK'}: {N - len(FAILS)}/{N}")
sys.exit(1 if FAILS else 0)
