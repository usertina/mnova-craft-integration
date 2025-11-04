// ============================================================================
// CHART MANAGER - CraftRMN Pro - VERSIÓN CORREGIDA Y COMPLETA
// Gestión de gráficos con Plotly + Traducciones dinámicas
// ============================================================================

class ChartManager {
    static chart = null;
    static layout = null;
    static config = null;
    static currentPeaks = [];
    static initialized = false; // Evita inicializaciones múltiples

    /**
     * Inicializa el ChartManager con layout y config por defecto,
     * incluso si el gráfico aún no está visible en el DOM.
     */
    static async init() {
        console.log('[ChartManager] Inicializando...');

        try {
            // --- 1. Definir layout base ---
            this.layout = {
                title: { 
                    text: LanguageManager.t('charts.spectrumTitle'),
                    font: { color: '#e5e7eb' }
                },
                xaxis: { 
                    title: { text: LanguageManager.t('charts.ppmAxis'), font: { color: '#9ca3af' } },
                    autorange: 'reversed',
                    gridcolor: '#4b5563',
                    zerolinecolor: '#4b5563',
                    tickfont: { color: '#9ca3af' }
                },
                yaxis: { 
                    title: { text: LanguageManager.t('charts.intensityAxis'), font: { color: '#9ca3af' } },
                    gridcolor: '#4b5563',
                    zerolinecolor: '#4b5563',
                    tickfont: { color: '#9ca3af' }
                },
                plot_bgcolor: '#1f2937',
                paper_bgcolor: '#1f2937',
                showlegend: true,
                legend: { font: { color: '#e5e7eb' } }
            };

            // --- 2. Configuración de Plotly ---
            this.config = {
                responsive: true,
                displaylogo: false,
                modeBarButtonsToRemove: ['toImage', 'sendDataToCloud', 'select2d', 'lasso2d'],
                locale: LanguageManager.currentLang || 'es'
            };

            // --- 3. Crear el gráfico solo si el elemento existe y es visible ---
            const spectrumElement = document.getElementById('spectrumChart');
            if (!spectrumElement || spectrumElement.offsetParent === null) {
                console.warn('[ChartManager] Elemento spectrumChart no encontrado o no visible. Se creará más tarde.');
            } else {
                await this.createEmptyChart();
            }

            // --- 4. Suscribirse al evento de cambio de idioma ---
            window.addEventListener('languageChanged', (event) => {
                const tab = document.getElementById('analyzer-tab');
                if (tab && tab.classList.contains('active')) {
                    console.log(`[ChartManager] 🗣️ Evento 'languageChanged' detectado. Refrescando traducciones.`);
                    this.refreshTranslations(event.detail.lang, false);
                }
            });

            this.initialized = true;
            console.log('[ChartManager] Inicializado correctamente ✅');

        } catch (error) {
            console.error('[ChartManager] Error en init():', error);
            this.initialized = false;
        }
    }

    /**
     * Crea un gráfico vacío con un trazo base.
     */
    static async createEmptyChart() {
        const intensityKey = LanguageManager.t('charts.tooltipIntensity');
        const trace = {
            x: [],
            y: [],
            type: 'scatter',
            mode: 'lines',
            line: { color: '#3498db', width: 1.5 },
            name: LanguageManager.t('charts.spectrumTrace'),
            hovertemplate: `ppm: %{x:.2f}<br>${intensityKey}: %{y:.2f}<extra></extra>`
        };

        this.chart = await Plotly.newPlot('spectrumChart', [trace], this.layout, this.config);
    }

    /**
     * Actualiza el gráfico con los datos del espectro y los picos.
     */
    static updateSpectrumChart(spectrumData, peaksData = null) {
        if (!spectrumData || !spectrumData.ppm || !spectrumData.intensity) {
            window.APP_LOGGER.error(`Invalid spectrum data for chart update.`);
            return;
        }

        if (!this.layout) {
            window.APP_LOGGER.error('Chart layout not initialized. Call init() first.');
            return;
        }

        const intensityKey = LanguageManager.t('charts.tooltipIntensity');
        const spectrumTrace = {
            x: spectrumData.ppm,
            y: spectrumData.intensity,
            type: 'scatter',
            mode: 'lines',
            line: { color: '#3498db', width: 1.5 },
            name: LanguageManager.t('charts.spectrumTrace'),
            hovertemplate: `ppm: %{x:.2f}<br>${intensityKey}: %{y:.2f}<extra></extra>`
        };

        const traces = [spectrumTrace];

        // --- Añadir picos ---
        if (peaksData && Array.isArray(peaksData) && peaksData.length > 0) {
            this.currentPeaks = peaksData;
            const peakKey = LanguageManager.t('charts.tooltipPeak');
            const regionKey = LanguageManager.t('charts.tooltipRegion');

            const peaksTrace = {
                x: peaksData.map(p => p.ppm),
                y: peaksData.map(p => p.intensity),
                type: 'scatter',
                mode: 'markers',
                marker: { color: '#e74c3c', size: 8, symbol: 'x' },
                name: LanguageManager.t('charts.peaksTrace'),
                hovertemplate:
                    `<b>${peakKey}</b><br>` +
                    `ppm: %{x:.3f}<br>` +
                    `${intensityKey}: %{y:.1f}<br>` +
                    `${regionKey}: %{customdata}<extra></extra>`,
                customdata: peaksData.map(p => p.region || 'N/A'),
                showlegend: true
            };

            traces.push(peaksTrace);

            // --- Añadir anotaciones a los tres picos más altos ---
            const topPeaks = [...peaksData].sort((a, b) => b.intensity - a.intensity).slice(0, 3);
            this.layout.annotations = topPeaks.map(peak => ({
                x: peak.ppm,
                y: peak.intensity,
                text: `<b>${LanguageManager.t('charts.tooltipRegion')}: ${peak.region}</b><br>${peak.ppm.toFixed(3)} ppm`,
                showarrow: true,
                arrowhead: 2,
                arrowwidth: 2,
                arrowcolor: '#e74c3c',
                ax: 0,
                ay: -40,
                bgcolor: 'rgba(255,255,255,0.9)',
                bordercolor: '#e74c3c',
                borderwidth: 2,
                borderpad: 4,
                font: { size: 11, color: '#2c3e50' }
            }));
        } else {
            this.currentPeaks = [];
            this.layout.annotations = [];
        }

        // --- Actualizar textos traducidos ---
        this.layout.title.text = LanguageManager.t('charts.spectrumTitle');
        this.layout.xaxis.title.text = LanguageManager.t('charts.ppmAxis');
        this.layout.yaxis.title.text = LanguageManager.t('charts.intensityAxis');

        Plotly.react('spectrumChart', traces, this.layout, this.config)
            .then(() => window.APP_LOGGER.debug('Spectrum chart updated successfully'))
            .catch(error => window.APP_LOGGER.error('Error updating spectrum chart:', error));
    }

    static getCurrentPeaks() {
        return this.currentPeaks;
    }

    static clearPeaks() {
        this.currentPeaks = [];
        if (!this.layout) return;

        this.layout.annotations = [];
        const chartDiv = document.getElementById('spectrumChart');
        if (chartDiv && chartDiv.data?.[0]) {
            Plotly.react('spectrumChart', [chartDiv.data[0]], this.layout, this.config);
        }
    }

    static refreshTranslations(lang, log = true) {
        const chartDiv = document.getElementById('spectrumChart');
        if (!chartDiv || !window.LanguageManager || !chartDiv.layout || !chartDiv.data) {
            if (log) window.APP_LOGGER.warn('Chart or LanguageManager not ready for translation');
            return;
        }

        try {
            const updateLayout = {
                'title.text': LanguageManager.t('charts.spectrumTitle'),
                'xaxis.title.text': LanguageManager.t('charts.ppmAxis'),
                'yaxis.title.text': LanguageManager.t('charts.intensityAxis')
            };

            const intensityKey = LanguageManager.t('charts.tooltipIntensity');
            const updateData = {};
            const traceNames = [];
            const hoverTemplates = [];

            if (chartDiv.data[0]) {
                traceNames.push(LanguageManager.t('charts.spectrumTrace'));
                hoverTemplates.push(`ppm: %{x:.2f}<br>${intensityKey}: %{y:.2f}<extra></extra>`);
            }

            if (chartDiv.data[1]) {
                const peakKey = LanguageManager.t('charts.tooltipPeak');
                const regionKey = LanguageManager.t('charts.tooltipRegion');
                traceNames.push(LanguageManager.t('charts.peaksTrace'));
                hoverTemplates.push(`<b>${peakKey}</b><br>ppm: %{x:.3f}<br>${intensityKey}: %{y:.1f}<br>${regionKey}: %{customdata}<extra></extra>`);
            }

            if (traceNames.length > 0) {
                updateData.name = traceNames;
                updateData.hovertemplate = hoverTemplates;
            }

            this.config.locale = lang;

            Plotly.update('spectrumChart', updateData, updateLayout)
                .then(() => Plotly.react('spectrumChart', chartDiv.data, chartDiv.layout, this.config))
                .then(() => {
                    this.chart = document.getElementById('spectrumChart');
                    if (log) window.APP_LOGGER.debug(`Chart translations updated to: ${lang}`);
                })
                .catch(error => window.APP_LOGGER.error('Error applying chart translations:', error));

            this.layout.title.text = updateLayout['title.text'];
            this.layout.xaxis.title.text = updateLayout['xaxis.title.text'];
            this.layout.yaxis.title.text = updateLayout['yaxis.title.text'];

        } catch (error) {
            window.APP_LOGGER.error('Error refreshing chart translations:', error);
        }
    }

    static addIntegrationRegion(regionData) {
        const chartDiv = document.getElementById('spectrumChart');
        if (!chartDiv || !chartDiv.layout) return;

        const shapes = regionData.map(region => ({
            type: 'rect',
            x0: region.start,
            x1: region.end,
            y0: 0,
            y1: 1,
            yref: 'paper',
            fillcolor: 'rgba(231, 76, 60, 0.2)',
            line: { width: 1, color: 'rgba(231, 76, 60, 0.8)' },
            opacity: 0.3
        }));

        const updatedLayout = { shapes: [...(chartDiv.layout.shapes || []), ...shapes] };
        Plotly.relayout('spectrumChart', updatedLayout)
            .then(() => window.APP_LOGGER.debug('Integration regions added'))
            .catch(error => window.APP_LOGGER.error('Error adding integration regions:', error));
    }

    static clearIntegrationRegions() {
        const chartDiv = document.getElementById('spectrumChart');
        if (!chartDiv || !chartDiv.layout) return;

        Plotly.relayout('spectrumChart', { shapes: [] })
            .then(() => window.APP_LOGGER.debug('Integration regions cleared'))
            .catch(error => window.APP_LOGGER.error('Error clearing integration regions:', error));
    }

    static updateChartTitle(title) {
        Plotly.relayout('spectrumChart', { 'title.text': title })
            .then(() => {
                window.APP_LOGGER.debug('Chart title updated');
                if (this.layout?.title) this.layout.title.text = title;
            })
            .catch(error => window.APP_LOGGER.error('Error updating chart title:', error));
    }

    static exportChart(format = 'png') {
        const chartDiv = document.getElementById('spectrumChart');
        if (!chartDiv) return Promise.reject('Chart not found.');
        return Plotly.downloadImage('spectrumChart', {
            format,
            filename: `rmn_spectrum_${new Date().toISOString().split('T')[0]}`,
            height: 600,
            width: 800,
            scale: 2
        });
    }

    static async getChartAsBase64() {
        const chartDiv = document.getElementById('spectrumChart');
        if (!chartDiv || !chartDiv.data) return null;

        try {
            const imageData = await Plotly.toImage(chartDiv, {
                format: 'png',
                width: 800,
                height: 500,
                scale: 2
            });
            window.APP_LOGGER.debug('Chart captured as base64');
            return imageData;
        } catch (error) {
            window.APP_LOGGER.error('Error capturing chart:', error);
            return null;
        }
    }

    static plotResults(results) {
        if (!this.chart && this.initialized) {
            window.APP_LOGGER.warn('[ChartManager] Chart not found, creating...');
            (async () => {
                await this.createEmptyChart();
                this.plotResults(results);
            })();
            return;
        }

        if (!results) return;

        let spectrumData = results.spectrum || {
            ppm: results.ppm,
            intensity: results.intensity
        };

        if (!spectrumData?.ppm || !spectrumData?.intensity) {
            window.APP_LOGGER.error('[ChartManager] Datos de espectro inválidos:', results);
            UIManager?.showNotification('No se pudieron graficar los datos del espectro', 'warning');
            return;
        }

        let peaksData = null;
        if (Array.isArray(results.peaks) && results.peaks.length > 0) {
            peaksData = results.peaks.map(p => ({
                ppm: p.position || p.ppm || 0,
                intensity: p.height || p.intensity || 0,
                region: p.region || p.assignment || 'N/A',
                width: p.width || 0,
                area: p.area || 0
            }));
        }

        this.updateSpectrumChart(spectrumData, peaksData);

        const sampleName = document.getElementById('sampleName');
        if (sampleName && (results.filename || results.sample_name)) {
            sampleName.textContent = results.sample_name || results.filename;
        }

        window.APP_LOGGER.info('[ChartManager] Gráfico actualizado exitosamente');
    }

    static clearChart() {
        this.clearPeaks();
        this.clearIntegrationRegions();
        const chartDiv = document.getElementById('spectrumChart');
        if (chartDiv) {
            Plotly.purge(chartDiv);
            this.createEmptyChart();
        }
    }
}

// Hacer disponible globalmente
window.ChartManager = ChartManager;
