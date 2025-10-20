import json
from pathlib import Path

ANALYSIS_DIR = Path("../backend/storage/analysis").resolve()

for f in ANALYSIS_DIR.glob("*_craft.json"):
    with open(f, "r") as file:
        data = json.load(file)
    
    # Ejemplo: añadir un campo de análisis adicional
    data["analyzed"] = True

    output_file = ANALYSIS_DIR / f"{f.stem}_final.json"
    with open(output_file, "w") as out:
        json.dump(data, out, indent=2)

    print(f"Archivo analizado: {output_file.name}")
