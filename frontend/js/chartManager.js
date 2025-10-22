// ============================================================================
// CHART MANAGER - CraftRMN Pro - VERSIÓN MEJORADA
// Gestión de gráficos con Plotly + Mostrar picos detectados
// ✅ Actualizado para analyzer_improved.py
// ============================================================================

class ChartManager {
    static chart = null;
    static layout = null;
    static config = null;
    static currentPeaks = []; // 🆕 Almacenar picos actuales

    // --- Definimos las traducciones AQUÍ ---
    static locales = {
        'es': {
            dictionary: {
                'Autoscale': 'Autoescala', 'Box Select': 'Selección de caja', 'Download plot as a png': 'Descargar gráfico como PNG', 'Download plot': 'Descargar gráfico', 'Lasso Select': 'Selección de lazo', 'Pan': 'Desplazar', 'Reset': 'Restablecer', 'Reset axes': 'Restablecer ejes', 'Show closest data on hover': 'Mostrar datos cercanos', 'Zoom': 'Zoom', 'Zoom in': 'Acercar', 'Zoom out': 'Alejar', 'close:': 'cierre:', 'trace': 'traza', 'lat:': 'lat:', 'lon:': 'lon:', 'max:': 'máx:', 'mean:': 'media:', 'median:': 'mediana:', 'min:': 'mín:', 'new text': 'nuevo texto'
            },
            format: {
                days: ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'], shortDays: ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'], months: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'], shortMonths: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'], date: '%d/%m/%Y'
            }
        },
        'eu': {
            dictionary: {
                'Autoscale': 'Autoeskala', 'Box Select': 'Kutxa hautapena', 'Download plot as a png': 'Deskargatu grafikoa PNG gisa', 'Download plot': 'Deskargatu grafikoa', 'Lasso Select': 'Lazo hautapena', 'Pan': 'Mugitu', 'Reset': 'Berrezarri', 'Reset axes': 'Berrezarri ardatzak', 'Show closest data on hover': 'Erakutsi datu hurbilenak', 'Zoom': 'Zoom', 'Zoom in': 'Hurbildu', 'Zoom out': 'Urrundu'
            },
            format: {
                days: ['Igandea', 'Astelehena', 'Asteartea', 'Asteazkena', 'Osteguna', 'Ostirala', 'Larunbata'], shortDays: ['Ig', 'Al', 'Ar', 'Az', 'Og', 'Or', 'Lr'], months: ['Urtarrila', 'Otsaila', 'Martxoa', 'Apirila', 'Maiatza', 'Ekaina', 'Uztaila', 'Abuztua', 'Iraila', 'Urria', 'Azaroa', 'Abendua'], shortMonths: ['Urt', 'Ots', 'Mar', 'Api', 'Mai', 'Eka', 'Uzt', 'Abu', 'Ira', 'Urr', 'Aza', 'Abe'], date: '%Y/%m/%d'
            }
        }
    };

    /**
     * FUNCIÓN MODIFICADA: Ahora es 'async'
     */
    static async init() {
        this.layout = {
            title: { text: 'Espectro de RMN', font: { size: 16, color: '#2c3e50' } },
            xaxis: {
                title: { text: 'Desplazamiento (ppm)', font: { size: 14, color: '#2c3e50' } },
                autorange: 'reversed', gridcolor: '#f0f0f0', zerolinecolor: '#f0f0f0', showline: true, linecolor: '#bdc3c7', mirror: true
            },
            yaxis: {
                title: { text: 'Intensidad', font: { size: 14, color: '#2c3e50' } },
                gridcolor: '#f0f0f0', zerolinecolor: '#f0f0f0', showline: true, linecolor: '#bdc3c7', mirror: true
            },
            plot_bgcolor: 'white', paper_bgcolor: 'white',
            font: { family: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif', color: '#2c3e50' },
            margin: { t: 60, r: 40, b: 60, l: 60 },
            showlegend: true, // 🆕 Mostrar leyenda para picos
            legend: { x: 1, y: 1, xanchor: 'right', yanchor: 'top' },
            hovermode: 'closest',
            dragmode: 'zoom' // Opcional: define el modo inicial, pero la barra permite cambiar
        };
        
        this.config = {
            responsive: true, displayModeBar: true, displaylogo: false,
            locale: 'es', locales: this.locales,
            // --- CAMBIO AQUÍ: Eliminado 'pan2d' de la lista ---
            modeBarButtonsToRemove: ['lasso2d', 'select2d'], 
            toImageButtonOptions: { format: 'png', filename: 'rmn_spectrum', height: 500, width: 800, scale: 2 },
            scrollZoom: true // Asegura que el zoom con rueda está activo
        };
        
        await this.createEmptyChart();
        
        window.APP_LOGGER.info('Chart manager initialized');
    }
    
    /**
     * FUNCIÓN MODIFICADA: Ahora es 'async'
     */
    static async createEmptyChart() {
        const trace = {
            x: [], y: [], type: 'scatter', mode: 'lines',
            line: { color: '#3498db', width: 1.5 },
            name: 'Espectro de RMN',
            hovertemplate: 'ppm: %{x:.2f}<br>Intensidad: %{y:.2f}<extra></extra>'
        };
        
        this.chart = await Plotly.newPlot('spectrumChart', [trace], this.layout, this.config);
    }
    
    // 🆕 NUEVA FUNCIÓN: Actualizar espectro con picos detectados
    static updateSpectrumChart(spectrumData, peaksData = null) {
        if (!spectrumData || !spectrumData.ppm || !spectrumData.intensity) {
            window.APP_LOGGER.error('Invalid spectrum data for chart update');
            return;
        }

        // Trace principal del espectro
        const spectrumTrace = {
            x: spectrumData.ppm,
            y: spectrumData.intensity,
            type: 'scatter',
            mode: 'lines',
            line: { color: '#3498db', width: 1.5 },
            name: 'Espectro de RMN',
            hovertemplate: 'ppm: %{x:.2f}<br>Intensidad: %{y:.2f}<extra></extra>'
        };

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
                mode: 'markers+text',
                marker: {
                    color: '#e74c3c',
                    size: 10,
                    symbol: 'circle',
                    line: { color: 'white', width: 2 }
                },
                text: peaksData.map(p => `${p.ppm.toFixed(2)}`),
                textposition: 'top center',
                textfont: { size: 10, color: '#e74c3c' },
                name: 'Picos Detectados',
                hovertemplate: '<b>Pico</b><br>' +
                               'ppm: %{x:.3f}<br>' +
                               'Intensidad: %{y:.1f}<br>' +
                               '<extra></extra>',
                customdata: peaksData.map(p => p.region),
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
        
        Plotly.react('spectrumChart', traces, this.layout, this.config)
            .then(() => {
                window.APP_LOGGER.debug('Spectrum chart updated successfully');
            })
            .catch(error => {
                window.APP_LOGGER.error('Error updating spectrum chart:', error);
            });
    }

    // 🆕 NUEVA FUNCIÓN: Obtener picos actuales
    static getCurrentPeaks() {
        return this.currentPeaks;
    }

    // 🆕 NUEVA FUNCIÓN: Limpiar picos
    static clearPeaks() {
        this.currentPeaks = [];
        this.layout.annotations = [];
        
        // Use document.getElementById to ensure we have the latest reference
        const chartDiv = document.getElementById('spectrumChart'); 
        if (chartDiv && chartDiv.data && chartDiv.data[0]) {
            // Mantener solo el trace del espectro
            const spectrumTrace = chartDiv.data[0];
            Plotly.react('spectrumChart', [spectrumTrace], this.layout, this.config);
        } else if (this.chart && this.chart.data && this.chart.data[0]){
             // Fallback to the stored chart object if needed
             const spectrumTrace = this.chart.data[0];
             Plotly.react('spectrumChart', [spectrumTrace], this.layout, this.config);
        }
    }

    static refreshTranslations(lang, log = true) {
        // Use document.getElementById to ensure we have the latest reference
        const chartDiv = document.getElementById('spectrumChart'); 
        if (!chartDiv || !window.LanguageManager || !chartDiv.layout || !chartDiv.data) {
             if (log) window.APP_LOGGER.warn('Chart or LanguageManager not ready for translation');
             return;
        }


        try {
            // Get current titles/labels directly from the live chart object
            const currentLayout = chartDiv.layout;
            const currentData = chartDiv.data;

            const newTitle = LanguageManager.t('chart.title') || currentLayout.title.text;
            const newXAxis = LanguageManager.t('chart.xaxis') || currentLayout.xaxis.title.text;
            const newYAxis = LanguageManager.t('chart.yaxis') || currentLayout.yaxis.title.text;
            const newTraceName = LanguageManager.t('chart.traceName') || (currentData[0] ? currentData[0].name : 'Espectro');
            const newHover = LanguageManager.t('chart.hover') || (currentData[0] ? currentData[0].hovertemplate : '');
            
            // Update the layout object we will pass to Plotly
            const updateLayout = {
                 'title.text': newTitle,
                 'xaxis.title.text': newXAxis,
                 'yaxis.title.text': newYAxis
            };

            // Update the data object we will pass to Plotly
            const updateData = {};
            if (currentData[0]) {
                 updateData['name'] = newTraceName; // Update trace 0 name
                 updateData['hovertemplate'] = newHover; // Update trace 0 hovertemplate
            }
             // Update peak trace name if it exists
             if (currentData[1]) {
                  const newPeakTraceName = LanguageManager.t('chart.peakTraceName') || currentData[1].name;
                  updateData['name'] = [newTraceName, newPeakTraceName]; // Update both trace names
             }


             // Update config locale
            if (this.config.locale !== lang) {
                 this.config.locale = lang; 
            }

            // Apply layout and data updates using Plotly.update
            Plotly.update('spectrumChart', updateData, updateLayout)
                 .then(() => {
                     // Force re-render with new locale config using Plotly.react
                     // This is often needed to update the modebar button tooltips
                     return Plotly.react('spectrumChart', chartDiv.data, chartDiv.layout, this.config);
                 })
                 .then(() => {
                     this.chart = document.getElementById('spectrumChart'); // Update internal reference
                     if (log) window.APP_LOGGER.debug(`Chart translations updated to: ${lang}`);
                 })
                 .catch(error => {
                      window.APP_LOGGER.error('Error applying chart translations:', error);
                 });
                 
             // Also update our stored layout object for consistency
            this.layout.title.text = newTitle;
            this.layout.xaxis.title.text = newXAxis;
            this.layout.yaxis.title.text = newYAxis;

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
        
        // Add to existing shapes if any
        const existingShapes = chartDiv.layout.shapes || [];
        const updatedLayout = {
             shapes: [...existingShapes, ...shapes] // Merge existing and new shapes
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
             shapes: [] // Set shapes to an empty array
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
        
        Plotly.relayout('spectrumChart', { 'title.text': title }) // More direct way to update title
            .then(() => {
                window.APP_LOGGER.debug('Chart title updated');
                // Update our stored layout too
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
              return Promise.reject('Chart element not found.'); // Return a rejected promise
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
        // This Plotly method downloads a JSON file, it doesn't return the data directly
        // If you need the data in JS, access chartDiv.data and chartDiv.layout
        const chartDiv = document.getElementById('spectrumChart');
         if (!chartDiv) {
              window.APP_LOGGER.error('Cannot get chart data: Chart element not found.');
              return Promise.reject('Chart element not found.');
         }
        window.APP_LOGGER.warn('getChartData() triggers a JSON download, it does not return data to JS.');
        return Plotly.downloadImage('spectrumChart', {
            format: 'json', // This format actually downloads a JSON file
            filename: 'plotly_chart_data', 
            height: 600,
            width: 800
        });
        
        // If you actually want the data in JS:
        // return Promise.resolve({ data: chartDiv.data, layout: chartDiv.layout });
    }
    
    static resizeChart() {
         const chartDiv = document.getElementById('spectrumChart');
         if (!chartDiv) {
              // No need to log error here, might happen during initial load
              return; 
         }
        Plotly.Plots.resize(chartDiv) // Pass the element reference
            .then(() => {
                window.APP_LOGGER.debug('Chart resized');
            })
            .catch(error => {
                // Avoid logging errors if chart wasn't fully rendered yet
                if (error.message && !error.message.includes('Resize must be passed a plot node')) {
                     window.APP_LOGGER.error('Error resizing chart:', error);
                }
            });
    }
}

