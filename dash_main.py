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
        from excel_main import main as extract_excel_data
        global datos_dashboard
        datos_dashboard = extract_excel_data()
        return datos_dashboard
    except Exception as e:
        print(f"Error al cargar datos: {str(e)}")
        return []

def create_layout():
    """
    Crea el layout principal del dashboard
    """
    data = load_dashboard_data()
    if not isinstance(data, list):
        raise ValueError("Los datos cargados no tienen el formato esperado")
    
    cia_values = []
    prjid_values = []
    for row in data:
        if isinstance(row, dict):
            cia = row.get('CIA')
            prjid = row.get('PRJID')
            if cia and str(cia) not in cia_values:
                cia_values.append(str(cia))
            if prjid and str(prjid) not in prjid_values:
                prjid_values.append(str(prjid))
    
    cia_values.sort()
    prjid_values.sort()
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

def init_callbacks(app):
    """
    Inicializa los callbacks de la aplicación
    """
    @app.callback(
        [Output('dashboard-content', 'children'),
         Output('user-message', 'children')],
        [Input('apply-filters', 'n_clicks')],
        [State('cia-filter', 'value'),
         State('prjid-filter', 'value'),
         State('view-selector', 'value')]
    )
    def update_dashboard_content(apply_n_clicks, cia, prjid, view_type):
        filtered_data = []
        if 'datos_dashboard' in globals() and isinstance(datos_dashboard, list):
            filtered_data = [
                item for item in datos_dashboard
                if (not cia or str(item.get('CIA', '')).strip() == str(cia).strip()) and
                   (not prjid or str(item.get('PRJID', '')).strip() == str(prjid).strip())
            ]
        if view_type == 'kpi':
            return kpi_view_external(filtered_data), ""
        elif view_type == 'historic':
            return historic_view_external(filtered_data), ""
        else:  # view_type == 'tree'
            return create_tree_view(filtered_data), ""

    @app.callback(
        Output('close-trigger', 'children'),
        Input('btn-close', 'n_clicks'),
        prevent_initial_call=True
    )
    def close_dashboard(n_clicks):
        if n_clicks:
            global app_running
            app_running = False
        return ''

def stop_server():
    """
    Detiene el servidor Dash de manera controlada
    """
    global app_running
    app_running = False

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
        dash_thread = threading.Thread(
            target=run_dash_app,
            args=(app, PORT, True)
        )
        dash_thread.daemon = True
        dash_thread.start()

        # Esperar a que el servidor esté listo
        if not wait_for_server(PORT):
            raise RuntimeError("El servidor no respondió en el tiempo esperado")

        # Abrir el navegador
        url = f"http://127.0.0.1:{PORT}"
        webbrowser.open(url)

        # Mantener el programa principal en ejecución
        try:
            while app_running:
                time.sleep(1)
            return 0
        except KeyboardInterrupt:
            return 0

    except Exception as e:
        return 1

if __name__ == "__main__":
    sys.exit(main())