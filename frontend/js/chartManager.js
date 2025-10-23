// ============================================================================
// CHART MANAGER - CraftRMN Pro - VERSIÓN CORREGIDA
// Gestión de gráficos con Plotly + Traducciones dinámicas
// ✅ ¡CORREGIDO! Usa LanguageManager para los títulos y ejes.
// ✅ ¡CORREGIDO! Usa los nombres de datos correctos (.ppm e .intensity)
// ============================================================================

class ChartManager {
    static chart = null;
    static layout = null;
    static config = null;
    static currentPeaks = []; 

    /**
     * FUNCIÓN MODIFICADA: Ahora es 'async' y usa LanguageManager
     */
    static async init() {
        // Usamos LanguageManager.t() para obtener el texto traducido
        this.layout = {
            title: { text: LanguageManager.t('charts.spectrumTitle'), font: { size: 16, color: '#2c3e50' } },
            xaxis: {
                title: { text: LanguageManager.t('charts.ppmAxis'), font: { size: 14, color: '#2c3e50' } },
                autorange: 'reversed', gridcolor: '#f0f0f0', zerolinecolor: '#f0f0f0', showline: true, linecolor: '#bdc3c7', mirror: true
            },
            yaxis: {
                title: { text: LanguageManager.t('charts.intensityAxis'), font: { size: 14, color: '#2c3e50' } },
                gridcolor: '#f0f0f0', zerolinecolor: '#f0f0f0', showline: true, linecolor: '#bdc3c7', mirror: true
            },
            plot_bgcolor: 'white', paper_bgcolor: 'white',
            font: { family: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif', color: '#2c3e50' },
            margin: { t: 60, r: 40, b: 60, l: 60 },
            showlegend: true, 
            legend: { x: 1, y: 1, xanchor: 'right', yanchor: 'top' },
            hovermode: 'x unified', // 'x unified' es a menudo mejor para espectros
            dragmode: 'zoom'
        };
        
        this.config = {
            responsive: true, displayModeBar: true, displaylogo: false,
            locale: LanguageManager.currentLang || 'es', 
            modeBarButtonsToRemove: ['lasso2d', 'select2d'], 
            toImageButtonOptions: { format: 'png', filename: 'rmn_spectrum', height: 500, width: 800, scale: 2 },
            scrollZoom: true
        };
        
        await this.createEmptyChart();
        
        window.APP_LOGGER.info('Chart manager initialized');
    }
    
    /**
     * FUNCIÓN MODIFICADA: Ahora es 'async' y usa LanguageManager
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
    
    // ========================================================================
    // --- ¡FUNCIÓN CORREGIDA! ---
    // ========================================================================
    // 🆕 FUNCIÓN MODIFICADA: Picos + Traducciones + Corrección de datos (.ppm / .intensity)
    static updateSpectrumChart(spectrumData, peaksData = null) {
        
        // --- CAMBIO AQUÍ ---
        // Volvemos a la comprobación original que tenías.
        if (!spectrumData || !spectrumData.ppm || !spectrumData.intensity) {
            // Este es el error que estás viendo, pero lo cambiamos para que sea más claro
            window.APP_LOGGER.error(`Invalid spectrum data for chart update. Esperando {ppm: [], intensity: []}. Recibido: ${JSON.stringify(spectrumData)}`);
            return;
        }

        // Trace principal del espectro
        const spectrumTrace = {
            // --- CAMBIO AQUÍ ---
            x: spectrumData.ppm,     // <-- CORREGIDO (antes era .x)
            y: spectrumData.intensity, // <-- CORREGIDO (antes era .y)
            type: 'scatter',
            mode: 'lines',
            line: { color: '#3498db', width: 1.5 },
            name: LanguageManager.t('charts.spectrumTrace'), 
            hovertemplate: 'ppm: %{x:.2f}<br>Intensidad: %{y:.2f}<extra></extra>'
        };
        // ========================================================================
        // --- FIN DE LA CORRECCIÓN ---
        // ========================================================================

        const traces = [spectrumTrace];

        // 🆕 Si hay picos detectados, añadirlos
        if (peaksData && Array.isArray(peaksData) && peaksData.length > 0) {
            window.APP_LOGGER.debug(`Adding ${peaksData.length} peaks to chart`);
            
            this.currentPeaks = peaksData;

            // Trace para los picos
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

            // 🆕 Añadir anotaciones para los picos principales (top 3)
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
        
        // Asegurarnos de que los títulos del layout están en el idioma correcto
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

    // (Tu función getCurrentPeaks está bien)
    static getCurrentPeaks() {
        return this.currentPeaks;
    }

    // (Tu función clearPeaks está bien, pero la simplifico)
    static clearPeaks() {
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
     * @param {string} lang - El nuevo código de idioma (ej. 'en', 'es', 'eu')
     */
    static refreshTranslations(lang, log = true) {
        const chartDiv = document.getElementById('spectrumChart'); 
        if (!chartDiv || !window.LanguageManager || !chartDiv.layout || !chartDiv.data) {
            if (log) window.APP_LOGGER.warn('Chart or LanguageManager not ready for translation');
            return;
        }

        try {
            // 1. Preparamos las actualizaciones del Layout (Títulos, Ejes)
            const updateLayout = {
                'title.text': LanguageManager.t('charts.spectrumTitle'),
                'xaxis.title.text': LanguageManager.t('charts.ppmAxis'),
                'yaxis.title.text': LanguageManager.t('charts.intensityAxis')
            };

            // 2. Preparamos las actualizaciones de las Trazas (Leyenda)
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

            // 3. Actualizamos el 'locale' en la configuración
            this.config.locale = lang;
            
            // 4. Aplicamos los cambios
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
    
    // (El resto de tus funciones: addIntegrationRegion, clearIntegrationRegions, etc. están bien)
    
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
}