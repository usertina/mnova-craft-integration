"""
Base de datos completa de PFAS para detección por RMN F-19
Incluye 30+ compuestos con desplazamientos químicos característicos
"""

# Base de datos principal de PFAS
PFAS_DATABASE = {
    # ============================================================================
    # PERFLUOROALCANOS SULFONATOS (PFSAs) - Ácidos sulfónicos
    # ============================================================================
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
            {"ppm": -81.2, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -115.5, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -122.5, "type": "CF2-internal", "relative_intensity": "strong"},
            {"ppm": -123.8, "type": "CF2-internal", "relative_intensity": "strong"},
            {"ppm": -127.2, "type": "CF2-beta", "relative_intensity": "medium"}
        ],
        "peak_pattern": "CF3 terminal + CF2 internos + CF2-alpha SO3",
        "diagnostic_region": (-117, -113)  # CF2-alpha a SO3
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
            {"ppm": -81.4, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -115.2, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -123.0, "type": "CF2-internal", "relative_intensity": "strong"},
            {"ppm": -127.5, "type": "CF2-beta", "relative_intensity": "medium"}
        ],
        "peak_pattern": "Similar a PFOS pero cadena más corta",
        "diagnostic_region": (-117, -113)
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
            {"ppm": -81.1, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -114.8, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -122.8, "type": "CF2-beta", "relative_intensity": "medium"}
        ],
        "peak_pattern": "Cadena corta - menos picos",
        "diagnostic_region": (-117, -113)
    },
    
    # ============================================================================
    # PERFLUOROALCANOS CARBOXILATOS (PFCAs) - Ácidos carboxílicos
    # ============================================================================
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
            {"ppm": -81.6, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -119.2, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -122.3, "type": "CF2-internal", "relative_intensity": "strong"},
            {"ppm": -123.5, "type": "CF2-internal", "relative_intensity": "strong"},
            {"ppm": -126.8, "type": "CF2-beta", "relative_intensity": "medium"}
        ],
        "peak_pattern": "CF3 terminal + CF2 internos + CF2-alpha COOH",
        "diagnostic_region": (-120, -117)  # CF2-alpha a COOH
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
            {"ppm": -81.5, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -119.0, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -122.4, "type": "CF2-internal", "relative_intensity": "strong"},
            {"ppm": -123.7, "type": "CF2-internal", "relative_intensity": "strong"},
            {"ppm": -126.9, "type": "CF2-beta", "relative_intensity": "medium"}
        ],
        "peak_pattern": "Similar a PFOA pero con cadena más larga",
        "diagnostic_region": (-120, -117)
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
            {"ppm": -81.7, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -119.5, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -122.6, "type": "CF2-internal", "relative_intensity": "medium"},
            {"ppm": -127.1, "type": "CF2-beta", "relative_intensity": "medium"}
        ],
        "peak_pattern": "Cadena corta",
        "diagnostic_region": (-120, -117)
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
            {"ppm": -81.8, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -119.8, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -127.3, "type": "CF2-beta", "relative_intensity": "weak"}
        ],
        "peak_pattern": "Muy corta - pocos picos",
        "diagnostic_region": (-120, -117)
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
            {"ppm": -81.7, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -119.6, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -122.7, "type": "CF2-internal", "relative_intensity": "medium"},
            {"ppm": -127.2, "type": "CF2-beta", "relative_intensity": "medium"}
        ],
        "peak_pattern": "Cadena corta",
        "diagnostic_region": (-120, -117)
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
            {"ppm": -81.6, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -119.3, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -122.5, "type": "CF2-internal", "relative_intensity": "strong"},
            {"ppm": -126.9, "type": "CF2-beta", "relative_intensity": "medium"}
        ],
        "peak_pattern": "Intermedia entre PFHxA y PFOA",
        "diagnostic_region": (-120, -117)
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
            {"ppm": -81.5, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -119.1, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -122.2, "type": "CF2-internal", "relative_intensity": "very strong"},
            {"ppm": -123.6, "type": "CF2-internal", "relative_intensity": "very strong"},
            {"ppm": -126.7, "type": "CF2-beta", "relative_intensity": "medium"}
        ],
        "peak_pattern": "Cadena larga - muchos CF2 internos",
        "diagnostic_region": (-120, -117)
    },
    
    # ============================================================================
    # FLUOROTELÓMEROS (FTOHs, FTCAs, FTSAs)
    # ============================================================================
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
            {"ppm": -81.3, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -122.0, "type": "CF2-internal", "relative_intensity": "strong"},
            {"ppm": -123.5, "type": "CF2-internal", "relative_intensity": "strong"},
            {"ppm": -126.5, "type": "CF2-CH2", "relative_intensity": "weak"}
        ],
        "peak_pattern": "CF3 + CF2 internos + pico característico CF2-CH2",
        "diagnostic_region": (-128, -125)  # CF2-CH2
    },
    
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
            {"ppm": -81.4, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -122.2, "type": "CF2-internal", "relative_intensity": "strong"},
            {"ppm": -126.7, "type": "CF2-CH2", "relative_intensity": "weak"}
        ],
        "peak_pattern": "Similar a 8:2 FTOH pero cadena más corta",
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
            {"ppm": -81.5, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -122.3, "type": "CF2-internal", "relative_intensity": "strong"},
            {"ppm": -123.8, "type": "CF2-internal", "relative_intensity": "strong"},
            {"ppm": -127.0, "type": "CF2-CH2", "relative_intensity": "weak"}
        ],
        "peak_pattern": "Similar a FTOH pero con CH2COOH",
        "diagnostic_region": (-128, -125)
    },
    
    # ============================================================================
    # POLIÉTERES (GenX, ADONA, etc.) - Nueva generación
    # ============================================================================
    "GenX": {
        "name": "GenX (HFPO-DA, Hexafluoropropylene oxide dimer acid)",
        "formula": "C6HF11O3",
        "cas": "13252-13-6",
        "chain_length": 6,
        "functional_group": "COOH",
        "category": "Polyether",
        "molecular_weight": 330.05,
        "regulation_status": "Emerging concern (GenX replacement)",
        "key_peaks": [
            {"ppm": -82.5, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -85.2, "type": "CF3-branch", "relative_intensity": "medium"},
            {"ppm": -118.5, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -130.5, "type": "CF2-ether", "relative_intensity": "weak"},
            {"ppm": -144.5, "type": "CF-ether", "relative_intensity": "weak"}
        ],
        "peak_pattern": "CF3 ramificado + CF-O característico",
        "diagnostic_region": (-150, -140)  # CF-ether
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
            {"ppm": -83.0, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -87.5, "type": "CF2-O", "relative_intensity": "medium"},
            {"ppm": -118.8, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -131.0, "type": "CF2-ether", "relative_intensity": "weak"},
            {"ppm": -145.0, "type": "CF-ether", "relative_intensity": "weak"}
        ],
        "peak_pattern": "Múltiples grupos éter",
        "diagnostic_region": (-150, -140)
    },
    
    # ============================================================================
    # PFAS RAMIFICADOS
    # ============================================================================
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
            {"ppm": -75.5, "type": "CF3-branch", "relative_intensity": "medium"},
            {"ppm": -81.0, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -115.3, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -122.8, "type": "CF2-internal", "relative_intensity": "strong"}
        ],
        "peak_pattern": "CF3 adicional por ramificación",
        "diagnostic_region": (-78, -70)  # CF3-branch
    },
    
    # ============================================================================
    # COMPUESTOS ADICIONALES (cadenas largas y cortas)
    # ============================================================================
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
            {"ppm": -81.4, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -119.0, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -122.1, "type": "CF2-internal", "relative_intensity": "very strong"}
        ],
        "peak_pattern": "Cadena muy larga",
        "diagnostic_region": (-120, -117)
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
            {"ppm": -81.4, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -119.0, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -122.0, "type": "CF2-internal", "relative_intensity": "very strong"}
        ],
        "peak_pattern": "Cadena muy larga",
        "diagnostic_region": (-120, -117)
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
            {"ppm": -81.3, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -119.0, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -121.9, "type": "CF2-internal", "relative_intensity": "very strong"}
        ],
        "peak_pattern": "Cadena muy larga",
        "diagnostic_region": (-120, -117)
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
            {"ppm": -81.3, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -118.9, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -121.9, "type": "CF2-internal", "relative_intensity": "very strong"}
        ],
        "peak_pattern": "Cadena muy larga",
        "diagnostic_region": (-120, -117)
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
            {"ppm": -81.1, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -115.4, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -122.3, "type": "CF2-internal", "relative_intensity": "very strong"}
        ],
        "peak_pattern": "Sulfonato de cadena larga",
        "diagnostic_region": (-117, -113)
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
            {"ppm": -81.0, "type": "CF3", "relative_intensity": "very strong"},
            {"ppm": -114.5, "type": "CF2-alpha", "relative_intensity": "medium"}
        ],
        "peak_pattern": "Muy corta - solo CF3 y CF2",
        "diagnostic_region": (-117, -113)
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
            {"ppm": -81.5, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -115.0, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -118.5, "type": "CF-cyclic", "relative_intensity": "weak"}
        ],
        "peak_pattern": "Estructura cíclica",
        "diagnostic_region": (-120, -115)
    },
    
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
            {"ppm": -81.3, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -115.8, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -122.6, "type": "CF2-internal", "relative_intensity": "strong"}
        ],
        "peak_pattern": "Similar a PFOS pero con SO2NH2",
        "diagnostic_region": (-117, -113)
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
            {"ppm": -81.2, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -115.9, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -122.7, "type": "CF2-internal", "relative_intensity": "strong"}
        ],
        "peak_pattern": "Derivado N-alquilado",
        "diagnostic_region": (-117, -113)
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
            {"ppm": -81.2, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -115.9, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -122.7, "type": "CF2-internal", "relative_intensity": "strong"}
        ],
        "peak_pattern": "Derivado N-metilado",
        "diagnostic_region": (-117, -113)
    },
    
    "FOSA": {
        "name": "FOSA (Perfluorooctane sulfonamide)",
        "formula": "C8H2F17NO2S",
        "cas": "754-91-6",
        "chain_length": 8,
        "functional_group": "SO2NH2",
        "category": "PFSA-derivative",
        "molecular_weight": 499.15,
        "regulation_status": "Precursor to PFOS",
        "key_peaks": [
            {"ppm": -81.3, "type": "CF3", "relative_intensity": "strong"},
            {"ppm": -115.8, "type": "CF2-alpha", "relative_intensity": "medium"},
            {"ppm": -122.6, "type": "CF2-internal", "relative_intensity": "strong"}
        ],
        "peak_pattern": "Sulfonamida",
        "diagnostic_region": (-117, -113)
    },
}

# ============================================================================
# CATEGORÍAS DE PFAS
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
        "compounds": ["8-2_FTOH", "6-2_FTOH", "8-2_FTCA"]
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
        "compounds": ["PFOSA", "N-EtFOSA", "N-MeFOSA", "FOSA"]
    }
}

# ============================================================================
# FIRMAS DE GRUPOS FUNCIONALES
# ============================================================================
FUNCTIONAL_GROUP_SIGNATURES = {
    "COOH": {
        "name": "Carboxylic Acid",
        "cf2_alpha_range": (-120, -117),
        "diagnostic_shift": -119.0,
        "description": "CF2 adyacente a grupo carboxilo"
    },
    "SO3H": {
        "name": "Sulfonic Acid",
        "cf2_alpha_range": (-117, -113),
        "diagnostic_shift": -115.5,
        "description": "CF2 adyacente a grupo sulfonato"
    },
    "CH2CH2OH": {
        "name": "Fluorotelomer Alcohol",
        "cf2_ch2_range": (-128, -125),
        "diagnostic_shift": -126.5,
        "description": "CF2-CH2 característico de fluorotelómeros"
    },
    "Ether": {
        "name": "Ether Linkage",
        "cf_ether_range": (-150, -140),
        "diagnostic_shift": -144.5,
        "description": "CF en enlace éter (PFAS de nueva generación)"
    }
}

# ============================================================================
# FUNCIONES HELPER
# ============================================================================

def get_pfas_by_category(category: str) -> list:
    """
    Obtiene lista de compuestos PFAS por categoría.
    
    Args:
        category: Nombre de la categoría (ej. "PFCA", "PFSA")
    
    Returns:
        Lista de IDs de compuestos en esa categoría
    """
    if category in PFAS_CATEGORIES:
        return PFAS_CATEGORIES[category]["compounds"]
    return []

def get_pfas_by_chain_length(min_length: int = None, max_length: int = None) -> list:
    """
    Obtiene compuestos PFAS filtrados por longitud de cadena.
    
    Args:
        min_length: Longitud mínima de cadena (número de carbonos)
        max_length: Longitud máxima de cadena
    
    Returns:
        Lista de tuplas (id, nombre, chain_length)
    """
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
    """
    Obtiene compuestos PFAS por grupo funcional.
    
    Args:
        functional_group: Grupo funcional (ej. "COOH", "SO3H")
    
    Returns:
        Lista de IDs de compuestos con ese grupo funcional
    """
    results = []
    for pfas_id, data in PFAS_DATABASE.items():
        if data.get("functional_group") == functional_group:
            results.append(pfas_id)
    return results

def get_regulated_pfas() -> list:
    """
    Obtiene lista de PFAS regulados.
    
    Returns:
        Lista de tuplas (id, nombre, regulación)
    """
    results = []
    for pfas_id, data in PFAS_DATABASE.items():
        regulation = data.get("regulation_status", "")
        if "Restricted" in regulation or "Stockholm" in regulation:
            results.append((pfas_id, data["name"], regulation))
    return results

def get_pfas_info(pfas_id: str) -> dict:
    """
    Obtiene información completa de un compuesto PFAS.
    
    Args:
        pfas_id: ID del compuesto (ej. "PFOS", "PFOA")
    
    Returns:
        Dict con toda la información del compuesto
    """
    return PFAS_DATABASE.get(pfas_id, {})

def search_pfas_by_cas(cas_number: str) -> dict:
    """
    Busca un compuesto PFAS por número CAS.
    
    Args:
        cas_number: Número CAS del compuesto
    
    Returns:
        Dict con información del compuesto o None si no se encuentra
    """
    for pfas_id, data in PFAS_DATABASE.items():
        if data.get("cas") == cas_number:
            return {**data, "id": pfas_id}
    return None

# ============================================================================
# INFORMACIÓN DE LA BASE DE DATOS
# ============================================================================

def get_database_stats() -> dict:
    """
    Obtiene estadísticas de la base de datos.
    
    Returns:
        Dict con estadísticas
    """
    total_compounds = len(PFAS_DATABASE)
    categories = {}
    chain_lengths = {}
    functional_groups = {}
    
    for pfas_id, data in PFAS_DATABASE.items():
        # Contar por categoría
        category = data.get("category", "Unknown")
        categories[category] = categories.get(category, 0) + 1
        
        # Contar por longitud de cadena
        chain = data.get("chain_length", 0)
        chain_lengths[chain] = chain_lengths.get(chain, 0) + 1
        
        # Contar por grupo funcional
        fg = data.get("functional_group", "Unknown")
        functional_groups[fg] = functional_groups.get(fg, 0) + 1
    
    return {
        "total_compounds": total_compounds,
        "by_category": categories,
        "by_chain_length": chain_lengths,
        "by_functional_group": functional_groups
    }

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("BASE DE DATOS DE PFAS - INFORMACIÓN")
    print("="*80)
    
    stats = get_database_stats()
    print(f"\nTotal de compuestos: {stats['total_compounds']}")
    
    print("\nCompuestos por categoría:")
    for cat, count in stats['by_category'].items():
        print(f"  - {cat}: {count}")
    
    print("\nCompuestos por grupo funcional:")
    for fg, count in stats['by_functional_group'].items():
        print(f"  - {fg}: {count}")
    
    print("\nPFAS regulados:")
    regulated = get_regulated_pfas()
    for pfas_id, name, regulation in regulated:
        print(f"  - {name} ({pfas_id}): {regulation}")
    
    print("\nEjemplo de búsqueda - PFOS:")
    pfos_info = get_pfas_info("PFOS")
    print(f"  Nombre: {pfos_info.get('name')}")
    print(f"  Fórmula: {pfos_info.get('formula')}")
    print(f"  CAS: {pfos_info.get('cas')}")
    print(f"  Cadena: C{pfos_info.get('chain_length')}")
    print(f"  Picos clave: {len(pfos_info.get('key_peaks', []))}")
    
    print("\n" + "="*80)

# ============================================================================
# BASE DE DATOS DE VISUALIZACIONES 3D/2D
# ============================================================================

MOLECULE_VISUALIZATIONS = {
    # === Ácidos Perfluoroalcanoicos (PFCAs) ===
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
    
    # === Sulfonatos (PFSAs) ===
    "423-41-6": {"name": "PFPrS", "file_3d": "pfprs.sdf", "image_2d": "assets/molecules/pfprs_2d.png"},
    "375-73-5": {"name": "PFBS", "file_3d": "pfbs.sdf", "image_2d": "assets/molecules/pfbs_2d.png"},
    "2706-91-4": {"name": "PFPeS", "file_3d": "pfpes.sdf", "image_2d": "assets/molecules/pfpes_2d.png"},
    "355-46-4": {"name": "PFHxS", "file_3d": "pfhxs.sdf", "image_2d": "assets/molecules/pfhxs_2d.png"},
    "375-92-8": {"name": "PFHpS", "file_3d": "pfhps.sdf", "image_2d": "assets/molecules/pfhps_2d.png"},
    "1763-23-1": {"name": "PFOS", "file_3d": "pfos.sdf", "image_2d": "assets/molecules/pfos_2d.png"},
    "68259-12-1": {"name": "PFNS", "file_3d": "pfns.sdf", "image_2d": "assets/molecules/pfns_2d.png"},
    "335-77-3": {"name": "PFDS", "file_3d": "pfds.sdf", "image_2d": "assets/molecules/pfds_2d.png"},
    
    # === Emergentes ===
    "13252-13-6": {"name": "GenX", "file_3d": "genx.sdf", "image_2d": "assets/molecules/genx_2d.png"},
    "919005-14-4": {"name": "ADONA", "file_3d": "adona.sdf", "image_2d": "assets/molecules/adona_2d.png"},
    "73606-19-6": {"name": "F-53B", "file_3d": "f-53b.sdf", "image_2d": "assets/molecules/f-53b_2d.png"},
    "756-13-8": {"name": "F-53B Alt", "file_3d": "f-53b_alt.sdf", "image_2d": "assets/molecules/f-53b_alt_2d.png"},
    
    # === Fluorotelómeros ===
    "647-42-7": {"name": "6:2 FTOH", "file_3d": "6-2_ftoh.sdf", "image_2d": "assets/molecules/6-2_ftoh_2d.png"},
    "678-39-7": {"name": "8:2 FTOH", "file_3d": "8-2_ftoh.sdf", "image_2d": "assets/molecules/8-2_ftoh_2d.png"},
    "865-86-1": {"name": "10:2 FTOH", "file_3d": "10-2_ftoh.sdf", "image_2d": "assets/molecules/10-2_ftoh_2d.png"},
    "53826-13-4": {"name": "6:2 FTCA", "file_3d": "6-2_ftca.sdf", "image_2d": "assets/molecules/6-2_ftca_2d.png"},
    "27854-31-5": {"name": "8:2 FTCA", "file_3d": "8-2_ftca.sdf", "image_2d": "assets/molecules/8-2_ftca_2d.png"},
    
    # === Derivados ===
    "67584-42-3": {"name": "PFECHS", "file_3d": "pfechs.sdf", "image_2d": "assets/molecules/pfechs_2d.png"},
    "754-91-6": {"name": "PFOSA", "file_3d": "pfosa.sdf", "image_2d": "assets/molecules/pfosa_2d.png"},
    "4151-50-2": {"name": "N-EtFOSA", "file_3d": "n-etfosa.sdf", "image_2d": "assets/molecules/n-etfosa_2d.png"},
    "31506-32-8": {"name": "N-MeFOSA", "file_3d": "n-mefosa.sdf", "image_2d": "assets/molecules/n-mefosa_2d.png"},
    
    # === Genéricos ===
    "GENERIC_PFAS_UNKNOWN": {"name": "PFAS Desconocido", "file_3d": "pfas_unknown.sdf", "image_2d": "assets/molecules/pfas_unknown_2d.png"}
}


def get_molecule_visualization(cas_number: str) -> dict:
    """
    Obtiene datos de visualización 3D/2D para un número CAS.
    
    Args:
        cas_number: Número CAS del compuesto
    
    Returns:
        Dict con file_3d, image_2d y name
    """
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
    """Retorna lista de todos los compuestos con visualización disponible."""
    return [
        {"cas": cas, **data}
        for cas, data in MOLECULE_VISUALIZATIONS.items()
    ]