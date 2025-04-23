#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Aplicación principal para convertir datos de Excel a un dashboard Plotly
"""
import os
import sys
import argparse
import json
import importlib.util

def check_dependencies():
    """
    Verifica que todas las dependencias estén instaladas
    """
    required_packages = [
        'dash', 'plotly', 'pandas', 'openpyxl', 'dash_bootstrap_components'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
    
    if missing_packages:
        print("Faltan las siguientes dependencias:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nPor favor, instale las dependencias faltantes con:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def debug_log(message):
    """Función para registrar mensajes de depuración con formato claro."""
    print(f"[DEBUG] {message}")

def main():
    """
    Función principal para realizar solo la extracción de datos.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Extraer datos desde un archivo Excel")
    parser.add_argument("--excel", type=str, required=True, help="Ruta al archivo Excel")
    parser.add_argument("--historic-sheet", type=str, required=True, help="Nombre de la hoja de datos históricos")
    parser.add_argument("--kpi-sheet", type=str, required=True, help="Nombre de la hoja de datos KPI")
    parser.add_argument("--debug", action="store_true", help="Activar modo depuración")
    args = parser.parse_args()

    from excel_extractor import ExcelDataExtractor

    def extract_and_format_data(excel_path, historic_sheet, kpi_sheet, debug=False):
        """Extrae y formatea los datos desde Excel."""
        extractor = ExcelDataExtractor(excel_path)
        data = {}

        # Extraer datos históricos
        if historic_sheet:
            try:
                data['historicData'] = extractor.extract_historic_data(historic_sheet)
                if debug:
                    print(f"Datos históricos extraídos: {len(data['historicData'])} registros")
            except Exception as e:
                print(f"Error al extraer datos históricos: {e}")

        # Extraer datos KPI
        if kpi_sheet:
            try:
                data['kpiData'] = extractor.extract_kpi_data(kpi_sheet)
                if debug:
                    print(f"Datos KPI extraídos: {len(data['kpiData'])} registros")
            except Exception as e:
                print(f"Error al extraer datos KPI: {e}")

        return data

    # Realizar la extracción de datos
    data = extract_and_format_data(
        excel_path=args.excel,
        historic_sheet=args.historic_sheet,
        kpi_sheet=args.kpi_sheet,
        debug=args.debug
    )

    # Mostrar los datos extraídos
    print("\n=== RESULTADOS DE LA EXTRACCIÓN ===")
    if 'historicData' in data:
        print(f"Datos históricos: {len(data['historicData'])} registros")
    if 'kpiData' in data:
        print(f"Datos KPI: {len(data['kpiData'])} registros")

if __name__ == "__main__":
    main()