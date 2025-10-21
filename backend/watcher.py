import time
import shutil
import sys
from pathlib import Path
from datetime import datetime

# Importar el analizador
sys.path.append(str(Path(__file__).parent.parent / "worker"))
from analyzer import SpectrumAnalyzer

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Carpeta donde Craft RMN exporta los archivos
CRAFT_EXPORT_DIR = Path("storage/craft_exports").resolve()

# Carpeta donde se guardan los archivos originales
OUTPUT_DIR = Path("storage/output").resolve()

# Carpeta donde se guardan los análisis
ANALYSIS_DIR = Path("storage/analysis").resolve()

# Crear directorios si no existen
CRAFT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

# Extensiones de archivo soportadas
SUPPORTED_EXTENSIONS = ['.csv', '.txt']

# Intervalo de verificación (segundos)
CHECK_INTERVAL = 5

# Parámetros de análisis por defecto
DEFAULT_PARAMS = {
    "fluor_range": {"min": -150, "max": -50},
    "pifas_range": {"min": -130, "max": -60},  # Rango típico PFAS en 19F-NMR
    "concentration": 1.0  # mM
}

# ============================================================================
# FUNCIONES
# ============================================================================

def is_supported_file(file_path: Path) -> bool:
    """Verifica si el archivo tiene una extensión soportada"""
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS

def process_file(file_path: Path, params: dict = None):
    """
    Procesa un archivo nuevo:
    1. Copia a OUTPUT_DIR
    2. Analiza con el analyzer
    3. Guarda resultados
    """
    if params is None:
        params = DEFAULT_PARAMS
    
    try:
        print(f"\n{'='*60}")
        print(f"🆕 Nuevo archivo detectado: {file_path.name}")
        print(f"{'='*60}")
        
        # 1. Copiar a OUTPUT_DIR
        dest_path = OUTPUT_DIR / file_path.name
        shutil.copy(file_path, dest_path)
        print(f"📁 Copiado a: {dest_path}")
        
        # 2. Analizar con el analyzer
        print(f"🔬 Iniciando análisis...")
        analyzer = SpectrumAnalyzer()
        
        results = analyzer.analyze_file(
            dest_path,
            fluor_range=params["fluor_range"],
            pifas_range=params["pifas_range"],
            concentration=params["concentration"]
        )
        
        # 3. Guardar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"{file_path.stem}_analysis_{timestamp}.json"
        result_path = ANALYSIS_DIR / result_filename
        
        import json
        with open(result_path, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Resultados guardados: {result_filename}")
        
        # 4. Mostrar resumen
        print(f"\n📊 RESUMEN:")
        print(f"   Flúor:         {results['analysis']['fluor_percentage']:.2f}%")
        print(f"   PFAS:          {results['analysis']['pifas_percentage']:.2f}% del flúor")
        print(f"   Concentración: {results['analysis']['pifas_concentration']:.4f} mM")
        print(f"   Calidad:       {results['quality_score']:.1f}/10")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Error procesando {file_path.name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# MAIN - Monitor continuo
# ============================================================================

def main():
    """
    Monitor principal que vigila la carpeta de Craft RMN
    y procesa automáticamente los archivos nuevos
    """
    print("="*60)
    print("🔍 CraftRMN File Watcher")
    print("="*60)
    print(f"📁 Vigilando: {CRAFT_EXPORT_DIR}")
    print(f"📊 Analizador: SpectrumAnalyzer")
    print(f"⏱️  Intervalo: {CHECK_INTERVAL}s")
    print(f"📝 Extensiones: {', '.join(SUPPORTED_EXTENSIONS)}")
    print("="*60)
    print("\n⏳ Esperando archivos nuevos...\n")
    
    # Set para trackear archivos ya procesados
    seen_files = set()
    
    # Agregar archivos existentes al set para no reprocesarlos
    for file_path in CRAFT_EXPORT_DIR.glob("*"):
        if file_path.is_file() and is_supported_file(file_path):
            seen_files.add(file_path.name)
    
    if seen_files:
        print(f"ℹ️  Archivos existentes ignorados: {len(seen_files)}")
    
    # Loop principal
    try:
        while True:
            # Buscar archivos nuevos
            current_files = []
            for file_path in CRAFT_EXPORT_DIR.glob("*"):
                if file_path.is_file() and is_supported_file(file_path):
                    current_files.append(file_path)
            
            # Procesar archivos nuevos
            for file_path in current_files:
                if file_path.name not in seen_files:
                    # Nuevo archivo detectado
                    success = process_file(file_path, DEFAULT_PARAMS)
                    
                    if success:
                        seen_files.add(file_path.name)
                    
                    # Pequeña pausa entre archivos
                    time.sleep(1)
            
            # Esperar antes de la próxima verificación
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n⛔ Watcher detenido por el usuario")
        print("👋 ¡Hasta pronto!")
        sys.exit(0)

# ============================================================================
# Modo manual - Procesar archivos específicos
# ============================================================================

def manual_mode():
    """Modo manual para procesar archivos específicos"""
    print("="*60)
    print("📁 Modo Manual - Procesamiento de Archivos")
    print("="*60)
    
    # Listar archivos disponibles
    files = [f for f in CRAFT_EXPORT_DIR.glob("*") 
             if f.is_file() and is_supported_file(f)]
    
    if not files:
        print("\n⚠️  No hay archivos disponibles para procesar")
        print(f"   Carpeta: {CRAFT_EXPORT_DIR}")
        return
    
    print(f"\nArchivos disponibles ({len(files)}):\n")
    for i, file_path in enumerate(files, 1):
        size_kb = file_path.stat().st_size / 1024
        print(f"  {i}. {file_path.name} ({size_kb:.1f} KB)")
    
    print("\nOpciones:")
    print("  - Número del archivo para procesarlo")
    print("  - 'all' para procesar todos")
    print("  - 'q' para salir")
    
    choice = input("\n> ").strip().lower()
    
    if choice == 'q':
        return
    elif choice == 'all':
        print(f"\n🔄 Procesando {len(files)} archivos...\n")
        for file_path in files:
            process_file(file_path)
            time.sleep(0.5)
    else:
        try:
            index = int(choice) - 1
            if 0 <= index < len(files):
                process_file(files[index])
            else:
                print("❌ Número inválido")
        except ValueError:
            print("❌ Opción inválida")

# ============================================================================
# EJECUTAR
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        manual_mode()
    else:
        main()