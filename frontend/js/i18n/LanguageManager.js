// ============================================================================
// LANGUAGE MANAGER - Sistema de Internacionalización
// ============================================================================

class LanguageManager {
    static currentLang = 'es';
    static translations = {};
    static availableLanguages = [
        { code: 'es', name: 'Español', flag: '🇪🇸' },
        { code: 'en', name: 'English', flag: '🇬🇧' },
        { code: 'eu', name: 'Euskara', flag: '🔴⚪' }
    ];

    /**
     * Inicializa el selector de idiomas
     */
    static init() {
        this.populateLanguageSelector();
        this.setupLanguageSelector();
        
        // Cargar idioma guardado o por defecto
        const savedLang = localStorage.getItem('selectedLanguage') || 'es';
        this.changeLanguage(savedLang);
    }

    /**
     * Pobla el selector de idiomas con las opciones disponibles
     */
    static populateLanguageSelector() {
        const selector = document.getElementById('languageSelector');
        if (!selector) {
            console.warn('[LanguageManager] Selector de idiomas no encontrado');
            return;
        }

        selector.innerHTML = this.availableLanguages.map(lang => 
            `<option value="${lang.code}">${lang.flag} ${lang.name}</option>`
        ).join('');
    }

    /**
     * Configura el event listener del selector
     */
    static setupLanguageSelector() {
        const selector = document.getElementById('languageSelector');
        if (!selector) return;

        selector.addEventListener('change', (e) => {
            this.changeLanguage(e.target.value);
        });
    }

    /**
     * Cambia el idioma de la aplicación
     */
    static async changeLanguage(langCode) {
        try {
            console.log(`[LanguageManager] Intentando cargar idioma: ${langCode}`);
            
            // ✅ CORREGIDO: Ruta absoluta desde la raíz
            const translationPath = `js/i18n/translations/${langCode}.json`;
            console.log(`[LanguageManager] Cargando desde: ${translationPath}`);
            
            const response = await fetch(translationPath);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.translations = await response.json();
            this.currentLang = langCode;

            // Guardar preferencia
            localStorage.setItem('selectedLanguage', langCode);

            // Actualizar selector
            const selector = document.getElementById('languageSelector');
            if (selector) {
                selector.value = langCode;
            }

            // Aplicar traducciones
            this.applyTranslations();

            // Actualizar traducciones en gráficos del dashboard
            if (window.DashboardManager && typeof window.DashboardManager.refreshTranslations === 'function') {
                window.DashboardManager.refreshTranslations();
            }

            console.log(`✅ [LanguageManager] Idioma cambiado a: ${langCode}`);

        } catch (error) {
            console.error('[LanguageManager] Error al cambiar idioma:', error);
            console.error('[LanguageManager] Ruta intentada:', `js/i18n/translations/${langCode}.json`);
            
            // Si falla, intentar cargar español por defecto
            if (langCode !== 'es') {
                console.warn('[LanguageManager] Intentando cargar español como respaldo...');
                this.changeLanguage('es');
            }
        }
    }

    /**
     * Aplica las traducciones a todos los elementos con data-i18n
     */
    static applyTranslations(container = document) {
        // Traducir elementos con data-i18n
        container.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                element.placeholder = translation;
            } else {
                element.textContent = translation;
            }
        });

        // Traducir placeholders con data-i18n-placeholder
        container.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.t(key);
        });

        // Traducir elementos con data-params (como "X of Y selected")
        container.querySelectorAll('[data-params-count]').forEach(element => {
            const key = element.getAttribute('data-i18n') || 'comparison.selected';
            const count = element.getAttribute('data-params-count') || '0';
            const max = element.getAttribute('data-params-max') || '5';
            
            const translation = this.t(key, { count, max });
            element.textContent = translation;
        });
    }

    /**
     * Obtiene una traducción por su clave
     */
    static t(key, params = {}) {
        if (!key) return '';

        const keys = key.split('.');
        let value = this.translations;

        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                console.warn(`[LanguageManager] Traducción no encontrada: ${key}`);
                return key; // Devolver la clave si no se encuentra
            }
        }

        // Reemplazar parámetros
        if (typeof value === 'string' && Object.keys(params).length > 0) {
            return value.replace(/{(\w+)}/g, (match, param) => {
                return params[param] !== undefined ? params[param] : match;
            });
        }

        return value;
    }

    /**
     * Obtiene el idioma actual
     */
    static getCurrentLanguage() {
        return this.currentLang;
    }
}

// Hacer disponible globalmente
window.LanguageManager = LanguageManager;