// AI Product Research Agent - Dashboard Script

// Data paths (relative to website/)
const DATA_PATHS = {
    statistics: 'data/statistics.json',
    insights: 'data/insights.json',
    clusters: 'data/clusters.json',
    results: 'data/results.json',
    manual_review: 'data/manual_review.json',
};

// State
let allResults = [];
let allStats = null;
let allInsights = [];
let allClusters = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadAllData();
    setupEventListeners();
});

// Load all data
async function loadAllData() {
    try {
        const [stats, insights, clusters, results] = await Promise.all([
            fetchJSON(DATA_PATHS.statistics).catch(() => null),
            fetchJSON(DATA_PATHS.insights).catch(() => []),
            fetchJSON(DATA_PATHS.clusters).catch(() => null),
            fetchJSON(DATA_PATHS.results).catch(() => []),
        ]);
        
        allStats = stats;
        allInsights = Array.isArray(insights) ? insights : [];
        allClusters = clusters;
        allResults = Array.isArray(results) ? results : [];
        
        // Hide loading
        const loadingEl = document.getElementById('loading');
        if (loadingEl) loadingEl.style.display = 'none';
        
        // Check if we have data
        if (allResults.length === 0) {
            const errorEl = document.getElementById('error-state');
            if (errorEl) errorEl.style.display = 'flex';
            return;
        }
        
        // Populate sections
        populateHero(allStats, allResults);
        populateInsights(allInsights);
        populateMetrics(allStats);
        populateCharts(allStats);
        populateOpportunities(allResults);
        populateWorkflow();
        populateVerification(allStats);
        populateTable(allResults);
        populateArchitecture();
        populateCategoryFilter();
        populateAuthFilter();
        
        // Setup fade-in animations
        setupAnimations();
        
    } catch (error) {
        console.error('Error loading data:', error);
        const loadingEl = document.getElementById('loading');
        if (loadingEl) loadingEl.innerHTML = '<p>Error loading data. Run research first.</p>';
    }
}

// Fetch JSON with error handling
async function fetchJSON(path) {
    const response = await fetch(path);
    if (!response.ok) {
        throw new Error(`Failed to load ${path}`);
    }
    return response.json();
}

// Populate Hero Section
function populateHero(stats, results) {
    const totalApps = results.length;
    const avgConfidence = results.reduce((sum, app) => sum + (app.confidence_score || 0), 0) / totalApps || 0;
    const verifiedCount = results.filter(app => app.verification_status === 'verified').length;
    const verificationRate = totalApps > 0 ? Math.round(verifiedCount / totalApps * 100) : 0;
    
    animateValue('total-apps', 0, totalApps, 1000);
    document.getElementById('avg-confidence').textContent = `${Math.round(avgConfidence * 100)}%`;
    document.getElementById('verification-rate').textContent = `${verificationRate}%`;
    document.getElementById('research-time').textContent = `${totalApps} apps`;
}

// Animate counter
function animateValue(id, start, end, duration) {
    const obj = document.getElementById(id);
    if (!obj) return;
    
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.textContent = Math.floor(progress * (end - start) + start);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Populate Insights
function populateInsights(insights) {
    const container = document.getElementById('insights-container');
    if (!container) return;
    
    if (!insights || insights.length === 0) {
        container.innerHTML = '<div class="empty-state">No insights available.</div>';
        return;
    }
    
    container.innerHTML = insights.map(insight => `
        <div class="insight-card fade-in">
            <h3>${escapeHtml(insight.insight)}</h3>
            <p>${escapeHtml(insight.evidence)}</p>
        </div>
    `).join('');
}

// Populate Metrics
function populateMetrics(stats) {
    const container = document.getElementById('metrics-container');
    if (!container || !stats) {
        if (container) container.innerHTML = '<div class="empty-state">No metrics available.</div>';
        return;
    }
    
    const metrics = [
        { label: 'OAuth', value: stats?.authentication?.auth_method_distribution?.oauth2 || 0 },
        { label: 'API Keys', value: stats?.authentication?.auth_method_distribution?.api_key || 0 },
        { label: 'Self Serve', value: stats?.accessibility?.self_serve || 0 },
        { label: 'Enterprise', value: stats?.accessibility?.enterprise_only || 0 },
        { label: 'REST', value: stats?.api?.api_type_distribution?.rest || 0 },
        { label: 'GraphQL', value: stats?.api?.api_type_distribution?.graphql || 0 },
        { label: 'MCP', value: stats?.mcp?.available || 0 },
        { label: 'Easy', value: stats?.buildability?.easy || 0 },
    ];
    
    container.innerHTML = metrics.map(m => `
        <div class="metric-card fade-in">
            <div class="value">${m.value}</div>
            <div class="label">${m.label}</div>
        </div>
    `).join('');
}

// Populate Charts
function populateCharts(stats) {
    if (!stats) return;
    
    const chartConfig = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: { 
                position: 'bottom', 
                labels: { 
                    color: '#a0a0a0',
                    boxWidth: 12,
                    padding: 8,
                } 
            }
        },
        animation: {
            duration: 800,
            easing: 'easeInOutQuart',
        }
    };
    
    // Auth Chart
    const authCtx = document.getElementById('authChart');
    if (authCtx && stats?.authentication?.auth_method_distribution) {
        destroyChart(authCtx);
        new Chart(authCtx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(stats.authentication.auth_method_distribution),
                datasets: [{
                    data: Object.values(stats.authentication.auth_method_distribution),
                    backgroundColor: ['#00d4ff', '#00ff88', '#ff006e', '#6b00ff', '#ff6b00', '#ffdd00'],
                    borderWidth: 0,
                }]
            },
            options: chartConfig
        });
    }
    
    // Category Chart
    const catCtx = document.getElementById('categoryChart');
    if (catCtx && stats?.categories?.category_distribution) {
        destroyChart(catCtx);
        new Chart(catCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(stats.categories.category_distribution),
                datasets: [{
                    data: Object.values(stats.categories.category_distribution),
                    backgroundColor: '#00d4ff',
                    borderRadius: 4,
                }]
            },
            options: {
                ...chartConfig,
                plugins: { legend: { display: false } },
                scales: { 
                    y: { 
                        ticks: { color: '#a0a0a0' },
                        grid: { color: 'rgba(255,255,255,0.05)' }
                    },
                    x: {
                        ticks: { color: '#a0a0a0' }
                    }
                }
            }
        });
    }
    
    // API Chart
    const apiCtx = document.getElementById('apiChart');
    if (apiCtx && stats?.api?.api_type_distribution) {
        destroyChart(apiCtx);
        new Chart(apiCtx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(stats.api.api_type_distribution),
                datasets: [{
                    data: Object.values(stats.api.api_type_distribution),
                    backgroundColor: ['#00d4ff', '#00ff88', '#ff006e', '#6b00ff', '#ff6b00'],
                    borderWidth: 0,
                }]
            },
            options: chartConfig
        });
    }
    
    // Access Chart
    const accessCtx = document.getElementById('accessChart');
    if (accessCtx && stats?.accessibility) {
        destroyChart(accessCtx);
        new Chart(accessCtx, {
            type: 'pie',
            data: {
                labels: ['Self-Serve', 'Enterprise', 'Unknown'],
                datasets: [{
                    data: [stats.accessibility.self_serve, stats.accessibility.enterprise_only, stats.accessibility.unknown],
                    backgroundColor: ['#00ff88', '#ff006e', '#666'],
                    borderWidth: 0,
                }]
            },
            options: chartConfig
        });
    }
    
    // Buildability Chart
    const buildCtx = document.getElementById('buildabilityChart');
    if (buildCtx && stats?.buildability) {
        destroyChart(buildCtx);
        new Chart(buildCtx, {
            type: 'bar',
            data: {
                labels: ['Easy', 'Medium', 'Hard', 'Blocked'],
                datasets: [{
                    data: [stats.buildability.easy, stats.buildability.medium, stats.buildability.hard, stats.buildability.blocked],
                    backgroundColor: ['#00ff88', '#ff6b00', '#ff006e', '#666'],
                    borderRadius: 4,
                }]
            },
            options: {
                ...chartConfig,
                plugins: { legend: { display: false } },
                scales: { 
                    y: { 
                        ticks: { color: '#a0a0a0' },
                        grid: { color: 'rgba(255,255,255,0.05)' }
                    }
                }
            }
        });
    }
    
    // Blockers Chart
    const blockCtx = document.getElementById('blockersChart');
    if (blockCtx && stats?.blockers?.blocker_distribution) {
        destroyChart(blockCtx);
        new Chart(blockCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(stats.blockers.blocker_distribution),
                datasets: [{
                    data: Object.values(stats.blockers.blocker_distribution),
                    backgroundColor: '#ff006e',
                    borderRadius: 4,
                }]
            },
            options: {
                ...chartConfig,
                indexAxis: 'y',
                plugins: { legend: { display: false } },
                scales: { 
                    x: { 
                        ticks: { color: '#a0a0a0' },
                        grid: { color: 'rgba(255,255,255,0.05)' }
                    },
                    y: {
                        ticks: { color: '#a0a0a0' }
                    }
                }
            }
        });
    }
}

// Destroy existing chart instance on a canvas
function destroyChart(canvas) {
    const charts = Chart.instances;
    for (const key in charts) {
        if (charts[key].canvas === canvas) {
            charts[key].destroy();
            break;
        }
    }
}

// Populate Opportunities
function populateOpportunities(results) {
    const easyWins = [];
    const mediumEffort = [];
    const highEffort = [];
    
    results.forEach(app => {
        if (app.self_serve && app.buildability === 'high' && !app.main_blocker) {
            easyWins.push(app);
        } else if (app.self_serve && (app.buildability === 'medium' || app.buildability === 'high')) {
            mediumEffort.push(app);
        } else if (!app.self_serve || app.main_blocker) {
            highEffort.push(app);
        }
    });
    
    const easyEl = document.getElementById('easy-wins');
    const mediumEl = document.getElementById('medium-effort');
    const highEl = document.getElementById('high-effort');
    
    if (easyEl) {
        easyEl.innerHTML = easyWins.length > 0
            ? easyWins.map(app => `<div class="opportunity-item">${escapeHtml(app.name)}</div>`).join('')
            : '<div class="empty-state">No easy wins found</div>';
    }
    
    if (mediumEl) {
        mediumEl.innerHTML = mediumEffort.length > 0
            ? mediumEffort.map(app => `<div class="opportunity-item">${escapeHtml(app.name)}</div>`).join('')
            : '<div class="empty-state">No medium effort apps found</div>';
    }
    
    if (highEl) {
        highEl.innerHTML = highEffort.length > 0
            ? highEffort.map(app => `<div class="opportunity-item">${escapeHtml(app.name)}</div>`).join('')
            : '<div class="empty-state">No high effort apps found</div>';
    }
}

// Populate Workflow
function populateWorkflow() {
    const steps = [
        { name: '100 Apps', icon: '📱' },
        { name: 'Doc Discovery', icon: '🔍' },
        { name: 'Web Research', icon: '🌐' },
        { name: 'Prompt Builder', icon: '✍️' },
        { name: 'LLM Extraction', icon: '🤖' },
        { name: 'Response Parser', icon: '📄' },
        { name: 'Verification', icon: '✅' },
        { name: 'Analytics', icon: '📊' },
        { name: 'Dashboard', icon: '📈' },
    ];
    
    const container = document.getElementById('workflow-container');
    if (!container) return;
    
    container.innerHTML = steps.map((step, i) => `
        <div class="workflow-step fade-in">
            <div class="workflow-icon">${step.icon}</div>
            <span>${step.name}</span>
            ${i < steps.length - 1 ? '<div class="workflow-arrow">↓</div>' : ''}
        </div>
    `).join('');
}

// Populate Verification
function populateVerification(stats) {
    const container = document.getElementById('verification-container');
    if (!container) return;
    
    if (!stats) {
        container.innerHTML = '<div class="empty-state">No verification data available</div>';
        return;
    }
    
    const metrics = [
        { label: 'Verified', value: stats?.verification?.verified || 0 },
        { label: 'Manual Review', value: stats?.verification?.manual_review || 0 },
        { label: 'Pending', value: stats?.verification?.pending || 0 },
        { label: 'Rate', value: stats?.verification?.verification_rate ? `${stats.verification.verification_rate}%` : '0%' },
    ];
    
    container.innerHTML = metrics.map(m => `
        <div class="verification-card fade-in">
            <div class="value">${m.value}</div>
            <div class="label">${m.label}</div>
        </div>
    `).join('');
}

// Populate Table
function populateTable(results) {
    const tbody = document.getElementById('table-body');
    if (!tbody) return;
    
    if (!results || results.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No data available. Run research first.</td></tr>';
        return;
    }
    
    tbody.innerHTML = results.map(app => `
        <tr>
            <td>${escapeHtml(app.name || 'Unknown')}</td>
            <td>${escapeHtml(app.category || 'other')}</td>
            <td>${(app.auth_methods || []).map(a => escapeHtml(a)).join(', ')}</td>
            <td>${app.self_serve ? 'Yes' : app.self_serve === false ? 'No' : 'Unknown'}</td>
            <td>${escapeHtml(app.buildability || 'Unknown')}</td>
            <td>${Math.round((app.confidence_score || 0) * 100)}%</td>
            <td>${app.evidence_url ? `<a href="${escapeHtml(app.evidence_url)}" target="_blank" rel="noopener">Link</a>` : '—'}</td>
        </tr>
    `).join('');
}

// Populate Architecture
function populateArchitecture() {
    const container = document.getElementById('architecture-container');
    if (!container) return;
    
    const nodes = [
        'ResearchAgent',
        'Workflow',
        'Doc Discovery',
        'Web Research',
        'Prompt Builder',
        'LLM Provider',
        'Response Parser',
        'Verification',
        'Analytics',
        'Dashboard',
    ];
    
    container.innerHTML = nodes.map((node, i) => `
        <div class="arch-node fade-in">${node}</div>
        ${i < nodes.length - 1 ? '<div class="workflow-arrow">↓</div>' : ''}
    `).join('');
}

// Populate Category Filter
function populateCategoryFilter() {
    const filter = document.getElementById('category-filter');
    if (!filter) return;
    
    const categories = [...new Set(allResults.map(app => app.category).filter(Boolean))];
    categories.sort();
    
    categories.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat;
        option.textContent = cat.charAt(0).toUpperCase() + cat.slice(1).replace(/_/g, ' ');
        filter.appendChild(option);
    });
}

// Populate Auth Filter
function populateAuthFilter() {
    const filter = document.getElementById('auth-filter');
    if (!filter) return;
    
    const authMethods = new Set();
    allResults.forEach(app => {
        (app.auth_methods || []).forEach(m => authMethods.add(m));
    });
    
    [...authMethods].sort().forEach(method => {
        const option = document.createElement('option');
        option.value = method;
        option.textContent = method.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        filter.appendChild(option);
    });
}

// Setup Event Listeners
function setupEventListeners() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', filterTable);
    }
    
    document.getElementById('category-filter')?.addEventListener('change', filterTable);
    document.getElementById('auth-filter')?.addEventListener('change', filterTable);
}

// Filter Table
function filterTable() {
    const search = document.getElementById('search-input')?.value.toLowerCase() || '';
    const category = document.getElementById('category-filter')?.value || '';
    const auth = document.getElementById('auth-filter')?.value || '';
    
    const rows = document.querySelectorAll('#table-body tr');
    rows.forEach(row => {
        const cells = row.cells;
        if (!cells || cells.length < 3) return;
        
        const name = cells[0]?.textContent?.toLowerCase() || '';
        const cat = cells[1]?.textContent || '';
        const authMethods = cells[2]?.textContent || '';
        
        const matchesSearch = name.includes(search);
        const matchesCategory = !category || cat === category;
        const matchesAuth = !auth || authMethods.includes(auth);
        
        row.style.display = matchesSearch && matchesCategory && matchesAuth ? '' : 'none';
    });
}

// Setup Animations
function setupAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.fade-in').forEach(el => {
        observer.observe(el);
    });
}

// Escape HTML
function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}