// ============================================================================
// CHART MANAGER - CraftRMN Pro - VERSIÓN CORREGIDA
// Gestión de gráficos con Plotly + Traducciones dinámicas
// ============================================================================

class ChartManager {
    static chart = null;
    static layout = null;
    static config = null;
    static currentPeaks = []; 
    static initialized = false; // Añadido para seguridad

    /**
     * FUNCIÓN CORREGIDA: Define el layout y config INCLUSO SI EL GRÁFICO ESTÁ OCULTO
     */
    static async init() {
        console.log('[ChartManager] Inicializando...');
        
        try {
            // 1. Definir el layout y config por defecto PRIMERO
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

            this.config = {
                responsive: true,
                displaylogo: false,
                modeBarButtonsToRemove: ['toImage', 'sendDataToCloud', 'select2d', 'lasso2d'],
                locale: LanguageManager.currentLang || 'es'
            };

            // 2. Comprobar si el elemento del gráfico existe Y es visible
            const spectrumElement = document.getElementById('spectrumChart');
            
            if (!spectrumElement || spectrumElement.offsetParent === null) {
                console.warn('[ChartManager] Elemento spectrumChart no encontrado o no visible, se creará cuando sea necesario');
            } else {
                 // 3. Si es visible, crear el gráfico vacío
                await this.createEmptyChart();
            }

            this.initialized = true;
            console.log('[ChartManager] Inicializado correctamente');
            
        } catch (error) {
            console.error('[ChartManager] Error en init():', error);
            this.initialized = false;
        }
    }
        
    /**
     * Crea el gráfico vacío
     */
    static async createEmptyChart() {
        const trace = {
            x: [], y: [], type: 'scatter', mode: 'lines',
            line: { color: '#3498db', width: 1.5 },
            name: LanguageManager.t('charts.spectrumTrace'), 
            hovertemplate: 'ppm: %{x:.2f}<br>Intensidad: %{y:.2f}<extra></extra>'
        };
        
        this.chart = await Plotly.newPlot('spectrumChart', [trace], this.layout, this.config);
    }
    
    /**
     * Función principal que actualiza el gráfico con nuevos datos
     */
    static updateSpectrumChart(spectrumData, peaksData = null) {
    
        if (!spectrumData || !spectrumData.ppm || !spectrumData.intensity) {
            window.APP_LOGGER.error(`Invalid spectrum data for chart update.`);
            return;
        }

        // --- ¡¡¡ESTA ES LA CORRECCIÓN IMPORTANTE!!! ---
        // Si 'init()' no definió el layout (porque la pestaña estaba oculta),
        // el log mostrará un error. Esto es solo informativo.
        if (!this.layout) {
            window.APP_LOGGER.error('Chart layout not initialized. Call init() first.');
            // En este punto, 'init()' ya debería haber sido llamado,
            // pero si falló, los títulos de los ejes no se cargarán.
            // Es mejor fallar aquí que continuar.
            return; 
        }

        const spectrumTrace = {
            x: spectrumData.ppm,
            y: spectrumData.intensity,
            type: 'scatter',
            mode: 'lines',
            line: { color: '#3498db', width: 1.5 },
            name: LanguageManager.t('charts.spectrumTrace'), 
            hovertemplate: 'ppm: %{x:.2f}<br>Intensidad: %{y:.2f}<extra></extra>'
        };

        const traces = [spectrumTrace];

        // Si hay picos detectados, añadirlos
        if (peaksData && Array.isArray(peaksData) && peaksData.length > 0) {
            window.APP_LOGGER.debug(`Adding ${peaksData.length} peaks to chart`);
            
            this.currentPeaks = peaksData;

            const peaksTrace = {
                x: peaksData.map(p => p.ppm),
                y: peaksData.map(p => p.intensity),
                type: 'scatter',
                mode: 'markers', 
                marker: {
                    color: '#e74c3c',
                    size: 8,
                    symbol: 'x', 
                },
                name: LanguageManager.t('charts.peaksTrace'), 
                hovertemplate: '<b>Pico</b><br>' +
                               'ppm: %{x:.3f}<br>' +
                               'Intensidad: %{y:.1f}<br>' +
                               'Region: %{customdata}<extra></extra>',
                customdata: peaksData.map(p => p.region || 'N/A'), 
                showlegend: true
            };

            traces.push(peaksTrace);

            // Añadir anotaciones para los picos principales (top 3)
            const topPeaks = [...peaksData]
                .sort((a, b) => b.intensity - a.intensity)
                .slice(0, 3);

            const annotations = topPeaks.map(peak => ({
                x: peak.ppm,
                y: peak.intensity,
                text: `<b>${peak.region}</b><br>${peak.ppm.toFixed(3)} ppm`, 
                showarrow: true,
                arrowhead: 2,
                arrowsize: 1,
                arrowwidth: 2,
                arrowcolor: '#e74c3c',
                ax: 0,
                ay: -40,
                bgcolor: 'rgba(255, 255, 255, 0.9)',
                bordercolor: '#e74c3c',
                borderwidth: 2,
                borderpad: 4,
                font: { size: 11, color: '#2c3e50' }
            }));

            this.layout.annotations = annotations;
        } else {
            this.currentPeaks = [];
            this.layout.annotations = [];
        }
        
        // Asegurarnos de que los títulos están actualizados
        this.layout.title.text = LanguageManager.t('charts.spectrumTitle');
        this.layout.xaxis.title.text = LanguageManager.t('charts.ppmAxis');
        this.layout.yaxis.title.text = LanguageManager.t('charts.intensityAxis');

        Plotly.react('spectrumChart', traces, this.layout, this.config)
            .then(() => {
                window.APP_LOGGER.debug('Spectrum chart updated successfully');
            })
            .catch(error => {
                window.APP_LOGGER.error('Error updating spectrum chart:', error);
            });
    }

    static getCurrentPeaks() {
        return this.currentPeaks;
    }

    static clearPeaks() {
        if (!this.layout) return; // No hacer nada si no hay layout
        
        this.currentPeaks = [];
        this.layout.annotations = [];
        
        const chartDiv = document.getElementById('spectrumChart'); 
        if (chartDiv && chartDiv.data && chartDiv.data[0]) {
            // Mantenemos solo la traza 0 (espectro) y borramos el resto
            Plotly.react('spectrumChart', [chartDiv.data[0]], this.layout, this.config);
        }
    }

    /**
     * Actualiza el texto del gráfico cuando el idioma cambia.
     */
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

            const updateData = {};
            const traceNames = [];
            
            if (chartDiv.data[0]) {
                traceNames.push(LanguageManager.t('charts.spectrumTrace'));
            }
            if (chartDiv.data[1]) { // Si existe la traza de picos
                traceNames.push(LanguageManager.t('charts.peaksTrace'));
            }
            
            if (traceNames.length > 0) {
                updateData.name = traceNames;
            }

            this.config.locale = lang;
            
            Plotly.update('spectrumChart', updateData, updateLayout)
                .then(() => {
                    return Plotly.react('spectrumChart', chartDiv.data, chartDiv.layout, this.config);
                })
                .then(() => {
                    this.chart = document.getElementById('spectrumChart'); 
                    if (log) window.APP_LOGGER.debug(`Chart translations updated to: ${lang}`);
                })
                .catch(error => {
                    window.APP_LOGGER.error('Error applying chart translations:', error);
                });
                
            this.layout.title.text = updateLayout['title.text'];
            this.layout.xaxis.title.text = updateLayout['xaxis.title.text'];
            this.layout.yaxis.title.text = updateLayout['yaxis.title.text'];

        } catch (error) {
            window.APP_LOGGER.error('Error refreshing chart translations:', error);
        }
    }
    
    static addIntegrationRegion(regionData) {
         const chartDiv = document.getElementById('spectrumChart');
         if (!chartDiv || !chartDiv.layout) {
             window.APP_LOGGER.warn('Chart not ready for adding integration regions');
             return;
         }
        if (!regionData || !Array.isArray(regionData)) {
             window.APP_LOGGER.warn('Invalid region data for integration regions');
             return;
         }
        
        const shapes = regionData.map(region => ({
            type: 'rect',
            x0: region.start,
            x1: region.end,
            y0: 0,
            y1: 1,
            yref: 'paper',
            fillcolor: 'rgba(231, 76, 60, 0.2)',
            line: {
                width: 1,
                color: 'rgba(231, 76, 60, 0.8)'
            },
            opacity: 0.3
        }));
        
        const existingShapes = chartDiv.layout.shapes || [];
        const updatedLayout = {
            shapes: [...existingShapes, ...shapes] 
        };
        
        Plotly.relayout('spectrumChart', updatedLayout)
            .then(() => {
                window.APP_LOGGER.debug('Integration regions added to chart');
            })
            .catch(error => {
                window.APP_LOGGER.error('Error adding integration regions:', error);
            });
    }
    
    static clearIntegrationRegions() {
       const chartDiv = document.getElementById('spectrumChart');
        if (!chartDiv || !chartDiv.layout) {
             window.APP_LOGGER.warn('Chart not ready for clearing integration regions');
             return;
         }
       const updatedLayout = {
            shapes: [] 
       };
        
       Plotly.relayout('spectrumChart', updatedLayout)
            .then(() => {
                window.APP_LOGGER.debug('Integration regions cleared');
            })
            .catch(error => {
                window.APP_LOGGER.error('Error clearing integration regions:', error);
            });
    }
    
    static updateChartTitle(title) {
       const chartDiv = document.getElementById('spectrumChart');
        if (!chartDiv || !chartDiv.layout) {
             window.APP_LOGGER.warn('Chart not ready for title update');
             return;
         }
        
        Plotly.relayout('spectrumChart', { 'title.text': title }) 
            .then(() => {
                window.APP_LOGGER.debug('Chart title updated');
                if (this.layout && this.layout.title) {
                     this.layout.title.text = title;
                 }
            })
            .catch(error => {
                window.APP_LOGGER.error('Error updating chart title:', error);
            });
    }
    
    static exportChart(format = 'png') {
       const chartDiv = document.getElementById('spectrumChart');
        if (!chartDiv) {
             window.APP_LOGGER.error('Cannot export chart: Chart element not found.');
             return Promise.reject('Chart element not found.'); 
         }
       return Plotly.downloadImage('spectrumChart', {
            format: format,
            filename: `rmn_spectrum_${new Date().toISOString().split('T')[0]}`,
            height: 600,
            width: 800,
            scale: 2
       });
    }
    
    static getChartData() {
       const chartDiv = document.getElementById('spectrumChart');
        if (!chartDiv) {
             window.APP_LOGGER.error('Cannot get chart data: Chart element not found.');
             return Promise.reject('Chart element not found.');
         }
       window.APP_LOGGER.warn('getChartData() triggers a JSON download, it does not return data to JS.');
       return Plotly.downloadImage('spectrumChart', {
            format: 'json', 
            filename: 'plotly_chart_data', 
            height: 600,
            width: 800
       });
    }
    
    static resizeChart() {
         const chartDiv = document.getElementById('spectrumChart');
         if (!chartDiv) {
             return; 
         }
        Plotly.Plots.resize(chartDiv) 
            .then(() => {
                window.APP_LOGGER.debug('Chart resized');
            })
            .catch(error => {
                if (error.message && !error.message.includes('Resize must be passed a plot node')) {
                     window.APP_LOGGER.error('Error resizing chart:', error);
                 }
            });
    }

    static async getChartAsBase64() {
        /**
         * Captura el gráfico actual como imagen base64
         * @returns {Promise<string>} - String base64 de la imagen PNG
         */
        const chartDiv = document.getElementById('spectrumChart');
        if (!chartDiv || !chartDiv.data) {
            window.APP_LOGGER.warn('No chart available to capture');
            return null;
        }
        
        try {
            // Usar Plotly.toImage para obtener la imagen como base64
            const imageData = await Plotly.toImage(chartDiv, {
                format: 'png',
                width: 800,
                height: 500,
                scale: 2 // Mejor calidad
            });
            
            window.APP_LOGGER.debug('Chart captured as base64');
            return imageData; // Ya viene como "data:image/png;base64,..."
            
        } catch (error) {
            window.APP_LOGGER.error('Error capturing chart:', error);
            return null;
        }
    }

    /**
     * Método wrapper para compatibilidad con app.js
     * Convierte los resultados del análisis al formato esperado por updateSpectrumChart
     */
    static plotResults(results) {

        // --- ¡ESTA ES LA CORRECCIÓN PARA EL GRÁFICO! ---
        // Si el gráfico no existe (porque 'init' no pudo crearlo), lo crea ahora.
        if (!this.chart && this.initialized) { 
            window.APP_LOGGER.warn('[ChartManager] Chart not found, creating empty chart now...');
            // Usamos un wrapper 'async' para llamar a la función 'async'
            (async () => {
                await this.createEmptyChart();
                // Volvemos a llamar a esta misma función ahora que el gráfico existe
                this.plotResults(results); 
            })();
            return; // Salimos por ahora, la función se volverá a llamar
        }
        // --- FIN DE LA CORRECCIÓN ---

        window.APP_LOGGER.debug('[ChartManager] plotResults llamado con:', results);

        if (!results) {
            window.APP_LOGGER.warn('[ChartManager] No hay resultados para graficar');
            return;
        }

        let spectrumData = null;
        
        if (results.spectrum && results.spectrum.ppm && results.spectrum.intensity) {
            spectrumData = {
                ppm: results.spectrum.ppm,
                intensity: results.spectrum.intensity
            };
        } else if (results.ppm && results.intensity) {
            spectrumData = {
                ppm: results.ppm,
                intensity: results.intensity
            };
        }

        if (!spectrumData || !spectrumData.ppm || !spectrumData.intensity) {
            window.APP_LOGGER.error('[ChartManager] Datos de espectro inválidos:', results);
            if (window.UIManager) {
                UIManager.showNotification(
                    'No se pudieron graficar los datos del espectro',
                    'warning'
                );
            }
            return;
        }

        let peaksData = null;
        
        if (results.peaks && Array.isArray(results.peaks) && results.peaks.length > 0) {
            peaksData = results.peaks.map(peak => ({
                ppm: peak.position || peak.ppm || 0,
                intensity: peak.height || peak.intensity || 0,
                region: peak.region || peak.assignment || 'N/A',
                width: peak.width || 0,
                area: peak.area || 0
            }));
            
            window.APP_LOGGER.debug(`[ChartManager] ${peaksData.length} picos detectados`);
        }

        // Llamada a la función de lógica principal
        this.updateSpectrumChart(spectrumData, peaksData);

        const sampleName = document.getElementById('sampleName');
        if (sampleName && (results.filename || results.sample_name)) {
            sampleName.textContent = results.sample_name || results.filename;
        }

        window.APP_LOGGER.info('[ChartManager] Gráfico actualizado exitosamente');
    }

    /**
     * Limpia el gráfico y resetea a estado inicial
     */
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