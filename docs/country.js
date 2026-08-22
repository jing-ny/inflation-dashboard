/**
 * Inflation Dashboard - Country Page Module
 * 
 * Shared JavaScript for all country detail pages.
 * Loads ALL data from JSON files for consistency:
 * - data/historical_cpi.json - CPI history
 * - data/cb_forecasts.json - Central bank forecasts (single source of truth)
 * - data/imf_forecasts.json - IMF WEO forecasts
 * 
 * Updated: 2026-01-26
 */

// ============================================================
// STATIC DATA (rarely changes, OK to hardcode)
// ============================================================

// Target descriptions and quotes
const TARGET_INFO = {
    US: {
        description: 'The Federal Reserve targets 2% inflation as measured by the annual change in the price index for personal consumption expenditures (PCE).',
        quote: 'The Committee judges that inflation at the rate of 2 percent, as measured by the annual change in the price index for personal consumption expenditures, is most consistent over the longer run with the Federal Reserve\'s statutory mandate.',
        quoteSource: 'FOMC Statement on Longer-Run Goals, January 2024'
    },
    CA: {
        description: 'The Bank of Canada targets 2% CPI inflation, the midpoint of a 1-3% target range. The inflation-control target has been in place since 1991.',
        quote: 'The target aims to keep total CPI inflation at the 2 per cent midpoint of a target range of 1 to 3 per cent over the medium term.',
        quoteSource: 'Bank of Canada Inflation-Control Target'
    },
    UK: {
        description: 'The Bank of England has a 2% CPI inflation target set by the government. If inflation deviates by more than 1 percentage point, the Governor must write a letter to the Chancellor explaining why.',
        quote: 'The inflation target of 2% is expressed in terms of an annual rate of inflation based on the Consumer Prices Index (CPI).',
        quoteSource: 'Bank of England Monetary Policy Framework'
    },
    EA: {
        description: 'The ECB aims for 2% inflation over the medium term, measured by the Harmonised Index of Consumer Prices (HICP).',
        quote: 'The Governing Council considers that price stability is best maintained by aiming for a 2% inflation target over the medium term. This target is symmetric.',
        quoteSource: 'ECB Monetary Policy Strategy, July 2021'
    },
    AU: {
        description: 'The RBA targets inflation of 2-3% on average over time, focusing on underlying (trimmed mean) inflation.',
        quote: 'The Governor and the Treasurer have agreed that the appropriate target for monetary policy in Australia is to achieve an inflation rate of 2–3 per cent, on average, over time.',
        quoteSource: 'Statement on the Conduct of Monetary Policy, September 2024'
    },
    NZ: {
        description: 'The RBNZ targets 1-3% CPI inflation, with a focus on keeping inflation near the 2% midpoint.',
        quote: 'The Reserve Bank shall formulate and implement monetary policy with the goals of keeping future annual CPI inflation between 1 and 3 percent over the medium term, with a focus on keeping future inflation near the 2 percent mid-point.',
        quoteSource: 'Remit for the Monetary Policy Committee, 2024'
    },
    ZA: {
        description: 'The SARB targets 3% CPI inflation with a ±1 percentage point tolerance band (2-4%). This replaced the previous 3-6% target range in November 2025—the first change in 25 years. The new lower target aims to anchor inflation expectations and reduce borrowing costs over time.',
        quote: 'South Africa\'s inflation target is 3%, with a tolerance band of plus or minus 1 percentage point. This target refers to the headline change in the consumer price index.',
        quoteSource: 'SARB Monetary Policy Framework, November 2025'
    },
    JP: {
        description: 'The Bank of Japan targets 2% CPI inflation, a goal adopted in January 2013 after decades of deflation. Japan achieved sustained inflation above target for the first time since the 1990s in 2022-2024.',
        quote: 'The Bank will achieve the price stability target of 2 percent in terms of the year-on-year rate of change in the consumer price index (CPI) at the earliest possible time.',
        quoteSource: 'Bank of Japan Price Stability Target'
    },
    KR: {
        description: 'The Bank of Korea targets 2% CPI inflation. The inflation targeting framework was adopted in 1998 following the Asian financial crisis. Korea has maintained relatively stable inflation near target in recent years.',
        quote: 'The Bank of Korea sets the inflation target at 2% in terms of consumer price inflation.',
        quoteSource: 'Bank of Korea Monetary Policy'
    },
    SG: {
        description: 'The Monetary Authority of Singapore (MAS) does not have an explicit inflation target. Instead, MAS uses the exchange rate as its primary monetary policy tool to maintain price stability. The implied target is around 2% for medium-term price stability.',
        quote: 'MAS conducts monetary policy by managing the trade-weighted exchange rate of the Singapore dollar within an undisclosed policy band.',
        quoteSource: 'MAS Monetary Policy Framework'
    },
    CN: {
        description: 'China sets an annual CPI target, typically around 3%, as part of its government work report. The target is more of a ceiling than a strict objective.',
        quote: 'We will keep the consumer price index increase at around 3 percent.',
        quoteSource: 'Government Work Report, March 2024'
    }
};

// Data source information (links rarely change)
const DATA_SOURCES = {
    US: [
        { label: 'CPI Data', value: 'Bureau of Labor Statistics', url: 'https://www.bls.gov/cpi/' },
        { label: 'Series ID', value: 'CPIAUCNS (CPI-U All Items)', url: 'https://fred.stlouisfed.org/series/CPIAUCNS' },
        { label: 'Core CPI', value: 'CPILFESL (All Items Less Food & Energy)', url: 'https://fred.stlouisfed.org/series/CPILFESL' },
        { label: 'PCE', value: 'PCEPI (PCE Price Index)', url: 'https://fred.stlouisfed.org/series/PCEPI' },
        { label: 'Core PCE', value: 'PCEPILFE (PCE ex Food & Energy)', url: 'https://fred.stlouisfed.org/series/PCEPILFE' },
        { label: 'Forecasts', value: 'FOMC Summary of Economic Projections', url: 'https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm' },
        { label: 'Target', value: 'FOMC Statement on Longer-Run Goals', url: 'https://www.federalreserve.gov/monetarypolicy/review-of-monetary-policy-strategy-tools-and-communications-statement-on-longer-run-goals-monetary-policy-strategy.htm' }
    ],
    CA: [
        { label: 'CPI Data', value: 'Statistics Canada via FRED', url: 'https://fred.stlouisfed.org/series/CANCPIALLMINMEI' },
        { label: 'Series ID', value: 'CANCPIALLMINMEI (OECD)', url: 'https://fred.stlouisfed.org/series/CANCPIALLMINMEI' },
        { label: 'Forecasts', value: 'Bank of Canada Monetary Policy Report', url: 'https://www.bankofcanada.ca/publications/mpr/' },
        { label: 'Target', value: 'BoC Inflation-Control Target', url: 'https://www.bankofcanada.ca/rates/indicators/key-variables/inflation-control-target/' }
    ],
    UK: [
        { label: 'CPI Data', value: 'Office for National Statistics via FRED', url: 'https://fred.stlouisfed.org/series/GBRCPIALLMINMEI' },
        { label: 'Series ID', value: 'GBRCPIALLMINMEI (OECD)', url: 'https://fred.stlouisfed.org/series/GBRCPIALLMINMEI' },
        { label: 'Forecasts', value: 'Bank of England Monetary Policy Report', url: 'https://www.bankofengland.co.uk/monetary-policy-report' },
        { label: 'Target', value: 'BoE Monetary Policy Framework', url: 'https://www.bankofengland.co.uk/monetary-policy' }
    ],
    EA: [
        { label: 'HICP Data', value: 'Eurostat via ECB Data Portal', url: 'https://data.ecb.europa.eu/data/datasets/ICP' },
        { label: 'Series ID', value: 'ICP.M.U2.N.000000.4.ANR', url: 'https://data.ecb.europa.eu/' },
        { label: 'Forecasts', value: 'ECB Staff Macroeconomic Projections', url: 'https://www.ecb.europa.eu/press/projections/html/index.en.html' },
        { label: 'Target', value: 'ECB Monetary Policy Strategy', url: 'https://www.ecb.europa.eu/mopo/strategy/html/index.en.html' }
    ],
    AU: [
        { label: 'CPI Data (headline)', value: 'ABS Monthly CPI Indicator', url: 'https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/' },
        { label: 'Historical series', value: 'ABS Quarterly CPI (FRED relay fallback)', url: 'https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/' },
        { label: 'Forecasts', value: 'RBA Statement on Monetary Policy', url: 'https://www.rba.gov.au/publications/smp/' },
        { label: 'Target', value: 'Statement on Conduct of Monetary Policy', url: 'https://www.rba.gov.au/monetary-policy/framework/stmt-conduct-mp.html' }
    ],
    NZ: [
        { label: 'CPI Data', value: 'Stats NZ via FRED', url: 'https://fred.stlouisfed.org/series/NZLCPIALLQINMEI' },
        { label: 'Series ID', value: 'NZLCPIALLQINMEI (OECD, Quarterly)', url: 'https://fred.stlouisfed.org/series/NZLCPIALLQINMEI' },
        { label: 'Forecasts', value: 'RBNZ Monetary Policy Statement', url: 'https://www.rbnz.govt.nz/monetary-policy/monetary-policy-statement' },
        { label: 'Target', value: 'Remit for the MPC', url: 'https://www.rbnz.govt.nz/monetary-policy/about-monetary-policy/remit-for-the-monetary-policy-committee' }
    ],
    ZA: [
        { label: 'CPI Data', value: 'Statistics South Africa via FRED', url: 'https://fred.stlouisfed.org/series/ZAFCPIALLMINMEI' },
        { label: 'Series ID', value: 'ZAFCPIALLMINMEI (OECD)', url: 'https://fred.stlouisfed.org/series/ZAFCPIALLMINMEI' },
        { label: 'Forecasts', value: 'SARB Monetary Policy Committee Statements', url: 'https://www.resbank.co.za/en/home/publications/publication-detail-pages/statements/monetary-policy-statements' },
        { label: 'Target', value: 'SARB Monetary Policy (3% target, Nov 2025)', url: 'https://www.resbank.co.za/en/home/what-we-do/monetary-policy' }
    ],
    JP: [
        { label: 'CPI Data', value: 'Statistics Bureau of Japan via FRED', url: 'https://fred.stlouisfed.org/series/JPNCPALTT01GYM659N' },
        { label: 'Series ID', value: 'JPNCPALTT01GYM659N (OECD, COICOP 2018)', url: 'https://fred.stlouisfed.org/series/JPNCPALTT01GYM659N' },
        { label: 'Forecasts', value: 'BoJ Outlook for Economic Activity and Prices', url: 'https://www.boj.or.jp/en/mopo/outlook/' },
        { label: 'Target', value: 'BoJ Price Stability Target', url: 'https://www.boj.or.jp/en/mopo/outline/index.htm' }
    ],
    KR: [
        { label: 'CPI Data', value: 'Statistics Korea (KOSTAT), via OECD SDMX', url: 'https://kostat.go.kr/en/' },
        { label: 'Series', value: 'OECD SDMX KOR.M.N.CPI.PA._T.N.GY', url: 'https://data-explorer.oecd.org/vis?df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_PRICES%40DF_PRICES_ALL&dq=KOR.M.N.CPI.PA._T.N.GY' },
        { label: 'Forecasts', value: 'Bank of Korea Economic Outlook', url: 'https://www.bok.or.kr/eng/main/main.do' },
        { label: 'Target', value: 'Bank of Korea Monetary Policy', url: 'https://www.bok.or.kr/eng/main/main.do' }
    ],
    SG: [
        { label: 'CPI Data', value: 'Department of Statistics Singapore', url: 'https://www.singstat.gov.sg/' },
        { label: 'FRED Series', value: 'SGPCPIALLMINMEI', url: 'https://fred.stlouisfed.org/series/SGPCPIALLMINMEI' },
        { label: 'Forecasts', value: 'MAS Survey of Professional Forecasters', url: 'https://www.mas.gov.sg/monetary-policy' },
        { label: 'Policy', value: 'MAS Monetary Policy', url: 'https://www.mas.gov.sg/monetary-policy' }
    ],
    CN: [
        { label: 'CPI Data', value: 'NBS China via FRED', url: 'https://fred.stlouisfed.org/series/CHNCPIALLMINMEI' },
        { label: 'Series ID', value: 'CHNCPIALLMINMEI (OECD)', url: 'https://fred.stlouisfed.org/series/CHNCPIALLMINMEI' },
        { label: 'Forecasts', value: 'IMF World Economic Outlook', url: 'https://www.imf.org/en/Publications/WEO' },
        { label: 'Target', value: 'Government Work Report', url: 'http://english.www.gov.cn/' }
    ]
};

// ============================================================
// MAIN INITIALIZATION FUNCTION
// ============================================================

/**
 * Initialize a country page
 * @param {string} countryCode - Two-letter country code (US, UK, etc.)
 */
async function initCountryPage(countryCode) {
    try {
        // Load CPI data + targets (data/targets.json is the single source
        // of truth for inflation targets, #82 — NOT the per-country target
        // field historical_cpi.json used to carry, which drifted once: ZA
        // showed the pre-Nov-2025 4.5% target for months)
        const [cpiResponse, targetsResponse] = await Promise.all([
            fetch('data/historical_cpi.json'),
            // Catch network failure here so a rejected targets fetch can't
            // reject the Promise.all and abort the whole page — CPI data
            // still renders with target UI degraded to N/A.
            fetch('data/targets.json').catch((e) => {
                console.error('Error fetching targets.json:', e);
                return null;
            }),
        ]);
        const allCpiData = await cpiResponse.json();
        const countryData = allCpiData[countryCode];

        let targetDef = null;
        if (targetsResponse) {
            try {
                const targetsData = await targetsResponse.json();
                targetDef = targetsData[countryCode] || null;
            } catch (e) {
                // Corrupt targets.json degrades target UI to N/A —
                // never fall back to a second definition of the target.
                console.error('Error parsing targets.json:', e);
            }
        }

        if (!countryData) {
            showError('Country data not found');
            return;
        }

        // Update metrics cards
        updateMetrics(countryCode, countryData, targetDef);

        // Render historical chart
        renderHistoricalChart(countryCode, countryData, targetDef);

        // Render supplementary metrics (Core CPI, PCE) if available
        renderSupplementaryMetrics(countryData);

        // Render forecast table (loads from cb_forecasts.json and imf_forecasts.json)
        await renderForecastTable(countryCode);

        // Render target information
        renderTargetInfo(countryCode, targetDef);

        // Render data sources
        renderDataSources(countryCode);

    } catch (error) {
        console.error('Error loading country data:', error);
        showError('Error loading data. Please refresh the page.');
    }
}

// ============================================================
// METRICS UPDATE
// ============================================================

function updateMetrics(countryCode, data, targetDef) {
    const current = data.latest;
    const previous = data.previous;
    const target = Number.isFinite(targetDef?.value) ? targetDef.value : null;

    // Current inflation
    const currentEl = document.getElementById('currentValue');
    if (currentEl && current) {
        currentEl.textContent = current.value.toFixed(1) + '%';
        currentEl.className = 'metric-value ' + getValueClass(current.value, target);
    }

    const currentDateEl = document.getElementById('currentDate');
    if (currentDateEl && current) {
        const dateText = formatDate(current.date);
        // CLAUDE.md #4: append a freshness pill aged against the CPI cadence
        // (monthly 75d/120d, quarterly 135d/225d — see freshness.js). Cadence
        // comes from the record's `frequency` field, not the date shape. The
        // pill is loaded from freshness.js; defensively check before calling.
        const pill = typeof freshnessPill === 'function'
            ? freshnessPill(current.date, 'cpi', data.frequency)
            : '';
        // Flag flash/provisional estimates (e.g. EA HICP flash, #60).
        const flash = current.provisional === true
            ? ' <span title="Flash estimate — provisional, not the final print"'
              + ' style="font-size:0.75rem;color:#b45309;background:#fef3c7;'
              + 'padding:1px 6px;border-radius:4px;margin-left:6px;">flash estimate</span>'
            : '';
        currentDateEl.innerHTML = (pill ? `${dateText} ${pill}` : dateText) + flash;
    }

    // Previous
    const prevEl = document.getElementById('previousValue');
    if (prevEl && previous) {
        prevEl.textContent = previous.value.toFixed(1) + '%';
    }

    const prevDateEl = document.getElementById('previousDate');
    if (prevDateEl && previous) {
        prevDateEl.textContent = formatDate(previous.date);
    }

    // Target
    const targetEl = document.getElementById('targetValue');
    if (targetEl) {
        targetEl.textContent = targetDef?.display
            || (target !== null ? target.toFixed(1) + '%' : 'N/A');
    }

    // Status vs target
    const statusEl = document.getElementById('statusValue');
    const statusDetailEl = document.getElementById('statusDetail');
    if (statusEl && current) {
        const diff = target !== null ? current.value - target : null;
        statusEl.textContent = diff !== null ? ((diff >= 0 ? '+' : '') + diff.toFixed(1) + 'pp') : 'N/A';
        statusEl.className = 'metric-value ' + (target !== null ? getValueClass(current.value, target) : 'neutral');
        
        if (statusDetailEl) {
            if (diff === null) statusDetailEl.textContent = 'No target set';
            else if (diff > 2) statusDetailEl.textContent = 'Well above target';
            else if (diff > 0.5) statusDetailEl.textContent = 'Above target';
            else if (diff < -0.5) statusDetailEl.textContent = 'Below target';
            else statusDetailEl.textContent = 'Near target';
        }
    }
}

// ============================================================
// SUPPLEMENTARY METRICS (Core CPI, PCE, Core PCE)
// ============================================================

function renderSupplementaryMetrics(data) {
    const section = document.getElementById('supplementarySection');
    const container = document.getElementById('supplementaryMetrics');
    if (!section || !container || !data.supplementary) return;

    const sup = data.supplementary;
    let html = '';

    for (const [key, metric] of Object.entries(sup)) {
        const val = metric.latest.value;
        const dateStr = formatDate(metric.latest.date);
        const fredUrl = metric.source_url
            || ('https://fred.stlouisfed.org/series/' + metric.fred_series);
        const colorClass = getValueClass(val, 2.0);
        // CLAUDE.md #4 (#99): age these cards like every other CPI value —
        // they froze for months once with no visible signal.
        const pill = typeof freshnessPill === 'function'
            ? freshnessPill(metric.latest.date, 'cpi')
            : '';

        html += `
            <div class="metric-card">
                <div class="metric-label">${metric.name}</div>
                <div class="metric-value ${colorClass}">${val.toFixed(1)}%</div>
                <div class="metric-detail">${dateStr}${pill ? ' ' + pill : ''} · <a href="${fredUrl}" target="_blank" style="color:#2563eb;text-decoration:none;font-size:0.8rem;">${metric.fred_series}</a></div>
            </div>
        `;
    }

    container.innerHTML = html;
    section.style.display = '';
}

// ============================================================
// HISTORICAL CHART
// ============================================================

function renderHistoricalChart(countryCode, data, targetDef) {
    const canvas = document.getElementById('historyChart');
    if (!canvas || !data.history || data.history.length === 0) return;

    const target = Number.isFinite(targetDef?.value) ? targetDef.value : null;
    const history = data.history;

    // Prepare chart data
    const labels = history.map(d => d.date);
    const values = history.map(d => d.value);

    const datasets = [
        {
            label: 'YoY Inflation',
            data: values,
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37, 99, 235, 0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 0,
            pointHoverRadius: 4
        }
    ];

    // Target line — omitted entirely when targets.json has no entry for
    // the country (no line at 0, no dangling legend entry)
    if (target !== null) {
        datasets.push({
            label: 'Target',
            data: history.map(() => target),
            borderColor: '#dc2626',
            borderDash: [5, 5],
            borderWidth: 2,
            pointRadius: 0,
            fill: false
        });
    }

    new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                },
                tooltip: {
                    callbacks: {
                        title: (items) => formatDate(items[0].label),
                        label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}%`
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxTicksLimit: 12,
                        callback: function(val, index) {
                            const label = this.getLabelForValue(val);
                            // Show only January of each year
                            if (label.endsWith('-01') || label.endsWith('-Q1')) {
                                return label.substring(0, 4);
                            }
                            return null;
                        },
                        font: { size: 11 },
                        color: '#6b7280'
                    },
                    grid: { display: false }
                },
                y: {
                    ticks: {
                        callback: (v) => v + '%',
                        font: { size: 11 },
                        color: '#6b7280'
                    },
                    grid: { color: '#e5e7eb' }
                }
            }
        }
    });
}

// ============================================================
// FORECAST TABLE - LOADS FROM JSON FILES
// ============================================================

async function renderForecastTable(countryCode) {
    const container = document.getElementById('forecastTable');
    if (!container) return;

    let cbForecast = null;
    let cbData = null;
    let imfData = null;
    let imfForecast = null;

    // Load central bank forecasts from JSON (single source of truth)
    try {
        const cbResponse = await fetch('data/cb_forecasts.json');
        if (cbResponse.ok) {
            cbData = await cbResponse.json();
            cbForecast = cbData.forecasts?.[countryCode];
        }
    } catch (e) {
        console.log('CB forecasts not available:', e);
    }

    // Load IMF forecasts
    try {
        const imfResponse = await fetch('data/imf_forecasts.json');
        if (imfResponse.ok) {
            imfData = await imfResponse.json();
            imfForecast = imfData?.countries?.[countryCode];
        }
    } catch (e) {
        console.log('IMF forecasts not available:', e);
    }

    if (!cbForecast && !imfForecast) {
        container.innerHTML = '<p>No forecast data available for this country.</p>';
        return;
    }

    // Some countries (e.g. CN, VE) have no standardized central-bank forecast,
    // so their cb_forecasts.json row is a placeholder that just mirrors the IMF
    // WEO (scraper_status: "imf_sourced"). Such a row is NOT a genuine central
    // bank source — rendering it alongside the IMF row would show "IMF vs IMF"
    // (#67). Treat it as absent for branching so we fall through to the
    // IMF-only view, while still surfacing its note for context.
    const cbIsImfPlaceholder = !!cbForecast && cbForecast.scraper_status === 'imf_sourced';
    const cbIsReal = !!cbForecast && !cbIsImfPlaceholder;

    let html = '';

    // If we have both a genuine CB forecast and IMF, show comparison table
    if (cbIsReal && imfForecast && imfForecast.forecasts) {
        const imfYears = Object.keys(imfForecast.forecasts).sort();
        
        html = `
            <p style="margin-bottom: 1rem;">Comparison of inflation projections from official sources.</p>
            <table class="forecast-table">
                <thead>
                    <tr>
                        <th>Source</th>
                        <th>Type</th>
                        ${imfYears.map(y => `<th>${y}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><a href="${cbForecast.source_url}" target="_blank">${cbForecast.source_full || cbForecast.source}</a></td>
                        <td>${cbForecast.forecast_type}</td>
        `;
        
        // Add CB forecast values aligned to IMF years. Scenario-based sources
        // (BoE, #10) carry a per-year cross-scenario range instead of a point.
        const cbRange = cbForecast.projection_range || null;
        for (const year of imfYears) {
            let cell = '—';
            if (cbRange && Array.isArray(cbRange[year])) {
                const [lo, hi] = cbRange[year];
                cell = lo === hi ? `${lo.toFixed(1)}%` : `${lo.toFixed(1)}–${hi.toFixed(1)}%`;
            } else {
                const value = cbForecast.projections?.[year];
                if (value !== null && value !== undefined) cell = `${value.toFixed(1)}%`;
            }
            html += `<td>${cell}</td>`;
        }
        
        html += `
                    </tr>
                    <tr>
                        <td><a href="${imfData.url || 'https://www.imf.org/external/datamapper/PCPIPCH@WEO'}" target="_blank">IMF</a></td>
                        <td>WEO ${imfData.version || ''}</td>
        `;
        
        for (const year of imfYears) {
            const value = imfForecast.forecasts[year];
            html += `<td>${value !== undefined ? value.toFixed(1) + '%' : '—'}</td>`;
        }
        
        html += `
                    </tr>
                </tbody>
            </table>
            <p style="margin-top: 0.75rem; font-size: 0.8125rem; color: #6b7280;">
                <strong>Central Bank:</strong> ${cbForecast.note}<br>
                <strong>IMF:</strong> World Economic Outlook${imfData.version ? ' (' + imfData.version + ')' : ''}${imfData.retrieved ? ', retrieved ' + imfData.retrieved : ''}
            </p>
        `;

        // Scenario-based sources (BoE, #10): show each scenario's CPI path so
        // the displayed range is auditable rather than a bare band.
        if (cbForecast.scenarios && typeof cbForecast.scenarios === 'object') {
            const scen = cbForecast.scenarios;
            const scenYears = Array.from(new Set(
                Object.values(scen).flatMap(p => Object.keys(p || {})))).sort();
            html += `
                <p style="margin-top: 1rem; margin-bottom: 0.5rem; font-weight: 600;">Scenario projections (CPI inflation, %)</p>
                <table class="forecast-table">
                    <thead><tr><th>Scenario</th>${scenYears.map(y => `<th>${y}</th>`).join('')}</tr></thead>
                    <tbody>
                        ${Object.keys(scen).sort().map(name => `
                            <tr>
                                <td>${name}</td>
                                ${scenYears.map(y => {
                                    const v = scen[name]?.[y];
                                    return `<td>${v !== undefined && v !== null ? v.toFixed(1) + '%' : '—'}</td>`;
                                }).join('')}
                            </tr>`).join('')}
                    </tbody>
                </table>
                <p style="margin-top: 0.5rem; font-size: 0.8125rem; color: #6b7280;">
                    The Bank of England publishes alternative scenarios rather than a single central projection;
                    the comparison table above shows the cross-scenario range.
                </p>
            `;
        }
    } else if (cbIsReal) {
        // Only central bank forecast available
        const years = Object.keys(cbForecast.projections).filter(y => y !== 'longer_run').sort();
        
        html = `
            <p style="margin-bottom: 1rem;">${cbForecast.forecast_type} from <a href="${cbForecast.source_url}" target="_blank">${cbForecast.source_full || cbForecast.source}</a></p>
            <table class="forecast-table">
                <thead>
                    <tr>
                        <th>Period</th>
                        <th>Forecast</th>
                    </tr>
                </thead>
                <tbody>
        `;

        for (const year of years) {
            const value = cbForecast.projections[year];
            if (value !== null) {
                html += `
                    <tr>
                        <td>${year}</td>
                        <td>${value.toFixed(1)}%</td>
                    </tr>
                `;
            }
        }

        // Add longer run if available
        if (cbForecast.projections.longer_run !== undefined) {
            html += `
                <tr>
                    <td>Longer Run</td>
                    <td>${cbForecast.projections.longer_run.toFixed(1)}%</td>
                </tr>
            `;
        }

        html += `
                </tbody>
            </table>
            <p style="margin-top: 0.75rem; font-size: 0.8125rem; color: #6b7280;">${cbForecast.note}</p>
        `;
    } else if (imfForecast && imfForecast.forecasts) {
        // Only IMF forecast available
        const years = Object.keys(imfForecast.forecasts).sort();
        
        html = `
            <p style="margin-bottom: 1rem;">IMF World Economic Outlook from <a href="${imfData.url || 'https://www.imf.org/external/datamapper/PCPIPCH@WEO'}" target="_blank">IMF DataMapper</a></p>
            <table class="forecast-table">
                <thead>
                    <tr>
                        <th>Year</th>
                        <th>Forecast</th>
                    </tr>
                </thead>
                <tbody>
        `;

        for (const year of years) {
            html += `
                <tr>
                    <td>${year}</td>
                    <td>${imfForecast.forecasts[year].toFixed(1)}%</td>
                </tr>
            `;
        }

        // When the central bank publishes no forecast, explain why only the IMF
        // projection is shown (the placeholder row's note), rather than silently
        // dropping the context (#67).
        const placeholderNote = cbIsImfPlaceholder && cbForecast.note ? cbForecast.note + ' ' : '';
        html += `
                </tbody>
            </table>
            <p style="margin-top: 0.75rem; font-size: 0.8125rem; color: #6b7280;">
                ${placeholderNote}${imfData.indicator_label || 'Inflation rate, average consumer prices'}. Retrieved ${imfData.retrieved || 'recently'}.
            </p>
        `;
    }

    container.innerHTML = html;
}

// ============================================================
// TARGET INFO AND DATA SOURCES
// ============================================================

function renderTargetInfo(countryCode, targetDef) {
    const container = document.getElementById('targetInfo');
    if (!container) return;

    const info = TARGET_INFO[countryCode];
    if (!info) return;

    let html = `<p>${info.description}</p>`;

    // Add target change alert box if there's a recent policy change
    // (recent_change lives in targets.json — the single source of truth
    // for target facts; TARGET_INFO carries only editorial copy)
    const change = targetDef?.recent_change;
    if (change) {
        html += `
            <div class="policy-change-alert">
                <div class="policy-change-header">
                    <span class="policy-change-icon">📋</span>
                    <strong>Recent Policy Change</strong>
                    <span class="policy-change-date">${change.date}</span>
                </div>
                <div class="policy-change-details">
                    <div class="policy-change-row">
                        <span class="policy-label">Previous target:</span>
                        <span class="policy-value previous">${change.previous}</span>
                    </div>
                    <div class="policy-change-row">
                        <span class="policy-label">New target:</span>
                        <span class="policy-value current">${change.current}</span>
                    </div>
                    ${change.note ? `<p class="policy-change-note">${change.note}</p>` : ''}
                </div>
            </div>
        `;
    }
    
    html += `
        <blockquote class="target-quote">
            "${info.quote}"
            <div class="target-quote-source">— ${info.quoteSource}</div>
        </blockquote>
    `;
    
    container.innerHTML = html;
}

function renderDataSources(countryCode) {
    const container = document.getElementById('dataSources');
    if (!container) return;

    const sources = DATA_SOURCES[countryCode];
    if (!sources) return;

    let html = '<h3>Data Sources</h3>';
    for (const source of sources) {
        html += `
            <div class="source-item">
                <span class="source-label">${source.label}:</span>
                <span class="source-value"><a href="${source.url}" target="_blank">${source.value}</a></span>
            </div>
        `;
    }

    container.innerHTML = html;
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function formatDate(dateStr) {
    if (!dateStr) return '—';
    
    // Handle quarterly format (e.g., "2025-Q3")
    if (dateStr.includes('Q')) {
        return dateStr;
    }
    
    const [year, month] = dateStr.split('-');
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return months[parseInt(month) - 1] + ' ' + year;
}

function getValueClass(value, target) {
    if (target === null || target === undefined) return "neutral";
    const diff = value - target;
    if (diff > 2) return 'high';
    if (diff > 0.5) return 'elevated';
    if (diff < -0.5) return 'low';
    return 'on-target';
}

function showError(message) {
    const main = document.querySelector('main');
    if (main) {
        main.innerHTML = `<div class="container"><div class="section error">${message}</div></div>`;
    }
}

// Log version for debugging
console.log('country.js loaded - Version 2026-03-24 (added supplementary metrics)');
