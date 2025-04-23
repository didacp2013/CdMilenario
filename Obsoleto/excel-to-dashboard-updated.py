#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Aplicación para generar un cuadro de mando a partir de datos en Excel
"""
import argparse
import os
import sys
import webbrowser
from pathlib import Path

# Importar los módulos de nuestra aplicación
from excel_extractor import ExcelDataExtractor
from data_processor import DataProcessor
from html_generator import HtmlGenerator

# Configuración predeterminada específica para tu proyecto
DEFAULT_EXCEL_PATH = "/Users/didac/Downloads/StoryMac/DashBTracker/PrjDB_31200_4.xlsm"
DEFAULT_HISTORIC_SHEET = "FrmBB_2"
DEFAULT_KPI_SHEET = "FrmBB_3"
DEFAULT_OUTPUT_HTML = "dashboard_output.html"
DEFAULT_TEMPLATE = "dashboard_template.html"

def main():
    """Función principal de la aplicación"""
    parser = argparse.ArgumentParser(description='Genera un cuadro de mando a partir de un archivo Excel')
    parser.add_argument('--excel', '-e', default=DEFAULT_EXCEL_PATH, 
                      help=f'Ruta al archivo Excel (por defecto: {DEFAULT_EXCEL_PATH})')
    parser.add_argument('--historic', '-h', default=DEFAULT_HISTORIC_SHEET, 
                      help=f'Nombre de la hoja con datos históricos (por defecto: {DEFAULT_HISTORIC_SHEET})')
    parser.add_argument('--kpi', '-k', default=DEFAULT_KPI_SHEET, 
                      help=f'Nombre de la hoja con datos de KPIs (por defecto: {DEFAULT_KPI_SHEET})')
    parser.add_argument('--template', '-t', default=DEFAULT_TEMPLATE, 
                      help=f'Plantilla HTML a utilizar (por defecto: {DEFAULT_TEMPLATE})')
    parser.add_argument('--output', '-o', default=DEFAULT_OUTPUT_HTML,
                      help=f'Nombre del archivo HTML de salida (por defecto: {DEFAULT_OUTPUT_HTML})')
    parser.add_argument('--open', '-b', action='store_true', help='Abrir el cuadro de mando en el navegador')
    
    args = parser.parse_args()
    
    # Verificar que el archivo Excel existe
    if not os.path.exists(args.excel):
        print(f"Error: El archivo {args.excel} no existe.")
        sys.exit(1)
    
    # Verificar que la plantilla HTML existe
    template_path = args.template
    if not os.path.exists(template_path):
        # Buscar en el directorio de la aplicación
        app_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(app_dir, args.template)
        if not os.path.exists(template_path):
            print(f"Error: La plantilla HTML {args.template} no existe.")
            sys.exit(1)
    
    try:
        # Extraer datos históricos del Excel
        print(f"Extrayendo datos históricos de {args.excel}, hoja: {args.historic}...")
        excel_extractor = ExcelDataExtractor(args.excel)
        historic_data = excel_extractor.extract_data(args.historic)
        
        # Extraer datos de KPIs del Excel
        print(f"Extrayendo datos de KPIs de {args.excel}, hoja: {args.kpi}...")
        kpi_data = excel_extractor.extract_data(args.kpi)
        
        # Procesar los datos históricos
        print("Procesando datos históricos...")
        historic_processor = DataProcessor(historic_data)
        historic_processed = historic_processor.process()
        
        # Procesar los datos de KPIs
        print("Procesando datos de KPIs...")
        kpi_processor = DataProcessor(kpi_data)
        kpi_processed = kpi_processor.process()
        
        # Combinar los datos procesados
        print("Combinando datos históricos y KPIs...")
        combined_data = combine_data(historic_processed, kpi_processed)
        
        # Generar el HTML
        print(f"Generando HTML utilizando la plantilla {template_path}...")
        generator = HtmlGenerator(template_path)
        html_content = generator.generate(combined_data)
        
        # Guardar el HTML generado
        output_path = args.output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Cuadro de mando generado correctamente: {output_path}")
        
        # Abrir en el navegador si se solicitó
        if args.open:
            # Convertir a ruta absoluta
            abs_path = os.path.abspath(output_path)
            url = f"file://{abs_path}"
            print(f"Abriendo en el navegador: {url}")
            webbrowser.open(url)
        
        return 0  # Éxito
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1  # Error

def combine_data(historic_data, kpi_data):
    """
    Combina los datos históricos y los datos de KPIs
    
    Args:
        historic_data (dict): Datos históricos procesados
        kpi_data (dict): Datos de KPIs procesados
        
    Returns:
        dict: Datos combinados
    """
    # Crear una copia de los datos históricos para no modificarlos directamente
    combined = historic_data.copy()
    
    # Agregar una marca de que los datos contienen KPIs
    combined['hasKpis'] = True
    
    # Añadir los datos de KPIs
    combined['kpiData'] = kpi_data.get('cellData', {})
    
    # Procesar cada celda para integrar los KPIs
    for key, cell in combined['cellData'].items():
        # Buscar el KPI correspondiente
        if key in combined['kpiData']:
            kpi_cell = combined['kpiData'][key]
            
            # Añadir datos de KPI a la celda
            cell['kpis'] = {
                'prevValue': kpi_cell.get('prevValue', 0),  # Valor de Previsión en €
                'realPrevPercent': kpi_cell.get('realPrevPercent', 0),  # % REAL/PREV
                'pptoPrevPercent': kpi_cell.get('pptoPrevPercent', 0),  # % PPTO/PREV
                'pendingValue': kpi_cell.get('pendingValue', 0)  # REAL-PREVISIÓN en €
            }
    
    return combined

if __name__ == "__main__":
    sys.exit(main())
