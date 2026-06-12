/**
 * Release Calendar Page (#85)
 *
 * Projects each country's next expected CPI print:
 *   next reference period = latest period in historical_cpi.json + 1 step
 *   expected publication  = end of that period + typical_lag_days
 *                           (typical_lag_days is an ESTIMATE — every date
 *                           rendered from it is labeled "est." per
 *                           CLAUDE.md #2; the agency calendar_url is the
 *                           authoritative schedule)
 *
 * A print whose expected date has passed is flagged "overdue" — that means
 * the dashboard's own pipeline should already have newer data, so overdue
 * here is an actionable staleness signal (CLAUDE.md #4), not a forecast.
 */

const CAL_COUNTRY_PAGES = {
    US: 'us.html', EA: 'ea.html', UK: 'uk.html', AU: 'au.html',
    CA: 'ca.html', NZ: 'nz.html', ZA: 'za.html', JP: 'jp.html',
    KR: 'kr.html', SG: 'sg.html', IN: 'in.html', CN: 'cn.html'
};

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/**
 * Next reference period after a "YYYY-MM" or "YYYY-Qn" period string.
 * Returns the same shape, or null if the input is unparseable.
 */
function nextPeriod(period) {
    let m;
    if ((m = period.match(/^(\d{4})-Q([1-4])$/i))) {
        const year = +m[1], q = +m[2];
        return q === 4 ? `${year + 1}-Q1` : `${year}-Q${q + 1}`;
    }
    if ((m = period.match(/^(\d{4})-(\d{2})/))) {
        const year = +m[1], month = +m[2];
        return month === 12
            ? `${year + 1}-01`
            : `${year}-${String(month + 1).padStart(2, '0')}`;
    }
    return null;
}

/**
 * Last day of a reference period (UTC ms), or null.
 */
function periodEnd(period) {
    let m;
    if ((m = period.match(/^(\d{4})-Q([1-4])$/i))) {
        // Day 0 of the month after the quarter's last month = quarter end
        return Date.UTC(+m[1], (+m[2]) * 3, 0);
    }
    if ((m = period.match(/^(\d{4})-(\d{2})/))) {
        return Date.UTC(+m[1], +m[2], 0);
    }
    return null;
}

function formatPeriod(period) {
    if (!period) return '—';
    if (period.includes('Q')) return period;
    const [y, mo] = period.split('-');
    return `${MONTH_NAMES[parseInt(mo, 10) - 1]} ${y}`;
}

function formatDay(ts) {
    const d = new Date(ts);
    return `${MONTH_NAMES[d.getUTCMonth()]} ${d.getUTCDate()}, ${d.getUTCFullYear()}`;
}

async function loadCalendar() {
    const tbody = document.getElementById('calendarTableBody');
    const note = document.getElementById('calendarNote');

    try {
        const [cpiResponse, calResponse] = await Promise.all([
            fetch('data/historical_cpi.json'),
            fetch('data/release_calendar.json'),
        ]);
        const cpiData = await cpiResponse.json();
        const calData = await calResponse.json();

        // Normalize "now" to the UTC calendar day. `expected` values are
        // midnight-UTC dates, so comparing against the raw timestamp made
        // "due today" span ±12h around that instant instead of the UTC day.
        const nowDate = new Date();
        const todayUtc = Date.UTC(
            nowDate.getUTCFullYear(), nowDate.getUTCMonth(), nowDate.getUTCDate());
        const rows = [];

        for (const [code, cal] of Object.entries(calData)) {
            if (code.startsWith('_')) continue;
            const country = cpiData[code];
            if (!country) continue;

            const latestPeriod = country.latest?.date
                ?? country.history?.[country.history.length - 1]?.date;
            if (!latestPeriod) continue;

            const next = nextPeriod(latestPeriod);
            const end = next ? periodEnd(next) : null;
            if (!next || end == null) continue;

            const expected = end + cal.typical_lag_days * 86_400_000;
            const daysAway = Math.round((expected - todayUtc) / 86_400_000);

            let status, statusClass;
            if (daysAway < 0) {
                status = `overdue ${-daysAway}d`;
                statusClass = 'cal-overdue';
            } else if (daysAway <= 7) {
                status = daysAway === 0 ? 'due today' : `in ${daysAway}d`;
                statusClass = 'cal-due-soon';
            } else {
                status = `in ${daysAway}d`;
                statusClass = 'cal-upcoming';
            }

            rows.push({
                code,
                flag: country.flag || '',
                name: country.name || code,
                agency: cal.agency,
                cadence: cal.cadence,
                nextRef: next,
                expected,
                daysAway,
                status,
                statusClass,
                calendarUrl: cal.calendar_url,
            });
        }

        rows.sort((a, b) => a.expected - b.expected);

        let html = '';
        for (const r of rows) {
            const page = CAL_COUNTRY_PAGES[r.code];
            html += `
                <tr onclick="window.location='${page}'" class="clickable-row">
                    <td class="country-cell">${r.flag} ${r.name}</td>
                    <td>${formatPeriod(r.nextRef)} CPI</td>
                    <td>${r.cadence}</td>
                    <td>${formatDay(r.expected)} <span class="cal-est" title="Estimated from the agency's typical publication lag (${calData[r.code].typical_lag_days}d after period end) — see the official calendar for the confirmed date">est.</span></td>
                    <td><span class="${r.statusClass}">${r.status}</span></td>
                    <td><a href="${r.calendarUrl}" target="_blank" rel="noopener" onclick="event.stopPropagation()">${r.agency} ↗</a></td>
                </tr>
            `;
        }

        tbody.innerHTML = html
            || '<tr><td colspan="6">No calendar data available.</td></tr>';

        if (note) {
            const overdue = rows.filter(r => r.daysAway < 0).length;
            const week = rows.filter(r => r.daysAway >= 0 && r.daysAway <= 7).length;
            note.textContent =
                `${week} release${week === 1 ? '' : 's'} expected within 7 days · `
                + `${overdue} overdue. All dates are estimates derived from each `
                + `agency's typical publication lag; click through to the official `
                + `calendar for confirmed dates. "Overdue" means this dashboard's `
                + `data pipeline should already have a newer print — treat it as `
                + `a staleness signal.`;
        }

    } catch (error) {
        console.error('Error loading release calendar:', error);
        tbody.innerHTML =
            '<tr><td colspan="6" class="error">Error loading calendar. Please refresh.</td></tr>';
    }
}

document.addEventListener('DOMContentLoaded', loadCalendar);
