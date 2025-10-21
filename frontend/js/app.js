class RMNAnalyzerApp {
    constructor() {
        this.currentFile = null;
        this.spectrumData = null;
        this.analysisResults = null;
        this.isConnected = false;
        
        this.initializeApp();
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
            this.setupChart();
            
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
        
        // Navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
        
        // Fullscreen
        document.getElementById('fullscreenBtn').addEventListener('click', () => {
            this.toggleFullscreen();
        });
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
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${param}</td>
                <td>${data.value?.toFixed(4) || '--'}</td>
                <td>${data.unit || '--'}</td>
                <td>${data.limits || 'N/A'}</td>
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
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Show selected tab
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
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
            await APIClient.exportReport(this.analysisResults, 'pdf');
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
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.rmnApp = new RMNAnalyzerApp();
});