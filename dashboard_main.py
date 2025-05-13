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
from dashboard_kpi_view import create_kpi_view as kpi_view_external
from dashboard_historic_view import create_historic_view as historic_view_external
from dashboard_tree_view import create_treemap_figure, render_tree_view

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
    Carga los datos reales desde Excel para el dashboard.
    Si falla, muestra el error y no intenta cargar datos simulados.
    """
    try:
        from excel_main import main as extract_excel_data
        datos_dashboard, fasg5_filtrados = extract_excel_data()
        global fasg5_data_filtrados
        fasg5_data_filtrados = fasg5_filtrados
        return datos_dashboard
    except Exception as e:
        print(f"Error al importar o ejecutar excel_main: {e}")
        raise RuntimeError("Error crítico al cargar los datos reales. Revise excel_main.") from e

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

def render_tree_view(data):
    """
    Renderiza la vista de árbol utilizando los datos de tipo T
    """
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
        
        tree_structure = row.get("DATACONTENTS", [])
        title = f"{clean_label(row.get('ROW', ''))} - {clean_label(row.get('COLUMN', ''))}"
        
        fig = create_treemap_figure(tree_structure, title="")
        card = html.Div([
            html.H5(title, style={'margin': '0', 'color': '#fff', 'fontWeight': '600', 'padding': '12px 15px', 'borderRadius': '5px 5px 0 0', 'background': 'linear-gradient(135deg, #4a6fa5 0%, #2c3e50 100%)'}),
            html.Div([
                dcc.Graph(figure=fig, id='treemap-graph', config={'displayModeBar': False})
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
    
    return html.Div([
        html.Div(tree_cards, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center', 'gap': '20px', 'padding': '20px'}),
        html.Div(id='node-info-modal', style={'display': 'none'})  # Contenedor para el modal
    ])

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
            return kpi_view_external(data), ""
        elif view_type == 'historic':
            return historic_view_external(data), ""
        else:  # view_type == 'tree'
            return render_tree_view(data), ""

    @app.callback(
        Output('close-trigger', 'children'),
        Input('btn-close', 'n_clicks'),
        prevent_initial_call=True
    )
    def close_dashboard(n_clicks):
        if n_clicks:
            stop_server()
        return ''

    @app.callback(
        Output('node-info-modal', 'style'),
        [Input('treemap-graph', 'clickData')],
        [State('node-info-modal', 'style')]
    )
    def show_node_info(click_data, current_style):
        if not click_data:
            return {'display': 'none'}
        
        # Obtener el ID del punto seleccionado y verificar si es un nodo hoja
        point = click_data['points'][0]
        customdata = point.get('customdata', '')
        
        if not customdata or 'Nodo hoja' not in customdata:
            return {'display': 'none'}
        
        # Es un nodo hoja, mostrar el modal
        return {
            'position': 'fixed',
            'top': '0',
            'left': '0',
            'width': '100%',
            'height': '100%',
            'backgroundColor': 'rgba(0,0,0,0.5)',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'zIndex': '1000'
        }
    
    @app.callback(
        Output('node-info-modal', 'children'),
        [Input('treemap-graph', 'clickData')],
        [State('cia-filter', 'value'),
         State('prjid-filter', 'value')]
    )
    def update_node_info(click_data, cia, prjid):
        if not click_data:
            return []
        
        # Obtener el ID del punto seleccionado
        point = click_data['points'][0]
        node_id = point.get('id', '')
        label = point.get('label', '')
        value = point.get('value', 0)
        customdata = point.get('customdata', '')
        
        if not customdata or 'Nodo hoja' not in customdata:
            return []
        
        # Obtener información filtrada de fasg5_data_filtrados si está disponible
        filtered_info = []
        if 'fasg5_data_filtrados' in globals() and fasg5_data_filtrados:
            # Filtrar por CIA, PRJID y el ID del nodo
            for item in fasg5_data_filtrados:
                if (not cia or str(item.get('CIA', '')) == str(cia)) and \
                   (not prjid or str(item.get('PRJID', '')) == str(prjid)) and \
                   str(item.get('itm_id', '')) == str(node_id):
                    filtered_info.append(item)
        
        # Crear tabla con la información filtrada
        table_rows = []
        if filtered_info:
            for item in filtered_info:
                for key, value in item.items():
                    if key not in ['CIA', 'PRJID', 'itm_id']:
                        table_rows.append(html.Tr([
                            html.Td(key, style={'fontWeight': 'bold', 'padding': '8px', 'borderBottom': '1px solid #ddd'}),
                            html.Td(str(value), style={'padding': '8px', 'borderBottom': '1px solid #ddd'})
                        ]))
        
        # Crear el contenido del modal
        return html.Div([
            html.Div([
                html.H4(f"Detalles del Nodo: {label}", style={'color': '#2c3e50', 'marginBottom': '15px'}),
                html.Hr(),
                html.P(f"Valor: {value:,.2f} €", style={'fontSize': '16px', 'marginBottom': '15px'}),
                
                # Tabla con información filtrada
                html.Div([
                    html.Table(
                        [html.Tbody(table_rows)],
                        style={'width': '100%', 'borderCollapse': 'collapse'}
                    ) if table_rows else html.P("No hay información adicional disponible para este nodo.")
                ], style={'maxHeight': '300px', 'overflowY': 'auto', 'marginBottom': '15px'}),
                
                html.Button("Cerrar", id="close-modal", n_clicks=0, 
                           style={'marginTop': '15px', 'backgroundColor': '#3498db', 'color': 'white', 
                                 'border': 'none', 'padding': '10px 20px', 'borderRadius': '5px', 'cursor': 'pointer'})
            ], style={
                'backgroundColor': 'white',
                'padding': '20px',
                'borderRadius': '5px',
                'boxShadow': '0 4px 8px rgba(0,0,0,0.2)',
                'maxWidth': '500px',
                'margin': '0 auto'
            })
        ])
    
    @app.callback(
        Output('node-info-modal', 'style', allow_duplicate=True),
        [Input('close-modal', 'n_clicks')],
        [State('node-info-modal', 'style')],
        prevent_initial_call=True
    )
    def close_modal(n_clicks, current_style):
        if n_clicks:
            return {'display': 'none'}
        return current_style

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

# Eliminar toda la función create_mock_data

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