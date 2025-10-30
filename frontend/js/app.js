/**
 * app.js
 * Lógica principal del frontend, modificada para multi-empresa.
 * Asume que 'CURRENT_COMPANY_PROFILE' ha sido definido en app.html
 * y que 'LanguageManager', 'UIManager', 'ChartManager' y 'APP_LOGGER' están disponibles globalmente.

/**
 * Aplica TODA la identidad corporativa (logo, nombre, colores, favicon) a la app.
 * Esta es la ÚNICA función de branding que debe existir.
 */

// --- PEGA ESTE BLOQUE AL PRINCIPIO DE TODO EN APP.JS ---

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
        const results = await APIClient.analyzeSpectrum(file, parameters);

        APP_LOGGER.info('Análisis completado:', results);

        // ✅ CRÍTICO: Almacenar el análisis completo
        currentAnalysisData = {
            filename: results.filename || file.name || 'Muestra',
            sample_name: results.sample_name || results.filename || file.name || 'Muestra',
            timestamp: results.timestamp || new Date().toISOString(),
            
            analysis: results.analysis || {},
            
            fluor_percentage: results.fluor_percentage || results.analysis?.fluor_percentage || 0,
            pfas_percentage: results.pfas_percentage || results.pifas_percentage || results.analysis?.pfas_percentage || results.analysis?.pifas_percentage || 0,
            pifas_percentage: results.pifas_percentage || results.analysis?.pifas_percentage || 0,
            concentration: results.concentration || results.analysis?.pifas_concentration || results.analysis?.pfas_concentration || 0,
            pifas_concentration: results.analysis?.pifas_concentration || results.concentration || 0,
            
            quality_score: results.quality_score || 0,
            quality_classification: results.quality_classification || 'N/A',
            signal_to_noise: results.signal_to_noise || results.snr || 0,
            snr: results.snr || results.signal_to_noise || 0,
            
            total_area: results.analysis?.total_area || results.total_area || 0,
            fluor_area: results.analysis?.fluor_area || 0,
            pfas_area: results.analysis?.pfas_area || results.analysis?.pifas_area || 0,
            pifas_area: results.analysis?.pifas_area || 0,
            sample_concentration: results.sample_concentration || 0,
            
            peaks: results.peaks || [],
            quality_metrics: results.quality_metrics || {},
            
            ppm: results.ppm || [],
            intensity: results.intensity || []
        };

        console.log('✅ Datos del análisis almacenados:', currentAnalysisData);

        if (window.ChartManager && typeof ChartManager.plotResults === 'function') {
            try {
                ChartManager.plotResults(results);
            } catch (chartError) {
                APP_LOGGER.warn('Error graficando resultados:', chartError);
            }
        }
        
        UIManager.displayResults(results);

        setupMoleculeViewers(results);
        
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

        let chartImage = null;
        if (window.ChartManager && typeof ChartManager.getChartAsBase64 === 'function') {
            try {
                chartImage = await ChartManager.getChartAsBase64();
            } catch (chartError) {
                console.warn('[exportReport] No se pudo capturar gráfico:', chartError);
            }
        }

        // ✅ USAR LOS DATOS ALMACENADOS
        const exportConfig = {
            type: 'single',
            format: format,
            lang: LanguageManager.currentLang || 'es',
            
            results: {
                filename: currentAnalysisData.filename,
                sample_name: currentAnalysisData.sample_name,
                timestamp: currentAnalysisData.timestamp,
                
                analysis: {
                    fluor_percentage: currentAnalysisData.fluor_percentage,
                    pfas_percentage: currentAnalysisData.pfas_percentage,
                    pifas_percentage: currentAnalysisData.pifas_percentage,
                    pifas_concentration: currentAnalysisData.pifas_concentration,
                    pfas_concentration: currentAnalysisData.concentration,
                    total_area: currentAnalysisData.total_area,
                    fluor_area: currentAnalysisData.fluor_area,
                    pfas_area: currentAnalysisData.pfas_area,
                    pifas_area: currentAnalysisData.pifas_area
                },
                
                quality_score: currentAnalysisData.quality_score,
                quality_classification: currentAnalysisData.quality_classification,
                signal_to_noise: currentAnalysisData.snr,
                snr: currentAnalysisData.snr,
                
                sample_concentration: currentAnalysisData.sample_concentration,
                
                // ✅ PICOS CON TODOS LOS DATOS
                peaks: currentAnalysisData.peaks.map(peak => ({
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
                })),
                
                quality_metrics: currentAnalysisData.quality_metrics || {}
            },
            
            chart_image: chartImage,
            
            company_data: {
                name: companyProfile.company_name,
                logo: companyProfile.logo_url,
                address: companyProfile.company_address,
                phone: companyProfile.contact_phone,
                email: companyProfile.contact_email
            }
        };

        console.log('📦 Configuración de exportación:', exportConfig);

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
async function loadResult(measurementId, filename) {
    try {
        console.log(`[loadResult] Cargando medición ${measurementId}...`);
        
        UIManager.showLoading(LanguageManager.t('messages.loading') || 'Cargando...');
        
        // Obtener la medición completa del servidor
        const measurement = await APIClient.getMeasurement(measurementId);
        
        console.log('[loadResult] Medición obtenida:', measurement);

        currentAnalysisData = {
            filename: measurement.filename || measurement.sample_name || 'Muestra',
            sample_name: measurement.sample_name || measurement.filename || 'Muestra',
            timestamp: measurement.timestamp || measurement.created_at || new Date().toISOString(),
            
            analysis: measurement.analysis || {},
            
            fluor_percentage: measurement.fluor_percentage || measurement.analysis?.fluor_percentage || 0,
            pfas_percentage: measurement.pfas_percentage || measurement.pifas_percentage || measurement.analysis?.pfas_percentage || 0,
            pifas_percentage: measurement.pifas_percentage || measurement.analysis?.pifas_percentage || 0,
            concentration: measurement.concentration || measurement.analysis?.pifas_concentration || 0,
            pifas_concentration: measurement.analysis?.pifas_concentration || measurement.concentration || 0,
            
            quality_score: measurement.quality_score || 0,
            quality_classification: measurement.quality_classification || 'N/A',
            signal_to_noise: measurement.signal_to_noise || measurement.snr || 0,
            snr: measurement.snr || measurement.signal_to_noise || 0,
            
            total_area: measurement.analysis?.total_area || measurement.total_area || 0,
            fluor_area: measurement.analysis?.fluor_area || 0,
            pfas_area: measurement.analysis?.pfas_area || measurement.analysis?.pifas_area || 0,
            pifas_area: measurement.analysis?.pifas_area || 0,
            sample_concentration: measurement.sample_concentration || 0,
            
            peaks: measurement.peaks || [],
            quality_metrics: measurement.quality_metrics || {},
            
            ppm: measurement.ppm || [],
            intensity: measurement.intensity || []
        };
        
        console.log('✅ Datos de medición almacenados:', currentAnalysisData);
        
        // Cambiar a la pestaña del analizador
        UIManager.switchTab('analyzer');
        
        // Mostrar los resultados en la interfaz
        if (window.ChartManager && typeof ChartManager.plotResults === 'function') {
            try {
                ChartManager.plotResults(measurement);
            } catch (chartError) {
                console.warn('[loadResult] Error graficando:', chartError);
            }
        }
        
        UIManager.displayResults(measurement);

        setupMoleculeViewers(measurement);
        
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

/**
 * 🆕 NUEVA FUNCIÓN
 * Configura los botones y contenedores de 2D/3D
 * basándose en los resultados del análisis.
 */
function setupMoleculeViewers(analysisResults) {
    // Referencias a todos los botones y contenedores
    const toggle3DBtn = document.getElementById('toggle3DModelBtn');
    const molecule3DContainer = document.getElementById('molecule3DContainer');
    const toggle2DBtn = document.getElementById('toggle2DInfoBtn');
    const molecule2DContainer = document.getElementById('molecule2DContainer');

    // Limpiar/resetear todo
    molecule3DContainer.innerHTML = '';
    molecule3DContainer.style.display = 'none';
    molecule2DContainer.style.display = 'none';

    // Coger la info de la molécula (si existe)
    // El backend ahora envía 'molecule_info'
    const moleculeInfo = analysisResults.molecule_info; 

    if (moleculeInfo) {
        // --- 1. Configurar el Botón 3D ---
        toggle3DBtn.style.display = 'inline-flex';
        toggle3DBtn.onclick = () => {
            const isVisible = molecule3DContainer.style.display === 'block';
            if (isVisible) {
                molecule3DContainer.style.display = 'none';
            } else {
                molecule3DContainer.style.display = 'block';
                molecule2DContainer.style.display = 'none'; // Ocultar el 2D
                if (molecule3DContainer.innerHTML === '') { // Cargar solo una vez
                    try {
                        const stage = new NGL.Stage("molecule3DContainer");
                        const filePath = `assets/molecules/${moleculeInfo.file_3d}`; // Usar el objeto
                        stage.loadFile(filePath).then(component => {
                            component.addRepresentation("ball+stick");
                            component.autoView();
                        });
                    } catch(e) { 
                        console.error("Error al cargar NGL Viewer:", e);
                        molecule3DContainer.innerHTML = "<p style='color:red;'>Error al cargar molécula 3D.</p>";
                    }
                }
            }
        };

        // --- 2. Configurar el Botón 2D ---
        toggle2DBtn.style.display = 'inline-flex';
        toggle2DBtn.onclick = () => {
            const isVisible = molecule2DContainer.style.display === 'block';
            if (isVisible) {
                molecule2DContainer.style.display = 'none';
            } else {
                molecule2DContainer.style.display = 'block';
                molecule3DContainer.style.display = 'none'; // Ocultar el 3D

                // Rellenar los datos (esto se hace cada vez, es rápido)
                document.getElementById('moleculeName').textContent = moleculeInfo.name;
                document.getElementById('molecule2DImage').src = moleculeInfo.image_2d;
                document.getElementById('moleculeFormula').textContent = moleculeInfo.formula;
                document.getElementById('moleculeWeight').textContent = moleculeInfo.mol_weight;
            }
        };

    } else {
        // No se detectó molécula, ocultar AMBOS botones
        toggle3DBtn.style.display = 'none';
        toggle3DBtn.onclick = null;
        toggle2DBtn.style.display = 'none';
        toggle2DBtn.onclick = null;
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