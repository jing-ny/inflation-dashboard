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

# Model IDs get retired. Keep this overridable from the workflow env so a
# retirement can be patched without a code change (see 2026-07/08 outage:
# claude-sonnet-4-20250514 started 404ing and the monthly cron failed twice).
MODEL = os.environ.get("NEWSLETTER_MODEL") or "claude-opus-5"
# Thinking is on by default on this model tier and its tokens count against
# max_tokens, so this ceiling is much higher than the ~550-token draft needs.
# It is a cap, not a spend — only what is generated is billed.
MAX_TOKENS = 16000


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

    return f"""You are writing a short, sharp, Substack-style inflation newsletter — the kind a policy-literate reader would forward. Target 300–400 words of polished publication-ready English. A reader should grasp the whole piece in under 2 minutes.

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

## Editorial voice
- Open with a punchy, high-signal lead — a little narrative tension, professional and source-first, no hype.
- Anchor the piece around the 3–4 moves that matter most this period. Default anchors are **Euro Area, Japan, South Korea, and China** unless the data clearly demands different ones. Do NOT try to cover every country in equal detail.
- Treat the IMF WEO revisions as ONE clean paragraph, not a data dump.
- Close with a tight "what to watch" — only the 1–3 most decision-relevant divergences or upcoming releases.
- Keep section headings light. Use a heading only if it materially helps scan-ability; otherwise flow prose. Do not use rigid "Key Changes / Trend Summary / What to Watch" labels.
- Short paragraphs. Avoid bullet overload.
- No filler, no generic macro commentary, no AI-slop phrasing. Cut on sight: "provided relief", "apparent comfort zone", "the standout remains", "warrants continued attention", "exactly matching", "first full WEO reflecting", and similar.
- Do not overclaim. Avoid causal language ("driven by X", "due to Y", "reflecting Z") unless the causation is directly and unambiguously stated in the data notes above.
- Describe older CPI readings by their specific period (e.g. "Japan's 1.3% in February") — never "held steady" or "current" when the data isn't the most recent month.

## CRITICAL data rules (these override style)
- Do not cite any IMF figures other than the numbers in the "IMF WEO 2026 forecasts" block above. Do not recall figures from prior WEO editions, news articles, or pre-training. When you attribute an IMF number, it MUST come from the provided data.
- Do not cite CB forecasts other than the numbers in the "Central bank forecasts" block above. Any "CB vs IMF" comparison must be computed from the provided numbers only.
- When citing CB forecasts, prefer the `publication_date` field as the vintage; do not assume a forecast is current if its publication_date is older than 3 months.

## Output
- Valid Markdown, 300–400 words (prefer the lower end).
- Do NOT add a title — the caller prepends one.
- End with a compact pointer to the dashboard: {DASHBOARD_URL}"""


def generate_draft(prompt: str) -> str:
    """Call the Claude API and return the generated text."""
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )

    # A refusal comes back as HTTP 200, not an exception — fail loudly rather
    # than committing an empty draft.
    if message.stop_reason == "refusal":
        detail = getattr(message.stop_details, "explanation", None) or "no explanation"
        raise RuntimeError(f"{MODEL} refused the request: {detail}")
    if message.stop_reason == "max_tokens":
        raise RuntimeError(
            f"Draft truncated at max_tokens={MAX_TOKENS}; raise the ceiling."
        )

    # content is a list of blocks (thinking, text, ...) — take only the text.
    text = "".join(b.text for b in message.content if b.type == "text").strip()
    if not text:
        raise RuntimeError(f"{MODEL} returned no text block (stop_reason={message.stop_reason})")
    return text


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
        "*Compiled with AI assistance. Verify figures against the original official sources "
        f"(linked at [the dashboard]({DASHBOARD_URL})) before any formal use. Not investment advice.*\n"
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
