class LanguageManager {
    static currentLang = 'es';
    static translations = {};
    static observers = [];

    static async init() {
        // Cargar idioma guardado o detectar navegador
        const savedLang = localStorage.getItem('rmnApp_language');
        const browserLang = navigator.language.split('-')[0];
        
        this.currentLang = savedLang || (['es', 'en', 'eu'].includes(browserLang) ? browserLang : 'es');
        
        // Cargar traducciones
        await this.loadTranslations(this.currentLang);
        
        // Aplicar traducciones iniciales
        this.applyTranslations();
        
        // Configurar el selector de idioma
        this.setupLanguageSelector();
        
        window.APP_LOGGER.info(`Language initialized: ${this.currentLang}`);
    }

    static async loadTranslations(lang) {
        try {
            const response = await fetch(`i18n/${lang}.json`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            this.translations = await response.json();
            window.APP_LOGGER.debug(`Translations loaded for: ${lang}`);
        } catch (error) {
            window.APP_LOGGER.error(`Error loading ${lang} translations:`, error);
            // Fallback to Spanish
            if (lang !== 'es') {
                await this.loadTranslations('es');
            }
        }
    }

    static t(key, params = {}) {
        const keys = key.split('.');
        let value = this.translations;
        
        for (const k of keys) {
            value = value?.[k];
            if (value === undefined) {
                window.APP_LOGGER.warn(`Translation key not found: ${key}`);
                return `[${key}]`; // Fallback to key name
            }
        }
        
        // Reemplazar parámetros
        if (typeof value === 'string') {
            return value.replace(/\{(\w+)\}/g, (match, param) => {
                return params[param] !== undefined ? params[param] : match;
            });
        }
        
        return value;
    }

    static async changeLanguage(lang) {
        if (this.currentLang === lang) return;
        
        window.APP_LOGGER.info(`Changing language to: ${lang}`);
        
        try {
            this.currentLang = lang;
            await this.loadTranslations(lang);
            localStorage.setItem('rmnApp_language', lang);
            
            this.applyTranslations();
            this.notifyObservers();
            
            // Actualizar atributo lang del HTML para accesibilidad
            document.documentElement.lang = lang;
            
            window.APP_LOGGER.info(`Language changed to: ${lang}`);
        } catch (error) {
            window.APP_LOGGER.error('Error changing language:', error);
            throw error;
        }
    }

    static applyTranslations() {
        // Título de la página
        document.title = this.t('app.title');

        // Elementos con data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const params = this.getParamsFromElement(element);
            
            this.translateElement(element, key, params);
        });

        // Elementos con data-i18n-html (para HTML interno)
        document.querySelectorAll('[data-i18n-html]').forEach(element => {
            const key = element.getAttribute('data-i18n-html');
            const params = this.getParamsFromElement(element);
            element.innerHTML = this.t(key, params);
        });

        // Actualizar selector de idioma
        this.updateLanguageSelector();
    }

    static translateElement(element, key, params) {
        if (element.tagName === 'INPUT') {
            const inputType = element.type.toLowerCase();
            if (inputType === 'submit' || inputType === 'button') {
                element.value = this.t(key, params);
            } else if (inputType !== 'file') {
                element.placeholder = this.t(key, params);
            }
        } else if (element.tagName === 'TEXTAREA') {
            element.placeholder = this.t(key, params);
        } else if (element.tagName === 'IMG' && element.alt) {
            element.alt = this.t(key, params);
        } else if (element.tagName === 'OPTION') {
            element.textContent = this.t(key, params);
        } else {
            element.textContent = this.t(key, params);
        }
    }

    static getParamsFromElement(element) {
        const params = {};
        const paramAttributes = element.getAttributeNames().filter(attr => 
            attr.startsWith('data-i18n-param-')
        );
        
        paramAttributes.forEach(attr => {
            const paramName = attr.replace('data-i18n-param-', '');
            params[paramName] = element.getAttribute(attr);
        });
        
        return params;
    }

    static setupLanguageSelector() {
        const selector = document.getElementById('languageSelector');
        if (!selector) {
            window.APP_LOGGER.warn('Language selector element not found');
            return;
        }

        // Limpiar opciones existentes
        selector.innerHTML = '';

        // Llenar opciones
        this.getAvailableLanguages().forEach(lang => {
            const option = document.createElement('option');
            option.value = lang;
            option.textContent = this.t(`languages.${lang}`);
            option.selected = lang === this.currentLang;
            selector.appendChild(option);
        });

        selector.addEventListener('change', (e) => {
            this.changeLanguage(e.target.value);
        });

        window.APP_LOGGER.debug('Language selector initialized');
    }

    static updateLanguageSelector() {
        const selector = document.getElementById('languageSelector');
        if (!selector) return;

        Array.from(selector.options).forEach(option => {
            option.textContent = this.t(`languages.${option.value}`);
        });
    }

    static subscribe(callback) {
        if (typeof callback === 'function') {
            this.observers.push(callback);
        }
    }

    static unsubscribe(callback) {
        this.observers = this.observers.filter(obs => obs !== callback);
    }

    static notifyObservers() {
        this.observers.forEach(callback => {
            try {
                callback(this.currentLang);
            } catch (error) {
                window.APP_LOGGER.error('Error in language observer:', error);
            }
        });
    }

    static getCurrentLanguage() {
        return this.currentLang;
    }

    static getAvailableLanguages() {
        return ['es', 'en', 'eu'];
    }

    static getTranslation(key, params = {}) {
        return this.t(key, params);
    }
}