"""
Base de datos expandida de PFAS
Contiene patrones espectrales de 19F-NMR para identificación
"""

PFAS_DATABASE = {
    # ==================== ÁCIDOS PERFLUOROALCANOICOS (PFAA) ====================
    
    "PFBA": {
        "name": "Ácido Perfluorobutanoico",
        "formula": "C4HF7O2",
        "cas": "375-22-4",
        "chain_length": 4,
        "functional_group": "COOH",
        "category": "PFCA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high", "multiplicity": "t"},
            "CF2_alpha": {"range": (-119, -117), "expected_intensity": "medium", "multiplicity": "m"},
            "CF2_beta": {"range": (-127, -125), "expected_intensity": "medium", "multiplicity": "m"}
        },
        "key_peaks": [-80.6, -118.0, -125.8],
        "intensity_ratio": {"CF3/CF2": 0.5},
        "molecular_weight": 214.04,
        "regulation_status": "EPA monitoring",
        "notes": "Cadena corta, alta solubilidad"
    },
    
    "PFPeA": {
        "name": "Ácido Perfluoropentanoico",
        "formula": "C5HF9O2",
        "cas": "2706-90-3",
        "chain_length": 5,
        "functional_group": "COOH",
        "category": "PFCA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
            "CF2_alpha": {"range": (-119, -117), "expected_intensity": "medium"},
            "CF2_internal": {"range": (-124, -122), "expected_intensity": "high"},
            "CF2_beta": {"range": (-127, -125), "expected_intensity": "medium"}
        },
        "key_peaks": [-80.7, -118.0, -123.0, -126.0],
        "intensity_ratio": {"CF3/CF2": 0.4},
        "molecular_weight": 264.05,
        "regulation_status": "Monitored"
    },
    
    "PFHxA": {
        "name": "Ácido Perfluorohexanoico",
        "formula": "C6HF11O2",
        "cas": "307-24-4",
        "chain_length": 6,
        "functional_group": "COOH",
        "category": "PFCA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
            "CF2_alpha": {"range": (-119, -117), "expected_intensity": "medium"},
            "CF2_internal": {"range": (-123, -121), "expected_intensity": "very_high"},
            "CF2_beta": {"range": (-127, -125), "expected_intensity": "high"}
        },
        "key_peaks": [-80.7, -118.0, -122.0, -126.1],
        "intensity_ratio": {"CF3/CF2": 0.35},
        "molecular_weight": 314.05,
        "regulation_status": "EPA 2020 monitoring"
    },
    
    "PFHpA": {
        "name": "Ácido Perfluoroheptanoico",
        "formula": "C7HF13O2",
        "cas": "375-85-9",
        "chain_length": 7,
        "functional_group": "COOH",
        "category": "PFCA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
            "CF2_alpha": {"range": (-119, -117), "expected_intensity": "medium"},
            "CF2_internal": {"range": (-123, -121), "expected_intensity": "very_high"},
            "CF2_beta": {"range": (-127, -125), "expected_intensity": "high"}
        },
        "key_peaks": [-80.7, -118.0, -121.9, -126.1],
        "intensity_ratio": {"CF3/CF2": 0.32},
        "molecular_weight": 364.06,
        "regulation_status": "Monitored"
    },
    
    "PFOA": {
        "name": "Ácido Perfluorooctanoico",
        "formula": "C8HF15O2",
        "cas": "335-67-1",
        "chain_length": 8,
        "functional_group": "COOH",
        "category": "PFCA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
            "CF2_alpha": {"range": (-119, -117), "expected_intensity": "medium"},
            "CF2_internal": {"range": (-123, -121), "expected_intensity": "very_high"},
            "CF2_beta": {"range": (-127, -125), "expected_intensity": "high"}
        },
        "key_peaks": [-80.7, -118.0, -121.9, -126.1],
        "intensity_ratio": {"CF3/CF2": 0.3},
        "molecular_weight": 414.07,
        "regulation_status": "EPA restricted",
        "notes": "PFAS legacy más común"
    },
    
    "PFNA": {
        "name": "Ácido Perfluorononanoico",
        "formula": "C9HF17O2",
        "cas": "375-95-1",
        "chain_length": 9,
        "functional_group": "COOH",
        "category": "PFCA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
            "CF2_alpha": {"range": (-119, -117), "expected_intensity": "medium"},
            "CF2_internal": {"range": (-123, -121), "expected_intensity": "very_high"},
            "CF2_beta": {"range": (-127, -125), "expected_intensity": "high"}
        },
        "key_peaks": [-80.7, -118.1, -122.0, -126.2],
        "intensity_ratio": {"CF3/CF2": 0.27},
        "molecular_weight": 464.08
    },
    
    "PFDA": {
        "name": "Ácido Perfluorodecanoico",
        "formula": "C10HF19O2",
        "cas": "335-76-2",
        "chain_length": 10,
        "functional_group": "COOH",
        "category": "PFCA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
            "CF2_alpha": {"range": (-119, -117), "expected_intensity": "medium"},
            "CF2_internal": {"range": (-123, -121), "expected_intensity": "very_high"},
            "CF2_beta": {"range": (-127, -125), "expected_intensity": "high"}
        },
        "key_peaks": [-80.7, -118.2, -122.1, -126.3],
        "intensity_ratio": {"CF3/CF2": 0.25},
        "molecular_weight": 514.08
    },
    
    "PFUnDA": {
        "name": "Ácido Perfluoroundecanoico",
        "formula": "C11HF21O2",
        "cas": "2058-94-8",
        "chain_length": 11,
        "functional_group": "COOH",
        "category": "PFCA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
            "CF2_alpha": {"range": (-119, -117), "expected_intensity": "medium"},
            "CF2_internal": {"range": (-123, -121), "expected_intensity": "very_high"},
            "CF2_beta": {"range": (-127, -125), "expected_intensity": "high"}
        },
        "key_peaks": [-80.7, -118.2, -122.1, -126.3],
        "intensity_ratio": {"CF3/CF2": 0.23},
        "molecular_weight": 564.09
    },
    
    "PFDoDA": {
        "name": "Ácido Perfluorododecanoico",
        "formula": "C12HF23O2",
        "cas": "307-55-1",
        "chain_length": 12,
        "functional_group": "COOH",
        "category": "PFCA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
            "CF2_alpha": {"range": (-119, -117), "expected_intensity": "medium"},
            "CF2_internal": {"range": (-123, -121), "expected_intensity": "very_high"},
            "CF2_beta": {"range": (-127, -125), "expected_intensity": "high"}
        },
        "key_peaks": [-80.7, -118.2, -122.1, -126.4],
        "intensity_ratio": {"CF3/CF2": 0.21},
        "molecular_weight": 614.10
    },
    
    # ==================== SULFONATOS PERFLUOROALCÁNICOS (PFSA) ====================
    
    "PFBS": {
        "name": "Sulfonato de Perfluorobutano",
        "formula": "C4HF9O3S",
        "cas": "375-73-5",
        "chain_length": 4,
        "functional_group": "SO3H",
        "category": "PFSA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
            "CF2_near_SO3": {"range": (-115, -113), "expected_intensity": "medium"},
            "CF2_beta": {"range": (-120, -118), "expected_intensity": "medium"}
        },
        "key_peaks": [-80.9, -114.0, -119.2],
        "intensity_ratio": {"CF3/CF2": 0.5},
        "molecular_weight": 300.10,
        "regulation_status": "Replacement for PFOS",
        "notes": "Cadena corta, considerado 'más seguro'"
    },
    
    "PFPeS": {
        "name": "Sulfonato de Perfluoropentano",
        "formula": "C5HF11O3S",
        "cas": "2706-91-4",
        "chain_length": 5,
        "functional_group": "SO3H",
        "category": "PFSA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
            "CF2_near_SO3": {"range": (-116, -113), "expected_intensity": "medium"},
            "CF2_internal": {"range": (-122, -119), "expected_intensity": "high"}
        },
        "key_peaks": [-81.0, -114.5, -120.3],
        "intensity_ratio": {"CF3/CF2": 0.45},
        "molecular_weight": 350.11
    },
    
    "PFHxS": {
        "name": "Sulfonato de Perfluorohexano",
        "formula": "C6HF13O3S",
        "cas": "355-46-4",
        "chain_length": 6,
        "functional_group": "SO3H",
        "category": "PFSA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
            "CF2_internal": {"range": (-122, -119), "expected_intensity": "high"},
            "CF2_near_SO3": {"range": (-116, -114), "expected_intensity": "medium"}
        },
        "key_peaks": [-81.0, -120.5, -115.1],
        "intensity_ratio": {"CF3/CF2": 0.4},
        "molecular_weight": 400.12,
        "regulation_status": "EPA 2021 monitoring"
    },
    
    "PFHpS": {
        "name": "Sulfonato de Perfluoroheptano",
        "formula": "C7HF15O3S",
        "cas": "375-92-8",
        "chain_length": 7,
        "functional_group": "SO3H",
        "category": "PFSA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -79), "expected_intensity": "high"},
            "CF2_near_SO3": {"range": (-115, -113), "expected_intensity": "medium"},
            "CF2_internal": {"range": (-122, -120), "expected_intensity": "very_high"}
        },
        "key_peaks": [-80.9, -114.3, -120.7],
        "intensity_ratio": {"CF3/CF2": 0.35},
        "molecular_weight": 450.13
    },
    
    "PFOS": {
        "name": "Sulfonato de Perfluorooctano",
        "formula": "C8HF17O3S",
        "cas": "1763-23-1",
        "chain_length": 8,
        "functional_group": "SO3H",
        "category": "PFSA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -79), "expected_intensity": "high"},
            "CF2_alpha": {"range": (-115, -113), "expected_intensity": "medium"},
            "CF2_internal": {"range": (-122, -120), "expected_intensity": "very_high"},
            "CF2_near_SO3": {"range": (-117, -115), "expected_intensity": "medium"}
        },
        "key_peaks": [-80.9, -114.3, -120.8, -116.2],
        "intensity_ratio": {"CF3/CF2": 0.3},
        "molecular_weight": 500.13,
        "regulation_status": "EPA banned",
        "notes": "PFAS legacy, alta persistencia"
    },
    
    "PFNS": {
        "name": "Sulfonato de Perfluorononano",
        "formula": "C9HF19O3S",
        "cas": "68259-12-1",
        "chain_length": 9,
        "functional_group": "SO3H",
        "category": "PFSA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -79), "expected_intensity": "high"},
            "CF2_near_SO3": {"range": (-116, -113), "expected_intensity": "medium"},
            "CF2_internal": {"range": (-122, -120), "expected_intensity": "very_high"}
        },
        "key_peaks": [-80.9, -114.4, -120.9],
        "intensity_ratio": {"CF3/CF2": 0.28},
        "molecular_weight": 550.14
    },
    
    "PFDS": {
        "name": "Sulfonato de Perfluorodecano",
        "formula": "C10HF21O3S",
        "cas": "335-77-3",
        "chain_length": 10,
        "functional_group": "SO3H",
        "category": "PFSA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -79), "expected_intensity": "high"},
            "CF2_near_SO3": {"range": (-116, -113), "expected_intensity": "medium"},
            "CF2_internal": {"range": (-122, -120), "expected_intensity": "very_high"}
        },
        "key_peaks": [-80.9, -114.5, -121.0],
        "intensity_ratio": {"CF3/CF2": 0.26},
        "molecular_weight": 600.15
    },
    
    # ==================== PFAS DE NUEVA GENERACIÓN ====================
    
    "GenX": {
        "name": "HFPO-DA (GenX)",
        "formula": "C6HF11O3",
        "cas": "13252-13-6",
        "chain_length": 6,
        "functional_group": "COOH",
        "category": "Ether-PFCA",
        "patterns": {
            "CF3_terminal": {"range": (-83, -78), "expected_intensity": "high"},
            "CF3_branch": {"range": (-75, -72), "expected_intensity": "medium"},
            "CF2_ether": {"range": (-88, -84), "expected_intensity": "medium"},
            "CF2_alpha": {"range": (-119, -115), "expected_intensity": "medium"}
        },
        "key_peaks": [-80.2, -73.5, -85.6, -117.3],
        "intensity_ratio": {"CF3/CF2": 0.6},
        "molecular_weight": 330.05,
        "regulation_status": "Replacement controversial",
        "notes": "Estructura ramificada con éter, reemplazo de PFOA"
    },
    
    "ADONA": {
        "name": "4,8-Dioxa-3H-perfluorononanoato",
        "formula": "C7HF13O4",
        "cas": "919005-14-4",
        "chain_length": 7,
        "functional_group": "COOH",
        "category": "Ether-PFCA",
        "patterns": {
            "CF3_terminal": {"range": (-83, -81), "expected_intensity": "high"},
            "CF2_ether": {"range": (-90, -83), "expected_intensity": "high"},
            "CF2_alpha": {"range": (-119, -116), "expected_intensity": "medium"}
        },
        "key_peaks": [-82.1, -86.2, -87.8, -117.8],
        "intensity_ratio": {"CF3/CF2": 0.5},
        "molecular_weight": 378.05,
        "regulation_status": "Monitored",
        "notes": "Dos grupos éter, alternativa a PFOA"
    },
    
    "HFPO-TA": {
        "name": "Ácido Perfluoro-2-propoxipropanoico",
        "formula": "C6HF11O3",
        "cas": "13252-13-6",
        "chain_length": 6,
        "functional_group": "COOH",
        "category": "Ether-PFCA",
        "patterns": {
            "CF3_terminal": {"range": (-83, -80), "expected_intensity": "high"},
            "CF3_branch": {"range": (-76, -73), "expected_intensity": "medium"},
            "CF_ether": {"range": (-147, -143), "expected_intensity": "low"},
            "CF2_alpha": {"range": (-120, -116), "expected_intensity": "medium"}
        },
        "key_peaks": [-81.5, -74.8, -145.2, -118.0],
        "intensity_ratio": {"CF3/CF2": 0.7},
        "molecular_weight": 330.05,
        "notes": "Isómero de GenX"
    },
    
    "F-53B": {
        "name": "Cl-PFESA (F-53B)",
        "formula": "C8HClF16O4S",
        "cas": "756-13-8",
        "chain_length": 8,
        "functional_group": "SO3H",
        "category": "Chlorinated-PFSA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -79), "expected_intensity": "high"},
            "CF2_near_Cl": {"range": (-111, -108), "expected_intensity": "medium"},
            "CF2_ether": {"range": (-88, -85), "expected_intensity": "medium"},
            "CF2_near_SO3": {"range": (-117, -114), "expected_intensity": "medium"}
        },
        "key_peaks": [-80.7, -109.5, -86.3, -115.8],
        "intensity_ratio": {"CF3/CF2": 0.35},
        "molecular_weight": 570.57,
        "regulation_status": "Emerging concern",
        "notes": "Usado en China, contiene cloro"
    },
    
    # ==================== PRECURSORES ====================
    
    "6:2 FTOH": {
        "name": "6:2 Fluorotelomer Alcohol",
        "formula": "C8H5F13O",
        "cas": "647-42-7",
        "chain_length": 8,
        "functional_group": "CH2CH2OH",
        "category": "FTOH",
        "patterns": {
            "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
            "CF2_internal": {"range": (-122, -120), "expected_intensity": "very_high"},
            "CF2_near_CH2": {"range": (-116, -114), "expected_intensity": "medium"}
        },
        "key_peaks": [-80.8, -121.2, -115.3],
        "intensity_ratio": {"CF3/CF2": 0.35},
        "molecular_weight": 364.11,
        "notes": "Precursor, puede degradarse a PFHxA"
    },
    
    "8:2 FTOH": {
        "name": "8:2 Fluorotelomer Alcohol",
        "formula": "C10H5F17O",
        "cas": "678-39-7",
        "chain_length": 10,
        "functional_group": "CH2CH2OH",
        "category": "FTOH",
        "patterns": {
            "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
            "CF2_internal": {"range": (-122, -120), "expected_intensity": "very_high"},
            "CF2_near_CH2": {"range": (-116, -114), "expected_intensity": "medium"}
        },
        "key_peaks": [-80.8, -121.3, -115.4],
        "intensity_ratio": {"CF3/CF2": 0.3},
        "molecular_weight": 464.12,
        "notes": "Precursor común, degrada a PFOA"
    },
    
    "10:2 FTOH": {
        "name": "10:2 Fluorotelomer Alcohol",
        "formula": "C12H5F21O",
        "cas": "865-86-1",
        "chain_length": 12,
        "functional_group": "CH2CH2OH",
        "category": "FTOH",
        "patterns": {
            "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
            "CF2_internal": {"range": (-122, -120), "expected_intensity": "very_high"},
            "CF2_near_CH2": {"range": (-116, -114), "expected_intensity": "medium"}
        },
        "key_peaks": [-80.8, -121.4, -115.5],
        "intensity_ratio": {"CF3/CF2": 0.27},
        "molecular_weight": 564.13,
        "notes": "Precursor de cadena larga"
    },
    
    "6:2 FTCA": {
        "name": "6:2 Fluorotelomer Carboxylic Acid",
        "formula": "C8H3F13O2",
        "cas": "53826-13-4",
        "chain_length": 8,
        "functional_group": "CH2COOH",
        "category": "FTCA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
            "CF2_internal": {"range": (-122, -120), "expected_intensity": "very_high"},
            "CF2_near_CH2": {"range": (-117, -115), "expected_intensity": "medium"}
        },
        "key_peaks": [-80.8, -121.3, -116.2],
        "intensity_ratio": {"CF3/CF2": 0.35},
        "molecular_weight": 378.09,
        "notes": "Intermediario de degradación"
    },
    
    "8:2 FTCA": {
        "name": "8:2 Fluorotelomer Carboxylic Acid",
        "formula": "C10H3F17O2",
        "cas": "27854-31-5",
        "chain_length": 10,
        "functional_group": "CH2COOH",
        "category": "FTCA",
        "patterns": {
            "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
            "CF2_internal": {"range": (-122, -120), "expected_intensity": "very_high"},
            "CF2_near_CH2": {"range": (-117, -115), "expected_intensity": "medium"}
        },
        "key_peaks": [-80.8, -121.4, -116.3],
        "intensity_ratio": {"CF3/CF2": 0.3},
        "molecular_weight": 478.10,
        "notes": "Intermediario hacia PFOA"
    },
    
    # ==================== FLUOROPOLÍMEROS ====================
    
    "PFESA": {
        "name": "Perfluoroether Sulfonic Acid",
        "formula": "Variable",
        "cas": "Various",
        "chain_length": 8,
        "functional_group": "SO3H",
        "category": "Ether-PFSA",
        "patterns": {
            "CF3_multiple": {"range": (-83, -78), "expected_intensity": "high"},
            "CF2_ether": {"range": (-90, -83), "expected_intensity": "high"},
            "CF2_near_SO3": {"range": (-117, -113), "expected_intensity": "medium"}
        },
        "key_peaks": [-80.5, -86.5, -115.0],
        "intensity_ratio": {"CF3/CF2": 0.5},
        "notes": "Familia de compuestos con éteres"
    },
    
    "PFECA": {
        "name": "Perfluoroether Carboxylic Acid",
        "formula": "Variable",
        "cas": "Various",
        "chain_length": 7,
        "functional_group": "COOH",
        "category": "Ether-PFCA",
        "patterns": {
            "CF3_multiple": {"range": (-83, -78), "expected_intensity": "high"},
            "CF2_ether": {"range": (-90, -83), "expected_intensity": "high"},
            "CF2_alpha": {"range": (-120, -116), "expected_intensity": "medium"}
        },
        "key_peaks": [-81.0, -87.0, -118.0],
        "intensity_ratio": {"CF3/CF2": 0.6},
        "notes": "Familia de ácidos con éteres"
    }
}

# Categorías para búsquedas y filtrado
PFAS_CATEGORIES = {
    "PFCA": "Perfluoroalkyl Carboxylic Acids",
    "PFSA": "Perfluoroalkane Sulfonic Acids",
    "Ether-PFCA": "Ether-based PFCA",
    "Ether-PFSA": "Ether-based PFSA",
    "FTOH": "Fluorotelomer Alcohols",
    "FTCA": "Fluorotelomer Carboxylic Acids",
    "Chlorinated-PFSA": "Chlorinated PFSA"
}

# Grupos funcionales y sus características espectrales
FUNCTIONAL_GROUP_SIGNATURES = {
    "COOH": {
        "name": "Ácido carboxílico",
        "cf2_alpha_range": (-120, -117),
        "cf2_alpha_shift": "upfield ~118 ppm",
        "influence": "Electron-withdrawing, deshields α-CF₂"
    },
    "SO3H": {
        "name": "Ácido sulfónico",
        "cf2_alpha_range": (-117, -113),
        "cf2_alpha_shift": "upfield ~115 ppm",
        "influence": "Strong electron-withdrawing, more deshielding"
    },
    "CH2CH2OH": {
        "name": "Alcohol (telómero)",
        "cf2_alpha_range": (-117, -114),
        "cf2_alpha_shift": "upfield ~115 ppm",
        "influence": "Non-fluorinated spacer present"
    },
    "CH2COOH": {
        "name": "Ácido carboxílico (telómero)",
        "cf2_alpha_range": (-118, -115),
        "cf2_alpha_shift": "upfield ~116 ppm",
        "influence": "Non-fluorinated spacer present"
    }
}

def get_pfas_by_category(category: str):
    """Retorna todos los PFAS de una categoría específica."""
    return {k: v for k, v in PFAS_DATABASE.items() if v.get("category") == category}

def get_pfas_by_chain_length(min_length: int, max_length: int):
    """Retorna PFAS con longitud de cadena en el rango especificado."""
    return {k: v for k, v in PFAS_DATABASE.items() 
            if min_length <= v.get("chain_length", 0) <= max_length}

def get_regulated_pfas():
    """Retorna PFAS con estado regulatorio."""
    return {k: v for k, v in PFAS_DATABASE.items() 
            if "regulation_status" in v}

def search_pfas_by_cas(cas_number: str):
    """Busca PFAS por número CAS."""
    return {k: v for k, v in PFAS_DATABASE.items() 
            if v.get("cas") == cas_number}


# ============================================================================
# BASE DE DATOS DE VISUALIZACIONES 3D/2D
# ============================================================================

MOLECULE_VISUALIZATIONS = {
    # === Ácidos Perfluoroalcanoicos (PFCAs) ===
    "375-22-4": {
        "name": "PFBA (Ácido Perfluorobutanoico)",
        "file_3d": "pfba.sdf",
        "image_2d": "assets/molecules/pfba_2d.png"
    },
    "2706-90-3": {
        "name": "PFPeA (Ácido Perfluoropentanoico)",
        "file_3d": "pfpea.sdf",
        "image_2d": "assets/molecules/pfpea_2d.png"
    },
    "307-24-4": {
        "name": "PFHxA (Ácido Perfluorohexanoico)",
        "file_3d": "pfhxa.sdf",
        "image_2d": "assets/molecules/pfhxa_2d.png"
    },
    "375-85-9": {
        "name": "PFHpA (Ácido Perfluoroheptanoico)",
        "file_3d": "pfhpa.sdf",
        "image_2d": "assets/molecules/pfhpa_2d.png"
    },
    "335-67-1": {
        "name": "PFOA (Ácido Perfluorooctanoico)",
        "file_3d": "pfoa.sdf",
        "image_2d": "assets/molecules/pfoa_2d.png"
    },
    "375-95-1": {
        "name": "PFNA (Ácido Perfluorononanoico)",
        "file_3d": "pfna.sdf",
        "image_2d": "assets/molecules/pfna_2d.png"
    },
    "335-76-2": {
        "name": "PFDA (Ácido Perfluorodecanoico)",
        "file_3d": "pfda.sdf",
        "image_2d": "assets/molecules/pfda_2d.png"
    },
    "2058-94-8": {
        "name": "PFUnDA (Ácido Perfluoroundecanoico)",
        "file_3d": "pfunda.sdf",
        "image_2d": "assets/molecules/pfunda_2d.png"
    },
    "307-55-1": {
        "name": "PFDoDA (Ácido Perfluorododecanoico)",
        "file_3d": "pfdoda.sdf",
        "image_2d": "assets/molecules/pfdoda_2d.png"
    },
    
    # === Sulfonatos Perfluoroalcanos (PFSAs) ===
    "375-73-5": {
        "name": "PFBS (Sulfonato de Perfluorobutano)",
        "file_3d": "pfbs.sdf",
        "image_2d": "assets/molecules/pfbs_2d.png"
    },
    "2706-91-4": {
        "name": "PFPeS (Sulfonato de Perfluoropentano)",
        "file_3d": "pfpes.sdf",
        "image_2d": "assets/molecules/pfpes_2d.png"
    },
    "355-46-4": {
        "name": "PFHxS (Sulfonato de Perfluorohexano)",
        "file_3d": "pfhxs.sdf",
        "image_2d": "assets/molecules/pfhxs_2d.png"
    },
    "375-92-8": {
        "name": "PFHpS (Sulfonato de Perfluoroheptano)",
        "file_3d": "pfhps.sdf",
        "image_2d": "assets/molecules/pfhps_2d.png"
    },
    "1763-23-1": {
        "name": "PFOS (Sulfonato de Perfluorooctano)",
        "file_3d": "pfos.sdf",
        "image_2d": "assets/molecules/pfos_2d.png"
    },
    "68259-12-1": {
        "name": "PFNS (Sulfonato de Perfluorononano)",
        "file_3d": "pfns.sdf",
        "image_2d": "assets/molecules/pfns_2d.png"
    },
    "335-77-3": {
        "name": "PFDS (Sulfonato de Perfluorodecano)",
        "file_3d": "pfds.sdf",
        "image_2d": "assets/molecules/pfds_2d.png"
    },

    # === PFAS Emergentes y Alternativos ===
    "13252-13-6": {
        "name": "GenX (HFPO-DA)",
        "file_3d": "genx.sdf",
        "image_2d": "assets/molecules/genx_2d.png"
    },
    "919005-14-4": {
        "name": "ADONA",
        "file_3d": "adona.sdf",
        "image_2d": "assets/molecules/adona_2d.png"
    },
    "73606-19-6": {
        "name": "F-53B",
        "file_3d": "f53b.sdf",
        "image_2d": "assets/molecules/f53b_2d.png"
    },
    "756-13-8": {
        "name": "F-53B (Cl-PFESA)",
        "file_3d": "f53b_alt.sdf",
        "image_2d": "assets/molecules/f53b_alt_2d.png"
    },

    # === Fluorotelómeros (FTOHs) ===
    "647-42-7": {
        "name": "6:2 FTOH",
        "file_3d": "6-2_ftoh.sdf",
        "image_2d": "assets/molecules/6-2_ftoh_2d.png"
    },
    "678-39-7": {
        "name": "8:2 FTOH",
        "file_3d": "8-2_ftoh.sdf",
        "image_2d": "assets/molecules/8-2_ftoh_2d.png"
    },
    "865-86-1": {
        "name": "10:2 FTOH",
        "file_3d": "10-2_ftoh.sdf",
        "image_2d": "assets/molecules/10-2_ftoh_2d.png"
    },
    
    # === Fluorotelómeros Ácidos (FTCAs) ===
    "53826-13-4": {
        "name": "6:2 FTCA",
        "file_3d": "6-2_ftca.sdf",
        "image_2d": "assets/molecules/6-2_ftca_2d.png"
    },
    "27854-31-5": {
        "name": "8:2 FTCA",
        "file_3d": "8-2_ftca.sdf",
        "image_2d": "assets/molecules/8-2_ftca_2d.png"
    },
    
    # === CATEGORÍAS GENÉRICAS (sin CAS específico) ===
    # Para compuestos detectados pero no identificados específicamente
    "GENERIC_PERFLUOROETHER": {
        "name": "Perfluoroether Carboxylic Acid (Genérico)",
        "file_3d": "perfluoroether_generic.sdf",
        "image_2d": "assets/molecules/perfluoroether_generic_2d.png"
    },
    "GENERIC_PERFLUOROALKYL": {
        "name": "Perfluoroalkyl Substance (Genérico)",
        "file_3d": "perfluoroalkyl_generic.sdf",
        "image_2d": "assets/molecules/perfluoroalkyl_generic_2d.png"
    },
    "GENERIC_FTOH": {
        "name": "Fluorotelomer Alcohol (Genérico)",
        "file_3d": "ftoh_generic.sdf",
        "image_2d": "assets/molecules/ftoh_generic_2d.png"
    },
    "GENERIC_FTCA": {
        "name": "Fluorotelomer Carboxylic Acid (Genérico)",
        "file_3d": "ftca_generic.sdf",
        "image_2d": "assets/molecules/ftca_generic_2d.png"
    },
    "GENERIC_PFCA": {
        "name": "Perfluorocarboxylic Acid (Genérico)",
        "file_3d": "pfca_generic.sdf",
        "image_2d": "assets/molecules/pfca_generic_2d.png"
    },
    "GENERIC_PFSA": {
        "name": "Perfluorosulfonic Acid (Genérico)",
        "file_3d": "pfsa_generic.sdf",
        "image_2d": "assets/molecules/pfsa_generic_2d.png"
    },
    "GENERIC_PFAS_UNKNOWN": {
        "name": "PFAS Desconocido",
        "file_3d": "pfas_unknown.sdf",
        "image_2d": "assets/molecules/pfas_unknown_2d.png"
    },
    "GENERIC_PFAS_MIXTURE": {
        "name": "Mezcla de PFAS",
        "file_3d": "pfas_mixture.sdf",
        "image_2d": "assets/molecules/pfas_mixture_2d.png"
    }
}


def get_molecule_visualization(cas_number: str) -> dict:
    """
    Obtiene datos de visualización 3D/2D para un número CAS.
    
    Args:
        cas_number: Número CAS del compuesto, o identificador genérico
    
    Returns:
        Dict con file_3d, image_2d y name. 
        Si no existe, retorna dict con valores None.
    
    Ejemplo:
        >>> viz = get_molecule_visualization("335-67-1")
        >>> print(viz["name"])  # "PFOA (Ácido Perfluorooctanoico)"
        >>> print(viz["file_3d"])  # "pfoa.sdf"
        
        >>> # Para categorías genéricas
        >>> viz = get_molecule_visualization("Various")
        >>> print(viz["name"])  # "PFAS Desconocido"
    """
    # Casos especiales para categorías genéricas
    if not cas_number or cas_number.lower() in ['various', 'variable', 'generic', 'unknown']:
        return MOLECULE_VISUALIZATIONS.get("GENERIC_PFAS_UNKNOWN", {
            "name": None,
            "file_3d": None,
            "image_2d": None
        })
    
    # Buscar por CAS normal
    return MOLECULE_VISUALIZATIONS.get(cas_number, {
        "name": None,
        "file_3d": None,
        "image_2d": None
    })


def get_generic_visualization_by_name(compound_name: str) -> dict:
    """
    Obtiene visualización genérica basada en el nombre del compuesto.
    
    Útil cuando el detector identifica una categoría genérica.
    
    Args:
        compound_name: Nombre del compuesto (ej: "Perfluoroether Carboxylic Acid")
    
    Returns:
        Dict con visualización genérica apropiada
    
    Ejemplo:
        >>> viz = get_generic_visualization_by_name("Perfluoroether Carboxylic Acid")
        >>> print(viz["image_2d"])  # "assets/molecules/perfluoroether_generic_2d.png"
    """
    name_lower = compound_name.lower()
    
    # Mapeo de palabras clave a categorías genéricas
    mappings = {
        "perfluoroether": "GENERIC_PERFLUOROETHER",
        "perfluoroalkyl": "GENERIC_PERFLUOROALKYL",
        "fluorotelomer alcohol": "GENERIC_FTOH",
        "ftoh": "GENERIC_FTOH",
        "fluorotelomer carboxylic": "GENERIC_FTCA",
        "ftca": "GENERIC_FTCA",
        "perfluorocarboxylic": "GENERIC_PFCA",
        "perfluorosulfonic": "GENERIC_PFSA",
        "mixture": "GENERIC_PFAS_MIXTURE",
        "mezcla": "GENERIC_PFAS_MIXTURE",
    }
    
    # Buscar coincidencia
    for keyword, generic_id in mappings.items():
        if keyword in name_lower:
            return MOLECULE_VISUALIZATIONS.get(generic_id, {
                "name": None,
                "file_3d": None,
                "image_2d": None
            })
    
    # Por defecto, retornar "PFAS Desconocido"
    return MOLECULE_VISUALIZATIONS.get("GENERIC_PFAS_UNKNOWN", {
        "name": None,
        "file_3d": None,
        "image_2d": None
    })


def list_available_visualizations() -> list:
    """
    Retorna lista de todos los compuestos con visualización disponible.
    
    Returns:
        Lista de dicts con cas, name, file_3d, image_2d
    """
    return [
        {"cas": cas, **data}
        for cas, data in MOLECULE_VISUALIZATIONS.items()
    ]


def check_visualization_files(base_path: str = "frontend") -> dict:
    """
    Verifica qué archivos de visualización existen en el sistema.
    
    Args:
        base_path: Ruta base donde buscar (default: "frontend")
    
    Returns:
        Dict con estadísticas de archivos encontrados/faltantes
    """
    from pathlib import Path
    
    base = Path(base_path)
    stats = {
        "total_compounds": len(MOLECULE_VISUALIZATIONS),
        "found_3d": 0,
        "found_2d": 0,
        "missing_3d": [],
        "missing_2d": []
    }
    
    for cas, data in MOLECULE_VISUALIZATIONS.items():
        # Verificar 3D
        if data["file_3d"]:
            file_3d_path = base / "assets" / "molecules" / data["file_3d"]
            if file_3d_path.exists():
                stats["found_3d"] += 1
            else:
                stats["missing_3d"].append({
                    "cas": cas,
                    "name": data["name"],
                    "file": data["file_3d"]
                })
        
        # Verificar 2D
        if data["image_2d"]:
            image_2d_path = base / data["image_2d"]
            if image_2d_path.exists():
                stats["found_2d"] += 1
            else:
                stats["missing_2d"].append({
                    "cas": cas,
                    "name": data["name"],
                    "file": data["image_2d"]
                })
    
    return stats