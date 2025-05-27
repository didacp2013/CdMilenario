#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Aplicación principal del dashboard
"""
import os
import sys
import threading
import time
import webbrowser
import socket
import psutil
import subprocess
import signal
from dash import Dash, html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import random
import pandas as pd
from dash_utils import check_and_kill_process_on_port, reserve_port
from dash_kpi_view import create_kpi_view as kpi_view_external
from dash_historic_view import create_historic_view as historic_view_external
from dash_tree_view import create_tree_view

# Variable global para controlar el estado de la aplicación
app_running = True
server_ready = threading.Event()

# Variables globales
datos_dashboard = []

def run_dash_app(app, port, debug):
    """
    Función que ejecuta la aplicación Dash en un hilo separado
    """
    server_ready.set()
    app.run(host='127.0.0.1', port=port, debug=debug)

def wait_for_server(port, timeout=30):
    """
    Espera hasta que el servidor esté listo para recibir conexiones
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if server_ready.is_set():
            try:
                with socket.create_connection(('127.0.0.1', port), timeout=1):
                    return True
            except (socket.timeout, ConnectionRefusedError):
                pass
        time.sleep(0.1)
    return False

def load_dashboard_data():
    """
    Carga los datos reales desde Excel para el dashboard
    """
    try:
        print("Intentando cargar datos desde Excel...")
        from excel_main import main as extract_excel_data
        print("Función extract_excel_data importada correctamente")
        
        # Verificar ruta del Excel
        import os
        from excel_main import EXCEL_PATH
        print(f"Ruta del Excel: {EXCEL_PATH}")
        print(f"¿El archivo existe? {os.path.exists(EXCEL_PATH)}")
        
        global datos_dashboard
        print("Ejecutando extract_excel_data()...")
        datos_dashboard = extract_excel_data()
        print("extract_excel_data() ejecutado")
        
        # Verificar que los datos sean válidos
        if not datos_dashboard:
            print("Advertencia: datos_dashboard está vacío o es None")
            return []
        
        if not isinstance(datos_dashboard, list):
            print("Advertencia: No se pudieron cargar datos válidos del Excel")
            print(f"Tipo de datos recibido: {type(datos_dashboard)}")
            print(f"Contenido: {datos_dashboard}")
            return []
            
        print(f"Datos cargados exitosamente: {len(datos_dashboard)} registros")
        if len(datos_dashboard) > 0:
            print(f"Ejemplo del primer registro: {datos_dashboard[0]}")
        return datos_dashboard
        
    except FileNotFoundError as e:
        print(f"Error: Archivo Excel no encontrado - {str(e)}")
        print(f"Buscando archivo en: {os.getcwd()}")
        return []
    except Exception as e:
        print(f"Error al cargar datos: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def create_layout():
    """
    Crea el layout principal del dashboard
    """
    data = load_dashboard_data()
    
    # Si no hay datos, crear datos de prueba
    if not data:
        print("Usando datos de prueba...")
        data = [
            {"CIA": "CIA001", "PRJID": "PRJ001", "ROW": "R1", "COLUMN": "C1", "DATATYPE": "K"},
            {"CIA": "CIA002", "PRJID": "PRJ002", "ROW": "R2", "COLUMN": "C2", "DATATYPE": "H"},
            {"CIA": "CIA003", "PRJID": "PRJ003", "ROW": "R3", "COLUMN": "C3", "DATATYPE": "T"}
        ]
    
    if not isinstance(data, list):
        raise ValueError("Los datos cargados no tienen el formato esperado")
    
    cia_values = sorted(list(set([item.get('CIA', '') for item in datos_dashboard if item.get('CIA')])), key=lambda x: str(x))
    prjid_values = sorted(list(set([item.get('PRJID', '') for item in datos_dashboard if item.get('PRJID')])), key=lambda x: str(x))
    
    default_cia = cia_values[0] if cia_values else None
    default_prjid = prjid_values[0] if prjid_values else None
    
    return html.Div([
        html.Div([
            html.H1("Dashboard Tracker", style={
                'color': '#2c3e50', 'textAlign': 'center', 'marginBottom': '10px', 'fontWeight': '700'})
        ], style={'padding': '20px 0', 'borderBottom': '2px solid #4a6fa5', 'marginBottom': '30px', 'background': 'linear-gradient(to right, #f8f9fa, #e9ecef, #f8f9fa)'}),
        html.Div([
            dcc.Dropdown(id='cia-filter', options=[{'label': cia, 'value': cia} for cia in cia_values], value=default_cia, placeholder='Selecciona una CIA', style={'width': '220px'}),
            dcc.Dropdown(id='prjid-filter', options=[{'label': prjid, 'value': prjid} for prjid in prjid_values], value=default_prjid, placeholder='Selecciona un PRJID', style={'width': '220px'}),
            html.Button("Actualizar datos", id="apply-filters", n_clicks=0, style={"marginLeft": "20px", "marginRight": "20px", "height": "40px"}),
            html.Button("Cerrar Dashboard", id="btn-close", n_clicks=0, style={"backgroundColor": "#dc3545", "color": "white", "height": "40px"}),
            html.Div(id='close-message-container', style={'display': 'none'}),
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

def init_callbacks(app):
    """
    Inicializa los callbacks de la aplicación
    """
    # Callback para actualizar el contenido del dashboard basado en los filtros
    @app.callback(
        [Output('dashboard-content', 'children'),
         Output('user-message', 'children')],
        [Input('apply-filters', 'n_clicks')],
        [State('cia-filter', 'value'),
         State('prjid-filter', 'value'),
         State('view-selector', 'value')]
    )
    def update_dashboard_content(n_clicks, cia, prjid, view_type):
        print(f"Callback de actualización activado: n_clicks={n_clicks}, cia={cia}, prjid={prjid}, view_type={view_type}")
        
        # Verificar que tenemos datos para filtrar
        if 'datos_dashboard' not in globals() or not isinstance(datos_dashboard, list):
            print("No hay datos disponibles para filtrar")
            return html.Div("No hay datos disponibles", style={'textAlign': 'center', 'padding': '20px'}), ""
        
        # Filtrar los datos según los criterios seleccionados
        filtered_data = [
            item for item in datos_dashboard
            if (not cia or str(item.get('CIA', '')).strip() == str(cia).strip()) and
               (not prjid or str(item.get('PRJID', '')).strip() == str(prjid).strip())
        ]
        
        print(f"Datos filtrados: {len(filtered_data)} registros")
        
        # Si no hay datos para la combinación, informar al usuario
        if not filtered_data:
            return None, "No hay datos para la combinación seleccionada. Cambie su selección."
            
        # Mostrar la vista seleccionada
        if view_type == 'kpi':
            return kpi_view_external(filtered_data), ""
        elif view_type == 'historic':
            return historic_view_external(filtered_data), ""
        else:  # view_type == 'tree'
            return create_tree_view(filtered_data), ""
    
    # Callback para cerrar el dashboard
    @app.callback(
        Output('close-trigger', 'children'),
        Input('btn-close', 'n_clicks'),
        prevent_initial_call=True
    )
    def close_dashboard(n_clicks):
        print(f"CALLBACK CERRAR DASHBOARD: n_clicks={n_clicks}")
        if n_clicks and n_clicks > 0:
            print(f"BOTÓN CERRAR DASHBOARD PRESIONADO {n_clicks} VECES")
            stop_server()
        return ""

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

        # Abrir el navegador en un hilo separado
        url = f"http://127.0.0.1:{PORT}"
        def open_browser():
            time.sleep(1.5)  # Esperar a que el servidor esté listo
            webbrowser.open(url)
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()

        # Ejecutar la aplicación en el hilo principal (sin debug para evitar problemas de threading)
        app.run(host='127.0.0.1', port=PORT, debug=False)
        
        return 0

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())