# 🔬 CraftRMN Pro - Analizador Profesional de PFAS

Sistema completo de análisis de espectros RMN para detección y cuantificación de PFAS (sustancias perfluoroalquiladas).

## 📋 Características

- ✅ **Análisis automático** de espectros RMN de flúor (19F)
- ✅ **Detección de PFAS** en rango -60 a -130 ppm
- ✅ **Cálculo de concentraciones** y porcentajes
- ✅ **Interfaz web profesional** multiidioma (ES/EN/EU)
- ✅ **Procesamiento por lotes** de múltiples muestras
- ✅ **Visualización interactiva** con gráficos Plotly
- ✅ **Exportación de reportes** en JSON/CSV
- ✅ **Monitor automático** de nuevos archivos

---

## 🏗️ Estructura del Proyecto

```
proyecto/
├── backend/
│   ├── app.py              # Servidor Flask con API REST
│   ├── watcher.py          # Monitor automático de archivos
│   ├── requirements.txt    # Dependencias Python
│   └── storage/
│       ├── craft_exports/  # ← Craft RMN exporta aquí (automático)
│       ├── output/         # Archivos originales copiados
│       └── analysis/       # Resultados JSON de análisis
│
├── worker/
│   ├── analyzer.py         # Motor de análisis PFAS
│   └── requirements.txt    # Dependencias del analizador
│
└── frontend/
    ├── index.html          # Interfaz web principal
    ├── js/                 # JavaScript (API, gráficos, UI)
    ├── styles/             # CSS responsive
    └── i18n/               # Traducciones (es, en, eu)
```

---

## 🚀 Instalación

### 1. Requisitos Previos

```bash
# Python 3.8 o superior
python --version

# pip actualizado
python -m pip install --upgrade pip
```

### 2. Instalar Dependencias

```bash
# Backend
cd backend
pip install -r requirements.txt

# Worker (si usas analyzer.py standalone)
cd ../worker
pip install -r requirements.txt
```

### 3. Configurar Craft RMN

Configura Craft RMN para que **exporte automáticamente** los archivos CSV a:

```
backend/storage/craft_exports/
```

**Formato requerido del CSV:**
```csv
ppm,intensity
-150.0,12.5
-148.0,15.2
...
```

---

## ▶️ Uso

### Opción 1: Sistema Completo (Recomendado)

**Terminal 1 - Servidor Backend:**
```bash
cd backend
python app.py
```
> 🌐 Servidor corriendo en: http://localhost:5000

**Terminal 2 - Monitor de Archivos (Opcional):**
```bash
cd backend
python watcher.py
```
> 🔍 Vigilando carpeta craft_exports/ y analizando automáticamente

**Navegador:**
```
Abre: http://localhost:5000
```

### Opción 2: Solo Analizar un Archivo

```bash
cd worker
python analyzer.py ruta/al/espectro.csv
```

---

## 🎯 Workflow Típico

### 1️⃣ **Análisis Manual (Frontend)**

1. Abre http://localhost:5000
2. Arrastra un archivo CSV de Craft RMN
3. Ajusta parámetros (rangos ppm, concentración)
4. Click en "Ejecutar Análisis"
5. Visualiza resultados: gráfico + métricas
6. Exporta reporte si lo necesitas

### 2️⃣ **Análisis Automático (Watcher)**

1. Inicia el backend: `python app.py`
2. Inicia el watcher: `python watcher.py`
3. Craft RMN exporta → automáticamente se analiza
4. Consulta resultados en el frontend

### 3️⃣ **Procesamiento por Lotes**

1. En el frontend, ve a "Procesamiento por Lotes"
2. Selecciona múltiples archivos CSV
3. Click en "Ejecutar Análisis por Lotes"
4. Obtén tabla comparativa de todas las muestras

---

## 🧪 Prueba con Datos de Ejemplo

Incluimos un archivo de prueba `ejemplo_espectro.csv`:

```bash
# Opción 1: Desde el frontend
# → Arrastra ejemplo_espectro.csv

# Opción 2: Línea de comandos
cd worker
python analyzer.py ../ejemplo_espectro.csv
```

**Resultados esperados:**
- Flúor Total: ~85%
- PFAS: ~92% del flúor
- Concentración PFAS: ~0.78 mM (con 1 mM de muestra)

---

## ⚙️ Configuración

### Parámetros de Análisis

Puedes ajustar en el **frontend** o en `watcher.py`:

```python
DEFAULT_PARAMS = {
    "fluor_range": {"min": -150, "max": -50},    # Rango total de flúor
    "pifas_range": {"min": -130, "max": -60},    # Rango específico PFAS
    "concentration": 1.0                          # Concentración muestra (mM)
}
```

### Rangos Típicos en 19F-NMR:

- **Flúor orgánico general:** -50 a -150 ppm
- **PFAS (CF₂, CF₃):** -60 a -130 ppm
- **Fluoruros inorgánicos:** ~-120 ppm (aislado)

---

## 📊 Resultados del Análisis

El análisis genera un JSON completo:

```json
{
  "filename": "muestra_001.csv",
  "analysis": {
    "fluor_percentage": 85.23,
    "pifas_percentage": 91.45,
    "pifas_concentration": 0.7785,
    "concentration": 1.0
  },
  "spectrum": {
    "ppm": [-150, -148, ...],
    "intensity": [12.5, 15.2, ...]
  },
  "peaks": [
    {"ppm": -88.0, "intensity": 1255.2, "relative_intensity": 99.5}
  ],
  "quality_score": 8.5,
  "detailed_analysis": { ... }
}
```

---

## 🌍 Multiidioma

El frontend soporta:

- 🇪🇸 **Español** (por defecto)
- 🇬🇧 **English**
- 🇪🇸 **Euskara** (Vasco)

Se detecta automáticamente del navegador o se puede cambiar desde el selector.

---

## 🐛 Solución de Problemas

### Error: "No se puede conectar al servidor"

```bash
# Verifica que el backend esté corriendo
cd backend
python app.py
```

### Error: "Module not found: numpy"

```bash
# Instala dependencias
cd backend
pip install -r requirements.txt
```

### El watcher no detecta archivos

```bash
# Verifica la ruta en watcher.py:
CRAFT_EXPORT_DIR = Path("storage/craft_exports").resolve()

# Asegúrate de que Craft RMN exporta a esa carpeta
```

### Formato CSV no reconocido

Verifica que tu CSV tenga este formato:

```csv
ppm,intensity
-150.0,12.5
-148.0,15.2
```

**Importante:**
- Primera línea puede ser encabezado (se detecta automáticamente)
- Separador: coma (`,`)
- Dos columnas: ppm, intensidad

---

## 📝 API REST Endpoints

Para integración con otros sistemas:

### Health Check
```http
GET /api/health
```

### Análisis Individual
```http
POST /api/analyze
Content-Type: multipart/form-data

file: archivo.csv
parameters: {"fluor_range": {...}, "pifas_range": {...}, "concentration": 1.0}
```

### Análisis por Lotes
```http
POST /api/batch
Content-Type: multipart/form-data

files: [archivo1.csv, archivo2.csv, ...]
parameters: {...}
```

### Exportar Reporte
```http
POST /api/export
Content-Type: application/json

{
  "results": { ... },
  "format": "json" | "csv"
}
```

---

## 🔬 Fundamentos Científicos

### ¿Qué son los PFAS?

Los PFAS (Per- and Polyfluoroalkyl Substances) son compuestos químicos que contienen enlaces carbono-flúor. Son persistentes en el medio ambiente y bioacumulables.

### RMN de Flúor (19F-NMR)

El análisis por RMN de ¹⁹F permite:
- **Identificar** compuestos fluorados
- **Cuantificar** concentraciones relativas
- **Diferenciar** tipos de grupos funcionales (CF₂, CF₃, etc.)

### Interpretación de Rangos PPM

- **-60 a -80 ppm:** CF₃ terminales
- **-80 a -120 ppm:** CF₂ de cadena
- **-120 a -130 ppm:** CF₂ cerca de grupos funcionales

---

## 👥 Soporte y Contribuciones

¿Encontraste un bug? ¿Tienes sugerencias?

- 📧 Email: tu@email.com
- 🐛 Issues: [GitHub](https://github.com/tu-repo)

---

## 📄 Licencia

Proyecto propietario - Todos los derechos reservados

---

## 🎉 ¡Listo para usar!

```bash
# Terminal 1
cd backend && python app.py

# Terminal 2 (opcional)
cd backend && python watcher.py

# Navegador
http://localhost:5000
```

**¡Feliz análisis de PFAS! 🧪🔬**