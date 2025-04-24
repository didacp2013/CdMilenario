#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Aplicación principal del dashboard
"""
import os
import sys
import argparse
import json
import threading
import time
import webbrowser
import socket
import psutil
import subprocess
import signal
from dash import Dash, html, dcc, callback, Output, Input, State, dash_table
import dash
import dash_bootstrap_components as dbc
import random
import pandas as pd
from excel_dash_utils import check_and_kill_process_on_port, reserve_port

# Importar módulos propios
try:
    from excel_data_extractor import main as extract_data
except ImportError as e:
    print(f"Error al importar módulos: {e}")
    sys.exit(1)

# Adapt the data handling to align with the structure defined in test_excel_data_extractor.py
from excel_data_extractor import main as extract_excel_data

# Variable global para controlar el estado de la aplicación
app_running = True
server_ready = threading.Event()

def find_free_port(start_port=8050, max_attempts=100):
    """
    Encuentra un puerto libre a partir del puerto inicial
    """
    for port in range(start_port, start_port + max_attempts):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('127.0.0.1', port))
            sock.close()
            return port
        except socket.error:
            continue
    return None

def run_dash_app(app, port, debug):
    """
    Función que ejecuta la aplicación Dash en un hilo separado
    """
    try:
        # Señalizar que el servidor está por iniciar
        print(f"Iniciando servidor Dash en puerto {port}...")
        
        # Configurar una ruta especial para verificar que el servidor está listo
        @app.server.route('/health')
        def health_check():
            return 'OK'
        
        # Configurar logging
        import logging
        logging.getLogger('werkzeug').setLevel(logging.INFO)
        
        # Iniciar el servidor con debug mode activado y hot reload desactivado
        app.run(debug=debug, port=port, use_reloader=False, dev_tools_hot_reload=False)
    except Exception as e:
        print(f"Error al iniciar el servidor Dash: {e}")
        global app_running
        app_running = False
        server_ready.set()  # Liberar el evento en caso de error
        sys.exit(1)

def wait_for_server(port, timeout=30):
    """
    Espera hasta que el servidor esté listo para recibir conexiones
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', port))
            sock.close()
            # Esperar un poco más para asegurar que el servidor Dash está completamente iniciado
            time.sleep(2)
            return True
        except socket.error:
            time.sleep(0.1)
    return False

def load_dashboard_data():
    # Use the main function from excel_data_extractor to extract data
    extracted_data = extract_excel_data()

    # Filter and structure the data as per the test_excel_data_extractor.py
    filtered_data = [
        {
            "CIA": row["CIA"],
            "PRJID": row["PRJID"],
            "ROW": row["ROW"],
            "COLUMN": row["COLUMN"]
        }
        for row in extracted_data
        if "CIA" in row and "PRJID" in row and "ROW" in row and "COLUMN" in row
    ]

    return filtered_data

def create_layout():
    data = load_dashboard_data()

    # Extract unique values for filters
    cia_values = list(set(row["CIA"] for row in data))
    prjid_values = list(set(row["PRJID"] for row in data))

    return html.Div([
        # Encabezado
        html.Div([
            html.H1("Dashboard de Seguimiento", style={
                'color': '#2c3e50',
                'textAlign': 'center',
                'marginBottom': '10px',
                'fontWeight': '700'
            }),
            html.H4("Visualización de KPIs e Históricos", style={
                'color': '#4a6fa5',
                'textAlign': 'center',
                'marginBottom': '20px',
                'fontWeight': '400'
            })
        ], style={
            'padding': '20px 0',
            'borderBottom': '2px solid #4a6fa5',
            'marginBottom': '30px',
            'background': 'linear-gradient(to right, #f8f9fa, #e9ecef, #f8f9fa)'
        }),
        # Filtros
        html.Div([
            dcc.Dropdown(
                id='cia-filter',
                options=[{'label': cia, 'value': cia} for cia in cia_values],
                placeholder='Selecciona una CIA'
            ),
            dcc.Dropdown(
                id='prjid-filter',
                options=[{'label': prjid, 'value': prjid} for prjid in prjid_values],
                placeholder='Selecciona un PRJID'
            )
        ], style={
            'display': 'flex',
            'justifyContent': 'space-around',
            'marginBottom': '20px'
        })
    ])

# Initialize the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Set the layout of the app
app.layout = create_layout()

# Callback para alternar entre KPIs e Históricos
@app.callback(
    Output('toggle-view-btn', 'style'),
    Input('toggle-view-btn', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_view(n_clicks):
    if n_clicks % 2 == 0:
        return {'backgroundColor': 'blue', 'color': 'white', 'width': '150px', 'height': '40px'}
    else:
        return {'backgroundColor': 'red', 'color': 'white', 'width': '150px', 'height': '40px'}

def create_kpi_view(data):
    """
    Crea la vista de KPIs con tarjetas individuales para cada combinación ROW/COLUMN
    """
    if not data or 'kpi_data' not in data or not data['kpi_data']:
        return html.Div("No hay datos KPI disponibles", style={'text-align': 'center', 'margin-top': '20px'})
    
    # Agrupar datos por ROW y COLUMN
    grouped_data = {}
    for item in data['kpi_data']:
        key = (item.get('ROW', ''), item.get('COLUMN', ''))
        if key not in grouped_data:
            grouped_data[key] = {
                'CIA': item.get('CIA', ''),
                'PRJID': item.get('PRJID', ''),
                'CONTENIDO': item.get('CONTENIDO', {})
            }
    
    # Crear tarjetas para cada grupo
    kpi_cards = []
    for (row, column), group_data in grouped_data.items():
        if 'CONTENIDO' in group_data and 'KPIS' in group_data['CONTENIDO']:
            kpis = group_data['CONTENIDO']['KPIS']
            
            card = html.Div([
                # Encabezado de la tarjeta
                html.Div([
                    html.H5(f"{row} - {column}", style={
                        'margin': '0',
                        'color': '#fff',
                        'fontWeight': '600'
                    })
                ], style={
                    'padding': '12px 15px',
                    'borderRadius': '5px 5px 0 0',
                    'background': 'linear-gradient(135deg, #4a6fa5 0%, #2c3e50 100%)'
                }),
                
                # Cuerpo de la tarjeta con los valores KPI
                html.Div([
                    # KPREV
                    html.Div([
                        html.Span("K.Prev: ", style={'fontWeight': 'bold'}),
                        html.Span(f"{kpis.get('KPREV', 0):,.2f} €".replace(",", "."), 
                                style={'color': '#28a745' if kpis.get('KPREV', 0) >= 0 else '#dc3545'})
                    ], style={'marginBottom': '10px'}),
                    
                    # PDTE
                    html.Div([
                        html.Span("PDTE: ", style={'fontWeight': 'bold'}),
                        html.Span(f"{kpis.get('PDTE', 0):,.2f} €".replace(",", "."), 
                                style={'color': '#28a745' if kpis.get('PDTE', 0) >= 0 else '#dc3545'})
                    ], style={'marginBottom': '10px'}),
                    
                    # REALPREV
                    html.Div([
                        html.Span("REALPREV: ", style={'fontWeight': 'bold'}),
                        html.Span(f"{kpis.get('REALPREV', 0):,.2%}", 
                                style={'color': '#28a745' if kpis.get('REALPREV', 0) >= 0 else '#dc3545'})
                    ], style={'marginBottom': '10px'}),
                    
                    # PPTOPREV
                    html.Div([
                        html.Span("PPTOPREV: ", style={'fontWeight': 'bold'}),
                        html.Span(f"{kpis.get('PPTOPREV', 0):,.2%}", 
                                style={'color': '#28a745' if kpis.get('PPTOPREV', 0) >= 0 else '#dc3545'})
                    ])
                ], style={'padding': '15px'})
            ], style={
                'margin': '12px',
                'border': '1px solid #dee2e6',
                'borderRadius': '6px',
                'backgroundColor': '#ffffff',
                'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
                'width': '300px',
                'display': 'inline-block',
                'verticalAlign': 'top'
            })
            
            kpi_cards.append(card)
    
    return html.Div([
        html.Div(kpi_cards, style={
            'display': 'flex',
            'flexWrap': 'wrap',
            'justifyContent': 'center',
            'gap': '20px',
            'padding': '20px'
        })
    ])

def create_historic_view(data):
    """
    Crea la vista histórica con gráficos para cada combinación ROW/COLUMN
    """
    if not data or 'historic_data' not in data or not data['historic_data']:
        return html.Div("No hay datos históricos disponibles", style={'text-align': 'center', 'margin-top': '20px'})
    
    # Agrupar datos por ROW y COLUMN
    grouped_data = {}
    for item in data['historic_data']:
        key = (item.get('ROW', ''), item.get('COLUMN', ''))
        if key not in grouped_data:
            grouped_data[key] = {
                'CIA': item.get('CIA', ''),
                'PRJID': item.get('PRJID', ''),
                'series': []
            }
        grouped_data[key]['series'].append(item)
    
    # Crear tarjetas para cada grupo
    historic_cards = []
    for (row, column), group_data in grouped_data.items():
        series_data = group_data['series']
        
        # Preparar datos para el gráfico
        dates = []
        prev_values = []
        ppto_values = []
        real_values = []
        
        for item in sorted(series_data, key=lambda x: x.get('TIMESTAMP', '')):
            if 'CONTENIDO' in item and 'HISTORICOS' in item['CONTENIDO']:
                hist = item['CONTENIDO']['HISTORICOS']
                dates.append(item.get('TIMESTAMP', ''))
                prev_values.append(float(hist.get('PREV', 0)))
                ppto_values.append(float(hist.get('PPTO', 0)))
                real_values.append(float(hist.get('REAL', 0)))
        
        if dates:  # Solo crear tarjeta si hay datos
            # Crear gráfico
            fig = {
                'data': [
                    {'x': dates, 'y': prev_values, 'type': 'scatter', 'name': 'PREV',
                     'line': {'color': '#4a6fa5', 'width': 2}},
                    {'x': dates, 'y': ppto_values, 'type': 'scatter', 'name': 'PPTO',
                     'line': {'color': '#28a745', 'width': 2}},
                    {'x': dates, 'y': real_values, 'type': 'scatter', 'name': 'REAL',
                     'line': {'color': '#dc3545', 'width': 2}}
                ],
                'layout': {
                    'margin': {'l': 40, 'r': 20, 't': 20, 'b': 40},
                    'height': 300,
                    'showlegend': True,
                    'legend': {'orientation': 'h', 'y': 1.1},
                    'plot_bgcolor': 'white',
                    'paper_bgcolor': 'white',
                    'xaxis': {'gridcolor': '#eee'},
                    'yaxis': {'gridcolor': '#eee', 'title': 'Valores (€)'}
                }
            }
            
            card = html.Div([
                # Encabezado
                html.Div([
                    html.H5(f"{row} - {column}", style={
                        'margin': '0',
                        'color': '#fff',
                        'fontWeight': '600'
                    })
                ], style={
                    'padding': '12px 15px',
                    'borderRadius': '5px 5px 0 0',
                    'background': 'linear-gradient(135deg, #4a6fa5 0%, #2c3e50 100%)'
                }),
                
                # Gráfico
                html.Div([
                    dcc.Graph(
                        figure=fig,
                        config={'displayModeBar': False}
                    )
                ], style={'padding': '15px'})
            ], style={
                'margin': '12px',
                'border': '1px solid #dee2e6',
                'borderRadius': '6px',
                'backgroundColor': '#ffffff',
                'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
                'width': '500px',
                'display': 'inline-block',
                'verticalAlign': 'top'
            })
            
            historic_cards.append(card)
    
    return html.Div([
        html.Div(historic_cards, style={
            'display': 'flex',
            'flexWrap': 'wrap',
            'justifyContent': 'center',
            'gap': '20px',
            'padding': '20px'
        })
    ])

def create_kpi_table(kpi_data):
    """
    Crea una tabla de KPIs adaptada a la estructura de datos procesada
    """
    try:
        if not kpi_data:
            return html.Div("No hay datos KPI disponibles")
        
        # Convertir los datos KPI a DataFrame y asegurar tipos de datos correctos
        df = pd.DataFrame(kpi_data)
        
        # Asegurar que las columnas estén en el orden deseado y con tipos correctos
        columns_order = ['CIA', 'PRJID', 'ROW', 'COLUMN', 'VALUE', 'TIMESTAMP']
        df = df.reindex(columns=columns_order, fill_value='')
        
        # Convertir explícitamente a tipos compatibles con Dash
        records = []
        for _, row in df.iterrows():
            record = {}
            for col in df.columns:
                val = row[col]
                # Convertir cada valor a str, int o float según corresponda
                if pd.isna(val):
                    record[col] = ''
                else:
                    try:
                        # Intentar convertir a número si es posible
                        float_val = float(val)
                        if float_val.is_integer():
                            record[col] = int(float_val)
                        else:
                            record[col] = float_val
                    except (ValueError, TypeError):
                        # Si no se puede convertir a número, usar str
                        record[col] = str(val)
            records.append(record)
        
        return dash_table.DataTable(
            id='kpi-table',
            columns=[{"name": i, "id": i} for i in df.columns],
            data=records,
            style_table={
                'overflowX': 'auto',
                'maxHeight': '500px',
                'overflowY': 'auto'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'whiteSpace': 'normal',
                'height': 'auto',
                'minWidth': '100px',
                'maxWidth': '300px'
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_data={
                'backgroundColor': 'white'
            },
            style_data_conditional=[],
            page_size=10,
            sort_action='native',
            filter_action='native'
        )
    except Exception as e:
        print(f"Error al crear tabla KPI: {e}")
        return html.Div("Error al crear la tabla KPI")

def create_historic_table(historic_data):
    """
    Crea una tabla histórica adaptada a la estructura de datos procesada
    """
    try:
        if not historic_data:
            return html.Div("No hay datos históricos disponibles")
        
        # Convertir los datos históricos a DataFrame y asegurar tipos de datos correctos
        df = pd.DataFrame(historic_data)
        
        # Asegurar que las columnas estén en el orden deseado y con tipos correctos
        columns_order = ['CIA', 'PRJID', 'ROW', 'COLUMN', 'VALUE', 'TIMESTAMP']
        df = df.reindex(columns=columns_order, fill_value='')
        
        # Convertir explícitamente a tipos compatibles con Dash
        records = []
        for _, row in df.iterrows():
            record = {}
            for col in df.columns:
                val = row[col]
                # Convertir cada valor a str, int o float según corresponda
                if pd.isna(val):
                    record[col] = ''
                else:
                    try:
                        # Intentar convertir a número si es posible
                        float_val = float(val)
                        if float_val.is_integer():
                            record[col] = int(float_val)
                        else:
                            record[col] = float_val
                    except (ValueError, TypeError):
                        # Si no se puede convertir a número, usar str
                        record[col] = str(val)
            records.append(record)
        
        return dash_table.DataTable(
            id='historic-table',
            columns=[{"name": i, "id": i} for i in df.columns],
            data=records,
            style_table={
                'overflowX': 'auto',
                'maxHeight': '500px',
                'overflowY': 'auto'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'whiteSpace': 'normal',
                'height': 'auto',
                'minWidth': '100px',
                'maxWidth': '300px'
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_data={
                'backgroundColor': 'white'
            },
            style_data_conditional=[],
            page_size=10,
            sort_action='native',
            filter_action='native'
        )
    except Exception as e:
        print(f"Error al crear tabla histórica: {e}")
        return html.Div("Error al crear la tabla histórica")

def init_callbacks(app):
    """
    Initialize the two main callbacks for the dashboard
    """
    print("Initializing callbacks...")

    # Callback 1: Apply Filters
    @app.callback(
        [Output('filtered-data', 'data'),
         Output('view-container', 'children'),
         Output('initial-message', 'style'),
         Output('view-selector', 'style')],
        [Input('apply-filters', 'n_clicks')],
        [State('cia-filter', 'value'),
         State('prjid-filter', 'value'),
         State('filtered-data', 'data'),
         State('view-state', 'data')]
    )
    def apply_filters(n_clicks, cia, prjid, current_data, view_state):
        if not n_clicks or not cia or not prjid:
            return current_data, None, {'display': 'block'}, {'display': 'block'}

        filtered_data = {'kpi_data': [], 'historic_data': []}

        # Filter KPI data
        if 'kpi_data' in current_data and current_data['kpi_data']:
            filtered_data['kpi_data'] = [
                d for d in current_data['kpi_data']
                if str(d.get('CIA', '')) == str(cia) and str(d.get('PRJID', '')) == str(prjid)
            ]

        # Filter historic data
        if 'historic_data' in current_data and current_data['historic_data']:
            filtered_data['historic_data'] = [
                d for d in current_data['historic_data']
                if str(d.get('CIA', '')) == str(cia) and str(d.get('PRJID', '')) == str(prjid)
            ]

        # Check if there are no valid labels
        if not filtered_data['kpi_data'] and not filtered_data['historic_data']:
            return current_data, html.Div("No valid labels found for the selected combination.", style={'color': 'red'}), {'display': 'block'}, {'display': 'block'}

        # Create view based on the current state
        current_view = view_state.get('current_view', 'kpi')
        view = create_kpi_view(filtered_data) if current_view == 'kpi' else create_historic_view(filtered_data)

        return filtered_data, view, {'display': 'none'}, {'display': 'block'}

    # Callback 2: Close Dashboard
    @app.callback(
        Output('close-trigger', 'data'),
        Input('btn-close', 'n_clicks'),
        prevent_initial_call=True
    )
    def close_dashboard(n_clicks):
        if n_clicks:
            stop_server()
        return ''

def stop_server():
    """
    Detiene el servidor Dash de manera controlada
    """
    global app_running
    
    print("\nCerrando el dashboard...")
    
    # 1. Primero cerramos el navegador
    try:
        # En macOS, cerrar Safari si está abierto en el puerto 8050
        subprocess.run(['pkill', '-x', 'Safari'])
    except Exception as e:
        print(f"Error al cerrar el navegador: {e}")
    
    # 2. Marcamos la aplicación para que termine
    app_running = False
    
    # 3. Esperamos un momento para que el hilo principal detecte que debe terminar
    time.sleep(1)
    
    # 4. Si después de esperar no se ha cerrado, forzamos el cierre
    os._exit(0)

def main():
    """
    Función principal que inicia la aplicación del dashboard
    """
    try:
        # Configurar el puerto
        PORT = 8050
        check_and_kill_process_on_port(PORT)
        reserve_port(PORT)

        print("Cargando datos...")  # Debug
        # Cargar datos usando excel_data_extractor
        data = extract_data()
        if not data:
            raise ValueError("No se pudieron cargar los datos")
        
        print("Datos cargados correctamente")  # Debug
        print(f"KPIs: {len(data.get('kpi_data', []))}")  # Debug
        print(f"Históricos: {len(data.get('historic_data', []))}")  # Debug

        # Crear la aplicación Dash
        app = Dash(__name__, 
                  external_stylesheets=[dbc.themes.BOOTSTRAP],
                  suppress_callback_exceptions=True)
        
        print("Configurando layout...")  # Debug
        # Configurar el layout
        app.layout = create_layout(data)
        
        print("Inicializando callbacks...")  # Debug
        # Inicializar callbacks
        init_callbacks(app)

        # Iniciar el servidor en un hilo separado
        print(f"Iniciando servidor en http://127.0.0.1:{PORT}")
        dash_thread = threading.Thread(
            target=run_dash_app,
            args=(app, PORT, True)  # Cambiado a True para activar modo debug
        )
        dash_thread.daemon = True
        dash_thread.start()

        # Esperar a que el servidor esté listo
        if not wait_for_server(PORT):
            print("Error: El servidor no respondió en el tiempo esperado")
            return 1

        # Abrir el navegador
        url = f"http://127.0.0.1:{PORT}"
        print(f"Abriendo navegador en {url}")
        webbrowser.open(url)

        # Mantener el programa principal en ejecución
        try:
            while app_running:
                time.sleep(1)
            print("Cerrando la aplicación...")
            return 0
        except KeyboardInterrupt:
            print("\nCerrando el dashboard...")
            return 0

    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())