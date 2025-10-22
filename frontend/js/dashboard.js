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
            UIManager.showNotification('Error al cargar el dashboard', 'error');
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
            throw error;
        }
    }

    async refreshDashboard() {
        const refreshBtn = document.getElementById('refreshDashboardBtn');
        if (refreshBtn) {
            UIManager.updateButtonState(refreshBtn, 'loading');
        }

        try {
            await this.loadDashboardData();
            UIManager.showNotification(
                LanguageManager.t('dashboard.refreshSuccess'),
                'success'
            );
        } catch (error) {
            UIManager.showNotification(
                LanguageManager.t('dashboard.refreshError'),
                'error'
            );
        } finally {
            if (refreshBtn) {
                UIManager.updateButtonState(refreshBtn, 'default');
            }
        }
    }

    // ========================================================================
    // CÁLCULO DE ESTADÍSTICAS
    // ========================================================================

    calculateStats() {
        if (this.allAnalyses.length === 0) {
            this.statsCache = {
                totalAnalyses: 0,
                avgConcentration: 0,
                avgPfas: 0,
                avgFluor: 0,
                outOfLimits: 0,
                lastWeek: 0,
                lastMonth: 0,
                avgQuality: 0,
                // 🆕 NUEVAS MÉTRICAS
                avgSNR: 0,
                highQualitySamples: 0
            };
            return;
        }

        const now = new Date();
        const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        const oneMonthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

        // Calcular totales y promedios
        let totalConcentration = 0;
        let totalPfas = 0;
        let totalFluor = 0;
        let totalQuality = 0;
        let totalSNR = 0; // 🆕
        let snrCount = 0; // 🆕
        let outOfLimits = 0;
        let lastWeek = 0;
        let lastMonth = 0;
        let highQualitySamples = 0; // 🆕 calidad >= 8

        this.allAnalyses.forEach(analysis => {
            const concentration = analysis.concentration || 0;
            const pfas = analysis.pfas || 0;
            const fluor = analysis.fluor || 0;
            const quality = analysis.quality || 0;
            const created = new Date(analysis.created);

            totalConcentration += concentration;
            totalPfas += pfas;
            totalFluor += fluor;
            totalQuality += quality;

            // 🆕 SNR promedio (si existe en los datos)
            if (analysis.snr) {
                totalSNR += analysis.snr;
                snrCount++;
            }

            // 🆕 Contar muestras de alta calidad
            if (quality >= 8) {
                highQualitySamples++;
            }

            // Contadores temporales
            if (created >= oneWeekAgo) lastWeek++;
            if (created >= oneMonthAgo) lastMonth++;

            // Muestras fuera de límites (ejemplo: concentración > 1.0 mM)
            if (concentration > 1.0) outOfLimits++;
        });

        const count = this.allAnalyses.length;

        this.statsCache = {
            totalAnalyses: count,
            avgConcentration: (totalConcentration / count).toFixed(4),
            avgPfas: (totalPfas / count).toFixed(2),
            avgFluor: (totalFluor / count).toFixed(2),
            outOfLimits: outOfLimits,
            lastWeek: lastWeek,
            lastMonth: lastMonth,
            avgQuality: (totalQuality / count).toFixed(1),
            // 🆕 NUEVAS MÉTRICAS
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
        const stats = this.statsCache;

        // Total de análisis
        const totalEl = document.getElementById('dashTotalAnalyses');
        if (totalEl) totalEl.textContent = stats.totalAnalyses;

        // Concentración promedio
        const avgConcEl = document.getElementById('dashAvgConcentration');
        if (avgConcEl) avgConcEl.textContent = `${stats.avgConcentration} mM`;

        // Fuera de límites
        const outLimitsEl = document.getElementById('dashOutOfLimits');
        if (outLimitsEl) outLimitsEl.textContent = stats.outOfLimits;

        // Esta semana
        const weekEl = document.getElementById('dashLastWeek');
        if (weekEl) weekEl.textContent = stats.lastWeek;

        // Calidad promedio
        const qualityEl = document.getElementById('dashAvgQuality');
        if (qualityEl) qualityEl.textContent = `${stats.avgQuality}/10`;

        // PFAS promedio
        const pfasEl = document.getElementById('dashAvgPfas');
        if (pfasEl) pfasEl.textContent = `${stats.avgPfas}%`;

        // 🆕 SNR promedio (si existe el elemento)
        const snrEl = document.getElementById('dashAvgSNR');
        if (snrEl) snrEl.textContent = stats.avgSNR;

        // 🆕 Muestras de alta calidad (si existe el elemento)
        const highQualityEl = document.getElementById('dashHighQuality');
        if (highQualityEl) highQualityEl.textContent = stats.highQualitySamples;
    }

    renderTrendChart() {
        if (this.allAnalyses.length === 0) {
            this.clearChart('trendChart');
            return;
        }

        // Preparar datos de tendencia temporal
        const sortedAnalyses = [...this.allAnalyses].sort((a, b) => {
            return new Date(a.created) - new Date(b.created);
        });

        const dates = sortedAnalyses.map(a => {
            return new Date(a.created).toLocaleDateString(LanguageManager.currentLang);
        });

        const concentrations = sortedAnalyses.map(a => a.concentration || 0);
        const pfasValues = sortedAnalyses.map(a => a.pfas || 0);
        const qualityValues = sortedAnalyses.map(a => a.quality || 0);

        const trace1 = {
            x: dates,
            y: concentrations,
            type: 'scatter',
            mode: 'lines+markers',
            name: LanguageManager.t('results.concentration'),
            line: { color: '#3498db', width: 2 },
            marker: { size: 6 }
        };

        const trace2 = {
            x: dates,
            y: pfasValues,
            type: 'scatter',
            mode: 'lines+markers',
            name: LanguageManager.t('results.pifas'),
            line: { color: '#e74c3c', width: 2 },
            marker: { size: 6 },
            yaxis: 'y2'
        };

        const trace3 = {
            x: dates,
            y: qualityValues,
            type: 'scatter',
            mode: 'lines+markers',
            name: LanguageManager.t('results.quality'),
            line: { color: '#2ecc71', width: 2 },
            marker: { size: 6 },
            yaxis: 'y3'
        };

        const layout = {
            title: LanguageManager.t('dashboard.trendTitle') || 'Tendencias Temporales',
            xaxis: { title: LanguageManager.t('dashboard.date') || 'Fecha' },
            yaxis: {
                title: LanguageManager.t('results.concentration') + ' (mM)',
                side: 'left'
            },
            yaxis2: {
                title: 'PFAS (%)',
                overlaying: 'y',
                side: 'right'
            },
            yaxis3: {
                title: LanguageManager.t('results.quality'),
                overlaying: 'y',
                side: 'right',
                position: 0.95
            },
            hovermode: 'x unified',
            showlegend: true,
            legend: { orientation: 'h', y: -0.2 }
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            locale: LanguageManager.currentLang
        };

        const chartDiv = document.getElementById('trendChart');
        if (chartDiv) {
            Plotly.newPlot('trendChart', [trace1, trace2, trace3], layout, config)
                .then(() => {
                    this.charts.trend = chartDiv;
                    window.APP_LOGGER.debug('Trend chart rendered');
                })
                .catch(error => {
                    window.APP_LOGGER.error('Error rendering trend chart:', error);
                });
        }
    }

    renderDistributionChart() {
        if (this.allAnalyses.length === 0) {
            this.clearChart('distributionChart');
            return;
        }

        // Distribución de calidad
        const qualityDistribution = {
            'Excelente (8-10)': 0,
            'Buena (6-8)': 0,
            'Regular (4-6)': 0,
            'Baja (<4)': 0
        };

        this.allAnalyses.forEach(a => {
            const quality = a.quality || 0;
            if (quality >= 8) qualityDistribution['Excelente (8-10)']++;
            else if (quality >= 6) qualityDistribution['Buena (6-8)']++;
            else if (quality >= 4) qualityDistribution['Regular (4-6)']++;
            else qualityDistribution['Baja (<4)']++;
        });

        const trace = {
            labels: Object.keys(qualityDistribution),
            values: Object.values(qualityDistribution),
            type: 'pie',
            marker: {
                colors: ['#2ecc71', '#3498db', '#f39c12', '#e74c3c']
            },
            textinfo: 'label+percent',
            hoverinfo: 'label+value+percent'
        };

        const layout = {
            title: LanguageManager.t('dashboard.qualityDistribution') || 'Distribución de Calidad',
            showlegend: true,
            height: 400
        };

        const config = {
            responsive: true,
            displayModeBar: false,
            locale: LanguageManager.currentLang
        };

        const chartDiv = document.getElementById('distributionChart');
        if (chartDiv) {
            Plotly.newPlot('distributionChart', [trace], layout, config)
                .then(() => {
                    this.charts.distribution = chartDiv;
                    window.APP_LOGGER.debug('Distribution chart rendered');
                })
                .catch(error => {
                    window.APP_LOGGER.error('Error rendering distribution chart:', error);
                });
        }
    }

    renderRecentAnalysesTable() {
        const tbody = document.querySelector('#recentAnalysesTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        // Ordenar por fecha (más reciente primero) y tomar los últimos 10
        const recentAnalyses = [...this.allAnalyses]
            .sort((a, b) => new Date(b.created) - new Date(a.created))
            .slice(0, 10);

        if (recentAnalyses.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 2rem; color: #7f8c8d;">
                        ${LanguageManager.t('dashboard.noData') || 'No hay datos disponibles'}
                    </td>
                </tr>
            `;
            return;
        }

        recentAnalyses.forEach((analysis, index) => {
            const row = document.createElement('tr');
            
            const date = new Date(analysis.created).toLocaleString(LanguageManager.currentLang);
            const fluor = analysis.fluor != null ? analysis.fluor.toFixed(2) + '%' : '--';
            const pfas = analysis.pfas != null ? analysis.pfas.toFixed(2) + '%' : '--';
            const concentration = analysis.concentration != null ? analysis.concentration.toFixed(4) + ' mM' : '--';
            const quality = analysis.quality != null ? analysis.quality.toFixed(1) : '--';
            
            let qualityClass = 'quality-low';
            if (analysis.quality >= 8) qualityClass = 'quality-excellent';
            else if (analysis.quality >= 6) qualityClass = 'quality-good';
            else if (analysis.quality >= 4) qualityClass = 'quality-regular';

            row.innerHTML = `
                <td>${index + 1}</td>
                <td><strong>${analysis.filename || analysis.name}</strong></td>
                <td>${date}</td>
                <td>${fluor}</td>
                <td>${pfas}</td>
                <td>${concentration}</td>
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
            
            // Limpiar selección previa
            this.selectedSamples.clear();
            
            // Cargar análisis disponibles
            await this.loadComparisonData();
            
            // Renderizar selector de muestras
            this.renderSampleSelector();
            
            // Limpiar comparación
            this.clearComparison();
            
            window.APP_LOGGER.info('Comparison tab initialized');
        } catch (error) {
            window.APP_LOGGER.error('Failed to initialize Comparison:', error);
            UIManager.showNotification('Error al cargar la comparación', 'error');
        }
    }

    async loadComparisonData() {
        try {
            // Cargar todos los análisis desde el backend
            const data = await APIClient.getAnalysisList();
            this.allAnalyses = data.analyses || [];
            
            window.APP_LOGGER.debug(`Comparison data loaded: ${this.allAnalyses.length} analyses`);
        } catch (error) {
            window.APP_LOGGER.error('Failed to load comparison data:', error);
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
        
        if (this.allAnalyses.length === 0) {
            container.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-light);">
                    <i class="fas fa-folder-open" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                    <p data-i18n="comparison.noSamples">No hay muestras disponibles</p>
                    <p style="font-size: 0.9rem; margin-top: 0.5rem;">
                        Analiza algunas muestras primero para poder compararlas
                    </p>
                </div>
            `;
            LanguageManager.applyTranslations();
            return;
        }
        
        // Crear botones de selección para cada muestra
        this.allAnalyses.forEach(analysis => {
            const button = document.createElement('button');
            button.className = 'sample-select-btn';
            button.dataset.analysisName = analysis.name;
            
            const displayName = analysis.filename || analysis.name;
            const date = new Date(analysis.created).toLocaleDateString(LanguageManager.currentLang);
            
            button.innerHTML = `
                <div class="sample-btn-content">
                    <div class="sample-btn-name">${this.escapeHtml(displayName)}</div>
                    <div class="sample-btn-date">${date}</div>
                </div>
                <i class="fas fa-check-circle sample-btn-check"></i>
            `;
            
            // Event listener para selección
            button.addEventListener('click', () => {
                this.toggleSampleSelection(analysis.name);
                this.updateSampleButton(button, this.selectedSamples.has(analysis.name));
            });
            
            container.appendChild(button);
        });
        
        window.APP_LOGGER.debug(`Rendered ${this.allAnalyses.length} sample buttons`);
    }

    updateSampleButton(button, isSelected) {
        if (isSelected) {
            button.classList.add('selected');
        } else {
            button.classList.remove('selected');
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    toggleSampleSelection(analysisName) {
        if (this.selectedSamples.has(analysisName)) {
            this.selectedSamples.delete(analysisName);
        } else {
            if (this.selectedSamples.size >= this.maxSelectedSamples) {
                UIManager.showNotification(
                    LanguageManager.t('comparison.maxSamples', { max: this.maxSelectedSamples }) || 
                    `Máximo ${this.maxSelectedSamples} muestras`,
                    'warning'
                );
                return;
            }
            this.selectedSamples.add(analysisName);
        }
        
        window.APP_LOGGER.debug(`Selected samples: ${Array.from(this.selectedSamples).join(', ')}`);
        
        // Actualizar vista de comparación
        this.updateComparisonView();
    }

    // ========================================================================
    // COMPARACIÓN DE MUESTRAS
    // ========================================================================

    updateComparisonView() {
        const selectedAnalyses = this.allAnalyses.filter(a => 
            this.selectedSamples.has(a.name)
        );

        if (selectedAnalyses.length < 2) {
            this.clearComparison();
            return;
        }

        this.renderComparisonChart(selectedAnalyses);
        this.renderComparisonTable(selectedAnalyses);

        const exportBtn = document.getElementById('exportComparisonBtn');
        if (exportBtn) {
            exportBtn.disabled = false;
        }
    }

    clearChart(chartId) {
        const chartDiv = document.getElementById(chartId);
        if (chartDiv) {
            Plotly.purge(chartId);
        }
    }

    // ========================================================================
    // COMPARACIÓN DE MUESTRAS
    // ========================================================================

    toggleSampleSelection(analysisName) {
        if (this.selectedSamples.has(analysisName)) {
            this.selectedSamples.delete(analysisName);
        } else {
            if (this.selectedSamples.size >= this.maxSelectedSamples) {
                UIManager.showNotification(
                    LanguageManager.t('comparison.maxSamplesReached') || `Máximo ${this.maxSelectedSamples} muestras`,
                    'warning'
                );
                return;
            }
            this.selectedSamples.add(analysisName);
        }

        this.updateComparisonView();
    }

    updateComparisonView() {
        const selectedAnalyses = this.allAnalyses.filter(a => 
            this.selectedSamples.has(a.name)
        );

        if (selectedAnalyses.length < 2) {
            this.clearComparison();
            return;
        }

        this.renderComparisonChart(selectedAnalyses);
        this.renderComparisonTable(selectedAnalyses);

        const exportBtn = document.getElementById('exportComparisonBtn');
        if (exportBtn) {
            exportBtn.disabled = false;
        }
    }

    renderComparisonChart(analyses) {
        const chartDiv = document.getElementById('comparisonChart');
        if (!chartDiv) return;

        // Trace para concentraciones
        const trace1 = {
            x: analyses.map(a => a.filename || a.name),
            y: analyses.map(a => a.concentration || 0),
            type: 'bar',
            name: LanguageManager.t('results.concentration'),
            marker: { color: '#3498db' },
            yaxis: 'y'
        };

        // Trace para PFAS
        const trace2 = {
            x: analyses.map(a => a.filename || a.name),
            y: analyses.map(a => a.pfas || 0),
            type: 'bar',
            name: LanguageManager.t('results.pifas'),
            marker: { color: '#e74c3c' },
            yaxis: 'y2'
        };

        const layout = {
            title: LanguageManager.t('comparison.chartTitle') || 'Comparación de Muestras',
            barmode: 'group',
            yaxis: {
                title: LanguageManager.t('results.concentration') + ' (mM)',
                side: 'left'
            },
            yaxis2: {
                title: 'PFAS (%)',
                overlaying: 'y',
                side: 'right'
            },
            hovermode: 'x unified',
            showlegend: true
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            locale: LanguageManager.currentLang
        };

        Plotly.newPlot('comparisonChart', [trace1, trace2], layout, config)
            .then(() => {
                this.charts.comparison = chartDiv;
                window.APP_LOGGER.debug('Comparison chart rendered');
            })
            .catch(error => {
                window.APP_LOGGER.error('Error rendering comparison chart:', error);
            });
    }

    renderComparisonTable(analyses) {
        const tbody = document.querySelector('#comparisonTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        // Fila 1: Nombres
        const nameRow = document.createElement('tr');
        nameRow.innerHTML = `<th>${LanguageManager.t('comparison.sample')}</th>`;
        analyses.forEach(a => {
            const displayName = a.filename || a.name;
            nameRow.innerHTML += `<td><strong>${displayName}</strong></td>`;
        });
        tbody.appendChild(nameRow);

        // Fila 2: Fecha
        const dateRow = document.createElement('tr');
        dateRow.innerHTML = `<th>${LanguageManager.t('comparison.date')}</th>`;
        analyses.forEach(a => {
            const date = new Date(a.created).toLocaleDateString(LanguageManager.currentLang);
            dateRow.innerHTML += `<td>${date}</td>`;
        });
        tbody.appendChild(dateRow);

        // Fila 3: Flúor
        const fluorRow = document.createElement('tr');
        fluorRow.innerHTML = `<th>${LanguageManager.t('results.fluor')} (%)</th>`;
        analyses.forEach(a => {
            const fluor = a.fluor != null ? a.fluor.toFixed(2) : '--';
            fluorRow.innerHTML += `<td>${fluor}</td>`;
        });
        tbody.appendChild(fluorRow);

        // Fila 4: PFAS
        const pfasRow = document.createElement('tr');
        pfasRow.innerHTML = `<th>${LanguageManager.t('results.pifas')} (%)</th>`;
        analyses.forEach(a => {
            const pfas = a.pfas != null ? a.pfas.toFixed(2) : '--';
            pfasRow.innerHTML += `<td>${pfas}</td>`;
        });
        tbody.appendChild(pfasRow);

        // Fila 5: Concentración
        const concRow = document.createElement('tr');
        concRow.innerHTML = `<th>${LanguageManager.t('results.concentration')} (mM)</th>`;
        analyses.forEach(a => {
            const conc = a.concentration != null ? a.concentration.toFixed(4) : '--';
            concRow.innerHTML += `<td>${conc}</td>`;
        });
        tbody.appendChild(concRow);

        // Fila 6: Calidad
        const qualityRow = document.createElement('tr');
        qualityRow.innerHTML = `<th>${LanguageManager.t('results.quality')}</th>`;
        analyses.forEach(a => {
            const quality = a.quality != null ? a.quality.toFixed(1) : '--';
            let qualityClass = 'quality-low';
            if (a.quality >= 8) qualityClass = 'quality-excellent';
            else if (a.quality >= 6) qualityClass = 'quality-good';
            else if (a.quality >= 4) qualityClass = 'quality-regular';
            
            qualityRow.innerHTML += `
                <td><span class="quality-badge ${qualityClass}">${quality}/10</span></td>
            `;
        });
        tbody.appendChild(qualityRow);
    }

    clearComparison() {
        const chartDiv = document.getElementById('comparisonChart');
        if (chartDiv) {
            Plotly.purge('comparisonChart');
        }

        const tbody = document.querySelector('#comparisonTable tbody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 2rem;">
                        <i class="fas fa-mouse-pointer" style="font-size: 2rem; margin-bottom: 0.5rem; color: #7f8c8d;"></i>
                        <p>${LanguageManager.t('comparison.selectSamples')}</p>
                    </td>
                </tr>
            `;
        }

        const exportBtn = document.getElementById('exportComparisonBtn');
        if (exportBtn) {
            exportBtn.disabled = true;
        }
    }

    async exportComparison() {
        if (this.selectedSamples.size === 0) {
            UIManager.showNotification(
                LanguageManager.t('comparison.noSamplesSelected'),
                'warning'
            );
            return;
        }

        try {
            const selectedAnalyses = this.allAnalyses.filter(a => 
                this.selectedSamples.has(a.name)
            );

            // Crear CSV de comparación
            const csvContent = this.generateComparisonCSV(selectedAnalyses);

            // Descargar archivo
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            
            link.setAttribute('href', url);
            link.setAttribute('download', `comparison_${new Date().toISOString().split('T')[0]}.csv`);
            link.style.visibility = 'hidden';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            UIManager.showNotification(
                LanguageManager.t('comparison.exportSuccess'),
                'success'
            );

        } catch (error) {
            window.APP_LOGGER.error('Export comparison failed:', error);
            UIManager.showNotification(
                LanguageManager.t('comparison.exportError'),
                'error'
            );
        }
    }

    generateComparisonCSV(analyses) {
        const headers = [
            'Sample',
            'Date',
            'Fluorine (%)',
            'PFAS (%)',
            'Concentration (mM)',
            'Quality'
        ];

        const rows = analyses.map(a => {
            return [
                a.filename || a.name,
                new Date(a.created).toISOString().split('T')[0],
                (a.fluor || 0).toFixed(2),
                (a.pfas || 0).toFixed(2),
                (a.concentration || 0).toFixed(4),
                (a.quality || 0).toFixed(1)
            ].join(',');
        });

        return [headers.join(','), ...rows].join('\n');
    }

    // ========================================================================
    // FILTROS
    // ========================================================================

    filterDashboardData() {
        const filter = document.getElementById('dashboardDateFilter')?.value || 'all';
        
        if (filter === 'all') {
            this.renderDashboard();
            return;
        }

        // Implementar filtros de fecha
        const now = new Date();
        let startDate;

        switch(filter) {
            case 'today':
                startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                break;
            case 'week':
                startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                break;
            case 'month':
                startDate = new Date(now.getFullYear(), now.getMonth(), 1);
                break;
        }

        if (startDate) {
            const filteredAnalyses = this.allAnalyses.filter(a => {
                const created = new Date(a.created);
                return created >= startDate;
            });

            // Temporalmente guardar todos los análisis
            const allAnalysesBackup = this.allAnalyses;
            this.allAnalyses = filteredAnalyses;
            
            this.calculateStats();
            this.renderDashboard();

            // Restaurar
            this.allAnalyses = allAnalysesBackup;
        }
    }
}

// Crear instancia global
window.dashboardManager = new DashboardManager();