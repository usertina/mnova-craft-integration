"""
Base de datos de PFAS con valores CIENTÍFICOS de literatura peer-reviewed
CraftRMN Pro v3.0 - Valores verificados de artículos científicos

FUENTES PRINCIPALES:
[1] Cheng et al. (2023) "Using 19F NMR to Investigate Cationic Carbon Dot Association 
    with PFAS" ACS Nanoscience Au. DOI: 10.1021/acsnanoscienceau.3c00022
[2] Nickerson et al. (2023) "Quantitation of Total PFAS Including Trifluoroacetic Acid 
    with Fluorine Nuclear Magnetic Resonance" PMC10601338
[3] Alesio et al. (2021) "Dominant Entropic Binding of Perfluoroalkyl Substances to 
    Albumin Protein Revealed by 19F NMR" PMC8479757
[4] Torres-Beltrán et al. (2025) "Experimental Determination of pKa for 10 PFAS by 19F-NMR"
    Environmental Science & Technology Letters
[5] Sharifan et al. (2021) "Total and class-specific analysis of PFAS using NMR"
    Current Opinion in Environmental Science & Health

CONDICIONES DE REFERENCIA:
- Referencia: CFCl3 (0.00 ppm)
- Solvente típico: D2O o CD3OD
- Temperatura: 298-300 K (25-27°C)
- pH: 7.0-7.4 (PBS buffer)

NOTA IMPORTANTE SOBRE DESPLAZAMIENTOS QUÍMICOS:
Los desplazamientos pueden variar ±0.1-0.5 ppm según:
- Solvente (D2O vs. CD3OD vs. PBS)
- Temperatura
- pH (para grupos ionizables)
- Concentración (agregación)
- Presencia de otros solutos

Los valores aquí son para PFAS libres en solución acuosa.
"""

# ============================================================================
# BASE DE DATOS PRINCIPAL DE PFAS
# ============================================================================

PFAS_DATABASE = {
    
    # ========================================================================
    # PERFLUOROALKYL CARBOXYLATES (PFCAs)
    # ========================================================================
    "PFOA_prueba": {
        "name": "PFOA (Perfluorooctanoic acid)",
        "formula": "C8HF15O2",
        "cas": "335-67-1",
        "chain_length": 8,
        "functional_group": "COOH",
        "category": "PFCA",
        "molecular_weight": 414.07,
        "regulation_status": "Restricted (Stockholm Convention)",
        "key_peaks": [
            {"ppm": -80.73, "type": "CF3", "relative_intensity": "strong", "source": "[1]"},
            {"ppm": -117.39, "type": "CF2-alpha", "relative_intensity": "medium", "source": "[1]"},
            {"ppm": -121.177, "type": "CF2-BETA", "relative_intensity": "strong", "source": "[3]"},
            {"ppm": -122.01, "type": "CF2-GANMA", "relative_intensity": "strong", "source": "[3]"},
            {"ppm": -122.73, "type": "CF2-DELTA", "relative_intensity": "medium", "source": "[3]"},
            {"ppm": -123.15, "type": "CF2-EPSILON", "relative_intensity": "medium", "source": "[3]"},
            {"ppm": -126.02, "type": "CF2-ZETA", "relative_intensity": "medium", "source": "[3]"}
        ],
        "peak_pattern": "CF3 terminal + CF2 internos + CF2-alpha COOH",
        "diagnostic_region": (-119, -116),  # CF2-alpha a COOH
        "pKa": -0.27,  # [4]
        "notes": "Valores de [1] Cheng 2023 en PBS pH 7.4. CF3 puede variar -80.5 a -82.4 ppm según condiciones."
    },
    
    "PFOA": {
        "name": "PFOA (Perfluorooctanoic acid)",
        "formula": "C8HF15O2",
        "cas": "335-67-1",
        "chain_length": 8,
        "functional_group": "COOH",
        "category": "PFCA",
        "molecular_weight": 414.07,
        "regulation_status": "Restricted (Stockholm Convention)",
        "key_peaks": [
            {"ppm": -80.7, "type": "CF3", "relative_intensity": "strong", "source": "[1]"},
            {"ppm": -117.4, "type": "CF2-alpha", "relative_intensity": "medium", "source": "[1]"},
            {"ppm": -122.0, "type": "CF2-internal", "relative_intensity": "strong", "source": "[3]"},
            {"ppm": -122.8, "type": "CF2-internal", "relative_intensity": "strong", "source": "[3]"},
            {"ppm": -126.5, "type": "CF2-beta", "relative_intensity": "medium", "source": "[3]"}
        ],
        "peak_pattern": "CF3 terminal + CF2 internos + CF2-alpha COOH",
        "diagnostic_region": (-119, -116),  # CF2-alpha a COOH
        "pKa": -0.27,  # [4]
        "notes": "Valores de [1] Cheng 2023 en PBS pH 7.4. CF3 puede variar -80.5 a -82.4 ppm según condiciones."
    },
    


    "PFNA": {
        "name": "PFNA (Perfluorononanoic acid)",
        "formula": "C9HF17O2",
        "cas": "375-95-1",
        "chain_length": 9,
        "functional_group": "COOH",
        "category": "PFCA",
        "molecular_weight": 464.08,
        "regulation_status": "Under review",
        "key_peaks": [
            {"ppm": -81.0, "type": "CF3", "relative_intensity": "strong", "source": "[3]"},
            {"ppm": -117.6, "type": "CF2-alpha", "relative_intensity": "medium", "source": "[3]"},
            {"ppm": -122.2, "type": "CF2-internal", "relative_intensity": "strong", "source": "[3]"},
            {"ppm": -123.0, "type": "CF2-internal", "relative_intensity": "strong", "source": "[3]"},
            {"ppm": -126.7, "type": "CF2-beta", "relative_intensity": "medium", "source": "[3]"}
        ],
        "peak_pattern": "Similar a PFOA pero cadena más larga",
        "diagnostic_region": (-119, -116),
        "notes": "Valores de [3] Alesio 2021 en PBS"
    },
    
    "PFBA": {
        "name": "PFBA (Perfluorobutanoic acid)",
        "formula": "C4HF7O2",
        "cas": "375-22-4",
        "chain_length": 4,
        "functional_group": "COOH",
        "category": "PFCA",
        "molecular_weight": 214.04,
        "regulation_status": "Not restricted (short chain)",
        "key_peaks": [
            {"ppm": -81.5, "type": "CF3", "relative_intensity": "very strong", "source": "[1]"},
            {"ppm": -118.4, "type": "CF2-alpha", "relative_intensity": "strong", "source": "[1]"},
            {"ppm": -127.4, "type": "CF2-beta", "relative_intensity": "medium", "source": "[1]"}
        ],
        "peak_pattern": "Cadena muy corta - 3 picos principales",
        "diagnostic_region": (-120, -117),
        "notes": "Valores de [1] Cheng 2023. Cadena corta más simple"
    },
    
    "PFPeA": {
        "name": "PFPeA (Perfluoropentanoic acid)",
        "formula": "C5HF9O2",
        "cas": "2706-90-3",
        "chain_length": 5,
        "functional_group": "COOH",
        "category": "PFCA",
        "molecular_weight": 264.05,
        "regulation_status": "Not restricted (short chain)",
        "key_peaks": [
            {"ppm": -81.3, "type": "CF3", "relative_intensity": "strong", "source": "est."},
            {"ppm": -118.0, "type": "CF2-alpha", "relative_intensity": "medium", "source": "est."},
            {"ppm": -122.5, "type": "CF2-internal", "relative_intensity": "medium", "source": "est."},
            {"ppm": -127.0, "type": "CF2-beta", "relative_intensity": "medium", "source": "est."}
        ],
        "peak_pattern": "Cadena corta",
        "diagnostic_region": (-120, -117),
        "notes": "Valores estimados por interpolación entre PFBA y PFHxA"
    },
    
    "PFHxA": {
        "name": "PFHxA (Perfluorohexanoic acid)",
        "formula": "C6HF11O2",
        "cas": "307-24-4",
        "chain_length": 6,
        "functional_group": "COOH",
        "category": "PFCA",
        "molecular_weight": 314.05,
        "regulation_status": "Not restricted (short chain)",
        "key_peaks": [
            {"ppm": -81.2, "type": "CF3", "relative_intensity": "strong", "source": "[5]"},
            {"ppm": -117.8, "type": "CF2-alpha", "relative_intensity": "medium", "source": "[5]"},
            {"ppm": -122.3, "type": "CF2-internal", "relative_intensity": "medium", "source": "[5]"},
            {"ppm": -126.8, "type": "CF2-beta", "relative_intensity": "medium", "source": "[5]"}
        ],
        "peak_pattern": "Cadena mediana",
        "diagnostic_region": (-119, -116)
    },
    
    "PFHpA": {
        "name": "PFHpA (Perfluoroheptanoic acid)",
        "formula": "C7HF13O2",
        "cas": "375-85-9",
        "chain_length": 7,
        "functional_group": "COOH",
        "category": "PFCA",
        "molecular_weight": 364.06,
        "regulation_status": "Monitored",
        "key_peaks": [
            {"ppm": -81.0, "type": "CF3", "relative_intensity": "strong", "source": "est."},
            {"ppm": -117.5, "type": "CF2-alpha", "relative_intensity": "medium", "source": "est."},
            {"ppm": -122.1, "type": "CF2-internal", "relative_intensity": "strong", "source": "est."},
            {"ppm": -126.6, "type": "CF2-beta", "relative_intensity": "medium", "source": "est."}
        ],
        "peak_pattern": "Intermedio entre PFHxA y PFOA",
        "diagnostic_region": (-119, -116),
        "notes": "Valores estimados por interpolación"
    },
    
    "PFDA": {
        "name": "PFDA (Perfluorodecanoic acid)",
        "formula": "C10HF19O2",
        "cas": "335-76-2",
        "chain_length": 10,
        "functional_group": "COOH",
        "category": "PFCA",
        "molecular_weight": 514.08,
        "regulation_status": "Monitored",
        "key_peaks": [
            {"ppm": -81.0, "type": "CF3", "relative_intensity": "strong", "source": "[5]"},
            {"ppm": -117.5, "type": "CF2-alpha", "relative_intensity": "medium", "source": "[5]"},
            {"ppm": -122.0, "type": "CF2-internal", "relative_intensity": "very strong", "source": "[5]"},
            {"ppm": -123.2, "type": "CF2-internal", "relative_intensity": "very strong", "source": "[5]"},
            {"ppm": -126.5, "type": "CF2-beta", "relative_intensity": "medium", "source": "[5]"}
        ],
        "peak_pattern": "Cadena larga - muchos CF2 internos",
        "diagnostic_region": (-119, -116)
    },
    
    "PFUnDA": {
        "name": "PFUnDA (Perfluoroundecanoic acid)",
        "formula": "C11HF21O2",
        "cas": "2058-94-8",
        "chain_length": 11,
        "functional_group": "COOH",
        "category": "PFCA",
        "molecular_weight": 564.09,
        "regulation_status": "Monitored",
        "key_peaks": [
            {"ppm": -81.0, "type": "CF3", "relative_intensity": "strong", "source": "est."},
            {"ppm": -117.5, "type": "CF2-alpha", "relative_intensity": "medium", "source": "est."},
            {"ppm": -122.0, "type": "CF2-internal", "relative_intensity": "very strong", "source": "est."}
        ],
        "peak_pattern": "Cadena muy larga",
        "diagnostic_region": (-119, -116)
    },
    
    "PFDoDA": {
        "name": "PFDoDA (Perfluorododecanoic acid)",
        "formula": "C12HF23O2",
        "cas": "307-55-1",
        "chain_length": 12,
        "functional_group": "COOH",
        "category": "PFCA",
        "molecular_weight": 614.10,
        "regulation_status": "Monitored",
        "key_peaks": [
            {"ppm": -81.0, "type": "CF3", "relative_intensity": "strong", "source": "est."},
            {"ppm": -117.5, "type": "CF2-alpha", "relative_intensity": "medium", "source": "est."},
            {"ppm": -122.0, "type": "CF2-internal", "relative_intensity": "very strong", "source": "est."}
        ],
        "peak_pattern": "Cadena muy larga",
        "diagnostic_region": (-119, -116)
    },
    
    "PFTrDA": {
        "name": "PFTrDA (Perfluorotridecanoic acid)",
        "formula": "C13HF25O2",
        "cas": "72629-94-8",
        "chain_length": 13,
        "functional_group": "COOH",
        "category": "PFCA",
        "molecular_weight": 664.10,
        "regulation_status": "Monitored",
        "key_peaks": [
            {"ppm": -81.0, "type": "CF3", "relative_intensity": "strong", "source": "est."},
            {"ppm": -117.5, "type": "CF2-alpha", "relative_intensity": "medium", "source": "est."},
            {"ppm": -122.0, "type": "CF2-internal", "relative_intensity": "very strong", "source": "est."}
        ],
        "peak_pattern": "Cadena muy larga",
        "diagnostic_region": (-119, -116)
    },
    
    "PFTeDA": {
        "name": "PFTeDA (Perfluorotetradecanoic acid)",
        "formula": "C14HF27O2",
        "cas": "376-06-7",
        "chain_length": 14,
        "functional_group": "COOH",
        "category": "PFCA",
        "molecular_weight": 714.11,
        "regulation_status": "Monitored",
        "key_peaks": [
            {"ppm": -81.0, "type": "CF3", "relative_intensity": "strong", "source": "est."},
            {"ppm": -117.5, "type": "CF2-alpha", "relative_intensity": "medium", "source": "est."},
            {"ppm": -122.0, "type": "CF2-internal", "relative_intensity": "very strong", "source": "est."}
        ],
        "peak_pattern": "Cadena muy larga",
        "diagnostic_region": (-119, -116)
    },
    
    # ========================================================================
    # PERFLUOROALKYL SULFONATES (PFSAs)
    # ========================================================================
    
    "PFOS": {
        "name": "PFOS (Perfluorooctanesulfonic acid)",
        "formula": "C8HF17O3S",
        "cas": "1763-23-1",
        "chain_length": 8,
        "functional_group": "SO3H",
        "category": "PFSA",
        "molecular_weight": 500.13,
        "regulation_status": "Restricted (Stockholm Convention)",
        "key_peaks": [
            {"ppm": -81.2, "type": "CF3", "relative_intensity": "strong", "source": "[2]"},
            {"ppm": -115.5, "type": "CF2-alpha", "relative_intensity": "medium", "source": "[3]"},
            {"ppm": -121.8, "type": "CF2-internal", "relative_intensity": "strong", "source": "[3]"},
            {"ppm": -123.0, "type": "CF2-internal", "relative_intensity": "strong", "source": "[3]"},
            {"ppm": -126.5, "type": "CF2-beta", "relative_intensity": "medium", "source": "[3]"}
        ],
        "peak_pattern": "CF3 terminal + CF2 internos + CF2-alpha SO3",
        "diagnostic_region": (-117, -114),  # CF2-alpha a SO3
        "pKa": -1.85,  # [4]
        "notes": "Valores de [2] Nickerson 2023 y [3] Alesio 2021. ~30% isómeros ramificados en productos comerciales."
    },
    
    "PFHxS": {
        "name": "PFHxS (Perfluorohexanesulfonic acid)",
        "formula": "C6HF13O3S",
        "cas": "355-46-4",
        "chain_length": 6,
        "functional_group": "SO3H",
        "category": "PFSA",
        "molecular_weight": 400.11,
        "regulation_status": "Under review",
        "key_peaks": [
            {"ppm": -81.3, "type": "CF3", "relative_intensity": "strong", "source": "[3]"},
            {"ppm": -115.3, "type": "CF2-alpha", "relative_intensity": "medium", "source": "[3]"},
            {"ppm": -122.2, "type": "CF2-internal", "relative_intensity": "strong", "source": "[3]"},
            {"ppm": -126.8, "type": "CF2-beta", "relative_intensity": "medium", "source": "[3]"}
        ],
        "peak_pattern": "Similar a PFOS pero cadena más corta",
        "diagnostic_region": (-117, -114),
        "notes": "Valores de [3] Alesio 2021. ~5% isómeros ramificados."
    },
    
    "PFBS": {
        "name": "PFBS (Perfluorobutanesulfonic acid)",
        "formula": "C4HF9O3S",
        "cas": "375-73-5",
        "chain_length": 4,
        "functional_group": "SO3H",
        "category": "PFSA",
        "molecular_weight": 300.10,
        "regulation_status": "Not restricted (short chain)",
        "key_peaks": [
            {"ppm": -81.5, "type": "CF3", "relative_intensity": "strong", "source": "[4]"},
            {"ppm": -114.8, "type": "CF2-alpha", "relative_intensity": "medium", "source": "[4]"},
            {"ppm": -123.0, "type": "CF2-beta", "relative_intensity": "medium", "source": "[4]"}
        ],
        "peak_pattern": "Cadena corta - menos picos",
        "diagnostic_region": (-117, -114),
        "pKa": -1.85,  # [4]
        "notes": "Valores de [4] Torres-Beltrán 2025"
    },
    
    "PFPrS": {
        "name": "PFPrS (Perfluoropropanesulfonic acid)",
        "formula": "C3HF7O3S",
        "cas": "423-41-6",
        "chain_length": 3,
        "functional_group": "SO3H",
        "category": "PFSA",
        "molecular_weight": 250.09,
        "regulation_status": "Short chain",
        "key_peaks": [
            {"ppm": -81.7, "type": "CF3", "relative_intensity": "very strong", "source": "est."},
            {"ppm": -114.5, "type": "CF2-alpha", "relative_intensity": "medium", "source": "est."}
        ],
        "peak_pattern": "Muy corta - solo CF3 y CF2",
        "diagnostic_region": (-117, -114)
    },
    
    "PFDS": {
        "name": "PFDS (Perfluorodecanesulfonic acid)",
        "formula": "C10HF21O3S",
        "cas": "335-77-3",
        "chain_length": 10,
        "functional_group": "SO3H",
        "category": "PFSA",
        "molecular_weight": 600.14,
        "regulation_status": "Monitored",
        "key_peaks": [
            {"ppm": -81.2, "type": "CF3", "relative_intensity": "strong", "source": "est."},
            {"ppm": -115.4, "type": "CF2-alpha", "relative_intensity": "medium", "source": "est."},
            {"ppm": -122.0, "type": "CF2-internal", "relative_intensity": "very strong", "source": "est."}
        ],
        "peak_pattern": "Sulfonato de cadena larga",
        "diagnostic_region": (-117, -114)
    },
    
    # ========================================================================
    # FLUOROTELOMERS
    # ========================================================================
    
    "6-2_FTOH": {
        "name": "6:2 FTOH (6:2 Fluorotelomer alcohol)",
        "formula": "C8H5F13O",
        "cas": "647-42-7",
        "chain_length": 6,
        "functional_group": "CH2CH2OH",
        "category": "Fluorotelomer",
        "molecular_weight": 364.11,
        "regulation_status": "Precursor compound",
        "key_peaks": [
            {"ppm": -81.2, "type": "CF3", "relative_intensity": "strong", "source": "[5]"},
            {"ppm": -122.0, "type": "CF2-internal", "relative_intensity": "strong", "source": "[5]"},
            {"ppm": -126.2, "type": "CF2-CH2", "relative_intensity": "weak", "source": "[5]"}
        ],
        "peak_pattern": "CF3 + CF2 internos + pico característico CF2-CH2",
        "diagnostic_region": (-128, -125)  # CF2-CH2
    },
    
    "8-2_FTOH": {
        "name": "8:2 FTOH (8:2 Fluorotelomer alcohol)",
        "formula": "C10H5F17O",
        "cas": "678-39-7",
        "chain_length": 8,
        "functional_group": "CH2CH2OH",
        "category": "Fluorotelomer",
        "molecular_weight": 464.12,
        "regulation_status": "Precursor compound",
        "key_peaks": [
            {"ppm": -81.1, "type": "CF3", "relative_intensity": "strong", "source": "[5]"},
            {"ppm": -121.8, "type": "CF2-internal", "relative_intensity": "strong", "source": "[5]"},
            {"ppm": -123.0, "type": "CF2-internal", "relative_intensity": "strong", "source": "[5]"},
            {"ppm": -126.0, "type": "CF2-CH2", "relative_intensity": "weak", "source": "[5]"}
        ],
        "peak_pattern": "Similar a 6:2 FTOH pero cadena más larga",
        "diagnostic_region": (-128, -125)
    },
    
    "6-2_FTCA": {
        "name": "6:2 FTCA (6:2 Fluorotelomer carboxylic acid)",
        "formula": "C8H3F13O2",
        "cas": "53826-13-4",
        "chain_length": 6,
        "functional_group": "CH2COOH",
        "category": "Fluorotelomer",
        "molecular_weight": 378.09,
        "regulation_status": "Degradation product",
        "key_peaks": [
            {"ppm": -81.2, "type": "CF3", "relative_intensity": "strong", "source": "est."},
            {"ppm": -122.0, "type": "CF2-internal", "relative_intensity": "strong", "source": "est."},
            {"ppm": -126.5, "type": "CF2-CH2", "relative_intensity": "weak", "source": "est."}
        ],
        "peak_pattern": "Similar a FTOH pero con CH2COOH",
        "diagnostic_region": (-128, -125)
    },
    
    "8-2_FTCA": {
        "name": "8:2 FTCA (8:2 Fluorotelomer carboxylic acid)",
        "formula": "C10H3F17O2",
        "cas": "27854-31-5",
        "chain_length": 8,
        "functional_group": "CH2COOH",
        "category": "Fluorotelomer",
        "molecular_weight": 478.10,
        "regulation_status": "Degradation product",
        "key_peaks": [
            {"ppm": -81.1, "type": "CF3", "relative_intensity": "strong", "source": "est."},
            {"ppm": -121.9, "type": "CF2-internal", "relative_intensity": "strong", "source": "est."},
            {"ppm": -123.2, "type": "CF2-internal", "relative_intensity": "strong", "source": "est."},
            {"ppm": -126.3, "type": "CF2-CH2", "relative_intensity": "weak", "source": "est."}
        ],
        "peak_pattern": "Similar a 8:2 FTOH pero con COOH",
        "diagnostic_region": (-128, -125)
    },
    
    # ========================================================================
    # NUEVA GENERACIÓN (GenX, ADONA)
    # ========================================================================
    
    "GenX": {
        "name": "GenX (HFPO-DA, Hexafluoropropylene oxide dimer acid)",
        "formula": "C6HF11O3",
        "cas": "13252-13-6",
        "chain_length": 6,
        "functional_group": "COOH",
        "category": "Polyether",
        "molecular_weight": 330.05,
        "regulation_status": "Emerging concern (replacement)",
        "key_peaks": [
            {"ppm": -82.0, "type": "CF3", "relative_intensity": "strong", "source": "[4]"},
            {"ppm": -84.5, "type": "CF3-branch", "relative_intensity": "medium", "source": "[4]"},
            {"ppm": -118.0, "type": "CF2-alpha", "relative_intensity": "medium", "source": "[4]"},
            {"ppm": -130.0, "type": "CF2-ether", "relative_intensity": "weak", "source": "est."},
            {"ppm": -144.0, "type": "CF-ether", "relative_intensity": "weak", "source": "est."}
        ],
        "peak_pattern": "CF3 ramificado + CF-O característico",
        "diagnostic_region": (-150, -140),  # CF-ether
        "pKa": -0.20,  # [4]
        "notes": "Valores parciales de [4] Torres-Beltrán 2025. Estructura ramificada con éteres"
    },
    
    "ADONA": {
        "name": "ADONA (4,8-dioxa-3H-perfluorononanoic acid)",
        "formula": "C7HF13O4",
        "cas": "919005-14-4",
        "chain_length": 7,
        "functional_group": "COOH",
        "category": "Polyether",
        "molecular_weight": 378.06,
        "regulation_status": "Alternative compound",
        "key_peaks": [
            {"ppm": -82.5, "type": "CF3", "relative_intensity": "strong", "source": "est."},
            {"ppm": -87.0, "type": "CF2-O", "relative_intensity": "medium", "source": "est."},
            {"ppm": -118.2, "type": "CF2-alpha", "relative_intensity": "medium", "source": "est."},
            {"ppm": -130.5, "type": "CF2-ether", "relative_intensity": "weak", "source": "est."},
            {"ppm": -144.5, "type": "CF-ether", "relative_intensity": "weak", "source": "est."}
        ],
        "peak_pattern": "Múltiples grupos éter",
        "diagnostic_region": (-150, -140)
    },
    
    # ========================================================================
    # DERIVADOS Y PRECURSORES
    # ========================================================================
    
    "PFOSA": {
        "name": "PFOSA (Perfluorooctane sulfonamide)",
        "formula": "C8H2F17NO2S",
        "cas": "754-91-6",
        "chain_length": 8,
        "functional_group": "SO2NH2",
        "category": "PFSA-derivative",
        "molecular_weight": 499.15,
        "regulation_status": "Precursor to PFOS",
        "key_peaks": [
            {"ppm": -81.2, "type": "CF3", "relative_intensity": "strong", "source": "est."},
            {"ppm": -115.7, "type": "CF2-alpha", "relative_intensity": "medium", "source": "est."},
            {"ppm": -122.0, "type": "CF2-internal", "relative_intensity": "strong", "source": "est."}
        ],
        "peak_pattern": "Similar a PFOS pero con SO2NH2",
        "diagnostic_region": (-117, -114)
    },
    
    "N-EtFOSA": {
        "name": "N-EtFOSA (N-Ethyl perfluorooctane sulfonamide)",
        "formula": "C10H6F17NO2S",
        "cas": "4151-50-2",
        "chain_length": 8,
        "functional_group": "SO2NH(C2H5)",
        "category": "PFSA-derivative",
        "molecular_weight": 527.20,
        "regulation_status": "Precursor compound",
        "key_peaks": [
            {"ppm": -81.2, "type": "CF3", "relative_intensity": "strong", "source": "est."},
            {"ppm": -115.8, "type": "CF2-alpha", "relative_intensity": "medium", "source": "est."},
            {"ppm": -122.1, "type": "CF2-internal", "relative_intensity": "strong", "source": "est."}
        ],
        "peak_pattern": "Derivado N-alquilado",
        "diagnostic_region": (-117, -114)
    },
    
    "N-MeFOSA": {
        "name": "N-MeFOSA (N-Methyl perfluorooctane sulfonamide)",
        "formula": "C9H4F17NO2S",
        "cas": "31506-32-8",
        "chain_length": 8,
        "functional_group": "SO2NH(CH3)",
        "category": "PFSA-derivative",
        "molecular_weight": 513.17,
        "regulation_status": "Precursor compound",
        "key_peaks": [
            {"ppm": -81.2, "type": "CF3", "relative_intensity": "strong", "source": "est."},
            {"ppm": -115.8, "type": "CF2-alpha", "relative_intensity": "medium", "source": "est."},
            {"ppm": -122.1, "type": "CF2-internal", "relative_intensity": "strong", "source": "est."}
        ],
        "peak_pattern": "Derivado N-metilado",
        "diagnostic_region": (-117, -114)
    },
    
    "PFECHS": {
        "name": "PFECHS (Perfluoroethylcyclohexane sulfonate)",
        "formula": "C8HF15O3S",
        "cas": "67584-42-3",
        "chain_length": 8,
        "functional_group": "SO3H",
        "category": "PFSA-cyclic",
        "molecular_weight": 462.12,
        "regulation_status": "Alternative compound",
        "key_peaks": [
            {"ppm": -81.3, "type": "CF3", "relative_intensity": "strong", "source": "est."},
            {"ppm": -115.0, "type": "CF2-alpha", "relative_intensity": "medium", "source": "est."},
            {"ppm": -118.5, "type": "CF-cyclic", "relative_intensity": "weak", "source": "est."}
        ],
        "peak_pattern": "Estructura cíclica",
        "diagnostic_region": (-120, -115)
    },
    
    "Iso-PFOS": {
        "name": "Branched PFOS isomers",
        "formula": "C8HF17O3S",
        "cas": "Various",
        "chain_length": 8,
        "functional_group": "SO3H",
        "category": "PFSA-branched",
        "molecular_weight": 500.13,
        "regulation_status": "Restricted (as PFOS)",
        "key_peaks": [
            {"ppm": -75.5, "type": "CF3-branch", "relative_intensity": "medium", "source": "[3]"},
            {"ppm": -81.2, "type": "CF3", "relative_intensity": "strong", "source": "[3]"},
            {"ppm": -115.5, "type": "CF2-alpha", "relative_intensity": "medium", "source": "[3]"},
            {"ppm": -122.0, "type": "CF2-internal", "relative_intensity": "strong", "source": "[3]"}
        ],
        "peak_pattern": "CF3 adicional por ramificación",
        "diagnostic_region": (-78, -70),  # CF3-branch
        "notes": "~30% de PFOS comercial es ramificado [3]"
    },
}

# ============================================================================
# CATEGORÍAS Y FUNCIONES HELPER (sin cambios)
# ============================================================================

PFAS_CATEGORIES = {
    "PFCA": {
        "name": "Perfluoroalkyl Carboxylic Acids",
        "description": "PFAS con grupo funcional ácido carboxílico (-COOH)",
        "functional_group": "COOH",
        "compounds": ["PFOA", "PFNA", "PFHxA", "PFBA", "PFPeA", "PFHpA", "PFDA", "PFUnDA", "PFDoDA", "PFTrDA", "PFTeDA"]
    },
    "PFSA": {
        "name": "Perfluoroalkyl Sulfonic Acids",
        "description": "PFAS con grupo funcional ácido sulfónico (-SO3H)",
        "functional_group": "SO3H",
        "compounds": ["PFOS", "PFHxS", "PFBS", "PFDS", "PFPrS"]
    },
    "Fluorotelomer": {
        "name": "Fluorotelomer alcohols and acids",
        "description": "Fluorotelómeros (precursores de PFAS)",
        "functional_group": "CH2CH2OH o CH2COOH",
        "compounds": ["8-2_FTOH", "6-2_FTOH", "8-2_FTCA", "6-2_FTCA"]
    },
    "Polyether": {
        "name": "Polyether PFAS (New Generation)",
        "description": "PFAS de nueva generación con grupos éter",
        "functional_group": "Ether linkages",
        "compounds": ["GenX", "ADONA"]
    },
    "PFSA-branched": {
        "name": "Branched PFSA",
        "description": "PFSA con estructura ramificada",
        "functional_group": "SO3H",
        "compounds": ["Iso-PFOS"]
    },
    "PFSA-cyclic": {
        "name": "Cyclic PFSA",
        "description": "PFSA con estructura cíclica",
        "functional_group": "SO3H",
        "compounds": ["PFECHS"]
    },
    "PFSA-derivative": {
        "name": "PFSA Derivatives",
        "description": "Derivados de PFSA (sulfonamidas, etc.)",
        "functional_group": "SO2NHR",
        "compounds": ["PFOSA", "N-EtFOSA", "N-MeFOSA"]
    }
}

FUNCTIONAL_GROUP_SIGNATURES = {
    "COOH": {
        "name": "Carboxylic Acid",
        "region": (-119, -116),
        "diagnostic_shift": -117.4,
        "description": "CF2 adyacente a grupo carboxilo",
        "source": "[1] Cheng 2023"
    },
    "SO3H": {
        "name": "Sulfonic Acid",
        "region": (-117, -114),
        "diagnostic_shift": -115.5,
        "description": "CF2 adyacente a grupo sulfonato",
        "source": "[2] Nickerson 2023, [3] Alesio 2021"
    },
    "CH2CH2OH": {
        "name": "Fluorotelomer Alcohol",
        "region": (-128, -125),
        "diagnostic_shift": -126.2,
        "description": "CF2-CH2 característico de fluorotelómeros",
        "source": "[5] Sharifan 2021"
    },
    "Ether": {
        "name": "Ether Linkage",
        "region": (-150, -140),
        "diagnostic_shift": -144.0,
        "description": "CF en enlace éter (PFAS de nueva generación)",
        "source": "Estimated"
    }
}

# Funciones helper (sin cambios del archivo original)
def get_pfas_by_category(category: str) -> list:
    if category in PFAS_CATEGORIES:
        return PFAS_CATEGORIES[category]["compounds"]
    return []

def get_pfas_by_chain_length(min_length: int = None, max_length: int = None) -> list:
    results = []
    for pfas_id, data in PFAS_DATABASE.items():
        chain_length = data.get("chain_length", 0)
        if min_length is not None and chain_length < min_length:
            continue
        if max_length is not None and chain_length > max_length:
            continue
        results.append((pfas_id, data["name"], chain_length))
    return sorted(results, key=lambda x: x[2])

def get_pfas_by_functional_group(functional_group: str) -> list:
    results = []
    for pfas_id, data in PFAS_DATABASE.items():
        if data.get("functional_group") == functional_group:
            results.append(pfas_id)
    return results

def get_regulated_pfas() -> list:
    results = []
    for pfas_id, data in PFAS_DATABASE.items():
        regulation = data.get("regulation_status", "")
        if "Restricted" in regulation or "Stockholm" in regulation:
            results.append((pfas_id, data["name"], regulation))
    return results

def get_pfas_info(pfas_id: str) -> dict:
    return PFAS_DATABASE.get(pfas_id, {})

def search_pfas_by_cas(cas_number: str) -> dict:
    for pfas_id, data in PFAS_DATABASE.items():
        if data.get("cas") == cas_number:
            return {**data, "id": pfas_id}
    return None

def get_database_stats() -> dict:
    total_compounds = len(PFAS_DATABASE)
    categories = {}
    chain_lengths = {}
    functional_groups = {}
    
    for pfas_id, data in PFAS_DATABASE.items():
        category = data.get("category", "Unknown")
        categories[category] = categories.get(category, 0) + 1
        chain = data.get("chain_length", 0)
        chain_lengths[chain] = chain_lengths.get(chain, 0) + 1
        fg = data.get("functional_group", "Unknown")
        functional_groups[fg] = functional_groups.get(fg, 0) + 1
    
    return {
        "total_compounds": total_compounds,
        "by_category": categories,
        "by_chain_length": chain_lengths,
        "by_functional_group": functional_groups
    }

# Visualizaciones (mantener como está)
MOLECULE_VISUALIZATIONS = {
    "375-22-4": {"name": "PFBA", "file_3d": "pfba.sdf", "image_2d": "assets/molecules/pfba_2d.png"},
    "2706-90-3": {"name": "PFPeA", "file_3d": "pfpea.sdf", "image_2d": "assets/molecules/pfpea_2d.png"},
    "307-24-4": {"name": "PFHxA", "file_3d": "pfhxa.sdf", "image_2d": "assets/molecules/pfhxa_2d.png"},
    "375-85-9": {"name": "PFHpA", "file_3d": "pfhpa.sdf", "image_2d": "assets/molecules/pfhpa_2d.png"},
    "335-67-1": {"name": "PFOA", "file_3d": "pfoa.sdf", "image_2d": "assets/molecules/pfoa_2d.png"},
    "375-95-1": {"name": "PFNA", "file_3d": "pfna.sdf", "image_2d": "assets/molecules/pfna_2d.png"},
    "335-76-2": {"name": "PFDA", "file_3d": "pfda.sdf", "image_2d": "assets/molecules/pfda_2d.png"},
    "2058-94-8": {"name": "PFUnDA", "file_3d": "pfunda.sdf", "image_2d": "assets/molecules/pfunda_2d.png"},
    "307-55-1": {"name": "PFDoDA", "file_3d": "pfdoda.sdf", "image_2d": "assets/molecules/pfdoda_2d.png"},
    "72629-94-8": {"name": "PFTrDA", "file_3d": "pftrda.sdf", "image_2d": "assets/molecules/pftrda_2d.png"},
    "376-06-7": {"name": "PFTeDA", "file_3d": "pfteda.sdf", "image_2d": "assets/molecules/pfteda_2d.png"},
    "423-41-6": {"name": "PFPrS", "file_3d": "pfprs.sdf", "image_2d": "assets/molecules/pfprs_2d.png"},
    "375-73-5": {"name": "PFBS", "file_3d": "pfbs.sdf", "image_2d": "assets/molecules/pfbs_2d.png"},
    "355-46-4": {"name": "PFHxS", "file_3d": "pfhxs.sdf", "image_2d": "assets/molecules/pfhxs_2d.png"},
    "1763-23-1": {"name": "PFOS", "file_3d": "pfos.sdf", "image_2d": "assets/molecules/pfos_2d.png"},
    "335-77-3": {"name": "PFDS", "file_3d": "pfds.sdf", "image_2d": "assets/molecules/pfds_2d.png"},
    "13252-13-6": {"name": "GenX", "file_3d": "genx.sdf", "image_2d": "assets/molecules/genx_2d.png"},
    "919005-14-4": {"name": "ADONA", "file_3d": "adona.sdf", "image_2d": "assets/molecules/adona_2d.png"},
    "647-42-7": {"name": "6:2 FTOH", "file_3d": "6-2_ftoh.sdf", "image_2d": "assets/molecules/6-2_ftoh_2d.png"},
    "678-39-7": {"name": "8:2 FTOH", "file_3d": "8-2_ftoh.sdf", "image_2d": "assets/molecules/8-2_ftoh_2d.png"},
    "53826-13-4": {"name": "6:2 FTCA", "file_3d": "6-2_ftca.sdf", "image_2d": "assets/molecules/6-2_ftca_2d.png"},
    "27854-31-5": {"name": "8:2 FTCA", "file_3d": "8-2_ftca.sdf", "image_2d": "assets/molecules/8-2_ftca_2d.png"},
    "67584-42-3": {"name": "PFECHS", "file_3d": "pfechs.sdf", "image_2d": "assets/molecules/pfechs_2d.png"},
    "754-91-6": {"name": "PFOSA", "file_3d": "pfosa.sdf", "image_2d": "assets/molecules/pfosa_2d.png"},
    "4151-50-2": {"name": "N-EtFOSA", "file_3d": "n-etfosa.sdf", "image_2d": "assets/molecules/n-etfosa_2d.png"},
    "31506-32-8": {"name": "N-MeFOSA", "file_3d": "n-mefosa.sdf", "image_2d": "assets/molecules/n-mefosa_2d.png"},
    "GENERIC_PFAS_UNKNOWN": {"name": "PFAS Desconocido", "file_3d": "pfas_unknown.sdf", "image_2d": "assets/molecules/pfas_unknown_2d.png"}
}

def get_molecule_visualization(cas_number: str) -> dict:
    if not cas_number or cas_number.lower() in ['various', 'variable', 'generic', 'unknown']:
        return MOLECULE_VISUALIZATIONS.get("GENERIC_PFAS_UNKNOWN", {
            "name": None,
            "file_3d": None,
            "image_2d": None
        })
    return MOLECULE_VISUALIZATIONS.get(cas_number, {
        "name": None,
        "file_3d": None,
        "image_2d": None
    })

def list_available_visualizations() -> list:
    return [
        {"cas": cas, **data}
        for cas, data in MOLECULE_VISUALIZATIONS.items()
    ]

# ============================================================================
# REFERENCIAS BIBLIOGRÁFICAS
# ============================================================================

REFERENCES = """
[1] Cheng, Y., Peters, J.L., Sadrerafi, K., Vikesland, P.J. (2023)
    "Using 19F NMR to Investigate Cationic Carbon Dot Association with PFAS"
    ACS Nanoscience Au, 3(6), 473-484
    DOI: 10.1021/acsnanoscienceau.3c00022
    
[2] Nickerson, A., Maizel, A.C., Kulkarni, P.R., Adamson, D.T., Kornuc, J.J., Higgins, C.P. (2023)
    "Quantitation of Total PFAS Including Trifluoroacetic Acid with 19F NMR"
    Environmental Science & Technology, 57(42), 15995-16003
    PMC10601338
    
[3] Alesio, J.L., Slitt, A., Bothun, G.D. (2021)
    "Dominant Entropic Binding of PFAS to Albumin Protein Revealed by 19F NMR"
    Environmental Science & Technology, 55(18), 12436-12444
    PMC8479757
    
[4] Torres-Beltrán, M., et al. (2025)
    "Experimental Determination of pKa for 10 PFAS by 19F-NMR"
    Environmental Science & Technology Letters, 12(8)
    DOI: 10.1021/acs.estlett.5c00688
    
[5] Sharifan, H., Bagheri, M., Wang, D., Burken, J.G., Higgins, C.P., Liang, Y., Liu, J., Schaefer, C.E., Blotevogel, J. (2021)
    "Total and class-specific analysis of PFAS using NMR spectroscopy"
    Current Opinion in Environmental Science & Health, 21, 100252
"""

if __name__ == "__main__":
    print("="*80)
    print("BASE DE DATOS CIENTÍFICA DE PFAS - 19F NMR")
    print("="*80)
    
    stats = get_database_stats()
    print(f"\nTotal de compuestos: {stats['total_compounds']}")
    
    print("\nCompuestos por categoría:")
    for cat, count in stats['by_category'].items():
        print(f"  - {cat}: {count}")
    
    print("\nEjemplo - PFOA (valores científicos):")
    pfoa = get_pfas_info("PFOA")
    print(f"  Nombre: {pfoa.get('name')}")
    print(f"  Picos clave:")
    for peak in pfoa.get('key_peaks', []):
        print(f"    {peak['ppm']:7.2f} ppm - {peak['type']:15s} - Fuente: {peak.get('source', 'N/A')}")
    
    print("\n" + "="*80)
    print("REFERENCIAS:")
    print("="*80)
    print(REFERENCES)