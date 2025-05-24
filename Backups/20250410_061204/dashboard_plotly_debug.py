#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo para crear un dashboard interactivo con Plotly y Dash
Versión con capacidades de depuración mejoradas
"""
import os
import sys
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
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
        
        # Cargar datos desde Excel
        extractor = ExcelDataExtractor(excel_path)
        
        # Extraer datos históricos
        if historic_sheet:
            historic_data = extractor.extract_historic_data(historic_sheet)
            if debug:
                print(f"Datos históricos extraídos: {len(historic_data)} registros")
        else:
            historic_data = []
            if debug:
                print("No se especificó hoja de datos históricos")
        
        # Extraer datos KPI
        if kpi_sheet:
            kpi_data = extractor.extract_kpi_data(kpi_sheet)
            if debug:
                print(f"Datos KPI extraídos: {len(kpi_data)} registros")
        else:
            kpi_data = []
            if debug:
                print("No se especificó hoja de datos KPI")
        
        # Procesar los datos
        if debug:
            print("\n=== PROCESANDO DATOS ===")
        
        processor = DataProcessor(historic_data, kpi_data)
        processed_data = processor.process_data(debug=debug)
        
        if debug:
            print("\n=== DATOS PROCESADOS ===")
            print(f"Estructura de datos procesada:")
            print(f"  Claves principales: {list(processed_data.keys())}")
            print(f"  Número de celdas: {len(processed_data.get('cellData', {}))}")
            
            # Verificar datos históricos
            cells_with_historic = 0
            for cell_key, cell_data in processed_data['cellData'].items():
                if cell_data.get('hasHistoric', False):
                    cells_with_historic += 1
            
            print(f"  Celdas con datos históricos: {cells_with_historic}")
        
        # Guardar los datos procesados en un archivo JSON
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        json_filename = f"dashboard_data_{timestamp}.json"
        
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
                if debug:
                    print(f"Datos guardados en: {json_filename}")
        except Exception as e:
            if debug:
                print(f"Error al guardar datos en JSON: {e}")
                import traceback
                traceback.print_exc()
        
        return processed_data
        
    except Exception as e:
        import traceback
        print(f"Error al cargar datos desde Excel: {e}")
        traceback.print_exc()
        return None

def create_dashboard(data, debug=False):
    """
    Crea un dashboard interactivo con Dash
    """
    if not data or 'cellData' not in data:
        print("Error: Datos inválidos para crear el dashboard")
        return None
    
    # Inicializar la aplicación Dash con tema Bootstrap
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    # Extraer valores únicos para los filtros
    cias = sorted(list(set(cell.get('CIA') for cell in data['cellData'].values() if 'CIA' in cell and cell['CIA'])))
    prjids = sorted(list(set(cell.get('PRJID') for cell in data['cellData'].values() if 'PRJID' in cell and cell['PRJID'])))
    
    # Definir el layout de la aplicación
    app.layout = html.Div([
        # Encabezado
        html.Div([
            html.H1("Dashboard de Seguimiento", style={'textAlign': 'center'}),
            html.Div(id='last-update-time', style={'textAlign': 'center', 'marginBottom': '10px'}),
            
            # Controles y filtros
            html.Div([
                # Fila para controles principales
                dbc.Row([
                    # Botón de actualización
                    dbc.Col(
                        html.Button('Actualizar Datos', id='refresh-button', n_clicks=0,
                                   style={'margin': '10px', 'padding': '10px 20px', 'backgroundColor': '#4CAF50', 
                                          'color': 'white', 'border': 'none', 'borderRadius': '5px'}),
                        width={"size": 3}
                    ),
                    
                    # Selector de tipo de visualización
                    dbc.Col(
                        html.Div([
                            html.Label("Tipo de visualización:"),
                            dcc.RadioItems(
                                id='visualization-type',
                                options=[
                                    {'label': 'KPI', 'value': 'kpi'},
                                    {'label': 'Histórico', 'value': 'historic'}
                                ],
                                value='kpi',  # Default to KPI view
                                labelStyle={'display': 'inline-block', 'margin-right': '20px'}
                            ),
                        ], style={'padding': '10px'}),
                        width={"size": 4}
                    ),
                    
                    # Filtros
                    dbc.Col(
                        html.Div([
                            html.Label("Filtros:"),
                            dbc.Row([
                                dbc.Col(
                                    dcc.Dropdown(
                                        id='cia-filter',
                                        options=[{'label': cia, 'value': cia} for cia in cias],
                                        placeholder="Filtrar por CIA",
                                        multi=True
                                    ),
                                    width=6
                                ),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id='prjid-filter',
                                        options=[{'label': prjid, 'value': prjid} for prjid in prjids],
                                        placeholder="Filtrar por PRJID",
                                        multi=True
                                    ),
                                    width=6
                                )
                            ])
                        ], style={'padding': '10px'}),
                        width={"size": 5}
                    )
                ], className="mb-4")
            ]),
            
            # Contenedor para gráficos
            html.Div([
                # Área de visualización principal
                html.Div(id='main-content')
            ]),
            
            # Almacenamiento de datos para actualización
            dcc.Store(id='dashboard-data', data=data),
            dcc.Store(id='filtered-data', data=data),  # Para almacenar datos filtrados
            dcc.Store(id='refresh-timestamp', data=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        ])
    ])
    
    # Callback para actualizar el timestamp cuando se hace clic en el botón de actualización
    @app.callback(
        [Output('dashboard-data', 'data'),
         Output('refresh-timestamp', 'data'),
         Output('last-update-time', 'children')],
        [Input('refresh-button', 'n_clicks')],
        [State('dashboard-data', 'data')]
    )
    def refresh_data(n_clicks, current_data):
        if n_clicks == 0:
            # Primera carga, usar los datos iniciales
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return current_data, timestamp, f"Última actualización: {timestamp}"
        
        # Intentar recargar los datos desde el archivo Excel
        try:
            # Asegúrate de que al principio del archivo estén estas importaciones
            import sys
            import os
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
            
            # Usar las mismas rutas que en excel_to_plotly.py
            excel_path = "/Users/didac/Downloads/StoryMac/DashBTracker/PruebasCdM/Tchart_V06.xlsm"
            historic_sheet = "FrmBB_2"
            kpi_sheet = "FrmBB_3"
            
            # Cargar datos nuevamente
            extractor = ExcelDataExtractor(excel_path)
            historic_data = extractor.extract_historic_data(historic_sheet)
            kpi_data = extractor.extract_kpi_data(kpi_sheet)
            
            processor = DataProcessor(historic_data, kpi_data)
            new_data = processor.process_data(debug=debug)
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return new_data, timestamp, f"Última actualización: {timestamp}"
        except Exception as e:
            import traceback
            print(f"Error al actualizar datos: {e}")
            traceback.print_exc()
            
            # En caso de error, mantener los datos actuales
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return current_data, timestamp, f"Error en actualización: {timestamp}"
    
    # Callback para aplicar filtros
    @app.callback(
        Output('filtered-data', 'data'),
        [Input('dashboard-data', 'data'),
         Input('cia-filter', 'value'),
         Input('prjid-filter', 'value')]
    )
    def filter_data(data, cia_filter, prjid_filter):
        if not data or 'cellData' not in data:
            return data
        
        # Si no hay filtros activos, devolver todos los datos
        if not cia_filter and not prjid_filter:
            return data
        
        # Crear una copia de los datos para no modificar los originales
        filtered_data = {'cellData': {}}
        
        # Aplicar filtros
        for cell_key, cell_data in data['cellData'].items():
            # Verificar filtro de CIA
            cia_match = True
            if cia_filter and 'CIA' in cell_data:
                cia_match = cell_data['CIA'] in cia_filter
            
            # Verificar filtro de PRJID
            prjid_match = True
            if prjid_filter and 'PRJID' in cell_data:
                prjid_match = cell_data['PRJID'] in prjid_filter
            
            # Si pasa ambos filtros, incluir en los datos filtrados
            if cia_match and prjid_match:
                filtered_data['cellData'][cell_key] = cell_data
        
        return filtered_data
    
    # Callback para actualizar el contenido principal
    @app.callback(
        Output('main-content', 'children'),
        [Input('visualization-type', 'value'),
         Input('filtered-data', 'data')]
    )
    def update_main_content(viz_type, data):
        if viz_type == 'kpi':
            return create_kpi_view(data)
        else:  # historic
            return create_historic_view(data)
    
    # Inicializar el contenido
    if debug:
        print("Dashboard creado correctamente")
    
    return app

def create_current_view(data, selected_rows, selected_columns, debug=False):
    """Crea la vista de valores actuales en tarjetas"""
    if debug:
        print("\n=== CREANDO VISTA DE VALORES ACTUALES ===")
        print(f"Filas seleccionadas: {selected_rows}")
        print(f"Columnas seleccionadas: {selected_columns}")
    
    cards = []
    
    # Crear una tarjeta para cada celda seleccionada
    for row in selected_rows:
        for column in selected_columns:
            # Buscar la celda en los datos
            cell_key = f"{row}_{column}"
            cell_data = None
            
            # Buscar en cellData
            for key, value in data['cellData'].items():
                if value.get('ROW') == row and value.get('COLUMN') == column:
                    cell_data = value
                    break
            
            if cell_data:
                if debug:
                    print(f"Procesando celda: {row} - {column}")
                    print(f"  Datos disponibles: {list(cell_data.keys())}")
                
                # Obtener el valor actual
                value = cell_data.get('VALUE')
                
                # Determinar si es un valor positivo o negativo para el estilo
                value_class = ""
                if value is not None:
                    try:
                        num_value = float(value)
                        if num_value > 0:
                            value_class = "positive-value"
                        elif num_value < 0:
                            value_class = "negative-value"
                    except (ValueError, TypeError):
                        pass
                
                # Formatear el valor para mostrar
                display_value = value
                if value is not None:
                    try:
                        num_value = float(value)
                        # Formatear números con separador de miles y 2 decimales
                        display_value = f"{num_value:,.2f}"
                    except (ValueError, TypeError):
                        pass
                
                # Crear el contenido de la tarjeta
                card_content = [
                    html.H5(f"{row}: {column}", className="card-title"),
                    html.Hr(),
                    html.H3(
                        display_value if display_value is not None else "N/A",
                        className=f"card-text text-center {value_class}"
                    ),
                ]
                
                # Añadir botón para ver histórico si hay datos disponibles
                if cell_data.get('hasHistoric', False):
                    card_content.append(
                        html.Div([
                            html.Hr(),
                            dbc.Button(
                                "Ver Histórico",
                                id=f"btn-historic-{cell_key}",
                                color="primary",
                                size="sm",
                                className="mt-2"
                            ),
                        ], className="text-center")
                    )
                
                # Crear la tarjeta
                card = dbc.Col([
                    dbc.Card([
                        dbc.CardBody(card_content)
                    ], className="h-100")
                ], width=12, md=6, lg=4, className="mb-4")
                
                cards.append(card)
    
    # Si no hay tarjetas para mostrar
    if not cards:
        if debug:
            print("No se encontraron datos para mostrar en la vista actual")
        # Return a tuple with empty list and info message
        return [], "No hay datos disponibles para la selección actual."
    
    if debug:
        print(f"Se generaron {len(cards)} tarjetas para la vista actual")
    
    # Return cards and info message about number of cards
    return cards, f"Mostrando {len(cards)} elementos"

def create_historic_view(data, debug=False):
    """
    Crea la vista de datos históricos
    """
    if debug:
        print("=== DEBUG: Creando vista de históricos ===")
        print(f"Tipo de datos recibidos: {type(data)}")
        if isinstance(data, dict) and 'cellData' in data:
            print(f"Número total de celdas: {len(data['cellData'])}")
            
            # Contar celdas con datos históricos
            historic_cells = {k: v for k, v in data['cellData'].items() 
                             if v.get('hasHistoric', False) and 'timeSeries' in v and v['timeSeries']}
            print(f"Número de celdas con datos históricos: {len(historic_cells)}")
            
            # Mostrar ejemplo de celda con histórico si existe
            if historic_cells:
                cell_key = next(iter(historic_cells))
                print(f"Ejemplo de celda con histórico ({cell_key}):")
                cell = historic_cells[cell_key]
                print(f"  ROW: {cell.get('ROW')}, COLUMN: {cell.get('COLUMN')}")
                print(f"  hasHistoric: {cell.get('hasHistoric')}")
                print(f"  Número de puntos en timeSeries: {len(cell.get('timeSeries', []))}")
                if cell.get('timeSeries'):
                    print(f"  Primer punto de la serie: {cell['timeSeries'][0]}")
    
    if not data or 'cellData' not in data:
        if debug:
            print("ERROR: No hay datos o no tienen la estructura esperada")
        return html.Div("No hay datos históricos disponibles", style={'padding': '20px', 'textAlign': 'center'})
    
    # Filtrar solo las celdas que tienen datos históricos
    historic_cells = {k: v for k, v in data['cellData'].items() 
                     if v.get('hasHistoric', False) and 'timeSeries' in v and v['timeSeries']}
    
    if not historic_cells:
        if debug:
            print("ERROR: No se encontraron celdas con datos históricos")
        return html.Div("No se encontraron datos históricos en las celdas", style={'padding': '20px', 'textAlign': 'center'})
    
    # Crear un contenedor para los gráficos históricos
    historic_graphs = []
    
    # Crear un gráfico para cada celda con datos históricos
    for cell_key, cell_data in historic_cells.items():
        try:
            row = cell_data.get('ROW', 'N/A')
            column = cell_data.get('COLUMN', 'N/A')
            cia = cell_data.get('CIA', 'N/A')
            prjid = cell_data.get('PRJID', 'N/A')
            
            # Verificar que hay datos en la serie temporal
            time_series = cell_data.get('timeSeries', [])
            if not time_series:
                if debug:
                    print(f"Celda {cell_key} tiene hasHistoric=True pero no tiene datos en timeSeries")
                continue
            
            # Extraer datos para el gráfico
            periods = [point.get('period', '') for point in time_series]
            real_values = [point.get('real', 0) for point in time_series]
            ppto_values = [point.get('ppto', 0) for point in time_series]
            prev_values = [point.get('prev', 0) for point in time_series]
            
            if debug:
                print(f"Creando gráfico para celda {cell_key} ({row}, {column})")
                print(f"  Periodos: {periods}")
                print(f"  Valores reales: {real_values}")
                print(f"  Valores presupuesto: {ppto_values}")
                print(f"  Valores previsión: {prev_values}")
            
            # Crear el gráfico
            fig = go.Figure()
            
            # Añadir líneas para cada serie
            fig.add_trace(go.Scatter(
                x=periods, y=real_values,
                mode='lines+markers',
                name='Real',
                line=dict(color='blue', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=periods, y=ppto_values,
                mode='lines+markers',
                name='Presupuesto',
                line=dict(color='green', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=periods, y=prev_values,
                mode='lines+markers',
                name='Previsión',
                line=dict(color='red', width=2)
            ))
            
            # Configurar el diseño del gráfico
            fig.update_layout(
                title=f'Histórico: {cia} - {prjid} ({row}, {column})',
                xaxis_title='Periodo',
                yaxis_title='Valor',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                margin=dict(l=40, r=40, t=60, b=40),
                height=300
            )
            
            # Añadir el gráfico al contenedor
            historic_graphs.append(
                html.Div([
                    dcc.Graph(
                        id=f'historic-graph-{cell_key}',
                        figure=fig
                    )
                ], style={'margin': '10px', 'border': '1px solid #ddd', 'borderRadius': '5px', 'padding': '10px'})
            )
        except Exception as e:
            if debug:
                import traceback
                print(f"Error al crear gráfico para celda {cell_key}: {e}")
                traceback.print_exc()
    
    # Si no hay gráficos, mostrar un mensaje
    if not historic_graphs:
        if debug:
            print("ERROR: No se pudieron generar gráficos históricos")
        return html.Div("No se pudieron generar gráficos históricos con los datos disponibles", 
                       style={'padding': '20px', 'textAlign': 'center'})
    
    if debug:
        print(f"Se generaron {len(historic_graphs)} gráficos históricos correctamente")
    
    # Devolver el contenedor con todos los gráficos
    return html.Div([
        html.H3("Visualización de Datos Históricos", style={'textAlign': 'center'}),
        html.Div(historic_graphs, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'})
    ])

def check_and_kill_process_on_port(port):
    """Verifica si un puerto está en uso y trata de liberar el proceso"""
    import socket
    import os
    import platform
    import subprocess
    
    # Verificar si el puerto está en uso
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    
    if result == 0:  # Puerto en uso
        print(f"El puerto {port} está en uso. Intentando liberar...")
        
        # En macOS, usar lsof para encontrar el PID
        try:
            # Obtener el PID del proceso que usa el puerto
            cmd = f"lsof -i tcp:{port} -t"
            pid = subprocess.check_output(cmd, shell=True).decode().strip()
            
            if pid:
                print(f"Proceso encontrado con PID: {pid}")
                # Intentar matar el proceso
                os.system(f"kill -9 {pid}")
                print(f"Se ha intentado terminar el proceso {pid}")
                
                # Verificar nuevamente si el puerto está libre
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()
                
                if result != 0:
                    print(f"Puerto {port} liberado correctamente")
                    return True
                else:
                    print(f"No se pudo liberar el puerto {port}")
                    return False
            else:
                print(f"No se encontró ningún proceso usando el puerto {port}")
                return False
        except Exception as e:
            print(f"Error al intentar liberar el puerto: {e}")
            return False
    else:
        # Puerto libre
        return True

def main():
    """Función principal"""
    import argparse
    
    # Configurar el parser de argumentos
    parser = argparse.ArgumentParser(description='Genera un dashboard interactivo a partir de datos en Excel o JSON.')
    parser.add_argument('--excel', type=str, default=None,
                        help='Ruta al archivo Excel (opcional)')
    parser.add_argument('--historic-sheet', type=str, default=None,
                        help='Nombre de la hoja con datos históricos (opcional)')
    parser.add_argument('--kpi-sheet', type=str, default=None,
                        help='Nombre de la hoja con datos KPI (opcional)')
    parser.add_argument('--debug', action='store_true',
                        help='Activar modo de depuración para ver información detallada')
    parser.add_argument('--port', type=int, default=8050,
                        help='Puerto específico para iniciar el servidor (opcional)')
    
    # Parsear los argumentos
    args = parser.parse_args()
    
    # Mostrar información de inicio
    print("\n=== DASHBOARD INTERACTIVO CON PLOTLY Y DASH ===")
    print(f"Modo debug: {'Activado' if args.debug else 'Desactivado'}")
    
    # Verificar si el puerto está en uso
    port_available = check_and_kill_process_on_port(args.port)
    if not port_available:
        print(f"El puerto {args.port} sigue en uso. Intentando con otro puerto...")
        # Intentar con otro puerto
        args.port = 8051
        port_available = check_and_kill_process_on_port(args.port)
        if not port_available:
            print(f"El puerto {args.port} también está en uso.")
            print("Por favor, cierra manualmente los procesos que están usando estos puertos.")
            return 1
    
    # Cargar datos
    data = load_data(args.excel, args.historic_sheet, args.kpi_sheet, debug=args.debug)
    
    if not data:
        print("Error: No se pudieron cargar los datos.")
        return 1
    
    # Crear el dashboard
    app = create_dashboard(data, debug=args.debug)
    
    if not app:
        print("Error: No se pudo crear el dashboard.")
        return 1
    
    # Iniciar el servidor
    print(f"\n=== INICIANDO SERVIDOR EN PUERTO {args.port} ===")
    print("Abriendo navegador web...")
    
    # Abrir el navegador automáticamente
    import webbrowser
    import threading
    import time
    
    def open_browser():
        """Abre el navegador después de un breve retraso"""
        time.sleep(1)
        webbrowser.open_new(f"http://127.0.0.1:{args.port}")
    
    # Iniciar el navegador en un hilo separado
    threading.Thread(target=open_browser).start()
    
    # Iniciar el servidor
    app.run_server(debug=args.debug, port=args.port)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())


def create_kpi_view(data):
    """
    Crea la vista de KPIs con estructura de etiquetas y celdas
    """
    if not data or 'cellData' not in data:
        return html.Div("No hay datos KPI disponibles", style={'padding': '20px', 'textAlign': 'center'})
    
    # Obtener todas las filas y columnas únicas
    rows = sorted(list(set(cell.get('ROW') for cell in data['cellData'].values() if 'ROW' in cell)))
    columns = sorted(list(set(cell.get('COLUMN') for cell in data['cellData'].values() if 'COLUMN' in cell)))
    
    if not rows or not columns:
        return html.Div("No se encontraron datos de filas y columnas para mostrar", 
                       style={'padding': '20px', 'textAlign': 'center'})
    
    # Crear un diccionario para acceder rápidamente a los datos de cada celda
    cell_lookup = {}
    for cell_key, cell_data in data['cellData'].items():
        if 'ROW' in cell_data and 'COLUMN' in cell_data:
            row = cell_data['ROW']
            column = cell_data['COLUMN']
            cell_lookup[(row, column)] = cell_data
    
    # Crear la tabla con etiquetas de fila y columna
    table_header = [html.Thead(html.Tr([html.Th("")] + [html.Th(col) for col in columns]))]
    
    table_rows = []
    for row in rows:
        # Crear una fila con la etiqueta de fila y las celdas
        cells = [html.Td(row, style={'fontWeight': 'bold'})]  # Etiqueta de fila
        
        for col in columns:
            # Buscar datos para esta celda
            cell_data = cell_lookup.get((row, col), {})
            
            # Verificar si hay datos KPI
            has_kpi = any(k in cell_data for k in ['KPREV', 'PDTE', 'REALPREV', 'PPTOPREV'])
            
            if has_kpi:
                # Crear el contenido de la celda con los valores KPI
                kprev = cell_data.get('KPREV', 0)
                pdte = cell_data.get('PDTE', 0)
                realprev = cell_data.get('REALPREV', 0)
                pptoprev = cell_data.get('PPTOPREV', 0)
                
                # Determinar el color de fondo según los valores
                bg_color = '#ffffff'  # Blanco por defecto
                
                # Aplicar lógica de colores según los valores
                if kprev is not None and kprev != 0:
                    if kprev > 0:
                        bg_color = '#d4edda'  # Verde claro para valores positivos
                    else:
                        bg_color = '#f8d7da'  # Rojo claro para valores negativos
                
                # Crear el contenido de la celda
                cell_content = html.Div([
                    html.Div([
                        html.Span("K.Prev: ", style={'fontWeight': 'bold'}),
                        html.Span(f"{kprev}")
                    ]),
                    html.Div([
                        html.Span("Pdte: ", style={'fontWeight': 'bold'}),
                        html.Span(f"{pdte}")
                    ]),
                    html.Div([
                        html.Span("Real/Prev: ", style={'fontWeight': 'bold'}),
                        html.Span(f"{realprev}")
                    ]),
                    html.Div([
                        html.Span("Ppto/Prev: ", style={'fontWeight': 'bold'}),
                        html.Span(f"{pptoprev}")
                    ])
                ], style={'padding': '5px'})
                
                # Añadir la celda a la fila
                cells.append(html.Td(cell_content, style={'backgroundColor': bg_color, 'border': '1px solid #dee2e6'}))
            else:
                # Celda vacía
                cells.append(html.Td("", style={'border': '1px solid #dee2e6'}))
        
        # Añadir la fila a la tabla
        table_rows.append(html.Tr(cells))
    
    table_body = [html.Tbody(table_rows)]
    
    if not table_rows:
        return html.Div("No se encontraron datos KPI para mostrar", style={'padding': '20px', 'textAlign': 'center'})
    
    return html.Div([
        html.H3("Visualización de KPIs", style={'textAlign': 'center'}),
        html.Div([
            dbc.Table(
                table_header + table_body, 
                bordered=True, 
                hover=True, 
                responsive=True,
                style={'width': '100%', 'tableLayout': 'fixed'}
            )
        ], style={'overflowX': 'auto'})
    ])