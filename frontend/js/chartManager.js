class ChartManager {
    static chart = null;
    static layout = null;
    static config = null;

    static init() {
        this.layout = {
            title: {
                text: 'Espectro de RMN',
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
                    text: 'Intensidad',
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
            scrollZoom: true
        };
        
        // Initialize empty chart
        this.createEmptyChart();
        
        window.APP_LOGGER.info('Chart manager initialized');
    }
    
    static createEmptyChart() {
        const trace = {
            x: [],
            y: [],
            type: 'scatter',
            mode: 'lines',
            line: {
                color: '#3498db',
                width: 1.5
            },
            name: 'Espectro RMN',
            hovertemplate: 'δ: %{x:.2f} ppm<br>Intensidad: %{y:.2f}<extra></extra>'
        };
        
        this.chart = Plotly.newPlot('spectrumChart', [trace], this.layout, this.config);
    }
    
    static updateSpectrumChart(spectrumData) {
        if (!spectrumData || !spectrumData.ppm || !spectrumData.intensity) {
            window.APP_LOGGER.error('Invalid spectrum data for chart update');
            return;
        }
        
        const trace = {
            x: spectrumData.ppm,
            y: spectrumData.intensity,
            type: 'scatter',
            mode: 'lines',
            line: {
                color: '#3498db',
                width: 1.5
            },
            name: 'Espectro RMN',
            hovertemplate: 'δ: %{x:.2f} ppm<br>Intensidad: %{y:.2f}<extra></extra>'
        };
        
        Plotly.react('spectrumChart', [trace], this.layout, this.config)
            .then(() => {
                window.APP_LOGGER.debug('Spectrum chart updated successfully');
            })
            .catch(error => {
                window.APP_LOGGER.error('Error updating spectrum chart:', error);
            });
    }
    static refreshTranslations(log = true) {
        if (!this.chart || !window.LanguageManager) {
            if (log) window.APP_LOGGER.warn('Chart or LanguageManager not ready for translation');
            return;
        }

        try {
            // 1. Obtener las nuevas traducciones
            const newLayout = {
                'title.text': LanguageManager.t('chart.title') || this.layout.title.text,
                'xaxis.title.text': LanguageManager.t('chart.xaxis') || this.layout.xaxis.title.text,
                'yaxis.title.text': LanguageManager.t('chart.yaxis') || this.layout.yaxis.title.text
            };

            const newTrace = {
                name: [LanguageManager.t('chart.traceName') || 'Espectro RMN'],
                hovertemplate: [LanguageManager.t('chart.hover') || 'δ: %{x:.2f} ppm<br>Intensidad: %{y:.2f}<extra></extra>']
            };

            // 2. Actualizar el objeto 'layout' guardado para futuros 'react'
            this.layout.title.text = newLayout['title.text'];
            this.layout.xaxis.title.text = newLayout['xaxis.title.text'];
            this.layout.yaxis.title.text = newLayout['yaxis.title.text'];
            
            // 3. Actualizar el gráfico en vivo
            Plotly.relayout('spectrumChart', newLayout);
            Plotly.restyle('spectrumChart', newTrace);

            if (log) window.APP_LOGGER.debug('Chart translations refreshed');

        } catch (error) {
            window.APP_LOGGER.error('Error refreshing chart translations:', error);
        }
    }
    
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
            ...this.layout,
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
            ...this.layout,
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
            ...this.layout,
            title: {
                ...this.layout.title,
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

// Initialize chart manager when loaded
document.addEventListener('DOMContentLoaded', () => {
    ChartManager.init();
});

// Handle window resize
window.addEventListener('resize', () => {
    if (ChartManager.chart) {
        ChartManager.resizeChart();
    }
});