class APIClient {
    static get baseURL() {
        // Asegura que CURRENT_COMPANY_PROFILE exista, aunque aquí no se use directamente
        if (typeof CURRENT_COMPANY_PROFILE === 'undefined') {
            console.warn("CURRENT_COMPANY_PROFILE no está definido aún.");
        }
        // Usar el origen actual sin '/api' al final, lo añadimos en cada endpoint
        return window.location.origin;
    }

    /**
     * ✅ NUEVO: Obtiene el company_id del perfil actual
     */
    static getCompanyId() {
        if (!window.CURRENT_COMPANY_PROFILE || !window.CURRENT_COMPANY_PROFILE.company_id) {
            throw new Error('No company profile loaded');
        }
        return window.CURRENT_COMPANY_PROFILE.company_id;
    }

    /**
     * ✅ NUEVO: Headers comunes para todas las peticiones
     */
    static getHeaders() {
        return {
            'Content-Type': 'application/json'
        };
    }

    static async checkConnection() {
        try {
            const response = await fetch(`${this.baseURL}/api/health`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            window.APP_LOGGER.info('Conexión con servidor OK:', data.version);
            return data;

        } catch (error) {
            window.APP_LOGGER.error('Connection check failed:', error);
            const errorMsg = LanguageManager?.t('errors.connectionFailed') || 'No se pudo conectar al servidor de análisis';
            throw new Error(errorMsg);
        }
    }

    static async analyzeSpectrum(file, parameters) {
        // Asegurarse de que tenemos el perfil de la empresa actual
        if (!CURRENT_COMPANY_PROFILE || !CURRENT_COMPANY_PROFILE.company_id) {
            const errorMsg = LanguageManager?.t('errors.noCompanySelected') || 'No se ha seleccionado una empresa.';
            window.APP_LOGGER.error('analyzeSpectrum: No company selected.');
            throw new Error(errorMsg);
        }

        const formData = new FormData();
        formData.append('file', file);
        
        if (parameters) {
            formData.append('parameters', JSON.stringify(parameters));
        }
        
        // ¡AÑADIR COMPANY_ID!
        formData.append('company_id', CURRENT_COMPANY_PROFILE.company_id);

        try {
            const response = await fetch(`${this.baseURL}/api/analyze`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                const backendError = result.error || `Error ${response.status}`;
                const clientErrorMsg = LanguageManager?.t('errors.analysisFailed', { error: backendError }) || `Error en análisis: ${backendError}`;
                throw new Error(clientErrorMsg);
            }

            window.APP_LOGGER.debug(`Analysis successful for company ${CURRENT_COMPANY_PROFILE.company_id}:`, result);
            return result;

        } catch (error) {
            window.APP_LOGGER.error('Analysis request failed:', error);
            throw error;
        }
    }

    /**
     * ✅ CORREGIDO: Obtiene el historial de mediciones
     */
    static async getHistory(page = 1, pageSize = 50, searchTerm = '') {
        try {
            const companyId = this.getCompanyId(); // ✅ Ahora existe
            
            const params = new URLSearchParams({
                company_id: companyId,
                page: page.toString(),
                page_size: pageSize.toString()
            });
            
            if (searchTerm) {
                params.append('search', searchTerm);
            }

            window.APP_LOGGER.debug(`Fetching history: ${this.baseURL}/api/history?${params}`);

            const response = await fetch(`${this.baseURL}/api/history?${params}`, {
                method: 'GET',
                headers: this.getHeaders() // ✅ Ahora existe
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }

            window.APP_LOGGER.debug(`History loaded: ${data.measurements?.length || 0} items`);
            return data;

        } catch (error) {
            window.APP_LOGGER.error('Failed to load history:', error);
            throw new Error(
                LanguageManager?.t('errors.historyLoadFailed') || 
                'No se pudo cargar el historial'
            );
        }
    }

    /**
     * Exporta datos con branding de la empresa
     */
    static async exportData(exportConfig) {
        if (!CURRENT_COMPANY_PROFILE || !CURRENT_COMPANY_PROFILE.company_id) {
            const errorMsg = LanguageManager?.t('errors.noCompanySelected') || 'No se ha seleccionado una empresa.';
            window.APP_LOGGER.error('exportData: No company selected.');
            throw new Error(errorMsg);
        }

        const requestBody = {
            ...exportConfig,
            company_id: CURRENT_COMPANY_PROFILE.company_id,
            company_name: CURRENT_COMPANY_PROFILE.company_name,
            branding_info: {
                logo_url: CURRENT_COMPANY_PROFILE.logo_url,
                primary_color: CURRENT_COMPANY_PROFILE.primary_color,
                secondary_color: CURRENT_COMPANY_PROFILE.secondary_color,
                language: CURRENT_COMPANY_PROFILE.language
            },
            lang: LanguageManager?.currentLang || 'es'
        };

        try {
            const response = await fetch(`${this.baseURL}/api/export`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const errorResult = await response.json().catch(() => ({ error: `Error ${response.status}` }));
                throw new Error(errorResult.error);
            }

            // Descargar el archivo
            const blob = await response.blob();
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `export_${CURRENT_COMPANY_PROFILE.company_id}_${Date.now()}.${exportConfig.format || 'bin'}`;

            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
                if (filenameMatch && filenameMatch.length > 1) {
                    filename = filenameMatch[1];
                }
            }

            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();

            window.APP_LOGGER.info(`Export successful: ${filename}`);
            return { success: true, filename };

        } catch (error) {
            window.APP_LOGGER.error('Export failed:', error);
            const errorMsg = LanguageManager?.t('errors.exportFailed', { error: error.message }) || `Error al exportar: ${error.message}`;
            throw new Error(errorMsg);
        }
    }

    /**
     * Limpia todo el historial de la empresa actual
     */
    static async clearAllHistory() {
        if (!CURRENT_COMPANY_PROFILE || !CURRENT_COMPANY_PROFILE.company_id) {
            const errorMsg = LanguageManager?.t('errors.noCompanySelected') || 'No se ha seleccionado una empresa.';
            window.APP_LOGGER.error('clearAllHistory: No company selected.');
            throw new Error(errorMsg);
        }

        const companyId = CURRENT_COMPANY_PROFILE.company_id;

        try {
            const url = new URL(`${this.baseURL}/api/analysis/clear-all`);
            url.searchParams.append('company', companyId);

            const response = await fetch(url, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || `Error ${response.status}`);
            }

            window.APP_LOGGER.info(`History cleared for company ${companyId}: ${result.deleted_count} files deleted`);
            return result;

        } catch (error) {
            window.APP_LOGGER.error('Failed to clear history:', error);
            const errorMsg = LanguageManager?.t('errors.clearHistoryFailed', { error: error.message }) || `No se pudo limpiar el historial: ${error.message}`;
            throw new Error(errorMsg);
        }
    }

    /**
     * Obtener resultado de análisis específico
     */
    static async getAnalysisResult(filename) {
        try {
            const encodedFilename = encodeURIComponent(filename);
            const response = await fetch(`${this.baseURL}/api/result/${encodedFilename}`, {
                method: 'GET',
                headers: {'Content-Type': 'application/json'}
            });

            if (!response.ok) {
                const result = await response.json().catch(() => ({}));
                const backendError = result.error || `HTTP ${response.status}`;
                throw new Error(backendError);
            }

            const data = await response.json();
            window.APP_LOGGER.debug(`Analysis result loaded: ${filename}`);
            return data;

        } catch (error) {
            window.APP_LOGGER.error(`Failed to load analysis result ${filename}:`, error);
            const errorMsg = LanguageManager?.t('errors.loadResultFailed', { filename: filename, error: error.message }) || `No se pudo cargar el resultado ${filename}: ${error.message}`;
            throw new Error(errorMsg);
        }
    }

    /**
 * Elimina una medición del historial (desde la BD)
 */
    static async deleteHistoryItem(measurementId, filename) {
        if (!CURRENT_COMPANY_PROFILE || !CURRENT_COMPANY_PROFILE.company_id) {
            const errorMsg = LanguageManager?.t('errors.noCompanySelected') || 'No se ha seleccionado una empresa.';
            window.APP_LOGGER.error('deleteHistoryItem: No company selected.');
            throw new Error(errorMsg);
        }

        const companyId = CURRENT_COMPANY_PROFILE.company_id;

        try {
            const url = `${this.baseURL}/api/measurements/${measurementId}?company=${companyId}`;

            const response = await fetch(url, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || `Error ${response.status}`);
            }

            window.APP_LOGGER.info(`Measurement ${measurementId} (${filename}) deleted`);
            return result;

        } catch (error) {
            window.APP_LOGGER.error(`Failed to delete measurement ${measurementId}:`, error);
            const errorMsg = LanguageManager?.t('errors.deleteResultFailed', { 
                filename: filename, 
                error: error.message 
            }) || `No se pudo eliminar ${filename}: ${error.message}`;
            throw new Error(errorMsg);
        }
    }

    /**
     * Limpia todo el historial de la empresa actual (desde la BD)
     */
    static async clearAllHistory() {
        if (!CURRENT_COMPANY_PROFILE || !CURRENT_COMPANY_PROFILE.company_id) {
            const errorMsg = LanguageManager?.t('errors.noCompanySelected') || 'No se ha seleccionado una empresa.';
            window.APP_LOGGER.error('clearAllHistory: No company selected.');
            throw new Error(errorMsg);
        }

        const companyId = CURRENT_COMPANY_PROFILE.company_id;

        try {
            const url = `${this.baseURL}/api/measurements/clear-all?company=${companyId}`;

            const response = await fetch(url, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || `Error ${response.status}`);
            }

            window.APP_LOGGER.info(`History cleared for company ${companyId}: ${result.deleted_count} deleted`);
            return result;

        } catch (error) {
            window.APP_LOGGER.error('Failed to clear history:', error);
            const errorMsg = LanguageManager?.t('errors.clearHistoryFailed', { 
                error: error.message 
            }) || `No se pudo limpiar el historial: ${error.message}`;
            throw new Error(errorMsg);
        }
    }

    /**
 * Obtiene una medición específica por ID
 */
    static async getMeasurement(measurementId) {
        try {
            const companyId = this.getCompanyId();
            const url = `${this.baseURL}/api/measurements/${measurementId}?company=${companyId}`;
            
            APP_LOGGER.debug(`Fetching measurement: ${url}`);
            
            const response = await fetch(url);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }
            
            const data = await response.json();
            APP_LOGGER.info(`Measurement ${measurementId} loaded`);
            
            return data;
            
        } catch (error) {
            APP_LOGGER.error('Error fetching measurement:', error);
            throw error;
        }
    }
    

    /**
     * Obtiene la configuración del servidor
     */
    static async getConfig() {
        try {
            const response = await fetch(`${this.baseURL}/api/config`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            window.APP_LOGGER.debug('Config loaded:', data);
            return data;
        } catch (error) {
            window.APP_LOGGER.error('Failed to get config:', error);
            throw new Error('No se pudo obtener la configuración');
        }
    }
}

// Hacer disponible globalmente
window.APIClient = APIClient;