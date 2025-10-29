// ============================================================================
// INIT.JS - Inicialización de componentes globales
// ============================================================================

console.log('[init.js] Script cargado');

// Función global para cerrar sesión
function logoutToPortal() {
    console.log('[logout] Cerrando sesión...');
    sessionStorage.removeItem('selectedCompanyProfile');
    window.location.href = 'index.html';
}
window.logoutToPortal = logoutToPortal;

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', async () => {
    console.log('[init.js] DOM cargado');
    
    // Esperar a que CURRENT_COMPANY_PROFILE esté disponible
    let attempts = 0;
    while (!window.CURRENT_COMPANY_PROFILE && attempts < 10) {
        console.log('[init.js] Esperando CURRENT_COMPANY_PROFILE...');
        await new Promise(resolve => setTimeout(resolve, 100));
        attempts++;
    }

    if (!window.CURRENT_COMPANY_PROFILE) {
        console.error('[init.js] CURRENT_COMPANY_PROFILE no disponible después de esperar');
        return;
    }

    console.log('[init.js] CURRENT_COMPANY_PROFILE disponible:', window.CURRENT_COMPANY_PROFILE);

    // Inicializar LanguageManager
    if (window.LanguageManager) {
        try {
            await LanguageManager.init();
            console.log('✅ [init.js] LanguageManager inicializado');
        } catch (error) {
            console.error('❌ [init.js] Error inicializando LanguageManager:', error);
        }
    } else {
        console.error('❌ [init.js] LanguageManager no está disponible');
    }

    // Mostrar branding de la empresa
    const brandingContainer = document.getElementById('companyBranding');
    const brandingLogo = document.getElementById('companyBrandingLogo');
    const brandingName = document.getElementById('companyBrandingName');

    if (brandingContainer && window.CURRENT_COMPANY_PROFILE) {
        if (brandingLogo && window.CURRENT_COMPANY_PROFILE.logo_url) {
            brandingLogo.src = window.CURRENT_COMPANY_PROFILE.logo_url;
            brandingLogo.style.display = 'block';
        }
        if (brandingName) {
            brandingName.textContent = window.CURRENT_COMPANY_PROFILE.company_name;
        }
        brandingContainer.style.display = 'flex';
    }

    console.log('[init.js] Inicialización completada');
});