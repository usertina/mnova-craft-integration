import time, shutil, subprocess
from pathlib import Path

MNOVA_EXPORT_DIR = Path("../mnova_exports").resolve()
OUTPUT_DIR = Path("storage/output").resolve()
ANALYSIS_DIR = Path("storage/analysis").resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

seen = set()

while True:
    for f in MNOVA_EXPORT_DIR.glob("*.*"):
        if f.is_file() and f.name not in seen:
            print("📄 Nuevo archivo MNova:", f.name)
            dest = OUTPUT_DIR / f.name
            shutil.copy(f, dest)

            try:
                subprocess.run([
                    "craft-cli",
                    "-i", str(dest),
                    "-o", str(ANALYSIS_DIR / f"{f.stem}_craft.json")
                ])
                print(f"✅ Craft procesó {f.name}")
            except Exception as e:
                print(f"⚠️ Error al ejecutar Craft: {e}")

            seen.add(f.name)
    time.sleep(5)
