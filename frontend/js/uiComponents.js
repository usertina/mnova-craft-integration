class UIManager {
    static notifications = [];
    static notificationId = 0;

    // ============================================================
    // SISTEMA DE NOTIFICACIONES
    // ============================================================

    static showNotification(message, type = 'info', duration = 5000) {
        const id = this.notificationId++;
        const notification = {
            id,
            message,
            type,
            duration,
            timestamp: Date.now()
        };

        this.notifications.push(notification);
        this.renderNotification(notification);
        this.autoRemoveNotification(id, duration);

        window.APP_LOGGER.debug(`Notification shown: ${type} - ${message}`);
    }

    static escapeHtml(text) {
        if (text === null || text === undefined) return '';
        
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }


    static renderNotification(notification) {
        const container = document.getElementById('notifications');
        if (!container) return;

        const notificationElement = document.createElement('div');
        notificationElement.className = `notification ${notification.type}`;
        notificationElement.id = `notification-${notification.id}`;

        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        notificationElement.innerHTML = `
            <i class="fas ${icons[notification.type] || icons.info}"></i>
            <div class="notification-content">
                <div class="notification-message">${this.escapeHtml(notification.message)}</div>
            </div>
            <button class="btn btn-icon notification-close" onclick="UIManager.removeNotification(${notification.id})">
                <i class="fas fa-times"></i>
            </button>
        `;

        container.appendChild(notificationElement);

        // Animate in
        setTimeout(() => {
            notificationElement.style.transform = 'translateX(0)';
            notificationElement.style.opacity = '1';
        }, 10);
    }

    static removeNotification(id) {
        const notificationElement = document.getElementById(`notification-${id}`);
        if (notificationElement) {
            notificationElement.classList.add('fade-out');
            setTimeout(() => {
                if (notificationElement.parentNode) {
                    notificationElement.parentNode.removeChild(notificationElement);
                }
            }, 300);
        }

        this.notifications = this.notifications.filter(n => n.id !== id);
    }

    static autoRemoveNotification(id, duration) {
        if (duration > 0) {
            setTimeout(() => {
                this.removeNotification(id);
            }, duration);
        }
    }

    static showToast(message, type = 'info') {
        // Alias para showNotification (mantener compatibilidad)
        this.showNotification(message, type);
    }

    // ============================================================
    // SISTEMA DE MODALES
    // ============================================================

    static showModal(title, content, buttons = []) {
        // Remove existing modal
        this.hideModal();

        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.id = 'dynamic-modal';

        const defaultButtons = [
            {
                text: 'Cerrar',
                type: 'outline',
                action: 'close'
            }
        ];

        const modalButtons = buttons.length > 0 ? buttons : defaultButtons;

        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${this.escapeHtml(title)}</h3>
                    <button class="close" onclick="UIManager.hideModal()">&times;</button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    ${modalButtons.map(btn => `
                        <button class="btn btn-${btn.type}" onclick="UIManager.handleModalButton('${btn.action}')">
                            ${this.escapeHtml(btn.text)}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        modal.style.display = 'block';

        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.hideModal();
            }
        });

        window.APP_LOGGER.debug(`Modal shown: ${title}`);
    }

    static hideModal() {
        const existingModal = document.getElementById('dynamic-modal');
        if (existingModal) {
            existingModal.remove();
        }
    }

    static handleModalButton(action) {
        switch (action) {
            case 'close':
                this.hideModal();
                break;
            // Add more actions as needed
            default:
                window.APP_LOGGER.warn(`Unknown modal button action: ${action}`);
        }
    }

    static async showConfirmationModal(title, body) {
        return new Promise((resolve) => {
            // Crear modal de confirmación
            const modal = document.createElement('div');
            modal.className = 'modal';
            modal.id = 'confirmation-modal';
            
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>${this.escapeHtml(title)}</h3>
                        <button class="close" onclick="this.closest('.modal').remove(); window._confirmResolve(false);">&times;</button>
                    </div>
                    <div class="modal-body">
                        <p>${this.escapeHtml(body)}</p>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-outline" onclick="this.closest('.modal').remove(); window._confirmResolve(false);">
                            Cancelar
                        </button>
                        <button class="btn btn-danger" onclick="this.closest('.modal').remove(); window._confirmResolve(true);">
                            Confirmar
                        </button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            modal.style.display = 'block';
            
            // Guardar resolve en el scope global temporalmente
            window._confirmResolve = resolve;
            
            // Cerrar con click fuera del modal
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                    resolve(false);
                }
            });
        });
    }

    // ============================================================
    // LOADING / SPINNER
    // ============================================================

    static showLoading(containerOrText, maybeText) {
        // Permitir llamadas como:
        // - showLoading(container, text)
        // - showLoading(text)
        // - showLoading()
        let container;
        let text;

        if (typeof containerOrText === 'string' || containerOrText === undefined) {
            // Si el primer argumento es texto o no se pasa nada, usamos document.body como contenedor
            container = document.body;
            text = containerOrText || 'Cargando...';
        } else {
            container = containerOrText;
            text = maybeText || 'Cargando...';
        }

        if (!container) {
            console.warn('[UIManager] showLoading() → container es null o undefined');
            return null;
        }

        const loadingElement = document.createElement('div');
        loadingElement.className = 'loading-overlay';
        loadingElement.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <p>${this.escapeHtml(text)}</p>
            </div>
        `;

        // Si el contenedor no tiene posición, la configuramos para que el overlay se posicione correctamente
        const computedStyle = window.getComputedStyle(container);
        if (computedStyle.position === 'static' || !computedStyle.position) {
            container.style.position = 'relative';
        }

        container.appendChild(loadingElement);
        return loadingElement;
    }

    static hideLoading(container = document.body) {
        const loadingElement = container.querySelector('.loading-overlay');
        if (loadingElement) {
            loadingElement.remove();
        }
    }

    // ============================================================
    // GESTIÓN DE PARÁMETROS Y CONFIGURACIÓN
    // ============================================================

    static setupAnalysisParameters(params) {
        console.debug("[UIManager] setupAnalysisParameters() →", params);
        if (!params) return;

        // Ejemplo: inicializar un <select> de modos de análisis
        const modeSelect = document.getElementById("analysis-mode");
        if (modeSelect && params.modes) {
            modeSelect.innerHTML = params.modes
                .map(m => `<option value="${m}">${m}</option>`)
                .join("");
        }

        // Ejemplo: establecer umbral por defecto
        const thresholdInput = document.getElementById("threshold");
        if (thresholdInput && params.default_threshold !== undefined) {
            thresholdInput.value = params.default_threshold;
        }
    }

    // ============================================================
    // GESTIÓN DE HISTORIAL
    // ============================================================

    static showHistoryLoading() {
        const historyList = document.getElementById('historyList');
        if (historyList) {
            historyList.innerHTML = `
                <div class="loading-state">
                    <div class="loading-spinner"></div>
                    <p>Cargando historial...</p>
                </div>
            `;
        }
    }

    static getHistorySearchTerm() {
        const searchInput = document.getElementById('searchHistory');
        return searchInput ? searchInput.value.trim() : '';
    }

    static displayHistory(historyData) {
        const historyList = document.getElementById('historyList');
        
        if (!historyList) {
            console.error('[UIManager] Elemento historyList no encontrado');
            return;
        }

        const measurements = historyData.measurements || [];
        
        if (measurements.length === 0) {
            historyList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox fa-3x"></i>
                    <p>${LanguageManager.t('history.empty')}</p>
                    <p class="text-muted">${LanguageManager.t('history.emptySubtitle')}</p>
                </div>
            `;
            return;
        }

        // Construir HTML de los items
        const itemsHTML = measurements.map(item => {
            const filename = UIManager.escapeHtml(item.filename || item.sample_name || 'Sin nombre');
            const timestamp = new Date(item.timestamp || item.created_at).toLocaleString();
            const fluorPercentage = item.fluor_percentage?.toFixed(2) || 'N/A';
            // ✅ CORREGIDO: Usar ambos nombres posibles
            const pfasPercentage = (item.pfas_percentage || item.pifas_percentage)?.toFixed(2) || 'N/A';
            const qualityScore = item.quality_score?.toFixed(1) || 'N/A';
            
            return `
                <div class="history-item" data-id="${item.id}" data-filename="${filename}">
                    <div class="history-item-header">
                        <div class="history-item-title">
                            <i class="fas fa-file-alt"></i>
                            <span>${filename}</span>
                        </div>
                        <div class="history-item-date">
                            ${timestamp}
                        </div>
                    </div>
                    <div class="history-item-details">
                        <div class="detail-badge">
                            <span class="detail-label">Flúor:</span>
                            <span class="detail-value">${fluorPercentage}%</span>
                        </div>
                        <div class="detail-badge">
                            <span class="detail-label">PFAS:</span>
                            <span class="detail-value">${pfasPercentage}%</span>
                        </div>
                        <div class="detail-badge">
                            <span class="detail-label">Calidad:</span>
                            <span class="detail-value">${qualityScore}/10</span>
                        </div>
                    </div>
                    <div class="history-item-actions">
                        <button class="btn btn-sm btn-icon" 
                                onclick="APP_HANDLERS.loadResult(${item.id}, '${filename}')"
                                title="${LanguageManager.t('history.viewTooltip') || 'Ver'}">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-icon btn-danger" 
                                onclick="APP_HANDLERS.deleteHistoryItem(${item.id}, '${filename}')"
                                title="${LanguageManager.t('history.deleteTooltip') || 'Eliminar'}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        historyList.innerHTML = itemsHTML;

        // Actualizar paginación si existe
        this.updatePagination(historyData.page, historyData.total_pages);
        
        console.debug(`[UIManager] ${measurements.length} items mostrados en historial`);
    }

    /**
 * Configura la paginación del historial
 */
    static setupPagination(currentPage, totalPages) {
        console.debug(`[UIManager] setupPagination: página ${currentPage} de ${totalPages}`);
        
        const paginationContainer = document.getElementById('historyPagination');
        
        if (!paginationContainer) {
            console.warn('[UIManager] Contenedor de paginación no encontrado');
            return;
        }

        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let html = '<div class="pagination">';
        
        // Botón anterior
        html += `
            <button class="pagination-btn ${currentPage === 1 ? 'disabled' : ''}" 
                    ${currentPage === 1 ? 'disabled' : ''} 
                    onclick="APP_HANDLERS.loadHistory(${currentPage - 1})">
                <i class="fas fa-chevron-left"></i>
            </button>
        `;
        
        // Números de página
        for (let i = 1; i <= totalPages; i++) {
            if (
                i === 1 || 
                i === totalPages || 
                (i >= currentPage - 2 && i <= currentPage + 2)
            ) {
                html += `
                    <button class="pagination-btn ${i === currentPage ? 'active' : ''}" 
                            onclick="APP_HANDLERS.loadHistory(${i})">
                        ${i}
                    </button>
                `;
            } else if (i === currentPage - 3 || i === currentPage + 3) {
                html += '<span class="pagination-ellipsis">...</span>';
            }
        }
        
        // Botón siguiente
        html += `
            <button class="pagination-btn ${currentPage === totalPages ? 'disabled' : ''}" 
                    ${currentPage === totalPages ? 'disabled' : ''} 
                    onclick="APP_HANDLERS.loadHistory(${currentPage + 1})">
                <i class="fas fa-chevron-right"></i>
            </button>
        `;
        
        html += '</div>';
        paginationContainer.innerHTML = html;
    }

    /**
     * Actualiza la paginación (versión simplificada)
     */
    static updatePagination(currentPage, totalPages) {
        this.setupPagination(currentPage, totalPages);
    }

    static displayHistoryError(errorMessage) {
        const historyList = document.getElementById('historyList');
        if (historyList) {
            historyList.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle error-icon"></i>
                    <p>${this.escapeHtml(errorMessage)}</p>
                </div>
            `;
        }
    }

    static getCurrentPage() {
        // Devuelve la página actual del historial (por defecto 1)
        return 1; // TODO: Implementar gestión real de paginación si es necesario
    }

    // ============================================================
    // GESTIÓN DE ANÁLISIS Y ARCHIVOS
    // ============================================================

    static getSelectedFile() {
        const fileInput = document.getElementById('fileInput');
        if (fileInput && fileInput.files && fileInput.files.length > 0) {
            return fileInput.files[0];
        }
        return null;
    }

    static getCurrentAnalysisParams() {
        // Recoger parámetros de análisis desde la UI
        const params = {};
        
        const modeSelect = document.getElementById('analysis-mode');
        if (modeSelect) {
            params.mode = modeSelect.value;
        }
        
        const thresholdInput = document.getElementById('threshold');
        if (thresholdInput) {
            params.threshold = parseFloat(thresholdInput.value) || 0;
        }
        
        return params;
    }

    static displayResults(results) {
        console.debug("[UIManager] Mostrando resultados:", results);
        
        // ✅ Extraer datos del objeto analysis si existe
        const analysis = results.analysis || results;
        
        // Actualizar nombre de la muestra
        const sampleName = document.getElementById('sampleName');
        if (sampleName) {
            sampleName.textContent = results.sample_name || results.filename || 'Muestra Analizada';
        }
        
        // Actualizar valores de flúor y PFAS
        const fluorResult = document.getElementById('fluorResult');
        if (fluorResult) {
            fluorResult.textContent = this.formatNumber(analysis.fluor_percentage, 2);
        }
        
        const pifasResult = document.getElementById('pifasResult');
        if (pifasResult) {
            // El backend usa 'pifas_percentage' o 'pfas_percentage'
            const pfasValue = analysis.pifas_percentage || analysis.pfas_percentage;
            pifasResult.textContent = this.formatNumber(pfasValue, 2);
        }
        
        // Actualizar calidad
        this.updateQualityDisplay(results.quality_score || 0);
        
        // Actualizar estadísticas rápidas
        const peaksCount = document.getElementById('peaksCount');
        if (peaksCount) {
            peaksCount.textContent = results.peaks?.length || 0;
        }
        
        const totalIntegral = document.getElementById('totalIntegral');
        if (totalIntegral) {
            totalIntegral.textContent = this.formatNumber(analysis.total_integral, 2);
        }
        
        const snRatio = document.getElementById('snRatio');
        if (snRatio) {
            snRatio.textContent = this.formatNumber(results.signal_to_noise || analysis.signal_to_noise, 2);
        }
        
        // Actualizar tabla de resultados detallados
        this.updateResultsTable(analysis);
        
        // Actualizar tabla de picos
        this.updatePeakTable(results.peaks || []);
        
        // Habilitar botón de exportación
        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn) {
            exportBtn.disabled = false;
        }
    }

    static updateQualityDisplay(qualityScore) {
        const progressBar = document.getElementById('qualityProgressBar');
        if (progressBar) {
            const bar = progressBar.querySelector('.progress-bar');
            if (bar) {
                const percentage = (qualityScore / 10) * 100;
                bar.style.width = `${percentage}%`;
                bar.textContent = `${qualityScore}/10`;
                bar.setAttribute('aria-valuenow', qualityScore);
                
                // Cambiar color según el score
                bar.className = 'progress-bar';
                if (qualityScore >= 8) {
                    bar.classList.add('bg-success');
                } else if (qualityScore >= 5) {
                    bar.classList.add('bg-warning');
                } else {
                    bar.classList.add('bg-danger');
                }
            }
        }
    }

    static updateResultsTable(analysis) {
        const tbody = document.querySelector('#resultsTable tbody');
        if (!tbody) return;
        
        // El backend usa 'pifas_percentage' o 'pfas_percentage'
        const pfasValue = analysis.pifas_percentage || analysis.pfas_percentage;
        const concentration = analysis.concentration || analysis.pifas_concentration;
        
        const rows = [
            { 
                param: 'Flúor Total', 
                value: this.formatNumber(analysis.fluor_percentage, 2), 
                unit: '%', 
                limits: '0-100' 
            },
            { 
                param: 'PFAS Total', 
                value: this.formatNumber(pfasValue, 2), 
                unit: '%', 
                limits: '0-100' 
            },
            { 
                param: 'Concentración', 
                value: this.formatNumber(concentration, 4), 
                unit: 'mM', 
                limits: '-' 
            },
            { 
                param: 'Relación S/N', 
                value: this.formatNumber(analysis.signal_to_noise, 2), 
                unit: 'dB', 
                limits: '>10' 
            }
        ];
        
        tbody.innerHTML = rows.map(row => `
            <tr>
                <td>${this.escapeHtml(row.param)}</td>
                <td>${row.value}</td>
                <td>${this.escapeHtml(row.unit)}</td>
                <td>${this.escapeHtml(row.limits)}</td>
            </tr>
        `).join('');
    }

    static updatePeakTable(peaks) {
        const tbody = document.querySelector('#peakTable tbody');
        if (!tbody) return;
        
        if (!peaks || peaks.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="empty-state">
                        <i class="fas fa-chart-line"></i>
                        <p>No hay picos analizados aún</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = peaks.map(peak => `
            <tr>
                <td>${this.formatNumber(peak.position || peak.ppm, 3)}</td>
                <td>${this.formatNumber(peak.height || peak.intensity, 2)}</td>
                <td>${this.formatNumber(peak.area, 2)}</td>
                <td>${this.formatNumber(peak.width, 2)}</td>
                <td>${this.escapeHtml(peak.region || peak.assignment || '-')}</td>
            </tr>
        `).join('');
    }

    // ============================================================
    // EXPORTACIÓN DE DATOS
    // ============================================================

    static getExportData(format) {
        console.debug(`[UIManager] Preparando datos para exportar en formato: ${format}`);
        
        // Recoger datos actuales de la UI
        const exportData = {
            format: format,
            sample_name: document.getElementById('sampleName')?.textContent || 'Muestra',
            timestamp: new Date().toISOString(),
            results: {
                fluor: document.getElementById('fluorResult')?.textContent || '--',
                pfas: document.getElementById('pifasResult')?.textContent || '--',
                quality: document.querySelector('#qualityProgressBar .progress-bar')?.textContent || '--'
            }
        };
        
        return exportData;
    }

    // ============================================================
    // GESTIÓN DE BOTONES Y ESTADOS
    // ============================================================

    static updateButtonState(button, state) {
        const states = {
            loading: {
                disabled: true,
                html: '<i class="fas fa-spinner fa-spin"></i> Procesando...'
            },
            success: {
                disabled: false,
                html: '<i class="fas fa-check"></i> Completado'
            },
            error: {
                disabled: false,
                html: '<i class="fas fa-times"></i> Error'
            },
            default: {
                disabled: false,
                html: button.dataset.originalHtml || button.innerHTML
            }
        };

        const buttonState = states[state] || states.default;

        // Save original HTML if not already saved
        if (!button.dataset.originalHtml && state !== 'default') {
            button.dataset.originalHtml = button.innerHTML;
        }

        button.disabled = buttonState.disabled;
        button.innerHTML = buttonState.html;

        if (state === 'success') {
            setTimeout(() => {
                this.updateButtonState(button, 'default');
            }, 2000);
        } else if (state === 'error') {
            setTimeout(() => {
                this.updateButtonState(button, 'default');
            }, 3000);
        }
    }

    // ============================================================
    // UTILIDADES DE FORMATO
    // ============================================================

    static formatNumber(value, decimals = 2) {
        if (value === null || value === undefined) return '--';
        return parseFloat(value).toFixed(decimals);
    }

    static formatPercentage(value, decimals = 2) {
        if (value === null || value === undefined) return '--';
        return `${parseFloat(value).toFixed(decimals)}%`;
    }

    static escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .toString()
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // ============================================================
    // UTILIDADES DE ELEMENTOS
    // ============================================================

    static createTooltip(element, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.innerHTML = `
            ${element.outerHTML}
            <span class="tooltip-text">${this.escapeHtml(text)}</span>
        `;

        element.parentNode.replaceChild(tooltip, element);
    }

    static updateElementText(elementId, text) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text;
        }
    }

    static updateElementHTML(elementId, html) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = html;
        }
    }

    static toggleElementVisibility(elementId, visible) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = visible ? 'block' : 'none';
        }
    }

    static addClassToElement(elementId, className) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.add(className);
        }
    }

    static removeClassFromElement(elementId, className) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.remove(className);
        }
    }

    static setElementValue(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.value = value;
        }
    }

    static getElementValue(elementId) {
        const element = document.getElementById(elementId);
        return element ? element.value : null;
    }

    static disableElement(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.disabled = true;
        }
    }

    static enableElement(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.disabled = false;
        }
    }

    static showElement(elementId) {
        this.toggleElementVisibility(elementId, true);
    }

    static hideElement(elementId) {
        this.toggleElementVisibility(elementId, false);
    }

    static createProgressBar(containerId, value, max = 100) {
        const container = document.getElementById(containerId);
        if (!container) return null;

        const progressBar = document.createElement('div');
        progressBar.className = 'progress';
        progressBar.innerHTML = `
            <div class="progress-bar" style="width: ${(value / max) * 100}%"></div>
        `;

        container.appendChild(progressBar);
        return progressBar;
    }

    static updateProgressBar(progressBar, value, max = 100) {
        if (progressBar) {
            const bar = progressBar.querySelector('.progress-bar');
            if (bar) {
                bar.style.width = `${(value / max) * 100}%`;
            }
        }
    }

    // ============================================================
    // EVENT LISTENERS
    // ============================================================

    static setupEventListeners() {
        console.debug("[UIManager] Configurando event listeners...");

        // === NAVEGACIÓN DE PESTAÑAS ===
        const navButtons = document.querySelectorAll('.nav-btn');
        navButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabName = e.currentTarget.dataset.tab;
                this.switchTab(tabName);
            });
        });

        // === CARGA DE ARCHIVOS ===
        const fileInput = document.getElementById('fileInput');
        const browseBtn = document.getElementById('browseFiles');
        const uploadArea = document.getElementById('uploadArea');

        if (browseBtn && fileInput) {
            browseBtn.addEventListener('click', () => fileInput.click());
        }

        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    // Llamar al handler global si existe
                    if (window.FileProcessor && window.FileProcessor.handleFileSelect) {
                        window.FileProcessor.handleFileSelect(e.target.files);
                    }
                }
            });
        }

        // Drag & Drop
        if (uploadArea) {
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('drag-over');
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('drag-over');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('drag-over');
                if (e.dataTransfer.files.length > 0) {
                    if (window.FileProcessor && window.FileProcessor.handleFileSelect) {
                        window.FileProcessor.handleFileSelect(e.dataTransfer.files);
                    }
                }
            });
        }

        // === BOTONES DE ANÁLISIS ===
        const analyzeBtn = document.getElementById('analyzeBtn');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => {
                if (window.APP_HANDLERS && window.APP_HANDLERS.runAnalysis) {
                    window.APP_HANDLERS.runAnalysis();
                }
            });
        }

        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                if (window.APP_HANDLERS && window.APP_HANDLERS.exportReport) {
                    window.APP_HANDLERS.exportReport(null);
                }
            });
        }

        // === HISTORIAL ===
        const searchHistory = document.getElementById('searchHistory');
        if (searchHistory) {
            searchHistory.addEventListener('input', (e) => {
                if (window.APP_HANDLERS && window.APP_HANDLERS.loadHistory) {
                    clearTimeout(this._searchTimeout);
                    this._searchTimeout = setTimeout(() => {
                        window.APP_HANDLERS.loadHistory(1);
                    }, 300);
                }
            });
        }

        const clearHistoryBtn = document.getElementById('clearHistory');
        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', () => {
                if (window.APP_HANDLERS && window.APP_HANDLERS.clearHistory) {
                    window.APP_HANDLERS.clearHistory();
                }
            });
        }

        // === DASHBOARD ===
        const refreshDashboard = document.getElementById('refreshDashboard');
        if (refreshDashboard && window.DashboardManager) {
            refreshDashboard.addEventListener('click', () => {
                window.DashboardManager.loadData();
            });
        }

        const dashboardQuickFilter = document.getElementById('dashboardQuickFilter');
        if (dashboardQuickFilter) {
            dashboardQuickFilter.addEventListener('change', (e) => {
                const customRange = document.getElementById('customDateRange');
                if (customRange) {
                    customRange.style.display = e.target.value === 'custom' ? 'flex' : 'none';
                }
                if (window.DashboardManager && e.target.value !== 'custom') {
                    window.DashboardManager.applyQuickFilter(e.target.value);
                }
            });
        }

        // === BOTONES DE TOGGLE (Show/Hide) ===
        const toggleSpectrumBtn = document.getElementById('toggleSpectrumBtn');
        if (toggleSpectrumBtn) {
            toggleSpectrumBtn.addEventListener('click', () => {
                this.toggleSection('spectrumChartContainer', toggleSpectrumBtn);
            });
        }

        const toggleDetailedResultsBtn = document.getElementById('toggleDetailedResultsBtn');
        if (toggleDetailedResultsBtn) {
            toggleDetailedResultsBtn.addEventListener('click', () => {
                this.toggleSection('detailedResultsContainer', toggleDetailedResultsBtn);
            });
        }

        const togglePeakDetailsBtn = document.getElementById('togglePeakDetailsBtn');
        if (togglePeakDetailsBtn) {
            togglePeakDetailsBtn.addEventListener('click', () => {
                this.toggleSection('peakDetailsContainer', togglePeakDetailsBtn);
            });
        }

        console.debug("[UIManager] Event listeners configurados correctamente");
    }

    // Método auxiliar para cambiar de pestaña
    static switchTab(tabName) {
        // Ocultar todas las pestañas
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });

        // Desactivar todos los botones de navegación
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Mostrar la pestaña seleccionada
        const targetTab = document.getElementById(`${tabName}-tab`);
        if (targetTab) {
            targetTab.classList.add('active');
        }

        // Activar el botón correspondiente
        const targetBtn = document.querySelector(`[data-tab="${tabName}"]`);
        if (targetBtn) {
            targetBtn.classList.add('active');
        }

        // Cargar datos específicos de la pestaña
        if (tabName === 'history' && window.APP_HANDLERS) {
            window.APP_HANDLERS.loadHistory(1);
        } else if (tabName === 'dashboard' && window.DashboardManager) {
            window.DashboardManager.loadData();
        }
    }

    // Método auxiliar para toggle de secciones
    static toggleSection(containerId, buttonElement) {
        const container = document.getElementById(containerId);
        if (!container || !buttonElement) return;

        const isHidden = container.style.display === 'none' || container.style.display === '';
        container.style.display = isHidden ? 'block' : 'none';

        const icon = buttonElement.querySelector('i');
        const text = buttonElement.querySelector('span');
        
        if (icon) {
            icon.className = isHidden ? 'fas fa-eye-slash' : 'fas fa-eye';
        }
        
        if (text && text.dataset.i18n) {
            const currentKey = text.dataset.i18n;
            let newKey = currentKey;

            if (isHidden) {
                // El contenido ahora es visible, el botón debe decir "Ocultar"
                newKey = currentKey.replace('.show', '.hide');
            } else {
                // El contenido ahora está oculto, el botón debe decir "Mostrar"
                newKey = currentKey.replace('.hide', '.show');
            }
            
            text.dataset.i18n = newKey; // Ej: "analyzer.hideSpectrum"

            // Re-traducir
            if (window.LanguageManager) {
                text.textContent = window.LanguageManager.t(newKey);
            }
        }
    }
}

// ============================================================
// ESTILOS CSS ADICIONALES
// ============================================================

const additionalStyles = `
.loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.9);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 10;
    border-radius: inherit;
}

.loading-overlay .loading-content {
    text-align: center;
}

.tooltip {
    position: relative;
    display: inline-block;
}

.tooltip .tooltip-text {
    visibility: hidden;
    width: 200px;
    background: var(--dark-bg);
    color: white;
    text-align: center;
    border-radius: var(--border-radius);
    padding: 0.5rem;
    position: absolute;
    z-index: 1;
    bottom: 125%;
    left: 50%;
    transform: translateX(-50%);
    opacity: 0;
    transition: opacity 0.3s;
    font-size: 0.875rem;
}

.tooltip:hover .tooltip-text {
    visibility: visible;
    opacity: 1;
}

.notification-close {
    background: none;
    border: none;
    color: inherit;
    cursor: pointer;
    padding: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.notification-close:hover {
    opacity: 0.7;
}

/* Estilos para el historial */
.history-item {
    background: var(--card-bg, #1f2937);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
}

.history-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.history-item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.history-item-header h4 {
    margin: 0;
    font-size: 1.1rem;
    color: #e5e7eb;
}

.history-date {
    font-size: 0.875rem;
    color: #9ca3af;
}

.history-stats {
    display: flex;
    gap: 16px;
    margin-bottom: 12px;
    font-size: 0.875rem;
    color: #d1d5db;
}

.history-item-actions {
    display: flex;
    gap: 8px;
}

.btn-sm {
    padding: 6px 12px;
    font-size: 0.875rem;
}

.loading-state, .error-state {
    text-align: center;
    padding: 40px;
    color: #9ca3af;
}

.loading-state .loading-spinner {
    margin: 0 auto 16px;
}

.error-icon {
    font-size: 3rem;
    color: #ef4444;
    margin-bottom: 16px;
}

.empty-state {
    text-align: center;
    padding: 40px;
    color: #9ca3af;
}

.empty-icon {
    font-size: 3rem;
    margin-bottom: 16px;
    opacity: 0.5;
}
`;

// Inyectar estilos adicionales
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);