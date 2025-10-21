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

    static async exportReport(results, format = 'pdf') {
        try {
            const response = await fetch(`${this.baseURL}/export`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    results: results,
                    format: format
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Export failed');
            }
            
            // Handle file download
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
}
