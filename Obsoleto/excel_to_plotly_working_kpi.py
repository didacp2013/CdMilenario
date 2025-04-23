#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicación para generar un cuadro de mando a partir de datos en Excel usando Plotly Dash
"""
import argparse
import os
import sys
import webbrowser
import time  # Añadido para usar time.sleep()
from pathlib import Path
from datetime import datetime
import json

# Importar los módulos de nuestra aplicación
# Verificar que los módulos necesarios existen
try:
    from excel_extractor import ExcelDataExtractor
    from data_processor_full import DataProcessor
    from dashboard_plotly_debug import load_data, create_dashboard
    print("Módulos importados correctamente")
except ImportError as e:
    print(f"Error al importar módulos: {e}")
    print("Asegúrate de que todos los archivos necesarios están en el directorio correcto.")
    sys.exit(1)

# Configuración predeterminada específica para tu proyecto
DEFAULT_EXCEL_PATH = "/Users/didac/Downloads/StoryMac/DashBTracker/PruebasCdM/Tchart_V06.xlsm"
DEFAULT_HISTORIC_SHEET = "FrmBB_2"
DEFAULT_KPI_SHEET = "FrmBB_3"

def check_and_kill_process_on_port(port):
    """Verifica si un puerto está en uso y pregunta al usuario si desea cerrar el proceso"""
    import subprocess
    
    # Verificar si el puerto está en uso
    try:
        # Ejecutar lsof para encontrar el proceso que usa el puerto
        result = subprocess.run(['lsof', '-i', f':{port}'], 
                               capture_output=True, text=True)
        
        if result.stdout:
            print(f"Información detallada sobre el proceso que usa el puerto {port}:")
            print(result.stdout)
            
            # Extraer el PID del proceso
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # La primera línea es el encabezado
                parts = lines[1].split()
                if len(parts) > 1:
                    pid = parts[1]
                    
                    # Obtener más información sobre el proceso
                    process_info = subprocess.run(['ps', '-p', pid, '-o', 'pid,ppid,user,%cpu,%mem,command'], 
                                                 capture_output=True, text=True)
                    print("Información detallada del proceso:")
                    print(process_info.stdout)
                    
                    # Preguntar al usuario si desea cerrar el proceso
                    print(f"El puerto {port} está siendo usado por el proceso {pid}")
                    response = input(f"¿Desea cerrar este proceso para liberar el puerto? (s/n): ")
                    
                    if response.lower() in ['s', 'si', 'sí', 'y', 'yes']:
                        # Cerrar el proceso
                        print(f"Intentando terminar el proceso {pid}...")
                        subprocess.run(['kill', '-9', pid])
                        
                        # Verificar si el proceso fue terminado
                        time.sleep(1)  # Esperar un momento para que el proceso termine
                        check = subprocess.run(['ps', '-p', pid], 
                                              capture_output=True, text=True)
                        if "PID" in check.stdout:
                            print(f"¡Advertencia! El proceso {pid} sigue en ejecución.")
                            print("Puede que necesites permisos de administrador para terminarlo.")
                            print("Intenta ejecutar: sudo kill -9 " + pid)
                            return False
                        else:
                            print(f"Proceso {pid} terminado exitosamente.")
                            return True
                    else:
                        print("Continuando sin cerrar el proceso...")
                        return False
            
            print("No se pudo identificar el PID del proceso que usa el puerto.")
            return False
        else:
            print(f"El puerto {port} no parece estar en uso.")
            return True
    except Exception as e:
        print(f"Error al verificar el puerto: {e}")
        return False

def main():
    """Función principal"""
    try:
        # Configurar el parser de argumentos
        parser = argparse.ArgumentParser(description='Genera un cuadro de mando a partir de datos en Excel.')
        parser.add_argument('--excel', type=str, default=DEFAULT_EXCEL_PATH,
                            help=f'Ruta al archivo Excel (default: {DEFAULT_EXCEL_PATH})')
        parser.add_argument('--historic-sheet', type=str, default=DEFAULT_HISTORIC_SHEET,
                            help=f'Nombre de la hoja con datos históricos (default: {DEFAULT_HISTORIC_SHEET})')
        parser.add_argument('--kpi-sheet', type=str, default=DEFAULT_KPI_SHEET,
                            help=f'Nombre de la hoja con datos KPI (default: {DEFAULT_KPI_SHEET})')
        parser.add_argument('--debug', action='store_true',
                            help='Activar modo de depuración para ver información detallada')
        parser.add_argument('--port', type=int, default=8050,
                            help='Puerto específico para iniciar el servidor (opcional)')
        
        # Parsear los argumentos
        args = parser.parse_args()
        
        # Forzar modo debug para diagnóstico
        args.debug = True
        print("Modo debug activado para diagnóstico")
        
        # Verificar que el archivo Excel existe
        if not os.path.isfile(args.excel):
            print(f"Error: El archivo Excel '{args.excel}' no existe.")
            return 1
        
        print(f"=== GENERANDO CUADRO DE MANDO INTERACTIVO CON PLOTLY ===")
        print(f"Archivo Excel: {args.excel}")
        print(f"Hoja de datos históricos: {args.historic_sheet}")
        print(f"Hoja de datos KPI: {args.kpi_sheet}")
        print(f"Modo debug: {'Activado' if args.debug else 'Desactivado'}")
        
        # Cargar datos directamente para verificación
        try:
            print("\nCargando datos originales desde Excel para verificación...")
            extractor = ExcelDataExtractor(args.excel)
            historic_data = extractor.extract_historic_data(args.historic_sheet)
            kpi_data = extractor.extract_kpi_data(args.kpi_sheet)
            
            # Verificar datos KPI originales
            if args.debug:
                print("\n=== VERIFICACIÓN DE DATOS KPI ORIGINALES ===")
                kpi_count = 0
                
                # Verificar los datos KPI originales
                for kpi_record in kpi_data:
                    if kpi_count < 10:  # Mostrar solo los primeros 10 registros
                        print(f"KPI original {kpi_count+1}:")
                        print(f"  CIA: {kpi_record.get('CIA')}")
                        print(f"  PRJID: {kpi_record.get('PRJID')}")
                        print(f"  ROW: {kpi_record.get('ROW')}")
                        print(f"  COLUMN: {kpi_record.get('COLUMN')}")
                        print(f"  KPREV: {kpi_record.get('KPREV')}")
                        print(f"  PDTE: {kpi_record.get('PDTE')}")
                        print(f"  REALPREV: {kpi_record.get('REALPREV')}")
                        print(f"  PPTOPREV: {kpi_record.get('PPTOPREV')}")
                        print()
                    kpi_count += 1
                
                print(f"Total de registros KPI originales: {kpi_count}")
        except Exception as e:
            import traceback
            print(f"Error al cargar datos originales: {e}")
            traceback.print_exc()
        
        # Cargar y procesar los datos con opción de depuración
        try:
            print("\nCargando datos procesados desde Excel...")
            data = load_data(args.excel, args.historic_sheet, args.kpi_sheet, debug=args.debug)
            
            if not data:
                print("Error: No se pudieron cargar los datos.")
                return 1
            
            print("Datos cargados correctamente.")
            
            # Verificar estructura de datos
            print("\n=== VERIFICACIÓN DE ESTRUCTURA DE DATOS ===")
            print(f"Tipo de datos: {type(data)}")
            if isinstance(data, dict):
                print(f"Claves en el diccionario de datos: {list(data.keys())}")
                if 'cellData' in data:
                    print(f"Número de celdas: {len(data['cellData'])}")
                    if data['cellData']:
                        print("Ejemplo de una celda:")
                        cell_key = next(iter(data['cellData']))
                        print(f"Celda {cell_key}: {data['cellData'][cell_key]}")
                        
                        # Verificar si hay ROW y COLUMN en la celda
                        cell_data = data['cellData'][cell_key]
                        if 'ROW' not in cell_data or 'COLUMN' not in cell_data:
                            print("ERROR: La celda no tiene ROW o COLUMN definidos")
                            print("Campos disponibles en la celda:", list(cell_data.keys()))
                            return 1
                else:
                    print("Error: No se encontró la clave 'cellData' en los datos.")
                    return 1
            else:
                print("Error: Los datos no son un diccionario.")
                return 1
            
        except Exception as e:
            import traceback
            print(f"Error al cargar datos: {e}")
            traceback.print_exc()
            return 1
        
        # Verificar datos KPI procesados
        if args.debug:
            print("\n=== VERIFICACIÓN DE DATOS KPI PROCESADOS ===")
            cells_with_kpi = 0
            cells_with_zero_kpi = 0
            
            for cell_key, cell_data in data['cellData'].items():
                # Verificar si la celda tiene datos KPI
                has_kpi = any(k in cell_data for k in ['KPREV', 'PDTE', 'REALPREV', 'PPTOPREV'])
                
                if has_kpi:
                    cells_with_kpi += 1
                    
                    # Verificar si todos los valores KPI son cero
                    all_zeros = all(cell_data.get(k, 0) == 0 for k in ['KPREV', 'PDTE', 'REALPREV', 'PPTOPREV'])
                    
                    if all_zeros:
                        cells_with_zero_kpi += 1
                        print(f"Celda {cell_key} ({cell_data.get('ROW', 'N/A')} - {cell_data.get('COLUMN', 'N/A')}) tiene todos los KPI en cero")
                    else:
                        print(f"Celda {cell_key} ({cell_data.get('ROW', 'N/A')} - {cell_data.get('COLUMN', 'N/A')}):")
                        print(f"  - KPREV: {cell_data.get('KPREV', 'N/A')}")
                        print(f"  - PDTE: {cell_data.get('PDTE', 'N/A')}")
                        print(f"  - REALPREV: {cell_data.get('REALPREV', 'N/A')}")
                        print(f"  - PPTOPREV: {cell_data.get('PPTOPREV', 'N/A')}")
                        print()
            
            print(f"Total de celdas con datos KPI: {cells_with_kpi}")
            print(f"Celdas con todos los KPI en cero: {cells_with_zero_kpi}")
            
            # Guardar datos en un archivo JSON para análisis posterior
            debug_file = os.path.join(os.path.dirname(args.excel), "debug_data.json")
            try:
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"Datos guardados para depuración en: {debug_file}")
            except Exception as e:
                print(f"Error al guardar archivo de depuración: {e}")
        
        # Crear y ejecutar la aplicación Dash
        try:
            print("\nCreando dashboard...")
            app = create_dashboard(data, debug=args.debug)
            
            if app is None:
                print("Error: No se pudo crear la aplicación Dash.")
                return 1
            
            print("Dashboard creado correctamente.")
        except Exception as e:
            import traceback
            print(f"Error al crear dashboard: {e}")
            traceback.print_exc()
            return 1
        
        print("\n=== INICIANDO SERVIDOR DASH ===")
        print("Intentando iniciar en http://127.0.0.1:8050/")
        print("Si ese puerto está ocupado, se intentarán puertos alternativos.")
        print("Presiona Ctrl+C para detener el servidor")
        
        # Intentar ejecutar la aplicación con diferentes puertos si es necesario
        ports_to_try = [8050, 8051, 8052, 8053, 8054]
        
        for port in ports_to_try:
            try:
                print(f"Intentando iniciar en puerto {port}...")
                
                # Verificar si el puerto está en uso y preguntar si se debe cerrar
                if not check_and_kill_process_on_port(port):
                    print(f"Saltando puerto {port}, intentando el siguiente...")
                    continue
                
                # Ejecutar la aplicación con configuración que permita los callbacks
                print(f"Servidor iniciado en http://127.0.0.1:{port}/")
                webbrowser.open(f'http://127.0.0.1:{port}/')
                
                # Usar app.run() en lugar de app.run_server() para compatibilidad con versiones recientes de Dash
                app.run(
                    debug=False,  # Debug mode off to avoid conflicts with debugger
                    dev_tools_hot_reload=True,  # Enable hot reload for component updates
                    dev_tools_ui=True,  # Enable dev tools UI
                    dev_tools_props_check=True,  # Enable props checking
                    host='127.0.0.1', 
                    port=port
                )
                return 0  # Si llegamos aquí, la aplicación se inició correctamente
            except OSError as e:
                if "Address already in use" in str(e):
                    print(f"Puerto {port} ya está en uso, intentando el siguiente...")
                    continue
                else:
                    print(f"Error OSError al iniciar en puerto {port}: {e}")
                    if args.debug:
                        import traceback
                        traceback.print_exc()
                    continue
            except Exception as e:
                print(f"Error al iniciar en puerto {port}: {e}")
                if args.debug:
                    import traceback
                    traceback.print_exc()
                continue
        
        # Si llegamos aquí, todos los puertos estaban ocupados
        print("Error: No se pudo iniciar la aplicación. Todos los puertos están ocupados.")
        return 1
        
    except SystemExit as e:
        # Capturar SystemExit específicamente
        if e.code == 0:
            return 0
        print(f"La aplicación se cerró con código: {e.code}")
        return e.code
    except Exception as e:
        # Mejorar el reporte de errores para obtener más información
        import traceback
        print(f"Error inesperado en la función principal: {e}")
        print("Detalles del error:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        print(f"Programa finalizado con código: {exit_code}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario.")
        sys.exit(0)
    except Exception as e:
        import traceback
        print(f"Error crítico no capturado: {e}")
        traceback.print_exc()
        sys.exit(1)