/**
 * Shared freshness helpers (used by index.html and country.js).
 *
 * Per CLAUDE.md #4 (stale data must be visibly stale): every value
 * in the dashboard is rendered with a freshness badge that ages from
 * green → amber → red against the source's expected publication cadence.
 */

/**
 * Parse the publication_date / latest.date strings used in the data files
 * into a millisecond timestamp. Day-of-month not specified ⇒ day 1.
 * Returns null if the string doesn't match any known shape.
 *
 * Handles:
 *   "2026-03-19"   YYYY-MM-DD (Fed, BoJ)
 *   "2026-03"      YYYY-MM    (historical CPI latest.date)
 *   "2026-Q1"      YYYY-Qn    (RBNZ quarterly CPI)
 *   "May 2026"     Month YYYY (RBA, BoC, BoE, ECB current curated entries)
 *   "Mar 2026"     Mon YYYY   (historic abbreviated curated entries)
 */
function parsePublicationDate(s) {
    if (!s || typeof s !== 'string') return null;
    s = s.trim();

    let m;
    if ((m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/))) {
        return Date.UTC(+m[1], +m[2] - 1, +m[3]);
    }
    if ((m = s.match(/^(\d{4})-(\d{2})$/))) {
        return Date.UTC(+m[1], +m[2] - 1, 1);
    }
    if ((m = s.match(/^(\d{4})-Q([1-4])$/i))) {
        // Use the last month of the quarter as the publication anchor —
        // Q1 data is published in/after March, etc.
        return Date.UTC(+m[1], (+m[2]) * 3 - 1, 1);
    }
    if ((m = s.match(/^([A-Za-z]+)\s+(\d{4})$/))) {
        const months = [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
        ];
        const needle = m[1].toLowerCase();
        const idx = months.findIndex(n => n.startsWith(needle));
        if (idx >= 0) return Date.UTC(+m[2], idx, 1);
    }
    return null;
}

/**
 * Compute freshness tier + relative-age label for a publication date.
 *
 *   kind = 'forecast'  thresholds 120d / 180d (quarterly CB publications)
 *   kind = 'cpi'       thresholds depend on the series' publication cadence:
 *                        monthly   75d / 120d
 *                        quarterly 135d / 225d (auto-detected from "YYYY-Qn")
 *
 * Why the CPI thresholds aren't tighter: official CPI is released a few weeks
 * after its reference month, and the age here is measured from the *reference
 * month* (day 1), not the release date. So the freshest-possible monthly print
 * is already ~45-75 days "old" by this measure, and a quarterly print (e.g. NZ)
 * stays current for a full quarter. Tighter limits flagged up-to-date data as
 * stale; these track the real cadence so green ≈ "this is the latest release",
 * amber ≈ "a release behind", red ≈ "genuinely lagging" (CLAUDE.md #4).
 *
 * Returns { tier, label, days } or null if the input is unparseable.
 */
function freshnessFor(publicationDate, kind) {
    const ts = parsePublicationDate(publicationDate);
    if (ts == null) return null;

    const days = Math.max(0, Math.floor((Date.now() - ts) / 86_400_000));
    let t1, t2;
    if (kind === 'forecast') {
        [t1, t2] = [120, 180];
    } else {
        const isQuarterly = /^\s*\d{4}-Q[1-4]\s*$/i.test(publicationDate || '');
        [t1, t2] = isQuarterly ? [135, 225] : [75, 120];
    }
    const tier = days <= t1 ? 'green' : days <= t2 ? 'amber' : 'red';

    let label;
    if (days < 30) {
        label = `${days}d`;
    } else if (days < 365) {
        label = `${Math.floor(days / 30)}mo`;
    } else {
        const years = Math.floor(days / 365);
        const months = Math.floor((days % 365) / 30);
        label = months ? `${years}y ${months}mo` : `${years}y`;
    }

    return { tier, label, days };
}

/**
 * Render a freshness pill as inline HTML. Empty string if the date is
 * unparseable — we never substitute placeholder values per CLAUDE.md #2.
 */
function freshnessPill(publicationDate, kind) {
    const fr = freshnessFor(publicationDate, kind);
    if (!fr) return '';
    return `<span class="freshness freshness-${fr.tier}" title="${fr.days} days since publication">${fr.label}</span>`;
}

/**
 * Render a "scraper paused" pill — distinct from green/amber/red. Used when
 * the auto-scraper for a source is explicitly disabled (e.g. UK / NZ / ZA
 * pending #6 / #10 / #12). The curated value is still shown, but the pill
 * tells the reader that the freshness signal here is *not* a real-world
 * stale-source signal — CLAUDE.md #4 layer 3.
 *
 * `issue` is an optional GitHub issue reference (e.g. "#10") used to link
 * the pill to the tracking ticket.
 */
function pausedPill(issue, reason) {
    const href = issue
        ? `https://github.com/jing-ny/inflation-dashboard/issues/${issue.replace('#', '')}`
        : null;
    const title = reason
        ? `Scraper paused: ${reason}`
        : 'Scraper paused; curated value preserved';
    const label = issue ? `⏸ paused (${issue})` : '⏸ paused';
    if (href) {
        return `<a href="${href}" target="_blank" class="freshness freshness-paused" title="${title}" style="text-decoration:none;">${label}</a>`;
    }
    return `<span class="freshness freshness-paused" title="${title}">${label}</span>`;
}

/**
 * Render an "IMF-sourced" pill — used for rows whose central bank publishes
 * no standardized inflation forecast (PBoC, BCV), so the Outlook value tracks
 * the IMF World Economic Outlook instead (#43 / #44).
 *
 * Unlike `pausedPill`, this is NOT a broken-scraper signal: there is no CB
 * scraper to break by design. The pill names the WEO edition so the reader
 * understands the value refreshes on the IMF's April/October cadence rather
 * than a frozen manual date. It still ages via the normal forecast thresholds
 * so that if the IMF pipeline itself stalls, the staleness stays visible
 * (CLAUDE.md #4) — a red tier flips the badge to the red treatment.
 *
 * `version` is the imf_forecasts.json `version` string (e.g. "April 2026").
 */
function imfSourcedPill(publicationDate, version) {
    const fr = freshnessFor(publicationDate, 'forecast');
    const shortVer = (version || publicationDate || '')
        .replace('January', 'Jan').replace('February', 'Feb').replace('March', 'Mar')
        .replace('April', 'Apr').replace('August', 'Aug').replace('September', 'Sep')
        .replace('October', 'Oct').replace('November', 'Nov').replace('December', 'Dec')
        .replace(/(\d{2})(\d{2})/, "'$2");
    const stale = fr && fr.tier === 'red';
    const cls = stale ? 'freshness-red' : 'freshness-imf';
    const age = fr ? `${fr.days} days since the ${version || 'WEO'} release` : 'release date unknown';
    const title = `Tracks the IMF World Economic Outlook (auto-updated each April & October). ` +
        `The central bank publishes no standardized inflation forecast, so there is no CB scraper for this row. ${age}.`;
    const label = `IMF WEO${shortVer ? ' ' + shortVer : ''}${stale ? ' · stale' : ''}`;
    return `<span class="freshness ${cls}" title="${title}">${label}</span>`;
}

/**
 * Render a "pending review" chip — used when the auto-scraper produced a
 * new value but the change exceeded the 1pp anomaly gate and was routed
 * to cb_forecasts_draft.json for manual review (CLAUDE.md #2: this row's
 * curated value is now known to be at-odds with the latest source data).
 *
 * `delta` is the largest absolute pp delta between old and new projections;
 * `bank` is the entity name shown in the tooltip.
 */
function pendingReviewPill(delta, bank) {
    const tip = bank && delta != null
        ? `Pending review: ${bank} produced a new projection ${delta.toFixed(2)}pp from the curated value`
        : 'Pending review — see cb_forecasts_draft.json';
    const label = delta != null ? `⚠ pending (Δ${delta.toFixed(1)}pp)` : '⚠ pending';
    return `<span class="freshness freshness-pending" title="${tip}">${label}</span>`;
}
