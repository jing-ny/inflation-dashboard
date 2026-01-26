/**
 * Inflation Dashboard - Country Page Module
 * 
 * Shared JavaScript for all country detail pages.
 * Loads data from data/historical_cpi.json and renders charts/tables.
 */

// Central bank forecast data (hardcoded - no reliable API for most)
const FORECASTS = {
    US: {
        source: 'Federal Reserve',
        sourceUrl: 'https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20241218.htm',
        type: 'FOMC PCE Projections',
        data: [
            { period: '2025', value: 2.5 },
            { period: '2026', value: 2.1 },
            { period: '2027', value: 2.0 },
            { period: 'Longer Run', value: 2.0 }
        ],
        note: 'PCE inflation (Fed\'s preferred measure), median projections'
    },
    CA: {
        source: 'Bank of Canada',
        sourceUrl: 'https://www.bankofcanada.ca/publications/mpr/',
        type: 'MPR Projections',
        data: [
            { period: '2025', value: 2.0 },
            { period: '2026', value: 2.0 }
        ],
        note: 'CPI inflation, from Monetary Policy Report'
    },
    UK: {
        source: 'Bank of England',
        sourceUrl: 'https://www.bankofengland.co.uk/monetary-policy-report/2024/november-2024',
        type: 'MPC Projections',
        data: [
            { period: 'Q4 2025', value: 2.7 },
            { period: 'Q4 2026', value: 2.2 },
            { period: 'Q4 2027', value: 1.8 }
        ],
        note: 'CPI inflation, modal projections from November 2024 MPR'
    },
    CH: {
        source: 'Swiss National Bank',
        sourceUrl: 'https://www.snb.ch/en/the-snb/mandates-goals/monetary-policy/decisions',
        type: 'Conditional Forecast',
        data: [
            { period: '2025', value: 0.3 },
            { period: '2026', value: 0.8 },
            { period: '2027', value: 0.8 }
        ],
        note: 'CPI inflation, conditional on policy rate remaining unchanged'
    },
    EA: {
        source: 'European Central Bank',
        sourceUrl: 'https://www.ecb.europa.eu/press/projections/html/index.en.html',
        type: 'Staff Projections',
        data: [
            { period: '2025', value: 2.1 },
            { period: '2026', value: 1.9 },
            { period: '2027', value: 2.1 }
        ],
        note: 'HICP inflation, December 2024 projections'
    },
    DE: {
        source: 'European Central Bank',
        sourceUrl: 'https://www.ecb.europa.eu/press/projections/html/index.en.html',
        type: 'Euro Area Projections',
        data: [
            { period: '2025', value: 2.1 },
            { period: '2026', value: 1.9 },
            { period: '2027', value: 2.1 }
        ],
        note: 'Germany follows ECB monetary policy as Euro Area member'
    },
    AU: {
        source: 'Reserve Bank of Australia',
        sourceUrl: 'https://www.rba.gov.au/publications/smp/',
        type: 'SMP Forecasts',
        data: [
            { period: 'Jun 2025', value: 2.8 },
            { period: 'Dec 2025', value: 2.6 },
            { period: 'Jun 2026', value: 2.7 }
        ],
        note: 'Trimmed mean inflation, November 2024 SMP'
    },
    NZ: {
        source: 'Reserve Bank of New Zealand',
        sourceUrl: 'https://www.rbnz.govt.nz/monetary-policy/monetary-policy-statement',
        type: 'MPS Projections',
        data: [
            { period: 'Mar 2025', value: 2.1 },
            { period: 'Mar 2026', value: 2.0 },
            { period: 'Mar 2027', value: 2.0 }
        ],
        note: 'CPI inflation, November 2024 MPS'
    },
    ZA: {
        source: 'South African Reserve Bank',
        sourceUrl: 'https://www.resbank.co.za/en/home/publications/publication-detail-pages/statements/monetary-policy-statements/2024',
        type: 'MPC Projections',
        data: [
            { period: '2025', value: 4.0 },
            { period: '2026', value: 4.5 }
        ],
        note: 'CPI inflation, November 2024 MPC statement'
    },
    CN: {
        source: 'IMF World Economic Outlook',
        sourceUrl: 'https://www.imf.org/en/Publications/WEO',
        type: 'IMF Projections',
        data: [
            { period: '2025', value: 1.0 },
            { period: '2026', value: 1.5 },
            { period: '2027', value: 1.8 }
        ],
        note: 'China does not publish official multi-year inflation forecasts'
    },
    JP: {
        source: 'Bank of Japan',
        sourceUrl: 'https://www.boj.or.jp/en/mopo/outlook/',
        type: 'Outlook Report',
        data: [
            { period: 'FY2025', value: 1.9 },
            { period: 'FY2026', value: 1.9 }
        ],
        note: 'CPI ex fresh food, median of Policy Board forecasts'
    }
};

// Target descriptions
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
    CH: {
        target: 1.0,
        targetRange: '0-2%',
        description: 'The Swiss National Bank defines price stability as a rise in the Swiss consumer price index (CPI) of less than 2% per annum. Deflation also breaches the objective of price stability.',
        quote: 'The SNB equates price stability with a rise in the Swiss consumer price index (CPI) of less than 2% per annum. Deflation, i.e. a sustained decrease in the price level, also breaches the objective of price stability.',
        quoteSource: 'SNB Monetary Policy Strategy'
    },
    EA: {
        target: 2.0,
        description: 'The ECB aims for 2% inflation over the medium term, measured by the Harmonised Index of Consumer Prices (HICP).',
        quote: 'The Governing Council considers that price stability is best maintained by aiming for a 2% inflation target over the medium term. This target is symmetric.',
        quoteSource: 'ECB Monetary Policy Strategy, July 2021'
    },
    DE: {
        target: 2.0,
        description: 'As a Euro Area member, Germany follows ECB monetary policy with a 2% inflation target.',
        quote: 'The Governing Council considers that price stability is best maintained by aiming for a 2% inflation target over the medium term.',
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
        target: 4.5,
        targetRange: '3-6%',
        description: 'The SARB targets 3-6% CPI inflation, with a recent preference for anchoring expectations around 4.5%.',
        quote: 'The inflation target range is 3–6%. The SARB has signalled a preference for inflation expectations to be anchored around the 4.5% midpoint of the target range.',
        quoteSource: 'SARB Monetary Policy Review, 2024'
    },
    CN: {
        target: 3.0,
        description: 'China sets an annual CPI target, typically around 3%, as part of its government work report. The target is more of a ceiling than a strict objective.',
        quote: 'We will keep the consumer price index increase at around 3 percent.',
        quoteSource: 'Government Work Report, March 2024'
    },
    JP: {
        target: 2.0,
        description: 'The Bank of Japan targets 2% CPI inflation, a goal it struggled to achieve for decades until recent global inflation pressures.',
        quote: 'The Bank of Japan conducts monetary policy based on the principle that the policy shall be aimed at achieving price stability, thereby contributing to the sound development of the national economy.',
        quoteSource: 'Bank of Japan Monetary Policy Framework'
    }
};

// Data source information
const DATA_SOURCES = {
    US: [
        { label: 'CPI Data', value: 'Bureau of Labor Statistics', url: 'https://www.bls.gov/cpi/' },
        { label: 'Series ID', value: 'CUSR0000SA0 (All Urban Consumers, All Items)', url: 'https://data.bls.gov/timeseries/CUSR0000SA0' },
        { label: 'Forecasts', value: 'FOMC Summary of Economic Projections', url: 'https://www.federalreserve.gov/monetarypolicy/fomcprojtable20241218.htm' },
        { label: 'Target', value: 'FOMC Statement on Longer-Run Goals', url: 'https://www.federalreserve.gov/monetarypolicy/files/FOMC_LongerRunGoals.pdf' }
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
    CH: [
        { label: 'CPI Data', value: 'Federal Statistical Office via FRED', url: 'https://fred.stlouisfed.org/series/CHECPIALLMINMEI' },
        { label: 'Series ID', value: 'CHECPIALLMINMEI (OECD)', url: 'https://fred.stlouisfed.org/series/CHECPIALLMINMEI' },
        { label: 'Forecasts', value: 'SNB Conditional Inflation Forecast', url: 'https://www.snb.ch/en/the-snb/mandates-goals/monetary-policy/decisions' },
        { label: 'Target', value: 'SNB Monetary Policy Strategy', url: 'https://www.snb.ch/en/the-snb/mandates-goals/monetary-policy/strategy' }
    ],
    EA: [
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
    DE: [
        { label: 'CPI Data', value: 'Destatis via FRED', url: 'https://fred.stlouisfed.org/series/DEUCPIALLMINMEI' },
        { label: 'Series ID', value: 'DEUCPIALLMINMEI (OECD)', url: 'https://fred.stlouisfed.org/series/DEUCPIALLMINMEI' },
        { label: 'Forecasts', value: 'ECB Staff Projections (Euro Area)', url: 'https://www.ecb.europa.eu/press/projections/html/index.en.html' },
        { label: 'Target', value: 'ECB Monetary Policy (Euro Area)', url: 'https://www.ecb.europa.eu/mopo/strategy/html/index.en.html' }
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
        { label: 'Target', value: 'SARB Inflation Targeting Framework', url: 'https://www.resbank.co.za/en/home/what-we-do/monetary-policy' }
    ],
    CN: [
        { label: 'CPI Data', value: 'NBS China via FRED', url: 'https://fred.stlouisfed.org/series/CHNCPIALLMINMEI' },
        { label: 'Series ID', value: 'CHNCPIALLMINMEI (OECD)', url: 'https://fred.stlouisfed.org/series/CHNCPIALLMINMEI' },
        { label: 'Forecasts', value: 'IMF World Economic Outlook', url: 'https://www.imf.org/en/Publications/WEO' },
        { label: 'Target', value: 'Government Work Report', url: 'http://english.www.gov.cn/' }
    ],
    JP: [
        { label: 'CPI Data', value: 'Statistics Bureau of Japan via FRED', url: 'https://fred.stlouisfed.org/series/JPNCPIALLMINMEI' },
        { label: 'Series ID', value: 'JPNCPIALLMINMEI (OECD)', url: 'https://fred.stlouisfed.org/series/JPNCPIALLMINMEI' },
        { label: 'Forecasts', value: 'Bank of Japan Outlook Report', url: 'https://www.boj.or.jp/en/mopo/outlook/' },
        { label: 'Target', value: 'BoJ Price Stability Target', url: 'https://www.boj.or.jp/en/mopo/outline/qqe.htm' }
    ]
};

/**
 * Initialize a country page
 * @param {string} countryCode - Two-letter country code (US, UK, etc.)
 */
async function initCountryPage(countryCode) {
    try {
        const response = await fetch('data/historical_cpi.json');
        const allData = await response.json();
        const countryData = allData[countryCode];

        if (!countryData) {
            showError('Country data not found');
            return;
        }

        // Update metrics cards
        updateMetrics(countryCode, countryData);

        // Render historical chart
        renderHistoricalChart(countryCode, countryData);

        // Render forecast table (async - loads IMF data)
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
    if (targetEl) {
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
                            if (label.endsWith('-01')) {
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

async function renderForecastTable(countryCode) {
    const container = document.getElementById('forecastTable');
    if (!container) return;

    const cbForecast = FORECASTS[countryCode];
    
    // Try to load IMF forecasts
    let imfData = null;
    try {
        const response = await fetch('data/imf_forecasts.json');
        if (response.ok) {
            imfData = await response.json();
        }
    } catch (e) {
        console.log('IMF forecasts not available');
    }
    
    const imfForecast = imfData?.countries?.[countryCode];
    
    if (!cbForecast && !imfForecast) {
        container.innerHTML = '<p>No forecast data available for this country.</p>';
        return;
    }

    let html = '';
    
    // If we have both, show comparison table
    if (cbForecast && imfForecast) {
        // Get all years from both sources
        const cbYears = cbForecast.data.map(d => d.period);
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
                        <td><a href="${cbForecast.sourceUrl}" target="_blank">${cbForecast.source}</a></td>
                        <td>${cbForecast.type}</td>
        `;
        
        // Add CB forecast values aligned to IMF years where possible
        for (const year of imfYears) {
            const cbMatch = cbForecast.data.find(d => d.period === year || d.period.includes(year));
            html += `<td>${cbMatch ? cbMatch.value.toFixed(1) + '%' : '—'}</td>`;
        }
        
        html += `
                    </tr>
                    <tr>
                        <td><a href="${imfData.url}" target="_blank">IMF</a></td>
                        <td>WEO ${imfData.version}</td>
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
                <strong>IMF:</strong> World Economic Outlook (${imfData.version}), retrieved ${imfData.retrieved}
            </p>
        `;
    } else if (cbForecast) {
        // Only central bank forecast available
        html = `
            <p style="margin-bottom: 1rem;">${cbForecast.type} from <a href="${cbForecast.sourceUrl}" target="_blank">${cbForecast.source}</a></p>
            <table class="forecast-table">
                <thead>
                    <tr>
                        <th>Period</th>
                        <th>Forecast</th>
                    </tr>
                </thead>
                <tbody>
        `;

        for (const row of cbForecast.data) {
            html += `
                <tr>
                    <td>${row.period}</td>
                    <td>${row.value.toFixed(1)}%</td>
                </tr>
            `;
        }

        html += `
                </tbody>
            </table>
            <p style="margin-top: 0.75rem; font-size: 0.8125rem; color: #6b7280;">${cbForecast.note}</p>
        `;
    } else if (imfForecast) {
        // Only IMF forecast available
        const years = Object.keys(imfForecast.forecasts).sort();
        
        html = `
            <p style="margin-bottom: 1rem;">IMF World Economic Outlook (${imfData.version}) from <a href="${imfData.url}" target="_blank">IMF DataMapper</a></p>
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
                ${imfData.indicator_label}. Retrieved ${imfData.retrieved}.
            </p>
        `;
    }

    container.innerHTML = html;
}

function renderTargetInfo(countryCode) {
    const container = document.getElementById('targetInfo');
    if (!container) return;

    const info = TARGET_INFO[countryCode];
    if (!info) return;

    container.innerHTML = `
        <p>${info.description}</p>
        <blockquote class="target-quote">
            "${info.quote}"
            <div class="target-quote-source">— ${info.quoteSource}</div>
        </blockquote>
    `;
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

// Utility functions
function formatDate(dateStr) {
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
