// ============================================================================
// COMPARISON MANAGER - Gestión de comparación de muestras (LIMPIA + OPTIMIZADA)
// ============================================================================

class ComparisonManager {
    constructor() {
        this.allSamples = [];
        this.selectedSamples = [];
        this.maxSamples = 5;
        this.comparisonChart = null;
        this.initialized = false;
    }

    /**
     * Inicializa el módulo de comparación
     */
    async init() {
        if (this.initialized) {
            // Si ya está inicializado, recargar muestras (por si hay datos nuevos)
            await this.loadSamples();
            return;
        }
        this.setupEventListeners();
        this.initialized = true;
        await this.loadSamples();
    }

    /**
     * Configura los event listeners relevantes
     */
    setupEventListeners() {
        const exportBtn = document.getElementById('exportComparisonBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportComparison());
        }

        window.addEventListener('languageChanged', (event) => {
            const tab = document.getElementById('comparison-tab');
            if (!(tab && tab.classList.contains('active'))) return;

            // Refrescar UI y traducciones al cambiar idioma
            this.updateUI();
            if (window.LanguageManager && typeof window.LanguageManager.applyTranslations === 'function') {
                window.LanguageManager.applyTranslations(tab);
            }
        });
    }

    /**
     * Carga todas las muestras disponibles desde APIClient
     */
    async loadSamples() {
        try {
            if (!window.CURRENT_COMPANY_PROFILE?.company_id) {
                this.showError('No hay empresa seleccionada. Por favor, vuelve a iniciar sesión.');
                return;
            }

            const companyId = window.CURRENT_COMPANY_PROFILE.company_id;
            this.showLoading(true);

            // Traer historial (paginación amplia por defecto)
            const response = await APIClient.getHistory(1, 1000);
            if (!response) throw new Error('No se recibió respuesta del servidor');

            this.allSamples = response.measurements || [];
            this.renderSampleSelector();
        } catch (error) {
            this.showError(`Error al cargar muestras: ${error?.message || error}`);
            console.error('[Comparison] loadSamples error:', error);
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Muestra/oculta estado de carga en el contenedor del selector
     */
    showLoading(show) {
        const container = document.getElementById('sampleSelectorContainer');
        if (!container) return;

        if (show) {
            const loadingText = window.LanguageManager?.t('comparison.loadingSamples') || 'Cargando muestras...';
            container.innerHTML = `
                <div style="text-align:center;padding:40px;">
                    <i class="fas fa-spinner fa-spin fa-2x" style="color:#6366f1;"></i>
                    <p style="margin-top:10px;color:#9ca3af;">${this.escapeHtml(loadingText)}</p>
                </div>
            `;
        }
    }

    /**
     * Mostrar mensaje de error (UIManager si existe, fallback a alert)
     */
    showError(message) {
        if (window.UIManager && typeof UIManager.showNotification === 'function') {
            UIManager.showNotification(message, 'error');
        } else {
            // Nota: preferimos console.error + alert solo si no hay UIManager
            console.error('[Comparison] Error:', message);
            alert(message);
        }
    }

    /**
     * Renderiza el selector de muestras
     */
    renderSampleSelector() {
        const container = document.getElementById('sampleSelectorContainer');
        if (!container) {
            console.warn('[Comparison] sampleSelectorContainer no encontrado');
            return;
        }

        if (!Array.isArray(this.allSamples) || this.allSamples.length === 0) {
            const noSamplesText = window.LanguageManager?.t('comparison.noSamples') || 'No hay muestras';
            container.innerHTML = `
                <div class="empty-state-comparison">
                    <i class="fas fa-inbox fa-3x" style="color: #6b7280; margin-bottom: 1rem;"></i>
                    <p>${this.escapeHtml(noSamplesText)}</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.allSamples.map(sample => {
            const isSelected = !!this.selectedSamples.find(s => s.id === sample.id);
            const displayName = sample.filename || sample.sample_name || 'N/A';
            const date = new Date(sample.timestamp || sample.created_at || Date.now()).toLocaleDateString();
            const fluorVal = Number(sample.fluor_percentage || 0).toFixed(2);
            const pfasVal = Number(sample.pfas_percentage ?? sample.pifas_percentage ?? 0).toFixed(2);
            const qualityVal = Number(sample.quality_score ?? 0).toFixed(1);

            return `
                <div class="sample-card ${isSelected ? 'selected' : ''}" data-sample-id="${sample.id}">
                    <div class="sample-card-header">
                        <input type="checkbox"
                            class="sample-checkbox"
                            data-sample-id="${sample.id}"
                            ${isSelected ? 'checked' : ''}
                            ${!isSelected && this.selectedSamples.length >= this.maxSamples ? 'disabled' : ''}>
                        <label class="sample-name">${this.escapeHtml(displayName)}</label>
                    </div>
                    <div class="sample-card-body">
                        <div class="sample-info"><small>${this.escapeHtml(date)}</small></div>
                        <div class="sample-metrics">
                            <div class="metric">
                                <span class="metric-label">${this.escapeHtml(window.LanguageManager?.t('results.fluor') || 'Flúor')}:</span>
                                <span class="metric-value">${fluorVal}%</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">${this.escapeHtml(window.LanguageManager?.t('results.pfas') || 'PFAS')}:</span>
                                <span class="metric-value">${pfasVal}%</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">${this.escapeHtml(window.LanguageManager?.t('results.quality') || 'Calidad')}:</span>
                                <span class="metric-value">${qualityVal}/10</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // Listeners: checkbox change
        container.querySelectorAll('.sample-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                e.stopPropagation();
                const id = parseInt(checkbox.getAttribute('data-sample-id'), 10);
                this.toggleSample(id);
            });
        });

        // Listeners: clicking card toggles checkbox
        container.querySelectorAll('.sample-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (e.target && e.target.classList && e.target.classList.contains('sample-checkbox')) return;
                const checkbox = card.querySelector('.sample-checkbox');
                if (!checkbox || checkbox.disabled) return;
                checkbox.checked = !checkbox.checked;
                const id = parseInt(checkbox.getAttribute('data-sample-id'), 10);
                this.toggleSample(id);
            });
        });
    }

    /**
     * Escapa HTML para prevenir XSS
     */
    escapeHtml(text = '') {
        if (window.UIManager && typeof UIManager.escapeHtml === 'function') {
            return UIManager.escapeHtml(text);
        }
        const div = document.createElement('div');
        div.textContent = String(text);
        return div.innerHTML;
    }

    /**
     * Alterna la selección de una muestra
     */
    toggleSample(sampleId) {
        const sample = this.allSamples.find(s => s.id === sampleId);
        if (!sample) {
            console.warn('[Comparison] Muestra no encontrada:', sampleId);
            return;
        }

        const idx = this.selectedSamples.findIndex(s => s.id === sampleId);
        if (idx > -1) {
            this.selectedSamples.splice(idx, 1);
        } else {
            if (this.selectedSamples.length >= this.maxSamples) {
                this.showError(`Máximo ${this.maxSamples} muestras permitidas`);
                return;
            }
            this.selectedSamples.push(sample);
        }

        this.updateUI();
    }

    /**
     * Actualiza la UI: contador, export button, re-render del selector, gráfico y tabla
     */
    updateUI() {
        const countDisplay = document.getElementById('selectedCountDisplay');
        if (countDisplay) {
            countDisplay.setAttribute('data-params-count', String(this.selectedSamples.length));
            countDisplay.setAttribute('data-params-max', String(this.maxSamples));
            const countText = `${this.selectedSamples.length} de ${this.maxSamples} seleccionadas`;
            countDisplay.textContent = this.escapeHtml(countText);
        }

        const exportBtn = document.getElementById('exportComparisonBtn');
        if (exportBtn) exportBtn.disabled = this.selectedSamples.length < 2;

        // Re-render para actualizar estados (checkbox, disabled, etc.)
        this.renderSampleSelector();

        if (this.selectedSamples.length >= 2) {
            this.updateComparisonChart();
            this.updateComparisonTable();
        } else {
            this.clearComparison();
        }
    }

    /**
     * Actualiza el gráfico de comparación (barras)
     */
    updateComparisonChart() {
        const chartDiv = document.getElementById('comparisonChart');
        if (!chartDiv) return;

        const labels = this.selectedSamples.map(s => s.filename || s.sample_name || 'N/A');
        const fluor = this.selectedSamples.map(s => Number(s.fluor_percentage || 0));
        const pfas = this.selectedSamples.map(s => Number(s.pfas_percentage ?? s.pifas_percentage ?? 0));

        const traces = [
            { x: labels, y: fluor, name: (window.LanguageManager?.t('results.fluor') || 'Flúor') + ' (%)', type: 'bar', marker: { color: '#10b981' } },
            { x: labels, y: pfas, name: (window.LanguageManager?.t('results.pfas') || 'PFAS') + ' (%)', type: 'bar', marker: { color: '#3b82f6' } }
        ];

        const layout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#e5e7eb' },
            barmode: 'group',
            xaxis: { title: window.LanguageManager?.t('comparison.sample') || 'Muestra', gridcolor: '#374151', color: '#e5e7eb' },
            yaxis: { title: (window.LanguageManager?.t('results.percentage') || 'Porcentaje') + ' (%)', gridcolor: '#374151', color: '#e5e7eb' },
            margin: { t: 20, r: 20, b: 80, l: 60 },
            showlegend: true
        };

        Plotly.newPlot('comparisonChart', traces, layout, { responsive: true });
    }

    /**
     * Actualiza la tabla de comparación
     */
    updateComparisonTable() {
        const thead = document.querySelector('#comparisonTable thead tr');
        const tbody = document.querySelector('#comparisonTable tbody');
        if (!thead || !tbody) return;

        const maxTitleLen = 15;
        thead.innerHTML = `<th>${this.escapeHtml(window.LanguageManager?.t('results.parameter') || 'Parámetro')}</th>` +
            this.selectedSamples.map(s => `<th>${this.escapeHtml((s.filename || s.sample_name || 'N/A').substring(0, maxTitleLen))}</th>`).join('');

        const rows = [
            { label: (window.LanguageManager?.t('results.fluor') || 'Flúor') + ' (%)', values: this.selectedSamples.map(s => (Number(s.fluor_percentage || 0)).toFixed(2)) },
            { label: (window.LanguageManager?.t('results.pfas') || 'PFAS') + ' (%)', values: this.selectedSamples.map(s => (Number(s.pfas_percentage ?? s.pifas_percentage ?? 0)).toFixed(2)) },
            { label: (window.LanguageManager?.t('results.concentration') || 'Concentración') + ' (mM)', values: this.selectedSamples.map(s => (Number(s.analysis?.pifas_concentration ?? s.concentration ?? 0)).toFixed(4)) },
            { label: (window.LanguageManager?.t('results.quality') || 'Calidad') + ' (/10)', values: this.selectedSamples.map(s => (Number(s.quality_score ?? 0)).toFixed(1)) },
            { label: (window.LanguageManager?.t('comparison.date') || 'Fecha'), values: this.selectedSamples.map(s => new Date(s.timestamp || s.created_at || Date.now()).toLocaleDateString()) }
        ];

        tbody.innerHTML = rows.map(row => `
            <tr>
                <td><strong>${this.escapeHtml(row.label)}</strong></td>
                ${row.values.map(v => `<td>${this.escapeHtml(String(v))}</td>`).join('')}
            </tr>
        `).join('');
    }

    /**
     * Limpia la visualización cuando hay < 2 muestras seleccionadas
     */
    clearComparison() {
        const emptyText = window.LanguageManager?.t('comparison.selectMinSamples') || 'Selecciona al menos 2 muestras';

        const chartDiv = document.getElementById('comparisonChart');
        if (chartDiv) {
            chartDiv.innerHTML = `
                <div style="display:flex;align-items:center;justify-content:center;height:100%;color:#9ca3af;">
                    <p>${this.escapeHtml(emptyText)}</p>
                </div>
            `;
        }

        const tbody = document.querySelector('#comparisonTable tbody');
        if (tbody) {
            tbody.innerHTML = `
                <tr><td colspan="6" class="empty-state-cell">${this.escapeHtml(emptyText)}</td></tr>
            `;
        }
    }

    /**
     * Exporta la comparación mostrando un menú de formatos
     */
    async exportComparison() {
        if (this.selectedSamples.length < 2) {
            this.showError(window.LanguageManager?.t('comparison.selectMinSamples') || 'Selecciona al menos 2 muestras para exportar');
            return;
        }
        this.showExportFormatMenu();
    }

    /**
     * Muestra diálogo simple de selección de formato de exportación
     */
    showExportFormatMenu() {
        const formats = [
            { value: 'pdf', label: 'PDF', icon: 'fa-file-pdf' },
            { value: 'docx', label: 'Word (DOCX)', icon: 'fa-file-word' },
            { value: 'csv', label: 'CSV', icon: 'fa-file-csv' }
        ];

        const menu = document.createElement('div');
        menu.className = 'export-format-menu';
        menu.innerHTML = `
            <div class="export-format-overlay"></div>
            <div class="export-format-dialog">
                <h3>${this.escapeHtml(window.LanguageManager?.t('comparison.exportComparison') || 'Exportar comparación')}</h3>
                <p>${this.escapeHtml(window.LanguageManager?.t('comparison.selectFormat') || 'Selecciona un formato')}</p>
                <div class="export-format-options">
                    ${formats.map(fmt => `
                        <button class="export-format-btn" data-format="${fmt.value}">
                            <i class="fas ${fmt.icon}"></i>
                            <span>${this.escapeHtml(fmt.label)}</span>
                        </button>
                    `).join('')}
                </div>
                <button class="export-format-cancel">${this.escapeHtml(window.LanguageManager?.t('comparison.cancel') || 'Cancelar')}</button>
            </div>
        `;
        document.body.appendChild(menu);

        const removeMenu = () => { if (menu && menu.parentNode) menu.parentNode.removeChild(menu); };

        menu.querySelectorAll('.export-format-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const format = btn.dataset.format;
                removeMenu();
                await this.performExport(format);
            });
        });

        menu.querySelector('.export-format-cancel')?.addEventListener('click', removeMenu);
        menu.querySelector('.export-format-overlay')?.addEventListener('click', removeMenu);
    }

    /**
     * Realiza la exportación: prepara datos, captura gráfico y llama a APIClient.exportData
     */
    async performExport(format) {
        try {
            UIManager?.showLoading?.('Exportando comparación...');

            const samples = this.selectedSamples.map(s => ({
                filename: s.filename || s.sample_name,
                fluor: Number(s.fluor_percentage || 0),
                pfas: Number(s.pfas_percentage ?? s.pifas_percentage ?? 0),
                concentration: Number(s.analysis?.pifas_concentration ?? s.concentration ?? 0),
                quality: Number(s.quality_score ?? 0),
                date: new Date(s.timestamp || s.created_at || Date.now()).toISOString()
            }));

            let chartImage = null;
            try {
                const chartDiv = document.getElementById('comparisonChart');
                if (chartDiv && window.Plotly) {
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    chartImage = await Plotly.toImage(chartDiv, { format: 'png', width: 800, height: 500 });
                }
            } catch (err) {
                console.warn('[Comparison] No se pudo capturar gráfico:', err);
            }

            const companyProfile = window.CURRENT_COMPANY_PROFILE || {};

            const exportConfig = {
                type: 'comparison',
                format,
                lang: window.LanguageManager?.currentLang || 'es',
                samples,
                chart_image: chartImage,
                company_data: {
                    name: companyProfile.company_name,
                    logo: companyProfile.logo_url,
                    address: companyProfile.company_address,
                    phone: companyProfile.contact_phone,
                    email: companyProfile.contact_email
                }
            };

            await APIClient.exportData(exportConfig);
            UIManager?.hideLoading?.();
            UIManager?.showNotification?.(window.LanguageManager?.t('comparison.exportSuccess') || 'Comparación exportada correctamente', 'success');
        } catch (error) {
            UIManager?.hideLoading?.();
            this.showError(window.LanguageManager?.t('comparison.exportError') || 'Error al exportar comparación');
            console.error('[Comparison] performExport error:', error);
        }
    }
}

// Instancia global y listener para inicializar cuando se active la pestaña
window.ComparisonManager = new ComparisonManager();

document.addEventListener('DOMContentLoaded', () => {
    const comparisonTab = document.querySelector('[data-tab="comparison"]');
    if (comparisonTab) {
        comparisonTab.addEventListener('click', () => {
            window.ComparisonManager?.init();
        });
    } else {
        console.warn('[Comparison] Pestaña de comparación no encontrada');
    }
});
