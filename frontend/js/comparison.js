// ============================================================================
// COMPARISON MANAGER - Gestión de comparación de muestras
// ============================================================================

class ComparisonManager {
    constructor() {
        this.allSamples = [];
        this.selectedSamples = [];
        this.maxSamples = 5;
        this.comparisonChart = null;
    }

    /**
     * Inicializa el módulo de comparación
     */
    async init() {
        console.log('[Comparison] Inicializando...');
        this.setupEventListeners();
        await this.loadSamples();
    }

    /**
     * Configura los event listeners
     */
    setupEventListeners() {
        const exportBtn = document.getElementById('exportComparisonBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportComparison());
        }
    }

    /**
     * Carga todas las muestras disponibles
     */
    async loadSamples() {
        try {
            console.log('[Comparison] Cargando muestras...');
            
            if (!window.CURRENT_COMPANY_PROFILE || !window.CURRENT_COMPANY_PROFILE.company_id) {
                console.error('[Comparison] No hay empresa seleccionada');
                return;
            }

            // Cargar todas las mediciones
            const response = await APIClient.getHistory(1, 1000);
            this.allSamples = response.measurements || [];
            
            console.log(`[Comparison] ${this.allSamples.length} muestras cargadas`);
            
            this.renderSampleSelector();
            
        } catch (error) {
            console.error('[Comparison] Error cargando muestras:', error);
            UIManager.showNotification('Error al cargar muestras', 'error');
        }
    }

    /**
     * Renderiza el selector de muestras
     */
    renderSampleSelector() {
        const container = document.getElementById('sampleSelectorContainer');
        if (!container) return;

        if (this.allSamples.length === 0) {
            container.innerHTML = `
                <div class="empty-state-comparison">
                    <i class="fas fa-inbox fa-3x" style="color: #6b7280; margin-bottom: 1rem;"></i>
                    <p>${LanguageManager.t('comparison.noSamples')}</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.allSamples.map(sample => {
            const isSelected = this.selectedSamples.find(s => s.id === sample.id);
            const displayName = sample.filename || sample.sample_name || 'N/A';
            const date = new Date(sample.timestamp || sample.created_at).toLocaleDateString();
            
            return `
                <div class="sample-card ${isSelected ? 'selected' : ''}" data-sample-id="${sample.id}">
                    <div class="sample-card-header">
                        <input type="checkbox" 
                            class="sample-checkbox" 
                            data-sample-id="${sample.id}"
                            ${isSelected ? 'checked' : ''}
                            ${!isSelected && this.selectedSamples.length >= this.maxSamples ? 'disabled' : ''}>
                        <label class="sample-name">${UIManager.escapeHtml(displayName)}</label>
                    </div>
                    <div class="sample-card-body">
                        <div class="sample-info">
                            <small>${date}</small>
                        </div>
                        <div class="sample-metrics">
                            <div class="metric">
                                <span class="metric-label">${LanguageManager.t('results.fluor')}:</span>
                                <span class="metric-value">${(sample.fluor_percentage || 0).toFixed(2)}%</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">${LanguageManager.t('results.pfas')}:</span>
                                <span class="metric-value">${(sample.pfas_percentage || sample.pifas_percentage || 0).toFixed(2)}%</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">${LanguageManager.t('results.quality')}:</span>
                                <span class="metric-value">${(sample.quality_score || 0).toFixed(1)}/10</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // ✅ CORREGIDO: Añadir event listeners correctamente
        container.querySelectorAll('.sample-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                e.stopPropagation(); // Evitar propagación
                const sampleId = parseInt(e.target.getAttribute('data-sample-id'));
                console.log('[Comparison] Checkbox clicked:', sampleId);
                this.toggleSample(sampleId);
            });
        });

        // También hacer clickeable toda la tarjeta
        container.querySelectorAll('.sample-card').forEach(card => {
            card.addEventListener('click', (e) => {
                // Solo si no se hizo click en el checkbox directamente
                if (e.target.classList.contains('sample-checkbox')) return;
                
                const checkbox = card.querySelector('.sample-checkbox');
                if (checkbox && !checkbox.disabled) {
                    checkbox.checked = !checkbox.checked;
                    const sampleId = parseInt(checkbox.getAttribute('data-sample-id'));
                    console.log('[Comparison] Card clicked:', sampleId);
                    this.toggleSample(sampleId);
                }
            });
        });
    }
    
    /**
     * Alterna la selección de una muestra
     */
    toggleSample(sampleId) {
        const sample = this.allSamples.find(s => s.id === sampleId);
        if (!sample) return;

        const index = this.selectedSamples.findIndex(s => s.id === sampleId);

        if (index > -1) {
            // Deseleccionar
            this.selectedSamples.splice(index, 1);
        } else {
            // Seleccionar (si no se alcanzó el máximo)
            if (this.selectedSamples.length >= this.maxSamples) {
                UIManager.showNotification(
                    LanguageManager.t('comparison.maxSamplesReached', { max: this.maxSamples }),
                    'warning'
                );
                return;
            }
            this.selectedSamples.push(sample);
        }

        console.log(`[Comparison] Muestras seleccionadas: ${this.selectedSamples.length}`);

        this.updateUI();
    }

    /**
     * Actualiza la interfaz según las muestras seleccionadas
     */
    updateUI() {
        // Actualizar contador
        const countDisplay = document.getElementById('selectedCountDisplay');
        if (countDisplay) {
            countDisplay.setAttribute('data-params-count', this.selectedSamples.length);
            countDisplay.setAttribute('data-params-max', this.maxSamples);
            countDisplay.textContent = LanguageManager.t('comparison.selected', {
                count: this.selectedSamples.length,
                max: this.maxSamples
            });
        }

        // Habilitar/deshabilitar botón de exportación
        const exportBtn = document.getElementById('exportComparisonBtn');
        if (exportBtn) {
            exportBtn.disabled = this.selectedSamples.length < 2;
        }

        // Re-renderizar selector para actualizar estados
        this.renderSampleSelector();

        // Actualizar gráfico y tabla
        if (this.selectedSamples.length >= 2) {
            this.updateComparisonChart();
            this.updateComparisonTable();
        } else {
            this.clearComparison();
        }
    }

    /**
     * Actualiza el gráfico de comparación
     */
    updateComparisonChart() {
        const chartDiv = document.getElementById('comparisonChart');
        if (!chartDiv) return;

        const sampleNames = this.selectedSamples.map(s => 
            (s.filename || s.sample_name || 'N/A').substring(0, 20)
        );

        const fluorData = this.selectedSamples.map(s => s.fluor_percentage || 0);
        const pfasData = this.selectedSamples.map(s => s.pfas_percentage || s.pifas_percentage || 0);
        const qualityData = this.selectedSamples.map(s => s.quality_score || 0);

        const data = [
            {
                x: sampleNames,
                y: fluorData,
                name: LanguageManager.t('results.fluor'),
                type: 'bar',
                marker: { color: '#10b981' }
            },
            {
                x: sampleNames,
                y: pfasData,
                name: LanguageManager.t('results.pfas'),
                type: 'bar',
                marker: { color: '#6366f1' }
            },
            {
                x: sampleNames,
                y: qualityData,
                name: LanguageManager.t('results.quality'),
                type: 'bar',
                yaxis: 'y2',
                marker: { color: '#f59e0b' }
            }
        ];

        const layout = {
            barmode: 'group',
            xaxis: { title: LanguageManager.t('comparison.sample') },
            yaxis: { title: '(%)', side: 'left' },
            yaxis2: {
                title: LanguageManager.t('results.quality'),
                overlaying: 'y',
                side: 'right',
                range: [0, 10]
            },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#e5e7eb' },
            margin: { t: 20, r: 50, b: 80, l: 50 }
        };

        Plotly.newPlot('comparisonChart', data, layout, { responsive: true });
    }

    /**
     * Actualiza la tabla de comparación
     */
    updateComparisonTable() {
        const table = document.getElementById('comparisonTable');
        if (!table) return;

        const thead = table.querySelector('thead tr');
        const tbody = table.querySelector('tbody');

        // Actualizar encabezados
        thead.innerHTML = `<th>${LanguageManager.t('results.parameter')}</th>` +
            this.selectedSamples.map(s => 
                `<th>${UIManager.escapeHtml((s.filename || s.sample_name || 'N/A').substring(0, 15))}</th>`
            ).join('');

        // Actualizar filas
        const rows = [
            {
                label: LanguageManager.t('results.fluor') + ' (%)',
                values: this.selectedSamples.map(s => (s.fluor_percentage || 0).toFixed(2))
            },
            {
                label: LanguageManager.t('results.pfas') + ' (%)',
                values: this.selectedSamples.map(s => (s.pfas_percentage || s.pifas_percentage || 0).toFixed(2))
            },
            {
                label: LanguageManager.t('results.concentration') + ' (mM)',
                values: this.selectedSamples.map(s => ((s.analysis?.pifas_concentration || s.concentration || 0)).toFixed(4))
            },
            {
                label: LanguageManager.t('results.quality') + ' (/10)',
                values: this.selectedSamples.map(s => (s.quality_score || 0).toFixed(1))
            },
            {
                label: LanguageManager.t('comparison.date'),
                values: this.selectedSamples.map(s => new Date(s.timestamp || s.created_at).toLocaleDateString())
            }
        ];

        tbody.innerHTML = rows.map(row => `
            <tr>
                <td><strong>${row.label}</strong></td>
                ${row.values.map(v => `<td>${v}</td>`).join('')}
            </tr>
        `).join('');
    }

    /**
     * Limpia el gráfico y la tabla
     */
    clearComparison() {
        const chartDiv = document.getElementById('comparisonChart');
        if (chartDiv) {
            chartDiv.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #9ca3af;">
                    <p>${LanguageManager.t('comparison.selectSamples')}</p>
                </div>
            `;
        }

        const tbody = document.querySelector('#comparisonTable tbody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="empty-state-cell">
                        ${LanguageManager.t('comparison.selectSamples')}
                    </td>
                </tr>
            `;
        }
    }

    /**
     * Exporta la comparación
     */
    async exportComparison() {
        if (this.selectedSamples.length < 2) {
            UIManager.showNotification(
                LanguageManager.t('comparison.noSamplesSelected'),
                'warning'
            );
            return;
        }

        // Mostrar menú de opciones de formato
        this.showExportFormatMenu();
    }

    /**
     * Muestra el menú de selección de formato
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
                <h3>${LanguageManager.t('analyzer.exportReport')}</h3>
                <p>Selecciona el formato de exportación:</p>
                <div class="export-format-options">
                    ${formats.map(fmt => `
                        <button class="export-format-btn" data-format="${fmt.value}">
                            <i class="fas ${fmt.icon}"></i>
                            <span>${fmt.label}</span>
                        </button>
                    `).join('')}
                </div>
                <button class="export-format-cancel">${LanguageManager.t('dashboard.clear')}</button>
            </div>
        `;

        document.body.appendChild(menu);

        // Event listeners
        menu.querySelectorAll('.export-format-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const format = btn.dataset.format;
                document.body.removeChild(menu);
                await this.performExport(format);
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
     * Realiza la exportación
     */
    async performExport(format) {
        try {
            UIManager.showLoading(LanguageManager.t('messages.exporting'));

            // Preparar datos para exportación
            const samples = this.selectedSamples.map(s => ({
                filename: s.filename || s.sample_name,
                fluor: s.fluor_percentage || 0,
                pfas: s.pfas_percentage || s.pifas_percentage || 0,
                concentration: s.analysis?.pifas_concentration || s.concentration || 0,
                quality: s.quality_score || 0,
                date: new Date(s.timestamp || s.created_at).toISOString()
            }));

            // Capturar gráfico
            let chartImage = null;
            try {
                chartImage = await Plotly.toImage(document.getElementById('comparisonChart'), {
                    format: 'png',
                    width: 800,
                    height: 500
                });
            } catch (error) {
                console.warn('[Comparison] No se pudo capturar gráfico:', error);
            }

            const exportConfig = {
                type: 'comparison',
                format: format,
                lang: LanguageManager.currentLang || 'es',
                samples: samples,
                chart_image: chartImage
            };

            await APIClient.exportData(exportConfig);
            
            UIManager.hideLoading();
            UIManager.showNotification(
                LanguageManager.t('comparison.exportSuccess'),
                'success'
            );

        } catch (error) {
            console.error('[Comparison] Error exportando:', error);
            UIManager.hideLoading();
            UIManager.showNotification(
                LanguageManager.t('comparison.exportError'),
                'error'
            );
        }
    }
}

// Instancia global
window.ComparisonManager = new ComparisonManager();

// Inicializar cuando se active la pestaña
document.addEventListener('DOMContentLoaded', () => {
    const comparisonTab = document.querySelector('[data-tab="comparison"]');
    if (comparisonTab) {
        comparisonTab.addEventListener('click', () => {
            if (window.ComparisonManager) {
                window.ComparisonManager.init();
            }
        });
    }
});