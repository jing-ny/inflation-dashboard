/**
 * Index Page - Dynamic Data Loading
 * Loads all data from JSON files for consistency with country pages
 */

// Country page mapping
const COUNTRY_PAGES = {
    US: 'us.html', EA: 'ea.html', UK: 'uk.html', AU: 'au.html',
    CA: 'ca.html', NZ: 'nz.html', ZA: 'za.html', BR: 'br.html',
    MX: 'mx.html', JP: 'jp.html',
    KR: 'kr.html', SG: 'sg.html', IN: 'in.html', CN: 'cn.html', VE: 've.html'
};

// Target definitions (rarely change, ok to hardcode)
const TARGETS = {
    US: { value: 2.0, display: '2.0%', range: null },
    EA: { value: 2.0, display: '2.0%', range: null },
    UK: { value: 2.0, display: '2.0%', range: null },
    AU: { value: 2.5, display: '2-3%', range: [2, 3] },
    CA: { value: 2.0, display: '1-3%', range: [1, 3] },
    NZ: { value: 2.0, display: '1-3%', range: [1, 3] },
    ZA: { value: 3.0, display: '2-4%', range: [2, 4], recentChange: true },
    BR: { value: 3.0, display: '1.5-4.5%', range: [1.5, 4.5] },
    MX: { value: 3.0, display: '2-4%', range: [2, 4] },
    JP: { value: 2.0, display: '2.0%', range: null },
    KR: { value: 2.0, display: '2.0%', range: null },
    SG: { value: 2.0, display: '~2%', range: null },
    IN: { value: 4.0, display: '2-6%', range: [2, 6] },
    CN: { value: 3.0, display: '~3%', range: null },
    VE: { value: null, display: 'N/A', range: null }
};

// Display order - Japan added before China
const DISPLAY_ORDER = ['US', 'EA', 'UK', 'CA', 'AU', 'NZ', 'ZA', 'BR', 'MX', 'JP', 'KR', 'SG', 'IN', 'CN', 'VE'];

/**
 * Load and render the current inflation table
 */
async function loadInflationTable() {
    const tbody = document.getElementById('inflationTableBody');
    
    try {
        const response = await fetch('data/historical_cpi.json');
        const cpiData = await response.json();

        let html = '';
        const inflationFreshnessCounts = { green: 0, amber: 0, red: 0, unknown: 0 };
        for (const code of DISPLAY_ORDER) {
            const data = cpiData[code];
            if (!data) continue;

            const current = data.latest?.value ?? data.history?.[data.history.length - 1]?.value;
            const previous = data.previous?.value ?? data.history?.[data.history.length - 2]?.value;
            const currentDate = data.latest?.date ?? data.history?.[data.history.length - 1]?.date;
            const target = TARGETS[code];
            const page = COUNTRY_PAGES[code];

            // Calculate change
            const change = previous !== null ? (current - previous) : null;
            const changeStr = change !== null ? 
                (change > 0 ? `▲ ${change.toFixed(1)}` : change < 0 ? `▼ ${Math.abs(change).toFixed(1)}` : '—') : '—';
            const changeClass = change > 0.05 ? 'change-up' : change < -0.05 ? 'change-down' : '';

            // Determine status
            let statusClass, statusText;
            if (target.range) {
                if (current >= target.range[0] && current <= target.range[1]) {
                    statusClass = 'status-good';
                    statusText = 'In Range';
                } else if (current < target.range[0]) {
                    statusClass = 'status-alert';
                    statusText = 'Below Range';
                } else {
                    statusClass = 'status-warning';
                    statusText = 'Above Range';
                }
            } else {
                const diff = current - target.value;
                if (Math.abs(diff) <= 0.5) {
                    statusClass = 'status-good';
                    statusText = 'Near Target';
                } else if (diff < 0) {
                    statusClass = 'status-alert';
                    statusText = 'Below Target';
                } else {
                    statusClass = 'status-warning';
                    statusText = 'Above Target';
                }
            }

            // Special case for China (deflationary)
            if (code === 'CN' && current < 1) {
                statusClass = 'status-alert';
                statusText = 'Deflationary';
            }

            // Target display with optional "NEW" badge for recent changes
            const targetDisplay = target.recentChange
                ? `${target.display} <span class="target-new-badge" title="Target changed Nov 2025">NEW</span>`
                : target.display;

            // Freshness pill — CPI is monthly cadence (45d/90d thresholds)
            const fr = freshnessFor(currentDate, 'cpi');
            if (fr) inflationFreshnessCounts[fr.tier]++;
            else inflationFreshnessCounts.unknown++;
            const freshnessCell = freshnessPill(currentDate, 'cpi') || '—';

            html += `
                <tr onclick="window.location='${page}'" class="clickable-row">
                    <td class="country-cell">${data.flag || ''} ${data.name || code}</td>
                    <td class="value-cell"><strong>${current.toFixed(1)}%</strong></td>
                    <td>${previous !== null ? previous.toFixed(1) + '%' : '—'}</td>
                    <td class="${changeClass}">${changeStr}</td>
                    <td>${targetDisplay}</td>
                    <td><span class="${statusClass}">${statusText}</span></td>
                    <td>${formatDate(currentDate)}</td>
                    <td>${freshnessCell}</td>
                </tr>
            `;
        }

        tbody.innerHTML = html;

        // Footer summary for the Current Inflation table
        const inflationFooter = document.getElementById('inflationFreshnessFooter');
        if (inflationFooter) {
            const total = inflationFreshnessCounts.green + inflationFreshnessCounts.amber + inflationFreshnessCounts.red + inflationFreshnessCounts.unknown;
            const today = new Date().toISOString().slice(0, 10);
            const parts = [
                `<span class="freshness freshness-green">${inflationFreshnessCounts.green}</span> current`,
                `<span class="freshness freshness-amber">${inflationFreshnessCounts.amber}</span> stale`,
                `<span class="freshness freshness-red">${inflationFreshnessCounts.red}</span> very stale`,
            ];
            if (inflationFreshnessCounts.unknown) {
                parts.push(`<span class="freshness freshness-unknown">${inflationFreshnessCounts.unknown}</span> unknown`);
            }
            inflationFooter.innerHTML = `Data freshness as of ${today} — ${parts.join(' · ')} (${total} countries). ` +
                `Green ≤ 45d · Amber ≤ 90d · Red &gt; 90d since CPI release.`;
        }

    } catch (error) {
        console.error('Error loading inflation data:', error);
        tbody.innerHTML = '<tr><td colspan="8" class="error">Error loading data. Please refresh.</td></tr>';
    }
}

/**
 * Load and render the Inflation Outlook table from cb_forecasts.json + imf_forecasts.json
 */
async function loadOutlookTable() {
    const tbody = document.getElementById('outlookTableBody');
    const contextDiv = document.getElementById('outlookContext');

    // Dynamic year columns based on current year
    const currentYear = new Date().getFullYear();
    const nextYear = currentYear + 1;
    const currentYearStr = String(currentYear);
    const nextYearStr = String(nextYear);

    // Update table headers
    document.querySelector('.outlook-year-cb').textContent = `${currentYearStr} (CB)`;
    document.querySelector('.outlook-year-imf').textContent = `${currentYearStr} (IMF)`;
    document.querySelector('.outlook-year-next').textContent = nextYearStr;

    try {
        const [cbResponse, imfResponse, draftResponse] = await Promise.all([
            fetch('data/cb_forecasts.json'),
            fetch('data/imf_forecasts.json'),
            // Draft file may legitimately be 404 — it's only written when
            // a >1pp jump is blocked by the merge anomaly gate.
            fetch('data/cb_forecasts_draft.json').catch(() => null),
        ]);
        const forecastData = await cbResponse.json();
        const imfData = await imfResponse.json();

        // Pending-review map: country code -> { bank, delta, newProjections }.
        // Populated from cb_forecasts_draft.json only for entries that the
        // scraper actually blocked (>1pp jump). The draft file contains all
        // scraped forecasts, so we filter against the _metadata.blocked_countries
        // list emitted alongside.
        const pendingByCountry = {};
        if (draftResponse && draftResponse.ok) {
            try {
                const draftData = await draftResponse.json();
                const blockedSet = new Set(
                    (draftData._metadata?.blocked_countries || [])
                        .map(b => b.country)
                        .filter(Boolean),
                );
                if (blockedSet.size) {
                    const drafts = draftData.forecasts || [];
                    const iter = Array.isArray(drafts) ? drafts : Object.values(drafts);
                    for (const d of iter) {
                        if (!d || !d.country || !blockedSet.has(d.country)) continue;
                        const newProj = {};
                        for (const p of (d.projections || [])) newProj[p.year] = p.value;
                        const oldProj = forecastData.forecasts?.[d.country]?.projections || {};
                        let maxDelta = 0;
                        for (const [y, v] of Object.entries(newProj)) {
                            if (oldProj[y] != null) {
                                maxDelta = Math.max(maxDelta, Math.abs(oldProj[y] - v));
                            }
                        }
                        pendingByCountry[d.country] = {
                            bank: d.bank || d.country,
                            delta: maxDelta,
                            newProjections: newProj,
                        };
                    }
                }
            } catch (_) {
                // Draft file present but unparseable — ignore, don't break the table.
            }
        }

        // Show geopolitical context note
        if (imfData.note) {
            contextDiv.innerHTML = `<strong>⚠ Context:</strong> ${imfData.note}`;
        }

        // Render the source legend with the IMF link derived from the
        // imf_forecasts.json metadata so it rolls forward automatically
        // when fetch_imf_forecasts.py refreshes for a new WEO edition.
        // Falls back to the IMF datamapper if no edition-specific URL
        // has been recorded.
        const legend = document.getElementById('outlookSourceLegend');
        if (legend && imfData.version) {
            const imfUrl = imfData.publication_url
                || imfData.url
                || 'https://www.imf.org/external/datamapper/PCPIPCH@WEO';
            legend.innerHTML =
                `CB = Central bank's own projection. ` +
                `IMF = <a href="${imfUrl}" target="_blank" style="color: #6b7280;">` +
                `IMF WEO ${imfData.version}</a>.`;
        }

        const displayOrder = forecastData.display_order || DISPLAY_ORDER;
        let html = '';
        const freshnessCounts = { green: 0, amber: 0, red: 0, unknown: 0, paused: 0, pending: 0 };

        for (const code of displayOrder) {
            const forecast = forecastData.forecasts[code];
            if (!forecast) continue;

            const page = COUNTRY_PAGES[code];
            const proj = forecast.projections;
            const imfCountry = imfData.countries?.[code];
            const imfCurrentYear = imfCountry?.forecasts?.[currentYearStr];

            // Format source with date abbreviation
            const sourceDate = forecast.publication_date
                .replace('January', 'Jan').replace('February', 'Feb').replace('March', 'Mar')
                .replace('April', 'Apr').replace('September', 'Sep')
                .replace('December', 'Dec').replace('November', 'Nov').replace('October', 'Oct')
                .replace('2025', "'25").replace('2026', "'26");

            // Highlight divergence between CB and IMF
            const cbCurrentYear = proj[currentYearStr];
            let imfCell = '—';
            if (imfCurrentYear !== undefined && imfCurrentYear !== null) {
                const diff = cbCurrentYear !== null ? Math.abs(cbCurrentYear - imfCurrentYear) : 0;
                const divergeStyle = diff >= 0.5 ? ' style="color: #dc2626; font-weight: 600;"' : '';
                imfCell = `<span${divergeStyle}>${imfCurrentYear.toFixed(1)}%</span>`;
            }

            // Freshness pill. Precedence:
            //   1. If the scraper is explicitly disabled (UK/NZ/ZA per #31),
            //      render a distinct "paused" pill so the reader sees "we
            //      can't auto-update this" instead of conflating with a
            //      real-world stale source (CLAUDE.md #4 layer 3). A
            //      disabled scraper can't have produced a pending draft,
            //      so we short-circuit here.
            //   2. Otherwise render the green/amber/red freshness pill,
            //      AND append a "pending review" chip if there's a draft
            //      blocked by the 1pp anomaly gate (CLAUDE.md #2, #32).
            let freshnessCell;
            if (forecast.scraper_status === 'imf_sourced') {
                // Row tracks the IMF WEO (no CB scraper by design — #43/#44).
                // Still tally by freshness tier so the footer totals stay
                // honest and a stalled IMF pipeline shows up as very-stale.
                const fr = freshnessFor(forecast.publication_date, 'forecast');
                if (fr) freshnessCounts[fr.tier]++;
                else freshnessCounts.unknown++;
                freshnessCell = imfSourcedPill(forecast.publication_date, imfData.version);
            } else if (forecast.scraper_status === 'disabled') {
                freshnessCounts.paused++;
                freshnessCell = pausedPill(
                    forecast.scraper_status_issue,
                    forecast.scraper_status_reason,
                );
            } else {
                const fr = freshnessFor(forecast.publication_date, 'forecast');
                if (fr) freshnessCounts[fr.tier]++;
                else freshnessCounts.unknown++;
                freshnessCell = freshnessPill(forecast.publication_date, 'forecast') || '—';
                if (pendingByCountry[code]) {
                    freshnessCounts.pending++;
                    const p = pendingByCountry[code];
                    freshnessCell += ' ' + pendingReviewPill(p.delta, p.bank);
                }
            }

            html += `
                <tr onclick="window.location='${page}'" class="clickable-row">
                    <td class="country-cell">${forecast.flag} ${code}</td>
                    <td class="source-cell">${forecast.source} ${sourceDate}</td>
                    <td><strong>${cbCurrentYear !== null && cbCurrentYear !== undefined ? cbCurrentYear.toFixed(1) + '%' : '—'}</strong></td>
                    <td>${imfCell}</td>
                    <td>${proj[nextYearStr] !== null && proj[nextYearStr] !== undefined ? proj[nextYearStr].toFixed(1) + '%' : '—'}</td>
                    <td>${freshnessCell}</td>
                    <td class="assessment-cell">"${forecast.key_quote}"</td>
                </tr>
            `;
        }

        tbody.innerHTML = html;

        // Footer summary
        const footer = document.getElementById('outlookFreshnessFooter');
        if (footer) {
            const total = freshnessCounts.green + freshnessCounts.amber + freshnessCounts.red
                + freshnessCounts.unknown + freshnessCounts.paused;
            const today = new Date().toISOString().slice(0, 10);
            const parts = [
                `<span class="freshness freshness-green">${freshnessCounts.green}</span> current`,
                `<span class="freshness freshness-amber">${freshnessCounts.amber}</span> stale`,
                `<span class="freshness freshness-red">${freshnessCounts.red}</span> very stale`,
            ];
            if (freshnessCounts.paused) {
                parts.push(`<span class="freshness freshness-paused">${freshnessCounts.paused}</span> scraper paused`);
            }
            if (freshnessCounts.pending) {
                parts.push(`<span class="freshness freshness-pending">${freshnessCounts.pending}</span> pending review`);
            }
            if (freshnessCounts.unknown) {
                parts.push(`<span class="freshness freshness-unknown">${freshnessCounts.unknown}</span> unknown`);
            }
            footer.innerHTML = `Data freshness as of ${today} — ${parts.join(' · ')} (${total} sources). ` +
                `Green ≤ 120d · Amber ≤ 180d · Red &gt; 180d since publication. ` +
                `Paused rows are explicitly disabled scrapers awaiting fix; curated value preserved. ` +
                `Pending rows have a draft awaiting human review (see cb_forecasts_draft.json). ` +
                `<span class="freshness freshness-imf">IMF WEO</span> rows (CN, VE) track the IMF World Economic ` +
                `Outlook — the central bank publishes no standardized forecast, so there is no CB scraper to break.`;
        }

    } catch (error) {
        console.error('Error loading forecast data:', error);
        tbody.innerHTML = '<tr><td colspan="7" class="error">Error loading forecasts. Please refresh.</td></tr>';
    }
}

/**
 * Load and render the Policy Rates grid from cb_forecasts.json
 */
async function loadPolicyRates() {
    const grid = document.getElementById('ratesGrid');
    const subtitle = document.getElementById('policyRatesSubtitle');
    
    try {
        const response = await fetch('data/cb_forecasts.json');
        const forecastData = await response.json();
        
        // Update subtitle with date
        const lastUpdated = forecastData.metadata?.last_updated || 'latest';
        subtitle.textContent = `Current central bank interest rates (as of ${lastUpdated})`;

        const displayOrder = forecastData.display_order || DISPLAY_ORDER;
        let html = '';

        for (const code of displayOrder) {
            const forecast = forecastData.forecasts[code];
            if (!forecast || !forecast.policy_rate) continue;

            const rate = forecast.policy_rate;
            
            // Determine arrow direction from last_change
            let changeClass = '';
            if (rate.last_change.includes('↓')) changeClass = 'rate-down';
            else if (rate.last_change.includes('↑')) changeClass = 'rate-up';

            html += `
                <div class="rate-card">
                    <span class="rate-flag">${forecast.flag}</span>
                    <span class="rate-name">${forecast.source}</span>
                    <span class="rate-value">${rate.rate}</span>
                    <span class="rate-change ${changeClass}">${rate.last_change}</span>
                </div>
            `;
        }

        grid.innerHTML = html;

    } catch (error) {
        console.error('Error loading policy rates:', error);
        grid.innerHTML = '<div class="error">Error loading rates.</div>';
    }
}

/**
 * Format date string (YYYY-MM or YYYY-QN) to readable format
 */
function formatDate(dateStr) {
    if (!dateStr) return '—';
    
    // Handle quarterly format (e.g., "2025-Q3")
    if (dateStr.includes('Q')) {
        return dateStr;
    }
    
    // Handle monthly format (e.g., "2025-12")
    const [year, month] = dateStr.split('-');
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[parseInt(month) - 1]} ${year}`;
}

/**
 * Click-to-sort for data tables.
 * Stores original row order so the default can be restored.
 */
function makeSortable(table) {
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');
    if (!thead || !tbody) return;

    const ths = Array.from(thead.querySelectorAll('th'));
    let currentCol = -1;
    let ascending = true;
    let originalRows = null; // captured on first sort

    ths.forEach((th, colIndex) => {
        th.classList.add('sortable');
        th.innerHTML += ' <span class="sort-indicator">▲</span>';

        th.addEventListener('click', () => {
            // Capture original order once (after data has loaded)
            if (!originalRows) {
                originalRows = Array.from(tbody.querySelectorAll('tr'));
            }

            // Toggle direction or switch column
            if (currentCol === colIndex) {
                ascending = !ascending;
            } else {
                currentCol = colIndex;
                ascending = true;
            }

            // Update header indicators
            ths.forEach(h => {
                h.classList.remove('sort-active');
                const ind = h.querySelector('.sort-indicator');
                if (ind) ind.textContent = '▲';
            });
            th.classList.add('sort-active');
            th.querySelector('.sort-indicator').textContent = ascending ? '▲' : '▼';

            // Get rows and sort
            const rows = Array.from(tbody.querySelectorAll('tr'));

            rows.sort((a, b) => {
                const cellA = a.children[colIndex];
                const cellB = b.children[colIndex];
                if (!cellA || !cellB) return 0;

                let valA = cellA.textContent.trim();
                let valB = cellB.textContent.trim();

                // Extract numeric value (handle %, ▲, ▼, —, N/A)
                const numA = parseFloat(valA.replace(/[▲▼%,]/g, '').trim());
                const numB = parseFloat(valB.replace(/[▲▼%,]/g, '').trim());

                let result;
                if (!isNaN(numA) && !isNaN(numB)) {
                    result = numA - numB;
                } else if (!isNaN(numA)) {
                    result = -1; // numbers before non-numbers
                } else if (!isNaN(numB)) {
                    result = 1;
                } else {
                    result = valA.localeCompare(valB);
                }

                return ascending ? result : -result;
            });

            // Re-append in new order
            rows.forEach(r => tbody.appendChild(r));
        });
    });
}

// Initialize page
document.addEventListener('DOMContentLoaded', async () => {
    await Promise.all([
        loadInflationTable(),
        loadOutlookTable(),
        loadPolicyRates()
    ]);
    // Attach sort behaviour to both data tables
    document.querySelectorAll('.data-table').forEach(makeSortable);
});
