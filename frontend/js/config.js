// Configuración de la aplicación
const CONFIG = {
    development: {
        apiBaseURL: 'http://localhost:5000/api',
        debug: true,
        logLevel: 'debug',
        autoReconnect: true,
        reconnectInterval: 5000
    },
    production: {
        apiBaseURL: '/api', // Relative path for same domain
        debug: false,
        logLevel: 'error',
        autoReconnect: true,
        reconnectInterval: 10000
    },
    staging: {
        apiBaseURL: 'https://staging-api.tudominio.com/api',
        debug: true,
        logLevel: 'info',
        autoReconnect: true,
        reconnectInterval: 8000
    }
};

// Detección automática del entorno
const getConfig = () => {
    const hostname = window.location.hostname;
    const port = window.location.port;
    
    if (hostname === 'localhost' || hostname === '127.0.0.1' || port === '3000') {
        return CONFIG.development;
    } else if (hostname.includes('staging')) {
        return CONFIG.staging;
    } else {
        return CONFIG.production;
    }
};

// Configuración global
window.APP_CONFIG = getConfig();

// Logger configurado
window.APP_LOGGER = {
    debug: (...args) => window.APP_CONFIG.debug && console.debug('[RMN]', ...args),
    info: (...args) => console.info('[RMN]', ...args),
    warn: (...args) => console.warn('[RMN]', ...args),
    error: (...args) => console.error('[RMN]', ...args)
};