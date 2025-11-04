document.addEventListener('DOMContentLoaded', () => {
    // --- TODO EL JAVASCRIPT SE EJECUTA DESPUÉS DE QUE EL DOM ESTÉ LISTO ---

    // Elementos de la UI
    const loadingView = document.getElementById('loading-view');
    const activationView = document.getElementById('activation-view');
    const companySelectionView = document.getElementById('company-selection-view');
    const criticalErrorContainer = document.getElementById('critical-error-container');
    const criticalErrorMessageEl = document.getElementById('critical-error-message');
    const deviceIdDisplay = document.getElementById('device-id-display');
    const licenseKeyInput = document.getElementById('license-key');
    const activateButton = document.getElementById('activate-button');
    const activateBtnText = document.getElementById('activate-btn-text');
    const activateBtnLoading = document.getElementById('activate-btn-loading');
    const activationError = document.getElementById('activation-error');
    const companyGrid = document.getElementById('company-grid');
    const selectionError = document.getElementById('selection-error');

    // --- URL Base de la API (Absoluta) ---
    const API_BASE_URL = window.location.origin; // e.g., http://localhost:5000

    // --- Función para Mostrar Error Crítico ---
    function showCriticalError(message) {
        console.error("Mostrando error crítico:", message);
        if(loadingView) loadingView.style.display = 'none';
        if(activationView) activationView.classList.add('hidden');
        if(companySelectionView) companySelectionView.classList.add('hidden');
        if(criticalErrorContainer) criticalErrorContainer.classList.remove('hidden');
        if(criticalErrorMessageEl) criticalErrorMessageEl.textContent = message;
    }

    // --- Función para Mostrar Vista de Activación ---
    function showActivationView(deviceId) {
        console.log("Mostrando vista de activación para deviceId:", deviceId);
        if(loadingView) loadingView.style.display = 'none';
        if(companySelectionView) companySelectionView.classList.add('hidden');
        if(criticalErrorContainer) criticalErrorContainer.classList.add('hidden');
        if(activationView) activationView.classList.remove('hidden');
        if(deviceIdDisplay) deviceIdDisplay.textContent = deviceId || 'No disponible';
    }

     // --- Función para Manejar Selección de Empresa (NUEVA VERSIÓN CON PIN) ---
    async function selectCompany(companyProfile) {
        console.log("selectCompany (con PIN) ejecutada para:", companyProfile);

        const companyId = companyProfile.company_id;
        if (!companyId) {
            console.error("Perfil inválido, sin company_id", companyProfile);
            if(selectionError) {
                selectionError.textContent = 'Error interno: Perfil inválido.';
                selectionError.classList.remove('hidden');
            }
            return;
        }

        // 1. Pedir el PIN al usuario
        const pin = prompt(`Por favor, introduce el PIN para ${companyProfile.company_name}:`);

        if (pin === null) {
            // El usuario pulsó "Cancelar"
            console.log("Validación de PIN cancelada.");
            return; 
        }

        // Limpiar errores antiguos
        if(selectionError) selectionError.classList.add('hidden');

        try {
            // 2. Llamar a la nueva API de validación que creamos en app.py
            const validateUrl = `${API_BASE_URL}/api/validate_pin`; // Usa tu constante global
            const response = await fetch(validateUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    company_id: companyId,
                    pin: pin
                })
            });

            const data = await response.json();

            if (!response.ok) {
                // Si la respuesta es 403 (Prohibido), 404, etc.
                throw new Error(data.error || 'PIN o empresa incorrectos');
            }

            // 3. ¡ÉXITO! Guardamos el perfil en el navegador
            // Usamos 'CURRENT_COMPANY_PROFILE' para ser consistentes con app.html
            sessionStorage.setItem('CURRENT_COMPANY_PROFILE', JSON.stringify(data.profile));

            // 4. Redirigir a la app
            console.log("PIN validado. Perfil guardado. Redirigiendo a app.html...");
            window.location.href = 'app.html';

        } catch (err) {
            console.error('Error al validar PIN:', err);
            // Mostrar el error en la UI
            if(selectionError) {
                selectionError.textContent = `Error: ${err.message}`;
                selectionError.classList.remove('hidden');
            } else {
                alert(`Error: ${err.message}`); // Fallback
            }
        }
    } 

    // --- Función para CREAR una Tarjeta de Empresa ---
    function createCompanyCard(company) {
         // console.log("Creando tarjeta para:", company.company_id); // Log opcional
         try {
             if (!company || typeof company !== 'object' || !company.company_id) {
                 console.warn("createCompanyCard: Saltando empresa inválida:", company);
                 return null;
             }
             const card = document.createElement('div');
             
             // ¡¡AQUÍ ESTÁ LA MODIFICACIÓN DE HOVER DE TAILWIND!!
             // He quitado .company-card y he puesto las clases de Tailwind
             card.className = 'bg-gray-700 p-4 rounded-lg shadow-md flex flex-col items-center cursor-pointer hover:bg-gray-600 transition-all duration-200 ease-in-out hover:-translate-y-1 hover:shadow-lg';
             card.setAttribute('data-company-id', company.company_id);

             const logo = document.createElement('img');
             logo.src = company.logo_url || 'https://placehold.co/100x50/7f7f7f/ffffff?text=Logo';
             logo.alt = `${company.company_name || 'Unknown'} Logo`;
             logo.className = 'h-16 w-auto object-contain mb-3';
             logo.onerror = (e) => { e.target.src = 'https://placehold.co/100x50/7f7f7f/ffffff?text=Logo'; };

             const name = document.createElement('p');
             name.className = 'text-sm font-semibold text-center text-white';
             name.textContent = company.company_name || 'Unnamed';

             card.appendChild(logo);
             card.appendChild(name);

             // Listener - ¡CAMBIO! Log directo aquí
             card.addEventListener('click', (event) => {
                 // LOG INMEDIATO AL HACER CLICK
                 console.log(`¡CLICK DETECTADO en ${company.company_id}!`, event);
                 // Ahora llamar a la función original
                 selectCompany(company);
             });
             // console.log("Listener de click añadido para:", company.company_id); // Log opcional

             return card;
         } catch(e) {
              console.error("Error creando tarjeta para:", company, e);
              return null;
         }
    }

    // --- Función para Mostrar Vista de Selección ---
    function showCompanySelectionView(companies) {
        console.log("Mostrando vista de selección con:", companies);
        if(loadingView) loadingView.style.display = 'none';
        if(activationView) activationView.classList.add('hidden');
        if(criticalErrorContainer) criticalErrorContainer.classList.add('hidden');
        if(companySelectionView) companySelectionView.classList.remove('hidden');
        
        // ESTA COMPROBACIÓN AHORA FUNCIONARÁ
        if(!companyGrid) return showCriticalError("Error: No se encontró el contenedor de empresas.");

        companyGrid.innerHTML = '';

        if (!Array.isArray(companies)) {
            console.error("showCompanySelectionView: companies no es un array!", companies);
            return showCriticalError("Error interno: Formato de datos de empresas inválido.");
        }
        if (companies.length === 0) {
            if(selectionError) {
                 selectionError.textContent = 'No hay empresas configuradas.';
                 selectionError.classList.remove('hidden');
            }
            return;
        }

        companies.forEach(company => {
            const cardElement = createCompanyCard(company);
            if (cardElement) {
                companyGrid.appendChild(cardElement);
            }
        });
        console.log("Tarjetas de empresa añadidas al DOM.");
    }


    // --- Función para Manejar Activación ---
    async function handleActivation() {
        if (!activateButton || !licenseKeyInput || !activationError || !activateBtnText || !activateBtnLoading) return;
        console.log("Intentando activar...");
        const licenseKey = licenseKeyInput.value.trim();
        if (!licenseKey) {
            activationError.textContent = 'Introduce la clave de licencia.';
            activationError.classList.remove('hidden');
            return;
        }

        activationError.classList.add('hidden');
        activateButton.disabled = true;
        activateBtnText.classList.add('hidden');
        activateBtnLoading.classList.remove('hidden');

        try {
            // --- CAMBIO: Usar URL absoluta ---
            const activateUrl = `${API_BASE_URL}/api/activate`;
            console.log("Enviando petición de activación a:", activateUrl);
            const response = await fetch(activateUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ license_key: licenseKey })
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || `Error ${response.status}`);
            console.log("Activación OK. Recargando...");
            window.location.reload();
        } catch (error) {
            console.error("Error de activación:", error);
            activationError.textContent = `Error: ${error.message}`;
            activationError.classList.remove('hidden');
        } finally {
            activateButton.disabled = false;
            activateBtnText.classList.remove('hidden');
            activateBtnLoading.classList.add('hidden');
        }
    }

    // --- Función Principal de Arranque ---
    async function initializePortal() {
        console.log("Iniciando initializePortal...");
        try {
            // --- CAMBIO: Usar URL absoluta ---
            const configUrl = `${API_BASE_URL}/api/config`;
            console.log("Solicitando configuración desde:", configUrl);
            const response = await fetch(configUrl);
            console.log("Respuesta de /api/config:", response.status);
            if (!response.ok) throw new Error(`Error ${response.status} del servidor.`);
            const config = await response.json();
            console.log("Configuración recibida:", config);

            if (!config || typeof config.activated === 'undefined') {
                throw new Error("Respuesta de configuración inválida.");
            }

            if (!config.activated) {
                showActivationView(config.device_id);
            } else {
                if (!Array.isArray(config.available_companies)) {
                     console.error("initializePortal: available_companies NO es array:", config.available_companies);
                     throw new Error("'available_companies' no es un array.");
                }
                showCompanySelectionView(config.available_companies);
            }
        } catch (error) {
            console.error("Error fatal en initializePortal:", error);
            // Mostrar el error original en la consola para más detalles
            console.error("Detalles del error:", error);
            showCriticalError(`No se pudo cargar: ${error.message}`);
        }
    }

    // --- CÓDIGO DE ARRANQUE ---
    // (Ahora que estamos dentro de DOMContentLoaded, podemos adjuntar listeners y llamar a la función principal)

    console.log("DOM listo. Adjuntando listeners e iniciando la aplicación del portal.");

    // Añadir listener al botón de activación
     if (activateButton) {
         activateButton.addEventListener('click', handleActivation);
     } else {
         console.warn("El botón de activación no se encontró.");
     }
    
    // Llamar a la función principal para empezar
    initializePortal();

}); // <-- NO OLVIDES ESTA LÍNEA QUE CIERRA EL 'DOMContentLoaded'