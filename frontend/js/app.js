class RMNAnalyzerApp {
    constructor() {
        this.currentFile = null;
        this.spectrumData = null;
        this.analysisResults = null;
        this.isConnected = false;
        
        this.initializeApp();

        // --- CAMBIO AQUÍ ---
        // Movimos el 'resize' listener de chartManager.js aquí
        // para que solo se active después de que la app esté lista.
        window.addEventListener('resize', () => {
            if (ChartManager.chart) {
                ChartManager.resizeChart();
            }
        });
    }
    
    async initializeApp() {
        try {
            // 1. Primero cargar configuraciones
            window.APP_LOGGER.info('Initializing RMN Analyzer App...');
            
            // 2. Inicializar sistema de idiomas
            await LanguageManager.init();
            LanguageManager.subscribe((lang) => this.onLanguageChanged(lang));
            
            // 3. Configurar componentes de UI
            this.setupEventListeners();
            
            
            // 4. Verificar conexión con backend
            await this.checkBackendConnection();
            
            // 5. Mostrar aplicación
            this.hideLoadingScreen();
            
            window.APP_LOGGER.info('App initialized successfully');
            
        } catch (error) {
            window.APP_LOGGER.error('Failed to initialize app:', error);
            this.showNotification('errors.initialization', 'error');
        }
    }
    
    setupEventListeners() {
        // File upload - single
        document.getElementById('browseFiles').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
        
        document.getElementById('fileInput').addEventListener('change', (e) => {
            this.handleFileSelection(e.target.files[0]);
        });
        
        // File upload - batch
        document.getElementById('browseBatchFiles').addEventListener('click', () => {
            document.getElementById('batchFileInput').click();
        });
        
        document.getElementById('batchFileInput').addEventListener('change', (e) => {
            this.handleBatchFileSelection(e.target.files);
        });
        
        // Drag and drop
        this.setupDragAndDrop('uploadArea', (file) => this.handleFileSelection(file));
        this.setupDragAndDrop('batchUploadArea', (files) => this.handleBatchFileSelection(files));
        
        // Analysis buttons
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.performAnalysis();
        });
        
        document.getElementById('runBatchAnalysis').addEventListener('click', () => {
            this.performBatchAnalysis();
        });
        
        document.getElementById('exportBtn').addEventListener('click', () => {
            this.exportReport();
        });

        // ====================================================================
        // BLOQUE DE NAVEGACIÓN RESTAURADO
        // ====================================================================
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Usamos currentTarget para asegurarnos de que el dataset.tab
                // se lee del botón aunque el usuario pulse en el icono <i>
                const tab = e.currentTarget.dataset.tab; 
                this.switchTab(tab);
                
                // Cargar historial al abrir la tab
                if (tab === 'history') {
                    this.loadHistory();
                    // Configurar filtros si no se han configurado
                    if (!this.historyFiltersSetup) {
                        this.setupHistoryFilters();
                        this.historyFiltersSetup = true;
                    }
                }
                
                // Cargar métodos guardados al abrir la tab
                if (tab === 'methods') {
                    loadSavedMethods();
                }
                // Cargar dashboard al abrir la tab
                if (tab === 'dashboard') {
                    if (window.dashboardManager) {
                        window.dashboardManager.init();
                    } else {
                        console.error('Dashboard Manager not initialized');
                    }
                }
                
                // Cargar comparación al abrir la tab
                if (tab === 'comparison') {
                    if (window.dashboardManager) {
                        window.dashboardManager.initComparison();
                    } else {
                        console.error('Dashboard Manager not initialized');
                    }
                }
            });
        });

        // Fullscreen (RESTAURADO)
        document.getElementById('fullscreenBtn').addEventListener('click', () => {
            this.toggleFullscreen();
        });


        // ====================================================================
        
        // --- NUEVOS LISTENERS AÑADIDOS ---
        // History buttons
        const refreshHistoryBtn = document.getElementById('refreshHistoryBtn');
        if (refreshHistoryBtn) {
            refreshHistoryBtn.addEventListener('click', () => {
                this.loadHistory();
                this.showNotification('history.refresh', 'success');
            });
        }

        // CORREGIDO: Ahora llama al método de la clase
        const clearHistoryBtn = document.getElementById('clearHistoryBtn');
        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', () => {
                this.clearHistory();
            });
        }
    }
    
    setupDragAndDrop(elementId, callback) {
        const element = document.getElementById(elementId);
        
        element.addEventListener('dragover', (e) => {
            e.preventDefault();
            element.classList.add('dragover');
        });
        
        element.addEventListener('dragleave', () => {
            element.classList.remove('dragover');
        });
        
        element.addEventListener('drop', (e) => {
            e.preventDefault();
            element.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                callback(files.length === 1 ? files[0] : files);
            }
        });
    }
    
    async checkBackendConnection() {
        try {
            this.updateConnectionStatus('connecting');
            
            const result = await APIClient.checkConnection();
            this.isConnected = true;
            this.updateConnectionStatus('connected');
            
            this.showNotification('notifications.connected', 'success');
            
        } catch (error) {
            this.isConnected = false;
            this.updateConnectionStatus('disconnected');
            
            if (window.APP_CONFIG.autoReconnect) {
                setTimeout(() => this.checkBackendConnection(), window.APP_CONFIG.reconnectInterval);
            }
        }
    }
    
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connectionStatus');
        const dot = statusElement.querySelector('.connection-dot');
        
        statusElement.className = `connection-status ${status}`;
        dot.className = `fas fa-circle connection-dot ${status}`;
        
        const texts = {
            connecting: 'connection.connecting',
            connected: 'connection.connected', 
            disconnected: 'connection.disconnected'
        };
        
        const textElement = statusElement.querySelector('span');
        textElement.setAttribute('data-i18n', texts[status]);
        LanguageManager.applyTranslations();
    }
    
    async handleFileSelection(file) {
        if (!file) return;
        
        if (!this.isConnected) {
            this.showNotification('errors.backendUnavailable', 'error');
            return;
        }
        
        this.currentFile = file;
        
        this.showNotification('notifications.fileLoaded', 'success', {
            filename: file.name
        });
        
        // Enable analyze button
        document.getElementById('analyzeBtn').disabled = false;
        
        // Update sample name with translation
        document.getElementById('sampleName').textContent = 
            LanguageManager.t('analyzer.sampleName', { name: file.name });
        
        // Show file in list
        this.addFileToList(file, 'fileList');
        
        try {
            const content = await this.readFileContent(file);
            this.previewFile(content);
        } catch (error) {
            this.showNotification('notifications.fileReadError', 'error');
        }
    }
    
    async performAnalysis() {
        if (!this.currentFile || !this.isConnected) return;
        
        const analyzeBtn = document.getElementById('analyzeBtn');
        
        // Update button state
        const analyzingText = LanguageManager.t('analyzer.analyzing');
        analyzeBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${analyzingText}`;
        analyzeBtn.disabled = true;
        
        try {
            const params = this.getAnalysisParameters();
            const results = await APIClient.analyzeSpectrum(this.currentFile, params);
            
            this.analysisResults = results;
            this.updateResultsDisplay(results);
            
            this.showNotification('notifications.analysisComplete', 'success');
            
            // Enable export button
            document.getElementById('exportBtn').disabled = false;
            
        } catch (error) {
            this.showNotification('notifications.analysisError', 'error', {
                error: error.message
            });
        } finally {
            const runAnalysisText = LanguageManager.t('analyzer.runAnalysis');
            analyzeBtn.innerHTML = `<i class="fas fa-play"></i> ${runAnalysisText}`;
            analyzeBtn.disabled = false;
        }
    }
    
    updateResultsDisplay(results) {
        // Update chart
        if (results.spectrum) {
            ChartManager.updateSpectrumChart(results.spectrum);
        }
        
        // Update result cards
        if (results.analysis) {
            document.getElementById('fluorResult').textContent = 
                results.analysis.fluor_percentage?.toFixed(2) || '--';
            document.getElementById('pifasResult').textContent = 
                results.analysis.pifas_percentage?.toFixed(2) || '--';
            document.getElementById('concentrationResult').textContent = 
                results.analysis.concentration?.toFixed(2) || '--';
            document.getElementById('qualityResult').textContent = 
                results.quality_score?.toFixed(1) || '--';
        }
        
        // Update detailed table
        if (results.detailed_analysis) {
            this.updateResultsTable(results.detailed_analysis);
        }
    }
    
    updateResultsTable(detailedResults) {
        const tbody = document.querySelector('#resultsTable tbody');
        tbody.innerHTML = '';
        
        Object.entries(detailedResults).forEach(([param, data]) => {
            // Formatear el valor
            let displayValue = '--';
            if (data.value !== null && data.value !== undefined) {
                if (typeof data.value === 'number') {
                    displayValue = data.value.toFixed(4);
                } else {
                    displayValue = data.value;
                }
            }
            
            // Traducir nombre del parámetro
            const translatedParam = LanguageManager.t(`results.${param}`) || param;
            
            // Reemplazar N/A por guión
            let displayLimits = data.limits || '--';
            if (displayLimits === 'N/A' || displayLimits === 'n/a') {
                displayLimits = '—';  // ← ESTO ELIMINA EL N/A
            }
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${translatedParam}</td>
                <td>${displayValue}</td>
                <td>${data.unit || '--'}</td>
                <td>${displayLimits}</td>
            `;
            tbody.appendChild(row);
        });
    }

    
    getAnalysisParameters() {
        return {
            fluor_range: {
                min: parseFloat(document.getElementById('fluorMin').value),
                max: parseFloat(document.getElementById('fluorMax').value)
            },
            pifas_range: {
                min: parseFloat(document.getElementById('pifasMin').value),
                max: parseFloat(document.getElementById('pifasMax').value)
            },
            concentration: parseFloat(document.getElementById('concentration').value)
        };
    }
    
    readFileContent(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = e => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsText(file);
        });
    }
    
    previewFile(content) {
        // Basic preview - can be extended based on file format
        window.APP_LOGGER.debug('File preview:', content.substring(0, 200));
    }
    
    onLanguageChanged(lang) {
        this.updateDynamicTexts();
        
        // Actualizar traducciones del gráfico
        ChartManager.refreshTranslations(lang);
        
        if (this.analysisResults) {
            this.updateResultsDisplay(this.analysisResults);
        }
    }
    
    updateDynamicTexts() {
        // Update dynamic texts that don't have data-i18n
        const sampleName = document.getElementById('sampleName');
        if (this.currentFile) {
            sampleName.textContent = LanguageManager.t('analyzer.sampleName', { 
                name: this.currentFile.name 
            });
        }
    }
    
    showNotification(messageKey, type = 'info', params = {}) {
        const message = LanguageManager.t(messageKey, params);
        UIManager.showNotification(message, type);
    }
    
    switchTab(tabName) {
    // Verificar si la tab existe
    const tabElement = document.getElementById(`${tabName}-tab`);
    if (!tabElement) {
        console.warn(`Tab ${tabName} no existe aún`);
        return;
    }
    
    // Update navigation
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const navBtn = document.querySelector(`[data-tab="${tabName}"]`);
    if (navBtn) {
        navBtn.classList.add('active');
    }
    
    // Show selected tab
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    tabElement.classList.add('active');
    }
    
    hideLoadingScreen() {
        setTimeout(() => {
            document.getElementById('loadingScreen').classList.add('hidden');
            document.getElementById('app').classList.remove('hidden');
        }, 1000);
    }
    
    // Batch processing methods
    handleBatchFileSelection(files) {
        if (!files || files.length === 0) return;
        
        this.batchFiles = Array.from(files);
        document.getElementById('runBatchAnalysis').disabled = false;
        
        // Show files in batch list
        const fileList = document.getElementById('batchFileList');
        fileList.innerHTML = '';
        
        this.batchFiles.forEach(file => {
            this.addFileToList(file, 'batchFileList');
        });
        
        this.showNotification('notifications.batchFilesLoaded', 'success', {
            count: files.length
        });
    }
    
    addFileToList(file, listId) {
        const list = document.getElementById(listId);
        const fileElement = document.createElement('div');
        fileElement.className = 'file-item';
        fileElement.innerHTML = `
            <i class="fas fa-file"></i>
            <span class="file-name">${file.name}</span>
            <span class="file-size">(${this.formatFileSize(file.size)})</span>
        `;
        list.appendChild(fileElement);
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    async performBatchAnalysis() {
        if (!this.batchFiles || !this.isConnected) return;
        
        const batchBtn = document.getElementById('runBatchAnalysis');
        const analyzingText = LanguageManager.t('batch.analyzing');
        batchBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${analyzingText}`;
        batchBtn.disabled = true;
        
        try {
            const params = this.getAnalysisParameters();
            const results = await APIClient.batchAnalyze(this.batchFiles, params);
            
            this.displayBatchResults(results);
            this.showNotification('notifications.batchComplete', 'success', {
                count: results.total_files
            });
            
        } catch (error) {
            this.showNotification('notifications.batchError', 'error', {
                error: error.message
            });
        } finally {
            const runAnalysisText = LanguageManager.t('batch.runAnalysis');
            batchBtn.innerHTML = `<i class="fas fa-play"></i> ${runAnalysisText}`;
            batchBtn.disabled = false;
        }
    }
    
    displayBatchResults(results) {
        const resultsContainer = document.getElementById('batchResults');
        resultsContainer.innerHTML = '';
        
        if (results.results && results.results.length > 0) {
            const table = document.createElement('table');
            table.className = 'batch-results-table';
            
            // Create header
            const header = document.createElement('thead');
            header.innerHTML = `
                <tr>
                    <th data-i18n="results.parameter">Archivo</th>
                    <th data-i18n="results.fluor">Flúor %</th>
                    <th data-i18n="results.pifas">PIFAS %</th>
                    <th data-i18n="results.concentration">Concentración</th>
                </tr>
            `;
            table.appendChild(header);
            
            // Create body
            const tbody = document.createElement('tbody');
            results.results.forEach(result => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${result.filename}</td>
                    <td>${result.analysis?.fluor_percentage?.toFixed(2) || '--'}</td>
                    <td>${result.analysis?.pifas_percentage?.toFixed(2) || '--'}</td>
                    <td>${result.analysis?.concentration?.toFixed(2) || '--'}</td>
                `;
                tbody.appendChild(row);
            });
            table.appendChild(tbody);
            
            resultsContainer.appendChild(table);
            LanguageManager.applyTranslations();
        }
    }
    
    async exportReport() {
        if (!this.analysisResults) return;
        
        try {
            await APIClient.exportReport(this.analysisResults, 'csv');
            this.showNotification('notifications.exportSuccess', 'success');
        } catch (error) {
            this.showNotification('notifications.exportError', 'error', {
                error: error.message
            });
        }
    }
    
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.error('Error attempting to enable fullscreen:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }

    // ============================================================================
    // MÉTODOS DE HISTORIAL Y FILTROS
    // ============================================================================
    
    // (EL PRIMER loadHistory() DUPLICADO HA SIDO ELIMINADO)

    displayHistory(analyses) {
        const historyList = document.getElementById('historyList');
        
        if (!analyses || analyses.length === 0) {
            historyList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-folder-open"></i>
                    <p data-i18n="history.empty">No hay análisis guardados</p>
                    <p class="empty-subtitle" data-i18n="history.emptySubtitle">Los análisis aparecerán aquí automáticamente</p>
                </div>
            `;
            LanguageManager.applyTranslations();
            return;
        }
        
        historyList.innerHTML = analyses.map(analysis => {
            // Formatear valores con verificación de null/undefined
            const fluor = analysis.fluor != null ? analysis.fluor.toFixed(2) : '--';
            const pfas = analysis.pfas != null ? analysis.pfas.toFixed(2) : '--';
            const quality = analysis.quality != null ? analysis.quality.toFixed(1) : '--';
            
            // Formatear fecha
            const date = new Date(analysis.created);
            const formattedDate = date.toLocaleString();
            
            // Usar filename original si existe, si no usar name
            const displayName = analysis.filename || analysis.name;
            
            return `
                <div class="history-item">
                    <div class="history-item-content" onclick="rmnApp.loadAnalysisFromHistory('${analysis.name}')">
                        <div class="history-item-header">
                            <div class="history-item-title">
                                <i class="fas fa-file"></i> ${displayName}
                            </div>
                            <div class="history-item-date">
                                ${formattedDate}
                            </div>
                        </div>
                        <div class="history-item-stats">
                            <div class="history-stat">
                                <i class="fas fa-vial"></i>
                                <span>Flúor: ${fluor}%</span>
                            </div>
                            <div class="history-stat">
                                <i class="fas fa-chart-bar"></i>
                                <span>PFAS: ${pfas}%</span>
                            </div>
                            <div class="history-stat">
                                <i class="fas fa-check-circle"></i>
                                <span>Calidad: ${quality}/10</span>
                            </div>
                        </div>
                    </div>
                    <div class="history-item-actions">
                        <button class="btn btn-icon btn-view" 
                                onclick="event.stopPropagation(); rmnApp.viewAnalysis('${analysis.name}')"
                                title="Ver análisis">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-icon btn-delete" 
                                onclick="event.stopPropagation(); rmnApp.deleteAnalysis('${analysis.name}', '${displayName}')"
                                title="Eliminar análisis">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    // ============================================================================
    // FUNCIONES DE FILTRADO DE HISTORIAL
    // ============================================================================
    
    setupHistoryFilters() {
        const searchInput = document.getElementById('historySearch');
        const dateFilter = document.getElementById('historyDateFilter');
        
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                this.filterHistory();
            });
        }
        
        if (dateFilter) {
            dateFilter.addEventListener('change', () => {
                this.filterHistory();
            });
        }
    }
    
    filterHistory() {
        if (!this.allAnalyses) {
            // Si this.allAnalyses no está cargado, no hacer nada.
            // loadHistory() se encargará de llamar a filterHistory() cuando tenga los datos.
            return;
        }
        
        const searchTerm = document.getElementById('historySearch').value.toLowerCase();
        const dateFilter = document.getElementById('historyDateFilter').value;
        
        let filtered = [...this.allAnalyses];
        
        // Filtrar por búsqueda
        if (searchTerm) {
            filtered = filtered.filter(analysis => {
                const name = (analysis.filename || analysis.name || '').toLowerCase();
                return name.includes(searchTerm);
            });
        }
        
        // Filtrar por fecha
        if (dateFilter !== 'all') {
            const now = new Date();
            let startDate;
            
            switch(dateFilter) {
                case 'today':
                    startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                    break;
                case 'week':
                    startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                    break;
                case 'month':
                    startDate = new Date(now.getFullYear(), now.getMonth(), 1);
                    break;
            }
            
            if (startDate) {
                filtered = filtered.filter(analysis => {
                    const analysisDate = new Date(analysis.created);
                    return analysisDate >= startDate;
                });
            }
        }
        
        this.displayHistory(filtered);
    }
    
    // ============================================================================
    // FUNCIONES PARA VER Y ELIMINAR ANÁLISIS
    // ============================================================================
    
    viewAnalysis(filename) {
        // Cargar y mostrar el análisis en el tab del Analizador
        this.loadAnalysisFromHistory(filename);
    }
    
    async loadAnalysisFromHistory(filename) {
        try {
            // Usar el método correcto de APIClient
            const data = await APIClient.getResult(filename);
            
            this.analysisResults = data;
            this.updateResultsDisplay(data);
            this.switchTab('analyzer');
            
            // Notificación con clave de traducción
            const displayName = data.filename || filename;
            this.showNotification('notifications.fileLoaded', 'success', {
                filename: displayName
            });
            
        } catch (error) {
            console.error('Error loading analysis:', error);
            this.showNotification('errors.analysisFailed', 'error');
        }
    }
    
/**
 * Cargar historial de análisis desde el servidor
 */
    async loadHistory() {
        try {
            const data = await APIClient.getAnalysisList();
            this.allAnalyses = data.analyses || [];
            this.filterHistory(); // Aplica filtros y muestra
            
            window.APP_LOGGER.debug(`History loaded: ${this.allAnalyses.length} analyses`);
        } catch (error) {
            console.error('Error loading history:', error);
            this.showNotification('errors.historyLoad', 'error');
            this.displayHistory([]);
        }
    }

    /**
     * Limpiar TODO el historial (con doble confirmación)
     */
    async clearHistory() {
        // Primera confirmación
        const confirmMessage = LanguageManager.t('history.confirmClearAll') || 
            '⚠️ ADVERTENCIA\n\n' +
            'Esta acción eliminará TODOS los análisis guardados.\n\n' +
            '¿Estás seguro de que deseas continuar?';
        
        if (!confirm(confirmMessage)) {
            return;
        }
        
        // Segunda confirmación - pedir escribir texto
        const secondConfirm = prompt(
            LanguageManager.t('history.confirmClearAll2') || 
            'Para confirmar, escribe "ELIMINAR" (en mayúsculas):'
        );
        
        if (secondConfirm !== 'ELIMINAR') {
            this.showNotification('history.clearCancelled', 'info');
            return;
        }
        
        try {
            // Mostrar loading
            const clearBtn = document.getElementById('clearHistoryBtn');
            if (clearBtn) {
                UIManager.updateButtonState(clearBtn, 'loading');
            }
            
            // Llamar al backend
            const result = await APIClient.clearAllHistory();
            
            // Limpiar UI
            this.allAnalyses = [];
            this.displayHistory([]);
            
            // Si el análisis actual estaba en el historial, limpiarlo
            if (this.analysisResults) {
                this.clearAnalysisResults();
            }
            
            // Mostrar resultado
            this.showNotification('history.clearSuccess', 'success', {
                count: result.deleted_count
            });
            
            window.APP_LOGGER.info(`History cleared: ${result.deleted_count} analyses deleted`);
            
        } catch (error) {
            console.error('Error clearing history:', error);
            this.showNotification('history.clearError', 'error', {
                error: error.message
            });
        } finally {
            // Restaurar botón
            const clearBtn = document.getElementById('clearHistoryBtn');
            if (clearBtn) {
                UIManager.updateButtonState(clearBtn, 'default');
            }
        }
    }

    /**
     * Eliminar un análisis específico
     */
    async deleteAnalysis(filename, displayName) {
        // Obtener mensaje traducido para la confirmación
        const confirmMessage = LanguageManager.t('history.confirmDelete', { 
            name: displayName 
        }) || `¿Estás seguro de que quieres eliminar el análisis "${displayName}"?\n\nEsta acción no se puede deshacer.`;
        
        if (!confirm(confirmMessage)) {
            return;
        }
        
        try {
            // Llamar al backend
            await APIClient.deleteAnalysis(filename);
            
            // Notificar éxito
            this.showNotification('history.deleteSuccess', 'success', {
                name: displayName
            });
            
            // Recargar el historial
            await this.loadHistory();
            
            // Si el análisis eliminado era el que estaba siendo mostrado, limpiar la vista
            if (this.analysisResults && this.analysisResults.filename === displayName) {
                this.clearAnalysisResults();
            }
            
            window.APP_LOGGER.info(`Analysis deleted: ${filename}`);
            
        } catch (error) {
            console.error('Error deleting analysis:', error);
            this.showNotification('history.deleteError', 'error', {
                error: error.message
            });
        }
    }

    /**
     * Limpiar los resultados mostrados en el analizador
     */
    clearAnalysisResults() {
        // Limpiar valores de las tarjetas
        document.getElementById('fluorResult').textContent = '--';
        document.getElementById('pifasResult').textContent = '--';
        document.getElementById('concentrationResult').textContent = '--';
        document.getElementById('qualityResult').textContent = '--';
        
        // Limpiar tabla detallada
        const tbody = document.querySelector('#resultsTable tbody');
        if (tbody) {
            tbody.innerHTML = '';
        }
        
        // Resetear gráfico
        if (ChartManager && ChartManager.chart) {
            ChartManager.chart.data[0].x = [];
            ChartManager.chart.data[0].y = [];
            Plotly.react('spectrumChart', ChartManager.chart.data, ChartManager.chart.layout, ChartManager.config);
        }
        
        // Actualizar título
        document.getElementById('sampleName').setAttribute('data-i18n', 'analyzer.waitingData');
        LanguageManager.applyTranslations();
        
        // Deshabilitar botón de exportar
        document.getElementById('exportBtn').disabled = true;
        
        // Limpiar referencia interna
        this.analysisResults = null;
        this.currentFile = null;
        
        window.APP_LOGGER.debug('Analysis results cleared');
    }  
    
    loadAnalysisFromHistory(filename) {
        // Asumiendo que APIClient tiene un método para esto
        APIClient.getResult(filename) 
            .then(data => {
                this.analysisResults = data;
                this.updateResultsDisplay(data);
                this.switchTab('analyzer');
                this.showNotification('notifications.fileLoaded', 'success', {
                    filename: filename
                });
            })
            .catch(error => {
                this.showNotification('errors.analysisFailed', 'error');
            });
    }

} // <-- FIN DE LA CLASE RMNAnalyzerApp


// ============================================================================
// FUNCIONES GLOBALES PARA GESTIÓN DE MÉTODOS
// (Estas se quedan aquí fuera porque son llamadas por `onclick` en el HTML)
// ============================================================================

function applyMethod(methodType) {
    const methods = {
        pfas: {
            fluorMin: -150,
            fluorMax: -50,
            pifasMin: -130,
            pifasMax: -60,
            concentration: 1.0
        },
        highSens: {
            fluorMin: -160,
            fluorMax: -40,
            pifasMin: -135,
            pifasMax: -55,
            concentration: 0.1
        }
    };
    
    const method = methods[methodType];
    if (method) {
        document.getElementById('fluorMin').value = method.fluorMin;
        document.getElementById('fluorMax').value = method.fluorMax;
        document.getElementById('pifasMin').value = method.pifasMin;
        document.getElementById('pifasMax').value = method.pifasMax;
        document.getElementById('concentration').value = method.concentration;
        
        UIManager.showNotification('Método aplicado correctamente', 'success');
        
        // Cambiar a tab de analizador
        window.rmnApp.switchTab('analyzer');
    }
}

function saveCustomMethod() {
    const methodName = document.getElementById('customMethodName').value;
    const fluorMin = parseFloat(document.getElementById('customFluorMin').value);
    const fluorMax = parseFloat(document.getElementById('customFluorMax').value);
    const pifasMin = parseFloat(document.getElementById('customPfasMin').value);
    const pifasMax = parseFloat(document.getElementById('customPfasMax').value);
    const concentration = parseFloat(document.getElementById('customConcentration').value);
    
    if (!methodName) {
        UIManager.showNotification('Por favor ingresa un nombre para el método', 'warning');
        return;
    }
    
    // Guardar en localStorage
    const savedMethods = JSON.parse(localStorage.getItem('customMethods') || '[]');
    savedMethods.push({
        name: methodName,
        params: {
            fluorMin,
            fluorMax,
            pifasMin,
            pifasMax,
            concentration
        },
        created: new Date().toISOString()
    });
    
    localStorage.setItem('customMethods', JSON.stringify(savedMethods));

    // Usamos LanguageManager para la notificación
    UIManager.showNotification(LanguageManager.t('methods.saved', { name: methodName }), 'success');
    
    // Limpiar formulario
    document.getElementById('customMethodName').value = '';
    
    // Mostrar métodos guardados
    loadSavedMethods();
}

function loadSavedMethods() {
    const savedMethods = JSON.parse(localStorage.getItem('customMethods') || '[]');
    const container = document.getElementById('savedMethods');
    const list = document.getElementById('savedMethodsList');
    
    if (savedMethods.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    list.innerHTML = savedMethods.map((method, index) => `
        <div class="saved-method-item">
            <div class="saved-method-name">
                <i class="fas fa-bookmark"></i> ${method.name}
            </div>
            <div class="saved-method-actions">
                <button class="btn btn-icon" onclick="applyCustomMethod(${index})" title="Aplicar">
                    <i class="fas fa-check"></i>
                </button>
                <button class="btn btn-icon" onclick="deleteCustomMethod(${index})" title="Eliminar">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function applyCustomMethod(index) {
    const savedMethods = JSON.parse(localStorage.getItem('customMethods') || '[]');
    const method = savedMethods[index];
    
    if (method) {
        document.getElementById('fluorMin').value = method.params.fluorMin;
        document.getElementById('fluorMax').value = method.params.fluorMax;
        document.getElementById('pifasMin').value = method.params.pifasMin;
        document.getElementById('pifasMax').value = method.params.pifasMax;
        document.getElementById('concentration').value = method.params.concentration;
        
        UIManager.showNotification(LanguageManager.t('methods.applied', { name: method.name }), 'success');
        window.rmnApp.switchTab('analyzer');
    }
}

function deleteCustomMethod(index) {
    const savedMethods = JSON.parse(localStorage.getItem('customMethods') || '[]');
    const methodName = savedMethods[index].name;
    
    savedMethods.splice(index, 1);
    localStorage.setItem('customMethods', JSON.stringify(savedMethods));
    
    UIManager.showNotification(LanguageManager.t('methods.deleted', { name: methodName }), 'info');
    loadSavedMethods();
}


// ============================================================================
// INICIALIZACIÓN DE LA APP (SECCIÓN ACTUALIZADA)
// ============================================================================
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // 1. Esperamos a que ChartManager esté 100% listo
        await ChartManager.init();
        
        // 2. Solo ENTONCES creamos la aplicación
        window.rmnApp = new RMNAnalyzerApp();

        // 3. AÑADIMOS ESTA LÍNEA para cargar los métodos al inicio
        loadSavedMethods(); 
        
    } catch (error) {
        console.error("Error grave al inicializar la aplicación", error);
    }
});