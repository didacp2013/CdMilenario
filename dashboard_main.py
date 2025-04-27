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
from dash_utils import check_and_kill_process_on_port, reserve_port

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
            sock = socket.socket(socket.AF_INET, socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', port))
            sock.close()
            # Esperar un poco más para asegurar que el servidor Dash está completamente iniciado
            time.sleep(2)
            return True
        except socket.error:
            time.sleep(0.1)
    return False

def load_dashboard_data():
    """
    Carga los datos extraídos como lista de dicts con DATATYPE y DATACONTENTS
    """
    return extract_excel_data()

def create_layout():
    data = load_dashboard_data()
    cia_values = sorted(list(set(row["CIA"] for row in data)))
    prjid_values = sorted(list(set(row["PRJID"] for row in data)))
    return html.Div([
        html.Div([
            html.H1("Dashboard de Seguimiento", style={
                'color': '#2c3e50', 'textAlign': 'center', 'marginBottom': '10px', 'fontWeight': '700'}),
            html.H4("Visualización de KPIs e Históricos", style={
                'color': '#4a6fa5', 'textAlign': 'center', 'marginBottom': '20px', 'fontWeight': '400'})
        ], style={'padding': '20px 0', 'borderBottom': '2px solid #4a6fa5', 'marginBottom': '30px', 'background': 'linear-gradient(to right, #f8f9fa, #e9ecef, #f8f9fa)'}),
        html.Div([
            dcc.Dropdown(id='cia-filter', options=[{'label': cia, 'value': cia} for cia in cia_values], placeholder='Selecciona una CIA', style={'width': '220px'}),
            dcc.Dropdown(id='prjid-filter', options=[{'label': prjid, 'value': prjid} for prjid in prjid_values], placeholder='Selecciona un PRJID', style={'width': '220px'}),
            html.Button("Actualizar datos", id="apply-filters", n_clicks=0, style={"marginLeft": "20px", "marginRight": "20px", "height": "40px"}),
            html.Button("Cerrar Dashboard", id="btn-close", n_clicks=0, style={"backgroundColor": "#dc3545", "color": "white", "height": "40px"}),
            html.Button("Alternar KPI/HISTÓRICO", id="toggle-view-btn", n_clicks=0, style={"marginLeft": "20px", "height": "40px"})
        ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'marginBottom': '20px', 'gap': '10px'}),
        html.Div(id='dashboard-content'),
        html.Div(id='user-message', style={'color': 'red', 'textAlign': 'center', 'marginTop': '10px'}),
        html.Div(id='close-trigger', style={'display': 'none'})
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

def create_dashboard_card(row):
    """
    Crea una tarjeta visual única para una celda/contenedor, mostrando el título y el contenido según DATATYPE.
    """
    title = f"{row.get('ROW', '')} - {row.get('COLUMN', '')}"
    header = html.Div([
        html.H5(title, style={'margin': '0', 'color': '#fff', 'fontWeight': '600'}),
        html.H6(f"CIA: {row.get('CIA', '')} | PRJID: {row.get('PRJID', '')}", style={
            'margin': '5px 0', 'fontWeight': 'normal', 'color': '#f8f9fa'})
    ], style={
        'borderBottom': '1px solid #dee2e6',
        'padding': '12px 15px',
        'borderRadius': '5px 5px 0 0',
        'background': 'linear-gradient(135deg, #4a6fa5 0%, #2c3e50 100%)'
    })
    if row.get('DATATYPE') == 'K':
        kpi = row.get('DATACONTENTS', {})
        body = html.Div([
            html.Div([
                html.Span("K.Prev: ", style={'fontWeight': 'bold'}),
                html.Span(f"{kpi.get('KPREV', 0):,.2f} €".replace(",", "."), style={'color': '#28a745' if kpi.get('KPREV', 0) >= 0 else '#dc3545'})
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Span("PDTE: ", style={'fontWeight': 'bold'}),
                html.Span(f"{kpi.get('PDTE', 0):,.2f} €".replace(",", "."), style={'color': '#28a745' if kpi.get('PDTE', 0) >= 0 else '#dc3545'})
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Span("REALPREV: ", style={'fontWeight': 'bold'}),
                html.Span(f"{kpi.get('REALPREV', 0):,.2%}", style={'color': '#28a745' if kpi.get('REALPREV', 0) >= 0 else '#dc3545'})
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Span("PPTOPREV: ", style={'fontWeight': 'bold'}),
                html.Span(f"{kpi.get('PPTOPREV', 0):,.2%}", style={'color': '#28a745' if kpi.get('PPTOPREV', 0) >= 0 else '#dc3545'})
            ])
        ], style={'padding': '15px'})
    elif row.get('DATATYPE') == 'H':
        historico = row.get('DATACONTENTS', [])
        weeks = [str(h.get("WKS", "")) for h in historico]
        ppto = [h.get("PPTO", 0) for h in historico]
        real = [h.get("REAL", 0) for h in historico]
        hprev = [h.get("HPREV", 0) for h in historico]
        fig = {
            'data': [
                {'x': weeks, 'y': hprev, 'type': 'scatter', 'name': 'HPREV', 'line': {'color': '#4a6fa5', 'width': 2}},
                {'x': weeks, 'y': ppto, 'type': 'scatter', 'name': 'PPTO', 'line': {'color': '#28a745', 'width': 2}},
                {'x': weeks, 'y': real, 'type': 'scatter', 'name': 'REAL', 'line': {'color': '#dc3545', 'width': 2}}
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
        body = html.Div([
            dcc.Graph(figure=fig, config={'displayModeBar': False})
        ], style={'padding': '15px'})
    else:
        return None
    return html.Div([
        header,
        body
    ], style={
        'margin': '12px',
        'border': '1px solid #dee2e6',
        'borderRadius': '6px',
        'backgroundColor': '#ffffff',
        'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
        'width': '350px' if row.get('DATATYPE') == 'K' else '500px',
        'display': 'inline-block',
        'verticalAlign': 'top'
    })

def create_kpi_view(data):
    kpi_data = [row for row in data if row.get("DATATYPE") == "K"]
    cards = [create_dashboard_card(row) for row in kpi_data if row.get("DATACONTENTS")]
    cards = [card for card in cards if card is not None]
    if not cards:
        return html.Div("No hay datos KPI disponibles", style={'text-align': 'center', 'margin-top': '20px'})
    return html.Div(cards, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center', 'gap': '20px', 'padding': '20px'})

def create_historic_view(data):
    historic_data = [row for row in data if row.get("DATATYPE") == "H"]
    cards = [create_dashboard_card(row) for row in historic_data if row.get("DATACONTENTS")]
    cards = [card for card in cards if card is not None]
    if not cards:
        return html.Div("No hay datos históricos disponibles", style={'text-align': 'center', 'margin-top': '20px'})
    return html.Div(cards, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center', 'gap': '20px', 'padding': '20px'})

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
    Inicializa los callbacks principales del dashboard
    """
    print("Initializing callbacks...")

    @app.callback(
        [Output('dashboard-content', 'children'),
         Output('user-message', 'children')],
        [Input('apply-filters', 'n_clicks')],
        [State('cia-filter', 'value'),
         State('prjid-filter', 'value'),
         State('toggle-view-btn', 'n_clicks')]
    )
    def update_dashboard_content(apply_n_clicks, cia, prjid, toggle_n_clicks):
        data = load_dashboard_data()
        # Filtrar por CIA y PRJID si están seleccionados
        if cia:
            data = [row for row in data if str(row.get('CIA', '')) == str(cia)]
        if prjid:
            data = [row for row in data if str(row.get('PRJID', '')) == str(prjid)]
        # Si no hay datos para la combinación, informar al usuario
        if not data:
            return None, "No hay datos para la combinación seleccionada. Cambie su selección."
        # Determinar vista: par = KPI, impar = HISTÓRICO
        if toggle_n_clicks is None or toggle_n_clicks % 2 == 0:
            return create_kpi_view(data), ""
        else:
            return create_historic_view(data), ""

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
    # 1. Cerrar Safari si está abierto
    try:
        subprocess.run(['pkill', '-x', 'Safari'])
        print("Safari cerrado correctamente.")
    except Exception as e:
        print(f"Error al cerrar Safari: {e}")
    # 2. Marcar la aplicación para terminar
    app_running = False
    # 3. Esperar un momento para que el hilo principal detecte que debe terminar
    time.sleep(1)
    # 4. Forzar el cierre de la aplicación Dash
    print("Cerrando el proceso Dash...")
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
        data = load_dashboard_data()
        if not data:
            raise ValueError("No se pudieron cargar los datos")
        print("Datos cargados correctamente")  # Debug
        print(f"Total celdas: {len(data)}")  # Debug

        # Crear la aplicación Dash
        app = Dash(__name__, 
                  external_stylesheets=[dbc.themes.BOOTSTRAP],
                  suppress_callback_exceptions=True)
        
        print("Configurando layout...")  # Debug
        # Configurar el layout
        app.layout = create_layout()
        
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