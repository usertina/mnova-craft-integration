/**
 * app.js
 * Lógica principal del frontend, modificada para multi-empresa.
 * Asume que 'CURRENT_COMPANY_PROFILE' ha sido definido en app.html
 * y que 'LanguageManager', 'UIManager', 'ChartManager' y 'APP_LOGGER' están disponibles globalmente.
 */

let currentHistoryPage = 1;

document.addEventListener('DOMContentLoaded', () => {
    // Función auto-ejecutable asíncrona para la inicialización
    (async () => {
        try {
            // 1. Validar que el perfil de empresa se cargó (definido en app.html)
            if (typeof CURRENT_COMPANY_PROFILE === 'undefined' || !CURRENT_COMPANY_PROFILE) {
                // Este error es crítico, la app no puede funcionar.
                throw new Error("No se pudo cargar el perfil de la empresa. La aplicación no puede iniciarse.");
            }
            
            // 2. Aplicar Branding (como se describe en tu resumen)
            applyBranding(CURRENT_COMPANY_PROFILE);
            
            // 3. Cargar el idioma basado en el perfil de la empresa
            const lang = CURRENT_COMPANY_PROFILE.language || 'en'; // 'en' por defecto
            await LanguageManager.changeLanguage(lang);

            APP_LOGGER.info(`Idioma cargado: ${lang}`);

            // 4. Inicializar el resto de la aplicación
            await initializeApp();

        } catch (error) {
            APP_LOGGER.error("Error crítico en la inicialización:", error);
            // Usar la nueva función de error crítico
            showCriticalError(error.message || 'Error desconocido al iniciar.');
        }
    })();
});

/**
 * Aplica el branding de la empresa (logo y nombre) a la cabecera.
 * (Función nueva según tu descripción)
 */
function applyBranding(profile) {
    if (!profile) return;

    try {
        const logoElement = document.getElementById('company-logo'); // Asumiendo ID 'company-logo' en app.html
        const nameElement = document.getElementById('company-name-header'); // Asumiendo ID 'company-name-header' en app.html

        if (logoElement) {
            logoElement.src = profile.logo_url || 'assets/images/default_logo.png'; // Fallback
            logoElement.alt = `${profile.company_name} Logo`;
            logoElement.onerror = () => { 
                logoElement.src = 'assets/images/default_logo.png'; 
                APP_LOGGER.warn(`No se pudo cargar el logo: ${profile.logo_url}`);
            };
        }
        
        if (nameElement) {
            nameElement.textContent = profile.company_name;
        }

        // (Opcional) Aplicar colores primarios/secundarios si el CSS está configurado para usar variables
        // document.documentElement.style.setProperty('--color-primary', profile.primary_color || '#0052cc');
        // document.documentElement.style.setProperty('--color-secondary', profile.secondary_color || '#f4f5f7');

        APP_LOGGER.debug("Branding aplicado:", profile.company_name);

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
    const file = FileProcessor.getCurrentFile(); // ✅ Usar FileProcessor
    
    if (!file) {
        UIManager.showNotification(
            LanguageManager.t('errors.noFileSelected') || 'No se ha seleccionado ningún archivo',
            'error'
        );
        return;
    }

    try {
        UIManager.showLoading(LanguageManager.t('messages.analyzing') || 'Analizando...');
        
        // Recoger parámetros de la UI
        const parameters = UIManager.getCurrentAnalysisParams();

        // APIClient usa CURRENT_COMPANY_PROFILE automáticamente
        const results = await APIClient.analyzeSpectrum(file, parameters);

        APP_LOGGER.info('Análisis completado:', results);

        // Mostrar resultados en gráfico (si ChartManager existe)
        if (window.ChartManager && typeof ChartManager.plotResults === 'function') {
            try {
                ChartManager.plotResults(results);
            } catch (chartError) {
                APP_LOGGER.warn('Error graficando resultados:', chartError);
            }
        }
        
        // Mostrar resultados en tablas
        UIManager.displayResults(results);
        
        // Recargar historial para mostrar el nuevo item
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
        
        // Limpiar archivo después del análisis
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
        // Si no se especificó formato, mostrar menú
        if (!format) {
            showExportFormatMenu('single');
            return;
        }

        UIManager.showLoading(LanguageManager.t('messages.exporting') || 'Exportando...');

        // Obtener datos del análisis actual desde la UI
        const results = {
            filename: document.getElementById('sampleName')?.textContent || 'Muestra',
            sample_name: document.getElementById('sampleName')?.textContent || 'Muestra',
            timestamp: new Date().toISOString(),
            analysis: {
                fluor_percentage: parseFloat(document.getElementById('fluorResult')?.textContent) || 0,
                pifas_percentage: parseFloat(document.getElementById('pifasResult')?.textContent) || 0,
                pfas_percentage: parseFloat(document.getElementById('pifasResult')?.textContent) || 0
            },
            quality_score: parseFloat(document.querySelector('#qualityProgressBar .progress-bar')?.textContent?.split('/')[0]) || 0,
            peaks: [] // TODO: Extraer picos de la tabla si están disponibles
        };

        // Capturar gráfico si existe
        let chartImage = null;
        if (window.ChartManager && typeof ChartManager.getChartAsBase64 === 'function') {
            try {
                chartImage = await ChartManager.getChartAsBase64();
            } catch (chartError) {
                console.warn('[exportReport] No se pudo capturar gráfico:', chartError);
            }
        }

        const exportConfig = {
            type: 'single',
            format: format,
            lang: LanguageManager.currentLang || 'es',
            results: results,
            chart_image: chartImage
        };

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
function showExportFormatMenu(exportType = 'single') {
    const formats = [
        { value: 'pdf', label: 'PDF', icon: 'fa-file-pdf' },
        { value: 'docx', label: 'Word (DOCX)', icon: 'fa-file-word' },
        { value: 'csv', label: 'CSV', icon: 'fa-file-csv' }
    ];

    const menu = document.createElement('div');
    menu.className = 'export-format-menu';
    menu.innerHTML = `
        <div class="export-format-overlay"></div>
        <div class="export-format-dialog">
            <h3>${LanguageManager.t('analyzer.exportReport') || 'Exportar Reporte'}</h3>
            <p>Selecciona el formato de exportación:</p>
            <div class="export-format-options">
                ${formats.map(fmt => `
                    <button class="export-format-btn" data-format="${fmt.value}">
                        <i class="fas ${fmt.icon}"></i>
                        <span>${fmt.label}</span>
                    </button>
                `).join('')}
            </div>
            <button class="export-format-cancel">Cancelar</button>
        </div>
    `;

    document.body.appendChild(menu);

    // Event listeners
    menu.querySelectorAll('.export-format-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const format = btn.dataset.format;
            document.body.removeChild(menu);
            
            if (exportType === 'single') {
                await exportReport(format);
            } else if (exportType === 'dashboard') {
                await exportDashboard(format);
            }
        });
    });

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