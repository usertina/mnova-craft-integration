/**
 * ============================================================================
 * CRAFTRMN PRO - FIX DEFINITIVO DE ESTILOS INLINE
 * ============================================================================
 * 
 * Este script elimina los estilos inline oscuros que inserta uiComponents.js
 * Debe cargarse DESPUÉS de uiComponents.js
 * 
 * INSTRUCCIONES:
 * 1. Guarda como: js/inline-styles-remover.js
 * 2. Añade en app.html DESPUÉS de uiComponents.js:
 *    <script src="js/inline-styles-remover.js"></script>
 * 3. Elimina: js/visibility-fix.js y js/tab-system-fix.js (los viejos)
 * ============================================================================
 */

(function() {
    'use strict';
    
    console.log('[InlineStylesRemover] 🧹 Iniciando limpieza de estilos inline...');

    // ========================================================================
    // FUNCIÓN PRINCIPAL: Limpiar estilos inline oscuros
    // ========================================================================
    
    function cleanInlineStyles() {
        console.log('[InlineStylesRemover] Limpiando estilos inline...');
        
        // Selectores de elementos que pueden tener estilos inline oscuros
        const selectors = [
            '.history-item',
            '.history-item-header',
            '.history-item-title',
            '.history-item-title span',
            '.history-item-title i',
            '.history-item-date',
            '.history-item-details',
            '.detail-badge',
            '.detail-label',
            '.detail-value',
            '.history-item-actions',
            '.history-item-actions button',
            '.history-item-actions button i',
            '.stat-card',
            '.chart-card',
            '.sample-card'
        ];
        
        let cleanedCount = 0;
        
        selectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(el => {
                // Solo eliminar style si tiene colores oscuros
                const style = el.getAttribute('style');
                if (style) {
                    // Detectar colores oscuros
                    if (style.includes('#1f2937') || 
                        style.includes('#e5e7eb') || 
                        style.includes('#9ca3af') ||
                        style.includes('#374151')) {
                        el.removeAttribute('style');
                        cleanedCount++;
                    }
                }
            });
        });
        
        console.log(`[InlineStylesRemover] ✅ ${cleanedCount} estilos inline eliminados`);
    }

    // ========================================================================
    // SOBRESCRIBIR UIManager.displayHistory
    // ========================================================================
    
    function patchDisplayHistory() {
        if (typeof UIManager === 'undefined') {
            console.warn('[InlineStylesRemover] UIManager no está definido aún');
            return false;
        }
        
        const originalDisplayHistory = UIManager.displayHistory;
        
        UIManager.displayHistory = function(historyData) {
            console.log('[InlineStylesRemover] displayHistory llamado, interceptando...');
            
            // Llamar a la función original
            originalDisplayHistory.call(this, historyData);
            
            // Limpiar estilos inline después de insertar HTML
            setTimeout(() => {
                cleanInlineStyles();
            }, 50);
        };
        
        console.log('[InlineStylesRemover] ✅ displayHistory parcheado');
        return true;
    }

    // ========================================================================
    // SOBRESCRIBIR UIManager.switchTab
    // ========================================================================
    
    function patchSwitchTab() {
        if (typeof UIManager === 'undefined') {
            console.warn('[InlineStylesRemover] UIManager no está definido aún');
            return false;
        }
        
        const originalSwitchTab = UIManager.switchTab;
        
        UIManager.switchTab = function(tabName) {
            console.log(`[InlineStylesRemover] 🔄 Cambiando a pestaña: ${tabName}`);
            
            // 1. Ocultar todas las pestañas
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });

            // 2. Desactivar todos los botones
            document.querySelectorAll('.nav-btn').forEach(btn => {
                btn.classList.remove('active');
            });

            // 3. Mostrar la pestaña seleccionada
            const targetTab = document.getElementById(`${tabName}-tab`);
            if (targetTab) {
                targetTab.classList.add('active');
                console.log(`[InlineStylesRemover] ✅ Pestaña ${tabName} activada`);
            }

            // 4. Activar el botón correspondiente
            const targetBtn = document.querySelector(`[data-tab="${tabName}"]`);
            if (targetBtn) {
                targetBtn.classList.add('active');
            }

            // 5. Cargar datos según la pestaña
            if (tabName === 'history' && window.APP_HANDLERS) {
                console.log('[InlineStylesRemover] 📜 Cargando historial...');
                window.APP_HANDLERS.loadHistory(1);
            } else if (tabName === 'dashboard' && window.DashboardManager) {
                console.log('[InlineStylesRemover] 📊 Inicializando dashboard...');
                setTimeout(() => {
                    window.DashboardManager.init();
                }, 100);
            } else if (tabName === 'comparison' && window.ComparisonManager) {
                console.log('[InlineStylesRemover] ⚖️ Inicializando comparación...');
                setTimeout(() => {
                    window.ComparisonManager.init();
                }, 100);
            }
            
            // 6. Limpiar estilos inline después de cambiar
            setTimeout(() => {
                cleanInlineStyles();
            }, 200);
        };
        
        console.log('[InlineStylesRemover] ✅ switchTab parcheado');
        return true;
    }

    // ========================================================================
    // INICIALIZACIÓN
    // ========================================================================
    
    function init() {
        console.log('[InlineStylesRemover] Esperando a que UIManager esté listo...');
        
        // Intentar parchear cada 100ms hasta que UIManager esté disponible
        const maxAttempts = 50; // 5 segundos máximo
        let attempts = 0;
        
        const checkInterval = setInterval(() => {
            attempts++;
            
            if (typeof UIManager !== 'undefined') {
                console.log('[InlineStylesRemover] ✅ UIManager encontrado, aplicando patches...');
                
                patchDisplayHistory();
                patchSwitchTab();
                
                clearInterval(checkInterval);
                
                // Limpiar cualquier estilo inline existente
                setTimeout(() => {
                    cleanInlineStyles();
                }, 500);
                
                console.log('[InlineStylesRemover] 🎉 Todo listo!');
            } else if (attempts >= maxAttempts) {
                console.error('[InlineStylesRemover] ❌ Timeout esperando UIManager');
                clearInterval(checkInterval);
            }
        }, 100);
    }

    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // ========================================================================
    // OBSERVER: Limpiar estilos cuando se añadan nuevos elementos
    // ========================================================================
    
    const observer = new MutationObserver((mutations) => {
        let shouldClean = false;
        
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1 && node.classList) {
                    if (node.classList.contains('history-item') ||
                        node.classList.contains('stat-card') ||
                        node.classList.contains('sample-card')) {
                        shouldClean = true;
                    }
                }
            });
        });
        
        if (shouldClean) {
            setTimeout(() => {
                cleanInlineStyles();
            }, 50);
        }
    });

    // Observar cambios en main-content
    setTimeout(() => {
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            observer.observe(mainContent, {
                childList: true,
                subtree: true
            });
            console.log('[InlineStylesRemover] 👁️ Observer activado');
        }
    }, 1000);

})();