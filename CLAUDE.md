# CLAUDE.md

Project-specific guidance for Claude Code working on `inflation-dashboard`.

## Principles

### No manual data entry as a fallback

When a data source breaks (scraper 404, WAF block, restructured HTML, PDF table that won't extract cleanly), **do not** propose "mark this source as manual-entry" as a solution — even if the publication is infrequent (e.g. quarterly).

This dashboard is automation-first. The maintenance cost of remembering to manually update a JSON every quarter compounds with every source we add, and the dashboard's "set it and forget it" model breaks the moment we accept hand-edited data alongside scraped data.

When automation is hard, the options are:

1. **Fix it properly** — new URL pattern, new dependency (`curl_cffi`, `pdfplumber`, headless browser), new extractor.
2. **Defer it** — leave the issue open, accept that the source goes stale until someone has time to do option 1.

That's it. "Just enter it by hand" is not on the menu.
