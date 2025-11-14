// ============================================================================
// Portal de Selección de Empresa - VERSIÓN CORREGIDA
// ============================================================================

document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 Portal iniciado');
    
    const companiesGrid = document.getElementById('companies-grid');
    const errorMessage = document.getElementById('error-message');
    
    try {
        // Obtener configuración del servidor
        const response = await fetch('/api/config');
        
        if (!response.ok) {
            throw new Error('Error de conexión con el servidor');
        }
        
        const config = await response.json();
        
        console.log('📊 Configuración recibida:', config);
        console.log('📊 Empresas disponibles:', config.available_companies);
        
        // Verificar que el dispositivo está activado
        if (!config.activated) {
            showError('Dispositivo no activado. Contacte con el administrador.');
            return;
        }
        
        // Obtener empresas disponibles
        const companies = config.available_companies || [];
        
        console.log(`✅ ${companies.length} empresas disponibles`);
        
        if (companies.length === 0) {
            showError('No hay empresas configuradas.');
            return;
        }
        
        // Renderizar empresas
        renderCompanies(companies);
        
    } catch (error) {
        console.error('❌ Error:', error);
        showError('Error de conexión. Recargue la página.');
    }
});

function renderCompanies(companies) {
    const grid = document.getElementById('companies-grid');
    grid.innerHTML = '';
    
    companies.forEach(company => {
        // ✅ DEBUG: Log de cada empresa
        console.log('🏢 Renderizando empresa:', company);
        
        const card = document.createElement('div');
        card.className = 'company-card';
        card.onclick = () => selectCompany(company);
        
        // ✅ CORRECCIÓN: Usar las propiedades correctas
        // Backend devuelve: { id: "FAES", name: "Faes Farma", logo: "assets/logos/...", pin: "1234" }
        // CORRECCIÓN: Tu backend usa el objeto profile completo, no id/name/logo
        const companyId = company.company_id || 'unknown';
        const companyName = company.company_name || 'Sin nombre';
        const companyLogo = company.logo_url || 'assets/images/logo_qubiz.png';
        
        card.innerHTML = `
            <img src="${companyLogo}" 
                 alt="${companyName}" 
                 class="company-logo"
                 onerror="this.src='assets/images/logo_qubiz.png'">
            <div class="company-name">${companyName}</div>
        `;
        
        grid.appendChild(card);
    });
    
    console.log(`✅ ${companies.length} cards renderizadas`);
}

function selectCompany(company) {
    // ✅ CORRECCIÓN: Obtener el ID correcto
    const companyId = company.company_id;
    const companyName = company.company_name;
    
    console.log(`🏢 Empresa seleccionada: ${companyName} (${companyId})`);
    console.log('📊 Objeto completo:', company);
    
    // Limpiar errores previos
    clearError();
    
    // Pedir PIN
    const pin = prompt(`Introduce el PIN de ${companyName}:`);
    
    if (!pin) {
        console.log('❌ PIN cancelado');
        return;
    }
    
    // Validar PIN
    validatePin(companyId, pin, companyName);
}

async function validatePin(companyId, pin, companyName) {
    try {
        console.log(`🔐 Validando PIN para: ${companyId}`);
        
        const response = await fetch('/api/validate_pin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                company_id: companyId,
                pin: pin
            })
        });
        
        const data = await response.json();
        
        console.log('📨 Respuesta del servidor:', data);
        
        if (response.ok && data.success) {
            console.log('✅ PIN correcto');
            
            // ✅ Guardar tokens JWT
            if (data.access_token) {
                localStorage.setItem('access_token', data.access_token);
                console.log('✅ Access token guardado');
            }
            
            if (data.refresh_token) {
                localStorage.setItem('refresh_token', data.refresh_token);
                console.log('✅ Refresh token guardado');
            }
            
            // --- ¡¡CORRECCIÓN AQUÍ!! ---
            // Guardar el perfil en sessionStorage con el nombre que app.html espera.
            if (data.profile) {
                sessionStorage.setItem('CURRENT_COMPANY_PROFILE', JSON.stringify(data.profile));
                console.log('✅ Perfil guardado en sessionStorage (CURRENT_COMPANY_PROFILE)');
            }
            // --- FIN DE LA CORRECCIÓN ---
            
            // Redirigir a la app principal
            console.log('🚀 Redirigiendo a app.html...');
            window.location.href = 'app.html';
            
        } else {
            console.error('❌ PIN incorrecto');
            showError('PIN incorrecto. Inténtalo de nuevo.');
        }
        
    } catch (error) {
        console.error('❌ Error validando PIN:', error);
        showError('Error de conexión. Inténtalo de nuevo.');
    }
}

function showError(message) {
    const errorEl = document.getElementById('error-message');
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.style.display = 'block';
    }
}

function clearError() {
    const errorEl = document.getElementById('error-message');
    if (errorEl) {
        errorEl.textContent = '';
        errorEl.style.display = 'none';
    }
}