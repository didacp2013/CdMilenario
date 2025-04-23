#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Aplicación principal del dashboard
"""
import os
import sys
import argparse
import json
from dash import Dash, html, dcc, callback_context
import dash
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

# Importar módulos propios
try:
    from dashboard_utils import check_and_kill_process_on_port
    from dashboard_data_loader import load_data
    from dashboard_kpi_view import create_kpi_view
    from dashboard_historic_view import create_historic_view
except ImportError as e:
    print(f"Error al importar módulos: {e}")
    sys.exit(1)

# Inicializar la aplicación Dash
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Dashboard de Seguimiento"

def create_layout(data=None):
    """
    Crea el layout principal de la aplicación
    """
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
        
        # Selector de vista
        html.Div([
            dbc.ButtonGroup([
                dbc.Button("Vista KPI", id="btn-kpi-view", color="primary", className="me-1", n_clicks=0),
                dbc.Button("Vista Histórica", id="btn-historic-view", color="secondary", className="me-1", n_clicks=0)
            ], style={'margin': '0 auto', 'display': 'flex', 'justifyContent': 'center'})
        ], style={'marginBottom': '30px'}),
        
        # Contenedor para la vista seleccionada
        html.Div(id="view-container", style={'padding': '20px'}),
        
        # Pie de página
        html.Footer([
            html.P("Dashboard de Seguimiento © 2023", style={
                'textAlign': 'center',
                'color': '#6c757d',
                'fontSize': '0.9em',
                'marginTop': '10px'
            })
        ], style={
            'borderTop': '1px solid #dee2e6',
            'marginTop': '30px',
            'padding': '20px 0'
        })
    ])

def main():
    # Add default arguments if none are provided
    if len(sys.argv) <= 1:
        excel_path = "/Users/didac/Downloads/StoryMac/DashBTracker/PruebasCdM/Tchart_V06.xlsm"
        historic_sheet = "FrmBB_2"
        kpi_sheet = "FrmBB_3"
        print("No se detectaron argumentos, usando valores por defecto:")
        print(f"  --excel {excel_path}")
        print(f"  --historic-sheet {historic_sheet}")
        print(f"  --kpi-sheet {kpi_sheet}")
        sys.argv.extend([
            "--excel", excel_path,
            "--historic-sheet", historic_sheet,
            "--kpi-sheet", kpi_sheet,
            "--debug"
        ])
    print("INICIO main()")
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Dashboard de Seguimiento')
    parser.add_argument('--excel', type=str, help='Ruta al archivo Excel con los datos')
    parser.add_argument('--historic-sheet', type=str, help='Nombre de la hoja con datos históricos')
    parser.add_argument('--kpi-sheet', type=str, help='Nombre de la hoja con datos KPI')
    parser.add_argument('--json', type=str, help='Ruta al archivo JSON con datos procesados')
    parser.add_argument('--port', type=int, default=8050, help='Puerto para la aplicación (default: 8050)')
    parser.add_argument('--debug', action='store_true', help='Activar modo debug')
    
    args = parser.parse_args()
    print("Argumentos parseados:", args)
    
    # Verificar argumentos
    if not args.excel and not args.json:
        print("Error: Debe especificar un archivo Excel (--excel) o un archivo JSON (--json)")
        return 1
    
    if args.excel and not (args.historic_sheet or args.kpi_sheet):
        print("Error: Al usar Excel, debe especificar al menos una hoja (--historic-sheet o --kpi-sheet)")
        return 1
    
    print("Cargando datos...")
    data = None
    
    if args.json:
        try:
            print(f"Intentando cargar datos desde JSON: {args.json}")
            with open(args.json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if args.debug:
                    print(f"Datos cargados desde JSON: {args.json}")
        except Exception as e:
            print(f"Error al cargar datos desde JSON: {e}")
            return 1
    else:
        print(f"Intentando cargar datos desde Excel: {args.excel}")
        data = load_data(
            excel_path=args.excel,
            historic_sheet=args.historic_sheet,
            kpi_sheet=args.kpi_sheet,
            debug=args.debug
        )
        print("Datos cargados desde Excel.")
    
        if not data:
            print("Error: No se pudieron cargar los datos desde Excel")
            return 1
    
    print("Verificando datos cargados...")
    if not data or 'cellData' not in data or not data['cellData']:
        print("Error: No hay datos para mostrar en el dashboard")
        return 1
    
    print("Verificando puerto disponible...")
    port = args.port
    max_port = port + 10  # Intentar hasta 10 puertos consecutivos
    
    while port < max_port:
        if check_and_kill_process_on_port(port, debug=args.debug):
            break
        port += 1
        if args.debug:
            print(f"Intentando con el puerto {port}...")
    
    if port >= max_port:
        print("Error: No se pudo iniciar la aplicación. Todos los puertos están ocupados.")
        return 1
    
    # Inicializar la aplicación Dash
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.title = "Dashboard de Seguimiento"
    
    # Configurar layout
    app.layout = create_layout(data)
    
    # Callback para cambiar entre vistas
    @app.callback(
        Output("view-container", "children"),
        [Input("btn-kpi-view", "n_clicks"), 
         Input("btn-historic-view", "n_clicks")],
        [State("btn-kpi-view", "n_clicks"), 
         State("btn-historic-view", "n_clicks")]
    )
    def update_view(kpi_clicks, historic_clicks, prev_kpi_clicks, prev_historic_clicks):
        # Determinar qué botón se presionó
        ctx = dash.callback_context
        
        if not ctx.triggered:
            # Mostrar vista KPI por defecto
            return create_kpi_view(data)
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == "btn-kpi-view":
            return create_kpi_view(data)
        elif button_id == "btn-historic-view":
            return create_historic_view(data)
        
        # Por defecto, mostrar vista KPI
        return create_kpi_view(data)
    
    # Iniciar el servidor
    print(f"Iniciando servidor en http://127.0.0.1:{port}")
    try:
        app.run(debug=args.debug, port=port)
        print("El servidor Dash ha terminado (esto NO debería verse si todo va bien).")
    except Exception as e:
        print(f"Error al arrancar el servidor Dash: {e}")
        import traceback
        traceback.print_exc()

    # At the end of the main function, before returning data:
    
    # Añadir información sobre el inicio de la aplicación
    data['app_started'] = True
    data['port'] = 8050  # O el puerto que estés utilizando
    
    return data
    
    return 0

def main(port=8050, data=None):
    """Inicia el servidor Dash en el puerto especificado y utiliza los datos proporcionados."""
    from dash import Dash, html, dcc
    import dash_bootstrap_components as dbc

    # Inicializar la aplicación Dash
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.title = "Dashboard de Seguimiento"

    # Definir la función create_layout si no está definida
    def create_layout(data=None):
        """Crea el layout principal de la aplicación Dash."""
        from dash import html
        return html.Div([
            html.H1("Dashboard de Seguimiento"),
            html.Div(f"Datos cargados: {len(data.get('cellData', {}))} celdas") if data else html.Div("No se proporcionaron datos.")
        ])

    # Configurar el layout utilizando los datos proporcionados
    if data:
        app.layout = html.Div([
            html.H1("Dashboard de Seguimiento"),
            html.Div(f"Datos cargados: {len(data.get('cellData', {}))} celdas"),
            # Agregar más elementos al layout según los datos
        ])
    else:
        app.layout = html.Div([
            html.H1("Dashboard de Seguimiento"),
            html.Div("No se proporcionaron datos.")
        ])

    # Iniciar el servidor Dash
    try:
        app.run(debug=True, port=port)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"El puerto {port} está ocupado. Intentando con un puerto alternativo...")
            port += 1
            app.run(debug=True, port=port)
        else:
            raise

# Asegurarse de que el archivo `dashboard_main.py` sea compatible con Gunicorn
if __name__ == "__main__":
    from dash import Dash
    app = Dash(__name__)
    app.run(debug=False, port=8050)