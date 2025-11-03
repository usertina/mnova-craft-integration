"""
CraftRMN Pro - Módulo de Base de Datos SQLite
Gestiona todas las operaciones de base de datos local del dispositivo
(VERSIÓN CORREGIDA - Extrae datos completos de raw_data)
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """Gestiona la base de datos SQLite local del dispositivo"""
    
    def __init__(self, db_path: str = "storage/measurements.db"):
        # Ancla la ruta al directorio de este script
        base_path = Path(__file__).parent.resolve()
        self.db_path = base_path / db_path
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
        
    def get_connection(self):
        """Obtiene una conexión a la base de datos con WAL mode"""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Inicializa todas las tablas necesarias (CON MOLECULE_INFO)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabla de configuración del dispositivo
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Tabla de mediciones (VERSIÓN 2.0 - CON MOLECULE_INFO)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                company_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                filename TEXT NOT NULL,
                fluor_percentage REAL,
                pifas_percentage REAL,
                pifas_concentration REAL,
                concentration REAL,
                quality_score REAL,
                raw_data TEXT NOT NULL,
                spectrum_data TEXT,
                peaks_data TEXT,
                molecule_info TEXT,
                synced INTEGER DEFAULT 0,
                sync_attempts INTEGER DEFAULT 0,
                last_sync_attempt TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Índices
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_measurements_company 
            ON measurements(company_id, timestamp DESC)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_measurements_synced 
            ON measurements(synced, created_at)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_measurements_filename 
            ON measurements(filename)
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Base de datos inicializada correctamente")
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Ejecuta una consulta SQL y devuelve todas las filas."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.commit()
            return rows
        except Exception as e:
            logger.error(f"Error ejecutando query: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
        finally:
            conn.close()
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Convierte una fila de SQLite a diccionario (versión simplificada)."""
        if not row:
            return {}
        
        try:
            return {
                'id': row['id'],
                'device_id': row['device_id'],
                'company_id': row['company_id'],
                'timestamp': row['timestamp'],
                'filename': row['filename'],
                'sample_name': row['filename'],
                'fluor_percentage': row['fluor_percentage'],
                'pfas_percentage': row['pifas_percentage'],  # Nombre principal
                'pifas_percentage': row['pifas_percentage'],  # Alias
                'pfas_concentration': row['pifas_concentration'],  # Nombre principal
                'pifas_concentration': row['pifas_concentration'],  # Alias
                'concentration': row['concentration'],
                'quality_score': row['quality_score'],
                'synced': bool(row['synced']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
        except Exception as e:
            logger.error(f"Error convirtiendo fila a dict: {e}")
            return {'error': str(e)}
    
    # ==================== CONFIGURACIÓN ====================
    
    def get_config(self, key: str) -> Optional[str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM device_config WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row['value'] if row else None
    
    def set_config(self, key: str, value: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT OR REPLACE INTO device_config (key, value, updated_at)
            VALUES (?, ?, ?)
        ''', (key, str(value), now))
        conn.commit()
        conn.close()
    
    def get_all_config(self) -> Dict[str, str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM device_config")
        config = {row['key']: row['value'] for row in cursor.fetchall()}
        conn.close()
        return config
    
    # ==================== MEDICIONES ====================
    
    def save_measurement(self, measurement_data: Dict) -> int:
        """
        Guarda una nueva medición en la base de datos
        (VERSIÓN CORREGIDA - 18 COLUMNAS)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        analysis = measurement_data.get('analysis', {})
        
        cursor.execute('''
            INSERT INTO measurements (
                device_id, company_id, timestamp, filename,
                fluor_percentage, pifas_percentage, pifas_concentration,
                concentration, quality_score,
                raw_data, spectrum_data, peaks_data,
                molecule_info, synced, sync_attempts, last_sync_attempt,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            measurement_data.get('device_id', 'unknown'),
            measurement_data.get('company_id', 'unknown'),
            measurement_data.get('timestamp', now),
            measurement_data.get('filename', 'unknown'),
            analysis.get('fluor_percentage'),
            analysis.get('pifas_percentage'),
            analysis.get('pifas_concentration'),
            analysis.get('concentration'),
            measurement_data.get('quality_score'),
            json.dumps(measurement_data),
            json.dumps(measurement_data.get('spectrum', {})),
            json.dumps(measurement_data.get('peaks', [])),
            json.dumps(measurement_data.get('molecule_info')),
            0,
            0,
            None,
            now,
            now
        ))
        
        measurement_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Medición guardada con ID: {measurement_id} para {measurement_data.get('company_id')}")
        return measurement_id
    
    def get_measurement(self, measurement_id: int) -> Optional[Dict]:
        """Obtiene una medición específica por ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM measurements WHERE id = ?", (measurement_id,))
        row = cursor.fetchone()
        conn.close()
        return self._row_to_measurement(row) if row else None
    
    def get_measurements(
        self, 
        company_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict:
        """
        Obtiene lista de mediciones.
        Si company_id es 'admin', devuelve todas las mediciones.
        
        Returns:
            Dict con 'measurements' (lista) y 'total' (int)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM measurements"
        params = []
        
        # Si se especifica un ID y NO es 'admin', filtrar por empresa
        if company_id and company_id != 'admin':
            query += " WHERE company_id = ?"
            params.append(company_id)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Obtener total de mediciones
        total = self.count_measurements(company_id)
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        
        conn.close()
        
        measurements = [self._row_to_measurement(row) for row in rows]
        
        return {
            'measurements': measurements,
            'total': total,
            'total_pages': total_pages
        }
    
    def count_measurements(self, company_id: Optional[str] = None) -> int:
        """
        Cuenta el total de mediciones para una empresa.
        Si company_id es 'admin' o None, cuenta todas.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if company_id == 'admin' or company_id is None:
                query = "SELECT COUNT(*) FROM measurements"
                cursor.execute(query)
            else:
                query = "SELECT COUNT(*) FROM measurements WHERE company_id = ?"
                cursor.execute(query, (company_id,))
            
            result = cursor.fetchone()
            count = result[0] if result else 0
            
            conn.close()
            return count
            
        except Exception as e:
            logger.error(f"Error counting measurements: {e}")
            return 0
    
    def get_measurements_with_search(
        self, 
        company_id: str, 
        search_term: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> Dict:
        """Obtiene mediciones con búsqueda por filename."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            search_pattern = f"%{search_term}%"
            
            if company_id == 'admin':
                query = """
                    SELECT * FROM measurements 
                    WHERE filename LIKE ?
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                """
                params = (search_pattern, limit, offset)
            else:
                query = """
                    SELECT * FROM measurements 
                    WHERE company_id = ? AND filename LIKE ?
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                """
                params = (company_id, search_pattern, limit, offset)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Contar total con búsqueda
            total = self.count_measurements_with_search(company_id, search_term)
            total_pages = (total + limit - 1) // limit if total > 0 else 0
            
            conn.close()
            
            measurements = [self._row_to_measurement(row) for row in rows]
            
            return {
                'measurements': measurements,
                'total': total,
                'total_pages': total_pages
            }
            
        except Exception as e:
            logger.error(f"Error getting measurements with search: {e}")
            return {'measurements': [], 'total': 0, 'total_pages': 0}
    
    def count_measurements_with_search(self, company_id: str, search_term: str) -> int:
        """Cuenta mediciones que coinciden con un término de búsqueda."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            search_pattern = f"%{search_term}%"
            
            if company_id == 'admin':
                query = "SELECT COUNT(*) FROM measurements WHERE filename LIKE ?"
                params = (search_pattern,)
            else:
                query = """
                    SELECT COUNT(*) FROM measurements 
                    WHERE company_id = ? AND filename LIKE ?
                """
                params = (company_id, search_pattern)
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            count = result[0] if result else 0
            
            conn.close()
            return count
            
        except Exception as e:
            logger.error(f"Error counting measurements with search: {e}")
            return 0
    
    def delete_measurement(self, measurement_id: int, company_id: Optional[str] = None) -> bool:
        """Elimina una medición específica."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if company_id and company_id != 'admin':
                cursor.execute(
                    "SELECT company_id FROM measurements WHERE id = ?", 
                    (measurement_id,)
                )
                row = cursor.fetchone()
                if not row:
                    conn.close()
                    return False
                if row['company_id'] != company_id:
                    logger.warning(
                        f"Intento de eliminar medición {measurement_id} "
                        f"de empresa {row['company_id']} por empresa {company_id}"
                    )
                    conn.close()
                    return False
            
            cursor.execute("DELETE FROM measurements WHERE id = ?", (measurement_id,))
            deleted = cursor.rowcount > 0
            
            conn.commit()
            conn.close()
            
            if deleted:
                logger.info(f"Medición {measurement_id} eliminada correctamente")
            else:
                logger.warning(f"No se encontró medición {measurement_id} para eliminar")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error eliminando medición {measurement_id}: {e}")
            return False
    
    def delete_all_measurements(self, company_id: Optional[str] = None) -> int:
        """Elimina todas las mediciones de una empresa."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if company_id == 'admin' or company_id is None:
                cursor.execute("DELETE FROM measurements")
            else:
                cursor.execute("DELETE FROM measurements WHERE company_id = ?", (company_id,))
            
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(
                f"Eliminadas {deleted_count} mediciones "
                f"{'(todas)' if company_id == 'admin' else f'de {company_id}'}"
            )
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error eliminando mediciones: {e}")
            return 0
    
    def _row_to_measurement(self, row: sqlite3.Row) -> Dict:
        """
        Convierte una fila de SQLite a diccionario completo de medición.
        ✅ VERSIÓN CORREGIDA - Extrae datos completos de raw_data
        """
        if not row:
            return {}
        
        try:
            # Parsear los datos JSON
            spectrum_data = json.loads(row['spectrum_data']) if row['spectrum_data'] else {}
            peaks_data = json.loads(row['peaks_data']) if row['peaks_data'] else []
            molecule_info_data = json.loads(row['molecule_info']) if row['molecule_info'] else None
            
            # 🔧 CORRECCIÓN: Extraer el objeto 'analysis' completo desde 'raw_data'
            raw_data = json.loads(row['raw_data']) if row['raw_data'] else {}
            analysis_full = raw_data.get('analysis', {})
            
            # Si analysis_full está vacío, usar los valores de las columnas como fallback
            if not analysis_full:
                logger.warning(f"Medición {row['id']}: raw_data['analysis'] está vacío, usando columnas directas")
                analysis_full = {
                    'fluor_percentage': row['fluor_percentage'],
                    'pfas_percentage': row['pifas_percentage'],  # Usar 'pfas' como estándar
                    'pifas_percentage': row['pifas_percentage'],  # Mantener 'pifas' para compatibilidad
                    'pfas_concentration': row['pifas_concentration'],
                    'pifas_concentration': row['pifas_concentration'],
                    'concentration': row['concentration']
                }
            
            logger.debug(f"Medición {row['id']}: analysis extraído con {len(analysis_full)} campos")
            
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON de medición {row['id']}: {e}")
            spectrum_data = {"error": "failed to decode spectrum"}
            peaks_data = []
            molecule_info_data = None
            analysis_full = {
                'fluor_percentage': row['fluor_percentage'],
                'pifas_percentage': row['pifas_percentage'],
                'pfas_percentage': row['pifas_percentage'],
                'pifas_concentration': row['pifas_concentration'],
                'concentration': row['concentration']
            }

        return {
            'id': row['id'],
            'device_id': row['device_id'],
            'company_id': row['company_id'],
            'timestamp': row['timestamp'],
            'filename': row['filename'],
            'sample_name': row['filename'],
            
            # ✅ USAR EL OBJETO ANALYSIS COMPLETO de raw_data
            'analysis': analysis_full,
            
            # Mantener campos directos para compatibilidad
            'fluor_percentage': row['fluor_percentage'],
            'pfas_percentage': row['pifas_percentage'],  # Nombre principal: pfas
            'pifas_percentage': row['pifas_percentage'],  # Alias para compatibilidad
            'pfas_concentration': row['pifas_concentration'],  # Nombre principal: pfas
            'pifas_concentration': row['pifas_concentration'],  # Alias para compatibilidad
            'quality_score': row['quality_score'],
            
            # Datos adicionales
            'spectrum': spectrum_data,
            'peaks': peaks_data,
            'molecule_info': molecule_info_data,
            'synced': bool(row['synced']),
            'sync_attempts': row['sync_attempts'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }


# ==================== INSTANCIA GLOBAL ====================

_db_instance = None

def get_db() -> Database:
    """Obtiene la instancia global de la base de datos"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance