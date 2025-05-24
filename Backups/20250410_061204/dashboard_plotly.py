#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo para crear un dashboard interactivo con Plotly y Dash
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

def load_data(excel_path=None, historic_sheet=None, kpi_sheet=None, debug=False):
    """Carga los datos desde el archivo Excel o desde un archivo JSON guardado"""
    import json
    import os
    from pathlib import Path
    
    # Si no se proporciona una ruta de Excel, intentar cargar desde JSON
    if not excel_path:
        # Buscar archivos JSON en el directorio actual
        json_files = list(Path('.').glob('dashboard_data_*.json'))
        
        if not json_files:
            print("Error: No se encontraron archivos de datos JSON.")
            return None
        
        # Usar el archivo JSON más reciente
        latest_json = max(json_files, key=os.path.getmtime)
        
        try:
            with open(latest_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"Datos cargados desde: {latest_json}")
                return data
        except Exception as e:
            print(f"Error al cargar datos desde JSON: {e}")
            return None
    
    # Si se proporciona una ruta de Excel, extraer y procesar los datos
    try:
        from excel_extractor import ExcelDataExtractor
        from data_processor_full import DataProcessor
        
        # Extraer datos del Excel
        if debug:
            print("\n=== EXTRAYENDO DATOS DEL EXCEL ===")
        
        extractor = ExcelDataExtractor(excel_path)
        
        # Extraer datos históricos
        if historic_sheet:
            if debug:
                print(f"Extrayendo datos históricos de la hoja: {historic_sheet}")
            historic_data = extractor.extract_historic_data(historic_sheet)
        else:
            historic_data = None
            
        # Extraer datos KPI
        if kpi_sheet:
            if debug:
                print(f"Extrayendo datos KPI de la hoja: {kpi_sheet}")
            kpi_data = extractor.extract_kpi_data(kpi_sheet)
        else:
            kpi_data = None
        
        # Procesar los datos
        if debug:
            print("\n=== PROCESANDO DATOS ===")
        
        processor = DataProcessor(historic_data, kpi_data)
        processed_data = processor.process_data(debug=debug)
        
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
        
        return processed_data
        
    except Exception as e:
        import traceback
        print(f"Error al cargar datos desde Excel: {e}")
        traceback.print_exc()
        return None

def create_dashboard(data, debug=False):
    """Crea la aplicación Dash con el dashboard"""
    if debug:
        print("Creando dashboard con modo de depuración activado")
        
    # Verificar que los datos son válidos
    if not data or not isinstance(data, dict) or 'cellData' not in data:
        print("Error: Datos inválidos para crear el dashboard.")
        return None
    
    # Extraer filas y columnas
    rows = data.get('rows', [])
    columns = data.get('columns', [])
    
    if not rows or not columns:
        print("Error: No hay filas o columnas definidas en los datos.")
        return None
    
    # Crear la aplicación Dash
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    # Definir el layout
    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("Dashboard de Indicadores", className="text-center mb-4"),
                html.Hr(),
            ], width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Filtros"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Seleccionar Filas:"),
                                dcc.Dropdown(
                                    id='row-filter',
                                    options=[{'label': row, 'value': row} for row in rows],
                                    value=rows,
                                    multi=True
                                ),
                            ], width=12, md=6),
                            dbc.Col([
                                html.Label("Seleccionar Columnas:"),
                                dcc.Dropdown(
                                    id='column-filter',
                                    options=[{'label': col, 'value': col} for col in columns],
                                    value=columns,
                                    multi=True
                                ),
                            ], width=12, md=6),
                        ]),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Modo de Visualización:"),
                                dbc.RadioItems(
                                    id='view-mode',
                                    options=[
                                        {'label': 'Valores Actuales', 'value': 'current'},
                                        {'label': 'Datos Históricos', 'value': 'historic'}
                                    ],
                                    value='current',
                                    inline=True,
                                    className="mt-2"
                                ),
                            ], width=12, md=6),
                            dbc.Col([
                                html.Div(id='info-message', className="mt-3 text-info"),
                            ], width=12, md=6),
                        ], className="mt-3"),
                    ]),
                ], className="mb-4"),
            ], width=12),
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Spinner(
                    html.Div(id='dashboard-content', className="mt-4"),
                    color="primary",
                ),
            ], width=12),
        ]),
        
        # Añadir un footer con información
        dbc.Row([
            dbc.Col([
                html.Hr(),
                html.Footer([
                    html.P("Dashboard generado con Plotly y Dash", className="text-center text-muted"),
                    html.P([
                        html.Span("Leyenda: "),
                        html.Span(className="legend-positive", style={"display": "inline-block", "width": "20px", "height": "20px", "marginRight": "5px"}),
                        html.Span("Costes/Gastos", style={"marginRight": "15px"}),
                        html.Span(className="legend-negative", style={"display": "inline-block", "width": "20px", "height": "20px", "marginRight": "5px"}),
                        html.Span("Ingresos/Ahorros"),
                    ], className="text-center text-muted"),
                ], className="mt-4"),
            ], width=12),
        ]),
    ], fluid=True)
    
    # Definir callbacks
    @app.callback(
        [Output('dashboard-content', 'children'),
         Output('info-message', 'children')],
        [Input('row-filter', 'value'),
         Input('column-filter', 'value'),
         Input('view-mode', 'value')],
        [State('dashboard-content', 'children')]
    )
    def update_dashboard(selected_rows, selected_columns, view_mode, current_content):
        """Actualiza el contenido del dashboard según los filtros seleccionados"""
        if not selected_rows or not selected_columns:
            return [], "Por favor, seleccione al menos una fila y una columna."
        
        if view_mode == 'current':
            # Mostrar valores actuales en tarjetas
            return create_current_view(data, selected_rows, selected_columns)
        else:
            # Mostrar datos históricos en gráficas
            return create_historic_view(data, selected_rows, selected_columns)
    
    return app

def create_current_view(data, selected_rows, selected_columns):
    """Crea la vista de valores actuales en tarjetas"""
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
        # Return a tuple with empty list and info message
        return [], "No hay datos disponibles para la selección actual."
    
    # Return cards and info message about number of cards
    return cards, f"Mostrando {len(cards)} elementos"

def create_historic_view(data, selected_rows, selected_columns):
    """Crea la vista de datos históricos en gráficas"""
    cards = []
    
    if debug:
        print("\n=== CREANDO VISTA HISTÓRICA ===")
        print(f"Filas seleccionadas: {selected_rows}")
        print(f"Columnas seleccionadas: {selected_columns}")
    
    # Crear una gráfica para cada celda seleccionada que tenga datos históricos
    for row in selected_rows:
        for column in selected_columns:
            # Buscar la celda en los datos
            cell_data = None
            
            # Buscar en cellData
            for key, value in data['cellData'].items():
                if value.get('ROW') == row and value.get('COLUMN') == column:
                    cell_data = value
                    break
            
            if cell_data and cell_data.get('hasHistoric', False):
                if debug:
                    print(f"\nProcesando celda histórica: {row}: {column}")
                    print(f"Datos de la celda: {cell_data.keys()}")
                
                # Obtener la serie temporal
                time_series = cell_data.get('timeSeries', [])
                
                if time_series:
                    if debug:
                        print(f"Serie temporal encontrada con {len(time_series)} puntos")
                        if time_series:
                            print(f"Primer punto: {time_series[0]}")
                            print(f"Último punto: {time_series[-1]}")
                    
                    # Extraer datos para la gráfica
                    periods = []
                    real_values = []
                    ppto_values = []
                    hprev_values = []
                    
                    for point in time_series:
                        period = point.get('period', '')
                        real = point.get('real', None)
                        ppto = point.get('ppto', None)
                        hprev = point.get('hprev', None)
                        
                        periods.append(period)
                        real_values.append(real)
                        ppto_values.append(ppto)
                        hprev_values.append(hprev)
                    
                    # Crear la figura de Plotly
                    fig = go.Figure()
                    
                    # Añadir líneas para cada serie
                    if any(v is not None for v in real_values):
                        fig.add_trace(go.Scatter(
                            x=periods,
                            y=real_values,
                            mode='lines+markers',
                            name='REAL',
                            line=dict(color='blue', width=2),
                            marker=dict(size=8)
                        ))
                    
                    if any(v is not None for v in ppto_values):
                        fig.add_trace(go.Scatter(
                            x=periods,
                            y=ppto_values,
                            mode='lines+markers',
                            name='PPTO',
                            line=dict(color='green', width=2, dash='dash'),
                            marker=dict(size=8)
                        ))
                    
                    if any(v is not None for v in hprev_values):
                        fig.add_trace(go.Scatter(
                            x=periods,
                            y=hprev_values,
                            mode='lines+markers',
                            name='HPREV',
                            line=dict(color='red', width=2, dash='dot'),
                            marker=dict(size=8)
                        ))
                    
                    # Configurar el layout de la gráfica
                    fig.update_layout(
                        title=f"{row}: {column}",
                        xaxis_title="Período",
                        yaxis_title="Valor",
                        template="plotly_white",
                        height=400,
                        margin=dict(l=40, r=40, t=60, b=40),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    
                    # Crear la tarjeta con la gráfica
                    card = dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5(f"{row}: {column}", className="card-title"),
                                dcc.Graph(
                                    figure=fig,
                                    config={
                                        'displayModeBar': True,
                                        'displaylogo': False,
                                        'modeBarButtonsToRemove': ['lasso2d', 'select2d']
                                    }
                                )
                            ])
                        ], className="h-100")
                    ], width=12, md=6, className="mb-4")
                    
                    cards.append(card)
                else:
                    if debug:
                        print(f"No se encontraron puntos en la serie temporal para {row}: {column}")
    
    # Si no hay tarjetas para mostrar
    if not cards:
        # Return a tuple with empty list and info message
        return [], "No hay datos históricos disponibles para la selección actual."
    
    # Return cards and info message about number of cards
    return cards, f"Mostrando {len(cards)} gráficas históricas"

def check_and_kill_process_on_port(port):
    """Verifica si un puerto está en uso y pregunta al usuario si desea cerrar el proceso"""
    import subprocess
    import time
    
    # Verificar si el puerto está en uso
    try:
        # Ejecutar lsof para encontrar el proceso que usa el puerto
        result = subprocess.run(['lsof', '-i', f':{port}'], 
                               capture_output=True, text=True)
        
        if result.stdout:
            # Extraer el PID del proceso
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # La primera línea es el encabezado
                parts = lines[1].split()
                if len(parts) > 1:
                    pid = parts[1]
                    
                    # Obtener más información sobre el proceso
                    process_info = subprocess.run(['ps', '-p', pid, '-o', 'pid,ppid,user,%cpu,%mem,command'], 
                                                 capture_output=True, text=True)
                    
                    # Verificar si el proceso parece ser una instancia de este mismo programa
                    is_same_app = False
                    if "python" in process_info.stdout.lower() and "dashboard_plotly.py" in process_info.stdout:
                        is_same_app = True
                        print(f"\nEl puerto {port} está siendo usado por otra instancia de esta misma aplicación (PID: {pid}).")
                        print("Información del proceso:")
                        print(process_info.stdout)
                        
                        # Para instancias del mismo programa, preguntar directamente si se desea cerrar
                        response = input(f"¿Desea cerrar esta instancia anterior para liberar el puerto {port}? (s/n): ")
                        
                        if response.lower() in ['s', 'si', 'sí', 'y', 'yes']:
                            # Cerrar el proceso, primero intentando con SIGTERM (más suave)
                            print(f"Intentando terminar el proceso {pid} con señal SIGTERM...")
                            subprocess.run(['kill', pid])
                            
                            # Esperar un momento para que el proceso termine
                            time.sleep(1)
                            
                            # Verificar si el proceso fue terminado
                            check = subprocess.run(['ps', '-p', pid], 
                                                  capture_output=True, text=True)
                            
                            # Si sigue en ejecución, intentar con SIGKILL (-9)
                            if "PID" in check.stdout:
                                print(f"El proceso sigue en ejecución. Intentando con señal SIGKILL...")
                                subprocess.run(['kill', '-9', pid])
                                
                                # Esperar otro momento
                                time.sleep(1)
                                
                                # Verificar nuevamente
                                check = subprocess.run(['ps', '-p', pid], 
                                                      capture_output=True, text=True)
                                if "PID" in check.stdout:
                                    print(f"¡Advertencia! El proceso {pid} sigue en ejecución.")
                                    print("Puede que necesites permisos de administrador para terminarlo.")
                                    print("Intenta ejecutar: sudo kill -9 " + pid)
                                    return False
                            
                            print(f"Proceso {pid} terminado exitosamente.")
                            return True
                        else:
                            print("Continuando sin cerrar el proceso...")
                            return False
                    else:
                        # Para otros procesos, seguir con el flujo normal
                        print(f"\nEl puerto {port} está siendo usado por otro proceso.")
                        check_response = input("¿Desea ver información detallada sobre este proceso? (s/n): ")
                        
                        if check_response.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
                            print("Continuando sin verificar el proceso...")
                            return False
                            
                        print(f"Información detallada sobre el proceso que usa el puerto {port}:")
                        print(result.stdout)
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
    # Cargar datos
    data = load_data()
    
    if not data:
        print("Error: No se pudieron cargar los datos.")
        return 1
    
    # Crear y ejecutar la aplicación Dash
    app = create_dashboard(data)
    
    if not app:
        print("Error: No se pudo crear la aplicación Dash.")
        return 1
    
    # Intentar ejecutar la aplicación con diferentes puertos si es necesario
    ports_to_try = [8051, 8052, 8053, 8054, 8055]
    
    print("\n=== INICIANDO SERVIDOR DASH ===")
    print("Intentando iniciar en uno de los puertos disponibles...")
    print("Presiona Ctrl+C para detener el servidor")
    
    # Añadir una opción para forzar un puerto específico
    force_port = input("¿Desea especificar un puerto concreto? (Dejar en blanco para probar automáticamente): ")
    if force_port.strip():
        try:
            port = int(force_port.strip())
            ports_to_try = [port]
            print(f"Intentando forzar el uso del puerto {port}...")
            
            # Verificar si el puerto está en uso y preguntar si se debe cerrar
            check_and_kill_process_on_port(port)
            
            # Ejecutar la aplicación
            print(f"Servidor iniciado en http://127.0.0.1:{port}/")
            app.run(debug=True, port=port)
            return 0
        except ValueError:
            print(f"El valor '{force_port}' no es un número de puerto válido. Continuando con la selección automática.")
        except Exception as e:
            print(f"Error al iniciar en el puerto {force_port}: {e}")
            print("Continuando con la selección automática de puertos...")
    
    # Intentar limpiar todos los puertos antes de comenzar
    import subprocess
    for port in ports_to_try:
        try:
            subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, check=False)
        except:
            pass
    
    for port in ports_to_try:
        try:
            print(f"Intentando iniciar en puerto {port}...")
            
            # Verificar si el puerto está en uso y preguntar si se debe cerrar
            if not check_and_kill_process_on_port(port):
                print(f"Saltando puerto {port}, intentando el siguiente...")
                continue
            
            # Ejecutar la aplicación
            print(f"Servidor iniciado en http://127.0.0.1:{port}/")
            app.run(debug=True, port=port)
            return 0  # Si llegamos aquí, la aplicación se inició correctamente
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"Puerto {port} ya está en uso, intentando el siguiente...")
                continue
            else:
                raise  # Re-lanzar si es otro tipo de error
    
    # Si llegamos aquí, todos los puertos estaban ocupados
    print("Error: No se pudo iniciar la aplicación. Todos los puertos están ocupados.")
    return 1

if __name__ == "__main__":
    sys.exit(main())