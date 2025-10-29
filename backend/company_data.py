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
        'company_id': 'FAES',
        'company_name': 'Faes Farma',
        'logo_url': '/assets/logos/faes_logo.png',
        'primary_color': '#004b8d', # Azul corporativo de Faes
        'secondary_color': '#006fcf',
        'language': 'es',
        'contact_email': 'info@faesfarma.com'
    },

    "AUGAS_GALICIA": {
        'company_id': 'AUGAS_GALICIA',
        'company_name': 'Augas de Galicia',
        'logo_url': '/assets/logos/augas_de_galicia_logo.png',
        'primary_color': '#0090d0', # Azul corporativo de Augas de Galicia
        'secondary_color': '#0070a0',
        'language': 'es', # O 'gl' si tuvieras un archivo de idioma gallego
        'contact_email': 'info@augasdegalicia.gal'
    }
}
