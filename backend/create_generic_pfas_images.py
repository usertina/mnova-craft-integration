#!/usr/bin/env python3
"""
Generador de Imágenes Genéricas para Categorías PFAS
=====================================================

Crea imágenes representativas para categorías genéricas de PFAS
que no tienen un CAS específico.

USO:
    pip install pillow
    python create_generic_pfas_images.py
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


def create_generic_image(text: str, output_path: Path, size: int = 400):
    """
    Crea una imagen genérica con texto para categorías PFAS.
    
    Args:
        text: Texto a mostrar (nombre de la categoría)
        output_path: Ruta donde guardar la imagen
        size: Tamaño de la imagen en píxeles
    """
    # Crear imagen con fondo gris claro
    img = Image.new('RGB', (size, size), color='#f0f0f0')
    draw = ImageDraw.Draw(img)
    
    # Dibujar borde
    border_color = '#666666'
    border_width = 3
    draw.rectangle(
        [(border_width, border_width), 
         (size - border_width, size - border_width)],
        outline=border_color,
        width=border_width
    )
    
    # Dibujar símbolo químico genérico (hexágono)
    center_x, center_y = size // 2, size // 2 - 30
    radius = 80
    
    hexagon_points = []
    for i in range(6):
        angle = i * 60 - 30  # Empezar desde arriba
        import math
        x = center_x + radius * math.cos(math.radians(angle))
        y = center_y + radius * math.sin(math.radians(angle))
        hexagon_points.append((x, y))
    
    draw.polygon(hexagon_points, outline='#0066cc', width=4)
    
    # Añadir "CF2" en el centro del hexágono
    try:
        # Intentar usar una fuente del sistema
        font_large = ImageFont.truetype("arial.ttf", 40)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except:
        # Usar fuente por defecto si no encuentra Arial
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    cf2_text = "CF₂"
    cf2_bbox = draw.textbbox((0, 0), cf2_text, font=font_large)
    cf2_width = cf2_bbox[2] - cf2_bbox[0]
    cf2_height = cf2_bbox[3] - cf2_bbox[1]
    
    draw.text(
        (center_x - cf2_width // 2, center_y - cf2_height // 2),
        cf2_text,
        fill='#0066cc',
        font=font_large
    )
    
    # Añadir texto de categoría en la parte inferior
    # Dividir texto largo en múltiples líneas
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        bbox = draw.textbbox((0, 0), test_line, font=font_small)
        if bbox[2] - bbox[0] > size - 40:
            current_line.pop()
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Dibujar líneas de texto
    y_offset = size - 80 - (len(lines) * 30)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_small)
        text_width = bbox[2] - bbox[0]
        draw.text(
            (center_x - text_width // 2, y_offset),
            line,
            fill='#333333',
            font=font_small
        )
        y_offset += 30
    
    # Añadir nota "Categoría Genérica"
    generic_text = "(Categoría Genérica)"
    bbox = draw.textbbox((0, 0), generic_text, font=font_small)
    text_width = bbox[2] - bbox[0]
    draw.text(
        (center_x - text_width // 2, size - 40),
        generic_text,
        fill='#999999',
        font=font_small
    )
    
    # Guardar
    img.save(output_path)
    print(f"   ✅ Imagen creada: {output_path.name}")


def create_all_generic_images():
    """Crea imágenes genéricas para todas las categorías PFAS."""
    
    # Determinar directorio de salida
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "frontend" / "assets" / "molecules"
    
    if not output_dir.parent.parent.exists():
        output_dir = script_dir / "molecules"
        print(f"⚠️  Directorio frontend no encontrado")
        print(f"   Usando: {output_dir}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("🎨 GENERADOR DE IMÁGENES GENÉRICAS PARA PFAS")
    print("="*70)
    print(f"\n📁 Directorio: {output_dir}\n")
    
    # Categorías genéricas que necesitan imágenes
    generic_categories = {
        "perfluoroether_generic": "Perfluoroether Carboxylic Acid",
        "perfluoroalkyl_generic": "Perfluoroalkyl Substance",
        "ftoh_generic": "Fluorotelomer Alcohol",
        "ftca_generic": "Fluorotelomer Carboxylic Acid",
        "pfca_generic": "Perfluorocarboxylic Acid",
        "pfsa_generic": "Perfluorosulfonic Acid",
        "pfas_unknown": "PFAS Desconocido",
        "pfas_mixture": "Mezcla de PFAS"
    }
    
    for filename, display_name in generic_categories.items():
        print(f"🖼️  Creando: {display_name}")
        
        # Crear imagen 2D
        png_path = output_dir / f"{filename}_2d.png"
        create_generic_image(display_name, png_path)
        
        # También crear un archivo placeholder SDF
        sdf_path = output_dir / f"{filename}.sdf"
        with open(sdf_path, 'w') as f:
            f.write(f"Generic PFAS Category: {display_name}\n")
            f.write("  Created by CraftRMN Pro\n")
            f.write("  This is a placeholder for generic categories\n")
            f.write("\n")
            f.write("  0  0  0  0  0  0            999 V2000\n")
            f.write("M  END\n")
        print(f"   ✅ Placeholder SDF creado: {sdf_path.name}")
    
    print("\n" + "="*70)
    print(f"✅ Completado: {len(generic_categories)} categorías creadas")
    print(f"📁 Archivos en: {output_dir}")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        from PIL import Image
    except ImportError:
        print("❌ Error: Pillow no está instalado")
        print("   Instala con: pip install pillow")
        exit(1)
    
    create_all_generic_images()