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

def main():
    """Función principal de la aplicación"""
    parser = argparse.ArgumentParser(description='Genera un cuadro de mando a partir de un archivo Excel')
    parser.add_argument('excel_file', help='Ruta al archivo Excel (e.g., TXplode_v06.xlsm)')
    parser.add_argument('--sheet', '-s', default='Data', help='Nombre de la hoja en Excel (por defecto: Data)')
    parser.add_argument('--template', '-t', default='dashboard_template.html', 
                        help='Plantilla HTML a utilizar (por defecto: dashboard_template.html)')
    parser.add_argument('--output', '-o', default='dashboard_output.html',
                        help='Nombre del archivo HTML de salida (por defecto: dashboard_output.html)')
    parser.add_argument('--open', '-b', action='store_true', help='Abrir el cuadro de mando en el navegador')
    
    args = parser.parse_args()
    
    # Verificar que el archivo Excel existe
    if not os.path.exists(args.excel_file):
        print(f"Error: El archivo {args.excel_file} no existe.")
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
        # Extraer datos del Excel
        print(f"Extrayendo datos de {args.excel_file}, hoja: {args.sheet}...")
        excel_extractor = ExcelDataExtractor(args.excel_file)
        data = excel_extractor.extract_data(args.sheet)
        
        # Procesar los datos
        print("Procesando datos...")
        processor = DataProcessor(data)
        processed_data = processor.process()
        
        # Generar el HTML
        print(f"Generando HTML utilizando la plantilla {template_path}...")
        generator = HtmlGenerator(template_path)
        html_content = generator.generate(processed_data)
        
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

if __name__ == "__main__":
    sys.exit(main())
