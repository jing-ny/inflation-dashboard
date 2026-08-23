# CLAUDE.md

Project-specific guidance for Claude Code (and humans) working on `inflation-dashboard`.

## Principles

### 1. No manual data entry as a fallback

When a data source breaks (scraper 404, WAF block, restructured HTML, PDF table that won't extract cleanly), **do not** propose "mark this source as manual-entry" as a solution — even if the publication is infrequent (e.g. quarterly).

This dashboard is automation-first. The maintenance cost of remembering to manually update a JSON every quarter compounds with every source we add, and the "set it and forget it" model breaks the moment we accept hand-edited data alongside scraped data.

When automation is hard, the options are:

1. **Fix it properly** — new URL pattern, new dependency (`curl_cffi`, `pdfplumber`, headless browser), new extractor.
2. **Defer it** — leave the issue open, accept that the source goes stale until someone has time to do option 1.

That's it. "Just enter it by hand" is not on the menu.

### 2. Every number is validated, or labeled as not yet validated

Every numeric value displayed by the dashboard must either:

- have passed the project's validation (anomaly detector, range checks, source consistency check), **or**
- carry an explicit unvalidated flag in the data record (e.g. `"validated": false` or `"status": "draft"`) and be presented to readers as such.

Unmarked numbers are presumed validated. Don't add a number without making this state explicit, and don't silently pass an unvalidated number through to the public dashboard.

### 3. Every record carries provenance

For any data point we publish — historical CPI, central-bank forecast, IMF projection — the underlying record must include:

- `source_url`: the canonical page or PDF the value was pulled from
- `fetch_date` (for scraped data) or `source_date` (for forecasts): when we got it / what publication it's from

If a number can't be traced back to an original source via fields on the record itself, it doesn't belong in the dataset. "The link is documented in the README" is not enough — provenance lives on the record.

### 4. Stale data must be visibly stale

If a source breaks, the dashboard should communicate that the value is out of date — not silently keep showing the last successful fetch as if it were current. A frozen number with no staleness indicator misleads readers and makes "no manual entry" (#1) materially worse, because broken sources stop being noticed.

Acceptable patterns: a "last updated" badge per country/source, a visual greying/strikethrough when the gap exceeds the publication cadence, or omitting the country entirely. Whatever the mechanism, "no signal" is not a valid state for a broken source.

### 5. Trust the anomaly detector — don't silence the alarm

When `STEP_THRESHOLD_PP` (or any future check) fires, treat it as a signal that something's wrong with the source data, the scraper, or the comparison logic — **not** as a CI annoyance to be raised, looser-ed, or `|| true`'d away.

If anomalies fire on real data, the fix is to investigate *why* — fetcher bug, scraper miscapture, source revision, threshold being applied to the wrong neighbor — and address the cause. Bumping the threshold or adding broad exemptions is a strict last resort, and never the first move.

### 6. Every change goes through an issue and a PR — never merge without review

For any change to this repo, the workflow is: **open a GitHub issue** describing the problem/intent, then **open a pull request** (on a branch, never committing straight to `main`) that references it, and **wait for the maintainer's explicit review and approval before merging**.

Do not commit directly to `main`, do not self-merge, and do not merge a PR on the maintainer's behalf — even for a one-line fix, a "trivial" cleanup, or something that looks obviously correct. The issue gives the change a paper trail; the PR gives the maintainer a reviewable diff and the chance to say no. "It's small" is not an exception.

Claude may create the issue, the branch, and the PR, and may push follow-up commits to that PR's branch in response to review — but the **merge** is the maintainer's action, not Claude's.

**"You told me to" is not an exception either.** A direct instruction — "fix it", "update it",
"just do it", "go ahead", "yes" — authorizes the *work*. It does not authorize a different
*delivery path*. Every one of those means **open a PR that does it**. The maintainer asking for
something is the normal case this rule was written for, not an escape from it. If they want a
direct commit, they will say so in those words; do not infer it from urgency, brevity, or a
second request.

**Scope is every tracked file, not just code.** Drafts, generated output, data JSON, docs,
workflows, and this file all take a PR. The examples above are code-shaped for brevity, not
because prose is exempt — a hand-edit to a newsletter draft is a change to this repo.

**If you commit to `main` anyway, say so in the same reply.** Name the SHA and what it touched.
Do not let the maintainer find it in the log later. A disclosed mistake is recoverable; a quiet
one costs them the ability to trust the rest of the session's reporting.

**The one carve-out: scheduled automation.** `update-data.yml`, `monitor-updates.yml`,
`auto-scrape-cb-forecasts.yml`, `newsletter-draft.yml`, and `weekly-alert.yml` push to `main` as
`github-actions[bot]`. That is pre-approved — the maintainer approved it when they merged the
workflow that does it. The carve-out is for **the bot running merged workflow code**, and nothing
else. Claude running the same script locally and pushing the result is an ordinary change and
takes a PR; so does changing what those workflows commit.

### 7. Every PR gets an independent Codex review before merge

Before any PR is merged, run an **independent code review with Codex** (the OpenAI Codex CLI, via the `/codex` skill) over the PR's diff and post its findings on the PR. This is a deliberately *independent* second opinion — separate from Claude, which authored the change, and from the maintainer's own review (#6). It must not be skipped on the grounds that Claude "already reviewed" the diff; the whole point is a different model's eyes.

Every Codex finding must be either fixed or explicitly dispositioned (with a one-line reason it's a non-issue) before merge. A clean Codex review is a **precondition** for merge — it does not replace the maintainer's approval required by #6.
