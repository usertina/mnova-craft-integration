// ============================================================================
// COMPARISON MANAGER - Gestión de comparación de muestras (VERSIÓN CORREGIDA)
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
        // Evitar múltiples inicializaciones
        if (this.initialized) {
            console.log('[Comparison] Ya está inicializado, solo recargando muestras...');
            await this.loadSamples();
            return;
        }

        console.log('[Comparison] Inicializando por primera vez...');
        this.setupEventListeners();
        this.initialized = true;
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
            console.log('[Comparison] 🔄 Iniciando carga de muestras...');
            
            // Validar que existe el perfil de empresa
            if (!window.CURRENT_COMPANY_PROFILE || !window.CURRENT_COMPANY_PROFILE.company_id) {
                console.error('[Comparison] ❌ No hay empresa seleccionada');
                this.showError('No hay empresa seleccionada. Por favor, vuelve a iniciar sesión.');
                return;
            }

            const companyId = window.CURRENT_COMPANY_PROFILE.company_id;
            console.log('[Comparison] 📊 Cargando muestras para empresa:', companyId);

            // Mostrar indicador de carga
            this.showLoading(true);

            // Cargar todas las mediciones
            console.log('[Comparison] 🔍 Llamando a APIClient.getHistory...');
            const response = await APIClient.getHistory(1, 1000);
            
            console.log('[Comparison] ✅ Respuesta recibida:', response);
            
            if (!response) {
                throw new Error('No se recibió respuesta del servidor');
            }
            
            this.allSamples = response.measurements || [];
            
            console.log(`[Comparison] ✅ ${this.allSamples.length} muestras cargadas correctamente`);
            
            this.renderSampleSelector();
            
        } catch (error) {
            console.error('[Comparison] ❌ Error cargando muestras:', error);
            console.error('[Comparison] Stack trace:', error.stack);
            this.showError(`Error al cargar muestras: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Muestra un estado de carga
     */
    showLoading(show) {
        const container = document.getElementById('sampleSelectorContainer');
        if (container && show) {
            container.innerHTML = '<div style="text-align:center;padding:40px;"><i class="fas fa-spinner fa-spin fa-2x" style="color:#6366f1;"></i><p style="margin-top:10px;color:#9ca3af;">Cargando muestras...</p></div>';
        }
    }

    /**
     * Muestra un mensaje de error
     */
    showError(message) {
        console.error('[Comparison] Error:', message);
        if (window.UIManager && typeof UIManager.showNotification === 'function') {
            UIManager.showNotification(message, 'error');
        } else {
            alert(message);
        }
    }

    /**
     * Renderiza el selector de muestras
     */
    renderSampleSelector() {
        const container = document.getElementById('sampleSelectorContainer');
        if (!container) {
            console.warn('[Comparison] No se encontró sampleSelectorContainer');
            return;
        }

        console.log('[Comparison] Renderizando', this.allSamples.length, 'muestras');

        if (this.allSamples.length === 0) {
            container.innerHTML = `
                <div class="empty-state-comparison">
                    <i class="fas fa-inbox fa-3x" style="color: #6b7280; margin-bottom: 1rem;"></i>
                    <p>No hay muestras disponibles</p>
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
                        <label class="sample-name">${this.escapeHtml(displayName)}</label>
                    </div>
                    <div class="sample-card-body">
                        <div class="sample-info">
                            <small>${date}</small>
                        </div>
                        <div class="sample-metrics">
                            <div class="metric">
                                <span class="metric-label">Flúor:</span>
                                <span class="metric-value">${(sample.fluor_percentage || 0).toFixed(2)}%</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">PFAS:</span>
                                <span class="metric-value">${(sample.pfas_percentage || sample.pifas_percentage || 0).toFixed(2)}%</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Calidad:</span>
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
        
        console.log('[Comparison] ✅ Selector de muestras renderizado');
    }
    
    /**
     * Escapa HTML para prevenir XSS
     */
    escapeHtml(text) {
        if (window.UIManager && typeof UIManager.escapeHtml === 'function') {
            return UIManager.escapeHtml(text);
        }
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Alterna la selección de una muestra
     */
    toggleSample(sampleId) {
        const sample = this.allSamples.find(s => s.id === sampleId);
        if (!sample) {
            console.warn('[Comparison] No se encontró la muestra con ID:', sampleId);
            return;
        }

        const index = this.selectedSamples.findIndex(s => s.id === sampleId);

        if (index > -1) {
            // Deseleccionar
            this.selectedSamples.splice(index, 1);
            console.log('[Comparison] Muestra deseleccionada:', sampleId);
        } else {
            // Seleccionar (si no se alcanzó el máximo)
            if (this.selectedSamples.length >= this.maxSamples) {
                this.showError(`Máximo ${this.maxSamples} muestras permitidas`);
                return;
            }
            this.selectedSamples.push(sample);
            console.log('[Comparison] Muestra seleccionada:', sampleId);
        }

        console.log(`[Comparison] Muestras seleccionadas: ${this.selectedSamples.length}`);

        this.updateUI();
    }

    /**
     * Actualiza la interfaz según las muestras seleccionadas
     */
    updateUI() {
        console.log('[Comparison] Actualizando UI...');
        
        // Actualizar contador
        const countDisplay = document.getElementById('selectedCountDisplay');
        if (countDisplay) {
            countDisplay.setAttribute('data-params-count', this.selectedSamples.length);
            countDisplay.setAttribute('data-params-max', this.maxSamples);
            countDisplay.textContent = `${this.selectedSamples.length} de ${this.maxSamples} seleccionadas`;
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
        if (!chartDiv) {
            console.warn('[Comparison] No se encontró comparisonChart');
            return;
        }

        console.log('[Comparison] Actualizando gráfico de comparación...');

        const traces = [
            {
                x: this.selectedSamples.map(s => s.filename || s.sample_name || 'N/A'),
                y: this.selectedSamples.map(s => s.fluor_percentage || 0),
                name: 'Flúor (%)',
                type: 'bar',
                marker: { color: '#10b981' }
            },
            {
                x: this.selectedSamples.map(s => s.filename || s.sample_name || 'N/A'),
                y: this.selectedSamples.map(s => s.pfas_percentage || s.pifas_percentage || 0),
                name: 'PFAS (%)',
                type: 'bar',
                marker: { color: '#3b82f6' }
            }
        ];

        const layout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#e5e7eb' },
            barmode: 'group',
            xaxis: {
                title: 'Muestra',
                gridcolor: '#374151',
                color: '#e5e7eb'
            },
            yaxis: {
                title: 'Porcentaje (%)',
                gridcolor: '#374151',
                color: '#e5e7eb'
            },
            margin: { t: 20, r: 20, b: 80, l: 60 },
            showlegend: true
        };

        Plotly.newPlot('comparisonChart', traces, layout, { responsive: true });
        console.log('[Comparison] ✅ Gráfico de comparación actualizado');
    }

    /**
     * Actualiza la tabla de comparación
     */
    updateComparisonTable() {
        const thead = document.querySelector('#comparisonTable thead tr');
        const tbody = document.querySelector('#comparisonTable tbody');
        
        if (!thead || !tbody) {
            console.warn('[Comparison] No se encontró thead o tbody de comparisonTable');
            return;
        }

        console.log('[Comparison] Actualizando tabla de comparación...');

        // Actualizar encabezados
        thead.innerHTML = '<th>Parámetro</th>' +
            this.selectedSamples.map(s => 
                `<th>${this.escapeHtml((s.filename || s.sample_name || 'N/A').substring(0, 15))}</th>`
            ).join('');

        // Actualizar filas
        const rows = [
            {
                label: 'Flúor (%)',
                values: this.selectedSamples.map(s => (s.fluor_percentage || 0).toFixed(2))
            },
            {
                label: 'PFAS (%)',
                values: this.selectedSamples.map(s => (s.pfas_percentage || s.pifas_percentage || 0).toFixed(2))
            },
            {
                label: 'Concentración (mM)',
                values: this.selectedSamples.map(s => ((s.analysis?.pifas_concentration || s.concentration || 0)).toFixed(4))
            },
            {
                label: 'Calidad (/10)',
                values: this.selectedSamples.map(s => (s.quality_score || 0).toFixed(1))
            },
            {
                label: 'Fecha',
                values: this.selectedSamples.map(s => new Date(s.timestamp || s.created_at).toLocaleDateString())
            }
        ];

        tbody.innerHTML = rows.map(row => `
            <tr>
                <td><strong>${row.label}</strong></td>
                ${row.values.map(v => `<td>${v}</td>`).join('')}
            </tr>
        `).join('');
        
        console.log('[Comparison] ✅ Tabla de comparación actualizada');
    }

    /**
     * Limpia el gráfico y la tabla
     */
    clearComparison() {
        console.log('[Comparison] Limpiando visualización...');
        
        const chartDiv = document.getElementById('comparisonChart');
        if (chartDiv) {
            chartDiv.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #9ca3af;">
                    <p>Selecciona al menos 2 muestras para comparar</p>
                </div>
            `;
        }

        const tbody = document.querySelector('#comparisonTable tbody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="empty-state-cell">
                        Selecciona al menos 2 muestras para comparar
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
            this.showError('Selecciona al menos 2 muestras para exportar');
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
                <h3>Exportar Comparación</h3>
                <p>Selecciona el formato de exportación:</p>
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
            if (window.UIManager) {
                UIManager.showLoading('Exportando comparación...');
            }

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
                const chartDiv = document.getElementById('comparisonChart');
                if (chartDiv && window.Plotly) {
                    chartImage = await Plotly.toImage(chartDiv, {
                        format: 'png',
                        width: 800,
                        height: 500
                    });
                }
            } catch (error) {
                console.warn('[Comparison] No se pudo capturar gráfico:', error);
            }

            // Obtener datos de la empresa
            const companyProfile = window.CURRENT_COMPANY_PROFILE || {};

            const exportConfig = {
                type: 'comparison',
                format: format,
                lang: window.LanguageManager?.currentLang || 'es',
                samples: samples,
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
            
            if (window.UIManager) {
                UIManager.hideLoading();
                UIManager.showNotification('Comparación exportada correctamente', 'success');
            }

        } catch (error) {
            console.error('[Comparison] Error exportando:', error);
            if (window.UIManager) {
                UIManager.hideLoading();
                UIManager.showNotification('Error al exportar comparación', 'error');
            }
        }
    }
}

// Instancia global
window.ComparisonManager = new ComparisonManager();

// Inicializar cuando se active la pestaña
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Comparison] DOM cargado, configurando listener de pestaña...');
    
    const comparisonTab = document.querySelector('[data-tab="comparison"]');
    if (comparisonTab) {
        console.log('[Comparison] Pestaña de comparación encontrada, añadiendo listener');
        comparisonTab.addEventListener('click', () => {
            console.log('[Comparison] Click en pestaña de comparación');
            if (window.ComparisonManager) {
                window.ComparisonManager.init();
            }
        });
    } else {
        console.warn('[Comparison] No se encontró la pestaña de comparación');
    }
});