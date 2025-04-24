import os
import json
from excel_data_extractor import main

def test_excel_data_extractor():
    """
    Prueba la extracción y procesamiento de datos desde un archivo Excel.
    """
    # Ruta al archivo Excel de prueba
    excel_path = "/Users/didac/Downloads/StoryMac/DashBTracker/PruebasCdM/Tchart_V06.xlsm"

    # Verificar que el archivo existe
    if not os.path.exists(excel_path):
        print(f"El archivo Excel no existe: {excel_path}")
        return

    # Ejecutar el extractor principal
    try:
        print("Iniciando prueba de extracción de datos...")
        data = main()
        if data is None:
            print("El extractor principal devolvió None. Verifique la implementación de la función main.")
            return
        print("Valor devuelto por main():")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("Prueba completada exitosamente.")

        # Filtrar los datos para las celdas específicas
        filtered_data = [
            row for row in data
            if (
                row.get("CIA") == "Sp"
                and row.get("PRJID") == "31199"
                and (
                    (row.get("ROW") == "01:TRANSPORTES Y EMBALAJES" and row.get("COLUMN") == "17:TRANSP. & DESPLAZ.")
                    or
                    (row.get("ROW") == "02:GASTOS DE DESPLAZAMIENTO" and row.get("COLUMN") == "17:TRANSP. & DESPLAZ.")
                )
            )
        ]
        # Mostrar los datos filtrados
        print("\n=== DATOS FILTRADOS ===")
        for row in filtered_data:
            print(json.dumps(row, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"Error durante la prueba: {e}")

if __name__ == "__main__":
    test_excel_data_extractor()