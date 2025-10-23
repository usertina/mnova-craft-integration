// ============================================================================
// DASHBOARD MANAGER - CraftRMN Pro - VERSIÓN CORREGIDA
// ✅ CORREGIDO: Gráficos ahora usan LanguageManager para las traducciones.
// ✅ CORREGIDO: Añadido listener para exportar dashboard.
// ✅ CORREGIDO: Eliminado el '}' extra al final del archivo.
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

        // Botón de exportar dashboard
        const exportDashBtn = document.getElementById('exportDashboardBtn');
        if (exportDashBtn) {
            exportDashBtn.addEventListener('click', () => this.exportDashboardData());
            window.APP_LOGGER.debug('Export dashboard listener attached');
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
        updateText('dashAvgSNR', stats.avgSNR); 
        updateText('dashHighQuality', stats.highQualitySamples); 
    }

    renderTrendChart() {
        if (!this.allAnalyses || this.allAnalyses.length === 0) {
            // this.clearChart('trendChart'); // Asegúrate que clearChart exista o coméntalo
            return;
        }
        
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
            title: LanguageManager.t('dashboard.trendTitle'),
            xaxis: { title: LanguageManager.t('dashboard.date') },
            yaxis: { title: LanguageManager.t('results.concentration') + ' (mM)', side: 'left' },
            yaxis2: { title: LanguageManager.t('dashboard.pfasAxis'), overlaying: 'y', side: 'right' },
            yaxis3: { title: LanguageManager.t('results.quality'), overlaying: 'y', side: 'right', position: 0.95 }, 
            hovermode: 'x unified', showlegend: true, legend: { orientation: 'h', y: -0.2, yanchor: 'top' },
            margin: { l: 50, r: 100, b: 80, t: 50 } 
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
            // this.clearChart('distributionChart'); // Asegúrate que clearChart exista
            return;
        }
        
        const validAnalyses = this.allAnalyses.filter(a => a && !a.error && a.quality !== null && a.quality !== undefined);

        const qualityDistribution = {
            'Excelente (>=8)': 0,
            'Buena (6-8)': 0,
            'Regular (4-6)': 0,
            'Baja (<4)': 0
        };
        const qualityKeys = Object.keys(qualityDistribution); 

        validAnalyses.forEach(a => {
            const quality = a.quality;
            if (quality >= 8) qualityDistribution[qualityKeys[0]]++;
            else if (quality >= 6) qualityDistribution[qualityKeys[1]]++;
            else if (quality >= 4) qualityDistribution[qualityKeys[2]]++;
            else qualityDistribution[qualityKeys[3]]++;
        });

        const labelTranslations = {
            'Excelente (>=8)': LanguageManager.t('dashboard.qualityLabels.excellent'),
            'Buena (6-8)': LanguageManager.t('dashboard.qualityLabels.good'),
            'Regular (4-6)': LanguageManager.t('dashboard.qualityLabels.regular'),
            'Baja (<4)': LanguageManager.t('dashboard.qualityLabels.low')
        };
        const translatedLabels = qualityKeys.map(key => labelTranslations[key] || key); 


        const trace = {
            labels: translatedLabels, 
            values: Object.values(qualityDistribution),
            type: 'pie',
            marker: { colors: ['#2ecc71', '#3498db', '#f39c12', '#e74c3c'] },
            textinfo: 'percent',
             hoverinfo: 'label+value+percent', 
             insidetextorientation: 'radial'
        };

        const layout = {
            title: LanguageManager.t('dashboard.distributionTitle'), 
            showlegend: true,
             legend: { orientation: 'h', y: -0.1, yanchor: 'top' }, 
            height: 400,
             margin: { l: 20, r: 20, t: 50, b: 50 } 
        };

        const config = { responsive: true, displayModeBar: false, locale: LanguageManager.currentLang };

        const chartDiv = document.getElementById('distributionChart');
        if (chartDiv) {
            Plotly.newPlot('distributionChart', [trace], layout, config)
                .then(() => { this.charts.distribution = chartDiv; window.APP_LOGGER.debug('Distribution chart rendered'); })
                .catch(error => { window.APP_LOGGER.error('Error rendering distribution chart:', error); });
        }
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
            tbody.innerHTML = `<tr><td colspan="5" data-i18n="dashboard.noData" class="empty-state-cell"></td></tr>`; 
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

            const exportCompareBtn = document.getElementById('exportComparisonBtn');
            if (exportCompareBtn) {
                if (!exportCompareBtn.dataset.listenerAttached) {
                    exportCompareBtn.addEventListener('click', () => this.exportComparison());
                    exportCompareBtn.dataset.listenerAttached = 'true';
                    window.APP_LOGGER.debug('Export comparison listener attached');
                }
            }

            await this.loadComparisonData(); 
            this.renderSampleSelector();
            this.clearComparison(); 
            window.APP_LOGGER.info('Comparison tab initialized');
        } catch (error) {
            window.APP_LOGGER.error('Failed to initialize Comparison:', error);
            if (typeof UIManager !== 'undefined') UIManager.showNotification('Error al cargar la comparación', 'error');
        }
    }

    async loadComparisonData() {
        try {
            if (!this.allAnalyses || this.allAnalyses.length === 0 || !this.lastUpdate || (new Date() - this.lastUpdate > 60000)) { 
                 const data = await APIClient.getAnalysisList();
                 this.allAnalyses = data.analyses || [];
                 this.lastUpdate = new Date();
                 window.APP_LOGGER.debug(`Comparison data reloaded: ${this.allAnalyses.length} analyses`);
            } else {
                 window.APP_LOGGER.debug(`Using cached dashboard data for comparison: ${this.allAnalyses.length} analyses`);
            }
        } catch (error) {
            window.APP_LOGGER.error('Failed to load comparison data:', error);
            this.allAnalyses = []; 
            throw error; 
        }
    }


    renderSampleSelector() {
        const container = document.getElementById('sampleSelectorContainer');
        if (!container) {
            window.APP_LOGGER.warn('Sample selector container not found');
            return;
        }
        container.innerHTML = ''; 

         const validAnalyses = this.allAnalyses.filter(a => a && !a.error && a.name);


        if (validAnalyses.length === 0) {
            container.innerHTML = `<div class="empty-state-comparison" data-i18n="comparison.noSamples"></div>`;
            LanguageManager.applyTranslationsToElement(container);
            return;
        }

        validAnalyses.forEach(analysis => {
            const button = document.createElement('button');
            button.className = 'sample-select-btn';
            button.dataset.analysisName = analysis.name; 
            
            const displayName = analysis.filename || analysis.name;
            const date = analysis.created ? new Date(analysis.created).toLocaleDateString(LanguageManager.currentLang) : '--';
            
            button.innerHTML = `
                <div class="sample-btn-content">
                    <div class="sample-btn-name">${this.escapeHtml(displayName)}</div>
                    <div class="sample-btn-date">${date}</div>
                </div>
                <i class="fas fa-check-circle sample-btn-check"></i>
            `;
            
            if (this.selectedSamples.has(analysis.name)) {
                 button.classList.add('selected');
            }

            button.addEventListener('click', () => {
                this.toggleSampleSelection(analysis.name); 
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

    escapeHtml(text = '') { 
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }


    // ========================================================================
    // COMPARACIÓN DE MUESTRAS
    // ========================================================================

    toggleSampleSelection(analysisName) {
         if (!analysisName) return; 

        if (this.selectedSamples.has(analysisName)) {
            this.selectedSamples.delete(analysisName);
        } else {
            if (this.selectedSamples.size >= this.maxSelectedSamples) {
                 if (typeof UIManager !== 'undefined') {
                     UIManager.showNotification(
                          LanguageManager.t('comparison.maxSamplesReached') || `Máximo ${this.maxSelectedSamples} muestras`, 
                          'warning'
                     );
                 }
                return;
            }
            this.selectedSamples.add(analysisName);
        }
        window.APP_LOGGER.debug(`Selected samples (${this.selectedSamples.size}): ${Array.from(this.selectedSamples).join(', ')}`);
        this.updateComparisonView(); 
    }


    updateComparisonView() {
         const selectedAnalyses = this.allAnalyses.filter(a => a && this.selectedSamples.has(a.name));

         const countDisplay = document.getElementById('selectedCountDisplay'); 
         if (countDisplay) {
              countDisplay.textContent = LanguageManager.t('comparison.selected', { count: selectedAnalyses.length, max: this.maxSelectedSamples });
         }

        if (selectedAnalyses.length === 0) { 
            this.clearComparison();
             const tbody = document.querySelector('#comparisonTable tbody');
             if(tbody) {
                  tbody.innerHTML = `<tr><td colspan="6" data-i18n="comparison.selectMoreSamples" class="empty-state-cell"></td></tr>`;
                  LanguageManager.applyTranslations(); 
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
        
        const validAnalyses = analyses.filter(a => a && (a.concentration !== null || a.pfas !== null));
        if (validAnalyses.length === 0) {
             // this.clearChart('comparisonChart'); // Asegúrate que clearChart exista
             return;
        }


        const trace1 = {
            x: validAnalyses.map(a => a.filename || a.name),
            y: validAnalyses.map(a => a.concentration ?? 0), 
            type: 'bar', name: LanguageManager.t('results.concentration'), marker: { color: '#3498db' }, yaxis: 'y'
        };
        const trace2 = {
            x: validAnalyses.map(a => a.filename || a.name),
            y: validAnalyses.map(a => a.pfas ?? 0), 
            type: 'bar', name: LanguageManager.t('results.pifas'), marker: { color: '#e74c3c' }, yaxis: 'y2'
        };

        const layout = {
            title: LanguageManager.t('comparison.chartTitle') || 'Comparación de Muestras',
            barmode: 'group',
            yaxis: { title: LanguageManager.t('results.concentration') + ' (mM)', side: 'left' },
            yaxis2: { title: 'PFAS (%)', overlaying: 'y', side: 'right' },
            hovermode: 'x unified', showlegend: true,
             legend: { orientation: 'h', y: -0.2, yanchor: 'top' }, 
             margin: { l: 50, r: 50, b: 100, t: 50 } 
        };
        const config = { responsive: true, displayModeBar: true, displaylogo: false, locale: LanguageManager.currentLang };

        Plotly.newPlot('comparisonChart', [trace1, trace2], layout, config)
            .then(() => { this.charts.comparison = chartDiv; window.APP_LOGGER.debug('Comparison chart rendered'); })
            .catch(error => { window.APP_LOGGER.error('Error rendering comparison chart:', error); });
    }

    renderComparisonTable(analyses) {
        const table = document.getElementById('comparisonTable');
        const thead = table.querySelector('thead');
        const tbody = table.querySelector('tbody');

        if (!thead || !tbody) {
            window.APP_LOGGER.error("Comparison table thead or tbody not found!");
            return;
        }

        thead.innerHTML = '';
        tbody.innerHTML = '';

        if (!analyses || analyses.length === 0) { 
             tbody.innerHTML = `<tr><td colspan="6" data-i18n="comparison.selectSamples" class="empty-state-cell"></td></tr>`;
             LanguageManager.applyTranslationsToElement(tbody);
            return;
        }

        let headerHtml = '<tr>';
        headerHtml += `<th data-i18n="results.parameter"></th>`; 
        analyses.forEach(a => {
            const displayName = this.escapeHtml(a.filename || a.name || 'Muestra');
            let date = '--';
             try { date = a.created ? new Date(a.created).toLocaleDateString(LanguageManager.currentLang) : '--'; } catch(e){}
            headerHtml += `<th>${displayName}<br><small>${date}</small></th>`;
        });
        headerHtml += '</tr>';
        thead.innerHTML = headerHtml;

        const parameters = [
            { key: 'fluor', labelKey: 'results.fluor', unit: '%', decimals: 2 },
            { key: 'pfas', labelKey: 'results.pifas', unit: '%', decimals: 2 },
            { key: 'concentration', labelKey: 'results.concentration', unit: 'mM', decimals: 4 },
            { key: 'quality', labelKey: 'results.quality', unit: '/10', decimals: 1 }
        ];

        parameters.forEach(param => {
            let rowHtml = '<tr>';
            rowHtml += `<td data-i18n="${param.labelKey}"></td>`; 

            analyses.forEach(a => {
                let value = '--';
                const rawValue = a[param.key];
                if (rawValue !== null && rawValue !== undefined) {
                    value = UIManager.formatNumber(rawValue, param.decimals);
                    if (param.key === 'quality') {
                        value += '/10'; 
                    }
                }
                 const qualityClass = (param.key === 'quality' && a.quality !== null) ? this.getQualityClass(a.quality) : '';
                 rowHtml += `<td class="${qualityClass}">${value}</td>`;
            });
            rowHtml += '</tr>';
            tbody.innerHTML += rowHtml;
        });

        LanguageManager.applyTranslations(); 

        window.APP_LOGGER.debug('Comparison table rendered');
    }
 
    getQualityClass(quality) {
         if (quality === null || quality === undefined) return '';
         if (quality >= 8) return 'quality-excellent';
         if (quality >= 6) return 'quality-good';
         if (quality >= 4) return 'quality-regular';
         return 'quality-low';
    }


    clearComparison() {
        const chartDiv = document.getElementById('comparisonChart');
        if (chartDiv) {
            Plotly.purge('comparisonChart'); 
        }

        const table = document.getElementById('comparisonTable');
        const thead = table ? table.querySelector('thead') : null;
        const tbody = table ? table.querySelector('tbody') : null;

         if (thead) {
              thead.innerHTML = `
                   <tr>
                        <th data-i18n="results.parameter"></th>
                   </tr>
              `;
         }

        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="${this.maxSelectedSamples + 1}" class="empty-state-cell">
                        <i class="fas fa-mouse-pointer"></i>
                        <p data-i18n="comparison.selectSamples"></p>
                    </td>
                </tr>
            `;
        }

        const exportBtn = document.getElementById('exportComparisonBtn');
        if (exportBtn) {
            exportBtn.disabled = true; 
        }

        document.querySelectorAll('.sample-select-btn.selected').forEach(btn => {
             btn.classList.remove('selected');
        });

        this.selectedSamples.clear(); 
        
         const countDisplay = document.getElementById('selectedCountDisplay');
         if (countDisplay) {
             countDisplay.textContent = LanguageManager.t('comparison.selected', { count: 0, max: this.maxSelectedSamples });
         }

        if (table) LanguageManager.applyTranslations(); 

        window.APP_LOGGER.debug('Comparison view cleared.');
    }


    async exportComparison() {
        if (this.selectedSamples.size === 0) {
            if (typeof UIManager !== 'undefined') {
                UIManager.showNotification(
                    LanguageManager.t('comparison.noSamplesSelected'), 'warning'
                );
            }
            return;
        }

        const format = await this.showFormatSelector();
        if (!format) return; 

        const exportBtn = document.getElementById('exportComparisonBtn');
        if(exportBtn && typeof UIManager !== 'undefined') 
            UIManager.updateButtonState(exportBtn, 'loading');

        try {
            const selectedAnalyses = this.allAnalyses.filter(a => this.selectedSamples.has(a.name));
            
            const payload = {
                type: 'comparison',
                format: format, 
                samples: selectedAnalyses,
                count: selectedAnalyses.length
            };
            
            await APIClient.exportReport(payload);
            
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

    
    async exportDashboardData() {
        window.APP_LOGGER.debug('Exporting dashboard data...');
        
        if (!this.statsCache || !this.allAnalyses || this.allAnalyses.length === 0) {
            UIManager.showNotification('No hay datos de dashboard para exportar', 'warning');
            return;
        }

        const exportBtn = document.getElementById('exportDashboardBtn');
        if(exportBtn) UIManager.updateButtonState(exportBtn, 'loading');

        try {
            const stats = this.statsCache;
            let csvContent = "data:text/csv;charset=utf-8,";
            
            csvContent += "Metrica,Valor\n";
            csvContent += `Total Analisis,${stats.totalAnalyses}\n`;
            csvContent += `Concentracion Promedio (mM),${stats.avgConcentration}\n`;
            csvContent += `PFAS Promedio (%),${stats.avgPfas}\n`;
            csvContent += `Fluor Promedio (%),${stats.avgFluor}\n`;
            csvContent += `Calidad Promedio,${stats.avgQuality}\n`;
            csvContent += `Fuera de Limites,${stats.outOfLimits}\n`;
            csvContent += `Analisis (Ultima Semana),${stats.lastWeek}\n`;
            csvContent += `Analisis (Ultimo Mes),${stats.lastMonth}\n`;
            csvContent += `Muestras Alta Calidad,${stats.highQualitySamples}\n`;
            csvContent += `SNR Promedio,${stats.avgSNR}\n`;
            
            csvContent += "\nAnalisis (Todos)\n";
            
            const allAnalyses = [...this.allAnalyses]
                .filter(a => a && !a.error && a.created)
                .sort((a, b) => new Date(b.created) - new Date(a.created));

            csvContent += "Muestra,Fecha,Fluor (%),PFAS (%),Concentracion (mM),Calidad\n";

            allAnalyses.forEach(analysis => {
                const date = analysis.created ? new Date(analysis.created).toISOString().split('T')[0] : '--';
                const fileName = this.escapeCsv(analysis.filename || analysis.name);
                const fluor = UIManager.formatNumber(analysis.fluor, 2);
                const pfas = UIManager.formatNumber(analysis.pfas, 2);
                const concentration = UIManager.formatNumber(analysis.concentration, 4);
                const quality = UIManager.formatNumber(analysis.quality, 1);
                
                csvContent += `${fileName},${date},${fluor},${pfas},${concentration},${quality}\n`;
            });

            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", `dashboard_export_${new Date().toISOString().split('T')[0]}.csv`);
            document.body.appendChild(link); 
            link.click();
            document.body.removeChild(link);

            UIManager.showNotification('Datos del dashboard exportados como CSV', 'success');
            if(exportBtn) UIManager.updateButtonState(exportBtn, 'success');

        } catch (error) {
            window.APP_LOGGER.error('Dashboard export failed:', error);
            UIManager.showNotification('Error al exportar datos del dashboard', 'error');
            if(exportBtn) UIManager.updateButtonState(exportBtn, 'error');
        }
    }

    escapeCsv(text) {
        if (text === null || text === undefined) return '';
        let str = String(text);
        if (str.includes(',') || str.includes('"') || str.includes('\n')) {
            return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
    }


    // ========================================================================
    // FILTROS DASHBOARD
    // ========================================================================

    filterDashboardData() {
        const filter = document.getElementById('dashboardDateFilter')?.value || 'all';
        const originalAnalyses = this.allAnalyses; 

        try {
            if (filter === 'all') {
                this.calculateStats(); 
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
                
                this.allAnalyses = filteredAnalyses;
                this.calculateStats(); 
                
                this.allAnalyses = originalAnalyses; 
                
                 this.renderStatsCards(); 
                 this.renderTrendChart(); 
                 this.renderDistributionChart(); 
                 this.renderRecentAnalysesTable(); 

            } else {
                 this.allAnalyses = originalAnalyses;
                 this.calculateStats();
                 this.renderDashboard();
            }
        } finally {
             this.allAnalyses = originalAnalyses;
        }
    }

    // ========================================================================
    // ### FUNCIÓN NUEVA ###
    // ========================================================================

    /**
     * Actualiza el texto de los gráficos del dashboard cuando el idioma cambia.
     */
    refreshTranslations() {
        window.APP_LOGGER.debug('Refreshing dashboard chart translations...');
        
        // --- 1. Actualizar Gráfico de Tendencia ---
        if (this.charts.trend) {
            const trendLayoutUpdate = {
                title: LanguageManager.t('dashboard.trendTitle'),
                'xaxis.title': LanguageManager.t('dashboard.date'),
                'yaxis.title': LanguageManager.t('results.concentration') + ' (mM)',
                'yaxis2.title': LanguageManager.t('dashboard.pfasAxis'),
                'yaxis3.title': LanguageManager.t('results.quality')
            };
            const trendDataUpdate = {
                name: [
                    LanguageManager.t('results.concentration'),
                    LanguageManager.t('results.pifas'),
                    LanguageManager.t('results.quality')
                ]
            };
            Plotly.relayout(this.charts.trend, trendLayoutUpdate);
            Plotly.restyle(this.charts.trend, trendDataUpdate, [0, 1, 2]);
        }

        // --- 2. Actualizar Gráfico de Distribución ---
        if (this.charts.distribution) {
            const distLayoutUpdate = {
                title: LanguageManager.t('dashboard.distributionTitle')
            };
            
            const qualityKeys = ['Excelente (>=8)', 'Buena (6-8)', 'Regular (4-6)', 'Baja (<4)'];
            const labelTranslations = {
                'Excelente (>=8)': LanguageManager.t('dashboard.qualityLabels.excellent'),
                'Buena (6-8)': LanguageManager.t('dashboard.qualityLabels.good'),
                'Regular (4-6)': LanguageManager.t('dashboard.qualityLabels.regular'),
                'Baja (<4)': LanguageManager.t('dashboard.qualityLabels.low')
            };
            const translatedLabels = qualityKeys.map(key => labelTranslations[key] || key);

            const distDataUpdate = {
                labels: [translatedLabels] 
            };
            
            Plotly.relayout(this.charts.distribution, distLayoutUpdate);
            Plotly.restyle(this.charts.distribution, distDataUpdate, [0]);
        }
    }

} // <-- Fin de la clase DashboardManager

// Crear instancia global
window.dashboardManager = new DashboardManager();

