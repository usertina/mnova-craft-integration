"""
CraftRMN Pro - Módulo de Base de Datos SQLite
Gestiona todas las operaciones de base de datos local del dispositivo
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
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
        """Inicializa todas las tablas necesarias"""
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
        
        # Tabla de mediciones
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
        
        conn.commit()
        conn.close()
        logger.info("Base de datos inicializada correctamente")
    
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
                synced, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            0, now, now
        ))
        
        measurement_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Medición guardada con ID: {measurement_id} para {measurement_data.get('company_id')}")
        return measurement_id
    
    def get_measurement(self, measurement_id: int) -> Optional[Dict]:
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
    ) -> List[Dict]:
        """
        Obtiene lista de mediciones.
        CAMBIO: Si company_id es 'admin', devuelve todas.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM measurements"
        params = []
        
        # Si se especifica un ID y NO es 'admin', filtrar.
        if company_id and company_id != 'admin':
            query += " WHERE company_id = ?"
            params.append(company_id)
        # Si es 'admin' or None (aunque app.py ya no debería pasar None),
        # no se añade WHERE, por lo que trae todo.
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_measurement(row) for row in rows]
    
    def _row_to_measurement(self, row: sqlite3.Row) -> Dict:
        """Convierte una fila de SQLite a diccionario"""
        try:
            spectrum_data = json.loads(row['spectrum_data']) if row['spectrum_data'] else {}
            peaks_data = json.loads(row['peaks_data']) if row['peaks_data'] else []
        except json.JSONDecodeError:
            spectrum_data = {"error": "failed to decode spectrum"}
            peaks_data = {"error": "failed to decode peaks"}

        return {
            'id': row['id'],
            'device_id': row['device_id'],
            'company_id': row['company_id'],
            'timestamp': row['timestamp'],
            'filename': row['filename'],
            'analysis': {
                'fluor_percentage': row['fluor_percentage'],
                'pifas_percentage': row['pifas_percentage'],
                'pifas_concentration': row['pifas_concentration'],
                'concentration': row['concentration']
            },
            'quality_score': row['quality_score'],
            'spectrum': spectrum_data,
            'peaks': peaks_data,
            'synced': bool(row['synced']),
            'sync_attempts': row['sync_attempts'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }

# Instancia global de la base de datos
_db_instance = None

def get_db() -> Database:
    """Obtiene la instancia global de la base de datos"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance

