#!/usr/bin/env python3
"""
Test de Reintento de Sincronización (Optimizado)
Verifica que el endpoint /api/sync/retry funciona.
"""

import requests
import time
import sys
import os

# --- Configuración ---
SERVER_URL = "http://127.0.0.1:5000"
ADMIN_PIN = "0000" # Asegúrate de que este es el PIN de 'ADMIN'
ADMIN_ID = "ADMIN"
RETRY_WAIT_TIME_SECONDS = 10 # Reducido para un test más rápido
# ---------------------

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def print_header(title):
    print(f"\n{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.CYAN}🧪 TEST: {title.upper()}{Colors.RESET}")
    print(f"{Colors.CYAN}{'-' * 70}{Colors.RESET}")

def print_pass(message):
    print(f"{Colors.GREEN}✅ PASS{Colors.RESET} | {message}")

def print_fail(message):
    print(f"{Colors.RED}❌ FAIL{Colors.RESET} | {message}")

def login_admin():
    """Obtiene un token JWT de administrador."""
    print(f"1. Obteniendo token de admin de {SERVER_URL}...")
    try:
        r = requests.post(f"{SERVER_URL}/api/validate_pin", json={
            "company_id": ADMIN_ID,
            "pin": ADMIN_PIN
        }, timeout=5)
        r.raise_for_status()
        token = r.json().get('access_token')
        if not token:
            print_fail("No se pudo obtener el 'access_token'. ¿PIN correcto?")
            return None
        print_pass("Token de admin obtenido.")
        return token
    except requests.exceptions.RequestException as e:
        print_fail(f"No se pudo contactar al servidor. ¿Está encendido? {e}")
        return None

def get_sync_status(token):
    """Obtiene el estado de la sincronización."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(f"{SERVER_URL}/api/sync/status", headers=headers, timeout=5)
        r.raise_for_status()
        status = r.json()
        pending = status.get('pending', 0)
        return pending
    except requests.exceptions.RequestException as e:
        print_fail(f"No se pudo obtener el estado de sync/status: {e}")
        return -1

def trigger_retry(token):
    """Llama al endpoint de reintento."""
    print(f"3. Lanzando reintento manual (POST /api/sync/retry)...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.post(f"{SERVER_URL}/api/sync/retry", headers=headers, timeout=10)
        r.raise_for_status()
        print_pass(f"Respuesta del servidor: {r.json().get('message')}")
        return True
    except requests.exceptions.RequestException as e:
        print_fail(f"Fallo al lanzar el reintento: {e}")
        return False

def main():
    print_header("Test de Reintento de Sincronización (/api/sync/retry)")
    
    token = login_admin()
    if not token:
        return 1 # Fallo crítico
    
    print("\n2. Comprobando estado de sincronización (ANTES)...")
    pending_before = get_sync_status(token)
    
    if pending_before == -1:
        print_fail("No se pudo obtener el estado inicial.")
        return 1
    if pending_before == 0:
        print_pass("No hay mediciones pendientes. El test se omite (no hay nada que reintentar).")
        print("   Para probar, desconecta la red, haz un análisis y vuelve a ejecutar esto.")
        return 0 # No es un fallo, solo no hay nada que probar

    print(f"   ℹ️  Estado (ANTES): {pending_before} mediciones pendientes.")

    if not trigger_retry(token):
        print_fail("El endpoint de reintento dio error.")
        return 1
        
    print(f"\n4. Esperando {RETRY_WAIT_TIME_SECONDS} segundos a que los hilos trabajen...")
    time.sleep(RETRY_WAIT_TIME_SECONDS)

    print("\n5. Comprobando estado de sincronización (DESPUÉS)...")
    pending_after = get_sync_status(token)
    
    if pending_after == -1:
        print_fail("No se pudo obtener el estado después del reintento.")
        return 1
        
    print(f"   ℹ️  Estado (DESPUÉS): {pending_after} mediciones pendientes.")

    # --- Resumen Final ---
    print(f"\n{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.CYAN}📊 RESUMEN FINAL DE REINTENTO{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    
    if pending_after < pending_before:
        print_pass("¡ÉXITO! El número de mediciones pendientes se ha reducido.")
        print(f"   Antes: {pending_before}, Después: {pending_after}")
        return 0
    else:
        print_fail("FALLO: El reintento se lanzó pero el número de pendientes no cambió.")
        print(f"   Antes: {pending_before}, Después: {pending_after}")
        print("   Revisa los logs del servidor para ver por qué falló la sincronización (¿Google Sheets caído?).")
        return 1

if __name__ == "__main__":
    sys.exit(main())