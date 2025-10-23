// ============================================================================
// DASHBOARD MANAGER - CraftRMN Pro - VERSIÓN MEJORADA
// Gestión completa de estadísticas y comparación de muestras
// ✅ Actualizado para analyzer_improved.py
// ============================================================================

class DashboardManager {
    constructor() {
        this.allAnalyses = [];
        this.selectedSamples = new Set();
        this.maxSelectedSamples = 5;
        this.charts = {
            trend: null,
            distribution: null,
            comparison: null
        };
        
        this.statsCache = null;
        this.lastUpdate = null;
    }

    // ========================================================================
    // INICIALIZACIÓN
    // ========================================================================
    
    async init() {
        try {
            window.APP_LOGGER.info('Initializing Dashboard Manager...');
            
            // Configurar event listeners
            this.setupEventListeners();
            
            // Cargar datos iniciales
            await this.loadDashboardData();
            
            window.APP_LOGGER.info('Dashboard Manager initialized');
        } catch (error) {
            window.APP_LOGGER.error('Failed to initialize Dashboard:', error);
            if (typeof UIManager !== 'undefined') UIManager.showNotification('Error al cargar el dashboard', 'error');
        }
    }

    setupEventListeners() {
        // Botón de actualizar dashboard
        const refreshBtn = document.getElementById('refreshDashboardBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshDashboard());
        }

        // Botón de exportar comparación
        const exportCompareBtn = document.getElementById('exportComparisonBtn');
        if (exportCompareBtn) {
            exportCompareBtn.addEventListener('click', () => this.exportComparison());
        }

        // Filtros de fecha en dashboard
        const dateFilterDash = document.getElementById('dashboardDateFilter');
        if (dateFilterDash) {
            dateFilterDash.addEventListener('change', () => this.filterDashboardData());
        }
    }

    // ========================================================================
    // CARGA DE DATOS
    // ========================================================================

    async loadDashboardData() {
        try {
            // Obtener todos los análisis del backend
            const data = await APIClient.getAnalysisList();
            this.allAnalyses = data.analyses || [];
            
            // Calcular estadísticas
            this.calculateStats();
            
            // Renderizar dashboard
            this.renderDashboard();
            
            this.lastUpdate = new Date();
            window.APP_LOGGER.debug(`Dashboard data loaded: ${this.allAnalyses.length} analyses`);
            
        } catch (error) {
            window.APP_LOGGER.error('Failed to load dashboard data:', error);
            throw error; // Re-throw error to be caught by refreshDashboard if called from there
        }
    }

    async refreshDashboard() {
        const refreshBtn = document.getElementById('refreshDashboardBtn');
        if (refreshBtn && typeof UIManager !== 'undefined') {
            UIManager.updateButtonState(refreshBtn, 'loading');
        }

        try {
            await this.loadDashboardData();
             if (typeof UIManager !== 'undefined') {
                 UIManager.showNotification(
                      LanguageManager.t('dashboard.refreshSuccess'),
                      'success'
                 );
             }
        } catch (error) {
             if (typeof UIManager !== 'undefined') {
                 UIManager.showNotification(
                      LanguageManager.t('dashboard.refreshError'),
                      'error'
                 );
             }
        } finally {
            if (refreshBtn && typeof UIManager !== 'undefined') {
                UIManager.updateButtonState(refreshBtn, 'default');
            }
        }
    }

    // ========================================================================
    // CÁLCULO DE ESTADÍSTICAS
    // ========================================================================

    calculateStats() {
        if (!this.allAnalyses || this.allAnalyses.length === 0) { // Add check for null/undefined
            this.statsCache = {
                totalAnalyses: 0, avgConcentration: 0, avgPfas: 0, avgFluor: 0,
                outOfLimits: 0, lastWeek: 0, lastMonth: 0, avgQuality: 0,
                avgSNR: 0, highQualitySamples: 0
            };
            return;
        }

        const now = new Date();
        const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        const oneMonthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

        let totalConcentration = 0, totalPfas = 0, totalFluor = 0, totalQuality = 0, totalSNR = 0;
        let count = 0, snrCount = 0, outOfLimits = 0, lastWeek = 0, lastMonth = 0, highQualitySamples = 0;

        this.allAnalyses.forEach(analysis => {
             // Skip analyses with errors or missing data points needed for stats
             if (!analysis || analysis.error || analysis.concentration === undefined || analysis.pfas === undefined || analysis.fluor === undefined || analysis.quality === undefined || !analysis.created) {
                  return;
             }
             count++; // Only count valid analyses for averages

            const concentration = analysis.concentration || 0;
            const pfas = analysis.pfas || 0;
            const fluor = analysis.fluor || 0;
            const quality = analysis.quality || 0;
            const created = new Date(analysis.created);

            totalConcentration += concentration;
            totalPfas += pfas;
            totalFluor += fluor;
            totalQuality += quality;

            // SNR promedio (si existe en los datos)
            if (analysis.snr !== null && analysis.snr !== undefined) { // Check for null/undefined specifically
                totalSNR += analysis.snr;
                snrCount++;
            }

            if (quality >= 8) highQualitySamples++;
            if (created >= oneWeekAgo) lastWeek++;
            if (created >= oneMonthAgo) lastMonth++;
            if (concentration > 1.0) outOfLimits++; // Example limit
        });

        this.statsCache = {
            totalAnalyses: this.allAnalyses.length, // Total files listed
            avgConcentration: count > 0 ? (totalConcentration / count).toFixed(4) : 0,
            avgPfas: count > 0 ? (totalPfas / count).toFixed(2) : 0,
            avgFluor: count > 0 ? (totalFluor / count).toFixed(2) : 0,
            outOfLimits: outOfLimits,
            lastWeek: lastWeek,
            lastMonth: lastMonth,
            avgQuality: count > 0 ? (totalQuality / count).toFixed(1) : 0,
            avgSNR: snrCount > 0 ? (totalSNR / snrCount).toFixed(2) : 'N/A',
            highQualitySamples: highQualitySamples
        };

        window.APP_LOGGER.debug('Stats calculated:', this.statsCache);
    }

    // ========================================================================
    // RENDERIZADO DEL DASHBOARD
    // ========================================================================

    renderDashboard() {
        this.renderStatsCards();
        this.renderTrendChart();
        this.renderDistributionChart();
        this.renderRecentAnalysesTable();
    }

    renderStatsCards() {
        const stats = this.statsCache || {}; // Use empty object if cache is null

        // Helper to update text safely
        const updateText = (id, value, suffix = '') => {
             const el = document.getElementById(id);
             if (el) el.textContent = (value !== null && value !== undefined && value !== 'N/A') ? `${value}${suffix}` : '--';
        };

        updateText('dashTotalAnalyses', stats.totalAnalyses);
        updateText('dashAvgConcentration', stats.avgConcentration, ' mM');
        updateText('dashOutOfLimits', stats.outOfLimits);
        updateText('dashLastWeek', stats.lastWeek);
        updateText('dashAvgQuality', stats.avgQuality, '/10');
        updateText('dashAvgPfas', stats.avgPfas, '%');
        updateText('dashAvgSNR', stats.avgSNR); // Assuming you add an element with id="dashAvgSNR"
        updateText('dashHighQuality', stats.highQualitySamples); // Assuming you add id="dashHighQuality"
    }

    renderTrendChart() {
        if (!this.allAnalyses || this.allAnalyses.length === 0) {
            this.clearChart('trendChart');
            return;
        }
        
        // Filter out invalid entries before sorting/mapping
        const validAnalyses = this.allAnalyses.filter(a => a && !a.error && a.created);

        const sortedAnalyses = [...validAnalyses].sort((a, b) => new Date(a.created) - new Date(b.created));

        const dates = sortedAnalyses.map(a => new Date(a.created).toLocaleDateString(LanguageManager.currentLang));
        const concentrations = sortedAnalyses.map(a => a.concentration || 0);
        const pfasValues = sortedAnalyses.map(a => a.pfas || 0);
        const qualityValues = sortedAnalyses.map(a => a.quality || 0);

        const trace1 = { x: dates, y: concentrations, type: 'scatter', mode: 'lines+markers', name: LanguageManager.t('results.concentration'), line: { color: '#3498db', width: 2 }, marker: { size: 6 } };
        const trace2 = { x: dates, y: pfasValues, type: 'scatter', mode: 'lines+markers', name: LanguageManager.t('results.pifas'), line: { color: '#e74c3c', width: 2 }, marker: { size: 6 }, yaxis: 'y2' };
        const trace3 = { x: dates, y: qualityValues, type: 'scatter', mode: 'lines+markers', name: LanguageManager.t('results.quality'), line: { color: '#2ecc71', width: 2 }, marker: { size: 6 }, yaxis: 'y3' };

        const layout = {
            title: LanguageManager.t('dashboard.trendTitle') || 'Tendencias Temporales',
            xaxis: { title: LanguageManager.t('dashboard.date') || 'Fecha' },
            yaxis: { title: LanguageManager.t('results.concentration') + ' (mM)', side: 'left' },
            yaxis2: { title: 'PFAS (%)', overlaying: 'y', side: 'right' },
            yaxis3: { title: LanguageManager.t('results.quality'), overlaying: 'y', side: 'right', position: 0.95 }, // Adjust position if needed
            hovermode: 'x unified', showlegend: true, legend: { orientation: 'h', y: -0.2, yanchor: 'top' }, // Move legend below
            margin: { l: 50, r: 100, b: 80, t: 50 } // Adjust margins
        };

        const config = { responsive: true, displayModeBar: true, displaylogo: false, locale: LanguageManager.currentLang };

        const chartDiv = document.getElementById('trendChart');
        if (chartDiv) {
            Plotly.newPlot('trendChart', [trace1, trace2, trace3], layout, config)
                .then(() => { this.charts.trend = chartDiv; window.APP_LOGGER.debug('Trend chart rendered'); })
                .catch(error => { window.APP_LOGGER.error('Error rendering trend chart:', error); });
        }
    }

    renderDistributionChart() {
         if (!this.allAnalyses || this.allAnalyses.length === 0) {
            this.clearChart('distributionChart');
            return;
        }
        
        const validAnalyses = this.allAnalyses.filter(a => a && !a.error && a.quality !== null && a.quality !== undefined);


        const qualityDistribution = {
            'Excelente (>=8)': 0,
            'Buena (6-8)': 0,
            'Regular (4-6)': 0,
            'Baja (<4)': 0
        };
        const qualityKeys = Object.keys(qualityDistribution); // Store keys in order

        validAnalyses.forEach(a => {
            const quality = a.quality;
            if (quality >= 8) qualityDistribution[qualityKeys[0]]++;
            else if (quality >= 6) qualityDistribution[qualityKeys[1]]++;
            else if (quality >= 4) qualityDistribution[qualityKeys[2]]++;
            else qualityDistribution[qualityKeys[3]]++;
        });

        // Translate labels
        const labelTranslations = {
            'Excelente (>=8)': LanguageManager.t('dashboard.qualityLabels.excellent') || 'Excelente (≥8)',
            'Buena (6-8)': LanguageManager.t('dashboard.qualityLabels.good') || 'Buena (6-8)',
            'Regular (4-6)': LanguageManager.t('dashboard.qualityLabels.regular') || 'Regular (4-6)',
            'Baja (<4)': LanguageManager.t('dashboard.qualityLabels.low') || 'Baja (<4)'
        };
        const translatedLabels = qualityKeys.map(key => labelTranslations[key] || key);


        const trace = {
            labels: translatedLabels, // Use translated labels
            values: Object.values(qualityDistribution),
            type: 'pie',
            marker: { colors: ['#2ecc71', '#3498db', '#f39c12', '#e74c3c'] },
            textinfo: 'percent', // Show only percent on slices
             hoverinfo: 'label+value+percent', // Show details on hover
             insidetextorientation: 'radial' // Improve text readability
        };

        const layout = {
            title: LanguageManager.t('dashboard.distributionTitle') || 'Distribución de Calidad',
            showlegend: true,
             legend: { orientation: 'h', y: -0.1, yanchor: 'top' }, // Move legend below
            height: 400,
             margin: { l: 20, r: 20, t: 50, b: 50 } // Adjust margins
        };

        const config = { responsive: true, displayModeBar: false, locale: LanguageManager.currentLang };

        const chartDiv = document.getElementById('distributionChart');
        if (chartDiv) {
            Plotly.newPlot('distributionChart', [trace], layout, config)
                .then(() => { this.charts.distribution = chartDiv; window.APP_LOGGER.debug('Distribution chart rendered'); })
                .catch(error => { window.APP_LOGGER.error('Error rendering distribution chart:', error); });
        }
         // Add these translation keys:
         // "dashboard.qualityLabels": {
         //      "Excelente (>=8)": "Excelente (>=8)",
         //      "Buena (6-8)": "Buena (6-8)",
         //      "Regular (4-6)": "Regular (4-6)",
         //      "Baja (<4)": "Baja (<4)"
         // }
    }


    renderRecentAnalysesTable() {
        const tbody = document.querySelector('#recentAnalysesTable tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        const validAnalyses = this.allAnalyses.filter(a => a && !a.error && a.created);


        const recentAnalyses = [...validAnalyses]
            .sort((a, b) => new Date(b.created) - new Date(a.created))
            .slice(0, 10);

        if (recentAnalyses.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" data-i18n="dashboard.noData" class="empty-state-cell"></td></tr>`; // Use 5 cols now
            LanguageManager.applyTranslationsToElement(tbody);
            return;
        }

        recentAnalyses.forEach(analysis => {
            const row = document.createElement('tr');
            const date = new Date(analysis.created).toLocaleString(LanguageManager.currentLang);
            const fluor = UIManager.formatNumber(analysis.fluor, 2) + '%';
            const pfas = UIManager.formatNumber(analysis.pfas, 2) + '%';
            const quality = UIManager.formatNumber(analysis.quality, 1);
            const qualityClass = this.getQualityClass(analysis.quality);

            row.innerHTML = `
                <td>${UIManager.escapeHtml(analysis.filename || analysis.name)}</td>
                <td>${date}</td>
                <td>${fluor}</td>
                <td>${pfas}</td>
                <td><span class="quality-badge ${qualityClass}">${quality}/10</span></td>
            `;
            tbody.appendChild(row);
        });
    }


    // ========================================================================
    // INICIALIZACIÓN DE COMPARACIÓN
    // ========================================================================

    async initComparison() {
        try {
            window.APP_LOGGER.info('Initializing Comparison tab...');
            this.selectedSamples.clear();
            await this.loadComparisonData(); // Renamed function for clarity
            this.renderSampleSelector();
            this.clearComparison(); // Call the function that now exists
            window.APP_LOGGER.info('Comparison tab initialized');
        } catch (error) {
            window.APP_LOGGER.error('Failed to initialize Comparison:', error);
            if (typeof UIManager !== 'undefined') UIManager.showNotification('Error al cargar la comparación', 'error');
        }
    }

     // Renamed from loadComparisonData to avoid conflict if dashboard data differs
    async loadComparisonData() {
        try {
            // Re-use dashboard data if already loaded recently, or load fresh
            if (!this.allAnalyses || this.allAnalyses.length === 0 || !this.lastUpdate || (new Date() - this.lastUpdate > 60000)) { // Reload if older than 1 min
                 const data = await APIClient.getAnalysisList();
                 this.allAnalyses = data.analyses || [];
                 this.lastUpdate = new Date();
                 window.APP_LOGGER.debug(`Comparison data reloaded: ${this.allAnalyses.length} analyses`);
            } else {
                 window.APP_LOGGER.debug(`Using cached dashboard data for comparison: ${this.allAnalyses.length} analyses`);
            }
        } catch (error) {
            window.APP_LOGGER.error('Failed to load comparison data:', error);
            this.allAnalyses = []; // Ensure it's an empty array on error
            throw error; // Re-throw to be caught by initComparison
        }
    }


    renderSampleSelector() {
        const container = document.getElementById('sampleSelectorContainer');
        if (!container) {
            window.APP_LOGGER.warn('Sample selector container not found');
            return;
        }
        container.innerHTML = ''; // Clear previous buttons

         const validAnalyses = this.allAnalyses.filter(a => a && !a.error && a.name);


        if (validAnalyses.length === 0) {
            container.innerHTML = `<div class="empty-state-comparison" data-i18n="comparison.noSamples"></div>`;
            LanguageManager.applyTranslationsToElement(container);
            return;
        }

        validAnalyses.forEach(analysis => {
            const button = document.createElement('button');
            button.className = 'sample-select-btn';
            button.dataset.analysisName = analysis.name; // Use unique name/ID
            
            const displayName = analysis.filename || analysis.name;
            const date = analysis.created ? new Date(analysis.created).toLocaleDateString(LanguageManager.currentLang) : '--';
            
            button.innerHTML = `
                <div class="sample-btn-content">
                    <div class="sample-btn-name">${this.escapeHtml(displayName)}</div>
                    <div class="sample-btn-date">${date}</div>
                </div>
                <i class="fas fa-check-circle sample-btn-check"></i>
            `;
            
            // Re-apply selected state if already in the set
            if (this.selectedSamples.has(analysis.name)) {
                 button.classList.add('selected');
            }

            button.addEventListener('click', () => {
                this.toggleSampleSelection(analysis.name); // Pass unique name/ID
                this.updateSampleButton(button, this.selectedSamples.has(analysis.name));
            });
            container.appendChild(button);
        });
        window.APP_LOGGER.debug(`Rendered ${validAnalyses.length} sample buttons`);
    }

    updateSampleButton(button, isSelected) {
        if (isSelected) button.classList.add('selected');
        else button.classList.remove('selected');
    }

    escapeHtml(text = '') { // Add default value
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }


    // ========================================================================
    // COMPARACIÓN DE MUESTRAS
    // ========================================================================

    toggleSampleSelection(analysisName) {
         if (!analysisName) return; // Add check

        if (this.selectedSamples.has(analysisName)) {
            this.selectedSamples.delete(analysisName);
        } else {
            if (this.selectedSamples.size >= this.maxSelectedSamples) {
                 if (typeof UIManager !== 'undefined') {
                     UIManager.showNotification(
                          LanguageManager.t('comparison.maxSamplesReached') || `Máximo ${this.maxSelectedSamples} muestras`, // Add fallback
                          'warning'
                     );
                 }
                return;
            }
            this.selectedSamples.add(analysisName);
        }
        window.APP_LOGGER.debug(`Selected samples (${this.selectedSamples.size}): ${Array.from(this.selectedSamples).join(', ')}`);
        this.updateComparisonView(); // Update chart and table
    }


    updateComparisonView() {
        // Find selected analyses from the full list using the unique names/IDs
         const selectedAnalyses = this.allAnalyses.filter(a => a && this.selectedSamples.has(a.name));


        // Update count display
         const countDisplay = document.getElementById('selectedCountDisplay'); // Needs <span id="selectedCountDisplay"></span> in HTML
         if (countDisplay) {
              countDisplay.textContent = LanguageManager.t('comparison.selected', { count: selectedAnalyses.length, max: this.maxSelectedSamples });
         }

        if (selectedAnalyses.length === 0) { // Clear if 0 or 1 selected
            this.clearComparison();
             const tbody = document.querySelector('#comparisonTable tbody');
             if(tbody) {
                  tbody.innerHTML = `<tr><td colspan="6" data-i18n="comparison.selectMoreSamples" class="empty-state-cell"></td></tr>`;
                  // ### CORRECTION ###
                  LanguageManager.applyTranslations(); // Use the general function
             }
            return;
        }


        this.renderComparisonChart(selectedAnalyses);
        this.renderComparisonTable(selectedAnalyses);

        const exportBtn = document.getElementById('exportComparisonBtn');
        if (exportBtn) exportBtn.disabled = false;
    }


    renderComparisonChart(analyses) {
        const chartDiv = document.getElementById('comparisonChart');
        if (!chartDiv) return;
        
        // Ensure analyses have valid data points for charting
        const validAnalyses = analyses.filter(a => a && (a.concentration !== null || a.pfas !== null));
        if (validAnalyses.length === 0) {
             this.clearChart('comparisonChart');
             return;
        }


        const trace1 = {
            x: validAnalyses.map(a => a.filename || a.name),
            y: validAnalyses.map(a => a.concentration ?? 0), // Use nullish coalescing
            type: 'bar', name: LanguageManager.t('results.concentration'), marker: { color: '#3498db' }, yaxis: 'y'
        };
        const trace2 = {
            x: validAnalyses.map(a => a.filename || a.name),
            y: validAnalyses.map(a => a.pfas ?? 0), // Use nullish coalescing
            type: 'bar', name: LanguageManager.t('results.pifas'), marker: { color: '#e74c3c' }, yaxis: 'y2'
        };

        const layout = {
            title: LanguageManager.t('comparison.chartTitle') || 'Comparación de Muestras',
            barmode: 'group',
            yaxis: { title: LanguageManager.t('results.concentration') + ' (mM)', side: 'left' },
            yaxis2: { title: 'PFAS (%)', overlaying: 'y', side: 'right' },
            hovermode: 'x unified', showlegend: true,
             legend: { orientation: 'h', y: -0.2, yanchor: 'top' }, // Legend below
             margin: { l: 50, r: 50, b: 100, t: 50 } // Increase bottom margin for labels
        };
        const config = { responsive: true, displayModeBar: true, displaylogo: false, locale: LanguageManager.currentLang };

        Plotly.newPlot('comparisonChart', [trace1, trace2], layout, config)
            .then(() => { this.charts.comparison = chartDiv; window.APP_LOGGER.debug('Comparison chart rendered'); })
            .catch(error => { window.APP_LOGGER.error('Error rendering comparison chart:', error); });
    }

    // ### CORRECTED renderComparisonTable ###
    renderComparisonTable(analyses) {
        const table = document.getElementById('comparisonTable');
        const thead = table.querySelector('thead');
        const tbody = table.querySelector('tbody');

        if (!thead || !tbody) {
            window.APP_LOGGER.error("Comparison table thead or tbody not found!");
            return;
        }

        // --- 1. Clear Header and Body ---
        thead.innerHTML = '';
        tbody.innerHTML = '';

        if (!analyses || analyses.length === 0) { // Should not happen if called from updateComparisonView
             tbody.innerHTML = `<tr><td colspan="6" data-i18n="comparison.selectSamples" class="empty-state-cell"></td></tr>`;
             LanguageManager.applyTranslationsToElement(tbody);
            return;
        }

        // --- 2. Build Header ---
        let headerHtml = '<tr>';
        headerHtml += `<th data-i18n="results.parameter"></th>`; // Parameter column
        analyses.forEach(a => {
            const displayName = this.escapeHtml(a.filename || a.name || 'Muestra');
            let date = '--';
             try { date = a.created ? new Date(a.created).toLocaleDateString(LanguageManager.currentLang) : '--'; } catch(e){}
            headerHtml += `<th>${displayName}<br><small>${date}</small></th>`;
        });
        headerHtml += '</tr>';
        thead.innerHTML = headerHtml;

        // --- 3. Build Body ---
        const parameters = [
            { key: 'fluor', labelKey: 'results.fluor', unit: '%', decimals: 2 },
            { key: 'pfas', labelKey: 'results.pifas', unit: '%', decimals: 2 },
            { key: 'concentration', labelKey: 'results.concentration', unit: 'mM', decimals: 4 },
            { key: 'quality', labelKey: 'results.quality', unit: '/10', decimals: 1 }
        ];

        parameters.forEach(param => {
            let rowHtml = '<tr>';
             // Use unit in label if available
             const unitLabel = param.unit ? ` (${param.unit})` : '';
            rowHtml += `<td data-i18n="${param.labelKey}"></td>`; // Parameter name (will be translated)

            analyses.forEach(a => {
                let value = '--';
                const rawValue = a[param.key];
                if (rawValue !== null && rawValue !== undefined) {
                    value = UIManager.formatNumber(rawValue, param.decimals);
                    if (param.key === 'quality') {
                        value += '/10'; // Add unit specifically for quality
                    }
                }
                 const qualityClass = (param.key === 'quality' && a.quality !== null) ? this.getQualityClass(a.quality) : '';
                 // Add class to TD for potential styling
                 rowHtml += `<td class="${qualityClass}">${value}</td>`;
            });
            rowHtml += '</tr>';
            tbody.innerHTML += rowHtml;
        });

        // --- 4. Apply Translations ---
        LanguageManager.applyTranslations(); // Apply translations to the whole table/page

        window.APP_LOGGER.debug('Comparison table rendered');
    }
    // ### END CORRECTED renderComparisonTable ###


     // ### NUEVO: Helper function to get quality class ###
    getQualityClass(quality) {
         if (quality === null || quality === undefined) return '';
         if (quality >= 8) return 'quality-excellent';
         if (quality >= 6) return 'quality-good';
         if (quality >= 4) return 'quality-regular';
         return 'quality-low';
    }


    // ### CORRECTED clearComparison ###
    clearComparison() {
        const chartDiv = document.getElementById('comparisonChart');
        if (chartDiv) {
            Plotly.purge('comparisonChart'); // Clear the chart
        }

        const table = document.getElementById('comparisonTable');
        const thead = table ? table.querySelector('thead') : null;
        const tbody = table ? table.querySelector('tbody') : null;


        // Reset table header
         if (thead) {
              thead.innerHTML = `
                   <tr>
                        <th data-i18n="results.parameter"></th>
                        {/* Headers will be added dynamically */}
                   </tr>
              `;
         }

        // Reset table body
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    {/* Adjust colspan dynamically based on max samples or keep it large */}
                    <td colspan="${this.maxSelectedSamples + 1}" class="empty-state-cell">
                        <i class="fas fa-mouse-pointer"></i>
                        <p data-i18n="comparison.selectSamples"></p>
                    </td>
                </tr>
            `;
        }

        const exportBtn = document.getElementById('exportComparisonBtn');
        if (exportBtn) {
            exportBtn.disabled = true; // Disable export button
        }

        // Clear selected samples visually
        document.querySelectorAll('.sample-select-btn.selected').forEach(btn => {
             btn.classList.remove('selected');
        });

        this.selectedSamples.clear(); // Ensure the set is cleared too
        
        // Update selection count display
         const countDisplay = document.getElementById('selectedCountDisplay');
         if (countDisplay) {
             countDisplay.textContent = LanguageManager.t('comparison.selected', { count: 0, max: this.maxSelectedSamples });
         }

        // Apply translations after resetting HTML
        if (table) LanguageManager.applyTranslations(); // Apply to whole page to catch placeholders


        window.APP_LOGGER.debug('Comparison view cleared.');
    }
    // ### END CORRECTED clearComparison ###


    async exportComparison() {
        if (this.selectedSamples.size === 0) {
            if (typeof UIManager !== 'undefined') {
                UIManager.showNotification(
                    LanguageManager.t('comparison.noSamplesSelected'), 'warning'
                );
            }
            return;
        }

        // Mostrar selector de formato
        const format = await this.showFormatSelector();
        if (!format) return;

        const exportBtn = document.getElementById('exportComparisonBtn');
        if(exportBtn && typeof UIManager !== 'undefined') 
            UIManager.updateButtonState(exportBtn, 'loading');

        try {
            const selectedAnalyses = this.allAnalyses.filter(a => this.selectedSamples.has(a.name));
            
            if (format === 'csv') {
                // Exportar CSV (método existente)
                const csvContent = this.generateComparisonCSV(selectedAnalyses);
                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                const link = document.createElement('a');
                const url = URL.createObjectURL(blob);
                link.setAttribute('href', url);
                link.setAttribute('download', `comparison_${new Date().toISOString().split('T')[0]}.csv`);
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
            } else {
                // Exportar en otros formatos usando el backend
                await APIClient.exportReport({
                    type: 'comparison',
                    samples: selectedAnalyses,
                    count: selectedAnalyses.length
                }, format);
            }
            
            if (typeof UIManager !== 'undefined') {
                UIManager.showNotification(LanguageManager.t('comparison.exportSuccess'), 'success');
                if(exportBtn) UIManager.updateButtonState(exportBtn, 'success');
            }
        } catch (error) {
            window.APP_LOGGER.error('Export comparison failed:', error);
            if (typeof UIManager !== 'undefined') {
                UIManager.showNotification(LanguageManager.t('comparison.exportError'), 'error');
                if(exportBtn) UIManager.updateButtonState(exportBtn, 'error');
            }
        }
    }

    showFormatSelector() {
        return new Promise((resolve) => {
            const formats = [
                { value: 'pdf', icon: 'file-pdf', label: 'PDF' },
                { value: 'docx', icon: 'file-word', label: 'Word' },
                { value: 'csv', icon: 'file-csv', label: 'CSV' }
            ];
            
            const buttonsHTML = formats.map(f => 
                `<button class="btn btn-primary format-selector-btn" data-format="${f.value}">
                    <i class="fas fa-${f.icon}"></i> ${f.label}
                </button>`
            ).join('');
            
            const content = `
                <div class="format-selector">
                    <p>Selecciona el formato de exportación:</p>
                    <div class="format-buttons">${buttonsHTML}</div>
                </div>
            `;
            
            UIManager.showModal('Exportar Comparación', content, [
                { text: 'Cancelar', type: 'outline', action: 'close' }
            ]);
            
            document.querySelectorAll('.format-selector-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    UIManager.hideModal();
                    resolve(btn.dataset.format);
                });
            });
        });
    }
    generateComparisonCSV(analyses) {
        // Use translated headers if possible
        const headers = [
            LanguageManager.t('comparison.sample') || 'Sample',
            LanguageManager.t('comparison.date') || 'Date',
            LanguageManager.t('results.fluor') + ' (%)' || 'Fluorine (%)',
            LanguageManager.t('results.pifas') + ' (%)' || 'PFAS (%)',
            LanguageManager.t('results.concentration') + ' (mM)' || 'Concentration (mM)',
            LanguageManager.t('results.quality') || 'Quality'
        ];

         // Helper to safely format CSV values (handle commas, quotes)
         const formatCsvValue = (value) => {
             if (value === null || value === undefined) return '';
             let str = String(value);
             // If value contains comma, double quote, or newline, enclose in double quotes
             if (str.includes(',') || str.includes('"') || str.includes('\n')) {
                  // Escape existing double quotes by doubling them
                  str = str.replace(/"/g, '""');
                  return `"${str}"`;
             }
             return str;
         };


        const rows = analyses.map(a => {
            return [
                formatCsvValue(a.filename || a.name),
                a.created ? new Date(a.created).toISOString().split('T')[0] : '', // Use ISO date for CSV consistency
                UIManager.formatNumber(a.fluor, 2),
                UIManager.formatNumber(a.pfas, 2),
                UIManager.formatNumber(a.concentration, 4),
                UIManager.formatNumber(a.quality, 1)
            ].join(','); // Join values with comma
        });

        // Join header and rows with newline
        return [headers.join(','), ...rows].join('\n');
    }


    // ========================================================================
    // FILTROS DASHBOARD (Parece OK, sin cambios necesarios aquí para los errores reportados)
    // ========================================================================

    filterDashboardData() {
        const filter = document.getElementById('dashboardDateFilter')?.value || 'all';
        const originalAnalyses = this.allAnalyses; // Keep a reference

        try {
            if (filter === 'all') {
                // If filter is 'all', ensure we are using the full original dataset
                // No need to filter, just recalculate and render with full data
                this.calculateStats(); // Recalculate based on potentially full 'this.allAnalyses'
                this.renderDashboard();
                return;
            }

            const now = new Date();
            let startDate;
            switch(filter) {
                case 'today': startDate = new Date(now.setHours(0,0,0,0)); break;
                case 'week': startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000); break;
                case 'month': startDate = new Date(now.getFullYear(), now.getMonth(), 1); break;
            }

            if (startDate) {
                const filteredAnalyses = originalAnalyses.filter(a => a && a.created && new Date(a.created) >= startDate);
                
                // Temporarily override this.allAnalyses FOR CALCULATION ONLY
                this.allAnalyses = filteredAnalyses;
                this.calculateStats(); // Calculate stats based on filtered data
                
                // Restore original data before rendering (render functions use this.allAnalyses)
                this.allAnalyses = originalAnalyses; 
                
                // Render dashboard using the calculated stats (which are based on filtered data)
                // but the charts/tables will use the full data unless modified
                 // TODO: Modify render functions to accept filtered data if charts/tables should also filter
                 this.renderStatsCards(); // This uses this.statsCache (filtered)
                 this.renderTrendChart(); // This currently uses this.allAnalyses (full)
                 this.renderDistributionChart(); // This currently uses this.allAnalyses (full)
                 this.renderRecentAnalysesTable(); // This currently uses this.allAnalyses (full)

            } else {
                 // If no valid startDate, revert to showing all data
                 this.allAnalyses = originalAnalyses;
                 this.calculateStats();
                 this.renderDashboard();
            }
        } finally {
             // Ensure this.allAnalyses is always restored
             this.allAnalyses = originalAnalyses;
        }
    }

}

// Crear instancia global
window.dashboardManager = new DashboardManager();