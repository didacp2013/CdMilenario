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
from dash import Dash, html, dcc, callback, Output, Input, State, dash_table, no_update
import dash
import dash_bootstrap_components as dbc
import random
import pandas as pd
from dash_utils import check_and_kill_process_on_port, reserve_port
from dashboard_kpi_view import create_kpi_view as kpi_view_external
from dashboard_historic_view import create_historic_view as historic_view_external
from dashboard_tree_view import create_tree_view
from dash import callback_context, MATCH
import re

# Variable global para controlar el estado de la aplicación
app_running = True
server_ready = threading.Event()

# Variables globales
datos_dashboard = []
fasg5_filtrados = []

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
        global datos_dashboard, fasg5_filtrados
        datos_dashboard, fasg5_filtrados = extract_excel_data()
        return datos_dashboard
    except Exception as e:
        print(f"Error al importar o ejecutar excel_main: {e}")
        raise RuntimeError("Error crítico al cargar los datos reales. Revise excel_main.") from e

def create_layout():
    data = load_dashboard_data()
    print("\nDEBUG: Datos recibidos en create_layout:")
    print(f"Tipo de data: {type(data)}")
    print(f"Longitud de data: {len(data) if isinstance(data, list) else 'N/A'}")
    
    # Asegurarnos de que los datos son listas de diccionarios
    if not isinstance(data, list):
        print("ERROR: data no es una lista")
        data = []
    
    # Extraer valores únicos de CIA y PRJID de manera segura
    cia_values = []
    prjid_values = []
    for row in data:
        if isinstance(row, dict):
            cia = row.get('CIA')
            prjid = row.get('PRJID')
            print(f"DEBUG: Procesando fila - CIA: {cia}, PRJID: {prjid}")
            if cia and str(cia) not in cia_values:
                cia_values.append(str(cia))
            if prjid and str(prjid) not in prjid_values:
                prjid_values.append(str(prjid))
    
    print(f"\nDEBUG: Valores únicos encontrados:")
    print(f"CIA values: {cia_values}")
    print(f"PRJID values: {prjid_values}")
    
    cia_values.sort()
    prjid_values.sort()
    
    # Seleccionar el primer valor por defecto si hay valores disponibles
    default_cia = cia_values[0] if cia_values else None
    default_prjid = prjid_values[0] if prjid_values else None
    
    return html.Div([
        html.Div([
            html.H1("Dashboard de Seguimiento", style={
                'color': '#2c3e50', 'textAlign': 'center', 'marginBottom': '10px', 'fontWeight': '700'})
        ], style={'padding': '20px 0', 'borderBottom': '2px solid #4a6fa5', 'marginBottom': '30px', 'background': 'linear-gradient(to right, #f8f9fa, #e9ecef, #f8f9fa)'}),
        html.Div([
            dcc.Dropdown(id='cia-filter', options=[{'label': cia, 'value': cia} for cia in cia_values], value=default_cia, placeholder='Selecciona una CIA', style={'width': '220px'}),
            dcc.Dropdown(id='prjid-filter', options=[{'label': prjid, 'value': prjid} for prjid in prjid_values], value=default_prjid, placeholder='Selecciona un PRJID', style={'width': '220px'}),
            html.Button("Actualizar datos", id="apply-filters", n_clicks=0, style={"marginLeft": "20px", "marginRight": "20px", "height": "40px"}),
            html.Button("Cerrar Dashboard", id="btn-close", n_clicks=0, style={"backgroundColor": "#dc3545", "color": "white", "height": "40px"}),
            html.Div([
                dcc.RadioItems(
                    id='view-selector',
                    options=[
                        {'label': 'KPI', 'value': 'kpi'},
                        {'label': 'HISTÓRICO', 'value': 'historic'},
                        {'label': 'ÁRBOL', 'value': 'tree'}
                    ],
                    value='kpi',
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
        print(f"DEBUG: update_dashboard_content llamado con n_clicks={apply_n_clicks}")
        data = load_dashboard_data()
        if not isinstance(data, list):
            data = []
        
        # Filtrar por CIA y PRJID si están seleccionados
        filtered_data = []
        for row in data:
            if isinstance(row, dict):
                row_cia = str(row.get('CIA', ''))
                row_prjid = str(row.get('PRJID', ''))
                if (not cia or row_cia == str(cia)) and (not prjid or row_prjid == str(prjid)):
                    filtered_data.append(row)
        
        # Si no hay datos para la combinación, informar al usuario
        if not filtered_data:
            return None, "No hay datos para la combinación seleccionada. Cambie su selección."
        
        # Determinar vista según el valor del selector
        if view_type == 'kpi':
            return kpi_view_external(filtered_data), ""
        elif view_type == 'historic':
            return historic_view_external(filtered_data), ""
        else:  # view_type == 'tree'
            # Filtrar los datos ITMFRM por CIA y PRJID si están seleccionados
            filtered_fasg5 = []
            if 'fasg5_filtrados' in globals() and isinstance(fasg5_filtrados, list):
                filtered_fasg5 = [
                    item for item in fasg5_filtrados
                    if (not cia or str(item.get('CIA', '')).strip() == str(cia).strip()) and
                       (not prjid or str(item.get('PRJID', '')).strip() == str(prjid).strip())
                ]
            
            print("DEBUG: Llamando a create_tree_view con app")
            print(f"DEBUG: app es None? {app is None}")
            print(f"DEBUG: filtered_fasg5 es None? {filtered_fasg5 is None}")
            return create_tree_view(filtered_data, filtered_fasg5, app), ""

    # Añadir un callback de prueba
    @app.callback(
        Output('user-message', 'children', allow_duplicate=True),
        [Input('view-selector', 'value')],
        prevent_initial_call=True
    )
    def test_callback(value):
        print(f"DEBUG: test_callback activado con valor={value}")
        return f"Callback de prueba activado con valor: {value}"

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
        
        # Obtener información filtrada de fasg5_filtrados si está disponible
        filtered_info = []
        if 'fasg5_filtrados' in globals() and isinstance(fasg5_filtrados, list):
            # Filtrar por CIA, PRJID y el ID del nodo
            for item in fasg5_filtrados:
                if isinstance(item, dict):
                    item_cia = str(item.get('CIA', ''))
                    item_prjid = str(item.get('PRJID', ''))
                    item_id = str(item.get('itm_id', ''))
                    if (not cia or item_cia == str(cia)) and \
                       (not prjid or item_prjid == str(prjid)) and \
                       item_id == str(node_id):
                        filtered_info.append(item)
        
        # Crear tabla con la información filtrada
        table_rows = []
        if filtered_info:
            for item in filtered_info:
                if isinstance(item, dict):
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

    # Callback global para los botones 'Incomings' de la vista árbol
    @app.callback(
        [Output({'type': 'popup-modal-datos-i', 'index': MATCH}, 'is_open'),
         Output({'type': 'popup-body-datos-i', 'index': MATCH}, 'children')],
        [Input({'type': 'incomings-btn', 'index': MATCH}, 'n_clicks'),
         Input({'type': 'close-popup-datos-i', 'index': MATCH}, 'n_clicks')],
        [State({'type': 'treemap-store', 'index': MATCH}, 'data'),
         State('cia-filter', 'value'),
         State('prjid-filter', 'value'),
         State({'type': 'popup-modal-datos-i', 'index': MATCH}, 'is_open')],
        prevent_initial_call=True
    )
    def show_itmfrm_popup(btn_open, btn_close, selected_node_id, cia, prjid, is_open):
        """
        Muestra un popup con la información ITMFRM para el nodo seleccionado.
        """
        print("\nDEBUG: show_itmfrm_popup callback llamado")
        print(f"DEBUG: btn_open={btn_open}, btn_close={btn_close}")
        print(f"DEBUG: selected_node_id={selected_node_id}")
        print(f"DEBUG: cia={cia}, prjid={prjid}")
        print(f"DEBUG: is_open={is_open}")
        
        # Si se hace clic en el botón de cerrar, cerrar el popup
        if btn_close:
            return False, no_update
        
        # Si el popup ya está abierto, no hacer nada
        if is_open:
            return no_update, no_update
        
        # Si no hay nodo seleccionado, no hacer nada
        if not selected_node_id:
            return no_update, no_update
        
        # Obtener el trigger que activó el callback
        trigger = callback_context.triggered[0]['prop_id'].split('.')[0]
        print(f"DEBUG: trigger={trigger}")
        
        # Llamar a la función show_itmfrm_popup de dash_utils
        from dash_utils import show_itmfrm_popup
        return show_itmfrm_popup(btn_open, selected_node_id, cia, prjid, trigger, fasg5_filtrados)

    # Callback global para guardar el id del nodo hoja clicado en el treemap
    @app.callback(
        Output({'type': 'treemap-store', 'index': MATCH}, 'data'),
        [Input({'type': 'treemap-graph', 'index': MATCH}, 'clickData')],
        [State({'type': 'treemap-store', 'index': MATCH}, 'data'),
         State({'type': 'treemap-graph', 'index': MATCH}, 'figure')],
        prevent_initial_call=True
    )
    def store_leaf_node(clickData, current_data, figure):
        print(f"DEBUG: Callback store_leaf_node activado. clickData={clickData}")
        if not clickData or 'points' not in clickData or not clickData['points']:
            print("DEBUG: No clickData válido. No se guarda nada.")
            return None
        point = clickData['points'][0]
        node_id = point.get('id', None)
        print(f"DEBUG: Nodo clicado id={node_id}")
        # Comprobar si es hoja (color rojo)
        idx = None
        if 'ids' in figure['data'][0]:
            try:
                idx = figure['data'][0]['ids'].index(node_id)
            except Exception:
                idx = None
        is_leaf = False
        if idx is not None and 'marker' in figure['data'][0] and 'colors' in figure['data'][0]['marker']:
            is_leaf = figure['data'][0]['marker']['colors'][idx] == 'red'
        print(f"DEBUG: is_leaf={is_leaf}")
        if is_leaf:
            print(f"DEBUG: Guardando id en store: {node_id}")
            return node_id
        print("DEBUG: Nodo no es hoja. No se guarda nada.")
        return None

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

        # Crear la aplicación Dash
        app = Dash(__name__, 
                  external_stylesheets=[dbc.themes.BOOTSTRAP],
                  suppress_callback_exceptions=True)
        
        # Configurar el layout
        app.layout = create_layout()
        
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