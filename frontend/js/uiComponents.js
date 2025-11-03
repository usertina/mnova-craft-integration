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

    /**
     * Actualiza el indicador de estado de conexión
     */
    
    static setConnectionStatus(status) {
        const statusEl = document.getElementById('connectionStatus');
        if (!statusEl) return;

        const dotEl = statusEl.querySelector('.connection-dot');
        const textEl = statusEl.querySelector('span');
        
        // Asumimos que 'connection.connecting' es la clave por defecto
        let textKey = 'connection.connecting'; 
        
        if (status === 'connected') {
            textKey = 'connection.connected';
            statusEl.classList.remove('disconnected');
            statusEl.classList.add('connected');
        } else if (status === 'disconnected') {
            textKey = 'connection.disconnected';
            statusEl.classList.remove('connected');
            statusEl.classList.add('disconnected');
        } else { // 'connecting'
            statusEl.classList.remove('connected', 'disconnected');
        }
        
        // Actualizar el texto usando el LanguageManager
        if (textEl && window.LanguageManager) {
            textEl.textContent = LanguageManager.t(textKey);
            // También actualizamos el data-i18n por si acaso
            textEl.dataset.i18n = textKey;
        }
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
            console.error('❌ [UIManager] Elemento historyList no encontrado');
            return;
        }

        console.log('🎨 [displayHistory] Datos recibidos:', historyData);

        const measurements = historyData?.measurements || historyData?.data || historyData || [];
        
        console.log('🎨 [displayHistory] Measurements:', measurements.length);
        
        if (!Array.isArray(measurements) || measurements.length === 0) {
            historyList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox fa-3x"></i>
                    <p>${LanguageManager.t('history.empty')}</p>
                    <p class="text-muted">${LanguageManager.t('history.emptySubtitle')}</p>
                </div>
            `;
            return;
        }

        // Construir HTML
        const itemsHTML = measurements.map(item => {
            const filename = UIManager.escapeHtml(item.filename || item.sample_name || 'Sin nombre');
            const timestamp = new Date(item.timestamp || item.created_at).toLocaleString();
            const fluorPercentage = item.fluor_percentage?.toFixed(2) || 'N/A';
            const pfasPercentage = (item.pfas_percentage || item.pifas_percentage)?.toFixed(2) || 'N/A';
            const qualityScore = item.quality_score?.toFixed(1) || 'N/A';
            
            return `
                <div class="history-item" data-id="${item.id}" data-filename="${filename}">
                    <div class="history-item-content">
                        <div class="history-item-header">
                            <div class="history-item-title">
                                <i class="fas fa-file-alt"></i>
                                <span>${filename}</span>
                            </div>
                            <div class="history-item-date">
                                ${timestamp}
                            </div>
                        </div>
                        <div class="history-item-stats">
                            <div class="stat-item">
                                <span class="stat-label">Flúor:</span>
                                <span class="stat-value">${fluorPercentage}%</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">PFAS:</span>
                                <span class="stat-value">${pfasPercentage}%</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Calidad:</span>
                                <span class="stat-value">${qualityScore}/10</span>
                            </div>
                        </div>
                    </div>
                    <div class="history-item-actions">
                        <button class="btn btn-icon btn-view" 
                                onclick="APP_HANDLERS.loadResult(${item.id}, '${filename}')"
                                title="Ver análisis">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-icon btn-delete" 
                                onclick="APP_HANDLERS.deleteHistoryItem(${item.id}, '${filename}')"
                                title="Eliminar">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        // ✅ CRÍTICO: Asegurar que el contenido se inserta
        historyList.innerHTML = itemsHTML;
        
        // ✅ AÑADIR: Forzar visibilidad
        historyList.style.display = 'block';
        historyList.style.opacity = '1';
        historyList.style.visibility = 'visible';
        
        console.log('✅ [displayHistory] HTML insertado, verificando...');
        console.log('✅ Elementos .history-item encontrados:', historyList.querySelectorAll('.history-item').length);

        // Actualizar paginación
        this.updatePagination(historyData.page, historyData.total_pages);
        
        console.log(`✅ [UIManager] ${measurements.length} items mostrados en historial`);
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

        // Mostrar detección de PFAS
    if (results.pfas_detection) {
        this.displayPFASDetection(results.pfas_detection);
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
                    <td colspan="7" class="empty-state">
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
                <td>${this.formatNumber(peak.width_ppm || peak.width, 3)}</td>
                <td>${this.formatNumber(peak.width_hz, 1)}</td>
                <td>${peak.snr ? this.formatNumber(peak.snr, 2) : '--'}</td>
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

    /**
     * Muestra la lista de compuestos PFAS detectados, con botones 2D/3D.
     * @param {object} pfas_detection_data - El objeto pfas_detection de los resultados.
     */
    static displayPFASDetection(pfas_detection_data) {
    
    // Asignamos el ID del contenedor donde se debe dibujar la lista.
    const container = document.getElementById('pfasDetectionContainer'); // <--- ¡ESTA ES LA LÍNEA CORRECTA!
    if (!container) {
        // Actualizamos el mensaje de error por si acaso
        console.error("No se encontró el contenedor '#pfasDetectionContainer'");
        return;
    }

        container.innerHTML = ''; // Limpiar resultados anteriores

        const compounds = pfas_detection_data?.compounds;

        if (compounds && compounds.length > 0) {

            // Recorremos cada compuesto que el backend nos envió
            compounds.forEach(compound => {
                const compoundElement = document.createElement('div');
                compoundElement.className = 'compound-result-item'; // Clase para CSS
                
                let buttonsHTML = '';
                
                // --- ¡AQUÍ ESTÁ LA LÓGICA! ---
                // El backend (app.py) ya ha añadido 'image_2d' y 'file_3d' 
                // a cada objeto 'compound' si los encontró en su base de datos.

                // Botón 2D: Solo se añade si el backend nos dio un 'image_2d'
                if (compound.image_2d) {
                    // Usamos 'data-name' y 'data-file' para pasar la info
                    buttonsHTML += `
                        <button class="btn btn-secondary btn-sm btn-ficha-2d" 
                                data-name="${compound.name}" 
                                data-file="${compound.image_2d}"
                                data-formula="${compound.formula}"
                                data-cas="${compound.cas}">
                            Ficha 2D
                        </button>`;
                }

                // Botón 3D: Solo se añade si el backend nos dio un 'file_3d'
                if (compound.file_3d) {
                    buttonsHTML += `
                        <button class="btn btn-primary btn-sm btn-view-3d" 
                                data-name="${compound.name}" 
                                data-file="${compound.file_3d}">
                            Ver 3D
                        </button>`;
                }

                // Construimos el HTML para este compuesto
                compoundElement.innerHTML = `
                    <div class="compound-info">
                        <h5 class="compound-name">${compound.name}</h5>
                        <div class="compound-confidence">
                            ${this.formatNumber(compound.confidence, 1)}% confianza
                        </div>
                        <div class="compound-details">
                            <span>Fórmula: ${compound.formula || 'N/A'}</span> | 
                            <span>CAS: ${compound.cas || 'N/A'}</span>
                        </div>
                    </div>
                    <div class="compound-actions">
                        ${buttonsHTML || '<span>(Sin vista previa)</span>'}
                    </div>
                `;
                
                container.appendChild(compoundElement);
            });

            // --- IMPORTANTE: ASIGNAR EVENTOS ---
            // Asignamos los 'clicks' a los botones que acabamos de crear.
            
            container.querySelectorAll('.btn-ficha-2d').forEach(button => {
                button.addEventListener('click', (e) => {
                    const data = e.currentTarget.dataset;
                    // Llamamos a una nueva función para mostrar el 2D
                    this.showMolecule2D(data.name, data.file, data.formula, data.cas);
                });
            });

            container.querySelectorAll('.btn-view-3d').forEach(button => {
                button.addEventListener('click', (e) => {
                    const data = e.currentTarget.dataset;
                    // Llamamos a una nueva función para mostrar el 3D
                    this.showMolecule3D(data.name, data.file);
                });
            });

        } else {
            container.innerHTML = '<p class="text-muted">No se detectaron compuestos PFAS específicos.</p>';
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

    /**
     * Muestra un pop-up (modal) genérico con un título y contenido.
     * @param {string} title - Título del modal.
     * @param {string} contentHTML - El HTML que irá dentro del modal.
     */
    static showModal(title, contentHTML) {
        // 1. Crear el elemento del modal
        const modal = document.createElement('div');
        modal.className = 'molecule-modal'; // Clase para CSS
        modal.innerHTML = `
            <div class="molecule-modal-overlay"></div>
            <div class="molecule-modal-content">
                <div class="molecule-modal-header">
                    <h4 class="molecule-modal-title">${title}</h4>
                    <button class="molecule-modal-close">&times;</button>
                </div>
                <div class="molecule-modal-body">
                    ${contentHTML}
                </div>
            </div>
        `;

        // 2. Añadirlo al body
        document.body.appendChild(modal);

        // 3. Añadir eventos de cierre
        const closeModal = () => document.body.removeChild(modal);
        modal.querySelector('.molecule-modal-overlay').addEventListener('click', closeModal);
        modal.querySelector('.molecule-modal-close').addEventListener('click', closeModal);

        // Devolver una referencia al cuerpo del modal, por si NGL lo necesita
        return modal.querySelector('.molecule-modal-body');
    }

    /**
     * Muestra la ficha 2D de una molécula en un modal.
     * @param {string} name - Nombre de la molécula (ej. "PFOA")
     * @param {string} imageFile - Ruta a la imagen (ej. "assets/molecules/pfoa_2d.png")
     * @param {string} formula - Fórmula (ej. "C8HF15O2")
     * @param {string} cas - Número CAS (ej. "335-67-1")
     */
    static showMolecule2D(name, imageFile, formula, cas) {
        const content = `
            <div class="molecule-2d-info">
                <img src="${imageFile}" alt="${name}" style="width:100%; max-width:400px; border: 1px solid #ddd; border-radius: 8px;"/>
                <ul style="list-style: none; padding-left: 0; margin-top: 15px;">
                    <li><strong>Fórmula:</strong> ${formula}</li>
                    <li><strong>CAS:</strong> ${cas}</li>
                </ul>
            </div>
        `;
        this.showModal(`Ficha 2D - ${name}`, content);
    }

    /**
     * Muestra el visor 3D de una molécula en un modal.
     * @param {string} name - Nombre de la molécula (ej. "PFOA")
     * @param {string} sdfFile - Ruta al archivo .sdf (ej. "assets/molecules/pfoa.sdf")
     */
    static showMolecule3D(name, sdfFile) {
        // 1. Crear el HTML del contenedor 3D
        const containerId = 'ngl-viewer-container';
        const content = `
            <div id="${containerId}" style="width:100%; height:400px; min-width: 500px; background: #333; border-radius: 8px;">
                <p style="color:white; padding:10px;">Cargando visor 3D...</p>
            </div>
        `;

        // 2. Mostrar el modal
        const modalBody = this.showModal(`Visor 3D - ${name}`, content);

        // 3. Cargar NGL (DESPUÉS de que el modal sea visible)
        // Usamos un pequeño 'timeout' para asegurar que el 'div' existe en el DOM
        setTimeout(() => {
            try {
                // Limpiar el texto "Cargando..."
                modalBody.querySelector(`#${containerId}`).innerHTML = '';
                
                // Cargar NGL (asumiendo que NGL está cargado globalmente)
                const stage = new NGL.Stage(containerId);
                stage.setParameters({ backgroundColor: "#333" });
                
                const filePath = `assets/molecules/${sdfFile}`; // Asume que están en esta carpeta
                
                stage.loadFile(filePath).then(component => {
                    component.addRepresentation("ball+stick", {
                        multipleBond: "symmetric"
                    });
                    component.autoView();
                }).catch(error => {
                    console.error("Error al cargar archivo NGL:", error);
                    modalBody.querySelector(`#${containerId}`).innerHTML = 
                        `<p style="color:red; padding:10px;">Error al cargar el archivo 3D: ${sdfFile}</p>`;
                });

            } catch (e) {
                console.error("Error al inicializar NGL Viewer:", e);
                modalBody.querySelector(`#${containerId}`).innerHTML = 
                    `<p style="color:red; padding:10px;">Error al iniciar el visor 3D. (¿Está ngl.js cargado?)</p>`;
            }
        }, 10); // 10ms es suficiente para que el DOM se actualice
    }

    // Método auxiliar para cambiar de pestaña
    static switchTab(tabName) {
        console.log(`[UIManager] 🔄 Cambiando a pestaña: ${tabName}`);
        
        // 1. Ocultar TODAS las pestañas
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
            // ✅ CRÍTICO: Establecer estilos inline para asegurar que se ocultan
            tab.style.display = 'none';
            tab.style.visibility = 'hidden';
        });

        // 2. Desactivar TODOS los botones de navegación
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // 3. Mostrar la pestaña seleccionada
        const targetTab = document.getElementById(`${tabName}-tab`);
        if (targetTab) {
            // ✅ CRÍTICO: Establecer estilos inline para forzar visualización
            targetTab.classList.add('active');
            targetTab.style.display = 'block';
            targetTab.style.visibility = 'visible';
            targetTab.style.opacity = '1';
            
            // ✅ NUEVO: También asegurar que el contenedor padre esté visible
            const parent = targetTab.parentElement;
            if (parent) {
                parent.classList.remove('hidden');
                parent.style.display = 'block';
                parent.style.visibility = 'visible';
            }
            
            console.log(`[UIManager] ✅ Pestaña ${tabName} activada y visible`);
        } else {
            console.error(`[UIManager] ❌ No se encontró elemento #${tabName}-tab`);
        }

        // 4. Activar el botón correspondiente
        const targetBtn = document.querySelector(`[data-tab="${tabName}"]`);
        if (targetBtn) {
            targetBtn.classList.add('active');
        }

        // 5. Cargar datos específicos de la pestaña
        if (tabName === 'history' && window.APP_HANDLERS) {
            console.log('[UIManager] 📜 Cargando historial...');
            window.APP_HANDLERS.loadHistory(1);
        } else if (tabName === 'dashboard' && window.DashboardManager) {
            console.log('[UIManager] 📊 Cargando dashboard...');
            // Pequeño delay para asegurar que el DOM está listo
            setTimeout(() => {
                window.DashboardManager.init();
            }, 100);
        } else if (tabName === 'comparison' && window.ComparisonManager) {
            console.log('[UIManager] ⚖️ Cargando comparación...');
            // Pequeño delay para asegurar que el DOM está listo
            setTimeout(() => {
                window.ComparisonManager.init();
            }, 100);
        }
        
        // 6. Disparar evento personalizado para otros módulos
        window.dispatchEvent(new CustomEvent('tabChanged', { 
            detail: { tab: tabName }
        }));
    }

    // Método auxiliar para toggle de secciones
    static toggleSection(containerId, buttonElement) {
        const container = document.getElementById(containerId);
        if (!container || !buttonElement) return;

        const isHidden = container.style.display === 'none' || container.style.display === '';
        container.style.display = isHidden ? 'block' : 'none';

        // ✅ AGREGAR/REMOVER CLASE ACTIVE
        if (isHidden) {
            buttonElement.classList.add('active');
        } else {
            buttonElement.classList.remove('active');
        }

        // Actualizar icono y texto
        const icon = buttonElement.querySelector('i');
        const text = buttonElement.querySelector('span');
        
        if (icon) {
            icon.className = isHidden ? 'fas fa-eye-slash' : 'fas fa-eye';
        }
        
        if (text && text.dataset.i18n) {
            const currentKey = text.dataset.i18n;
            let newKey = currentKey;

            if (isHidden) {
                newKey = currentKey.replace('.show', '.hide');
            } else {
                newKey = currentKey.replace('.hide', '.show');
            }
            
            text.dataset.i18n = newKey;

            if (window.LanguageManager) {
                text.textContent = window.LanguageManager.t(newKey);
            }
        }
    }

} // ✅ CIERRE DE LA CLASE UIManager

// ============================================================
// ESTILOS CSS ADICIONALES (FUERA DE LA CLASE)
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