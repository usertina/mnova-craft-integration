class ChartManager {
    static chart = null;
    static layout = null;
    static config = null;

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
            showlegend: false, hovermode: 'closest'
        };
        
        this.config = {
            responsive: true, displayModeBar: true, displaylogo: false,
            locale: 'es', locales: this.locales,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
            toImageButtonOptions: { format: 'png', filename: 'rmn_spectrum', height: 500, width: 800, scale: 2 },
            scrollZoom: true
        };
        
        // --- CAMBIO ---
        // Esperamos a que el gráfico se cree antes de continuar
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
        
        // --- CAMBIO ---
        // newPlot devuelve una Promesa. La esperamos y asignamos el resultado
        // (el elemento del gráfico) a 'this.chart'.
        this.chart = await Plotly.newPlot('spectrumChart', [trace], this.layout, this.config);
    }
    
    static updateSpectrumChart(spectrumData) {
        if (!spectrumData || !spectrumData.ppm || !spectrumData.intensity) {
            window.APP_LOGGER.error('Invalid spectrum data for chart update');
            return;
        }

        this.chart.data[0].x = spectrumData.ppm;
        this.chart.data[0].y = spectrumData.intensity;
        
        Plotly.react('spectrumChart', this.chart.data, this.chart.layout, this.config)
            .then(() => {
                window.APP_LOGGER.debug('Spectrum chart updated successfully');
            })
            .catch(error => {
                window.APP_LOGGER.error('Error updating spectrum chart:', error);
            });
    }

    static refreshTranslations(lang, log = true) {
        // Esta comprobación ahora FUNCIONARÁ
        if (!this.chart || !window.LanguageManager || !this.chart.data) {
            if (log) window.APP_LOGGER.warn('Chart or LanguageManager not ready for translation');
            return;
        }

        try {
            const newTitle = LanguageManager.t('chart.title') || this.chart.layout.title.text;
            const newXAxis = LanguageManager.t('chart.xaxis') || this.chart.layout.xaxis.title.text;
            const newYAxis = LanguageManager.t('chart.yaxis') || this.chart.layout.yaxis.title.text;
            const newTraceName = LanguageManager.t('chart.traceName') || this.chart.data[0].name;
            const newHover = LanguageManager.t('chart.hover') || this.chart.data[0].hovertemplate;

            this.chart.layout.title.text = newTitle;
            this.chart.layout.xaxis.title.text = newXAxis;
            this.chart.layout.yaxis.title.text = newYAxis;
            
            if (this.config.locale !== lang) {
                this.config.locale = lang; 
            }

            this.chart.data[0].name = newTraceName;
            this.chart.data[0].hovertemplate = newHover;
            
            // Usamos newPlot para forzar la traducción de los iconos
            Plotly.newPlot('spectrumChart', this.chart.data, this.chart.layout, this.config)
                .then(() => {
                     this.chart = document.getElementById('spectrumChart'); // Re-asignamos
                     if (log) window.APP_LOGGER.debug(`Chart translations and locale REBUILT to: ${lang}`);
                })
                .catch(error => {
                     window.APP_LOGGER.error('Error applying chart translations:', error);
                });

            this.layout.title.text = newTitle;
            this.layout.xaxis.title.text = newXAxis;
            this.layout.yaxis.title.text = newYAxis;

        } catch (error) {
            window.APP_LOGGER.error('Error refreshing chart translations:', error);
        }
    }
    
    // ... (El resto de funciones: addIntegrationRegion, etc. no cambian) ...
    
    static addIntegrationRegion(regionData) {
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
        
        const updatedLayout = {
            ...this.chart.layout,
            shapes: shapes
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
        const updatedLayout = {
            ...this.chart.layout,
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
        const updatedLayout = {
            ...this.chart.layout,
            title: {
                ...this.chart.layout.title,
                text: title
            }
        };
        
        Plotly.relayout('spectrumChart', { title: updatedLayout.title })
            .then(() => {
                window.APP_LOGGER.debug('Chart title updated');
            })
            .catch(error => {
                window.APP_LOGGER.error('Error updating chart title:', error);
            });
    }
    
    static exportChart(format = 'png') {
        return Plotly.downloadImage('spectrumChart', {
            format: format,
            filename: `rmn_spectrum_${new Date().toISOString().split('T')[0]}`,
            height: 600,
            width: 800,
            scale: 2
        });
    }
    
    static getChartData() {
        return new Promise((resolve, reject) => {
            Plotly.downloadImage('spectrumChart', {
                format: 'json',
                height: 600,
                width: 800
            })
            .then(data => resolve(data))
            .catch(error => {
                window.APP_LOGGER.error('Error getting chart data:', error);
                reject(error);
            });
        });
    }
    
    static resizeChart() {
        Plotly.Plots.resize('spectrumChart')
            .then(() => {
                window.APP_LOGGER.debug('Chart resized');
            })
            .catch(error => {
                window.APP_LOGGER.error('Error resizing chart:', error);
            });
    }
}

// --- CAMBIO ---
// HEMOS BORRADO EL 'DOMContentLoaded' LISTENER DE AQUÍ
// Y EL 'resize' LISTENER