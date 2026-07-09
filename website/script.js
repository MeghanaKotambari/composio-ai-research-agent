/**
 * Composio AI Research Agent - Dashboard JavaScript
 * 
 * This module handles:
 * - Data loading and management
 * - Chart rendering with Chart.js
 * - Table population and filtering
 * - Modal interactions
 * - Statistics calculation
 * 
 * NOTE: This is a skeleton implementation. Data loading and chart rendering
 * will be fully implemented when backend research logic is complete.
 */

// ============================================================================
// Global State
// ============================================================================

const AppState = {
    apps: [],
    filteredApps: [],
    charts: {},
    currentFilters: {
        search: '',
        category: '',
        buildability: ''
    }
};

// ============================================================================
// Data Management
// ============================================================================

/**
 * Load application data from JSON file.
 * 
 * @param {string} url - URL to JSON data file
 * @returns {Promise<Array>} Array of application objects
 */
async function loadData(url = 'data/apps.json') {
    try {
        showLoading();
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Handle both array and object with apps property
        AppState.apps = Array.isArray(data) ? data : (data.apps || []);
        AppState.filteredApps = [...AppState.apps];
        
        hideLoading();
        return AppState.apps;
        
    } catch (error) {
        console.error('Failed to load data:', error);
        showError('Failed to load application data. Please try again later.');
        return [];
    }
}

/**
 * Load sample/demo data for development.
 * 
 * @returns {Array} Sample application data
 */
function loadSampleData() {
    // TODO: Implement sample data for development and testing
    // This will be used when no real data is available
    return [];
}

// ============================================================================
// Statistics Calculation
// ============================================================================

/**
 * Calculate overview statistics.
 * 
 * @returns {Object} Statistics object
 */
function calculateStatistics() {
    const apps = AppState.apps;
    
    if (apps.length === 0) {
        return {
            totalApps: 0,
            verifiedApps: 0,
            avgConfidence: 0,
            mcpSupport: 0
        };
    }
    
    const totalApps = apps.length;
    const verifiedApps = apps.filter(app => app.verification_status === 'verified').length;
    
    const confidenceScores = apps
        .filter(app => app.confidence_score !== null && app.confidence_score !== undefined)
        .map(app => app.confidence_score);
    const avgConfidence = confidenceScores.length > 0
        ? (confidenceScores.reduce((a, b) => a + b, 0) / confidenceScores.length * 100).toFixed(0)
        : 0;
    
    const mcpSupportedApps = apps.filter(app => app.mcp_support === true).length;
    const mcpSupport = totalApps > 0 ? (mcpSupportedApps / totalApps * 100).toFixed(0) : 0;
    
    return {
        totalApps,
        verifiedApps,
        avgConfidence,
        mcpSupport
    };
}

/**
 * Update statistics display.
 */
function updateStatistics() {
    const stats = calculateStatistics();
    
    document.getElementById('total-apps').textContent = stats.totalApps;
    document.getElementById('verified-apps').textContent = stats.verifiedApps;
    document.getElementById('avg-confidence').textContent = `${stats.avgConfidence}%`;
    document.getElementById('mcp-support').textContent = `${stats.mcpSupport}%`;
}

// ============================================================================
// Chart Rendering
// ============================================================================

/**
 * Initialize all charts.
 * 
 * @param {Array} apps - Array of application objects
 */
function initializeCharts(apps) {
    renderCategoryChart(apps);
    renderAuthChart(apps);
    renderBuildabilityChart(apps);
    renderConfidenceChart(apps);
}

/**
 * Render category distribution chart.
 * 
 * @param {Array} apps - Array of application objects
 */
function renderCategoryChart(apps) {
    const ctx = document.getElementById('category-chart');
    if (!ctx) return;
    
    // TODO: Implement category distribution calculation
    const categoryCounts = {};
    apps.forEach(app => {
        const category = app.category || 'other';
        categoryCounts[category] = (categoryCounts[category] || 0) + 1;
    });
    
    const labels = Object.keys(categoryCounts);
    const data = Object.values(categoryCounts);
    
    // Destroy existing chart if it exists
    if (AppState.charts.category) {
        AppState.charts.category.destroy();
    }
    
    AppState.charts.category = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.map(l => formatLabel(l)),
            datasets: [{
                data: data,
                backgroundColor: [
                    '#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
                    '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16'
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: {
                            size: 11
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Render authentication methods chart.
 * 
 * @param {Array} apps - Array of application objects
 */
function renderAuthChart(apps) {
    const ctx = document.getElementById('auth-chart');
    if (!ctx) return;
    
    // TODO: Implement auth methods calculation
    const authCounts = {};
    apps.forEach(app => {
        if (app.auth_methods && Array.isArray(app.auth_methods)) {
            app.auth_methods.forEach(method => {
                authCounts[method] = (authCounts[method] || 0) + 1;
            });
        }
    });
    
    const labels = Object.keys(authCounts);
    const data = Object.values(authCounts);
    
    // Destroy existing chart if it exists
    if (AppState.charts.auth) {
        AppState.charts.auth.destroy();
    }
    
    AppState.charts.auth = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.map(l => formatLabel(l)),
            datasets: [{
                label: 'Number of Apps',
                data: data,
                backgroundColor: '#2563eb',
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

/**
 * Render buildability assessment chart.
 * 
 * @param {Array} apps - Array of application objects
 */
function renderBuildabilityChart(apps) {
    const ctx = document.getElementById('buildability-chart');
    if (!ctx) return;
    
    // TODO: Implement buildability calculation
    const buildabilityCounts = { high: 0, medium: 0, low: 0 };
    apps.forEach(app => {
        const buildability = app.buildability || 'unknown';
        if (buildabilityCounts.hasOwnProperty(buildability)) {
            buildabilityCounts[buildability]++;
        }
    });
    
    const labels = Object.keys(buildabilityCounts);
    const data = Object.values(buildabilityCounts);
    const colors = ['#10b981', '#f59e0b', '#ef4444'];
    
    // Destroy existing chart if it exists
    if (AppState.charts.buildability) {
        AppState.charts.buildability.destroy();
    }
    
    AppState.charts.buildability = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels.map(l => formatLabel(l)),
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: {
                            size: 11
                        }
                    }
                }
            }
        }
    });
}

/**
 * Render confidence score distribution chart.
 * 
 * @param {Array} apps - Array of application objects
 */
function renderConfidenceChart(apps) {
    const ctx = document.getElementById('confidence-chart');
    if (!ctx) return;
    
    // TODO: Implement confidence distribution calculation
    const ranges = {
        '0.0-0.2': 0,
        '0.2-0.4': 0,
        '0.4-0.6': 0,
        '0.6-0.8': 0,
        '0.8-1.0': 0
    };
    
    apps.forEach(app => {
        const score = app.confidence_score || 0;
        if (score < 0.2) ranges['0.0-0.2']++;
        else if (score < 0.4) ranges['0.2-0.4']++;
        else if (score < 0.6) ranges['0.4-0.6']++;
        else if (score < 0.8) ranges['0.6-0.8']++;
        else ranges['0.8-1.0']++;
    });
    
    const labels = Object.keys(ranges);
    const data = Object.values(ranges);
    
    // Destroy existing chart if it exists
    if (AppState.charts.confidence) {
        AppState.charts.confidence.destroy();
    }
    
    AppState.charts.confidence = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Apps',
                data: data,
                backgroundColor: '#8b5cf6',
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// ============================================================================
// Table Management
// ============================================================================

/**
 * Populate applications table.
 * 
 * @param {Array} apps - Array of application objects
 */
function populateTable(apps) {
    const tbody = document.getElementById('apps-tbody');
    if (!tbody) return;
    
    if (apps.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="empty-state">
                    <h3>No applications found</h3>
                    <p>Try adjusting your filters or load data to see results.</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = apps.map(app => createTableRow(app)).join('');
    
    // Add click handlers to rows
    tbody.querySelectorAll('tr').forEach(row => {
        row.addEventListener('click', () => {
            const appName = row.dataset.appName;
            const app = AppState.apps.find(a => a.name === appName);
            if (app) {
                showAppDetails(app);
            }
        });
    });
}

/**
 * Create table row HTML for an application.
 * 
 * @param {Object} app - Application object
 * @returns {string} HTML string for table row
 */
function createTableRow(app) {
    return `
        <tr data-app-name="${escapeHtml(app.name)}">
            <td><strong>${escapeHtml(app.name)}</strong></td>
            <td>${formatLabel(app.category)}</td>
            <td>${escapeHtml(app.description || 'N/A')}</td>
            <td>${formatAuthMethods(app.auth_methods)}</td>
            <td>${formatBoolean(app.self_serve)}</td>
            <td>${formatBoolean(app.mcp_support)}</td>
            <td>${formatBuildability(app.buildability)}</td>
            <td>${formatConfidence(app.confidence_score)}</td>
            <td>${formatStatus(app.verification_status)}</td>
        </tr>
    `;
}

// ============================================================================
// Filtering and Search
// ============================================================================

/**
 * Apply filters to applications.
 */
function applyFilters() {
    const { search, category, buildability } = AppState.currentFilters;
    
    AppState.filteredApps = AppState.apps.filter(app => {
        // Search filter
        if (search) {
            const searchLower = search.toLowerCase();
            const matchesSearch = 
                app.name.toLowerCase().includes(searchLower) ||
                (app.description && app.description.toLowerCase().includes(searchLower));
            if (!matchesSearch) return false;
        }
        
        // Category filter
        if (category && app.category !== category) {
            return false;
        }
        
        // Buildability filter
        if (buildability && app.buildability !== buildability) {
            return false;
        }
        
        return true;
    });
    
    populateTable(AppState.filteredApps);
    updateCategoryFilter();
}

/**
 * Update category filter dropdown.
 */
function updateCategoryFilter() {
    const select = document.getElementById('category-filter');
    if (!select) return;
    
    const categories = [...new Set(AppState.apps.map(app => app.category).filter(Boolean))];
    const currentValue = select.value;
    
    select.innerHTML = '<option value="">All Categories</option>' +
        categories.map(cat => `<option value="${cat}">${formatLabel(cat)}</option>`).join('');
    
    select.value = currentValue;
}

/**
 * Setup filter event listeners.
 */
function setupFilters() {
    // Search input
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            AppState.currentFilters.search = e.target.value;
            applyFilters();
        });
    }
    
    // Category filter
    const categoryFilter = document.getElementById('category-filter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', (e) => {
            AppState.currentFilters.category = e.target.value;
            applyFilters();
        });
    }
    
    // Buildability filter
    const buildabilityFilter = document.getElementById('buildability-filter');
    if (buildabilityFilter) {
        buildabilityFilter.addEventListener('change', (e) => {
            AppState.currentFilters.buildability = e.target.value;
            applyFilters();
        });
    }
}

// ============================================================================
// Modal Management
// ============================================================================

/**
 * Show application details in modal.
 * 
 * @param {Object} app - Application object
 */
function showAppDetails(app) {
    const modal = document.getElementById('details-modal');
    const modalBody = document.getElementById('modal-body');
    
    if (!modal || !modalBody) return;
    
    modalBody.innerHTML = `
        <h2>${escapeHtml(app.name)}</h2>
        
        <div class="modal-section">
            <h3>Category</h3>
            <p>${formatLabel(app.category)}</p>
        </div>
        
        <div class="modal-section">
            <h3>Description</h3>
            <p>${escapeHtml(app.description || 'N/A')}</p>
        </div>
        
        <div class="modal-section">
            <h3>Authentication Methods</h3>
            <p>${formatAuthMethods(app.auth_methods, true)}</p>
        </div>
        
        <div class="modal-section">
            <h3>Self-Serve</h3>
            <p>${formatBoolean(app.self_serve)}</p>
        </div>
        
        <div class="modal-section">
            <h3>API Surface</h3>
            <p>${escapeHtml(app.api_surface || 'N/A')}</p>
        </div>
        
        <div class="modal-section">
            <h3>MCP Support</h3>
            <p>${formatBoolean(app.mcp_support)}</p>
        </div>
        
        <div class="modal-section">
            <h3>Buildability</h3>
            <p>${formatBuildability(app.buildability)}</p>
        </div>
        
        <div class="modal-section">
            <h3>Main Blocker</h3>
            <p>${escapeHtml(app.main_blocker || 'N/A')}</p>
        </div>
        
        <div class="modal-section">
            <h3>Evidence URL</h3>
            <p>${app.evidence_url ? `<a href="${escapeHtml(app.evidence_url)}" target="_blank">${escapeHtml(app.evidence_url)}</a>` : 'N/A'}</p>
        </div>
        
        <div class="modal-section">
            <h3>Confidence Score</h3>
            <p>${(app.confidence_score * 100).toFixed(0)}%</p>
        </div>
        
        <div class="modal-section">
            <h3>Verification Status</h3>
            <p>${formatStatus(app.verification_status)}</p>
        </div>
        
        ${app.notes ? `
        <div class="modal-section">
            <h3>Notes</h3>
            <p>${escapeHtml(app.notes)}</p>
        </div>
        ` : ''}
        
        <div class="modal-section">
            <h3>Researched At</h3>
            <p>${formatDate(app.researched_at)}</p>
        </div>
    `;
    
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

/**
 * Close modal.
 */
function closeModal() {
    const modal = document.getElementById('details-modal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = 'auto';
    }
}

/**
 * Setup modal event listeners.
 */
function setupModal() {
    const modal = document.getElementById('details-modal');
    const closeBtn = modal ? modal.querySelector('.close') : null;
    
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }
    
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
    }
    
    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

// ============================================================================
// Formatting Utilities
// ============================================================================

/**
 * Format label for display.
 * 
 * @param {string} label - Label to format
 * @returns {string} Formatted label
 */
function formatLabel(label) {
    if (!label) return 'N/A';
    return label
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Escape HTML to prevent XSS.
 * 
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format authentication methods for display.
 * 
 * @param {Array} methods - Array of auth methods
 * @param {boolean} detailed - Whether to show detailed format
 * @returns {string} Formatted auth methods
 */
function formatAuthMethods(methods, detailed = false) {
    if (!methods || !Array.isArray(methods) || methods.length === 0) {
        return 'N/A';
    }
    
    if (detailed) {
        return methods.map(m => formatLabel(m)).join(', ');
    }
    
    return methods.length + ' method' + (methods.length > 1 ? 's' : '');
}

/**
 * Format boolean value for display.
 * 
 * @param {boolean|null} value - Boolean value
 * @returns {string} Formatted boolean
 */
function formatBoolean(value) {
    if (value === true) return '<span class="badge badge-true">Yes</span>';
    if (value === false) return '<span class="badge badge-false">No</span>';
    return 'N/A';
}

/**
 * Format buildability for display.
 * 
 * @param {string} buildability - Buildability value
 * @returns {string} Formatted buildability
 */
function formatBuildability(buildability) {
    if (!buildability) return 'N/A';
    
    const badgeClass = {
        'high': 'badge-high',
        'medium': 'badge-medium',
        'low': 'badge-low'
    }[buildability] || '';
    
    return badgeClass ? `<span class="badge ${badgeClass}">${formatLabel(buildability)}</span>` : formatLabel(buildability);
}

/**
 * Format confidence score for display.
 * 
 * @param {number} score - Confidence score
 * @returns {string} Formatted confidence
 */
function formatConfidence(score) {
    if (score === null || score === undefined) return 'N/A';
    const percentage = (score * 100).toFixed(0);
    return `${percentage}%`;
}

/**
 * Format verification status for display.
 * 
 * @param {string} status - Verification status
 * @returns {string} Formatted status
 */
function formatStatus(status) {
    if (!status) return 'N/A';
    
    const badgeClass = {
        'verified': 'badge-verified',
        'pending': 'badge-pending',
        'needs_review': 'badge-needs_review',
        'failed': 'badge-failed'
    }[status] || '';
    
    return badgeClass ? `<span class="badge ${badgeClass}">${formatLabel(status)}</span>` : formatLabel(status);
}

/**
 * Format date for display.
 * 
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'N/A';
    
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ============================================================================
// UI Helpers
// ============================================================================

/**
 * Show loading indicator.
 */
function showLoading() {
    const tbody = document.getElementById('apps-tbody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">Loading applications...</td></tr>';
    }
}

/**
 * Hide loading indicator.
 */
function hideLoading() {
    // Loading indicator is replaced when data is loaded
}

/**
 * Show error message.
 * 
 * @param {string} message - Error message
 */
function showError(message) {
    const tbody = document.getElementById('apps-tbody');
    if (tbody) {
        tbody.innerHTML = `<tr><td colspan="9" class="empty-state"><h3>Error</h3><p>${escapeHtml(message)}</p></td></tr>`;
    }
}

/**
 * Show empty state message.
 */
function showEmptyState() {
    const tbody = document.getElementById('apps-tbody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="empty-state">
                    <h3>No applications loaded</h3>
                    <p>Load data to see applications here.</p>
                </td>
            </tr>
        `;
    }
}

// ============================================================================
// Initialization
// ============================================================================

/**
 * Initialize dashboard.
 * 
 * @param {string} dataUrl - URL to data file
 */
async function initializeDashboard(dataUrl) {
    try {
        // Load data
        const apps = await loadData(dataUrl);
        
        if (apps.length === 0) {
            showEmptyState();
            return;
        }
        
        // Update statistics
        updateStatistics();
        
        // Initialize charts
        initializeCharts(apps);
        
        // Populate table
        populateTable(apps);
        
        // Setup filters
        setupFilters();
        
        // Setup modal
        setupModal();
        
        console.log(`Dashboard initialized with ${apps.length} applications`);
        
    } catch (error) {
        console.error('Failed to initialize dashboard:', error);
        showError('Failed to initialize dashboard. Please refresh the page.');
    }
}

// ============================================================================
// Event Listeners
// ============================================================================

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Try to load data from default location
    initializeDashboard('data/apps.json');
});

// ============================================================================
// Export for Testing
// ============================================================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        loadData,
        calculateStatistics,
        applyFilters,
        formatLabel,
        escapeHtml,
        AppState
    };
}