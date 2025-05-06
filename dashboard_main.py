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
    from dashboard_tree_view import create_tree_view
except ImportError as e:
    print(f"Error al importar módulos: {e}")
    sys.exit(1)

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
    Carga los datos reales desde Excel para el dashboard
    """
    try:
        # Importar el módulo para extraer datos de Excel
        from excel_main import main as extract_excel_data
        
        # Cargar datos reales desde Excel
        return extract_excel_data()
    except ImportError as e:
        print(f"Error al importar el módulo excel_main: {e}")
        print("Usando datos simulados como respaldo...")
        return create_mock_data()

def create_mock_data():
    """
    Crea datos simulados para el dashboard
    """
    # Datos simulados para KPIs
    kpi_data = [
        {
            "CIA": "CIA1",
            "PRJID": "31199",  # Cambiado de "PRJ1" a "31199"
            "ROW": "1: Ingresos",
            "COLUMN": "1: Actual",
            "DATATYPE": "K",
            "DATACONTENTS": {
                "KPREV": 100000,
                "PDTE": 50000,
                "REALPREV": 0.75,
                "PPTOPREV": 0.80
            }
        },
        {
            "CIA": "CIA1",
            "PRJID": "31200",  # Añadido proyecto 31200
            "ROW": "2: Gastos",
            "COLUMN": "1: Actual",
            "DATATYPE": "K",
            "DATACONTENTS": {
                "KPREV": -80000,
                "PDTE": -30000,
                "REALPREV": 0.65,
                "PPTOPREV": 0.70
            }
        }
    ]
    
    # Datos simulados para históricos
    historic_data = [
        {
            "CIA": "CIA1",
            "PRJID": "PRJ1",
            "ROW": "1: Ingresos",
            "COLUMN": "1: Actual",
            "DATATYPE": "H",
            "DATACONTENTS": [
                {"WKS": "2023.01", "WKS_DATE": "2023-01-08", "WKS_SERIAL": 44934, "PPTO": 10000, "REAL": 9500, "HPREV": 9800},
                {"WKS": "2023.02", "WKS_DATE": "2023-01-15", "WKS_SERIAL": 44941, "PPTO": 12000, "REAL": 11800, "HPREV": 12100},
                {"WKS": "2023.03", "WKS_DATE": "2023-01-22", "WKS_SERIAL": 44948, "PPTO": 13000, "REAL": 13200, "HPREV": 13500}
            ]
        },
        {
            "CIA": "CIA1",
            "PRJID": "PRJ1",
            "ROW": "2: Gastos",
            "COLUMN": "1: Actual",
            "DATATYPE": "H",
            "DATACONTENTS": [
                {"WKS": "2023.01", "WKS_DATE": "2023-01-08", "WKS_SERIAL": 44934, "PPTO": -8000, "REAL": -7800, "HPREV": -7900},
                {"WKS": "2023.02", "WKS_DATE": "2023-01-15", "WKS_SERIAL": 44941, "PPTO": -9000, "REAL": -9200, "HPREV": -9100},
                {"WKS": "2023.03", "WKS_DATE": "2023-01-22", "WKS_SERIAL": 44948, "PPTO": -10000, "REAL": -9800, "HPREV": -10200}
            ]
        }
    ]
    
    # Datos simulados para árbol de costes
    tree_data = [
        {
            "CIA": "CIA1",
            "PRJID": "31199",  # Cambiado de "PRJ1" a "31199"
            "ROW": "3: Estructura de Costes",
            "COLUMN": "1: Actual",
            "DATATYPE": "T",
            "DATACONTENTS": [
                {"itm_id": "1000", "parent_id": None, "description": "Costes Directos", "value": 750000},
                {"itm_id": "1100", "parent_id": "1000", "description": "Materiales", "value": 350000},
                {"itm_id": "1110", "parent_id": "1100", "description": "Hormigón", "value": 120000},
                {"itm_id": "1120", "parent_id": "1100", "description": "Acero", "value": 95000},
                {"itm_id": "1130", "parent_id": "1100", "description": "Madera", "value": 45000},
                {"itm_id": "1140", "parent_id": "1100", "description": "Otros materiales", "value": 90000},
                {"itm_id": "1200", "parent_id": "1000", "description": "Mano de obra", "value": 280000},
                {"itm_id": "1210", "parent_id": "1200", "description": "Albañilería", "value": 120000},
                {"itm_id": "1220", "parent_id": "1200", "description": "Electricidad", "value": 60000},
                {"itm_id": "1230", "parent_id": "1200", "description": "Fontanería", "value": 50000},
                {"itm_id": "1240", "parent_id": "1200", "description": "Acabados", "value": 50000},
                {"itm_id": "1300", "parent_id": "1000", "description": "Maquinaria", "value": 120000},
                {"itm_id": "2000", "parent_id": None, "description": "Costes Indirectos", "value": 250000},
                {"itm_id": "2100", "parent_id": "2000", "description": "Gestión", "value": 100000},
                {"itm_id": "2200", "parent_id": "2000", "description": "Seguros", "value": 50000},
                {"itm_id": "2300", "parent_id": "2000", "description": "Licencias", "value": 30000},
                {"itm_id": "2400", "parent_id": "2000", "description": "Otros gastos", "value": 70000}
            ]
        },
        {
            "CIA": "CIA1",
            "PRJID": "31200",  # Añadido proyecto 31200
            "ROW": "3: Estructura de Costes",
            "COLUMN": "1: Actual",
            "DATATYPE": "T",
            "DATACONTENTS": [
                {"itm_id": "1000", "parent_id": None, "description": "Costes Directos", "value": 800000},
                {"itm_id": "1100", "parent_id": "1000", "description": "Materiales", "value": 400000},
                {"itm_id": "1110", "parent_id": "1100", "description": "Hormigón", "value": 150000},
                {"itm_id": "1120", "parent_id": "1100", "description": "Acero", "value": 120000},
                {"itm_id": "1130", "parent_id": "1100", "description": "Madera", "value": 50000},
                {"itm_id": "1140", "parent_id": "1100", "description": "Otros materiales", "value": 80000},
                {"itm_id": "1200", "parent_id": "1000", "description": "Mano de obra", "value": 300000},
                {"itm_id": "1300", "parent_id": "1000", "description": "Maquinaria", "value": 100000},
                {"itm_id": "2000", "parent_id": None, "description": "Costes Indirectos", "value": 200000}
            ]
        }
    ]
    
    # Combinar todos los datos
    return kpi_data + historic_data + tree_data

def create_layout():
    data = load_dashboard_data()
    cia_values = sorted(list(set(row["CIA"] for row in data)))
    prjid_values = sorted(list(set(row["PRJID"] for row in data)))
    return html.Div([
        html.Div([
            html.H1("Dashboard de Seguimiento", style={
                'color': '#2c3e50', 'textAlign': 'center', 'marginBottom': '10px', 'fontWeight': '700'})
        ], style={'padding': '20px 0', 'borderBottom': '2px solid #4a6fa5', 'marginBottom': '30px', 'background': 'linear-gradient(to right, #f8f9fa, #e9ecef, #f8f9fa)'}),
        html.Div([
            dcc.Dropdown(id='cia-filter', options=[{'label': cia, 'value': cia} for cia in cia_values], placeholder='Selecciona una CIA', style={'width': '220px'}),
            dcc.Dropdown(id='prjid-filter', options=[{'label': prjid, 'value': prjid} for prjid in prjid_values], placeholder='Selecciona un PRJID', style={'width': '220px'}),
            html.Button("Actualizar datos", id="apply-filters", n_clicks=0, style={"marginLeft": "20px", "marginRight": "20px", "height": "40px"}),
            html.Button("Cerrar Dashboard", id="btn-close", n_clicks=0, style={"backgroundColor": "#dc3545", "color": "white", "height": "40px"}),
            # Reemplazar el botón de alternancia por un grupo de botones de opción
            html.Div([
                dcc.RadioItems(
                    id='view-selector',
                    options=[
                        {'label': 'KPI', 'value': 'kpi'},
                        {'label': 'HISTÓRICO', 'value': 'historic'},
                        {'label': 'ÁRBOL', 'value': 'tree'}
                    ],
                    value='kpi',  # Valor predeterminado
                    labelStyle={'display': 'inline-block', 'marginRight': '10px', 'fontWeight': 'bold'},
                    style={'display': 'flex', 'justifyContent': 'center'}
                )
            ], style={"marginLeft": "20px"})
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
# Eliminar los callbacks del botón de alternancia que ya no se necesitan
# @app.callback(
#     Output('toggle-view-btn', 'style'),
#     Input('toggle-view-btn', 'n_clicks')
# )
# def toggle_view(n_clicks):
#     if n_clicks is None:
#         return {'backgroundColor': 'blue', 'color': 'white', 'width': '150px', 'height': '40px'}
#     
#     view_type = n_clicks % 3
#     if view_type == 0:
#         return {'backgroundColor': 'blue', 'color': 'white', 'width': '150px', 'height': '40px'}
#     elif view_type == 1:
#         return {'backgroundColor': 'red', 'color': 'white', 'width': '150px', 'height': '40px'}
#     else:
#         return {'backgroundColor': 'green', 'color': 'white', 'width': '150px', 'height': '40px'}
#
# @app.callback(
#     Output('toggle-view-btn', 'children'),
#     Input('toggle-view-btn', 'n_clicks')
# )
# def update_button_text(n_clicks):
#     if n_clicks is None:
#         return "Vista: KPI"
#     
#     view_type = n_clicks % 3
#     if view_type == 0:
#         return "Vista: KPI"
#     elif view_type == 1:
#         return "Vista: HISTÓRICO"
#     else:
#         return "Vista: ÁRBOL"

def create_dashboard_card(row):
    print(f"[DEBUG] Creando tarjeta para ROW={row.get('ROW')} COLUMN={row.get('COLUMN')} DATATYPE={row.get('DATATYPE')}")
    def clean_label(label):
        # Elimina el número y los dos puntos iniciales, dejando solo el texto descriptivo
        if label and ":" in label:
            return label.split(":", 1)[1].strip()
        return label or ""
    title = f"{clean_label(row.get('ROW', ''))} - {clean_label(row.get('COLUMN', ''))}"
    header = html.Div([
        html.H5(title, style={'margin': '0', 'color': '#fff', 'fontWeight': '600'})
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
        print(f"[DEBUG HISTÓRICO] Entrando en rama histórica para ROW={row.get('ROW')} COLUMN={row.get('COLUMN')}")
        historico = row.get('DATACONTENTS', [])
        def format_wks_label(wks):
            try:
                wks_str = str(wks).replace(',', '').replace(' ', '').strip()
                if '.' in wks_str:
                    year, week = wks_str.split('.', 1)
                    year = int(year)
                    week = int(week)
                    return f"{year:04d}.{week:02d}"
                elif wks_str.isdigit() and len(wks_str) == 4:
                    return f"{int(wks_str):04d}.00"
                else:
                    return wks_str
            except Exception:
                return str(wks)
        # Usar WKS_SERIAL como eje X, ordenando por él
        data_tuples = [
            (h.get("WKS_SERIAL"), format_wks_label(h.get("WKS", "")), h.get("HPREV", 0), h.get("PPTO", 0), h.get("REAL", 0))
            for h in historico if h is not None and h.get("WKS_SERIAL") is not None
        ]
        data_tuples.sort(key=lambda x: x[0])
        if data_tuples:
            serials, week_labels, hprev, ppto, real = zip(*data_tuples)
            print("[DEBUG HISTÓRICO] WKS_SERIAL eje X:", serials)
            print("[DEBUG HISTÓRICO] Etiquetas semana:", week_labels)
            print("[DEBUG HISTÓRICO] HPREV:", hprev)
            print("[DEBUG HISTÓRICO] PPTO:", ppto)
            print("[DEBUG HISTÓRICO] REAL:", real)
        else:
            print("[DEBUG HISTÓRICO] No hay data_tuples para esta tarjeta histórica.")
            serials, week_labels, hprev, ppto, real = [], [], [], [], []
        fig = {
            'data': [
                {'x': serials, 'y': hprev, 'type': 'scatter', 'name': 'HPREV', 'line': {'color': '#4a6fa5', 'width': 2}, 'text': week_labels, 'hovertemplate': '%{text}<br>HPREV: %{y}'},
                {'x': serials, 'y': ppto, 'type': 'scatter', 'name': 'PPTO', 'line': {'color': '#28a745', 'width': 2}, 'text': week_labels, 'hovertemplate': '%{text}<br>PPTO: %{y}'},
                {'x': serials, 'y': real, 'type': 'scatter', 'name': 'REAL', 'line': {'color': '#dc3545', 'width': 2}, 'text': week_labels, 'hovertemplate': '%{text}<br>REAL: %{y}'}
            ],
            'layout': {
                'margin': {'l': 40, 'r': 20, 't': 20, 'b': 40},
                'height': 300,
                'showlegend': True,
                'legend': {'orientation': 'h', 'y': 1.1},
                'plot_bgcolor': 'white',
                'paper_bgcolor': 'white',
                'xaxis': {
                    'gridcolor': '#eee',
                    'tickangle': -90,
                    'tickmode': 'auto',
                    'title': 'Fecha (número de serie Excel)',
                },
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
         State('view-selector', 'value')]
    )
    def update_dashboard_content(apply_n_clicks, cia, prjid, view_type):
        data = load_dashboard_data()
        # Filtrar por CIA y PRJID si están seleccionados
        if cia:
            data = [row for row in data if str(row.get('CIA', '')) == str(cia)]
        if prjid:
            data = [row for row in data if str(row.get('PRJID', '')) == str(prjid)]
        # Si no hay datos para la combinación, informar al usuario
        if not data:
            return None, "No hay datos para la combinación seleccionada. Cambie su selección."
        
        # Determinar vista según el valor del selector
        if view_type == 'kpi':
            return create_kpi_view(data), ""
        elif view_type == 'historic':
            return create_historic_view(data), ""
        else:  # view_type == 'tree'
            return create_tree_view(data), ""

    @app.callback(
        Output('close-trigger', 'children'),
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

def create_tree_view(data):
    """
    Crea la vista de árbol de costes para datos tipo T
    """
    from dashboard_tree_view import create_treemap_figure
    def clean_label(label):
        if label and ":" in label:
            return label.split(":", 1)[1].strip()
        return label or ""
    tree_data = [row for row in data if row.get("DATATYPE") == "T"]
    if not tree_data:
        return html.Div("No hay datos de árbol de costes disponibles", style={'text-align': 'center', 'margin-top': '20px'})
    # Procesamos los datos para convertirlos en estructura de árbol
    tree_cards = []
    for row in tree_data:
        if not row.get("DATACONTENTS"):
            continue
        tree_structure = row.get("DATACONTENTS", {})
        title = f"{clean_label(row.get('ROW', ''))} - {clean_label(row.get('COLUMN', ''))}"
        fig = create_treemap_figure(tree_structure, title="")
        card = html.Div([
            html.H5(title, style={'margin': '0', 'color': '#fff', 'fontWeight': '600', 'padding': '12px 15px', 'borderRadius': '5px 5px 0 0', 'background': 'linear-gradient(135deg, #4a6fa5 0%, #2c3e50 100%)'}),
            html.Div([
                dcc.Graph(figure=fig, config={'displayModeBar': False})
            ], style={'padding': '15px'})
        ], style={
            'margin': '12px',
            'border': '1px solid #dee2e6',
            'borderRadius': '6px',
            'backgroundColor': '#ffffff',
            'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
            'width': '800px',
            'display': 'inline-block',
            'verticalAlign': 'top'
        })
        tree_cards.append(card)
    return html.Div(tree_cards, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center', 'gap': '20px', 'padding': '20px'})

def build_tree_structure(tree_items):
    """
    Construye una estructura jerárquica a partir de una lista plana de elementos de árbol
    """
    # Crear diccionario para mapear ID a nodo
    nodes_by_id = {}
    root = {"children": []}
    
    # Primera pasada: crear todos los nodos
    for item in tree_items:
        item_id = item.get("itm_id")
        if item_id:
            nodes_by_id[item_id] = {
                "itm_id": item_id,
                "value": item.get("value", 0),
                "description": item.get("description", ""),
                "children": []
            }
    
    # Segunda pasada: establecer relaciones padre-hijo
    for item in tree_items:
        item_id = item.get("itm_id")
        parent_id = item.get("parent_id")
        
        if item_id and item_id in nodes_by_id:
            node = nodes_by_id[item_id]
            
            # Si tiene padre, añadirlo como hijo
            if parent_id and parent_id in nodes_by_id:
                nodes_by_id[parent_id]["children"].append(node)
            else:
                # Si no tiene padre o el padre no existe, añadirlo a la raíz
                root["children"].append(node)
    
    return root

def main():
    """
    Función principal que inicia la aplicación del dashboard
    """
    try:
        # Configurar el puerto
        PORT = 8050
        check_and_kill_process_on_port(PORT)
        reserve_port(PORT)

        print("Cargando datos simulados...")  # Debug
        # Cargar datos simulados
        data = load_dashboard_data()
        if not data:
            raise ValueError("No se pudieron cargar los datos simulados")
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