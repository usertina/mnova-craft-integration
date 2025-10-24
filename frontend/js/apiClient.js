class APIClient {
    static get baseURL() {
        return window.APP_CONFIG?.apiBaseURL || 'http://localhost:5000/api';
    }

    static async checkConnection() {
        try {
            const response = await fetch(`${this.baseURL}/health`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                timeout: 5000
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            return data;
            
        } catch (error) {
            window.APP_LOGGER.error('Connection check failed:', error);
            throw new Error('No se pudo conectar al servidor de análisis');
        }
    }

    static async analyzeSpectrum(file, parameters) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('parameters', JSON.stringify(parameters));
        
        try {
            const response = await fetch(`${this.baseURL}/analyze`, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || `Error ${response.status}`);
            }
            
            window.APP_LOGGER.debug('Analysis completed:', result);
            return result;
            
        } catch (error) {
            window.APP_LOGGER.error('Analysis request failed:', error);
            throw new Error(`Análisis falló: ${error.message}`);
        }
    }

    static async batchAnalyze(files, parameters) {
        const formData = new FormData();
        
        Array.from(files).forEach(file => {
            formData.append('files', file);
        });
        formData.append('parameters', JSON.stringify(parameters));
        
        try {
            const response = await fetch(`${this.baseURL}/batch`, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || `Error ${response.status}`);
            }
            
            return result;
            
        } catch (error) {
            window.APP_LOGGER.error('Batch analysis failed:', error);
            throw new Error(`Análisis por lotes falló: ${error.message}`);
        }
    }

    static async exportReport(results, format = 'pdf', chartImage = null) {
        try {
            // 🆕 Obtener el idioma actual
            const currentLang = LanguageManager.getCurrentLanguage();
            
            // Preparar el payload
            const payload = {
                results: results,
                format: format,
                lang: currentLang  // 🆕 Enviar idioma al backend
            };

            window.APP_LOGGER.debug(`Exporting report in language: ${currentLang}`);

            
            // Añadir la imagen del gráfico si existe
            if (chartImage) {
                payload.chart_image = chartImage; // Base64 string
                window.APP_LOGGER.debug('Chart image included in export payload');
            }
            
            const response = await fetch(`${this.baseURL}/export`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Export failed');
            }
            
            // Manejar descarga del archivo
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `rmn_analysis_${new Date().toISOString().split('T')[0]}.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            return true;
            
        } catch (error) {
            window.APP_LOGGER.error('Export failed:', error);
            throw new Error(`Exportación falló: ${error.message}`);
        }
    }

    static async getResult(filename) {
        try {
            const response = await fetch(`${this.baseURL}/result/${filename}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            window.APP_LOGGER.debug('Result loaded:', filename);
            return data;
            
        } catch (error) {
            window.APP_LOGGER.error('Failed to load result:', error);
            throw new Error(`No se pudo cargar el análisis: ${error.message}`);
        }
    }
/**
 * Eliminar un análisis específico
 */
    static async deleteAnalysis(filename) {
        try {
            const response = await fetch(`${this.baseURL}/analysis/${encodeURIComponent(filename)}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || `Error ${response.status}`);
            }
            
            window.APP_LOGGER.debug('Analysis deleted:', filename);
            return result;
            
        } catch (error) {
            window.APP_LOGGER.error('Failed to delete analysis:', error);
            throw new Error(`No se pudo eliminar el análisis: ${error.message}`);
        }
    }

    /**
     * Eliminar TODOS los análisis
     */
    static async clearAllHistory() {
        try {
            const response = await fetch(`${this.baseURL}/analysis/clear-all`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || `Error ${response.status}`);
            }
            
            window.APP_LOGGER.info(`All history cleared: ${result.deleted_count} files deleted`);
            return result;
            
        } catch (error) {
            window.APP_LOGGER.error('Failed to clear all history:', error);
            throw new Error(`No se pudo limpiar el historial: ${error.message}`);
        }
    }

    /**
     * Obtener lista de análisis disponibles
     */
    static async getAnalysisList() {
        try {
            const response = await fetch(`${this.baseURL}/analysis`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            window.APP_LOGGER.debug(`Analysis list loaded: ${data.total} items`);
            return data;
            
        } catch (error) {
            window.APP_LOGGER.error('Failed to load analysis list:', error);
            throw new Error(`No se pudo cargar el historial: ${error.message}`);
        }
    }
}
