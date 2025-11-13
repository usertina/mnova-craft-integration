class APIClient {
    static get baseURL() {
        // Asegura que CURRENT_COMPANY_PROFILE exista
        if (typeof CURRENT_COMPANY_PROFILE === 'undefined') {
            console.warn("CURRENT_COMPANY_PROFILE no está definido aún.");
        }
        return window.location.origin;
    }

    /**
     * ✅ Obtiene el company_id del perfil actual
     */
    static getCompanyId() {
        if (!window.CURRENT_COMPANY_PROFILE || !window.CURRENT_COMPANY_PROFILE.company_id) {
            throw new Error('No company profile loaded');
        }
        return window.CURRENT_COMPANY_PROFILE.company_id;
    }

    /**
     * ✅ NUEVO: Helper para incluir token en headers
     */
    static getAuthHeaders(additionalHeaders = {}) {
        const token = localStorage.getItem('access_token');
        const headers = { ...additionalHeaders };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        return headers;
    }

    /**
     * ✅ Headers comunes para todas las peticiones (sin token)
     */
    static getHeaders() {
        return {
            'Content-Type': 'application/json'
        };
    }

    /**
     * ✅ NUEVO: Verificar si hay token válido
     */
    static hasValidToken() {
        return !!localStorage.getItem('access_token');
    }

    /**
     * ✅ NUEVO: Limpiar tokens (logout)
     */
    static clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        console.log('✅ Tokens limpiados');
    }

    /**
     * ✅ NUEVO: Helper para parsear errores del backend
     */
    static parseBackendError(result, response) {
        // Intentar obtener el error del backend en diferentes formatos
        if (result.error) {
            // Error simple
            return result.error;
        }
        
        if (result.traceback) {
            // Error con traceback de Python
            console.error('Backend traceback:', result.traceback);
            return `Error del servidor: ${result.message || result.error || 'Error desconocido'}\n\nVer consola para detalles técnicos.`;
        }
        
        if (result.message) {
            return result.message;
        }
        
        if (result.details) {
            return `Error: ${JSON.stringify(result.details)}`;
        }
        
        // Fallback
        return `Error ${response.status}: ${response.statusText}`;
    }

    static async checkConnection() {
        try {
            const response = await fetch(`${this.baseURL}/api/health`, {
                method: 'GET',
                headers: this.getAuthHeaders({ 'Content-Type': 'application/json' })
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

    /**
     * ✅ MEJORADO: Análisis con JWT y mejor manejo de errores
     */
    static async analyzeSpectrum(file, parameters) {
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
        
        formData.append('company_id', CURRENT_COMPANY_PROFILE.company_id);

        window.APP_LOGGER.debug('Sending analysis request:', {
            filename: file.name,
            size: file.size,
            company_id: CURRENT_COMPANY_PROFILE.company_id,
            parameters: parameters
        });

        try {
            // ✅ NUEVO: Incluir token en headers
            const token = localStorage.getItem('access_token');
            const headers = {};
            
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
                window.APP_LOGGER.debug('✅ Token incluido en análisis');
            } else {
                window.APP_LOGGER.warn('⚠️ No hay token - La petición puede fallar');
            }

            const response = await fetch(`${this.baseURL}/api/analyze`, {
                method: 'POST',
                headers: headers,
                body: formData
            });

            let result;
            const contentType = response.headers.get('content-type');
            
            if (contentType && contentType.includes('application/json')) {
                result = await response.json();
            } else {
                const text = await response.text();
                window.APP_LOGGER.error('Non-JSON response:', text);
                throw new Error(`Respuesta inesperada del servidor (no JSON). Status: ${response.status}`);
            }

            if (!response.ok) {
                const backendError = this.parseBackendError(result, response);
                
                window.APP_LOGGER.error('Backend analysis error:', {
                    status: response.status,
                    statusText: response.statusText,
                    error: result.error,
                    message: result.message,
                    traceback: result.traceback,
                    details: result.details
                });
                
                const clientErrorMsg = LanguageManager?.t('errors.analysisFailed', { 
                    error: backendError 
                }) || `Error en análisis: ${backendError}`;
                
                throw new Error(clientErrorMsg);
            }
            
            window.APP_LOGGER.debug(`Analysis successful for company ${CURRENT_COMPANY_PROFILE.company_id}:`, {
                filename: result.file_name,
                peaks: result.peaks?.length || 0,
                pfas_detected: result.pfas_detection?.total_detected || 0
            });
            
            return result;

        } catch (error) {
            window.APP_LOGGER.error('Analysis request failed:', error);
            
            if (error.message.includes('Error en análisis:') || 
                error.message.includes('Respuesta')) {
                throw error;
            }
            
            const errorMsg = LanguageManager?.t('errors.analysisFailed', { 
                error: error.message 
            }) || `Error al comunicarse con el servidor: ${error.message}`;
            
            throw new Error(errorMsg);
        }
    }

    /**
     * ✅ MEJORADO: Obtiene el historial con JWT
     */
    static async getHistory(page = 1, pageSize = 50, searchTerm = '') {
        try {
            const companyId = this.getCompanyId();
            
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
                headers: this.getAuthHeaders(this.getHeaders())
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
     * ✅ MEJORADO: Exporta datos con JWT
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
                headers: this.getAuthHeaders({ 'Content-Type': 'application/json' }),
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
     * ✅ MEJORADO: Obtener resultado con JWT
     */
    static async getAnalysisResult(filename) {
        try {
            const encodedFilename = encodeURIComponent(filename);
            const response = await fetch(`${this.baseURL}/api/result/${encodedFilename}`, {
                method: 'GET',
                headers: this.getAuthHeaders({'Content-Type': 'application/json'})
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
            const errorMsg = LanguageManager?.t('errors.loadResultFailed', { 
                filename: filename, 
                error: error.message 
            }) || `No se pudo cargar el resultado ${filename}: ${error.message}`;
            throw new Error(errorMsg);
        }
    }

    /**
     * ✅ MEJORADO: Elimina medición con JWT
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
                headers: this.getAuthHeaders({ 'Content-Type': 'application/json' })
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
     * ✅ MEJORADO: Limpia historial con JWT
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
                headers: this.getAuthHeaders({ 'Content-Type': 'application/json' })
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
     * ✅ MEJORADO: Obtiene medición con JWT
     */
    static async getMeasurement(measurementId) {
        try {
            const companyId = this.getCompanyId();
            const url = `${this.baseURL}/api/measurements/${measurementId}?company=${companyId}`;
            
            APP_LOGGER.debug(`Fetching measurement: ${url}`);
            
            const response = await fetch(url, {
                headers: this.getAuthHeaders()
            });
            
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
     * ✅ Obtiene la configuración del servidor
     */
    static async getConfig() {
        try {
            const response = await fetch(`${this.baseURL}/api/config`, {
                headers: this.getAuthHeaders()
            });
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