# backend/translation_manager.py

"""
Translation Manager para CraftRMN Pro
Gestiona las traducciones de los reportes exportados
"""

import json
from pathlib import Path
from typing import Dict, Any

class TranslationManager:
    """Gestor de traducciones para reportes"""
    
    def __init__(self, lang: str = 'es'):
        self.lang = lang
        self.translations = {}
        self.i18n_dir = Path(__file__).parent / 'i18n'
        self.load_translations(lang)
    
    def load_translations(self, lang: str):
        """Carga las traducciones para un idioma específico"""
        try:
            file_path = self.i18n_dir / f'{lang}.json'
            
            if not file_path.exists():
                print(f"⚠️  Translation file not found: {file_path}, falling back to Spanish")
                lang = 'es'
                file_path = self.i18n_dir / 'es.json'
            
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
                self.lang = lang
                print(f"✅ Translations loaded: {lang}")
                
        except Exception as e:
            print(f"❌ Error loading translations for {lang}: {e}")
            # Fallback a español
            if lang != 'es':
                self.load_translations('es')
    
    def t(self, key: str, params: Dict[str, Any] = None) -> str:
        """
        Obtiene una traducción por su clave
        
        Args:
            key: Clave de traducción en formato 'section.subsection.key'
            params: Parámetros opcionales para reemplazar en el texto
            
        Returns:
            Texto traducido
        """
        keys = key.split('.')
        value = self.translations
        
        try:
            for k in keys:
                value = value[k]
            
            # Reemplazar parámetros si existen
            if params and isinstance(value, str):
                for param_key, param_value in params.items():
                    value = value.replace(f'{{{param_key}}}', str(param_value))
            
            return value
            
        except (KeyError, TypeError):
            print(f"⚠️  Translation key not found: {key}")
            return f'[{key}]'  # Retornar la clave si no se encuentra
    
    def change_language(self, lang: str):
        """Cambia el idioma de las traducciones"""
        self.load_translations(lang)
    
    @staticmethod
    def get_supported_languages():
        """Retorna los idiomas soportados"""
        return ['es', 'en', 'eu']
    
    def __call__(self, key: str, params: Dict[str, Any] = None) -> str:
        """Permite usar el TranslationManager como función"""
        return self.t(key, params)


# Instancia global (opcional)
_default_manager = None

def get_translator(lang: str = 'es') -> TranslationManager:
    """
    Obtiene una instancia del TranslationManager
    
    Args:
        lang: Código de idioma (es, en, eu)
        
    Returns:
        Instancia de TranslationManager
    """
    return TranslationManager(lang)


def t(key: str, params: Dict[str, Any] = None, lang: str = 'es') -> str:
    """
    Función de conveniencia para obtener traducciones
    
    Args:
        key: Clave de traducción
        params: Parámetros opcionales
        lang: Código de idioma
        
    Returns:
        Texto traducido
    """
    global _default_manager
    
    if _default_manager is None or _default_manager.lang != lang:
        _default_manager = TranslationManager(lang)
    
    return _default_manager.t(key, params)