#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo para la vista de KPIs del dashboard
"""
from dash import html

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