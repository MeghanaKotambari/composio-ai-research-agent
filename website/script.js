// AI Product Research Agent - Dashboard Script

// Data paths
const DATA_PATHS = {
    statistics: '../output/reports/statistics.json',
    insights: '../output/reports/insights.json',
    clusters: '../output/reports/clusters.json',
    results: '../output/raw/results.json',
};

// State
let allResults = [];
let allStats = null;
let allInsights = [];

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
        allInsights = insights;
        allResults = results;
        
        // Hide loading
        document.getElementById('loading').style.display = 'none';
        
        // Check if we have data
        if (!stats && results.length === 0) {
            document.getElementById('error-state').style.display = 'flex';
            return;
        }
        
        // Populate sections
        populateHero(stats, results);
        populateInsights(insights);
        populateMetrics(stats);
        populateCharts(stats);
        populateOpportunities(results);
        populateWorkflow();
        populateVerification(stats);
        populateTable(results);
        populateArchitecture();
        
        // Setup fade-in animations
        setupAnimations();
        
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('loading').innerHTML = '<p>Error loading data. Run research first.</p>';
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
    const totalApps = results?.length || 0;
    const avgConfidence = results?.reduce((sum, app) => sum + (app.confidence_score || 0), 0) / totalApps || 0;
    
    animateValue('total-apps', 0, totalApps, 1000);
    document.getElementById('avg-confidence').textContent = `${Math.round(avgConfidence * 100)}%`;
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
    
    if (!insights || insights.length === 0) {
        container.innerHTML = '<div class="empty-state">No insights available. Run research to generate insights.</div>';
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
    
    if (!stats) {
        container.innerHTML = '<div class="empty-state">No metrics available. Run research to generate metrics.</div>';
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
    
    // Auth Chart
    const authCtx = document.getElementById('authChart');
    if (authCtx && stats?.authentication?.auth_method_distribution) {
        new Chart(authCtx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(stats.authentication.auth_method_distribution),
                datasets: [{
                    data: Object.values(stats.authentication.auth_method_distribution),
                    backgroundColor: ['#00d4ff', '#00ff88', '#ff006e', '#6b00ff', '#ff6b00'],
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#a0a0a0' } }
                }
            }
        });
    }
    
    // Category Chart
    const catCtx = document.getElementById('categoryChart');
    if (catCtx && stats?.categories?.category_distribution) {
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
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { ticks: { color: '#a0a0a0' } } }
            }
        });
    }
    
    // API Chart
    const apiCtx = document.getElementById('apiChart');
    if (apiCtx && stats?.api?.api_type_distribution) {
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
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#a0a0a0' } }
                }
            }
        });
    }
    
    // Access Chart
    const accessCtx = document.getElementById('accessChart');
    if (accessCtx && stats?.accessibility) {
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
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#a0a0a0' } }
                }
            }
        });
    }
    
    // Buildability Chart
    const buildCtx = document.getElementById('buildabilityChart');
    if (buildCtx && stats?.buildability) {
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
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { ticks: { color: '#a0a0a0' } } }
            }
        });
    }
    
    // Blockers Chart
    const blockCtx = document.getElementById('blockersChart');
    if (blockCtx && stats?.blockers?.blocker_distribution) {
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
                responsive: true,
                indexAxis: 'y',
                plugins: { legend: { display: false } },
                scales: { x: { ticks: { color: '#a0a0a0' } } }
            }
        });
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
    
    document.getElementById('easy-wins').innerHTML = easyWins.length > 0
        ? easyWins.map(app => `<div class="opportunity-item">${escapeHtml(app.name)}</div>`).join('')
        : '<div class="empty-state">No easy wins found</div>';
    
    document.getElementById('medium-effort').innerHTML = mediumEffort.length > 0
        ? mediumEffort.map(app => `<div class="opportunity-item">${escapeHtml(app.name)}</div>`).join('')
        : '<div class="empty-state">No medium effort apps found</div>';
    
    document.getElementById('high-effort').innerHTML = highEffort.length > 0
        ? highEffort.map(app => `<div class="opportunity-item">${escapeHtml(app.name)}</div>`).join('')
        : '<div class="empty-state">No high effort apps found</div>';
}

// Populate Workflow
function populateWorkflow() {
    const steps = [
        { name: '100 Apps', icon: '📱' },
        { name: 'Documentation Discovery', icon: '🔍' },
        { name: 'Web Research', icon: '🌐' },
        { name: 'Prompt Builder', icon: '✍️' },
        { name: 'LLM Extraction', icon: '🤖' },
        { name: 'Response Parser', icon: '📄' },
        { name: 'Verification Engine', icon: '✅' },
        { name: 'Pattern Detection', icon: '📊' },
        { name: 'Interactive Dashboard', icon: '📈' },
    ];
    
    const container = document.getElementById('workflow-container');
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
    
    if (!stats) {
        container.innerHTML = '<div class="empty-state">No verification data available</div>';
        return;
    }
    
    const metrics = [
        { label: 'Verified', value: stats?.verification_rate || 0 },
        { label: 'Manual Review', value: stats?.manual_review || 0 },
        { label: 'Failed Fields', value: stats?.failed_fields || 0 },
        { label: 'Warnings', value: stats?.warnings || 0 },
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
    
    if (!results || results.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No data available. Run research first.</td></tr>';
        return;
    }
    
    tbody.innerHTML = results.map(app => `
        <tr>
            <td>${escapeHtml(app.name || 'Unknown')}</td>
            <td>${escapeHtml(app.category || 'other')}</td>
            <td>${(app.auth_methods || []).map(a => escapeHtml(a)).join(', ')}</td>
            <td>${app.self_serve ? 'Yes' : 'No'}</td>
            <td>${escapeHtml(app.buildability || 'Unknown')}</td>
            <td>${Math.round((app.confidence_score || 0) * 100)}%</td>
            <td>${app.evidence_url ? `<a href="${escapeHtml(app.evidence_url)}" target="_blank">Link</a>` : '—'}</td>
        </tr>
    `).join('');
}

// Populate Architecture
function populateArchitecture() {
    const nodes = [
        'ResearchAgent',
        'Workflow',
        'WebResearch',
        'Prompt Builder',
        'LLM Provider',
        'Response Parser',
        'Verification Engine',
        'Analytics Engine',
        'Dashboard',
    ];
    
    const container = document.getElementById('architecture-container');
    container.innerHTML = nodes.map((node, i) => `
        <div class="arch-node fade-in">${node}</div>
        ${i < nodes.length - 1 ? '<div class="workflow-arrow">↓</div>' : ''}
    `).join('');
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
        const name = row.cells[0].textContent.toLowerCase();
        const cat = row.cells[1].textContent;
        const authMethods = row.cells[2].textContent;
        
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
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}