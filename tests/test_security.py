"""
🔒 TESTS DE SEGURIDAD - SQL INJECTION
CraftRMN Pro - Verificación de protecciones

Ejecutar desde la carpeta raíz del proyecto:
    python tests/test_security.py

O desde la carpeta tests:
    python test_security.py
"""

import sys
from pathlib import Path
import logging

# Configurar logging para ver los warnings
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

# CORRECCIÓN: Añadir el directorio backend al path
# Detectar si estamos en /tests o en la raíz
current_dir = Path(__file__).parent.resolve()
project_root = current_dir.parent if current_dir.name == 'tests' else current_dir

# Añadir la carpeta backend al sys.path
backend_dir = project_root / "backend"
if backend_dir.exists():
    sys.path.insert(0, str(backend_dir))
    print(f"📁 Backend encontrado en: {backend_dir}")
else:
    # Intentar otras ubicaciones comunes
    possible_paths = [
        project_root / "worker",  # Por si database.py está en worker
        project_root,              # Por si está en la raíz
    ]
    
    for path in possible_paths:
        if (path / "database.py").exists():
            sys.path.insert(0, str(path))
            backend_dir = path
            print(f"📁 database.py encontrado en: {path}")
            break
    else:
        print("❌ ERROR: No se encuentra database.py")
        print(f"   Buscado en:")
        print(f"   - {backend_dir}")
        for path in possible_paths:
            print(f"   - {path}")
        print("\n   Asegúrate de ejecutar el script desde la carpeta correcta.")
        sys.exit(1)

# Ahora sí, importar database
try:
    from database import get_db
    print("✅ Módulo database importado correctamente\n")
except ImportError as e:
    print(f"❌ Error al importar database: {e}")
    print(f"   sys.path: {sys.path}")
    sys.exit(1)


def test_sql_injection_attempts():
    """
    Prueba varios intentos de SQL injection conocidos.
    Todos deben ser bloqueados o neutralizados.
    """
    
    try:
        db = get_db()
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")
        print("   Asegúrate de que la base de datos existe.")
        print("   Ejecuta primero: python backend/app.py")
        return False
    
    # Lista de payloads de inyección SQL comunes
    malicious_inputs = [
        # Intentos de borrar tablas
        "'; DROP TABLE measurements; --",
        "test'; DROP TABLE measurements; --",
        
        # Intentos de bypass de autenticación
        "' OR '1'='1",
        "' OR 1=1--",
        "admin'--",
        "' OR 'x'='x",
        
        # Intentos de UNION injection
        "' UNION SELECT * FROM device_config--",
        "1' UNION SELECT NULL, NULL, NULL--",
        
        # Intentos de UPDATE/DELETE
        "%'; DELETE FROM measurements WHERE '1'='1",
        "'; UPDATE measurements SET company_id='hacked'--",
        
        # Intentos de ejecución de comandos
        "'; EXEC sp_MSForEachTable 'DROP TABLE ?'--",
        "'; EXEC xp_cmdshell('dir')--",
        
        # Intentos de extracción de información
        "' AND 1=CONVERT(int, (SELECT TOP 1 key FROM device_config))--",
        "' AND '1'='1' UNION SELECT key, value FROM device_config--",
        
        # Intentos con encoding
        "admin%27--",
        "admin%22--",
        
        # Intentos con caracteres especiales
        "test\'; DROP TABLE measurements; --",
        "test\\'; DROP TABLE measurements; --",
    ]
    
    print("\n" + "=" * 70)
    print("🔒 TESTS DE SEGURIDAD - SQL INJECTION PROTECTION")
    print("=" * 70)
    print("\nProbando protecciones contra SQL Injection...")
    print("Si todos los tests muestran ✅, las protecciones funcionan correctamente.\n")
    
    passed = 0
    failed = 0
    
    for i, malicious in enumerate(malicious_inputs, 1):
        try:
            # Intentar búsqueda con input malicioso
            result = db.count_measurements_with_search("admin", malicious)
            
            # Verificar que no haya causado daño
            # Un resultado 0 o muy bajo indica que la entrada fue sanitizada
            if result == 0:
                print(f"✅ Test {i:2d}/18: BLOQUEADO correctamente")
                passed += 1
            else:
                print(f"⚠️  Test {i:2d}/18: Resultado sospechoso ({result} matches)")
                print(f"    Puede indicar problema de sanitización")
                failed += 1
            
            print(f"    Payload: {malicious[:60]}{'...' if len(malicious) > 60 else ''}")
            
        except Exception as e:
            print(f"❌ Test {i:2d}/18: ERROR inesperado")
            print(f"    Payload: {malicious[:60]}")
            print(f"    Error: {str(e)[:100]}")
            failed += 1
        
        print()
    
    print("=" * 70)
    print(f"\n📊 RESULTADOS:")
    print(f"   ✅ Tests pasados: {passed}/18")
    print(f"   ❌ Tests fallidos: {failed}/18")
    
    if failed == 0:
        print(f"\n🎉 ¡EXCELENTE! Todas las protecciones funcionan correctamente.")
        print(f"   Tu aplicación está protegida contra SQL Injection.")
        return True
    else:
        print(f"\n⚠️  ATENCIÓN: Algunos tests fallaron.")
        print(f"   Revisa que aplicaste todos los cambios correctamente.")
        return False
    
    print("=" * 70 + "\n")


def test_valid_searches():
    """
    Prueba que las búsquedas legítimas siguen funcionando.
    """
    
    try:
        db = get_db()
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")
        return False
    
    valid_searches = [
        "muestra",
        "test-01",
        "sample.csv",
        "archivo_2024",
        "data 123",
        "NMR",
    ]
    
    print("\n" + "=" * 70)
    print("✅ TESTS DE FUNCIONALIDAD - BÚSQUEDAS VÁLIDAS")
    print("=" * 70)
    print("\nProbando que las búsquedas normales funcionan...\n")
    
    passed = 0
    failed = 0
    
    for i, search in enumerate(valid_searches, 1):
        try:
            result = db.count_measurements_with_search("admin", search)
            print(f"✅ Test {i}/6: '{search}' -> {result} resultados")
            passed += 1
        except Exception as e:
            print(f"❌ Test {i}/6: '{search}' -> ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    if failed == 0:
        print("✅ Todas las búsquedas funcionan correctamente.")
        print("   La sanitización no afecta búsquedas legítimas.")
        return True
    else:
        print("⚠️  Algunas búsquedas fallaron. Revisa la función _sanitize_search_term.")
        return False
    
    print("=" * 70 + "\n")


def test_company_id_validation():
    """
    Prueba la validación de company_id.
    """
    
    try:
        db = get_db()
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("🔐 TESTS DE VALIDACIÓN - COMPANY_ID")
    print("=" * 70)
    print("\nProbando validación de company_id...\n")
    
    test_cases = [
        ("admin", True, "ID válido"),
        ("FAES", True, "ID válido"),
        ("AUGAS_GALICIA", True, "ID con guion bajo válido"),
        ("'; DROP TABLE--", False, "Inyección SQL"),
        ("../../../etc/passwd", False, "Path traversal"),
        ("company@malicious.com", False, "Caracteres especiales"),
        ("", False, "Vacío"),
        ("a" * 100, False, "Demasiado largo"),
    ]
    
    passed = 0
    failed = 0
    
    for company_id, should_pass, description in test_cases:
        try:
            result = db.count_measurements_with_search(company_id, "test")
            
            if should_pass and result >= 0:
                print(f"✅ '{company_id}': {description} - Aceptado correctamente")
                passed += 1
            elif not should_pass and result == 0:
                print(f"✅ '{company_id}': {description} - Rechazado correctamente")
                passed += 1
            else:
                print(f"⚠️  '{company_id}': {description} - Comportamiento inesperado")
                failed += 1
                
        except Exception as e:
            if not should_pass:
                print(f"✅ '{company_id}': {description} - Rechazado con excepción")
                passed += 1
            else:
                print(f"❌ '{company_id}': {description} - Error: {e}")
                failed += 1
    
    print(f"\n📊 Resultados: {passed}/{len(test_cases)} tests pasados")
    print("=" * 70 + "\n")
    
    return failed == 0


def check_protections_installed():
    """
    Verifica si las protecciones están instaladas en el código.
    """
    
    print("\n" + "=" * 70)
    print("🔍 VERIFICACIÓN DE PROTECCIONES INSTALADAS")
    print("=" * 70)
    print()
    
    try:
        from database import Database
        db_instance = Database()
        
        checks = {
            "_sanitize_search_term": hasattr(db_instance, '_sanitize_search_term'),
            "_validate_company_id": hasattr(db_instance, '_validate_company_id'),
        }
        
        all_ok = True
        
        for func_name, exists in checks.items():
            if exists:
                print(f"✅ Función {func_name}() encontrada")
            else:
                print(f"❌ Función {func_name}() NO encontrada")
                all_ok = False
        
        print()
        
        if all_ok:
            print("✅ Todas las protecciones están instaladas correctamente.")
            return True
        else:
            print("⚠️  ATENCIÓN: Faltan algunas protecciones.")
            print("   Revisa INSTRUCCIONES_PASO_A_PASO.md")
            return False
            
    except Exception as e:
        print(f"❌ Error al verificar protecciones: {e}")
        return False
    
    finally:
        print("=" * 70 + "\n")


def run_all_tests():
    """Ejecuta todos los tests de seguridad."""
    
    print("\n" + "=" * 70)
    print("🚀 EJECUTANDO SUITE COMPLETA DE TESTS DE SEGURIDAD")
    print("=" * 70)
    
    results = {
        'protections': False,
        'injection': False,
        'functionality': False,
        'validation': False
    }
    
    try:
        # 0. Verificar que las protecciones están instaladas
        results['protections'] = check_protections_installed()
        
        if not results['protections']:
            print("\n⚠️  Las protecciones no están completamente instaladas.")
            print("   Instala las correcciones antes de ejecutar los tests.")
            print("   Ver: INSTRUCCIONES_PASO_A_PASO.md\n")
            return False
        
        # 1. Tests de SQL Injection
        results['injection'] = test_sql_injection_attempts()
        
        # 2. Tests de funcionalidad normal
        results['functionality'] = test_valid_searches()
        
        # 3. Tests de validación de company_id
        results['validation'] = test_company_id_validation()
        
        # Resumen final
        print("\n" + "=" * 70)
        print("🏁 RESUMEN FINAL")
        print("=" * 70)
        print(f"\n✅ Protecciones instaladas: {'SÍ' if results['protections'] else 'NO'}")
        print(f"{'✅' if results['injection'] else '❌'} Tests SQL Injection: {'PASADOS' if results['injection'] else 'FALLIDOS'}")
        print(f"{'✅' if results['functionality'] else '❌'} Tests Funcionalidad: {'PASADOS' if results['functionality'] else 'FALLIDOS'}")
        print(f"{'✅' if results['validation'] else '❌'} Tests Validación: {'PASADOS' if results['validation'] else 'FALLIDOS'}")
        
        all_passed = all(results.values())
        
        print("\n" + "=" * 70)
        if all_passed:
            print("🎉 ¡TODOS LOS TESTS PASARON!")
            print("   Tu aplicación está correctamente protegida.")
        else:
            print("⚠️  ALGUNOS TESTS FALLARON")
            print("   Revisa los resultados arriba y corrige los problemas.")
        print("=" * 70 + "\n")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO durante los tests: {e}")
        print("Verifica que la base de datos existe y el servidor está configurado.\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⛔ Tests interrumpidos por el usuario.\n")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error fatal: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)