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

        this.dateFilter = {
            type: 'all', // 'all', 'today', 'week', 'month', 'custom'
            customFrom: null,
            customTo: null
        };
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

        // 🆕 Selector de filtro rápido
        const quickFilter = document.getElementById('dashboardQuickFilter');
        if (quickFilter) {
            quickFilter.addEventListener('change', (e) => this.handleQuickFilterChange(e.target.value));
        }

        // 🆕 Botón aplicar filtro personalizado
        const applyBtn = document.getElementById('applyDateFilter');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => this.applyCustomDateFilter());
        }

        // 🆕 Botón limpiar filtro
        const clearBtn = document.getElementById('clearDateFilter');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearCustomDateFilter());
        }

        // 🆕 Permitir aplicar con Enter en los inputs de fecha
        const dateInputs = document.querySelectorAll('#dateFrom, #dateTo');
        dateInputs.forEach(input => {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.applyCustomDateFilter();
                }
            });
        });
        
        // Filtros de fecha en dashboard
        const dateFilterDash = document.getElementById('dashboardDateFilter');
        if (dateFilterDash) {
            dateFilterDash.addEventListener('change', () => this.filterDashboardData());
        }
    }

    /**
     * 🆕 Maneja el cambio en el selector de filtro rápido
     */
    handleQuickFilterChange(value) {
        const customRange = document.getElementById('customDateRange');
        
        if (value === 'custom') {
            // Mostrar selector de rango personalizado
            customRange.style.display = 'flex';
            this.dateFilter.type = 'custom';
            
            // Establecer fechas por defecto si no hay ninguna
            const dateFrom = document.getElementById('dateFrom');
            const dateTo = document.getElementById('dateTo');
            
            if (!dateFrom.value) {
                // Por defecto: último mes
                const today = new Date();
                const monthAgo = new Date(today);
                monthAgo.setMonth(monthAgo.getMonth() - 1);
                
                dateFrom.value = this.formatDateForInput(monthAgo);
                dateTo.value = this.formatDateForInput(today);
            }
        } else {
            // Ocultar selector personalizado
            customRange.style.display = 'none';
            this.dateFilter.type = value;
            this.dateFilter.customFrom = null;
            this.dateFilter.customTo = null;
            
            // Aplicar filtro predefinido
            this.applyDateFilter();
        }
    }

    /**
     * 🆕 Aplica el filtro de fecha personalizado
     */
    applyCustomDateFilter() {
        const dateFromInput = document.getElementById('dateFrom');
        const dateToInput = document.getElementById('dateTo');
        
        if (!dateFromInput.value || !dateToInput.value) {
            UIManager.showNotification(
                LanguageManager.t('dashboard.invalidDateRange') || 'Por favor, selecciona ambas fechas',
                'warning'
            );
            return;
        }

        const dateFrom = new Date(dateFromInput.value);
        const dateTo = new Date(dateToInput.value);
        
        // Validar que la fecha inicial sea anterior a la final
        if (dateFrom > dateTo) {
            UIManager.showNotification(
                LanguageManager.t('dashboard.invalidDateRange') || 'La fecha inicial debe ser anterior a la final',
                'error'
            );
            return;
        }

        // Ajustar las fechas para incluir el día completo
        dateFrom.setHours(0, 0, 0, 0);
        dateTo.setHours(23, 59, 59, 999);

        // Guardar en el estado
        this.dateFilter.type = 'custom';
        this.dateFilter.customFrom = dateFrom;
        this.dateFilter.customTo = dateTo;

        // Aplicar filtro
        this.applyDateFilter();

        // Marcar inputs como activos
        dateFromInput.classList.add('active');
        dateToInput.classList.add('active');

        // Mostrar notificación
        const fromStr = this.formatDateForDisplay(dateFrom);
        const toStr = this.formatDateForDisplay(dateTo);
        UIManager.showNotification(
            LanguageManager.t('dashboard.dateRangeApplied', { from: fromStr, to: toStr }) ||
            `Filtro aplicado: ${fromStr} - ${toStr}`,
            'success'
        );

        window.APP_LOGGER.debug(`Custom date filter applied: ${dateFrom} to ${dateTo}`);
    }

    /**
     * 🆕 Limpia el filtro de fecha personalizado
     */
    clearCustomDateFilter() {
        // Limpiar inputs
        const dateFromInput = document.getElementById('dateFrom');
        const dateToInput = document.getElementById('dateTo');
        const quickFilter = document.getElementById('dashboardQuickFilter');
        
        if (dateFromInput) {
            dateFromInput.value = '';
            dateFromInput.classList.remove('active');
        }
        if (dateToInput) {
            dateToInput.value = '';
            dateToInput.classList.remove('active');
        }
        
        // Resetear a "Todos"
        if (quickFilter) quickFilter.value = 'all';
        
        // Ocultar selector personalizado
        const customRange = document.getElementById('customDateRange');
        if (customRange) customRange.style.display = 'none';

        // Resetear estado
        this.dateFilter.type = 'all';
        this.dateFilter.customFrom = null;
        this.dateFilter.customTo = null;

        // Aplicar filtro (mostrar todos)
        this.applyDateFilter();

        UIManager.showNotification(
            LanguageManager.t('dashboard.filterCleared') || 'Filtro eliminado',
            'info'
        );

        window.APP_LOGGER.debug('Date filter cleared');
    }

    /**
     * 🆕 Aplica el filtro de fecha actual a los datos
     */
    applyDateFilter() {
        if (!this.allAnalyses || this.allAnalyses.length === 0) {
            window.APP_LOGGER.warn('No data to filter');
            return;
        }

        // Guardar datos originales
        const originalAnalyses = [...this.allAnalyses];
        let filteredAnalyses = [...this.allAnalyses];

        try {
            // Aplicar filtro según el tipo
            switch (this.dateFilter.type) {
                case 'today':
                    filteredAnalyses = this.filterByToday(filteredAnalyses);
                    break;
                case 'week':
                    filteredAnalyses = this.filterByLastWeek(filteredAnalyses);
                    break;
                case 'month':
                    filteredAnalyses = this.filterByLastMonth(filteredAnalyses);
                    break;
                case 'custom':
                    if (this.dateFilter.customFrom && this.dateFilter.customTo) {
                        filteredAnalyses = this.filterByCustomRange(
                            filteredAnalyses,
                            this.dateFilter.customFrom,
                            this.dateFilter.customTo
                        );
                    }
                    break;
                case 'all':
                default:
                    // No filtrar, usar todos los datos
                    break;
            }

            // Verificar si hay datos después del filtro
            if (filteredAnalyses.length === 0) {
                UIManager.showNotification(
                    LanguageManager.t('dashboard.noDataInRange') || 'No hay datos en el rango seleccionado',
                    'warning'
                );
            }

            // Actualizar temporalmente allAnalyses con los datos filtrados
            this.allAnalyses = filteredAnalyses;
            
            // Recalcular estadísticas y re-renderizar
            this.calculateStats();
            this.renderDashboard();

            window.APP_LOGGER.debug(`Filtered ${originalAnalyses.length} -> ${filteredAnalyses.length} analyses`);

        } catch (error) {
            window.APP_LOGGER.error('Error applying date filter:', error);
            UIManager.showNotification('Error al aplicar el filtro de fechas', 'error');
        } finally {
            // Restaurar datos originales (los filtrados se usan solo para visualización)
            this.allAnalyses = originalAnalyses;
        }
    }

    /**
     * 🆕 Filtra análisis por hoy
     */
    filterByToday(analyses) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);

        return analyses.filter(a => {
            if (!a.created) return false;
            const created = new Date(a.created);
            return created >= today && created < tomorrow;
        });
    }

    /**
     * 🆕 Filtra análisis por última semana
     */
    filterByLastWeek(analyses) {
        const now = new Date();
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        weekAgo.setHours(0, 0, 0, 0);

        return analyses.filter(a => {
            if (!a.created) return false;
            const created = new Date(a.created);
            return created >= weekAgo;
        });
    }

    /**
     * 🆕 Filtra análisis por último mes
     */
    filterByLastMonth(analyses) {
        const now = new Date();
        const monthAgo = new Date(now);
        monthAgo.setMonth(monthAgo.getMonth() - 1);
        monthAgo.setHours(0, 0, 0, 0);

        return analyses.filter(a => {
            if (!a.created) return false;
            const created = new Date(a.created);
            return created >= monthAgo;
        });
    }

    /**
     * 🆕 Filtra análisis por rango personalizado
     */
    filterByCustomRange(analyses, fromDate, toDate) {
        return analyses.filter(a => {
            if (!a.created) return false;
            const created = new Date(a.created);
            return created >= fromDate && created <= toDate;
        });
    }

    /**
     * 🆕 Formatea fecha para input HTML5 (YYYY-MM-DD)
     */
    formatDateForInput(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    /**
     * 🆕 Formatea fecha para visualización
     */
    formatDateForDisplay(date) {
        return date.toLocaleDateString(LanguageManager.currentLang || 'es', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }


    // ========================================================================
    // CARGA DE DATOS
    // ========================================================================

    async loadDashboardData() {
        try {
            // Obtener todos los análisis del backend
            const data = await APIClient.getAnalysisList();
            this.allAnalyses = data.analyses || [];
            
            // 🆕 Aplicar filtro de fecha si existe
            if (this.dateFilter.type !== 'all') {
                this.applyDateFilter();
            } else {
                // Calcular estadísticas normalmente
                this.calculateStats();
                this.renderDashboard();
            }
            
            this.lastUpdate = new Date();
            window.APP_LOGGER.debug(`Dashboard data loaded: ${this.allAnalyses.length} analyses`);
            
        } catch (error) {
            window.APP_LOGGER.error('Failed to load dashboard data:', error);
            throw error;
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
            LanguageManager.applyTranslations(tbody);
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
            LanguageManager.applyTranslations(container);
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
             LanguageManager.applyTranslations(tbody);
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
            // 🆕 CAPTURAR EL GRÁFICO DE COMPARACIÓN
            let chartImage = null;
            try {
                const comparisonChart = document.getElementById('comparisonChart');
                if (comparisonChart && comparisonChart.data) {
                    chartImage = await Plotly.toImage(comparisonChart, {
                        format: 'png',
                        width: 800,
                        height: 500,
                        scale: 2
                    });
                    window.APP_LOGGER.debug('Comparison chart captured successfully');
                }
            } catch (error) {
                window.APP_LOGGER.error('Error capturing comparison chart:', error);
                // Continuar sin gráfico si hay error
            }
            
            // Obtener las muestras seleccionadas con todos sus datos
            const selectedAnalyses = this.allAnalyses.filter(a => this.selectedSamples.has(a.name));
            
            // Preparar datos completos para el reporte
            const samplesData = selectedAnalyses.map(analysis => ({
                filename: analysis.filename || analysis.name,
                name: analysis.name,
                date: analysis.created ? new Date(analysis.created).toLocaleDateString(LanguageManager.currentLang) : '--',
                fluor: analysis.fluor || 0,
                pfas: analysis.pfas || 0,
                concentration: analysis.concentration || 0,
                quality: analysis.quality || 0
            }));
            
            const payload = {
                type: 'comparison',
                format: format, 
                samples: samplesData,  // 🆕 Datos completos
                count: samplesData.length,
                chart_image: chartImage  // 🆕 Imagen del gráfico
            };
            
            window.APP_LOGGER.debug('Exporting comparison with chart:', {
                samples: samplesData.length,
                hasChart: !!chartImage
            });
            
            // Enviar al backend usando el método de APIClient
            await this.sendComparisonExport(payload);
            
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

    // 🆕 Método auxiliar para enviar la exportación
    async sendComparisonExport(payload) {
        const response = await fetch(`${APIClient.baseURL}/export`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Export failed');
        }
        
        // Descargar archivo
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `comparison_${new Date().toISOString().split('T')[0]}.${payload.format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
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

        // 🆕 Mostrar selector de formato
        const format = await this.showDashboardFormatSelector();
        if (!format) return; // Usuario canceló

        const exportBtn = document.getElementById('exportDashboardBtn');
        if(exportBtn) UIManager.updateButtonState(exportBtn, 'loading');

        try {
            if (format === 'csv') {
                // Exportación CSV existente (mantener como está)
                await this.exportDashboardCSV();
            } else {
                // 🆕 Exportación PDF/DOCX con gráficos
                await this.exportDashboardWithCharts(format);
            }

            UIManager.showNotification(`Dashboard exportado como ${format.toUpperCase()}`, 'success');
            if(exportBtn) UIManager.updateButtonState(exportBtn, 'success');

        } catch (error) {
            window.APP_LOGGER.error('Dashboard export failed:', error);
            UIManager.showNotification('Error al exportar datos del dashboard', 'error');
            if(exportBtn) UIManager.updateButtonState(exportBtn, 'error');
        }
    }

    // 🆕 Método para exportar CSV (código existente extraído)
    async exportDashboardCSV() {
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
    }

    // 🆕 Método para exportar con gráficos (PDF/DOCX)
    async exportDashboardWithCharts(format) {
        window.APP_LOGGER.debug(`Exporting dashboard as ${format} with charts...`);
        
        // 1. Capturar los gráficos
        const chartImages = {};
        
        try {
            // Capturar gráfico de tendencia
            const trendChart = document.getElementById('trendChart');
            if (trendChart && trendChart.data) {
                const trendImage = await Plotly.toImage(trendChart, {
                    format: 'png',
                    width: 800,
                    height: 500,
                    scale: 2
                });
                chartImages.trend = trendImage;
                window.APP_LOGGER.debug('Trend chart captured');
            }
            
            // Capturar gráfico de distribución
            const distributionChart = document.getElementById('distributionChart');
            if (distributionChart && distributionChart.data) {
                const distImage = await Plotly.toImage(distributionChart, {
                    format: 'png',
                    width: 800,
                    height: 500,
                    scale: 2
                });
                chartImages.distribution = distImage;
                window.APP_LOGGER.debug('Distribution chart captured');
            }
        } catch (error) {
            window.APP_LOGGER.error('Error capturing dashboard charts:', error);
            // Continuar sin gráficos si hay error
        }
        
        // 2. Preparar datos para el backend
        const exportData = {
            type: 'dashboard',
            format: format,
            stats: this.statsCache,
            chart_images: chartImages,
            recent_analyses: this.allAnalyses
                .filter(a => a && !a.error && a.created)
                .sort((a, b) => new Date(b.created) - new Date(a.created))
                .slice(0, 10) // Solo las 10 más recientes
        };
        
        // 3. Enviar al backend
        const response = await fetch(`${APIClient.baseURL}/export`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(exportData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Export failed');
        }
        
        // 4. Descargar archivo
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `dashboard_export_${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    // 🆕 Selector de formato para dashboard
    showDashboardFormatSelector() {
        return new Promise((resolve) => {
            const formats = [
                { value: 'pdf', icon: 'file-pdf', label: 'PDF', color: 'danger' },
                { value: 'docx', icon: 'file-word', label: 'Word', color: 'primary' },
                { value: 'csv', icon: 'file-csv', label: 'CSV', color: 'success' }
            ];
            
            const buttonsHTML = formats.map(f => 
                `<button class="btn btn-${f.color} format-selector-btn" data-format="${f.value}">
                    <i class="fas fa-${f.icon}"></i> ${f.label}
                </button>`
            ).join('');
            
            const content = `
                <div class="format-selector">
                    <p>Selecciona el formato de exportación del dashboard:</p>
                    <div class="format-buttons">${buttonsHTML}</div>
                </div>
            `;
            
            UIManager.showModal('Exportar Dashboard', content, [
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

        // 🆕 Actualizar traducciones de filtros
        const quickFilter = document.getElementById('dashboardQuickFilter');
        if (quickFilter) {
            Array.from(quickFilter.options).forEach(option => {
                const key = option.getAttribute('data-i18n');
                if (key) {
                    option.textContent = LanguageManager.t(key);
                }
            });
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

        // --- 3. Actualizar Textos ---
        const countDisplay = document.getElementById('selectedCountDisplay');
        if (countDisplay) {
            // Obtenemos el número actual de muestras seleccionadas
            const count = this.selectedSamples ? this.selectedSamples.size : 0;
            // Aplicamos la traducción con los parámetros correctos
            countDisplay.textContent = LanguageManager.t('comparison.selected', { 
                count: count, 
                max: this.maxSelectedSamples 
            });
        }
    }

    // ============================================================================
// EXPORTAR INDICADOR VISUAL DE FILTRO ACTIVO (Opcional)
// ============================================================================

    showDateRangeIndicator(fromDate, toDate) {
        // Buscar o crear contenedor para el indicador
        let indicator = document.getElementById('dateRangeIndicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'dateRangeIndicator';
            indicator.className = 'date-range-indicator';
            
            const dashboardHeader = document.querySelector('.dashboard-header');
            if (dashboardHeader) {
                dashboardHeader.appendChild(indicator);
            }
        }

        const fromStr = fromDate.toLocaleDateString();
        const toStr = toDate.toLocaleDateString();
        
        indicator.innerHTML = `
            <i class="fas fa-filter"></i>
            <span>Filtrado: ${fromStr} - ${toStr}</span>
        `;
        indicator.style.display = 'inline-flex';
    }

    /**
     * 🆕 Función auxiliar para ocultar indicador
     */
    hideDateRangeIndicator() {
        const indicator = document.getElementById('dateRangeIndicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    } // <-- Fin de la clase DashboardManager

// Crear instancia global
window.dashboardManager = new DashboardManager();

