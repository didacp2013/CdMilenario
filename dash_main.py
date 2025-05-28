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
        # Header con efecto de sombra y gradiente mejorado
        html.Div([
            html.H1("Dashboard Tracker", style={
                'color': '#2c3e50', 
                'textAlign': 'center', 
                'marginBottom': '10px', 
                'fontWeight': '700',
                'letterSpacing': '0.5px',
                'textShadow': '0 2px 4px rgba(0,0,0,0.1)'
            })
        ], style={
            'padding': '20px 0', 
            'borderBottom': '2px solid #4a6fa5', 
            'marginBottom': '30px', 
            'background': 'linear-gradient(135deg, #f8f9fa, #e9ecef, #f8f9fa)',
            'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'
        }),
        
        # Panel de controles con mejor espaciado y estilo
        html.Div([
            # Filtros con estilos mejorados
            html.Div([
                html.Label("CIA", style={'fontWeight': '600', 'color': '#2c3e50', 'marginBottom': '5px', 'fontSize': '14px'}),
                dcc.Dropdown(
                    id='cia-filter', 
                    options=[{'label': cia, 'value': cia} for cia in cia_values], 
                    value=default_cia, 
                    placeholder='Selecciona una CIA', 
                    style={
                        'width': '220px',
                        'borderRadius': '4px',
                        'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
                    }
                )
            ], style={'display': 'flex', 'flexDirection': 'column', 'marginRight': '15px'}),
            
            html.Div([
                html.Label("PRJID", style={'fontWeight': '600', 'color': '#2c3e50', 'marginBottom': '5px', 'fontSize': '14px'}),
                dcc.Dropdown(
                    id='prjid-filter', 
                    options=[{'label': prjid, 'value': prjid} for prjid in prjid_values], 
                    value=default_prjid, 
                    placeholder='Selecciona un PRJID', 
                    style={
                        'width': '220px',
                        'borderRadius': '4px',
                        'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
                    }
                )
            ], style={'display': 'flex', 'flexDirection': 'column', 'marginRight': '20px'}),
            
            # Botones con estilos mejorados y efectos hover
            html.Button(
                "Actualizar datos", 
                id="apply-filters", 
                n_clicks=0, 
                style={
                    "marginLeft": "10px", 
                    "marginRight": "15px", 
                    "height": "40px",
                    "backgroundColor": "#4a6fa5",
                    "color": "white",
                    "border": "none",
                    "borderRadius": "4px",
                    "padding": "0 20px",
                    "fontWeight": "600",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                    "cursor": "pointer",
                    "transition": "all 0.2s ease"
                }
            ),
            
            html.Button(
                "Cerrar Dashboard", 
                id="btn-close", 
                n_clicks=0, 
                style={
                    "backgroundColor": "#dc3545", 
                    "color": "white", 
                    "height": "40px",
                    "border": "none",
                    "borderRadius": "4px",
                    "padding": "0 20px",
                    "fontWeight": "600",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                    "cursor": "pointer",
                    "transition": "all 0.2s ease"
                }
            ),
            
            html.Div(id='close-message-container', style={'display': 'none'}),
            
            # Selector de vista con estilo mejorado
            html.Div([
                html.Label("Vista", style={'fontWeight': '600', 'color': '#2c3e50', 'marginBottom': '5px', 'fontSize': '14px', 'textAlign': 'center', 'display': 'block'}),
                dcc.RadioItems(
                    id='view-selector',
                    options=[
                        {'label': 'KPI', 'value': 'kpi'},
                        {'label': 'HISTÓRICO', 'value': 'historic'},
                        {'label': 'ÁRBOL', 'value': 'tree'}
                    ],
                    value='kpi',
                    labelStyle={
                        'display': 'inline-block', 
                        'marginRight': '15px', 
                        'marginLeft': '15px',
                        'fontWeight': 'bold',
                        'color': '#2c3e50',
                        'cursor': 'pointer'
                    },
                    style={
                        'display': 'flex', 
                        'justifyContent': 'center',
                        'backgroundColor': '#f8f9fa',
                        'padding': '8px 15px',
                        'borderRadius': '4px',
                        'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
                    }
                )
            ], style={"marginLeft": "20px"})
        ], style={
            'display': 'flex', 
            'justifyContent': 'center', 
            'alignItems': 'flex-end', 
            'marginBottom': '25px', 
            'gap': '10px',
            'flexWrap': 'wrap',
            'padding': '0 15px'
        }),

        # Contenedor principal con sombra sutil
        html.Div(
            id='dashboard-content',
            style={
                'padding': '15px',
                'backgroundColor': '#f9f9f9',
                'borderRadius': '8px',
                'boxShadow': '0 2px 10px rgba(0,0,0,0.05)',
                'minHeight': '300px'
            }
        ),
        
        # Mensaje de usuario con estilo mejorado
        html.Div(
            id='user-message', 
            style={
                'color': '#dc3545', 
                'textAlign': 'center', 
                'marginTop': '15px',
                'padding': '10px',
                'fontWeight': '500',
                'backgroundColor': 'rgba(220, 53, 69, 0.1)',
                'borderRadius': '4px',
                'display': 'none'  # Inicialmente oculto, se mostrará cuando tenga contenido
            }
        ),
        
        # Elemento oculto para el trigger de cierre
        html.Div(id='close-trigger', style={'display': 'none'})
    ])

def init_callbacks(app):
    """
    Inicializa los callbacks de la aplicación
    """
    # Callback para actualizar el contenido del dashboard basado en los filtros
    @app.callback(
        [Output('dashboard-content', 'children'),
         Output('user-message', 'children'),
         Output('user-message', 'style')],
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
            return html.Div(
                html.Div([
                    html.I(className="fas fa-exclamation-circle", style={'fontSize': '48px', 'color': '#dc3545', 'marginBottom': '15px'}),
                    html.H4("No hay datos disponibles", style={'color': '#2c3e50', 'marginBottom': '10px'}),
                    html.P("Por favor, verifica que el archivo Excel existe y contiene datos válidos.", style={'color': '#6c757d'})
                ], style={'textAlign': 'center', 'padding': '40px'})
            ), "", {'display': 'none'}
        
        # Filtrar los datos según los criterios seleccionados
        filtered_data = [
            item for item in datos_dashboard
            if (not cia or str(item.get('CIA', '')).strip() == str(cia).strip()) and
               (not prjid or str(item.get('PRJID', '')).strip() == str(prjid).strip())
        ]
        
        print(f"Datos filtrados: {len(filtered_data)} registros")
        
        # Si no hay datos para la combinación, informar al usuario
        if not filtered_data:
            return None, "No hay datos para la combinación seleccionada. Cambie su selección.", {'display': 'block', 'color': '#dc3545', 'textAlign': 'center', 'marginTop': '15px', 'padding': '10px', 'fontWeight': '500', 'backgroundColor': 'rgba(220, 53, 69, 0.1)', 'borderRadius': '4px'}
            
        # Mostrar la vista seleccionada
        if view_type == 'kpi':
            return kpi_view_external(filtered_data), "", {'display': 'none'}
        elif view_type == 'historic':
            return historic_view_external(filtered_data), "", {'display': 'none'}
        else:  # view_type == 'tree'
            return create_tree_view(filtered_data), "", {'display': 'none'}
    
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

        # Crear la aplicación Dash con estilos mejorados
        app = Dash(__name__, 
                  external_stylesheets=[
                      dbc.themes.BOOTSTRAP,
                      'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css'  # Añadir Font Awesome para iconos
                  ],
                  suppress_callback_exceptions=True,
                  meta_tags=[
                      # Asegurar responsive design
                      {"name": "viewport", "content": "width=device-width, initial-scale=1"}
                  ])
        
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