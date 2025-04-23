#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo para crear un dashboard interactivo con Plotly y Dash
Versión con capacidades de depuración mejoradas
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
import socket
import argparse

# Importar los módulos necesarios
try:
    from excel_extractor import ExcelDataExtractor
    from data_processor_full import DataProcessor
except ImportError as e:
    print(f"Error al importar módulos: {e}")
    sys.exit(1)

def check_and_kill_process_on_port(port, debug=False):
    """
    Verifica si hay un proceso usando el puerto especificado y lo mata si es necesario
    """
    import socket
    import os
    import signal
    import subprocess
    
    try:
        # Verificar si el puerto está en uso
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:  # Puerto en uso
            if debug:
                print(f"Puerto {port} en uso. Intentando liberar...")
            
            # En macOS, usar lsof para encontrar el PID
            try:
                cmd = f"lsof -i :{port} -t"
                pid = subprocess.check_output(cmd, shell=True).decode().strip()
                
                if pid:
                    if debug:
                        print(f"Proceso con PID {pid} encontrado en el puerto {port}. Intentando matar...")
                    
                    # Intentar matar el proceso
                    os.kill(int(pid), signal.SIGTERM)
                    
                    # Verificar nuevamente si el puerto está libre
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('127.0.0.1', port))
                    sock.close()
                    
                    if result != 0:
                        if debug:
                            print(f"Puerto {port} liberado exitosamente.")
                        return True
                    else:
                        if debug:
                            print(f"No se pudo liberar el puerto {port}.")
                        return False
            except Exception as e:
                if debug:
                    print(f"Error al intentar liberar el puerto: {e}")
                return False
        else:
            if debug:
                print(f"Puerto {port} disponible.")
            return True
    except Exception as e:
        if debug:
            print(f"Error al verificar el puerto: {e}")
        return False

def load_data(excel_path=None, historic_sheet=None, kpi_sheet=None, debug=False):
    """
    Carga datos desde un archivo Excel o JSON
    """
    try:
        if debug:
            print("\n=== CARGANDO DATOS ===")
            print(f"Archivo Excel: {excel_path}")
            print(f"Hoja histórica: {historic_sheet}")
            print(f"Hoja KPI: {kpi_sheet}")
        
        # Verificar si se proporcionó un archivo Excel
        if not excel_path:
            print("No se especificó archivo Excel")
            return None
        
        # Cargar datos desde Excel
        extractor = ExcelDataExtractor(excel_path)
        
        # Extraer datos históricos
        if historic_sheet:
            historic_data = extractor.extract_historic_data(historic_sheet)
            if debug:
                print(f"Datos históricos extraídos: {len(historic_data)} registros")
        else:
            historic_data = []
            if debug:
                print("No se especificó hoja de datos históricos")
        
        # Extraer datos KPI
        if kpi_sheet:
            kpi_data = extractor.extract_kpi_data(kpi_sheet)
            if debug:
                print(f"Datos KPI extraídos: {len(kpi_data)} registros")
        else:
            kpi_data = []
            if debug:
                print("No se especificó hoja de datos KPI")
        
        # Procesar los datos
        if debug:
            print("\n=== PROCESANDO DATOS ===")
        
        processor = DataProcessor(historic_data, kpi_data)
        processed_data = processor.process_data(debug=debug)
        
        if debug:
            print("\n=== DATOS PROCESADOS ===")
            print(f"Estructura de datos procesada:")
            print(f"  Claves principales: {list(processed_data.keys())}")
            print(f"  Número de celdas: {len(processed_data.get('cellData', {}))}")
            
            # Verificar datos históricos
            cells_with_historic = 0
            for cell_key, cell_data in processed_data['cellData'].items():
                if cell_data.get('hasHistoric', False):
                    cells_with_historic += 1
            
            print(f"  Celdas con datos históricos: {cells_with_historic}")
        
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
                import traceback
                traceback.print_exc()
        
        return processed_data
        
    except Exception as e:
        import traceback
        print(f"Error al cargar datos desde Excel: {e}")
        traceback.print_exc()
        return None

def create_dashboard(data, debug=False):
    """
    Crea un dashboard interactivo con Dash
    """
    if not data or 'cellData' not in data:
        print("Error: Datos inválidos para crear el dashboard")
        return None
    
    # Inicializar la aplicación Dash con tema Bootstrap
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    # Extraer valores únicos para los filtros
    cias = sorted(list(set(cell.get('CIA') for cell in data['cellData'].values() if 'CIA' in cell and cell['CIA'])))
    prjids = sorted(list(set(cell.get('PRJID') for cell in data['cellData'].values() if 'PRJID' in cell and cell['PRJID'])))
    
    # Definir el layout de la aplicación
    app.layout = html.Div([
        # Encabezado
        html.Div([
            html.H1("Dashboard de Seguimiento", style={'textAlign': 'center'}),
            html.Div(id='last-update-time', style={'textAlign': 'center', 'marginBottom': '10px'}),
            
            # Controles y filtros
            html.Div([
                # Fila para controles principales
                dbc.Row([
                    # Botón de actualización
                    dbc.Col(
                        html.Button('Actualizar Datos', id='refresh-button', n_clicks=0,
                                   style={'margin': '10px', 'padding': '10px 20px', 'backgroundColor': '#4CAF50', 
                                          'color': 'white', 'border': 'none', 'borderRadius': '5px'}),
                        width={"size": 3}
                    ),
                    
                    # Selector de tipo de visualización
                    dbc.Col(
                        html.Div([
                            html.Label("Tipo de visualización:"),
                            dcc.RadioItems(
                                id='visualization-type',
                                options=[
                                    {'label': 'KPI', 'value': 'kpi'},
                                    {'label': 'Histórico', 'value': 'historic'}
                                ],
                                value='kpi',  # Default to KPI view
                                labelStyle={'display': 'inline-block', 'margin-right': '20px'}
                            ),
                        ], style={'padding': '10px'}),
                        width={"size": 4}
                    ),
                    
                    # Filtros
                    dbc.Col(
                        html.Div([
                            html.Label("Filtros:"),
                            dbc.Row([
                                dbc.Col(
                                    dcc.Dropdown(
                                        id='cia-filter',
                                        options=[{'label': cia, 'value': cia} for cia in cias],
                                        placeholder="Filtrar por CIA",
                                        multi=True
                                    ),
                                    width=6
                                ),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id='prjid-filter',
                                        options=[{'label': prjid, 'value': prjid} for prjid in prjids],
                                        placeholder="Filtrar por PRJID",
                                        multi=True
                                    ),
                                    width=6
                                )
                            ])
                        ], style={'padding': '10px'}),
                        width={"size": 5}
                    )
                ], className="mb-4")
            ]),
            
            # Contenedor para gráficos
            html.Div([
                # Área de visualización principal
                html.Div(id='main-content')
            ]),
            
            # Almacenamiento de datos para actualización
            dcc.Store(id='dashboard-data', data=data),
            dcc.Store(id='filtered-data', data=data),  # Para almacenar datos filtrados
            dcc.Store(id='refresh-timestamp', data=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        ])
    ])
        # Callback para actualizar el timestamp cuando se hace clic en el botón de actualización
    @app.callback(
        [Output('dashboard-data', 'data'),
         Output('refresh-timestamp', 'data'),
         Output('last-update-time', 'children')],
        [Input('refresh-button', 'n_clicks')],
        [State('dashboard-data', 'data')]
    )
    def refresh_data(n_clicks, current_data):
        if n_clicks == 0:
            # Primera carga, usar los datos iniciales
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return current_data, timestamp, f"Última actualización: {timestamp}"
        
        # Intentar recargar los datos desde el archivo Excel
        try:
            # Usar las mismas rutas que en excel_to_plotly.py
            excel_path = "/Users/didac/Downloads/StoryMac/DashBTracker/PruebasCdM/Tchart_V06.xlsm"
            historic_sheet = "FrmBB_2"
            kpi_sheet = "FrmBB_3"
            
            # Cargar datos nuevamente
            extractor = ExcelDataExtractor(excel_path)
            historic_data = extractor.extract_historic_data(historic_sheet)
            kpi_data = extractor.extract_kpi_data(kpi_sheet)
            
            processor = DataProcessor(historic_data, kpi_data)
            new_data = processor.process_data(debug=True)
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return new_data, timestamp, f"Última actualización: {timestamp}"
        except Exception as e:
            import traceback
            print(f"Error al actualizar datos: {e}")
            traceback.print_exc()
            
            # En caso de error, mantener los datos actuales
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return current_data, timestamp, f"Error en actualización: {timestamp}"
    
    # Callback para aplicar filtros
    @app.callback(
        Output('filtered-data', 'data'),
        [Input('dashboard-data', 'data'),
         Input('cia-filter', 'value'),
         Input('prjid-filter', 'value')]
    )
    def filter_data(data, cia_filter, prjid_filter):
        if not data or 'cellData' not in data:
            return data
        
        # Si no hay filtros activos, devolver todos los datos
        if not cia_filter and not prjid_filter:
            return data
        
        # Crear una copia de los datos para no modificar los originales
        filtered_data = {'cellData': {}}
        
        # Aplicar filtros
        for cell_key, cell_data in data['cellData'].items():
            # Verificar filtro de CIA
            cia_match = True
            if cia_filter and 'CIA' in cell_data:
                cia_match = cell_data['CIA'] in cia_filter
            
            # Verificar filtro de PRJID
            prjid_match = True
            if prjid_filter and 'PRJID' in cell_data:
                prjid_match = cell_data['PRJID'] in prjid_filter
            
            # Si pasa ambos filtros, incluir en los datos filtrados
            if cia_match and prjid_match:
                filtered_data['cellData'][cell_key] = cell_data
        
        return filtered_data
    
    # Callback para actualizar el contenido principal
    @app.callback(
        Output('main-content', 'children'),
        [Input('visualization-type', 'value'),
         Input('filtered-data', 'data')]
    )
    def update_main_content(viz_type, data):
        if viz_type == 'kpi':
            return create_kpi_view(data)
        else:  # historic
            return create_historic_view(data)
    
    # Inicializar el contenido
    if debug:
        print("Dashboard creado correctamente")
    
    return app

def create_kpi_view(data):
    """
    Crea la vista de KPIs con tarjetas individuales para cada celda
    """
    if not data or 'cellData' not in data:
        return html.Div("No hay datos KPI disponibles", style={'padding': '20px', 'textAlign': 'center'})
    
    # Filtrar solo las celdas que tienen datos KPI
    kpi_cells = []
    for cell_key, cell_data in data['cellData'].items():
        # Verificar si la celda tiene datos KPI
        has_kpi = any(k in cell_data for k in ['KPREV', 'PDTE', 'REALPREV', 'PPTOPREV'])
        
        if has_kpi:
            # Verificar si todos los valores KPI son cero
            all_zeros = all(cell_data.get(k, 0) == 0 for k in ['KPREV', 'PDTE', 'REALPREV', 'PPTOPREV'])
            
            if not all_zeros:  # Solo incluir celdas con al menos un valor no cero
                kpi_cells.append(cell_data)
    
    if not kpi_cells:
        return html.Div("No se encontraron datos KPI para mostrar", style={'padding': '20px', 'textAlign': 'center'})
    
    # Ordenar las celdas por ROW y COLUMN
    kpi_cells.sort(key=lambda x: (x.get('ROW', ''), x.get('COLUMN', '')))
    
    # Crear tarjetas para cada celda con datos KPI
    kpi_cards = []
    for cell_data in kpi_cells:
        row = cell_data.get('ROW', 'N/A')
        column = cell_data.get('COLUMN', 'N/A')
        cia = cell_data.get('CIA', 'N/A')
        prjid = cell_data.get('PRJID', 'N/A')
        
        # Obtener valores KPI
        kprev = cell_data.get('KPREV', 0)
        pdte = cell_data.get('PDTE', 0)
        realprev = cell_data.get('REALPREV', 0)
        pptoprev = cell_data.get('PPTOPREV', 0)
        
        # Formatear valores según los requisitos:
        # - KPREV y PDTE en formato € sin decimales
        # - REALPREV y PPTOPREV en formato porcentual sin decimales
        try:
            # Asegurarse de que los valores son numéricos
            kprev = float(kprev) if kprev is not None else 0
            pdte = float(pdte) if pdte is not None else 0
            realprev = float(realprev) if realprev is not None else 0
            pptoprev = float(pptoprev) if pptoprev is not None else 0
            
            # Formatear como euros sin decimales
            kprev_formatted = f"{int(kprev):,} €".replace(",", ".")
            pdte_formatted = f"{int(pdte):,} €".replace(",", ".")
            
            # Formatear como porcentajes sin decimales
            realprev_formatted = f"{int(realprev * 100)}%"
            pptoprev_formatted = f"{int(pptoprev * 100)}%"
            
            # Determinar colores para cada valor
            kprev_color = '#28a745' if kprev >= 0 else '#dc3545'  # Verde para positivo, rojo para negativo
            pdte_color = '#28a745' if pdte >= 0 else '#dc3545'
            realprev_color = '#28a745' if realprev >= 0 else '#dc3545'
            pptoprev_color = '#28a745' if pptoprev >= 0 else '#dc3545'
            
        except (ValueError, TypeError) as e:
            # En caso de error, usar valores sin formato
            print(f"Error al formatear valores KPI: {e}")
            kprev_formatted = str(kprev)
            pdte_formatted = str(pdte)
            realprev_formatted = str(realprev)
            pptoprev_formatted = str(pptoprev)
            kprev_color = '#000000'
            pdte_color = '#000000'
            realprev_color = '#000000'
            pptoprev_color = '#000000'
        
        # Determinar el color de fondo según los valores
        bg_color = '#ffffff'  # Blanco por defecto
        
        # Aplicar lógica de colores según los valores
        if kprev is not None and kprev != 0:
            if kprev > 0:
                bg_color = '#d4edda'  # Verde claro para valores positivos
            else:
                bg_color = '#f8d7da'  # Rojo claro para valores negativos
        
        # Crear título de la celda simplificado (sin la palabra "Celda")
        if row and column and ":" in str(row) and ":" in str(column):
            # Si ROW y COLUMN tienen formato "código:descripción"
            cell_title = f"{row}, {column}"
        else:
            cell_title = f"{row}, {column}"
        
        # Crear una tarjeta para esta celda con diseño mejorado
        card = html.Div([
            # Encabezado de la tarjeta con gradiente
            html.Div([
                html.H5(cell_title, style={
                    'margin': '0',
                    'color': '#fff',
                    'fontWeight': '600',
                    'textShadow': '1px 1px 2px rgba(0,0,0,0.2)'
                }),
                html.H6(f"CIA: {cia} | PRJID: {prjid}", style={
                    'margin': '5px 0', 
                    'fontWeight': 'normal',
                    'color': '#f8f9fa'
                })
            ], style={
                'borderBottom': '1px solid #dee2e6', 
                'padding': '12px 15px',
                'borderRadius': '5px 5px 0 0',
                'background': 'linear-gradient(135deg, #4a6fa5 0%, #2c3e50 100%)'
            }),
            
            # Cuerpo de la tarjeta con los valores KPI
            html.Div([
                # Columna izquierda - Valores monetarios
                html.Div([
                    # K.Prev con valor en línea separada y badge
                    html.Div([
                        html.Div([
                            html.Span("K.Prev", style={'fontWeight': 'bold'}),
                            html.Span("€", style={
                                'backgroundColor': '#e9ecef', 
                                'padding': '2px 6px', 
                                'borderRadius': '12px', 
                                'fontSize': '0.8em',
                                'marginLeft': '5px'
                            })
                        ], style={'marginBottom': '5px'}),
                        html.Div(kprev_formatted, style={
                            'fontSize': '1.2em', 
                            'fontWeight': 'bold',
                            'color': kprev_color
                        })
                    ], style={'marginBottom': '15px'}),
                    
                    # PDTE con valor en línea separada y badge
                    html.Div([
                        html.Div([
                            html.Span("PDTE", style={'fontWeight': 'bold'}),
                            html.Span("€", style={
                                'backgroundColor': '#e9ecef', 
                                'padding': '2px 6px', 
                                'borderRadius': '12px', 
                                'fontSize': '0.8em',
                                'marginLeft': '5px'
                            })
                        ], style={'marginBottom': '5px'}),
                        html.Div(pdte_formatted, style={
                            'fontSize': '1.2em', 
                            'fontWeight': 'bold',
                            'color': pdte_color
                        })
                    ])
                ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                
                # Columna derecha - Valores porcentuales
                html.Div([
                    # REALPREV con valor en línea separada y badge
                    html.Div([
                        html.Div([
                            html.Span("REALPREV", style={'fontWeight': 'bold'}),
                            html.Span("%", style={
                                'backgroundColor': '#e9ecef', 
                                'padding': '2px 6px', 
                                'borderRadius': '12px', 
                                'fontSize': '0.8em',
                                'marginLeft': '5px'
                            })
                        ], style={'marginBottom': '5px', 'textAlign': 'right'}),
                        html.Div(realprev_formatted, style={
                            'fontSize': '1.2em', 
                            'fontWeight': 'bold',
                            'color': realprev_color,
                            'textAlign': 'right'
                        })
                    ], style={'marginBottom': '15px'}),
                    
                    # PPTOPREV con valor en línea separada y badge
                    html.Div([
                        html.Div([
                            html.Span("PPTOPREV", style={'fontWeight': 'bold'}),
                            html.Span("%", style={
                                'backgroundColor': '#e9ecef', 
                                'padding': '2px 6px', 
                                'borderRadius': '12px', 
                                'fontSize': '0.8em',
                                'marginLeft': '5px'
                            })
                        ], style={'marginBottom': '5px', 'textAlign': 'right'}),
                        html.Div(pptoprev_formatted, style={
                            'fontSize': '1.2em', 
                            'fontWeight': 'bold',
                            'color': pptoprev_color,
                            'textAlign': 'right'
                        })
                    ])
                ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'})
            ], style={'padding': '15px', 'backgroundColor': bg_color})
        ], style={
            'margin': '12px',
            'border': '1px solid #dee2e6',
            'borderRadius': '6px',
            'backgroundColor': '#ffffff',
            'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
            'width': '350px',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'transition': 'transform 0.3s ease, box-shadow 0.3s ease',
            ':hover': {
                'transform': 'translateY(-5px)',
                'boxShadow': '0 8px 16px rgba(0,0,0,0.15)'
            }
        })
        
        kpi_cards.append(card)
    
    return html.Div([
        html.H3("Vista de KPIs", style={
            'textAlign': 'center', 
            'marginBottom': '25px',
            'color': '#2c3e50',
            'fontWeight': '600',
            'borderBottom': '2px solid #4a6fa5',
            'paddingBottom': '10px',
            'maxWidth': '300px',
            'margin': '0 auto 30px auto'
        }),
        html.Div(kpi_cards, style={
            'display': 'flex',
            'flexWrap': 'wrap',
            'justifyContent': 'center',
            'padding': '10px'
        })
    ])

def create_historic_view(data):
    """
    Crea la vista de datos históricos con gráficos de línea
    """
    if not data or 'cellData' not in data:
        return html.Div("No hay datos históricos disponibles", style={'padding': '20px', 'textAlign': 'center'})
    
    # Depuración: Verificar datos históricos
    print("\n=== VERIFICACIÓN DE DATOS HISTÓRICOS PARA VISUALIZACIÓN ===")
    cells_with_historic = 0
    
    for cell_key, cell_data in data['cellData'].items():
        if 'historicData' in cell_data and len(cell_data.get('historicData', [])) > 0:
            cells_with_historic += 1
            print(f"Celda {cell_key} tiene {len(cell_data['historicData'])} registros históricos")
            
            # Mostrar el primer registro para verificar la estructura
            if len(cell_data['historicData']) > 0:
                first_entry = cell_data['historicData'][0]
                print(f"  Primer registro: WKS={first_entry.get('WKS')}, PREV={first_entry.get('PREV')}, PPTO={first_entry.get('PPTO')}, REAL={first_entry.get('REAL')}")
    
    print(f"Total de celdas con datos históricos: {cells_with_historic}")
    
    if cells_with_historic == 0:
        return html.Div("No se encontraron datos históricos para mostrar", 
                       style={'padding': '20px', 'textAlign': 'center'})
    
    # Crear tarjetas para cada celda con datos históricos
    historic_cards = []
    
    # Filtrar y ordenar las celdas por ROW y COLUMN
    historic_cells = []
    for cell_key, cell_data in data['cellData'].items():
        # Solo incluir celdas con datos históricos
        if 'historicData' in cell_data and len(cell_data.get('historicData', [])) > 0:
            # Verificar que hay al menos un registro con datos no nulos
            has_valid_data = False
            for entry in cell_data.get('historicData', []):
                prev = entry.get('PREV', 0)
                ppto = entry.get('PPTO', 0)
                real = entry.get('REAL', 0)
                
                try:
                    prev_val = float(prev) if prev is not None else 0
                    ppto_val = float(ppto) if ppto is not None else 0
                    real_val = float(real) if real is not None else 0
                    
                    # Limpiar valores si contienen símbolos de moneda o comas
                    if isinstance(prev_val, str):
                        prev_val = float(prev_val.replace('€', '').replace(',', '').replace('.', '').strip())
                    if isinstance(ppto_val, str):
                        ppto_val = float(ppto_val.replace('€', '').replace(',', '').replace('.', '').strip())
                    if isinstance(real_val, str):
                        real_val = float(real_val.replace('€', '').replace(',', '').replace('.', '').strip())
                    
                    if prev_val != 0 or ppto_val != 0 or real_val != 0:
                        has_valid_data = True
                        break
                except (ValueError, TypeError):
                    continue
            
            if has_valid_data:
                historic_cells.append(cell_data)
                print(f"Celda {cell_key} añadida a historic_cells con datos válidos")
            else:
                print(f"Celda {cell_key} tiene datos históricos pero todos son cero o nulos")
    
    # Ordenar por ROW y COLUMN
    historic_cells.sort(key=lambda x: (x.get('ROW', ''), x.get('COLUMN', '')))
    
    for cell_data in historic_cells:
        row = cell_data.get('ROW', 'N/A')
        column = cell_data.get('COLUMN', 'N/A')
        cia = cell_data.get('CIA', 'N/A')
        prjid = cell_data.get('PRJID', 'N/A')
        
        # Obtener datos históricos
        historic_data = cell_data.get('historicData', [])
        
        # Crear gráfico de línea para datos históricos
        fig = go.Figure()
        
        # Preparar datos para el gráfico
        weeks = []
        prev_values = []
        ppto_values = []
        real_values = []
        
        print(f"Procesando {len(historic_data)} registros históricos para celda {row}, {column}")
        
        for entry in historic_data:
            # Usar WKS como base temporal (formato año.semana)
            wks = entry.get('WKS', '')
            prev = entry.get('PREV', 0)
            ppto = entry.get('PPTO', 0)
            real = entry.get('REAL', 0)
            
            print(f"  Registro: WKS={wks}, PREV={prev}, PPTO={ppto}, REAL={real}")
            
            # Convertir a valores numéricos
            try:
                # Solo añadir si wks no es None
                if wks is not None:
                    # Convertir WKS a string para usarlo como etiqueta en el eje X
                    weeks.append(str(wks))
                    
                    # Limpiar y convertir valores si contienen símbolos de moneda o comas
                    if isinstance(prev, str):
                        prev = prev.replace('€', '').replace('.', '').replace(',', '.').strip()
                    if isinstance(ppto, str):
                        ppto = ppto.replace('€', '').replace('.', '').replace(',', '.').strip()
                    if isinstance(real, str):
                        real = real.replace('€', '').replace('.', '').replace(',', '.').strip()
                    
                    prev_values.append(float(prev) if prev and prev != '' else 0)
                    ppto_values.append(float(ppto) if ppto and ppto != '' else 0)
                    real_values.append(float(real) if real and real != '' else 0)
            except (ValueError, TypeError) as e:
                print(f"Error al procesar datos históricos: {e}, WKS: {wks}, PREV: {prev}, PPTO: {ppto}, REAL: {real}")
        
        # Ordenar por WKS (año.semana)
        if weeks:
            # Crear un diccionario para ordenar los datos
            data_dict = list(zip(weeks, prev_values, ppto_values, real_values))
            
            # Ordenar por WKS (año.semana)
            # Convertir a float para ordenar correctamente por año y semana
            data_dict.sort(key=lambda x: float(x[0]) if x[0] and x[0].replace('.', '', 1).isdigit() else 0)
            
            # Desempaquetar los datos ordenados
            weeks, prev_values, ppto_values, real_values = zip(*data_dict)
            
            print(f"Datos ordenados: {len(weeks)} semanas")
            print(f"Semanas ordenadas: {weeks}")
            
            # Añadir líneas al gráfico
            fig.add_trace(go.Scatter(
                x=weeks,
                y=prev_values,
                mode='lines+markers',
                line=dict(color='#4a6fa5', width=3),
                marker=dict(size=8, color='#4a6fa5'),
                name='PREV'
            ))
            
            fig.add_trace(go.Scatter(
                x=weeks,
                y=ppto_values,
                mode='lines+markers',
                line=dict(color='#28a745', width=3),
                marker=dict(size=8, color='#28a745'),
                name='PPTO'
            ))
            
            fig.add_trace(go.Scatter(
                x=weeks,
                y=real_values,
                mode='lines+markers',
                line=dict(color='#dc3545', width=3),
                marker=dict(size=8, color='#dc3545'),
                name='REAL'
            ))
            
            # Configurar layout del gráfico
            fig.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                height=300,
                xaxis=dict(
                    title='Semanas (Año.Semana)',
                    showgrid=True,
                    gridcolor='rgba(211, 211, 211, 0.3)',
                    tickangle=45,
                    # Asegurar que todas las etiquetas de semanas se muestren
                    tickmode='array',
                    tickvals=weeks,
                    ticktext=weeks
                ),
                yaxis=dict(
                    title='Valores (€)',
                    showgrid=True,
                    gridcolor='rgba(211, 211, 211, 0.3)',
                ),
                plot_bgcolor='rgba(255, 255, 255, 0.9)',
                paper_bgcolor='rgba(255, 255, 255, 0.9)',
                hovermode='closest',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Crear título de la celda simplificado
            if row and column and ":" in str(row) and ":" in str(column):
                cell_title = f"{row}, {column}"
            else:
                cell_title = f"{row}, {column}"
            
            # Obtener los últimos valores disponibles
            last_prev = prev_values[-1]
            last_ppto = ppto_values[-1]
            last_real = real_values[-1]
            
            # Formatear valores
            prev_formatted = f"{int(last_prev):,} €".replace(",", ".")
            ppto_formatted = f"{int(last_ppto):,} €".replace(",", ".")
            real_formatted = f"{int(last_real):,} €".replace(",", ".")
            
            # Colores para cada serie
            prev_color = '#4a6fa5'  # Azul para PREV
            ppto_color = '#28a745'  # Verde para PPTO
            real_color = '#dc3545'  # Rojo para REAL
            
            # Crear una tarjeta para esta celda con diseño mejorado
            card = html.Div([
                # Encabezado de la tarjeta con gradiente
                html.Div([
                    html.H5(cell_title, style={
                        'margin': '0',
                        'color': '#fff',
                        'fontWeight': '600',
                        'textShadow': '1px 1px 2px rgba(0,0,0,0.2)'
                    }),
                    html.H6(f"CIA: {cia} | PRJID: {prjid}", style={
                        'margin': '5px 0', 
                        'fontWeight': 'normal',
                        'color': '#f8f9fa'
                    })
                ], style={
                    'borderBottom': '1px solid #dee2e6', 
                    'padding': '12px 15px',
                    'borderRadius': '5px 5px 0 0',
                    'background': 'linear-gradient(135deg, #4a6fa5 0%, #2c3e50 100%)'
                }),
                
                # Cuerpo de la tarjeta con el gráfico y estadísticas
                html.Div([
                    # Gráfico
                    dcc.Graph(
                        figure=fig,
                        config={'displayModeBar': False},
                        style={'marginBottom': '15px'}
                    ),
                    
                    # Estadísticas en formato similar a los KPIs
                    html.Div([
                        # Columna izquierda - PREV y PPTO
                        html.Div([
                            # PREV
                            html.Div([
                                html.Div([
                                    html.Span("PREV", style={'fontWeight': 'bold'}),
                                    html.Span("€", style={
                                        'backgroundColor': '#e9ecef', 
                                        'padding': '2px 6px', 
                                        'borderRadius': '12px', 
                                        'fontSize': '0.8em',
                                        'marginLeft': '5px'
                                    })
                                ], style={'marginBottom': '2px'}),
                                html.Div(prev_formatted, style={
                                    'fontSize': '1.3em', 
                                    'color': prev_color,
                                    'fontWeight': 'bold',
                                    'padding': '3px 0'
                                })
                            ], style={'marginBottom': '15px', 'borderLeft': f'4px solid {prev_color}', 'paddingLeft': '10px'})
                        ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                        
                        # Columna derecha - PPTO
                        html.Div([
                            # PPTO
                            html.Div([
                                html.Div([
                                    html.Span("PPTO", style={'fontWeight': 'bold'}),
                                    html.Span("€", style={
                                        'backgroundColor': '#e9ecef', 
                                        'padding': '2px 6px', 
                                        'borderRadius': '12px', 
                                        'fontSize': '0.8em',
                                        'marginLeft': '5px'
                                    })
                                ], style={'marginBottom': '2px'}),
                                html.Div(ppto_formatted, style={
                                    'fontSize': '1.3em', 
                                    'color': ppto_color,
                                    'fontWeight': 'bold',
                                    'padding': '3px 0'
                                })
                            ], style={'marginBottom': '15px', 'borderLeft': f'4px solid {ppto_color}', 'paddingLeft': '10px'})
                        ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                        
                        # Columna derecha - REAL
                        html.Div([
                            # REAL
                            html.Div([
                                html.Div([
                                    html.Span("REAL", style={'fontWeight': 'bold'}),
                                    html.Span("€", style={
                                        'backgroundColor': '#e9ecef', 
                                        'padding': '2px 6px', 
                                        'borderRadius': '12px', 
                                        'fontSize': '0.8em',
                                        'marginLeft': '5px'
                                    })
                                ], style={'marginBottom': '2px'}),
                                html.Div(real_formatted, style={
                                    'fontSize': '1.3em', 
                                    'color': real_color,
                                    'fontWeight': 'bold',
                                    'padding': '3px 0'
                                })
                            ], style={'marginBottom': '15px', 'borderLeft': f'4px solid {real_color}', 'paddingLeft': '10px'})
                        ], style={'width': '100%', 'display': 'block', 'verticalAlign': 'top'})
                    ], style={'padding': '0 10px'})
                ], style={'padding': '15px'})
            ], style={
                'margin': '12px',
                'border': '1px solid #dee2e6',
                'borderRadius': '6px',
                'backgroundColor': '#ffffff',
                'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
                'width': '500px',
                'display': 'inline-block',
                'verticalAlign': 'top',
                'transition': 'transform 0.3s ease, box-shadow 0.3s ease',
                ':hover': {
                    'transform': 'translateY(-5px)',
                    'boxShadow': '0 8px 16px rgba(0,0,0,0.15)'
                }
            })
            
            historic_cards.append(card)
    
    # Si no hay tarjetas, mostrar mensaje
    if not historic_cards:
        return html.Div("No hay datos históricos disponibles", style={'padding': '20px', 'textAlign': 'center'})
    
    return html.Div([
        html.H3("Vista de Datos Históricos", style={
            'textAlign': 'center', 
            'marginBottom': '25px',
            'color': '#2c3e50',
            'fontWeight': '600',
            'borderBottom': '2px solid #4a6fa5',
            'paddingBottom': '10px',
            'maxWidth': '400px',
            'margin': '0 auto 30px auto'
        }),
        html.Div(historic_cards, style={
            'display': 'flex',
            'flexWrap': 'wrap',
            'justifyContent': 'center',
            'padding': '10px'
        })
    ])

def main():
    """
    Función principal para ejecutar el dashboard
    """
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Dashboard interactivo para visualización de datos')
    parser.add_argument('--excel', type=str, help='Ruta al archivo Excel')
    parser.add_argument('--historic-sheet', type=str, help='Nombre de la hoja con datos históricos')
    parser.add_argument('--kpi-sheet', type=str, help='Nombre de la hoja con datos KPI')
    parser.add_argument('--port', type=int, default=8050, help='Puerto para el servidor (default: 8050)')
    parser.add_argument('--debug', action='store_true', help='Activar modo de depuración')
    
    args = parser.parse_args()
    
    # Valores por defecto si no se especifican argumentos
    excel_path = args.excel or "/Users/didac/Downloads/StoryMac/DashBTracker/PruebasCdM/Tchart_V06.xlsm"
    historic_sheet = args.historic_sheet or "FrmBB_2"
    kpi_sheet = args.kpi_sheet or "FrmBB_3"
    port = args.port
    debug_mode = args.debug
    
    # Verificar si el puerto está disponible
    if not check_and_kill_process_on_port(port, debug=debug_mode):
        print(f"No se pudo liberar el puerto {port}. Intentando con puerto alternativo...")
        port = 8051
        if not check_and_kill_process_on_port(port, debug=debug_mode):
            print(f"No se pudo liberar el puerto {port}. Saliendo...")
            sys.exit(1)
    
    # Cargar datos
    data = load_data(excel_path, historic_sheet, kpi_sheet, debug=debug_mode)
    
    if not data:
        print("Error: No se pudieron cargar los datos. Saliendo...")
        sys.exit(1)
    
    # Crear dashboard
    app = create_dashboard(data, debug=debug_mode)
    
    if not app:
        print("Error: No se pudo crear el dashboard. Saliendo...")
        sys.exit(1)
    
    # Ejecutar el servidor
    print(f"\n=== INICIANDO SERVIDOR EN PUERTO {port} ===")
    print(f"Accede al dashboard en: http://127.0.0.1:{port}")
    
    app.run_server(debug=debug_mode, port=port)

if __name__ == "__main__":
    main()