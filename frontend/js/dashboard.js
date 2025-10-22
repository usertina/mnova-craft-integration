// ============================================================================
// DASHBOARD MANAGER - CraftRMN Pro
// Gestión completa de estadísticas y comparación de muestras
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
                avgQuality: 0
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
        let outOfLimits = 0;
        let lastWeek = 0;
        let lastMonth = 0;

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
            avgQuality: (totalQuality / count).toFixed(1)
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
            const date = new Date(a.created);
            return date.toLocaleDateString(LanguageManager.currentLang, {
                day: '2-digit',
                month: 'short'
            });
        });

        const concentrations = sortedAnalyses.map(a => a.concentration || 0);

        const trace = {
            x: dates,
            y: concentrations,
            type: 'scatter',
            mode: 'lines+markers',
            line: {
                color: '#3498db',
                width: 2
            },
            marker: {
                size: 6,
                color: '#3498db'
            },
            name: LanguageManager.t('dashboard.concentration'),
            hovertemplate: LanguageManager.t('dashboard.trendHover')
        };

        const layout = {
            title: {
                text: LanguageManager.t('dashboard.trendTitle'),
                font: { size: 16, color: '#2c3e50' }
            },
            xaxis: {
                title: LanguageManager.t('dashboard.date'),
                gridcolor: '#f0f0f0'
            },
            yaxis: {
                title: LanguageManager.t('dashboard.concentration') + ' (mM)',
                gridcolor: '#f0f0f0'
            },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            margin: { t: 60, r: 40, b: 60, l: 60 },
            showlegend: false,
            hovermode: 'closest'
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            locale: LanguageManager.currentLang
        };

        Plotly.newPlot('trendChart', [trace], layout, config)
            .then(() => {
                this.charts.trend = document.getElementById('trendChart');
                window.APP_LOGGER.debug('Trend chart rendered');
            })
            .catch(error => {
                window.APP_LOGGER.error('Error rendering trend chart:', error);
            });
    }

    renderDistributionChart() {
        if (this.allAnalyses.length === 0) {
            this.clearChart('distributionChart');
            return;
        }

        // Agrupar por rangos de calidad
        const qualityRanges = {
            'Excelente (8-10)': 0,
            'Buena (6-8)': 0,
            'Regular (4-6)': 0,
            'Baja (0-4)': 0
        };

        this.allAnalyses.forEach(analysis => {
            const quality = analysis.quality || 0;
            if (quality >= 8) qualityRanges['Excelente (8-10)']++;
            else if (quality >= 6) qualityRanges['Buena (6-8)']++;
            else if (quality >= 4) qualityRanges['Regular (4-6)']++;
            else qualityRanges['Baja (0-4)']++;
        });

        const labels = Object.keys(qualityRanges);
        const values = Object.values(qualityRanges);
        const colors = ['#27ae60', '#3498db', '#f39c12', '#e74c3c'];

        const trace = {
            labels: labels,
            values: values,
            type: 'pie',
            marker: {
                colors: colors
            },
            hovertemplate: '%{label}: %{value}<br>%{percent}<extra></extra>'
        };

        const layout = {
            title: {
                text: LanguageManager.t('dashboard.distributionTitle'),
                font: { size: 16, color: '#2c3e50' }
            },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            margin: { t: 60, r: 40, b: 40, l: 40 },
            showlegend: true,
            legend: {
                orientation: 'h',
                y: -0.2
            }
        };

        const config = {
            responsive: true,
            displayModeBar: false,
            locale: LanguageManager.currentLang
        };

        Plotly.newPlot('distributionChart', [trace], layout, config)
            .then(() => {
                this.charts.distribution = document.getElementById('distributionChart');
                window.APP_LOGGER.debug('Distribution chart rendered');
            })
            .catch(error => {
                window.APP_LOGGER.error('Error rendering distribution chart:', error);
            });
    }

    renderRecentAnalysesTable() {
        const tbody = document.querySelector('#recentAnalysesTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (this.allAnalyses.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 2rem; color: #7f8c8d;">
                        <i class="fas fa-inbox" style="font-size: 2rem; margin-bottom: 0.5rem;"></i>
                        <p>${LanguageManager.t('dashboard.noData')}</p>
                    </td>
                </tr>
            `;
            return;
        }

        // Mostrar últimos 10 análisis
        const recent = [...this.allAnalyses]
            .sort((a, b) => new Date(b.created) - new Date(a.created))
            .slice(0, 10);

        recent.forEach(analysis => {
            const row = document.createElement('tr');
            
            const displayName = analysis.filename || analysis.name;
            const date = new Date(analysis.created).toLocaleDateString(
                LanguageManager.currentLang
            );
            const fluor = analysis.fluor != null ? analysis.fluor.toFixed(2) : '--';
            const pfas = analysis.pfas != null ? analysis.pfas.toFixed(2) : '--';
            const quality = analysis.quality != null ? analysis.quality.toFixed(1) : '--';

            // Badge de calidad
            let qualityClass = 'quality-low';
            if (analysis.quality >= 8) qualityClass = 'quality-excellent';
            else if (analysis.quality >= 6) qualityClass = 'quality-good';
            else if (analysis.quality >= 4) qualityClass = 'quality-regular';

            row.innerHTML = `
                <td>
                    <i class="fas fa-file"></i> ${displayName}
                </td>
                <td>${date}</td>
                <td>${fluor}%</td>
                <td>${pfas}%</td>
                <td>
                    <span class="quality-badge ${qualityClass}">${quality}/10</span>
                </td>
            `;

            row.style.cursor = 'pointer';
            row.addEventListener('click', () => {
                window.rmnApp.loadAnalysisFromHistory(analysis.name);
            });

            tbody.appendChild(row);
        });
    }

    clearChart(chartId) {
        const chartElement = document.getElementById(chartId);
        if (chartElement) {
            Plotly.purge(chartId);
        }
    }

    // ========================================================================
    // COMPARACIÓN DE MUESTRAS
    // ========================================================================

    initComparison() {
        this.renderSampleSelector();
    }

    renderSampleSelector() {
        const container = document.getElementById('sampleSelectorContainer');
        if (!container) return;

        container.innerHTML = '';

        if (this.allAnalyses.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>${LanguageManager.t('comparison.noSamples')}</p>
                </div>
            `;
            return;
        }

        // Crear botones de selección
        this.allAnalyses.forEach(analysis => {
            const button = document.createElement('button');
            button.className = 'sample-select-btn';
            button.dataset.analysisId = analysis.name;
            
            const displayName = analysis.filename || analysis.name;
            const date = new Date(analysis.created).toLocaleDateString(
                LanguageManager.currentLang,
                { month: 'short', day: '2-digit' }
            );

            button.innerHTML = `
                <div class="sample-btn-content">
                    <div class="sample-btn-name">${displayName}</div>
                    <div class="sample-btn-date">${date}</div>
                </div>
                <i class="fas fa-check sample-btn-check"></i>
            `;

            if (this.selectedSamples.has(analysis.name)) {
                button.classList.add('selected');
            }

            button.addEventListener('click', () => this.toggleSampleSelection(analysis.name));

            container.appendChild(button);
        });
    }

    toggleSampleSelection(analysisId) {
        if (this.selectedSamples.has(analysisId)) {
            this.selectedSamples.delete(analysisId);
        } else {
            if (this.selectedSamples.size >= this.maxSelectedSamples) {
                UIManager.showNotification(
                    LanguageManager.t('comparison.maxSamples', { max: this.maxSelectedSamples }),
                    'warning'
                );
                return;
            }
            this.selectedSamples.add(analysisId);
        }

        this.updateSampleSelector();
        this.updateComparison();
    }

    updateSampleSelector() {
        const buttons = document.querySelectorAll('.sample-select-btn');
        buttons.forEach(btn => {
            const id = btn.dataset.analysisId;
            if (this.selectedSamples.has(id)) {
                btn.classList.add('selected');
            } else {
                btn.classList.remove('selected');
            }
        });
    }

    async updateComparison() {
        if (this.selectedSamples.size === 0) {
            this.clearComparison();
            return;
        }

        try {
            const selectedAnalyses = this.allAnalyses.filter(a => 
                this.selectedSamples.has(a.name)
            );

            this.renderComparisonChart(selectedAnalyses);
            this.renderComparisonTable(selectedAnalyses);

            // Mostrar botón de exportar
            const exportBtn = document.getElementById('exportComparisonBtn');
            if (exportBtn) {
                exportBtn.disabled = false;
            }

        } catch (error) {
            window.APP_LOGGER.error('Error updating comparison:', error);
            UIManager.showNotification(
                LanguageManager.t('comparison.error'),
                'error'
            );
        }
    }

    renderComparisonChart(analyses) {
        const chartDiv = document.getElementById('comparisonChart');
        if (!chartDiv) return;

        // Preparar datos para gráfico de barras
        const names = analyses.map(a => a.filename || a.name);
        const concentrations = analyses.map(a => a.concentration || 0);
        const pfasValues = analyses.map(a => a.pfas || 0);

        const trace1 = {
            x: names,
            y: concentrations,
            name: LanguageManager.t('results.concentration'),
            type: 'bar',
            marker: { color: '#3498db' }
        };

        const trace2 = {
            x: names,
            y: pfasValues,
            name: LanguageManager.t('results.pifas'),
            type: 'bar',
            marker: { color: '#27ae60' },
            yaxis: 'y2'
        };

        const layout = {
            title: {
                text: LanguageManager.t('comparison.chartTitle'),
                font: { size: 16, color: '#2c3e50' }
            },
            xaxis: {
                title: LanguageManager.t('comparison.samples')
            },
            yaxis: {
                title: LanguageManager.t('results.concentration') + ' (mM)',
                side: 'left'
            },
            yaxis2: {
                title: LanguageManager.t('results.pifas') + ' (%)',
                side: 'right',
                overlaying: 'y'
            },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            margin: { t: 60, r: 60, b: 100, l: 60 },
            showlegend: true,
            legend: { orientation: 'h', y: -0.2 },
            barmode: 'group'
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