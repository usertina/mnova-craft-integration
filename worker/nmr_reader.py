"""
NMR Data Reader con soporte para múltiples formatos
Integra nmrglue para leer FID directos de espectrómetros

Formatos soportados:
- CSV (formato actual de JEOL Craft)
- Bruker (FID, ser, fid, 1r, 1i, 2rr)
- Varian/Agilent (fid)
- JEOL Delta (formato nativo JEOL)
- NMRPipe

VERSIÓN 19: Híbrido Final v3.
Re-implementa V16 (np.real + invertir + baseline_correct ord=1)
PERO AÑADE la normalización a 1M al final para la UI.
"""

import numpy as np
import csv
from pathlib import Path
from typing import Dict, Tuple, Optional
import logging

# Intentar importar nmrglue
try:
    import nmrglue as ng
    NMRGLUE_AVAILABLE = True
    logging.info("✅ nmrglue disponible - Soporte FID activado")
except ImportError:
    NMRGLUE_AVAILABLE = False
    logging.warning("⚠️  nmrglue no encontrado - Solo soporte CSV")
    logging.warning("   Instalar con: pip install nmrglue")


class NMRDataReader:
    """
    Lector universal de datos NMR
    """
    
    def __init__(self):
        self.data_format = None
        self.metadata = {}
    
    def detect_format(self, path: Path) -> str:
        if not path.exists():
            return 'unknown'
        if path.is_file() and path.suffix.lower() in ['.csv', '.txt']:
            return 'csv'
        if not NMRGLUE_AVAILABLE:
            return 'csv_only'
        if path.is_dir():
            has_fid = (path / 'fid').exists() or (path / 'ser').exists()
            has_acqus = (path / 'acqus').exists()
            if has_fid or has_acqus:
                return 'bruker'
        if path.is_file() and path.name == 'fid':
            parent = path.parent
            if (parent / 'procpar').exists():
                return 'varian'
            else:
                return 'bruker'
        if path.is_file():
            if path.suffix.lower() in ['.jdf', '.jdx', '.hdr']:
                return 'jeol'
        if path.is_file():
            if path.suffix.lower() in ['.ft', '.ft1', '.ft2']:
                return 'nmrpipe'
        return 'unknown'
    
    def read_data(self, path: Path) -> Tuple[np.ndarray, np.ndarray, Dict]:
        path = Path(path)
        data_format = self.detect_format(path)
        self.data_format = data_format
        logging.info(f"📂 Formato detectado: {data_format}")
        
        if data_format == 'csv':
            return self._read_csv(path)
        elif data_format == 'bruker' and NMRGLUE_AVAILABLE:
            return self._read_bruker(path)
        elif data_format == 'varian' and NMRGLUE_AVAILABLE:
            return self._read_varian(path)
        elif data_format == 'jeol' and NMRGLUE_AVAILABLE:
            return self._read_jeol(path)
        elif data_format == 'nmrpipe' and NMRGLUE_AVAILABLE:
            return self._read_nmrpipe(path)
        else:
            raise ValueError(f"Formato no soportado o nmrglue no disponible: {data_format}")
    
    def _read_csv(self, path: Path) -> Tuple[np.ndarray, np.ndarray, Dict]:
        ppm_values = []
        intensity_values = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                sample = f.read(4096)
                f.seek(0)
                try:
                    delimiter = csv.Sniffer().sniff(sample).delimiter
                except csv.Error:
                    delimiter = '\t'
                csv_reader = csv.reader(f, delimiter=delimiter)
                all_rows = list(csv_reader)
        except UnicodeDecodeError:
            with open(path, 'r', encoding='latin-1') as f:
                sample = f.read(4096)
                f.seek(0)
                delimiter = '\t'
                csv_reader = csv.reader(f, delimiter=delimiter)
                all_rows = list(csv_reader)
        
        num_cols = len(all_rows[0]) if all_rows else 0
        intensity_col = 1
        if num_cols > 2:
            intensity_col = self._find_best_intensity_column(all_rows, num_cols)
        
        for row in all_rows:
            if len(row) < 2:
                continue
            try:
                ppm_str = row[0].strip()
                intensity_str = row[intensity_col].strip()
                if not ppm_str or not intensity_str:
                    continue
                ppm = float(ppm_str)
                intensity = float(intensity_str)
                ppm_values.append(ppm)
                intensity_values.append(intensity)
            except (ValueError, IndexError):
                continue
        
        metadata = {'format': 'csv', 'filename': path.name, 'n_points': len(ppm_values)}
        return np.array(ppm_values), np.array(intensity_values), metadata
    
    def _read_bruker(self, path: Path) -> Tuple[np.ndarray, np.ndarray, Dict]:
        logging.info("  📖 Leyendo datos Bruker...")
        if path.is_file() and path.name == 'fid':
            parent_dir = path.parent
            logging.warning("  ⚠️  Archivo FID suelto detectado")
            acqus_path = parent_dir / 'acqus'
            if not acqus_path.exists():
                logging.info("  📝 Creando archivo acqus con parámetros por defecto...")
                self._create_default_acqus(acqus_path)
            path = parent_dir
        
        try:
            # 💡 SOLUCIÓN V19: Forzar que lea el FID crudo, ignorando el 1r procesado
                logging.info("  ✅ Leyendo FID crudo (ignorando 1r)...")
                dic, data = ng.bruker.read(str(path))
                logging.info("  ✅ FID crudo leído - procesando...")
                is_processed = False
                data = self._process_fid_bruker(data, dic) # V19
        
        except Exception as e:
            raise ValueError(f"Error leyendo datos Bruker: {e}")
        
        ppm_scale = self._create_ppm_scale_bruker(dic, len(data))
        metadata = self._extract_bruker_metadata(dic)
        metadata['format'] = 'bruker'
        metadata['processed'] = is_processed
        
        if np.iscomplexobj(data):
            logging.warning("  ⚠️  Se esperaba espectro real pero se encontró complejo. Tomando magnitud.")
            data = np.abs(data)
        
        return ppm_scale, data, metadata
    
    def _process_fid_bruker(self, fid: np.ndarray, dic: dict) -> np.ndarray:
        """
        Procesa FID de Bruker (FFT, phase correction, etc.)
        ✅ VERSIÓN 19: (V16) Inversión simple + Baseline + (V17) Normalización
        """
        
        # Zero filling
        fid = ng.proc_base.zf_size(fid, fid.size * 2)
        
        # Aplicar ventana exponencial
        fid = ng.proc_base.em(fid, lb=1.0)  # 1 Hz line broadening
        
        # Fourier Transform
        spectrum_complex = ng.proc_base.fft(fid)

        # 💡 V16: NO USAR NP.ABS. Tomar la parte real.
        spectrum_real = np.real(spectrum_complex)

        min_val = np.min(spectrum_real)
        max_val = np.max(spectrum_real)

        # 💡 V16: Comprobar si el espectro está "al revés" (picos negativos)
        if min_val < 0 and abs(min_val) > abs(max_val) * 2:
            logging.warning(f"  ⚠️  Espectro con fase invertida detectado (Min: {min_val:.2e}, Max: {max_val:.2e}). Invirtiendo...")
            spectrum_final = -spectrum_real # Invertir
        else:
            spectrum_final = spectrum_real # Usar como está

        # 💡 V16: Corregir el baseline (inclinación)
        try:
            logging.info("  💡 Aplicando corrección de línea base (lineal, ord=1)...")
            spectrum_final = ng.proc_base.baseline_corrector(spectrum_final, ord=1) # Corrección LINEAL
        except Exception as e:
            logging.error(f" ❌ Error aplicando corrección de línea base a FID: {e}")

        # 💡 V17: RE-NORMALIZAR a 1M (para la UI y el detector de picos)
        max_intensity = np.max(spectrum_final)
        if max_intensity > 0:
            spectrum_final = (spectrum_final / max_intensity) * 1_000_000
            logging.info(f" 💡 Espectro RE-NORMALIZADO a 1M (Max post-corrección: {max_intensity:.2e})")
        else:
            logging.warning(" ⚠️ Espectro nulo post-corrección; no se puede normalizar.")
        
        logging.info(f"  💡 Pasando espectro procesado (real) al analizador (Max: {np.max(spectrum_final):.2e}).")
        
        return spectrum_final
    
    def _create_ppm_scale_bruker(self, dic: dict, n_points: int) -> np.ndarray:
        try:
            sfo1 = float(dic['acqus']['SFO1'])
            sw_ppm = float(dic['acqus']['SW'])
            o1 = float(dic['acqus']['O1'])
            ref_ppm = o1 / sfo1
            ppm_max = ref_ppm + sw_ppm / 2
            ppm_min = ref_ppm - sw_ppm / 2
            return np.linspace(ppm_max, ppm_min, n_points)
        except Exception as e:
            logging.warning(f"  ⚠️  No se pudo crear escala PPM precisa: {e}")
            return np.linspace(0, -200, n_points)
    
    def _extract_bruker_metadata(self, dic: dict) -> Dict:
        metadata = {}
        try:
            acqus = dic.get('acqus', {})
            metadata['spectrometer_freq'] = float(acqus.get('SFO1', 0))
            metadata['nucleus'] = acqus.get('NUC1', 'unknown')
            metadata['pulse_program'] = acqus.get('PULPROG', 'unknown')
            metadata['n_scans'] = int(acqus.get('NS', 0))
            metadata['relaxation_delay'] = float(acqus.get('D1', 0))
            metadata['temperature'] = float(acqus.get('TE', 298))
            metadata['solvent'] = acqus.get('SOLVENT', 'unknown')
        except Exception as e:
            logging.warning(f"  ⚠️  Error extrayendo metadata: {e}")
        return metadata
    
    def _read_varian(self, path: Path) -> Tuple[np.ndarray, np.ndarray, Dict]:
        logging.info("  📖 Leyendo datos Varian/Agilent...")
        try:
            parent_dir = path.parent if path.is_file() else path
            dic, data = ng.varian.read(str(parent_dir))
            data = self._process_fid_generic(data) # 💡 V19: Usar genérico
            ppm_scale = self._create_ppm_scale_varian(dic, len(data))
            metadata = {
                'format': 'varian',
                'spectrometer_freq': dic['procpar'].get('sfrq', {}).get('values', [0])[0],
                'n_points': len(data)
            }
            return ppm_scale, data, metadata
        except Exception as e:
            raise ValueError(f"Error leyendo datos Varian: {e}")
    
    def _create_ppm_scale_varian(self, dic: dict, n_points: int) -> np.ndarray:
        try:
            procpar = dic['procpar']
            sfo1 = float(procpar['sfrq']['values'][0])
            sw = float(procpar['sw']['values'][0])
            sw_ppm = sw / sfo1
            return np.linspace(sw_ppm/2, -sw_ppm/2, n_points)
        except Exception as e:
            logging.warning(f"  ⚠️  Error creando escala PPM: {e}")
            return np.linspace(0, -200, n_points)
    
    def _read_jeol(self, path: Path) -> Tuple[np.ndarray, np.ndarray, Dict]:
        logging.info("  📖 Leyendo datos JEOL Delta...")
        try:
            dic, data = ng.jcampdx.read(str(path))
            if np.iscomplexobj(data):
                data = self._process_fid_generic(data) # 💡 V19: Usar genérico
            ppm_scale = self._create_ppm_scale_generic(dic, len(data))
            metadata = {'format': 'jeol', 'n_points': len(data)}
            return ppm_scale, data, metadata
        except Exception as e:
            raise ValueError(f"Error leyendo datos JEOL: {e}")
    
    def _read_nmrpipe(self, path: Path) -> Tuple[np.ndarray, np.ndarray, Dict]:
        logging.info("  📖 Leyendo datos NMRPipe...")
        try:
            dic, data = ng.pipe.read(str(path))
            uc = ng.pipe.make_uc(dic, data, dim=0)
            ppm_scale = uc.ppm_scale()
            metadata = {'format': 'nmrpipe', 'n_points': len(data)}
            # 💡 V19: Normalizar datos de NMRPipe si es necesario
            if np.max(data) < 1000: # Asumir que necesita normalización
                max_intensity = np.max(data)
                if max_intensity > 0:
                    data = (data / max_intensity) * 1_000_000
                    logging.info(f" 💡 Espectro NMRPipe RE-NORMALIZADO a 1M (Max: {max_intensity:.2e})")
            return ppm_scale, data, metadata
        except Exception as e:
            raise ValueError(f"Error leyendo datos NMRPipe: {e}")
    
    def _process_fid_generic(self, fid: np.ndarray) -> np.ndarray:
        """
        Procesamiento genérico de FID
        ✅ VERSIÓN 19: (V16) Inversión simple + Baseline + (V17) Normalización
        """
        
        # Zero filling
        fid = ng.proc_base.zf_size(fid, fid.size * 2)
        
        # Ventana
        fid = ng.proc_base.em(fid, lb=1.0)
        
        # FFT
        spectrum_complex = ng.proc_base.fft(fid)
        
        # 💡 V16: Invertir si es necesario, luego corregir baseline
        spectrum_real = np.real(spectrum_complex)

        min_val = np.min(spectrum_real)
        max_val = np.max(spectrum_real)

        if min_val < 0 and abs(min_val) > abs(max_val) * 2:
            logging.warning(f"  ⚠️  Espectro genérico con fase invertida detectado. Invirtiendo...")
            spectrum_final = -spectrum_real # Invertir
        else:
            spectrum_final = spectrum_real # Usar como está

        # 💡 V16: Corregir el baseline (inclinación)
        try:
            logging.info("  💡 Aplicando corrección de línea base genérica (lineal, ord=1)...")
            spectrum_final = ng.proc_base.baseline_corrector(spectrum_final, ord=1) # Corrección LINEAL
        except Exception as e:
            logging.error(f" ❌ Error aplicando corrección de línea base genérica: {e}")

        # 💡 V17: RE-NORMALIZAR a 1M
        max_intensity = np.max(spectrum_final)
        if max_intensity > 0:
            spectrum_final = (spectrum_final / max_intensity) * 1_000_000
            logging.info(f" 💡 Espectro genérico RE-NORMALIZADO a 1M (Max post-corrección: {max_intensity:.2e})")
        
        return spectrum_final
    
    def _create_ppm_scale_generic(self, dic: dict, n_points: int) -> np.ndarray:
        return np.linspace(0, -200, n_points)
    
    def _find_best_intensity_column(self, all_rows, num_cols):
        from scipy.signal import find_peaks
        column_stats = []
        for col_idx in range(1, num_cols):
            intensities = []
            for row in all_rows:
                if len(row) > col_idx and row[col_idx].strip():
                    try:
                        intensities.append(float(row[col_idx].strip()))
                    except ValueError:
                        pass
            if len(intensities) < 100:
                continue
            data = np.array(intensities)
            mean_val = np.mean(data)
            std_val = np.std(data)
            peak_count = len(find_peaks(data, height=mean_val + 2*std_val)[0])
            column_stats.append({
                'index': col_idx, 'mean': mean_val, 'std': std_val,
                'peak_count': peak_count, 'score': peak_count * std_val
            })
        if not column_stats:
            return 1
        best_column = max(column_stats, key=lambda x: x['score'])
        return best_column['index']
    
    def _create_default_acqus(self, acqus_path: Path):
        default_acqus_content = """##TITLE= Parameter file
##JCAMPDX= 5.0
##DATATYPE= Parameter Values
##ORIGIN= Bruker
##OWNER= unknown
$SFO1= 470.4
$SW= 100.0
$O1= 0
$NUC1= 19F
$NS= 1
$D1= 1.0
$TE= 298
$SOLVENT= unknown
$PULPROG= zgpg30
##END=
"""
        try:
            acqus_path.write_text(default_acqus_content, encoding='utf-8')
            logging.info("  ✅ Archivo acqus creado con parámetros por defecto")
        except Exception as e:
            logging.error(f"  ❌ Error creando acqus: {e}")
            raise

# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================

def read_nmr_data(path: Path) -> Tuple[np.ndarray, np.ndarray, Dict]:
    reader = NMRDataReader()
    return reader.read_data(path)

def is_nmrglue_available() -> bool:
    return NMRGLUE_AVAILABLE

if __name__ == '__main__':
    print("="*60)
    print("NMR Data Reader - Test")
    print("="*60)
    print(f"nmrglue disponible: {NMRGLUE_AVAILABLE}")
    
    if NMRGLUE_AVAILABLE:
        print("\n✅ Formatos soportados:")
        print("   - CSV (JEOL Craft export)")
        print("   - Bruker (fid, ser, 1r)")
        print("   - Varian/Agilent (fid)")
        print("   - JEOL Delta (.jdf)")
        print("   - NMRPipe (.ft)")
    else:
        print("\n⚠️  Solo soporte CSV")
        print("   Instalar nmrglue: pip install nmrglue")