class UIManager {
    static notifications = [];
    static notificationId = 0;

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

    static escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

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

    static showLoading(container, text = 'Cargando...') {
        const loadingElement = document.createElement('div');
        loadingElement.className = 'loading-overlay';
        loadingElement.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <p>${this.escapeHtml(text)}</p>
            </div>
        `;

        container.style.position = 'relative';
        container.appendChild(loadingElement);

        return loadingElement;
    }

    static hideLoading(container) {
        const loadingElement = container.querySelector('.loading-overlay');
        if (loadingElement) {
            loadingElement.remove();
        }
    }

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

    static formatNumber(value, decimals = 2) {
        if (value === null || value === undefined) return '--';
        return parseFloat(value).toFixed(decimals);
    }

    static formatPercentage(value, decimals = 2) {
        if (value === null || value === undefined) return '--';
        return `${parseFloat(value).toFixed(decimals)}%`;
    }

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
}

// Additional CSS for UI components
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
`;

// Inject additional styles
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);