#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo para cargar datos para el dashboard
"""
import os
import sys
import json
import pandas as pd
from datetime import datetime

# Importar los módulos necesarios
try:
    from excel_extractor import ExcelDataExtractor
    from data_processor_full import DataProcessor
except ImportError as e:
    print(f"Error al importar módulos: {e}")
    sys.exit(1)

def load_data(excel_path=None, historic_sheet=None, kpi_sheet=None, debug=False):
    """
    Carga datos desde un archivo Excel o JSON
    """
    try:
        if debug:
            print("\n=== CARGANDO DATOS ===")
            print(f"Archivo Excel: {excel_path}")
            print(f"Hoja histórica: {historic_sheet}")
            print(f"Hoja KPI: {kpi_sheet}")
        
        # Verificar si se proporcionó un archivo Excel
        if not excel_path:
            print("No se especificó archivo Excel")
            return None
        
        # Asegurar que no se abran puertos durante la carga de datos
        # Este archivo solo debe manejar la lectura y procesamiento de datos
        
        # Cargar datos desde Excel
        extractor = ExcelDataExtractor(excel_path)
        
        # Extraer datos históricos
        if historic_sheet:
            historic_data = extractor.extract_historic_data(historic_sheet)
            if debug:
                print(f"Datos históricos extraídos: {len(historic_data)} registros")
                # Mostrar los primeros registros para depuración
                for i, record in enumerate(historic_data[:3]):
                    print(f"Registro histórico {i+1}:")
                    for key, value in record.items():
                        print(f"  {key}: {value}")
                    print()
        else:
            historic_data = []
            if debug:
                print("No se especificó hoja de datos históricos")
        
        # Extraer datos KPI
        if kpi_sheet:
            kpi_data = extractor.extract_kpi_data(kpi_sheet)
            if kpi_data is None:
                kpi_data = []
            print(f"Datos KPI extraídos: {len(kpi_data)} registros")
            if debug:
                print("No se especificó hoja de datos KPI")
        
        # Procesar los datos
        if debug:
            print("\n=== PROCESANDO DATOS ===")
        
        processor = DataProcessor(historic_data, kpi_data)
        processed_data = processor.process_data(debug=debug)
        
        # Establecer hasHistoric para todas las celdas con datos históricos
        if processed_data and 'cellData' in processed_data:
            cells_with_historic = 0
            for cell_key, cell_data in processed_data['cellData'].items():
                # Verificar si hay datos históricos en timeSeries
                if 'timeSeries' in cell_data and len(cell_data['timeSeries']) > 0:
                    cell_data['hasHistoric'] = True
                    cells_with_historic += 1
                # También verificar historicData para compatibilidad
                elif 'historicData' in cell_data and len(cell_data['historicData']) > 0:
                    cell_data['hasHistoric'] = True
                    cells_with_historic += 1
        
        if debug:
            print("\n=== DATOS PROCESADOS ===")
            print(f"Estructura de datos procesada:")
            print(f"  Claves principales: {list(processed_data.keys())}")
            print(f"  Número de celdas: {len(processed_data.get('cellData', {}))}")
            
            # Corregir la verificación de datos históricos
            cells_with_historic = 0
            for cell_key, cell_data in processed_data.get('cellData', {}).items():
                if 'timeSeries' in cell_data and len(cell_data.get('timeSeries', [])) > 0:
                    cells_with_historic += 1
                elif 'historicData' in cell_data and len(cell_data.get('historicData', [])) > 0:
                    cells_with_historic += 1
            
            print(f"  Celdas con datos históricos: {cells_with_historic}")
            
            # Mostrar información sobre hasHistoric
            cells_with_hashistoric = sum(1 for cell in processed_data.get('cellData', {}).values() 
                                       if cell.get('hasHistoric', False))
            print(f"  Celdas con hasHistoric=True: {cells_with_hashistoric}")
        
        return processed_data
        
    except Exception as e:
        import traceback
        print(f"Error al cargar datos desde Excel: {e}")
        traceback.print_exc()
        return None