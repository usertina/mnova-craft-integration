/**
 * app.js
 * Lógica principal del frontend, modificada para multi-empresa.
 * Asume que 'CURRENT_COMPANY_PROFILE' ha sido definido en app.html
 * y que 'LanguageManager', 'UIManager', 'ChartManager' y 'APP_LOGGER' están disponibles globalmente.

*/
 

let currentHistoryPage = 1;
let currentAnalysisData = null;

document.addEventListener('DOMContentLoaded', () => {
    // Función auto-ejecutable asíncrona para la inicialización
    (async () => {
        try {
            // 1. Validar que el perfil de empresa se cargó (definido en app.html)
            if (typeof CURRENT_COMPANY_PROFILE === 'undefined' || !CURRENT_COMPANY_PROFILE) {
                throw new Error("No se pudo cargar el perfil de la empresa. La aplicación no puede iniciarse.");
            }
            
            // 2. APLICAR TODO EL BRANDING DE LA EMPRESA
            applyCompanyBranding(CURRENT_COMPANY_PROFILE);
            
            // 3. Cargar el idioma basado en el perfil de la empresa
            const lang = CURRENT_COMPANY_PROFILE.language || 'en'; // 'en' por defecto
            await LanguageManager.changeLanguage(lang);
            APP_LOGGER.info(`Idioma cargado: ${lang}`);

            // 4. Inicializar el resto de la aplicación
            await initializeApp(); // Esta es la función que ya tienes más abajo

        } catch (error) {
            APP_LOGGER.error("Error crítico en la inicialización:", error);
            showCriticalError(error.message || 'Error desconocido al iniciar.');
        }
    })();
});



function applyCompanyBranding(profile) {
    if (!profile) {
        APP_LOGGER.warn("applyCompanyBranding se llamó sin un perfil.");
        return;
    }

    try {
        // --- 1. Aplicar Logo y Nombre (CON LOS IDs CORRECTOS) ---
        const logoElement = document.getElementById('companyBrandingLogo');
        const nameElement = document.getElementById('companyBrandingName');
        const containerElement = document.getElementById('companyBranding');

        if (logoElement && nameElement && containerElement) {
            if (profile.logo_url) {
                logoElement.src = profile.logo_url;
                logoElement.alt = `${profile.company_name} Logo`;
                logoElement.style.display = 'block';
                logoElement.onerror = () => { 
                    logoElement.style.display = 'none'; 
                    APP_LOGGER.warn(`No se pudo cargar el logo: ${profile.logo_url}`);
                };
            } else {
                logoElement.style.display = 'none';
            }
            
            nameElement.textContent = profile.company_name;
            containerElement.style.display = 'flex'; // Mostrar el contenedor
        }

        // --- 2. Inyectar Colores como Variables CSS ---
        if (profile.primary_color) {
            document.documentElement.style.setProperty('--primary-color', profile.primary_color);
        }
        if (profile.secondary_color) {
            document.documentElement.style.setProperty('--secondary-color', profile.secondary_color);
        }

        // --- 3. Implementar el Favicon ---
        if (profile.favicon_url) {
            // Eliminar cualquier favicon existente
            document.querySelector("link[rel*='icon']")?.remove();
            
            // Crear y añadir el nuevo favicon
            const favicon = document.createElement('link');
            favicon.rel = 'icon';
            favicon.type = 'image/x-icon';
            favicon.href = profile.favicon_url;
            document.head.appendChild(favicon);
        }
        
        APP_LOGGER.debug("Branding de empresa aplicado:", profile.company_name);

    } catch (error) {
        APP_LOGGER.error("Error al aplicar branding:", error);
        // No es un error crítico, la app puede continuar.
    }
}

/**
 * Muestra un error fatal que impide que la aplicación funcione.
 * (Función nueva según tu descripción)
 */
function showCriticalError(message) {
    try {
        // Ocultar la aplicación principal
        const mainApp = document.getElementById('main-app'); // Asumiendo ID 'main-app'
        if (mainApp) mainApp.style.display = 'none';

        // Mostrar el contenedor de error
        const errorContainer = document.getElementById('critical-error-container'); // Asumiendo ID 'critical-error-container'
        const errorMessageEl = document.getElementById('critical-error-message');
        
        if (errorContainer && errorMessageEl) {
            errorMessageEl.textContent = message;
            errorContainer.style.display = 'flex';
        } else {
            // Fallback si los elementos no existen
            document.body.innerHTML = `<div style="text-align: center; padding: 40px; color: red;">
                <h1>Error Crítico</h1>
                <p>${message}</p>
                <p>Por favor, regrese a la página de inicio o contacte al administrador.</p>
                <a href="index.html">Volver a Inicio</a>
            </div>`;
        }
    } catch (e) {
        // Error irrecuperable
        console.error("Error en showCriticalError:", e);
        alert(`Error Crítico: ${message}`); // fallback final
    }
}

/**
 * Inicialización principal de la aplicación
 */
async function initializeApp() {
    try {
        UIManager.showLoading(LanguageManager.t('messages.initializing') || 'Inicializando...');

        // Comprobar conexión y cargar configuración base
        await APIClient.checkConnection();
        UIManager.setConnectionStatus('connected');
        const config = await APIClient.getConfig();
        
        UIManager.setupAnalysisParameters(config.analysis_parameters);
        UIManager.setupEventListeners();
        
        // ✅ CRÍTICO: Inicializar ChartManager ANTES de cargar historial
        if (window.ChartManager && typeof ChartManager.init === 'function') {
            try {
                await ChartManager.init();
                APP_LOGGER.info('ChartManager inicializado correctamente');
            } catch (chartError) {
                APP_LOGGER.error('Error inicializando ChartManager:', chartError);
                // Continuar aunque falle ChartManager
            }
        } else {
            APP_LOGGER.warn('ChartManager no disponible');
        }
        
        // Intentar cargar historial pero sin bloquear la app si falla
        try {
            await loadHistory(1);
        } catch (historyError) {
            APP_LOGGER.warn("No se pudo cargar el historial inicial:", historyError.message);
            // Mostrar mensaje de error en el historial
            const historyList = document.getElementById('historyList');
            if (historyList) {
                historyList.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-exclamation-triangle fa-3x"></i>
                        <p>Error al cargar el historial</p>
                        <p class="text-muted">${historyError.message}</p>
                    </div>
                `;
            }
        }

        UIManager.hideLoading();
        
        // CRÍTICO: Ocultar pantalla de carga inicial y mostrar la app
        const loadingScreen = document.getElementById('loadingScreen');
        const appContainer = document.getElementById('app');
        
        if (loadingScreen) {
            loadingScreen.style.display = 'none';
        }
        
        if (appContainer) {
            appContainer.classList.remove('hidden');
        }
        
        APP_LOGGER.info(`Aplicación inicializada para ${CURRENT_COMPANY_PROFILE.company_name}`);

    } catch (error) {
        APP_LOGGER.error("Fallo al inicializar la app:", error);
        
        const loadingScreen = document.getElementById('loadingScreen');
        if (loadingScreen) {
            loadingScreen.style.display = 'none';
        }
        
        showCriticalError(
            LanguageManager.t('errors.initFailed', { error: error.message }) || 
            `Error al inicializar: ${error.message}`
        );
    }
}
/**
 * Ejecuta un nuevo análisis.
 * (Modificado: Ya no pasa companyId, APIClient lo maneja)
 */
async function runAnalysis() {
    const file = FileProcessor.getCurrentFile();
    
    if (!file) {
        UIManager.showNotification(
            LanguageManager.t('errors.noFileSelected') || 'No se ha seleccionado ningún archivo',
            'error'
        );
        return;
    }

    try {
        UIManager.showLoading(LanguageManager.t('messages.analyzing') || 'Analizando...');
        
        const parameters = UIManager.getCurrentAnalysisParams();
        
        // --- INICIO DEL CAMBIO ---
        // 1. Obtener respuesta del servidor (ahora es plana)
        const analysisData = await APIClient.analyzeSpectrum(file, parameters);
        
        APP_LOGGER.info('Respuesta del servidor (plana):', analysisData);
        
        // EL BLOQUE DE DESANIDACIÓN HA SIDO ELIMINADO
        // --- FIN DEL CAMBIO ---
        if (analysisData.error) {
            // Si el backend devolvió un error, muéstralo y detente.
            throw new Error(`Error del servidor: ${analysisData.error}`);
        }
        // VALIDACIÓN ADICIONAL
        if (!analysisData.spectrum) {
            console.error('❌ Falta campo "spectrum" en los datos');
            console.log('Estructura recibida:', Object.keys(analysisData));
        }
        
        if (!analysisData.peaks || !Array.isArray(analysisData.peaks)) {
            console.warn('⚠️ Campo "peaks" faltante o inválido');
        }
        
        // 2. Guardar en variable global
        currentAnalysisData = analysisData;
        
        console.log('✅ Datos del análisis normalizados:', {
            filename: analysisData.file_name || analysisData.filename,
            hasPeaks: !!analysisData.peaks,
            peaksCount: analysisData.peaks?.length || 0,
            hasSpectrum: !!analysisData.spectrum,
            spectrumPoints: analysisData.spectrum?.ppm?.length || 0,
            hasPFAS: !!analysisData.pfas_detection,
            pfasDetected: analysisData.pfas_detection?.total_detected || 0
        });
        
        // 3. Graficar con ChartManager
        if (window.ChartManager && typeof ChartManager.plotResults === 'function') {
            try {
                console.log('📊 Graficando resultados...');
                ChartManager.plotResults(analysisData);
                console.log('✅ Gráfico generado');
            } catch (chartError) {
                console.error('❌ Error graficando:', chartError);
                APP_LOGGER.warn('Error graficando resultados:', chartError);
            }
        } else {
            console.error('❌ ChartManager no disponible');
        }
        
        // 4. Mostrar en UI
        console.log('🎨 Mostrando resultados en UI...');
        UIManager.displayResults(analysisData); // UIManager ya tiene el código para mostrar PFAS
        console.log('✅ Resultados mostrados');
        
        // 5. Recargar historial
        try {
            await loadHistory(1);
        } catch (histError) {
            APP_LOGGER.warn('No se pudo recargar historial:', histError);
        }
        
        UIManager.hideLoading();
        UIManager.showNotification(
            LanguageManager.t('messages.analysisSuccess') || 'Análisis completado',
            'success'
        );
        
        FileProcessor.clearFiles();

    } catch (error) {
        console.error("❌ Error en runAnalysis:", error);
        APP_LOGGER.error("Error en runAnalysis:", error);
        UIManager.hideLoading();
        UIManager.showNotification(error.message, 'error');
    }
}

/**
 * Carga la lista del historial (mediciones).
 */
async function loadHistory(page = 1) {
    try {
        // ✅ Guardar página actual
        currentHistoryPage = page;
        
        UIManager.showHistoryLoading();
        const searchTerm = UIManager.getHistorySearchTerm();

        const historyData = await APIClient.getHistory(page, 50, searchTerm);

        UIManager.displayHistory(historyData);

    } catch (error) {
        APP_LOGGER.error("Error en loadHistory:", error);
        
        const errorMessage = error.message || 
                           LanguageManager.t('errors.historyLoadFailed') || 
                           'No se pudo cargar el historial';
        
        UIManager.displayHistoryError(errorMessage);
    }
}

/**
 * Limpia todo el historial de la empresa actual.
 * (Modificado: Ya no pasa companyId, APIClient lo maneja)
 */
async function clearHistory() {
    const confirmTitle = LanguageManager.t('confirm.clearHistoryTitle') || 'Confirmar limpieza';
    const confirmBody = LanguageManager.t('confirm.clearHistoryBody') || 
                       '¿Está seguro de que desea eliminar todo el historial? Esta acción no se puede deshacer.';
    
    if (!confirm(`${confirmTitle}\n\n${confirmBody}`)) {
        return;
    }

    try {
        UIManager.showLoading(LanguageManager.t('messages.deleting') || 'Eliminando...');
        
        const result = await APIClient.clearAllHistory();
        
        UIManager.hideLoading();
        UIManager.showNotification(
            LanguageManager.t('messages.clearSuccess', { count: result.deleted_count }) || 
            `Se eliminaron ${result.deleted_count} registros`,
            'success'
        );
        
        // Recargar historial
        await loadHistory(1);
        
    } catch (error) {
        APP_LOGGER.error("Error en clearHistory:", error);
        UIManager.hideLoading();
        UIManager.showNotification(error.message, 'error');
    }
}


/**
 * Elimina un item específico del historial.
 * (Modificado: Ya no pasa companyId, APIClient lo maneja)
 */
async function deleteHistoryItem(measurementId, filename) {
    const confirmTitle = LanguageManager.t('confirm.deleteItemTitle') || 'Confirmar eliminación';
    const confirmBody = LanguageManager.t('confirm.deleteItemBody', { filename }) || 
                       `¿Está seguro de que desea eliminar '${filename}'?`;
    
    if (!confirm(`${confirmTitle}\n\n${confirmBody}`)) {
        return;
    }

    try {
        UIManager.showLoading(LanguageManager.t('messages.deleting') || 'Eliminando...');
        
        // Usar el nuevo método que elimina desde la BD
        await APIClient.deleteHistoryItem(measurementId, filename);
        
        UIManager.hideLoading();
        UIManager.showNotification(
            LanguageManager.t('messages.deleteSuccess') || 'Eliminado correctamente',
            'success'
        );
        
        // Recargar historial
        await loadHistory(currentHistoryPage);
        
    } catch (error) {
        APP_LOGGER.error(`Error en deleteHistoryItem (${filename}):`, error);
        UIManager.hideLoading();
        UIManager.showNotification(error.message, 'error');
    }
}

/**
 * Exporta el reporte actual.
 */
async function exportReport(format = null) {
    try {
        if (!format) {
            showExportFormatMenu('single');
            return;
        }

        // ✅ VERIFICAR que tenemos datos
        if (!currentAnalysisData) {
            UIManager.showNotification(
                '⚠️ No hay datos de análisis disponibles. Por favor, realiza un análisis primero.',
                'warning'
            );
            console.error('❌ currentAnalysisData es null');
            return;
        }

        console.log('📤 Exportando reporte con datos:', currentAnalysisData);

        UIManager.showLoading(LanguageManager.t('messages.exporting') || 'Exportando...');

        const companyProfile = window.CURRENT_COMPANY_PROFILE || {};

        // Capturar imagen del gráfico
        let chartImage = null;
        if (window.ChartManager && typeof ChartManager.getChartAsBase64 === 'function') {
            try {
                chartImage = await ChartManager.getChartAsBase64();
            } catch (chartError) {
                console.warn('[exportReport] No se pudo capturar gráfico:', chartError);
            }
        }

        // ✅ CONFIGURACIÓN CORREGIDA - Enviar TODOS los datos necesarios
        const exportConfig = {
            type: 'single',
            format: format,
            lang: LanguageManager.currentLang || 'es',  // ✅ Idioma para traducciones
            
            // ✅ ENVIAR EL OBJETO results COMPLETO
            results: {
                // Información básica
                filename: currentAnalysisData.filename || 'Muestra',
                sample_name: currentAnalysisData.sample_name || currentAnalysisData.filename,
                timestamp: currentAnalysisData.timestamp || new Date().toISOString(),
                
                // ✅ CRÍTICO: Enviar el objeto 'analysis' COMPLETO
                // Este objeto contiene todos los porcentajes y áreas
                analysis: currentAnalysisData.analysis || {
                    fluor_percentage: currentAnalysisData.fluor_percentage || 0,
                    pfas_percentage: currentAnalysisData.pfas_percentage || currentAnalysisData.pifas_percentage || 0,
                    pifas_percentage: currentAnalysisData.pifas_percentage || currentAnalysisData.pfas_percentage || 0,
                    pfas_concentration: currentAnalysisData.pfas_concentration || currentAnalysisData.pifas_concentration || 0,
                    pifas_concentration: currentAnalysisData.pifas_concentration || currentAnalysisData.pfas_concentration || 0,
                    concentration: currentAnalysisData.concentration || 0,
                    total_area: currentAnalysisData.total_area || currentAnalysisData.total_integral || 0,
                    total_integral: currentAnalysisData.total_integral || currentAnalysisData.total_area || 0,
                    fluor_area: currentAnalysisData.fluor_area || 0,
                    pfas_area: currentAnalysisData.pfas_area || currentAnalysisData.pifas_area || 0,
                    pifas_area: currentAnalysisData.pifas_area || currentAnalysisData.pfas_area || 0,
                    signal_to_noise: currentAnalysisData.signal_to_noise || currentAnalysisData.snr || 0
                },
                
                // ✅ CRÍTICO: Enviar pfas_detection con los compuestos
                pfas_detection: currentAnalysisData.pfas_detection || {
                    total_pfas_concentration: 0,
                    compounds: []
                },
                
                // Calidad
                quality_score: currentAnalysisData.quality_score || 0,
                quality_classification: currentAnalysisData.quality_classification || 'N/A',
                quality_breakdown: currentAnalysisData.quality_breakdown || {},
                
                // Métricas de calidad
                quality_metrics: currentAnalysisData.quality_metrics || {
                    snr: currentAnalysisData.signal_to_noise || currentAnalysisData.snr || 0
                },
                
                // S/N en nivel raíz (para compatibilidad)
                signal_to_noise: currentAnalysisData.signal_to_noise || currentAnalysisData.snr || 0,
                snr: currentAnalysisData.snr || currentAnalysisData.signal_to_noise || 0,
                
                // Parámetros de la muestra
                parameters: {
                    concentration: currentAnalysisData.sample_concentration || 
                                 currentAnalysisData.concentration || 
                                 currentAnalysisData.analysis?.concentration || 1.0
                },
                sample_concentration: currentAnalysisData.sample_concentration || 
                                    currentAnalysisData.concentration || 1.0,
                
                // Espectro
                spectrum: currentAnalysisData.spectrum || {
                    ppm: currentAnalysisData.ppm || [],
                    intensity: currentAnalysisData.intensity || [],
                    ppm_min: Math.min(...(currentAnalysisData.ppm || [0])),
                    ppm_max: Math.max(...(currentAnalysisData.ppm || [0]))
                },
                
                // ✅ PICOS CON TODOS LOS CAMPOS
                peaks: (currentAnalysisData.peaks || []).map(peak => ({
                    ppm: peak.ppm || peak.position || 0,
                    position: peak.position || peak.ppm || 0,
                    intensity: peak.intensity || peak.height || 0,
                    height: peak.height || peak.intensity || 0,
                    relative_intensity: peak.relative_intensity || 0,
                    width: peak.width || peak.width_ppm || 0,
                    width_ppm: peak.width_ppm || peak.width || 0,
                    width_hz: peak.width_hz || 0,
                    area: peak.area || 0,
                    snr: peak.snr || 0,
                    region: peak.region || 'N/A'
                }))
            },
            
            // ✅ Imagen del gráfico
            chart_image: chartImage,
            
            // ✅ DATOS DE LA EMPRESA para el branding
            company_data: {
                name: companyProfile.company_name || 'CraftRMN Pro',
                logo: companyProfile.logo_url || '',  // URL del logo
                address: companyProfile.company_address || '',
                phone: companyProfile.contact_phone || '',
                email: companyProfile.contact_email || ''
            }
        };

        console.log('📦 Configuración de exportación COMPLETA:', exportConfig);
        console.log('📊 Analysis enviado:', exportConfig.results.analysis);
        console.log('🧪 PFAS Detection enviado:', exportConfig.results.pfas_detection);
        console.log('🌐 Idioma:', exportConfig.lang);

        // Llamar al API
        await APIClient.exportData(exportConfig);
        
        UIManager.hideLoading();
        UIManager.showNotification(
            LanguageManager.t('messages.exportSuccess') || 'Exportado correctamente',
            'success'
        );

    } catch (error) {
        console.error("Error en exportReport:", error);
        UIManager.hideLoading();
        UIManager.showNotification(error.message, 'error');
    }
}

/**
 * Exporta el dashboard (wrapper para DashboardManager)
 */
async function exportDashboard(format = null) {
    if (window.DashboardManager && typeof DashboardManager.exportDashboard === 'function') {
        await DashboardManager.exportDashboard(format);
    } else {
        console.error('[exportDashboard] DashboardManager no disponible');
        UIManager.showNotification('Error: Dashboard no inicializado', 'error');
    }
}

/**
 * Muestra el menú de selección de formato de exportación
 */
function showExportFormatMenu(exportType = 'single') { // 'single', 'dashboard', 'comparison'
    const formats = [
        { value: 'pdf', label: 'PDF', icon: 'fa-file-pdf' },
        { value: 'docx', label: 'Word (DOCX)', icon: 'fa-file-word' },
        // Solo añadir CSV si el tipo de exportación lo soporta
        ...((exportType === 'single' || exportType === 'comparison') ? [{ value: 'csv', label: 'CSV', icon: 'fa-file-csv' }] : [])
        // Puedes añadir JSON si lo implementas para todos los tipos
        // { value: 'json', label: 'JSON', icon: 'fa-file-code' }
    ];

    const menu = document.createElement('div');
    menu.className = 'export-format-menu';

    // Determinar el título correcto según el tipo
    let titleKey = 'analyzer.exportReport'; // Default para 'single'
    if (exportType === 'dashboard') titleKey = 'dashboard.export';
    else if (exportType === 'comparison') titleKey = 'comparison.exportComparison';

    menu.innerHTML = `
        <div class="export-format-overlay"></div>
        <div class="export-format-dialog">
            <h3>${LanguageManager.t(titleKey) || 'Exportar'}</h3>
            <p>Selecciona el formato de exportación:</p>
            <div class="export-format-options">
                ${formats.map(fmt => `
                    <button class="export-format-btn" data-format="${fmt.value}">
                        <i class="fas ${fmt.icon}"></i>
                        <span>${fmt.label}</span>
                    </button>
                `).join('')}
            </div>
            // Asumiendo t(key, variables, defaultValue)
<button class="export-format-cancel">${LanguageManager.t('history.clear', {}, 'Cancelar')}</button>
        </div>
    `; // Usé 'history.clear' como key para Cancelar, ajústalo si tienes otra

    document.body.appendChild(menu);

    // Event listeners
    menu.querySelectorAll('.export-format-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const format = btn.dataset.format;
            document.body.removeChild(menu); // Cierra el menú

            // --- ¡¡AQUÍ ESTÁ LA CORRECCIÓN!! ---
            try {
                if (exportType === 'single') {
                    // Llama a la función global para reporte individual
                    await exportReport(format); 
                } else if (exportType === 'dashboard') {
                    // Llama al MÉTODO específico del DashboardManager
                    if (window.DashboardManager && typeof window.DashboardManager.exportDashboard === 'function') {
                        await window.DashboardManager.exportDashboard(format); 
                    } else {
                        console.error("DashboardManager no está listo para exportar.");
                        UIManager.showNotification("Error: El módulo Dashboard no está listo.", "error");
                    }
                } else if (exportType === 'comparison') {
                     // Llama al MÉTODO específico del ComparisonManager (si lo refactorizas así)
                     // O sigue llamando a la función global si esta maneja la comparación
                     // Por ahora, asumimos que APP_HANDLERS.exportReport (llamado por comparison.js) maneja esto
                     // Si ComparisonManager.performExport llama a APIClient.exportData directamente, está bien.
                     // PERO, si ComparisonManager necesita llamar a showExportFormatMenu, deberías
                     // pasarle una referencia a sí mismo o refactorizar.

                     // Si comparison.js llama a esta función:
                     if (window.ComparisonManager && typeof window.ComparisonManager.performExport === 'function') {
                        // Este es el flujo actual según tu comparison.js
                        await window.ComparisonManager.performExport(format);
                     } else {
                         console.error("ComparisonManager no está listo para exportar.");
                         UIManager.showNotification("Error: El módulo Comparison no está listo.", "error");
                     }
                }
            } catch (exportError) {
                console.error(`Error durante la exportación (${exportType}, ${format}):`, exportError);
                // UIManager.showNotification ya debería haberse mostrado desde la función específica
            }
        });
    });

    // Listeners para cerrar el menú (sin cambios)
    menu.querySelector('.export-format-cancel').addEventListener('click', () => {
        document.body.removeChild(menu);
    });
    menu.querySelector('.export-format-overlay').addEventListener('click', () => {
        document.body.removeChild(menu);
    });
}


/**
 * Carga un resultado específico del historial para verlo/compararlo.
 */
/**
 * Carga un resultado específico del historial para verlo/compararlo.
 */
async function loadResult(measurementId, filename) {
    try {
        console.log(`[loadResult] Cargando medición ${measurementId}...`);
        
        UIManager.showLoading(LanguageManager.t('messages.loading') || 'Cargando...');
        
        // 1. Obtener la medición de la BD
        const measurement = await APIClient.getMeasurement(measurementId);
        console.log('[loadResult] Medición obtenida:', measurement);

        // 2. ✅ CORRECCIÓN: Reconstruir currentAnalysisData con la estructura correcta
        // El objeto 'measurement.analysis' de la BD contiene todos los datos de análisis
        const analysisData = measurement.analysis || {};
        
        currentAnalysisData = {
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            // INFORMACIÓN BÁSICA
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            filename: measurement.filename || 'Muestra',
            sample_name: measurement.sample_name || measurement.filename || 'Muestra',
            timestamp: measurement.timestamp || new Date().toISOString(),
            measurement_id: measurementId,
            
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            // PUNTUACIÓN DE CALIDAD
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            quality_score: measurement.quality_score || 0,
            quality_classification: analysisData.quality_classification || 'N/A',
            quality_breakdown: analysisData.quality_breakdown || {},
            
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            // DATOS DEL ESPECTRO
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            spectrum: measurement.spectrum || {},
            ppm: measurement.spectrum?.ppm || [],
            intensity: measurement.spectrum?.intensity || [],
            
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            // PICOS DETECTADOS
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            peaks: measurement.peaks || [],
            
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            // ✅ CRÍTICO: OBJETO 'analysis'
            // Este objeto debe contener TODOS los campos de análisis
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            analysis: {
                // Porcentajes
                fluor_percentage: analysisData.fluor_percentage || 0,
                pfas_percentage: analysisData.pfas_percentage || analysisData.pifas_percentage || 0,
                pifas_percentage: analysisData.pifas_percentage || analysisData.pfas_percentage || 0,
                
                // Concentraciones
                pfas_concentration: analysisData.pfas_concentration || analysisData.pifas_concentration || 0,
                pifas_concentration: analysisData.pifas_concentration || analysisData.pfas_concentration || 0,
                concentration: analysisData.concentration || analysisData.pfas_concentration || 0,
                
                // Áreas
                total_area: analysisData.total_area || analysisData.total_integral || 0,
                total_integral: analysisData.total_integral || analysisData.total_area || 0,
                fluor_area: analysisData.fluor_area || 0,
                pfas_area: analysisData.pfas_area || analysisData.pifas_area || 0,
                pifas_area: analysisData.pifas_area || analysisData.pfas_area || 0,
                
                // S/N
                signal_to_noise: analysisData.signal_to_noise || 0,
                
                // Incluir cualquier otro campo que pueda existir
                ...analysisData
            },
            
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            // ✅ CRÍTICO: DETECCIÓN DE COMPUESTOS PFAS
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            pfas_detection: analysisData.pfas_detection || null,
            
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            // MÉTRICAS DE CALIDAD
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            quality_metrics: {
                snr: analysisData.signal_to_noise || 0,
                ...analysisData.quality_metrics
            },
            
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            // S/N EN NIVEL RAÍZ (para compatibilidad)
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            signal_to_noise: analysisData.signal_to_noise || 0,
            snr: analysisData.signal_to_noise || 0,
            
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            // CONCENTRACIÓN DE LA MUESTRA
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            sample_concentration: analysisData.concentration || 1.0,
            concentration: analysisData.concentration || 0,
            
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            // COMPATIBILIDAD: Campos en nivel raíz
            // (algunos componentes pueden buscar aquí)
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            fluor_percentage: analysisData.fluor_percentage || 0,
            pfas_percentage: analysisData.pfas_percentage || analysisData.pifas_percentage || 0,
            pifas_percentage: analysisData.pifas_percentage || analysisData.pfas_percentage || 0,
            total_area: analysisData.total_area || analysisData.total_integral || 0,
            total_integral: analysisData.total_integral || analysisData.total_area || 0,
            fluor_area: analysisData.fluor_area || 0,
            pfas_area: analysisData.pfas_area || analysisData.pifas_area || 0,
            pifas_area: analysisData.pifas_area || analysisData.pfas_area || 0
        };
        
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        // LOGS DE DEBUGGING
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        console.log('✅ Datos de medición normalizados:', currentAnalysisData);
        console.log('📊 Analysis object:', currentAnalysisData.analysis);
        console.log('📈 Total Area:', currentAnalysisData.analysis?.total_area);
        console.log('📡 Signal to Noise:', currentAnalysisData.signal_to_noise);
        console.log('🔬 PFAS Detection:', currentAnalysisData.pfas_detection);
        console.log('🧪 Compounds:', currentAnalysisData.pfas_detection?.compounds?.length || 0);
        
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        // MOSTRAR LOS DATOS EN LA UI
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        // Cambiar a la pestaña del analizador
        UIManager.switchTab('analyzer');
        
        // Graficar si ChartManager está disponible
        if (window.ChartManager && typeof ChartManager.plotResults === 'function') {
            try {
                ChartManager.plotResults(currentAnalysisData);
                console.log('✅ Gráfico generado correctamente');
            } catch (chartError) {
                console.warn('[loadResult] Error graficando:', chartError);
            }
        }
        
        // Mostrar resultados en la UI
        UIManager.displayResults(currentAnalysisData);
        
        UIManager.hideLoading();
        UIManager.showNotification(
            `Análisis cargado: ${filename}`,
            'success'
        );
        
    } catch (error) {
        console.error(`[loadResult] Error cargando ${filename}:`, error);
        UIManager.hideLoading();
        UIManager.showNotification(
            `No se pudo cargar ${filename}: ${error.message}`,
            'error'
        );
    }
}


// --- Exponer funciones al scope global para ser llamadas desde el HTML (onclick="...") ---
// (Es mejor que UIManager.setupEventListeners() las asigne, pero esto funciona)
window.APP_HANDLERS = {
    runAnalysis,
    loadHistory,
    clearHistory,
    deleteHistoryItem,
    exportReport,
    exportDashboard,
    loadResult
};

// Hacer disponible globalmente para dashboard y comparison
window.showExportFormatMenu = showExportFormatMenu;
window.exportDashboard = exportDashboard;