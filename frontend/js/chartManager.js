class ChartManager {
    static chart = null;
    static layout = null;
    static config = null;

    static init() {
        this.updateLayout();
        this.setupConfig();
        this.createEmptyChart();
        
        window.APP_LOGGER?.info('Chart manager initialized');
    }
    
    static updateLayout() {
        // Función mejorada para obtener traducciones
        const getTranslation = (key, fallback) => {
            try {
                if (typeof LanguageManager === 'undefined' || !LanguageManager.t) {
                    return fallback;
                }
                const translation = LanguageManager.t(key);
                // Verificar que la traducción sea una cadena válida
                return (translation && typeof translation === 'string') ? translation : fallback;
            } catch (e) {
                console.warn(`Translation error for key "${key}":`, e);
                return fallback;
            }
        };
        
        this.layout = {
            title: {
                text: getTranslation('chart.title', 'Espectro de RMN'),
                font: {
                    size: 16,
                    color: '#2c3e50'
                }
            },
            xaxis: {
                title: {
                    text: 'δ (ppm)',
                    font: {
                        size: 14,
                        color: '#2c3e50'
                    }
                },
                autorange: 'reversed',
                gridcolor: '#f0f0f0',
                zerolinecolor: '#f0f0f0',
                showline: true,
                linecolor: '#bdc3c7',
                mirror: true
            },
            yaxis: {
                title: {
                    text: getTranslation('chart.intensity', 'Intensidad'),
                    font: {
                        size: 14,
                        color: '#2c3e50'
                    }
                },
                gridcolor: '#f0f0f0',
                zerolinecolor: '#f0f0f0',
                showline: true,
                linecolor: '#bdc3c7',
                mirror: true
            },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            font: { 
                family: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
                color: '#2c3e50'
            },
            margin: { t: 60, r: 40, b: 60, l: 60 },
            showlegend: false,
            hovermode: 'closest'
        };
    }
    
    static setupConfig() {
        let currentLang = 'es';
        try {
            if (typeof LanguageManager !== 'undefined' && LanguageManager.getCurrentLanguage) {
                const lang = LanguageManager.getCurrentLanguage();
                currentLang = (lang && typeof lang === 'string') ? lang : 'es';
            }
        } catch (e) {
            console.warn('Error getting current language:', e);
            currentLang = 'es';
        }
        
        this.config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
            toImageButtonOptions: {
                format: 'png',
                filename: 'rmn_spectrum',
                height: 500,
                width: 800,
                scale: 2
            },
            scrollZoom: true,
            locale: currentLang
        };
        
        // Configurar locale globalmente
        if (typeof Plotly !== 'undefined') {
            try {
                Plotly.setPlotConfig({ locale: currentLang });
            } catch (e) {
                console.warn('Could not set Plotly locale:', e);
            }
        }
    }
    
    static createEmptyChart() {
        const getTranslation = (key, fallback) => {
            try {
                if (typeof LanguageManager === 'undefined' || !LanguageManager.t) {
                    return fallback;
                }
                const translation = LanguageManager.t(key);
                return (translation && typeof translation === 'string') ? translation : fallback;
            } catch (e) {
                console.warn(`Translation error for key "${key}":`, e);
                return fallback;
            }
        };
        
        const trace = {
            x: [],
            y: [],
            type: 'scatter',
            mode: 'lines',
            line: {
                color: '#3498db',
                width: 1.5
            },
            name: getTranslation('chart.spectrum', 'Espectro RMN'),
            hovertemplate: 'δ: %{x:.2f} ppm<br>' + 
                          getTranslation('chart.intensity', 'Intensidad') + 
                          ': %{y:.2f}<extra></extra>'
        };
        
        const chartDiv = document.getElementById('spectrumChart');
        if (!chartDiv) {
            console.error('Chart container not found');
            return;
        }
        
        this.chart = Plotly.newPlot('spectrumChart', [trace], this.layout, this.config);
    }
    
    static updateSpectrumChart(spectrumData) {
        if (!spectrumData || !spectrumData.ppm || !spectrumData.intensity) {
            window.APP_LOGGER?.error('Invalid spectrum data for chart update');
            return;
        }
        
        const getTranslation = (key, fallback) => {
            try {
                if (typeof LanguageManager === 'undefined' || !LanguageManager.t) {
                    return fallback;
                }
                const translation = LanguageManager.t(key);
                return (translation && typeof translation === 'string') ? translation : fallback;
            } catch (e) {
                console.warn(`Translation error for key "${key}":`, e);
                return fallback;
            }
        };
        
        const trace = {
            x: spectrumData.ppm,
            y: spectrumData.intensity,
            type: 'scatter',
            mode: 'lines',
            line: {
                color: '#3498db',
                width: 1.5
            },
            name: getTranslation('chart.spectrum', 'Espectro RMN'),
            hovertemplate: 'δ: %{x:.2f} ppm<br>' + 
                          getTranslation('chart.intensity', 'Intensidad') + 
                          ': %{y:.2f}<extra></extra>'
        };
        
        Plotly.react('spectrumChart', [trace], this.layout, this.config)
            .then(() => {
                window.APP_LOGGER?.debug('Spectrum chart updated successfully');
            })
            .catch(error => {
                window.APP_LOGGER?.error('Error updating spectrum chart:', error);
            });
    }
    
    static refreshTranslations() {
        this.updateLayout();
        this.setupConfig();
        
        if (this.chart) {
            const chartDiv = document.getElementById('spectrumChart');
            if (chartDiv && chartDiv.data && chartDiv.data.length > 0) {
                Plotly.react('spectrumChart', chartDiv.data, this.layout, this.config);
            } else {
                this.createEmptyChart();
            }
        }
    }
    
    static resizeChart() {
        if (typeof Plotly !== 'undefined' && Plotly.Plots) {
            Plotly.Plots.resize('spectrumChart')
                .then(() => {
                    window.APP_LOGGER?.debug('Chart resized');
                })
                .catch(error => {
                    window.APP_LOGGER?.error('Error resizing chart:', error);
                });
        }
    }
}

// Initialize chart manager when loaded
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        ChartManager.init();
    }, 200);
});

// Handle window resize
window.addEventListener('resize', () => {
    if (ChartManager.chart) {
        ChartManager.resizeChart();
    }
});