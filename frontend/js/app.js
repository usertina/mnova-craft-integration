class RMNAnalyzerApp {
    constructor() {
        this.currentFile = null;
        this.spectrumData = null;
        this.analysisResults = null;
        this.isConnected = false;

        this.initializeApp();

        window.addEventListener('resize', () => {
            if (ChartManager.chart) {
                ChartManager.resizeChart();
            }
        });
    }

    async initializeApp() {
        try {
            window.APP_LOGGER.info('Initializing RMN Analyzer App...');
            await LanguageManager.init();
            LanguageManager.subscribe((lang) => this.onLanguageChanged(lang));
            this.setupEventListeners();
            await this.checkBackendConnection();
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

        /* ... (listeners comentados de batch y methods) ... */

        // Drag and drop
        this.setupDragAndDrop('uploadArea', (file) => this.handleFileSelection(file));
        /* ... (drag and drop de batch comentado) ... */


        // Analysis buttons
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.performAnalysis();
        });
        /* ... (botón batch comentado) ... */

        document.getElementById('exportBtn').addEventListener('click', () => {
            this.exportReport();
        });

        // Navigation listeners
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.currentTarget.dataset.tab;
                this.switchTab(tab);

                if (tab === 'history') {
                    this.loadHistory();
                    if (!this.historyFiltersSetup) {
                        this.setupHistoryFilters();
                        this.historyFiltersSetup = true;
                    }
                }
                /* ... (carga de methods comentada) ... */
                if (tab === 'dashboard') {
                   if (window.dashboardManager) window.dashboardManager.init();
                   else console.error('Dashboard Manager not initialized');
                }
                if (tab === 'comparison') {
                    if (window.dashboardManager) window.dashboardManager.initComparison();
                    else console.error('Dashboard Manager not initialized');
                }
            });
        });

        // Fullscreen listener
        document.getElementById('fullscreenBtn').addEventListener('click', () => {
            this.toggleFullscreen();
        });

        // History buttons listeners
        const refreshHistoryBtn = document.getElementById('refreshHistoryBtn');
        if (refreshHistoryBtn) {
            refreshHistoryBtn.addEventListener('click', () => {
                this.loadHistory();
                this.showNotification('history.refresh', 'success');
            });
        }
        const clearHistoryBtn = document.getElementById('clearHistory');
        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', () => {
                this.clearHistory();
            });
        }

        const filterHistoryBtn = document.getElementById('filterHistory');
        if (filterHistoryBtn) {
            filterHistoryBtn.addEventListener('click', () => {
                // Toggle filtros o mostrar menú
                console.log('Filter history clicked - implementar UI de filtros');
                // Puedes implementar un dropdown de fechas aquí
            });
        }

        const searchHistoryInput = document.getElementById('searchHistory');
        if (searchHistoryInput) {
            searchHistoryInput.addEventListener('input', () => {
                this.filterHistory();
            });
        }
    }

    setupDragAndDrop(elementId, callback) {
        const element = document.getElementById(elementId);
        if (!element) return; // Add check if element exists

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
        if (!statusElement) return;
        const dot = statusElement.querySelector('.connection-dot');
        const textElement = statusElement.querySelector('span');

        statusElement.className = `connection-status ${status}`;
        if (dot) dot.className = `fas fa-circle connection-dot ${status}`;

        const texts = {
            connecting: 'connection.connecting',
            connected: 'connection.connected',
            disconnected: 'connection.disconnected'
        };

        if (textElement) {
             textElement.setAttribute('data-i18n', texts[status]);
             LanguageManager.applyTranslations(); // Apply translation only to this element
        }
    }

    async handleFileSelection(file) {
        if (!file) return;
        if (!this.isConnected) {
            this.showNotification('errors.backendUnavailable', 'error');
            return;
        }
        this.currentFile = file;
        this.showNotification('notifications.fileLoaded', 'success', { filename: file.name });
        document.getElementById('analyzeBtn').disabled = false;
        document.getElementById('sampleName').textContent =
            LanguageManager.t('analyzer.sampleName', { name: file.name });
        this.addFileToList(file, 'fileList'); // Clear previous file from list before adding new one
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
        UIManager.updateButtonState(analyzeBtn, 'loading');

        try {
            const params = this.getAnalysisParameters();
            console.log("🔬 Iniciando análisis con parámetros:", params);
            
            const results = await APIClient.analyzeSpectrum(this.currentFile, params);
            
            console.log("📊 Resultados del análisis:", results);
            
            if (results.error) {
                throw new Error(results.error);
            }

            // Log específico para picos
            console.log("🔍 Picos detectados:", results.peaks ? results.peaks.length : 0);
            if (results.peaks && results.peaks.length > 0) {
                console.log("   Primeros 3 picos:", results.peaks.slice(0, 3));
            }

            this.analysisResults = results;
            this.updateResultsDisplay(results);
            this.showNotification('notifications.analysisComplete', 'success');
            document.getElementById('exportBtn').disabled = false;

        } catch (error) {
            console.error("❌ Error en análisis:", error);
            let errorMessage = error.message;
            if (error.details) {
                const lines = error.details.split('\n');
                const lastLine = lines[lines.length - 2] || lines[lines.length - 1];
                errorMessage = lastLine.startsWith('Error:') ? lastLine : error.message;
            }
            this.showNotification('notifications.analysisError', 'error', {
                error: errorMessage
            });
        } finally {
            UIManager.updateButtonState(analyzeBtn, 'default');
        }
    }

    updateResultsDisplay(results) {
        // Update chart
        if (results.spectrum) {
            ChartManager.updateSpectrumChart(results.spectrum, results.peaks || []);
        }

        // Update result cards
        if (results.analysis) {
            UIManager.updateElementText('fluorResult', UIManager.formatNumber(results.analysis.fluor_percentage, 2));
            UIManager.updateElementText('pifasResult', UIManager.formatNumber(results.analysis.pifas_percentage, 2));
            UIManager.updateElementText('qualityResult', UIManager.formatNumber(results.quality_score, 1));
        } else {
            UIManager.updateElementText('fluorResult', '--');
            UIManager.updateElementText('pifasResult', '--');
            UIManager.updateElementText('qualityResult', '--');
        }

        // ### CORRECCIÓN: Actualizar detalles básicos ###
        const peaksCount = results.peaks ? results.peaks.length : 0;
        const totalIntegral = results.analysis ? results.analysis.total_area : 0;
        const snr = results.quality_metrics ? results.quality_metrics.snr : 0;
        
        UIManager.updateElementText('peaksCount', peaksCount);
        UIManager.updateElementText('totalIntegral', UIManager.formatNumber(totalIntegral, 2));
        UIManager.updateElementText('snRatio', UIManager.formatNumber(snr, 2));
        
        console.log(`✅ Detalles actualizados: Picos=${peaksCount}, Integral=${totalIntegral}, SNR=${snr}`);

        // Update detailed table
        if (results.detailed_analysis) {
            this.updateResultsTable(results.detailed_analysis);
        } else {
            const tbody = document.querySelector('#resultsTable tbody');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="4" data-i18n="results.noDetails">No hay datos detallados disponibles.</td></tr>';
                LanguageManager.applyTranslations();
            }
        }

        // Update Peaks Table
        this.updatePeaksTable(results.peaks || []);
        
        // Update Peak Count
        const peaksCountElement = document.getElementById('peaksCount');
        if (peaksCountElement) {
            peaksCountElement.textContent = peaksCount;
        }

        // Update Quality Breakdown
        this.updateQualityBreakdown(results.quality_score, results.quality_breakdown || {});

        // Make sure export button is enabled only if results are valid
        document.getElementById('exportBtn').disabled = !results.analysis;
    }

    // ### MODIFICADO: Updated updateResultsTable function ###
    updateResultsTable(detailedResults) {
        const tbody = document.querySelector('#resultsTable tbody');
        if (!tbody) return; // Exit if table body not found
        tbody.innerHTML = ''; // Clear previous results

        // Check if detailedResults is an object and not empty
        if (typeof detailedResults !== 'object' || detailedResults === null || Object.keys(detailedResults).length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" data-i18n="results.noDetails">No hay datos detallados disponibles.</td></tr>';
             LanguageManager.applyTranslations(); // Translate the message
            return;
        }

        // Iterate through the detailed results object
        Object.entries(detailedResults).forEach(([key, data]) => {
            if (!data || typeof data !== 'object') return; // Skip invalid entries

            // Determine status class
            let statusClass = '';
            if (data.status === 'OK') statusClass = 'status-ok';
            else if (data.status === 'WARN') statusClass = 'status-warn';
            else if (data.status === 'FAIL') statusClass = 'status-fail';
            else statusClass = 'status-info'; // Default for INFO or undefined

            // Use provided parameter name, fallback to key, then translate
            const paramName = data.parameter || key;
            // ### CORRECCIÓN: Usar la clave original 'key' para buscar traducción primero ###
            const translatedParam = LanguageManager.t(`results.${key}`) || LanguageManager.t(paramName) || paramName;

            const displayValue = data.value ?? '--'; // Use nullish coalescing
            const displayUnit = data.unit || '--';
            const displayLimits = data.limits || '—'; // Use em dash for consistency

            const row = document.createElement('tr');
            row.className = statusClass; // Apply status class to the row
            row.innerHTML = `
                <td>${translatedParam}</td>
                <td>${displayValue}</td>
                <td>${displayUnit}</td>
                <td>${displayLimits}</td>
            `;
            tbody.appendChild(row);
        });
         // ### CAMBIO AQUÍ ###
         LanguageManager.applyTranslations(); // Use the general function
    }
     // ### NUEVO: Function to update the peaks table ###
    updatePeaksTable(peaks) {
        const tbody = document.querySelector('#peakTable tbody');
        if (!tbody) {
            console.warn("Peaks table body not found!");
            return;
        }
        tbody.innerHTML = ''; // Clear previous results

        // Log para debug
        console.log("Actualizando tabla de picos:", peaks);

        if (!peaks || peaks.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="empty-state">
                        <i class="fas fa-chart-line"></i>
                        <p data-i18n="peaks.none">No se detectaron picos significativos.</p>
                    </td>
                </tr>
            `;
            LanguageManager.applyTranslations();
            return;
        }

        // Ordenar picos por PPM para la tabla
        const sortedPeaks = [...peaks].sort((a, b) => a.ppm - b.ppm);

        sortedPeaks.forEach(peak => {
            const row = document.createElement('tr');
            
            // Asegurar que todos los valores existen
            const ppm = peak.ppm !== undefined && peak.ppm !== null ? UIManager.formatNumber(peak.ppm, 3) : '--';
            const intensity = peak.intensity !== undefined && peak.intensity !== null ? UIManager.formatNumber(peak.intensity, 2) : '--';
            const relIntensity = peak.relative_intensity !== undefined && peak.relative_intensity !== null ? UIManager.formatNumber(peak.relative_intensity, 1) : '--';
            const width = peak.width_ppm !== undefined && peak.width_ppm !== null ? UIManager.formatNumber(peak.width_ppm, 3) : '--';
            const region = peak.region || '--';
            
            row.innerHTML = `
                <td>${ppm}</td>
                <td>${intensity}</td>
                <td>${relIntensity}</td>
                <td>${width}</td>
                <td>${UIManager.escapeHtml(region)}</td>
            `;
            tbody.appendChild(row);
        });
        
        console.log(`✅ Tabla de picos actualizada: ${sortedPeaks.length} picos mostrados`);
    } 

     // ### NUEVO: Function to update the quality breakdown ###
    updateQualityBreakdown(score, breakdown) {
        const qualityContainer = document.getElementById('qualityBreakdownContainer'); // Needs an element in HTML
        if (!qualityContainer) {
            console.warn("Quality breakdown container not found!");
            return; // Exit if container not found
        }

          // Update progress bar (assuming it exists with id 'qualityProgressBar' and its child div)
        const progressBarDiv = document.getElementById('qualityProgressBar');
        if (progressBarDiv) {
            const bar = progressBarDiv.querySelector('.progress-bar');
            if (bar) {
                const scoreValue = typeof score === 'number' ? score : 0;
                bar.style.width = `${scoreValue * 10}%`;
                bar.textContent = `${UIManager.formatNumber(scoreValue, 1)} / 10`;
                bar.setAttribute('aria-valuenow', scoreValue);
            }
        } else {
               // Fallback: Just display the score if no progress bar element
            qualityContainer.innerHTML = `<p><strong data-i18n="quality.score">Puntuación de Calidad:</strong> ${UIManager.formatNumber(score, 1)} / 10</p>`;
        }


          // Display breakdown details
        let breakdownHtml = `<h5 data-i18n="quality.breakdownTitle">Desglose de Penalizaciones:</h5>`;
        if (breakdown && Object.keys(breakdown).length > 0) {
            breakdownHtml += `<ul class="quality-breakdown-list">`;
            Object.entries(breakdown).forEach(([key, reason]) => {
                    // Translate the metric key if possible
                const translatedKey = LanguageManager.t(`quality.${key}`) || key;
                breakdownHtml += `<li><strong>${translatedKey}:</strong> ${reason}</li>`;
            });
            breakdownHtml += `</ul>`;
        } else {
            breakdownHtml += `<p class="text-muted small" data-i18n="quality.noPenalties">No se aplicaron penalizaciones.</p>`;
        }
        qualityContainer.innerHTML += breakdownHtml; // Append breakdown after progress bar/score

        LanguageManager.applyTranslationsToElement(qualityContainer); // Apply translations

          // Add this container in your index.html where you want the quality info:
          /*
          <div class="result-card quality-card"> <div class="result-icon quality"><i class="fas fa-check-circle"></i></div>
               <div class="result-content">
                    <h4 data-i18n="results.quality">Calidad</h4>
                    <div class="progress" id="qualityProgressBar" style="height: 20px;">
                         <div class="progress-bar" role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="10">0/10</div>
                    </div>
                    <div id="qualityBreakdownContainer" class="mt-2">
                         </div>
               </div>
          </div>
          */

           // Add some basic CSS for the breakdown list:
           /*
           .quality-breakdown-list {
               list-style: none;
               padding-left: 0;
               font-size: 0.85em;
               margin-top: 0.5rem;
           }
           .quality-breakdown-list li {
               margin-bottom: 0.3rem;
               color: #555;
           }
            .quality-breakdown-list strong {
                color: #333;
                margin-right: 0.3rem;
           }
           */
    }


    getAnalysisParameters() {
        // Retrieve values safely, providing defaults
        const fluorMin = parseFloat(document.getElementById('fluorMin')?.value) || -150;
        const fluorMax = parseFloat(document.getElementById('fluorMax')?.value) || -50;
        const pifasMin = parseFloat(document.getElementById('pifasMin')?.value) || -130;
        const pifasMax = parseFloat(document.getElementById('pifasMax')?.value) || -60;
        const concentration = parseFloat(document.getElementById('concentration')?.value) || 1.0;

        return {
            fluor_range: { min: fluorMin, max: fluorMax },
            pifas_range: { min: pifasMin, max: pifasMax },
            concentration: concentration
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
        window.APP_LOGGER.debug('File preview:', content.substring(0, 200) + (content.length > 200 ? '...' : ''));
    }

    onLanguageChanged(lang) {
        this.updateDynamicTexts();
        setTimeout(() => {
            ChartManager.refreshTranslations(lang);
        }, 100);
        ChartManager.refreshTranslations(lang);
        if (this.analysisResults) {
            // Re-render results to apply translations
            this.updateResultsDisplay(this.analysisResults);
        }
        // Update static texts managed by LanguageManager
        LanguageManager.applyTranslations();
    }

    updateDynamicTexts() {
        const sampleNameEl = document.getElementById('sampleName');
        if (sampleNameEl) {
            if (this.currentFile) {
                sampleNameEl.textContent = LanguageManager.t('analyzer.sampleName', {
                    name: this.currentFile.name
                });
            } else if (!this.analysisResults) {
                sampleNameEl.setAttribute('data-i18n', 'analyzer.waitingData');
                // ### CORRECTION ###
                LanguageManager.applyTranslations(); // Use the general function
            }
        }
        // It's generally safe to call the general applyTranslations here anyway
        // to catch any other dynamic elements, unless it causes performance issues.
        // LanguageManager.applyTranslations();
    }

    showNotification(messageKey, type = 'info', params = {}) {
        const message = LanguageManager.t(messageKey, params);
        // Use UIManager safely
        if (typeof UIManager !== 'undefined' && UIManager.showNotification) {
             UIManager.showNotification(message, type);
        } else {
             console.warn("UIManager not available, falling back to console:", type, message);
             if(type === 'error') console.error(message);
             else if(type === 'warning') console.warn(message);
             else console.log(message);
        }
    }

    switchTab(tabName) {
        const tabElement = document.getElementById(`${tabName}-tab`);
        if (!tabElement) {
            // If the target tab doesn't exist (because it's commented out), maybe switch to default?
             console.warn(`Tab ${tabName} content not found. Switching to analyzer.`);
             tabName = 'analyzer'; // Fallback to analyzer tab
             // Try finding analyzer tab again
             const defaultTabElement = document.getElementById('analyzer-tab');
             if(!defaultTabElement) {
                  console.error("Default analyzer tab not found either!");
                  return; // Critical error if default tab is missing
             }
             tabElement = defaultTabElement; // Use default tab
        }

        // Update navigation buttons
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        const navBtn = document.querySelector(`.nav-btn[data-tab="${tabName}"]`);
        if (navBtn) {
            navBtn.classList.add('active');
        } else {
             // If the nav button for the target tab doesn't exist (commented out), activate analyzer button
             const defaultNavBtn = document.querySelector('.nav-btn[data-tab="analyzer"]');
             if (defaultNavBtn) defaultNavBtn.classList.add('active');
        }


        // Show selected tab content
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        if (tabElement) tabElement.classList.add('active');

        // Update page title if element exists
        const pageTitle = document.getElementById('pageTitle');
        if (pageTitle) {
             const titleKey = `header.${tabName}`; // Assumes translation key matches tab name
             pageTitle.setAttribute('data-i18n', titleKey);
             LanguageManager.applyTranslationsToElement(pageTitle);
        }
    }

    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loadingScreen');
        const appElement = document.getElementById('app');
        if (loadingScreen) loadingScreen.classList.add('hidden');
        if (appElement) appElement.classList.remove('hidden');
    }

    /* ... (Batch methods commented out) ... */

    addFileToList(file, listId) {
        const list = document.getElementById(listId);
        if (!list) return;
        list.innerHTML = ''; // Clear previous file entry
        const fileElement = document.createElement('div');
        fileElement.className = 'file-item';
        fileElement.innerHTML = `
            <i class="fas fa-file-alt"></i>
            <span class="file-name">${UIManager.escapeHtml(file.name)}</span>
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

    /* ... (performBatchAnalysis, displayBatchResults commented out) ... */

    async exportReport() {
        if (!this.analysisResults) return;
        const exportBtn = document.getElementById('exportBtn');
        UIManager.updateButtonState(exportBtn, 'loading');

        try {
            // Pass the entire results object
            await APIClient.exportReport(this.analysisResults, 'csv');
            this.showNotification('notifications.exportSuccess', 'success');
             UIManager.updateButtonState(exportBtn, 'success');
        } catch (error) {
            this.showNotification('notifications.exportError', 'error', {
                error: error.message
            });
             UIManager.updateButtonState(exportBtn, 'error');
        }
        // No finally needed, success/error states handle timeout
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.error('Error attempting to enable fullscreen:', err);
                 this.showNotification('errors.fullscreen', 'error');
            });
        } else {
            if (document.exitFullscreen) {
                 document.exitFullscreen();
            }
        }
    }

    // --- History Methods ---
    
    displayHistory(analyses) {
        const historyList = document.getElementById('historyList');
        if (!historyList) return; // Salir si el elemento no existe

        if (!analyses || analyses.length === 0) {
            historyList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-folder-open"></i>
                    <p data-i18n="history.empty">No hay análisis guardados</p>
                    <p class="empty-subtitle" data-i18n="history.emptySubtitle">Los análisis aparecerán aquí automáticamente</p>
                </div>
            `;
            // Aplicar traducciones a este mensaje estático si se usa i18n
            if (typeof LanguageManager !== 'undefined') {
                LanguageManager.applyTranslationsToElement(historyList);
            }
            return;
        }

        historyList.innerHTML = analyses.map(analysis => {
            // Formatear valores de forma segura
            const fluor = UIManager.formatNumber(analysis.fluor, 2);
            const pfas = UIManager.formatNumber(analysis.pfas, 2);
            const quality = UIManager.formatNumber(analysis.quality, 1);
            let formattedDate = '--';
            try {
                formattedDate = new Date(analysis.created).toLocaleString();
            } catch(e) { console.error("Error formatting date", analysis.created); }

            // Obtener nombres escapando HTML
            const displayName = UIManager.escapeHtml(analysis.filename || analysis.name || 'Nombre Desconocido');
            // Nombre único para acciones (generalmente el nombre del archivo JSON)
            const analysisName = UIManager.escapeHtml(analysis.name || '');

            // Escapar comillas simples para que no rompan el onclick
            const escapedAnalysisName = analysisName.replace(/'/g, "\\'");
            const escapedDisplayName = displayName.replace(/'/g, "\\'");

            // Obtener textos traducidos para tooltips (con fallback)
            const loadTooltip = LanguageManager.t('history.loadTooltip') || 'Cargar este análisis';
            const viewTooltip = LanguageManager.t('history.viewTooltip') || 'Ver análisis';
            const deleteTooltip = LanguageManager.t('history.deleteTooltip') || 'Eliminar análisis';

            return `
                <div class="history-item">
                    <div class="history-item-content" onclick="window.rmnApp.loadAnalysisFromHistory('${escapedAnalysisName}')" title="${loadTooltip}">
                        <div class="history-item-header">
                            <div class="history-item-title">
                                <i class="fas fa-file-alt"></i> ${displayName}
                            </div>
                            <div class="history-item-date">${formattedDate}</div>
                        </div>
                        <div class="history-item-stats">
                            <div class="history-stat" title="${LanguageManager.t('results.fluor') || 'Flúor'}"><i class="fas fa-vial"></i> ${fluor}%</div>
                            <div class="history-stat" title="${LanguageManager.t('results.pifas') || 'PFAS'}"><i class="fas fa-chart-bar"></i> ${pfas}%</div>
                            <div class="history-stat" title="${LanguageManager.t('results.quality') || 'Calidad'}"><i class="fas fa-check-circle"></i> ${quality}/10</div>
                        </div>
                    </div>
                    <div class="history-item-actions">
                        <button class="btn btn-icon btn-view"
                                onclick="event.stopPropagation(); window.rmnApp.viewAnalysis('${escapedAnalysisName}')"
                                title="${viewTooltip}">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-icon btn-delete"
                                onclick="event.stopPropagation(); window.rmnApp.deleteAnalysis('${escapedAnalysisName}', '${escapedDisplayName}')"
                                title="${deleteTooltip}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

    }

    setupHistoryFilters() {
        const searchInput = document.getElementById('historySearch');
        const dateFilter = document.getElementById('historyDateFilter');
        if (searchInput) searchInput.addEventListener('input', () => this.filterHistory());
        if (dateFilter) dateFilter.addEventListener('change', () => this.filterHistory());
    }

    filterHistory() {
        if (!this.allAnalyses) return;
        const searchTerm = document.getElementById('historySearch')?.value.toLowerCase() || '';
        const dateFilter = document.getElementById('historyDateFilter')?.value || 'all';
        let filtered = [...this.allAnalyses];

        if (searchTerm) {
            filtered = filtered.filter(analysis =>
                (analysis.filename || analysis.name || '').toLowerCase().includes(searchTerm)
            );
        }

        if (dateFilter !== 'all') {
            const now = new Date();
            let startDate;
            switch (dateFilter) {
                case 'today': startDate = new Date(now.setHours(0, 0, 0, 0)); break;
                case 'week': startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000); break;
                case 'month': startDate = new Date(now.getFullYear(), now.getMonth(), 1); break;
            }
            if (startDate) {
                filtered = filtered.filter(analysis => new Date(analysis.created) >= startDate);
            }
        }
        this.displayHistory(filtered);
    }

    viewAnalysis(filename) {
        this.loadAnalysisFromHistory(filename);
    }

    async loadAnalysisFromHistory(filename) {
        if(!filename) return;
        UIManager.showLoading(document.getElementById('analyzer-tab'), LanguageManager.t('history.loadingAnalysis')); // Show loading
        try {
            const data = await APIClient.getResult(filename);
            this.analysisResults = data;
            this.updateResultsDisplay(data);
            this.switchTab('analyzer'); // Switch after loading
            const displayName = data.filename || filename;
            this.showNotification('notifications.analysisLoaded', 'success', { filename: displayName });
        } catch (error) {
            console.error('Error loading analysis from history:', error);
            this.showNotification('errors.analysisLoad', 'error');
        } finally {
             UIManager.hideLoading(document.getElementById('analyzer-tab')); // Hide loading
        }
    }


    async loadHistory() {
         const historyListContainer = document.getElementById('historyList');
         if(historyListContainer) UIManager.showLoading(historyListContainer, LanguageManager.t('history.loading'));
        try {
            const data = await APIClient.getAnalysisList();
            this.allAnalyses = data.analyses || [];
            this.filterHistory(); // Apply filters and display
            window.APP_LOGGER.debug(`History loaded: ${this.allAnalyses.length} analyses`);
        } catch (error) {
            console.error('Error loading history:', error);
            this.showNotification('errors.historyLoad', 'error');
            this.displayHistory([]); // Show empty state on error
        } finally {
             if(historyListContainer) UIManager.hideLoading(historyListContainer);
        }
    }

    async clearHistory() {
        const confirmMessage = LanguageManager.t('history.confirmClearAll') || /* ... default message ... */ '';
        if (!confirm(confirmMessage)) return;
        const secondConfirm = prompt(LanguageManager.t('history.confirmClearAll2') || /* ... default message ... */ '');
        if (secondConfirm !== 'ELIMINAR') {
            this.showNotification('history.clearCancelled', 'info');
            return;
        }

        const clearBtn = document.getElementById('clearHistoryBtn');
        if (clearBtn) UIManager.updateButtonState(clearBtn, 'loading');

        try {
            const result = await APIClient.clearAllHistory();
            this.allAnalyses = [];
            this.displayHistory([]);
            if (this.analysisResults) this.clearAnalysisResults();
            this.showNotification('history.clearSuccess', 'success', { count: result.deleted_count });
            window.APP_LOGGER.info(`History cleared: ${result.deleted_count} analyses deleted`);
        } catch (error) {
            console.error('Error clearing history:', error);
            this.showNotification('history.clearError', 'error', { error: error.message });
        } finally {
            if (clearBtn) UIManager.updateButtonState(clearBtn, 'default');
        }
    }

    async deleteAnalysis(filename, displayName) {
         if (!filename) return;
        const confirmMessage = LanguageManager.t('history.confirmDelete', { name: displayName }) || /* ... default message ... */ '';
        if (!confirm(confirmMessage)) return;

        try {
            await APIClient.deleteAnalysis(filename);
            this.showNotification('history.deleteSuccess', 'success', { name: displayName });
            // Remove from local cache before reloading list visually
            this.allAnalyses = this.allAnalyses.filter(a => a.name !== filename);
            this.filterHistory(); // Update display immediately
            // await this.loadHistory(); // Or reload fully from server

            if (this.analysisResults && (this.analysisResults.filename === displayName || this.analysisResults.name === filename)) {
                this.clearAnalysisResults();
            }
            window.APP_LOGGER.info(`Analysis deleted: ${filename}`);
        } catch (error) {
            console.error('Error deleting analysis:', error);
            this.showNotification('history.deleteError', 'error', { error: error.message });
        }
    }

    clearAnalysisResults() {
        UIManager.updateElementText('fluorResult', '--');
        UIManager.updateElementText('pifasResult', '--');
        UIManager.updateElementText('concentrationResult', '--');
        UIManager.updateElementText('qualityResult', '--');

        const tbody = document.querySelector('#resultsTable tbody');
        if (tbody) tbody.innerHTML = '';

        ChartManager.clearPeaks(); // Clear peaks from chart
        // Optionally create an empty chart or just clear data
        if (ChartManager && ChartManager.chart) {
             Plotly.react('spectrumChart', [{x:[], y:[]}], ChartManager.layout, ChartManager.config);
        }


        const sampleNameEl = document.getElementById('sampleName');
        if(sampleNameEl){
             sampleNameEl.setAttribute('data-i18n', 'analyzer.waitingData');
             LanguageManager.applyTranslationsToElement(sampleNameEl);
        }

        UIManager.disableElement('exportBtn');
        this.analysisResults = null;
        this.currentFile = null;

        // Clear file list display
        const fileList = document.getElementById('fileList');
        if (fileList) fileList.innerHTML = '';

        window.APP_LOGGER.debug('Analysis results cleared');
    }


    /* ... (loadAnalysisFromHistory already exists) ... */

} // <-- FIN DE LA CLASE RMNAnalyzerApp


/* ... (Funciones globales de Methods comentadas) ... */


// ============================================================================
// INICIALIZACIÓN DE LA APP (SECCIÓN ACTUALIZADA)
// ============================================================================
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await ChartManager.init(); // Initialize ChartManager first
        window.rmnApp = new RMNAnalyzerApp(); // THEN initialize the App
        /* ... (Carga de methods comentada) ... */
    } catch (error) {
        console.error("Critical application initialization error:", error);
         // Display error to user if possible
         const loadingScreen = document.getElementById('loadingScreen');
         if(loadingScreen) {
              loadingScreen.innerHTML = `<div class="loading-content"><p class="error">Error al iniciar la aplicación. Revise la consola.</p></div>`;
              loadingScreen.classList.remove('hidden'); // Ensure it's visible
         }
    }
});