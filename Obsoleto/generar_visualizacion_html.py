import pandas as pd
import numpy as np
from pathlib import Path
import webbrowser
import json

def generar_visualizacion_html(df, ruta_salida=None):
    """Genera un archivo HTML con visualización treemap de los datos jerárquicos"""
    if ruta_salida is None:
        ruta_salida = Path.cwd() / "treemap_visualizacion.html"
    else:
        ruta_salida = Path(ruta_salida)
    
    # Leer la plantilla HTML
    plantilla_path = Path("template.html")
    
    if plantilla_path.exists():
        with open(plantilla_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    else:
        print("No se encontró el archivo de plantilla. Asegúrate de crear template.html")
        return None
    
    # Convertir DataFrame a JSON para JavaScript
    json_data = df.to_json(orient='records')
    
    # Reemplazar marcador de posición en la plantilla
    html_content = html_content.replace("DATOS_AQUI", json_data)
    
    # Guardar el archivo HTML
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Visualización generada en: {ruta_salida}")
    
    # Abrir en navegador
    webbrowser.open(f"file://{ruta_salida.absolute()}")
    
    return ruta_salida