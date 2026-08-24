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
import re
import sys
from dataclasses import asdict
from datetime import datetime

# Allow imports from scripts/
sys.path.insert(0, os.path.dirname(__file__))

from send_weekly_alert import (
    load_current_data,
    ChangeRules,
    CountryChange,
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


def preceding_period(period: str) -> str:
    """The reference period immediately before `period` ("2026-01" -> "2025-12")."""
    if "-Q" in period:
        year, quarter = period.split("-Q")
        return f"{int(year) - 1}-Q4" if quarter == "1" else f"{year}-Q{int(quarter) - 1}"
    year, month = period.split("-")[:2]
    return f"{int(year) - 1}-12" if month == "01" else f"{year}-{int(month) - 1:02d}"


def compare_periods(data: dict) -> list:
    """Period-over-period change per country, read from the dataset itself.

    This deliberately does NOT use send_weekly_alert.compare_snapshots (#117).
    That helper diffs the current weekly snapshot against the previous weekly
    snapshot, which is the right semantics for a weekly alert and the wrong
    semantics for a monthly newsletter — the comparison window becomes whatever
    the last snapshot happened to be, so a real month-over-month move lands
    inside or outside it by luck of fetch timing.

    Two observed failures, both published-quality wrong:

      2026-08-22  China 1.0 -> 0.5 (-0.5pp, the largest move in the data) was
                  reported as "unchanged", because the 08-17 snapshot already
                  carried 0.5.
      2026-08-23  Korea was reported as "up 0.59pp, the one real move", because
                  the previous snapshot held 2.2 (2026-03) — the last value the
                  dead FRED relay ever produced — while the dataset had just
                  been backfilled to 2026-07. July was actually DOWN 0.37pp from
                  June. A source repair read as an inflation move.

    Each country's `latest` and `previous` are adjacent reference periods
    maintained by the fetchers, so they give the true period-over-period change
    regardless of when we fetched or how much history was backfilled.
    """
    changes = []

    for code, record in data.items():
        if code == "metadata" or not isinstance(record, dict):
            continue
        latest = record.get("latest") or {}
        previous = record.get("previous") or {}
        if latest.get("value") is None or previous.get("value") is None:
            continue

        current_yoy = latest["value"]
        previous_yoy = previous["value"]
        delta = round(current_yoy - previous_yoy, 2)
        current_direction = ChangeRules.get_direction(delta)

        # Prior direction, for the reversal rule: the step into `previous`.
        # Looked up in history by date. AU stores a monthly latest/previous over
        # a quarterly history, so the lookup misses and the reversal rule is a
        # no-op there — same as compare_snapshots without two weeks of history.
        previous_direction = "stable"
        history = record.get("history") or []
        dates = [h.get("date") for h in history]
        if previous.get("date") in dates:
            i = dates.index(previous["date"])
            expected = preceding_period(previous["date"])
            # The entry before `previous` in history is only usable if it is
            # genuinely the preceding period. NZ's stored history jumps
            # 2025-Q1 -> 2025-Q4, so without this a small 2026-Q1 move would be
            # judged a "reversal" against an observation three quarters old.
            if (i > 0 and dates[i - 1] == expected
                    and isinstance(history[i - 1].get("value"), (int, float))):
                prior_delta = round(previous_yoy - history[i - 1]["value"], 2)
                previous_direction = ChangeRules.get_direction(prior_delta)

        changes.append(CountryChange(
            code=code,
            name=record.get("name", code),
            current_yoy=current_yoy,
            previous_yoy=previous_yoy,
            delta_pp=delta,
            direction=current_direction,
            direction_symbol=ChangeRules.get_direction_symbol(current_direction),
            is_material=ChangeRules.is_material_change(
                current_yoy, previous_yoy, current_direction, previous_direction),
            current_period=latest.get("date", "?"),
            previous_period=previous.get("date", "?"),
        ))

    changes.sort(key=lambda c: -abs(c.delta_pp))
    return changes


def load_json_safe(path: str) -> dict:
    """Load a JSON file, returning empty dict on failure."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load {path}: {e}")
        return {}


def source_blob(changes: list, cb_forecasts: dict, imf_forecasts: dict) -> str:
    """Just the data handed to the model — no instructions.

    verify_draft must not read the rendered prompt: the instructions carry
    numbers of their own ("300-400 words", the 0.3pp materiality threshold, and
    the 0.7pp example in the rule forbidding self-computed gaps). Harvesting
    those as source figures let the instruction text license exactly the copy it
    forbids (Codex review, PR #122).
    """
    return json.dumps(
        {"changes": [asdict(c) for c in changes],
         "cb": cb_forecasts, "imf": imf_forecasts},
        indent=2, ensure_ascii=False, default=str)


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

### Current CPI changes (each country's latest reference period vs. the one before it)
{json.dumps(all_changes, indent=2, ensure_ascii=False)}

### Material changes (>= 0.3pp or direction reversal)
{json.dumps([asdict(c) for c in material], indent=2, ensure_ascii=False)}

### Central bank forecasts (selected fields)
{json.dumps(cb_summary, indent=2, ensure_ascii=False)}

### IMF WEO forecasts — vintage metadata
{json.dumps(imf_meta, indent=2, ensure_ascii=False)}

### IMF WEO 2026 forecasts (per country)
{json.dumps(imf_summary, indent=2, ensure_ascii=False)}

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
- Every change you describe MUST come from the change list above, which compares each country's latest reference period against the immediately preceding one. Do not construct your own comparison against some other period and present it as the current move: if a country's `current_period` is 2026-07 and its `previous_period` is 2026-06, the move is that one. Quote `delta_pp` as given; do not compute a different delta.
- Match direction to the sign of `delta_pp`. A negative delta fell, a positive delta rose, and a delta the change list marks non-material did not "move".
- Only ever write a "pp" figure that is given to you — a `delta_pp` from the change list, or a pp figure quoted in the source notes. Do NOT compute your own pp gap between two numbers. Express a gap in the levels themselves ("the RBA's 3.3% against the IMF's 4.0%"), never as "a 0.7pp gap". A pp figure you calculated will be rejected and the draft discarded.

## CRITICAL data rules (these override style)
- Do not cite any IMF figures other than the numbers in the "IMF WEO 2026 forecasts" block above. Do not recall figures from prior WEO editions, news articles, or pre-training. When you attribute an IMF number, it MUST come from the provided data.
- Do not cite CB forecasts other than the numbers in the "Central bank forecasts" block above. Any "CB vs IMF" comparison must be computed from the provided numbers only.
- When citing CB forecasts, prefer the `publication_date` field as the vintage; do not assume a forecast is current if its publication_date is older than 3 months.

## Output
- Valid Markdown, 300–400 words (prefer the lower end).
- Do NOT add a title — the caller prepends one.
- End with a compact pointer to the dashboard: {DASHBOARD_URL}"""


# Words that assert a level did not move. Checked only in a tight window right
# after a country's own headline figure — see check_no_change_claims.
NO_CHANGE_WORDS = (
    "unchanged", "flat", "steady", "stable", "held", "holding", "no change",
)

# Short forms the model actually writes, beyond the dataset's `name` field.
ADJECTIVAL = {
    "CN": "Chinese", "JP": "Japanese", "KR": "Korean", "US": "American",
    "UK": "British", "CA": "Canadian", "AU": "Australian", "SG": "Singaporean",
    "NZ": "New Zealand", "ZA": "South African", "EA": "European",
}

COUNTRY_ALIASES = {
    "US": ("US", "U.S.", "United States", "America"),
    "EA": ("Euro Area", "Eurozone", "euro area"),
    "UK": ("UK", "U.K.", "Britain", "United Kingdom"),
    "KR": ("Korea", "South Korea"),
    "CN": ("China",),
    "JP": ("Japan",),
    "IN": ("India",),
    "CA": ("Canada",),
    "AU": ("Australia",),
    "NZ": ("New Zealand",),
    "ZA": ("South Africa",),
    "SG": ("Singapore",),
}


def _matches_at_precision(value: float, candidates) -> bool:
    """True if any candidate rounds to `value` at `value`'s own precision.

    Lets the model write 2.8 for a stored 2.79 without letting it write 2.9.
    """
    text = f"{value}"
    decimals = len(text.split(".")[1]) if "." in text else 0
    return any(round(c, decimals) == value for c in candidates)


# A percentage or pp figure as the model writes it. Captures an optional sign so
# "-0.6%" is not read as a positive 0.6, and rejects a thousands separator
# outright rather than silently parsing "1,000pp" as "000pp".
FIGURE_RE = r"(?<![\d,.])([+-]?\d+(?:\.\d+)?)\s*(%|pp\b|percentage points)"


def _figures(text: str, unit: str, signed_only: bool = False) -> list:
    """Figures in `text` carrying `unit` ("%" or "pp").

    signed_only keeps just the ones written with an explicit + or -. That
    distinction matters: "down 0.37pp" carries its direction in the word, not
    the number, so treating an unsigned positive as "written as an increase"
    would reject correct copy.
    """
    out = []
    for raw, found in re.findall(FIGURE_RE, text, flags=re.IGNORECASE):
        is_pp = found.lower() in ("pp", "percentage points")
        if (unit == "pp") != is_pp:
            continue
        if signed_only and raw[0] not in "+-":
            continue
        out.append(float(raw))
    return out


def _number_pattern(value: float) -> str:
    """Regex alternation matching how the model may write `value`.

    0.5 is written "0.5" or "0.50"; without both, a check keyed on one spelling
    silently misses the other (this is why "rose 0.50pp" first slipped past a
    magnitude built with :g).
    """
    forms = {f"{value:g}", f"{value:.2f}"}
    # The left guard matters: without it the pattern for 5.0 matches the tail of
    # "2.5%", which reported a South Africa claim from a sentence about the BOK.
    return "(?<![\\d.])(?:" + "|".join(
        re.escape(f) for f in sorted(forms, key=len, reverse=True)) + ")"


def _was_signed(draft: str, value: float) -> bool:
    """True if `value` appears in `draft` written with an explicit + or -."""
    return any(abs(v) == abs(value) for v in _figures(draft, "pp", signed_only=True))


def check_figures(draft: str, source: str, changes: list) -> list:
    """Every % and pp figure in the draft must trace back to the source data.

    `source` is the data blob, never the rendered prompt — see source_blob.

    Known limit, stated rather than implied: the `%` rule does not attach a
    level to the country it is claimed for. "China CPI was 2.93%" passes because
    2.93 is the Euro Area's value. Establishing that attribution means parsing
    the sentence, the fragile thing this checker exists to avoid. It is a
    hallucination guard, not a precision instrument. The `pp` rule is the sharp
    one: it catches a delta measured against a period we never supplied.
    """
    problems = []

    # A thousands separator makes a figure unparseable by FIGURE_RE, and an
    # unparseable figure is an UNCHECKED figure, not a safe one. Reject it.
    for raw in re.findall(r"\d[\d,]*\d\s*(?:%|pp\b|percentage points)", draft,
                          flags=re.IGNORECASE):
        if "," in raw:
            problems.append(
                f"figure {raw.strip()!r} uses a thousands separator, so it cannot "
                f"be checked — and no CPI figure needs one"
            )

    source_numbers = [float(m) for m in re.findall(r"-?\d+(?:\.\d+)?", source)]
    signed_deltas = [round(c.delta_pp, 2) for c in changes]
    source_pp = _figures(source, "pp")          # signed, e.g. the IMF's "+0.8pp"
    magnitudes = {abs(d) for d in signed_deltas} | {abs(f) for f in source_pp}

    for value in _figures(draft, "%"):
        if not _matches_at_precision(value, source_numbers):
            problems.append(
                f"figure {value}% appears in the draft but in none of the source data")

    for value in _figures(draft, "pp"):
        if not _matches_at_precision(abs(value), magnitudes):
            allowed = ", ".join(f"{d:.2f}" for d in sorted(magnitudes, reverse=True))
            problems.append(
                f"delta {value}pp is neither a period-over-period change we computed "
                f"nor a pp figure the source quotes (allowed: {allowed}) — it is "
                f"either invented, measured against a period we never supplied, or "
                f"a gap the model computed itself, which the prompt forbids"
            )
            continue
        # An explicit sign must name something that actually moved that way. A
        # supplied +0.8pp must not license a written -0.8pp.
        if _was_signed(draft, value) and not any(
                _matches_at_precision(value, [c]) for c in signed_deltas + source_pp):
            problems.append(
                f"delta {value:+}pp is written with that sign but nothing of that "
                f"size moved in that direction"
            )
    return problems


UP_WORDS = ("rose", "rise", "risen", "rising", "climbed", "gained", "up",
            "higher", "accelerated", "increased", "jumped")
DOWN_WORDS = ("fell", "fall", "fallen", "falling", "eased", "easing", "declined",
              "down", "lower", "dropped", "slowed", "cooled", "decreased")


def check_direction_words(draft: str, changes: list) -> list:
    """A direction word next to a country's own delta must match that delta's sign.

    "China CPI rose 0.50pp" is false when CN fell 0.50pp — the magnitude is
    right, so check_figures waves it through; the verb is what is wrong. Same
    proximity rule as check_no_change_claims: within 25 characters, no other
    figure and no sentence boundary in between.
    """
    problems = []
    ups, downs = "|".join(UP_WORDS), "|".join(DOWN_WORDS)

    for change in changes:
        if change.direction == "stable":
            continue
        magnitude = _number_pattern(abs(change.delta_pp))
        wrong = ups if change.delta_pp < 0 else downs
        said = "an increase" if change.delta_pp < 0 else "a decrease"
        for pattern in (rf"\b(?:{wrong})\b[^0-9.]{{0,25}}{magnitude}\s*pp",
                        rf"{magnitude}\s*pp[^0-9.]{{0,25}}\b(?:{wrong})\b"):
            match = re.search(pattern, draft, flags=re.IGNORECASE)
            if match:
                problems.append(
                    f"{change.code}'s {abs(change.delta_pp):g}pp change is described as "
                    f"{said} ({match.group(0).strip()!r}), but "
                    f"{change.previous_period} -> {change.current_period} moved "
                    f"{change.delta_pp:+.2f}pp"
                )
                break
    return problems


# Words that assert a level did not move.
# Only unambiguous assertions. "remains"/"stable" were dropped after review:
# in "fell 0.5pp to 0.5%, where it remains below target" the word modifies
# "below target", not the level, and proximity cannot tell the difference.
NO_CHANGE_WORDS = (
    "unchanged", "flat", "no change", "held at", "holds at", "sat at",
    "sits at", "steady at",
)


def check_no_change_claims(draft: str, changes: list) -> list:
    """Flag "unchanged" asserted about a country whose latest print did move.

    Scoped by proximity to the country's OWN headline figure, in either word
    order, within 25 characters, with no other figure and no sentence boundary
    in between — `[^0-9.]{0,25}` does that work. It
    fires on "China's July CPI sat at 0.5%, unchanged" and on "Australia CPI was
    unchanged at 3.8%", and stays quiet on "China was 0.5% in July, with the 1Y
    LPR unchanged at 3.00%", where the word belongs to a different number.

    Applies to every country the project's own DIRECTION_THRESHOLD_PP calls a
    move, not only material ones: a 0.2pp fall described as "unchanged" is still
    a false statement about the data.
    """
    problems = []
    words = "|".join(re.escape(w) for w in NO_CHANGE_WORDS)

    for change in changes:
        if change.direction == "stable":
            continue
        aliases = set(COUNTRY_ALIASES.get(change.code, ())) | {change.name}
        aliases |= {ADJECTIVAL.get(change.code, "")} - {""}
        if not any(a.lower() in draft.lower() for a in aliases):
            continue

        value = _number_pattern(change.current_yoy)
        patterns = (
            rf"(?:{words})[^0-9.]{{0,25}}{value}\s*%",   # "unchanged at 3.8%"
            rf"{value}\s*%[^0-9.]{{0,25}}(?:{words})",   # "0.5%, unchanged"
        )
        for pattern in patterns:
            match = re.search(pattern, draft, flags=re.IGNORECASE)
            if match:
                problems.append(
                    f"{change.code} described as unmoved near its {change.current_yoy:g}% "
                    f"headline ({match.group(0).strip()!r}), but "
                    f"{change.previous_period} -> {change.current_period} moved "
                    f"{change.delta_pp:+.2f}pp"
                )
                break
    return problems


def verify_draft(draft: str, source: str, changes: list) -> tuple:
    """Returns (blocking, advisory).

    The split is the point, not a detail. This gates a scheduled monthly job, so
    a false positive silently stops the newsletter — which makes severity a
    design decision, not formatting:

    - BLOCKING: the figure checks. Mechanically decidable. A pp delta either is
      one we computed (or one the source quotes) or it is not, and no sentence
      has to be understood to know which. This is what catches 2026-08-23.
    - ADVISORY: the prose heuristics. Deciding whether "unchanged" modifies the
      CPI level or the phrase after it, or whether "rose" refers to this
      country's print or to a forecast revision in the same clause, needs
      parsing. Two review rounds produced a fresh false positive for every fix,
      so they report instead of blocking. A wrong warning costs a line in the
      log; a wrong rejection costs the month's newsletter.

    The 2026-08-22 "unchanged" failure is prevented upstream by compare_periods,
    which hands the model CN at -0.50pp marked material, rather than by these
    heuristics catching the sentence after the fact.
    """
    blocking = check_figures(draft, source, changes)
    advisory = check_no_change_claims(draft, changes) + check_direction_words(draft, changes)
    return blocking, advisory


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
    changes = compare_periods(current_data)
    for c in changes:
        print(f"  {c.code}: {c.previous_period} {c.previous_yoy} -> "
              f"{c.current_period} {c.current_yoy} ({c.delta_pp:+.2f}pp)"
              f"{' MATERIAL' if c.is_material else ''}")

    cb_forecasts = load_json_safe(CB_FORECASTS_FILE)
    imf_forecasts = load_json_safe(IMF_FORECASTS_FILE)

    prompt = build_prompt(changes, cb_forecasts, imf_forecasts)
    source = source_blob(changes, cb_forecasts, imf_forecasts)

    # --- dry run ---
    if args.dry_run:
        print("\n=== PROMPT (dry run) ===\n")
        print(prompt)
        print(f"\nModel: {MODEL} | Max tokens: {MAX_TOKENS}")
        return

    # --- call API ---
    print(f"Calling {MODEL}...")
    body = generate_draft(prompt)

    # --- verify before anything is written or emailed (#117) ---
    # A draft that misstates the data is worse than no draft: it reads as a
    # finished editorial judgement. Fail the run instead of committing it. The
    # rejected text is printed so the failure alert's run log carries it.
    blocking, advisory = verify_draft(body, source, changes)
    for warning in advisory:
        print(f"  ! advisory: {warning}")
    if blocking:
        print("\n=== REJECTED DRAFT ===\n" + body + "\n=== END ===\n")
        for problem in blocking:
            print(f"  ✗ {problem}")
        raise SystemExit(
            f"Draft failed {len(blocking)} consistency check(s) against the source "
            f"data; nothing written. See the rejected text above."
        )
    print(f"Draft passed the blocking checks"
          f"{f'; {len(advisory)} advisory warning(s) above' if advisory else ''}.")

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
