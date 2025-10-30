// ============================================================================
// DASHBOARD MANAGER - Gestión del panel de control
// ============================================================================

class DashboardManager {
    constructor() {
        this.measurements = [];
        this.filteredMeasurements = [];
        this.charts = {
            trend: null,
            distribution: null
        };
    }

    /**
     * Inicializa el dashboard
     */
    async init() {
        console.log('[Dashboard] Inicializando...');
        this.setupEventListeners();
        await this.loadData();
    }

    /**
     * Configura los event listeners
     */
    setupEventListeners() {
        // Filtro rápido
        const quickFilter = document.getElementById('dashboardQuickFilter');
        if (quickFilter) {
            quickFilter.addEventListener('change', () => this.applyQuickFilter());
        }

        // Mostrar/ocultar rango personalizado
        const customDateRange = document.getElementById('customDateRange');
        if (quickFilter && customDateRange) {
            quickFilter.addEventListener('change', (e) => {
                customDateRange.style.display = e.target.value === 'custom' ? 'flex' : 'none';
            });
        }

        // Aplicar filtro de fecha personalizado
        const applyDateFilter = document.getElementById('applyDateFilter');
        if (applyDateFilter) {
            applyDateFilter.addEventListener('click', () => this.applyCustomDateFilter());
        }

        // Limpiar filtro
        const clearDateFilter = document.getElementById('clearDateFilter');
        if (clearDateFilter) {
            clearDateFilter.addEventListener('click', () => this.clearDateFilter());
        }

        // Refrescar dashboard
        const refreshBtn = document.getElementById('refreshDashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadData());
        }

        // Exportar dashboard
        const exportBtn = document.getElementById('exportDashboardBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportDashboard());
        }
    }

    /**
     * Carga los datos del dashboard
     */
    async loadData() {
        try {
            console.log('[Dashboard] Cargando datos...');
            
            if (!window.CURRENT_COMPANY_PROFILE || !window.CURRENT_COMPANY_PROFILE.company_id) {
                console.error('[Dashboard] No hay empresa seleccionada');
                return;
            }

            const companyId = window.CURRENT_COMPANY_PROFILE.company_id;
            
            // Cargar todas las mediciones (sin paginación para el dashboard)
            const response = await APIClient.getHistory(1, 1000); // Cargar muchas para estadísticas
            
            this.measurements = response.measurements || [];
            this.filteredMeasurements = [...this.measurements];
            
            console.log(`[Dashboard] ${this.measurements.length} mediciones cargadas`);
            
            this.updateStatistics();
            this.updateCharts();
            this.updateRecentAnalyses();
            
        } catch (error) {
            console.error('[Dashboard] Error cargando datos:', error);
            UIManager.showNotification('Error al cargar datos del dashboard', 'error');
        }
    }

    /**
     * Aplica filtro rápido
     */
    applyQuickFilter() {
        const filter = document.getElementById('dashboardQuickFilter')?.value;
        if (!filter) return;

        const now = new Date();
        let startDate = null;

        switch (filter) {
            case 'today':
                startDate = new Date(now.setHours(0, 0, 0, 0));
                break;
            case 'week':
                startDate = new Date(now.setDate(now.getDate() - 7));
                break;
            case 'month':
                startDate = new Date(now.setMonth(now.getMonth() - 1));
                break;
            case 'all':
            default:
                this.filteredMeasurements = [...this.measurements];
                this.updateStatistics();
                this.updateCharts();
                return;
        }

        this.filteredMeasurements = this.measurements.filter(m => {
            const measurementDate = new Date(m.timestamp || m.created_at);
            return measurementDate >= startDate;
        });

        console.log(`[Dashboard] Filtro aplicado: ${this.filteredMeasurements.length} mediciones`);
        
        this.updateStatistics();
        this.updateCharts();
    }

    /**
     * Aplica filtro de fecha personalizado
     */
    applyCustomDateFilter() {
        const dateFrom = document.getElementById('dateFrom')?.value;
        const dateTo = document.getElementById('dateTo')?.value;

        if (!dateFrom || !dateTo) {
            UIManager.showNotification('Selecciona ambas fechas', 'warning');
            return;
        }

        const startDate = new Date(dateFrom);
        const endDate = new Date(dateTo);
        endDate.setHours(23, 59, 59, 999);

        this.filteredMeasurements = this.measurements.filter(m => {
            const measurementDate = new Date(m.timestamp || m.created_at);
            return measurementDate >= startDate && measurementDate <= endDate;
        });

        console.log(`[Dashboard] Filtro personalizado: ${this.filteredMeasurements.length} mediciones`);
        
        this.updateStatistics();
        this.updateCharts();
    }

    /**
     * Limpia el filtro de fecha
     */
    clearDateFilter() {
        document.getElementById('dateFrom').value = '';
        document.getElementById('dateTo').value = '';
        document.getElementById('dashboardQuickFilter').value = 'all';
        document.getElementById('customDateRange').style.display = 'none';
        
        this.filteredMeasurements = [...this.measurements];
        this.updateStatistics();
        this.updateCharts();
    }

    /**
     * Actualiza las estadísticas
     */
    updateStatistics() {
        const measurements = this.filteredMeasurements;
        
        if (measurements.length === 0) {
            document.getElementById('dashTotalAnalyses').textContent = '0';
            document.getElementById('dashAvgFluor').textContent = '0%';
            document.getElementById('dashAvgPfas').textContent = '0%';
            return;
        }

        // Total de análisis
        document.getElementById('dashTotalAnalyses').textContent = measurements.length;

        // Promedio de flúor
        const avgFluor = measurements.reduce((sum, m) => sum + (m.fluor_percentage || 0), 0) / measurements.length;
        document.getElementById('dashAvgFluor').textContent = `${avgFluor.toFixed(2)}%`;

        // Promedio de PFAS
        const avgPfas = measurements.reduce((sum, m) => sum + (m.pfas_percentage || m.pifas_percentage || 0), 0) / measurements.length;
        document.getElementById('dashAvgPfas').textContent = `${avgPfas.toFixed(2)}%`;
    }

    /**
     * Actualiza los gráficos
     */
    updateCharts() {
        this.updateTrendChart();
        this.updateDistributionChart();
    }

    /**
     * Actualiza el gráfico de tendencia
     */
    updateTrendChart() {
        const measurements = this.filteredMeasurements.slice().reverse(); // Más antiguos primero

        if (measurements.length === 0) {
            const container = document.getElementById('trendChart');
            if (container) {
                container.innerHTML = '<p style="text-align:center;padding:20px;">No hay datos disponibles</p>';
            }
            return;
        }

        const dates = measurements.map(m => {
            const date = new Date(m.timestamp || m.created_at);
            return date.toLocaleDateString();
        });

        const fluorData = measurements.map(m => m.fluor_percentage || 0);
        const pfasData = measurements.map(m => m.pfas_percentage || m.pifas_percentage || 0);
        const concentrationData = measurements.map(m => m.analysis?.pifas_concentration || 0);

        const data = [
            {
                x: dates,
                y: fluorData,
                name: LanguageManager.t('results.fluor'),
                type: 'scatter',
                mode: 'lines+markers',
                line: { color: '#10b981' },
                yaxis: 'y'
            },
            {
                x: dates,
                y: pfasData,
                name: LanguageManager.t('results.pfas'),
                type: 'scatter',
                mode: 'lines+markers',
                line: { color: '#6366f1' },
                yaxis: 'y'
            },
            {
                x: dates,
                y: concentrationData,
                name: LanguageManager.t('results.concentration') || 'Concentración',
                type: 'scatter',
                mode: 'lines+markers',
                line: { color: '#f59e0b', dash: 'dot' },
                yaxis: 'y2'
            }
        ];

        const layout = {
            title: '',
            xaxis: { title: LanguageManager.t('dashboard.date') },
            yaxis: { 
                title: '(%)',
                side: 'left'
            },
            yaxis2: {
                title: 'Concentración (mM)',
                overlaying: 'y',
                side: 'right',
                color: '#f59e0b'
            },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#e5e7eb' },
            margin: { t: 20, r: 60, b: 40, l: 50 },
            showlegend: true,
            legend: { x: 0, y: 1.1, orientation: 'h' }
        };

        Plotly.newPlot('trendChart', data, layout, { responsive: true });
    }

    /**
     * Actualiza el gráfico de distribución de calidad
     */
    updateDistributionChart() {
        const measurements = this.filteredMeasurements;

        if (measurements.length === 0) {
            const container = document.getElementById('distributionChart');
            if (container) {
                container.innerHTML = '<p style="text-align:center;padding:20px;">No hay datos disponibles</p>';
            }
            return;
        }

        // Categorizar por calidad
        const categories = {
            excellent: 0,
            good: 0,
            regular: 0,
            low: 0
        };

        measurements.forEach(m => {
            const quality = m.quality_score || 0;
            if (quality >= 8) categories.excellent++;
            else if (quality >= 6) categories.good++;
            else if (quality >= 4) categories.regular++;
            else categories.low++;
        });

        const data = [{
            values: [categories.excellent, categories.good, categories.regular, categories.low],
            labels: [
                LanguageManager.t('dashboard.qualityLabels.excellent'),
                LanguageManager.t('dashboard.qualityLabels.good'),
                LanguageManager.t('dashboard.qualityLabels.regular'),
                LanguageManager.t('dashboard.qualityLabels.low')
            ],
            type: 'pie',
            marker: {
                colors: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444']
            }
        }];

        const layout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#e5e7eb' },
            margin: { t: 20, r: 20, b: 20, l: 20 },
            showlegend: true
        };

        Plotly.newPlot('distributionChart', data, layout, { responsive: true });
    }

    /**
     * Actualiza la tabla de análisis recientes
     */
    updateRecentAnalyses() {
        const tbody = document.querySelector('#recentAnalysesTable tbody');
        if (!tbody) return;

        const recent = this.measurements.slice(0, 10); // Últimos 10

        if (recent.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align:center;padding:20px;">
                        ${LanguageManager.t('dashboard.noData')}
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = recent.map(m => `
            <tr>
                <td>${UIManager.escapeHtml(m.filename || m.sample_name || 'N/A')}</td>
                <td>${new Date(m.timestamp || m.created_at).toLocaleString()}</td>
                <td>${(m.fluor_percentage || 0).toFixed(2)}%</td>
                <td>${(m.pfas_percentage || m.pifas_percentage || 0).toFixed(2)}%</td>
                <td>${(m.quality_score || 0).toFixed(1)}/10</td>
            </tr>
        `).join('');
    }

    /**
     * Exporta los datos del dashboard
     */
    async exportDashboard(format = null) {
        try {
            // Si no se especificó formato, mostrar menú
            if (!format) {
                if (window.showExportFormatMenu) {
                    window.showExportFormatMenu('dashboard');
                } else {
                    // Fallback si no existe la función global
                    this.showDashboardExportMenu();
                }
                return;
            }

            UIManager.showLoading(LanguageManager.t('messages.exporting'));

            // Recopilar estadísticas
            const stats = {
                totalAnalyses: this.filteredMeasurements.length,
                avgFluor: this.filteredMeasurements.reduce((sum, m) => sum + (m.fluor_percentage || 0), 0) / this.filteredMeasurements.length,
                avgPfas: this.filteredMeasurements.reduce((sum, m) => sum + (m.pfas_percentage || m.pifas_percentage || 0), 0) / this.filteredMeasurements.length,
                avgConcentration: this.filteredMeasurements.reduce((sum, m) => sum + (m.analysis?.pifas_concentration || m.concentration || 0), 0) / this.filteredMeasurements.length,
                avgQuality: this.filteredMeasurements.reduce((sum, m) => sum + (m.quality_score || 0), 0) / this.filteredMeasurements.length,
                avgSNR: this.filteredMeasurements.reduce((sum, m) => sum + (m.snr || m.signal_to_noise || 0), 0) / this.filteredMeasurements.length,
                highQualitySamples: this.filteredMeasurements.filter(m => (m.quality_score || 0) >= 8).length
            };

            // Capturar gráficos como imágenes
            const trendImage = await this.captureChartAsBase64('trendChart');
            const distributionImage = await this.captureChartAsBase64('distributionChart');

            // Obtener datos de la empresa
            const companyProfile = window.CURRENT_COMPANY_PROFILE || {};

            const exportConfig = {
                type: 'dashboard',
                format: format,
                lang: LanguageManager.currentLang || 'es',
                stats: stats,
                chart_images: {
                    trend: trendImage,
                    distribution: distributionImage
                },
                company_data: {
                    name: companyProfile.company_name,
                    logo: companyProfile.logo_url,
                    address: companyProfile.company_address,
                    phone: companyProfile.contact_phone,
                    email: companyProfile.contact_email
                }
            };

            await APIClient.exportData(exportConfig);
            
            UIManager.hideLoading();
            UIManager.showNotification(LanguageManager.t('messages.exportSuccess'), 'success');

        } catch (error) {
            console.error('[Dashboard] Error exportando:', error);
            UIManager.hideLoading();
            UIManager.showNotification(LanguageManager.t('errors.exportFailed'), 'error');
        }
    }

    /**
     * Muestra menú de exportación del dashboard (fallback)
     */
    showDashboardExportMenu() {
        const formats = [
            { value: 'pdf', label: 'PDF', icon: 'fa-file-pdf' },
            { value: 'docx', label: 'Word (DOCX)', icon: 'fa-file-word' }
        ];

        const menu = document.createElement('div');
        menu.className = 'export-format-menu';
        menu.innerHTML = `
            <div class="export-format-overlay"></div>
            <div class="export-format-dialog">
                <h3>Exportar Dashboard</h3>
                <p>Selecciona el formato:</p>
                <div class="export-format-options">
                    ${formats.map(fmt => `
                        <button class="export-format-btn" data-format="${fmt.value}">
                            <i class="fas ${fmt.icon}"></i>
                            <span>${fmt.label}</span>
                        </button>
                    `).join('')}
                </div>
                <button class="export-format-cancel">Cancelar</button>
            </div>
        `;

        document.body.appendChild(menu);

        menu.querySelectorAll('.export-format-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const format = btn.dataset.format;
                document.body.removeChild(menu);
                await this.exportDashboard(format);
            });
        });

        menu.querySelector('.export-format-cancel').addEventListener('click', () => {
            document.body.removeChild(menu);
        });

        menu.querySelector('.export-format-overlay').addEventListener('click', () => {
            document.body.removeChild(menu);
        });
    }

    /**
     * Captura un gráfico de Plotly como base64
     */
    async captureChartAsBase64(chartId) {
        try {
            const chartDiv = document.getElementById(chartId);
            if (!chartDiv) return null;

            return await Plotly.toImage(chartDiv, {
                format: 'png',
                width: 800,
                height: 500
            });
        } catch (error) {
            console.error(`[Dashboard] Error capturando gráfico ${chartId}:`, error);
            return null;
        }
    }

    /**
     * Refresca las traducciones (llamado cuando cambia el idioma)
     */
    refreshTranslations() {
        console.log('[Dashboard] Refrescando traducciones...');
        this.updateCharts();
    }
}

// Instancia global
window.DashboardManager = new DashboardManager();

// Inicializar cuando se active la pestaña
document.addEventListener('DOMContentLoaded', () => {
    const dashboardTab = document.querySelector('[data-tab="dashboard"]');
    if (dashboardTab) {
        dashboardTab.addEventListener('click', () => {
            if (window.DashboardManager) {
                window.DashboardManager.init();
            }
        });
    }
});