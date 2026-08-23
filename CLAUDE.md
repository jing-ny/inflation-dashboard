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
something is the normal case this rule was written for, not an escape from it.

**Not even an explicit request to commit directly.** "Just push it to main", "skip the PR",
"commit it directly" — Claude still opens a PR and says why. This rule binds Claude, not the
maintainer: they can push to `main` themselves whenever they like, and that is the right way for
that to happen. The only way to grant Claude that power is to change this rule — through a PR to
this file, reviewed and merged like anything else. A rule the system can waive on request is not
a rule.

**Scope is every repository change** — adding, deleting, renaming, or modifying any file.
Drafts, generated output, data JSON, docs, workflows, and this file all take a PR, and a new
file is not exempt for being untracked until you add it. The examples above are code-shaped for
brevity, not because prose is exempt: a hand-edit to a newsletter draft is a change to this repo.

**If you commit to `main` anyway, say so in the same reply.** Name the SHA and what it touched.
Do not let the maintainer find it in the log later. A disclosed mistake is recoverable; a quiet
one costs them the ability to trust the rest of the session's reporting.

**The one carve-out: workflow runs the maintainer did not have to ask for.** These five push to
`main` as `github-actions[bot]`: `update-data.yml`, `monitor-updates.yml`,
`auto-scrape-cb-forecasts.yml`, `newsletter-draft.yml`, `weekly-alert.yml`. Their pushes are
pre-approved — approved when the maintainer merged the workflow that does them.

The carve-out is scoped **by trigger, not by author**, because every one of these also accepts
`workflow_dispatch`, and "the bot pushed it" would otherwise let Claude launder any change
through a manual dispatch:

- **Covered:** `schedule` runs, and `newsletter-draft.yml`'s automatic `push` trigger on
  `docs/data/historical_cpi.json`. Nobody initiated these; they are the automation doing its job.
- **NOT covered:** any run Claude starts. `gh workflow run` is Claude acting, and a dispatch that
  writes to `main` needs the maintainer's go-ahead for that dispatch, plus disclosure of what it
  committed. Prefer a `dry_run` input where the workflow offers one. Verifying a freshly merged
  workflow is a legitimate reason to ask; it is not a reason to skip asking.

Editing these workflows, the scripts they run, or which paths they commit is an ordinary change
and takes a PR. Running one of their scripts locally and pushing the result is also an ordinary
change and takes a PR — the carve-out covers the workflow running itself, not its code run by
hand.

The carve-out waives only #6's delivery path. Rules 1-5 apply to everything these workflows
commit, exactly as they apply to a PR.

### 7. Every PR gets an independent Codex review before merge

Before any PR is merged, run an **independent code review with Codex** (the OpenAI Codex CLI, via the `/codex` skill) over the PR's diff and post its findings on the PR. This is a deliberately *independent* second opinion — separate from Claude, which authored the change, and from the maintainer's own review (#6). It must not be skipped on the grounds that Claude "already reviewed" the diff; the whole point is a different model's eyes.

Every Codex finding must be either fixed or explicitly dispositioned (with a one-line reason it's a non-issue) before merge. A clean Codex review is a **precondition** for merge — it does not replace the maintainer's approval required by #6.
