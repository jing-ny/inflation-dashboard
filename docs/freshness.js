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
 *   kind = 'cpi'       thresholds  45d /  90d (monthly statistical agencies)
 *
 * Returns { tier, label, days } or null if the input is unparseable.
 */
function freshnessFor(publicationDate, kind) {
    const ts = parsePublicationDate(publicationDate);
    if (ts == null) return null;

    const days = Math.max(0, Math.floor((Date.now() - ts) / 86_400_000));
    const [t1, t2] = kind === 'forecast' ? [120, 180] : [45, 90];
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
