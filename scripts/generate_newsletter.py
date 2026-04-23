# -*- coding: utf-8 -*-
"""
Newsletter Draft Generator
===========================

Uses change detection from send_weekly_alert.py and the Claude API
to generate a factual inflation newsletter draft.

Usage:
    python scripts/generate_newsletter.py
    python scripts/generate_newsletter.py --dry-run
    python scripts/generate_newsletter.py --output docs/drafts/custom.md
"""

import argparse
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime

# Allow imports from scripts/
sys.path.insert(0, os.path.dirname(__file__))

from send_weekly_alert import (
    load_current_data,
    create_current_snapshot,
    load_snapshots,
    get_previous_snapshot,
    compare_snapshots,
    DASHBOARD_URL,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "data")
DRAFTS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "drafts")
CB_FORECASTS_FILE = os.path.join(DATA_DIR, "cb_forecasts.json")
IMF_FORECASTS_FILE = os.path.join(DATA_DIR, "imf_forecasts.json")

MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1024


def load_json_safe(path: str) -> dict:
    """Load a JSON file, returning empty dict on failure."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load {path}: {e}")
        return {}


def build_prompt(changes: list, cb_forecasts: dict, imf_forecasts: dict) -> str:
    """Build the prompt for the Claude API."""
    material = [c for c in changes if c.is_material]
    all_changes = [asdict(c) for c in changes]

    # IMF metadata — pass to the model so it knows which WEO vintage these numbers are from
    imf_meta = {
        "version": imf_forecasts.get("version"),
        "retrieved": imf_forecasts.get("retrieved"),
        "note": imf_forecasts.get("note"),
    }

    # Compact forecast summaries
    cb_summary = {}
    for code, fc in cb_forecasts.get("forecasts", {}).items():
        cb_summary[code] = {
            "source": fc.get("source"),
            "publication_date": fc.get("publication_date"),
            "2026": fc.get("projections", {}).get("2026"),
            "rate": fc.get("policy_rate", {}).get("rate"),
            "note": fc.get("note"),
        }

    imf_summary = {}
    for code, entry in imf_forecasts.get("countries", {}).items():
        imf_summary[code] = {
            "name": entry.get("name"),
            "2026": entry.get("forecasts", {}).get("2026"),
        }

    return f"""You are writing a concise inflation newsletter draft (300-500 words).

## Data provided

### Current CPI changes (vs. previous snapshot)
{json.dumps(all_changes, indent=2)}

### Material changes (>= 0.3pp or direction reversal)
{json.dumps([asdict(c) for c in material], indent=2)}

### Central bank forecasts (selected fields)
{json.dumps(cb_summary, indent=2)}

### IMF WEO forecasts — vintage metadata
{json.dumps(imf_meta, indent=2)}

### IMF WEO 2026 forecasts (per country)
{json.dumps(imf_summary, indent=2)}

## Instructions
- Structure: **Key Changes**, **Trend Summary**, **What to Watch**
- Tone: professional, factual, no predictions or opinions
- Include specific numbers (inflation rates, changes in pp) with source attributions
- Mention relevant central bank and IMF forecast context where useful
- **CRITICAL — do not cite any IMF figures other than the numbers in the "IMF WEO 2026 forecasts" block above.** Do not recall figures from prior WEO editions, news articles, or pre-training. When you attribute an IMF number, it MUST come from the provided data.
- **CRITICAL — do not cite CB forecasts other than the numbers in the "Central bank forecasts" block above.** When you say "X vs Y" comparisons between CB and IMF, compute them from the provided data only.
- When citing CB forecasts, prefer the `publication_date` field as the vintage; do not assume a forecast is current if its publication_date is older than 3 months.
- If a country's latest CPI reading is older than the current newsletter date (see `current_period` in the changes block), describe the value as being from that specific month/quarter, not "held steady" or "current".
- End with a pointer to the dashboard for full data: {DASHBOARD_URL}
- Output valid Markdown
- Do NOT add a title — the caller will prepend one
- Stay within 300-500 words"""


def generate_draft(prompt: str) -> str:
    """Call the Claude API and return the generated text."""
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def main():
    parser = argparse.ArgumentParser(description="Generate an inflation newsletter draft via Claude API")
    parser.add_argument("--dry-run", action="store_true", help="Print the prompt without calling the API")
    parser.add_argument("--output", type=str, default=None, help="Custom output path for the draft")
    args = parser.parse_args()

    # --- gather data ---
    print("Loading inflation data...")
    current_data = load_current_data()
    snapshot = create_current_snapshot(current_data)
    previous = get_previous_snapshot(load_snapshots())
    changes = compare_snapshots(snapshot, previous)

    cb_forecasts = load_json_safe(CB_FORECASTS_FILE)
    imf_forecasts = load_json_safe(IMF_FORECASTS_FILE)

    prompt = build_prompt(changes, cb_forecasts, imf_forecasts)

    # --- dry run ---
    if args.dry_run:
        print("\n=== PROMPT (dry run) ===\n")
        print(prompt)
        print(f"\nModel: {MODEL} | Max tokens: {MAX_TOKENS}")
        return

    # --- call API ---
    print(f"Calling {MODEL}...")
    body = generate_draft(prompt)

    # --- assemble output ---
    today = datetime.now().strftime("%Y-%m-%d")
    title = f"# Inflation Newsletter — {today}\n\n"
    disclaimer = (
        "\n\n---\n\n"
        "*Some data points in this newsletter are compiled with AI assistance. "
        "Figures should be verified against the original official sources (linked on each "
        f"country page at {DASHBOARD_URL}) before any formal, professional, or published use. "
        "This newsletter is for informational purposes only and is not investment advice.*\n"
    )
    draft = title + body + disclaimer

    # --- write file ---
    output_path = args.output or os.path.join(DRAFTS_DIR, f"newsletter_{today}.md")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(draft)

    print(f"Draft saved to {output_path}")


if __name__ == "__main__":
    main()
