# backend/translation_manager.py

"""
Gestor de Traducciones para CraftRMN Pro
Maneja la carga y obtención de traducciones multiidioma
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional


class TranslationManager:
    """
    Gestor de traducciones que carga archivos JSON de idiomas
    y proporciona una interfaz simple para obtener textos traducidos
    """
    
    # Directorio donde están los archivos de traducción
    # Ajusta esta ruta según tu estructura de proyecto
    TRANSLATIONS_DIR = Path(__file__).parent / 'i18n'
    
    # Idiomas soportados
    SUPPORTED_LANGUAGES = ['en', 'es', 'eu']
    
    # Idioma por defecto si no se especifica o no se encuentra
    DEFAULT_LANGUAGE = 'es'
    
    def __init__(self, language: str = 'es'):
        """
        Inicializa el gestor de traducciones
        
        Args:
            language: Código del idioma (en, es, eu)
        """
        self.language = language if language in self.SUPPORTED_LANGUAGES else self.DEFAULT_LANGUAGE
        self.translations: Dict = {}
        self._load_translations()
    
    def _load_translations(self) -> None:
        """Carga el archivo de traducción correspondiente al idioma"""
        translation_file = self.TRANSLATIONS_DIR / f"{self.language}.json"
        
        try:
            with open(translation_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            print(f"✅ Traducciones cargadas: {self.language}.json")
        except FileNotFoundError:
            print(f"⚠️  Archivo de traducción no encontrado: {translation_file}")
            print(f"   Buscando en rutas alternativas...")
            
            # Intentar rutas alternativas
            alternative_paths = [
                Path(__file__).parent.parent / 'translations' / f"{self.language}.json",
                Path.cwd() / 'translations' / f"{self.language}.json",
                Path.cwd() / f"{self.language}.json",
            ]
            
            for alt_path in alternative_paths:
                if alt_path.exists():
                    try:
                        with open(alt_path, 'r', encoding='utf-8') as f:
                            self.translations = json.load(f)
                        print(f"✅ Traducciones cargadas desde: {alt_path}")
                        return
                    except Exception as e:
                        continue
            
            print(f"❌ No se pudo cargar el archivo de traducción para {self.language}")
            print(f"   Se usarán los códigos de traducción sin procesar")
            self.translations = {}
            
        except json.JSONDecodeError as e:
            print(f"❌ Error al decodificar JSON: {e}")
            self.translations = {}
        except Exception as e:
            print(f"❌ Error inesperado al cargar traducciones: {e}")
            self.translations = {}
    
    def get(self, key: str, default: Optional[str] = None) -> str:
        """
        Obtiene una traducción usando notación de punto
        
        Args:
            key: Clave en formato 'section.item' (ej: 'report.title')
            default: Valor por defecto si no se encuentra la traducción
        
        Returns:
            Texto traducido o el código entre corchetes si no se encuentra
        
        Examples:
            >>> t = TranslationManager('es')
            >>> t.get('report.title')
            'Informe de Análisis RMN'
            >>> t.get('report.subtitle')
            'Detección y Cuantificación de PFAS'
        """
        parts = key.split('.')
        value = self.translations
        
        # Navegar por el diccionario anidado
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
                if value is None:
                    # No se encontró la traducción
                    if default is not None:
                        return default
                    return f"[{key}]"
            else:
                # El valor no es un diccionario, no se puede continuar
                if default is not None:
                    return default
                return f"[{key}]"
        
        return str(value)
    
    def __call__(self, key: str, default: Optional[str] = None) -> str:
        """
        Permite usar el manager como una función
        
        Examples:
            >>> t = TranslationManager('es')
            >>> t('report.title')
            'Informe de Análisis RMN'
        """
        return self.get(key, default)
    
    def translate(self, key: str, **kwargs) -> str:
        """
        Obtiene una traducción y reemplaza placeholders
        
        Args:
            key: Clave de traducción
            **kwargs: Valores para reemplazar en la traducción (si tiene placeholders)
        
        Returns:
            Texto traducido con placeholders reemplazados
        
        Examples:
            >>> t = TranslationManager('es')
            >>> t.translate('comparison.subtitle', count=5)
            'Análisis Comparativo de 5 Muestras'
        """
        text = self.get(key)
        
        # Reemplazar placeholders {variable}
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    
    def switch_language(self, language: str) -> None:
        """
        Cambia el idioma actual
        
        Args:
            language: Nuevo código de idioma (en, es, eu)
        """
        if language in self.SUPPORTED_LANGUAGES:
            self.language = language
            self._load_translations()
        else:
            print(f"⚠️  Idioma no soportado: {language}")
    
    def get_available_languages(self) -> list:
        """Devuelve la lista de idiomas soportados"""
        return self.SUPPORTED_LANGUAGES.copy()
    
    def get_current_language(self) -> str:
        """Devuelve el idioma actual"""
        return self.language
    
    def is_loaded(self) -> bool:
        """Verifica si las traducciones están cargadas"""
        return bool(self.translations)
    
    def get_all_translations(self) -> Dict:
        """Devuelve todas las traducciones cargadas (útil para debugging)"""
        return self.translations.copy()


# ============================================================================
# FUNCIÓN AUXILIAR PARA USO RÁPIDO
# ============================================================================

def create_translator(language: str = 'es') -> TranslationManager:
    """
    Función auxiliar para crear rápidamente un traductor
    
    Args:
        language: Código del idioma
    
    Returns:
        Instancia de TranslationManager
    
    Example:
        >>> t = create_translator('es')
        >>> t('report.title')
        'Informe de Análisis RMN'
    """
    return TranslationManager(language)


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("DEMOSTRACIÓN DEL TRANSLATION MANAGER")
    print("=" * 70)
    print()
    
    # Crear traductor en español
    t = TranslationManager('es')
    
    if t.is_loaded():
        print(f"✅ Idioma actual: {t.get_current_language()}")
        print()
        
        # Ejemplos de uso
        print("Ejemplos de traducciones:")
        print("-" * 70)
        
        test_keys = [
            'report.title',
            'report.subtitle',
            'report.sample',
            'report.date',
            'results.fluor',
            'results.pfas',
            'results.concentration',
            'units.percentage',
            'units.millimolar',
            'peaks.title'
        ]
        
        for key in test_keys:
            translation = t(key)
            print(f"{key:30s} → {translation}")
        
        print()
        print("-" * 70)
        
        # Ejemplo con placeholders
        print("\nEjemplo con placeholders:")
        comparison_text = t.translate('comparison.subtitle', count=5)
        print(f"comparison.subtitle (count=5) → {comparison_text}")
        
    else:
        print("❌ No se pudieron cargar las traducciones")
        print("   Verifica que los archivos JSON estén en el directorio correcto")