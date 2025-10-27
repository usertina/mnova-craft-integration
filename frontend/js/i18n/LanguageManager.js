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
        this.applyTranslations(); // Se aplicará a todo el 'document'
        
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
            
            this.applyTranslations(); // Aplica a todo el 'document'
            this.notifyObservers();
            
            // Actualizar atributo lang del HTML para accesibilidad
            document.documentElement.lang = lang;
            
            window.APP_LOGGER.info(`Language changed to: ${lang}`);
        } catch (error) {
            window.APP_LOGGER.error('Error changing language:', error);
            throw error;
        }
    }

    // --- FUNCIÓN CORREGIDA ---
    static applyTranslations(element = document) { // Usa 'document' por defecto
        // Título de la página
        const titleElement = document.querySelector('title[data-i18n]');
        if (titleElement) {
            document.title = this.t(titleElement.getAttribute('data-i18n'));
        } else {
            const appTitle = this.t('app.title');
            // Evita poner '[app.title]' si la clave no existe
            if (!appTitle.startsWith('[')) document.title = appTitle; 
        }

        // Elementos con data-i18n attribute
        element.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const params = this.getParamsFromElement(el);
            this.translateElement(el, key, params);
        });

        // Elementos con data-i18n-html (para HTML interno)
        element.querySelectorAll('[data-i18n-html]').forEach(el => {
            const key = el.getAttribute('data-i18n-html');
            const params = this.getParamsFromElement(el);
            el.innerHTML = this.t(key, params);
        });
        
        // --- CÓDIGO AÑADIDO Y CORREGIDO PARA PLACEHOLDERS ---
        element.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            const translation = this.t(key);
            // Solo traducir si la clave existe y no es el fallback '[key]'
            if (translation && !translation.startsWith('[')) { 
                el.setAttribute('placeholder', translation);
            } else if (!translation || translation.startsWith('[')) { // Log si la clave falta o es fallback
                // Ya se loguea en la función t(), no es necesario aquí
                // window.APP_LOGGER.warn(`Placeholder translation key not found or missing: ${key}`);
            }
        });
        // --- Fin del código para placeholders ---

        // Actualizar selector de idioma (siempre busca en todo el documento)
        this.updateLanguageSelector();
    }
    // --- FIN DE LA FUNCIÓN CORREGIDA ---


    static translateElement(element, key, params) {
        // (Esta función parece correcta, no la he modificado)
        if (element.tagName === 'INPUT') {
            const inputType = element.type.toLowerCase();
            if (inputType === 'submit' || inputType === 'button') {
                element.value = this.t(key, params);
            // 💡 NOTA: La lógica original traducía el placeholder aquí si el data-i18n estaba en el input.
            // Esto es redundante ahora que manejamos data-i18n-placeholder por separado.
            // } else if (inputType !== 'file') {
            //     element.placeholder = this.t(key, params); 
            }
        } else if (element.tagName === 'TEXTAREA') {
             // 💡 NOTA: También redundante si usas data-i18n-placeholder
             // element.placeholder = this.t(key, params);
        } else if (element.tagName === 'IMG' && element.hasAttribute('alt')) { // Mejor usar hasAttribute
            element.alt = this.t(key, params);
        } else if (element.tagName === 'OPTION') {
            element.textContent = this.t(key, params);
        } else {
            // Traduce el contenido de texto para otros elementos (label, span, p, etc.)
            element.textContent = this.t(key, params);
        }
    }

    static getParamsFromElement(element) {
        const params = {};
        // Usamos Array.from para compatibilidad y filtramos
        Array.from(element.attributes).forEach(attr => {
            if (attr.name.startsWith('data-i18n-param-')) {
                const paramName = attr.name.substring('data-i18n-param-'.length);
                params[paramName] = attr.value;
            }
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
            // Usamos una clave fija 'languages.{lang}' para el nombre del idioma
            option.textContent = this.t(`languages.${lang}`); 
            option.selected = lang === this.currentLang;
            selector.appendChild(option);
        });

        // Solo añadir el listener una vez
        if (!selector.dataset.listenerAttached) {
             selector.addEventListener('change', (e) => {
                  this.changeLanguage(e.target.value);
             });
             selector.dataset.listenerAttached = 'true'; // Marcar que ya tiene listener
        }


        window.APP_LOGGER.debug('Language selector initialized');
    }

    static updateLanguageSelector() {
        const selector = document.getElementById('languageSelector');
        if (!selector) return;

        // Actualizar el texto de cada opción
        Array.from(selector.options).forEach(option => {
            option.textContent = this.t(`languages.${option.value}`);
        });
        
        // Asegurarse de que la opción seleccionada coincida con el idioma actual
        selector.value = this.currentLang;
    }

    static subscribe(callback) {
        if (typeof callback === 'function' && !this.observers.includes(callback)) { // Evitar duplicados
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
        // Podrías obtener esto dinámicamente si tuvieras muchos idiomas
        return ['es', 'en', 'eu'];
    }

    // Método alias para conveniencia, si se usa externamente
    static getTranslation(key, params = {}) {
        return this.t(key, params);
    }
}