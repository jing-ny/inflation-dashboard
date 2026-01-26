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
        target: 2.0,
        description: 'The Federal Reserve targets 2% inflation as measured by the annual change in the price index for personal consumption expenditures (PCE).',
        quote: 'The Committee judges that inflation at the rate of 2 percent, as measured by the annual change in the price index for personal consumption expenditures, is most consistent over the longer run with the Federal Reserve\'s statutory mandate.',
        quoteSource: 'FOMC Statement on Longer-Run Goals, January 2024'
    },
    CA: {
        target: 2.0,
        targetRange: '1-3%',
        description: 'The Bank of Canada targets 2% CPI inflation, the midpoint of a 1-3% target range. The inflation-control target has been in place since 1991.',
        quote: 'The target aims to keep total CPI inflation at the 2 per cent midpoint of a target range of 1 to 3 per cent over the medium term.',
        quoteSource: 'Bank of Canada Inflation-Control Target'
    },
    UK: {
        target: 2.0,
        description: 'The Bank of England has a 2% CPI inflation target set by the government. If inflation deviates by more than 1 percentage point, the Governor must write a letter to the Chancellor explaining why.',
        quote: 'The inflation target of 2% is expressed in terms of an annual rate of inflation based on the Consumer Prices Index (CPI).',
        quoteSource: 'Bank of England Monetary Policy Framework'
    },
    EA: {
        target: 2.0,
        description: 'The ECB aims for 2% inflation over the medium term, measured by the Harmonised Index of Consumer Prices (HICP).',
        quote: 'The Governing Council considers that price stability is best maintained by aiming for a 2% inflation target over the medium term. This target is symmetric.',
        quoteSource: 'ECB Monetary Policy Strategy, July 2021'
    },
    AU: {
        target: 2.5,
        targetRange: '2-3%',
        description: 'The RBA targets inflation of 2-3% on average over time, focusing on underlying (trimmed mean) inflation.',
        quote: 'The Governor and the Treasurer have agreed that the appropriate target for monetary policy in Australia is to achieve an inflation rate of 2–3 per cent, on average, over time.',
        quoteSource: 'Statement on the Conduct of Monetary Policy, September 2024'
    },
    NZ: {
        target: 2.0,
        targetRange: '1-3%',
        description: 'The RBNZ targets 1-3% CPI inflation, with a focus on keeping inflation near the 2% midpoint.',
        quote: 'The Reserve Bank shall formulate and implement monetary policy with the goals of keeping future annual CPI inflation between 1 and 3 percent over the medium term, with a focus on keeping future inflation near the 2 percent mid-point.',
        quoteSource: 'Remit for the Monetary Policy Committee, 2024'
    },
    ZA: {
        target: 3.0,
        targetRange: '2-4%',
        description: 'The SARB targets 3% CPI inflation with a ±1 percentage point tolerance band (2-4%). This replaced the previous 3-6% target range in November 2025—the first change in 25 years. The new lower target aims to anchor inflation expectations and reduce borrowing costs over time.',
        quote: 'South Africa\'s inflation target is 3%, with a tolerance band of plus or minus 1 percentage point. This target refers to the headline change in the consumer price index.',
        quoteSource: 'SARB Monetary Policy Framework, November 2025',
        targetChange: {
            date: 'November 2025',
            previous: '3-6% (4.5% midpoint)',
            current: '3% ± 1pp',
            note: 'First target change in 25 years'
        }
    },
    JP: {
        target: 2.0,
        description: 'The Bank of Japan targets 2% CPI inflation, a goal adopted in January 2013 after decades of deflation. Japan achieved sustained inflation above target for the first time since the 1990s in 2022-2024.',
        quote: 'The Bank will achieve the price stability target of 2 percent in terms of the year-on-year rate of change in the consumer price index (CPI) at the earliest possible time.',
        quoteSource: 'Bank of Japan Price Stability Target'
    },
    IN: {
        target: 4.0,
        targetRange: '2-6%',
        description: 'The Reserve Bank of India targets 4% CPI inflation with a ±2 percentage point tolerance band (2-6%). The flexible inflation targeting framework was adopted in 2016. India experienced record-low inflation below 2% in late 2025 due to falling food prices.',
        quote: 'The primary objective of monetary policy is to maintain price stability while keeping in mind the objective of growth. The inflation target is set at 4 per cent with a tolerance band of +/- 2 per cent.',
        quoteSource: 'RBI Monetary Policy Framework'
    },
    CN: {
        target: 3.0,
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
        { label: 'CPI Data', value: 'Australian Bureau of Statistics via FRED', url: 'https://fred.stlouisfed.org/series/AUSCPIALLQINMEI' },
        { label: 'Series ID', value: 'AUSCPIALLQINMEI (OECD, Quarterly)', url: 'https://fred.stlouisfed.org/series/AUSCPIALLQINMEI' },
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
    IN: [
        { label: 'CPI Data', value: 'Ministry of Statistics and Programme Implementation', url: 'https://www.mospi.gov.in/' },
        { label: 'FRED Series', value: 'INDCPIALLMINMEI', url: 'https://fred.stlouisfed.org/series/INDCPIALLMINMEI' },
        { label: 'Forecasts', value: 'RBI Monetary Policy Statement', url: 'https://www.rbi.org.in/Scripts/PublicationsView.aspx' },
        { label: 'Target', value: 'RBI Monetary Policy Framework', url: 'https://www.rbi.org.in/' }
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
        // Load CPI data
        const cpiResponse = await fetch('data/historical_cpi.json');
        const allCpiData = await cpiResponse.json();
        const countryData = allCpiData[countryCode];

        if (!countryData) {
            showError('Country data not found');
            return;
        }

        // Update metrics cards
        updateMetrics(countryCode, countryData);

        // Render historical chart
        renderHistoricalChart(countryCode, countryData);

        // Render forecast table (loads from cb_forecasts.json and imf_forecasts.json)
        await renderForecastTable(countryCode);

        // Render target information
        renderTargetInfo(countryCode);

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

function updateMetrics(countryCode, data) {
    const current = data.latest;
    const previous = data.previous;
    const target = data.target;
    const targetInfo = TARGET_INFO[countryCode];

    // Current inflation
    const currentEl = document.getElementById('currentValue');
    if (currentEl && current) {
        currentEl.textContent = current.value.toFixed(1) + '%';
        currentEl.className = 'metric-value ' + getValueClass(current.value, target);
    }

    const currentDateEl = document.getElementById('currentDate');
    if (currentDateEl && current) {
        currentDateEl.textContent = formatDate(current.date);
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
    if (targetEl && targetInfo) {
        targetEl.textContent = targetInfo.targetRange || (target.toFixed(1) + '%');
    }

    // Status vs target
    const statusEl = document.getElementById('statusValue');
    const statusDetailEl = document.getElementById('statusDetail');
    if (statusEl && current) {
        const diff = current.value - target;
        statusEl.textContent = (diff >= 0 ? '+' : '') + diff.toFixed(1) + 'pp';
        statusEl.className = 'metric-value ' + getValueClass(current.value, target);
        
        if (statusDetailEl) {
            if (diff > 2) statusDetailEl.textContent = 'Well above target';
            else if (diff > 0.5) statusDetailEl.textContent = 'Above target';
            else if (diff < -0.5) statusDetailEl.textContent = 'Below target';
            else statusDetailEl.textContent = 'Near target';
        }
    }
}

// ============================================================
// HISTORICAL CHART
// ============================================================

function renderHistoricalChart(countryCode, data) {
    const canvas = document.getElementById('historyChart');
    if (!canvas || !data.history || data.history.length === 0) return;

    const target = data.target;
    const history = data.history;

    // Prepare chart data
    const labels = history.map(d => d.date);
    const values = history.map(d => d.value);

    // Target line
    const targetLine = history.map(() => target);

    new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'YoY Inflation',
                    data: values,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: 'Target',
                    data: targetLine,
                    borderColor: '#dc2626',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false
                }
            ]
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

    let html = '';

    // If we have both CB and IMF, show comparison table
    if (cbForecast && imfForecast && imfForecast.forecasts) {
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
        
        // Add CB forecast values aligned to IMF years
        for (const year of imfYears) {
            const value = cbForecast.projections?.[year];
            html += `<td>${value !== null && value !== undefined ? value.toFixed(1) + '%' : '—'}</td>`;
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
    } else if (cbForecast) {
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

        html += `
                </tbody>
            </table>
            <p style="margin-top: 0.75rem; font-size: 0.8125rem; color: #6b7280;">
                ${imfData.indicator_label || 'Inflation rate, average consumer prices'}. Retrieved ${imfData.retrieved || 'recently'}.
            </p>
        `;
    }

    container.innerHTML = html;
}

// ============================================================
// TARGET INFO AND DATA SOURCES
// ============================================================

function renderTargetInfo(countryCode) {
    const container = document.getElementById('targetInfo');
    if (!container) return;

    const info = TARGET_INFO[countryCode];
    if (!info) return;

    let html = `<p>${info.description}</p>`;
    
    // Add target change alert box if there's a recent policy change
    if (info.targetChange) {
        html += `
            <div class="policy-change-alert">
                <div class="policy-change-header">
                    <span class="policy-change-icon">📋</span>
                    <strong>Recent Policy Change</strong>
                    <span class="policy-change-date">${info.targetChange.date}</span>
                </div>
                <div class="policy-change-details">
                    <div class="policy-change-row">
                        <span class="policy-label">Previous target:</span>
                        <span class="policy-value previous">${info.targetChange.previous}</span>
                    </div>
                    <div class="policy-change-row">
                        <span class="policy-label">New target:</span>
                        <span class="policy-value current">${info.targetChange.current}</span>
                    </div>
                    ${info.targetChange.note ? `<p class="policy-change-note">${info.targetChange.note}</p>` : ''}
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
console.log('country.js loaded - Version 2026-01-26 (includes Japan)');
