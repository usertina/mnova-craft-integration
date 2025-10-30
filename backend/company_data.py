"""
Archivo Central de Perfiles de Empresa.
"""

COMPANY_PROFILES = {
    "admin": {
        'company_id': 'admin',
        'company_name': 'Administrador (TODOS LOS DATOS)',
        'logo_url': '/assets/images/logo_qubiz.png', # Un logo de "CraftRMN" o de admin
        'primary_color': '#424242', # Gris oscuro
        'secondary_color': '#616161',
        'language': 'es',
        'contact_email': 'admin@craftrmn.com'
    },

    "FAES": {
    # --- Identidad Visual ---
    'company_id': 'FAES',
    'company_name': 'Faes Farma',
    'logo_url': '/assets/logos/faes_logo.png',         
    'favicon_url': '/assets/favicons/faes_favicon.ico', 
    'primary_color': '#004b8d',
    'secondary_color': '#006fcf',
    
    # --- Datos para Reportes (PDF) ---
    'language': 'es',
    'contact_email': 'atencionalcliente@faes.es',
    'contact_phone': '+34 94 481 83 00',            
    'company_address': 'Máximo Aguirre 14, 48940 Leioa, Bizkaia' 
},

    "AUGAS_GALICIA": {
        'company_id': 'AUGAS_GALICIA',
        'company_name': 'Augas de Galicia',
        'logo_url': '/assets/logos/augas_de_galicia_logo.png',
        'favicon_url': '/assets/favicons/augas_favicon.ico',
        'primary_color': '#0090d0', # Azul corporativo de Augas de Galicia
        'secondary_color': '#0070a0',

    # --- Datos para Reportes (PDF) ---    
        'language': 'es', 
        'contact_email': 'augasdegalicia@xunta.gal',
        'contact_phone': '+34 981 95 74 01',             
        'company_address': 'Plaza Camilo Díaz Baliño 7-9, 15781 Santiago de Compostela'
    }
}
