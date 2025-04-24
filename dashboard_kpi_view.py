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
    if not data:
        return html.Div("No hay datos KPI disponibles", style={'padding': '20px', 'textAlign': 'center'})
    
    # Crear tarjetas para cada celda con datos KPI
    kpi_cards = []
    
    for cell_data in data:
        # Verificar si la celda tiene datos KPI
        if 'CONTENIDO' in cell_data and 'KPIS' in cell_data['CONTENIDO']:
            kpis = cell_data['CONTENIDO']['KPIS']
            
            # Crear una tarjeta para esta celda
            card = html.Div([
                # Encabezado de la tarjeta
                html.Div([
                    html.H5(f"{cell_data['ROW']}, {cell_data['COLUMN']}", style={
                        'margin': '0',
                        'color': '#fff',
                        'fontWeight': '600'
                    }),
                    html.H6(f"CIA: {cell_data['CIA']} | PRJID: {cell_data['PRJID']}", style={
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
                    # KPREV
                    html.Div([
                        html.Span("K.Prev: ", style={'fontWeight': 'bold'}),
                        html.Span(f"{kpis.get('KPREV', 0):,.2f} €".replace(",", "."), 
                                style={'color': '#28a745' if kpis.get('KPREV', 0) >= 0 else '#dc3545'})
                    ], style={'marginBottom': '10px'}),
                    
                    # PDTE
                    html.Div([
                        html.Span("PDTE: ", style={'fontWeight': 'bold'}),
                        html.Span(f"{kpis.get('PDTE', 0):,.2f} €".replace(",", "."), 
                                style={'color': '#28a745' if kpis.get('PDTE', 0) >= 0 else '#dc3545'})
                    ], style={'marginBottom': '10px'}),
                    
                    # REALPREV
                    html.Div([
                        html.Span("REALPREV: ", style={'fontWeight': 'bold'}),
                        html.Span(f"{kpis.get('REALPREV', 0):,.2%}", 
                                style={'color': '#28a745' if kpis.get('REALPREV', 0) >= 0 else '#dc3545'})
                    ], style={'marginBottom': '10px'}),
                    
                    # PPTOPREV
                    html.Div([
                        html.Span("PPTOPREV: ", style={'fontWeight': 'bold'}),
                        html.Span(f"{kpis.get('PPTOPREV', 0):,.2%}", 
                                style={'color': '#28a745' if kpis.get('PPTOPREV', 0) >= 0 else '#dc3545'})
                    ])
                ], style={'padding': '15px'})
            ], style={
                'margin': '12px',
                'border': '1px solid #dee2e6',
                'borderRadius': '6px',
                'backgroundColor': '#ffffff',
                'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
                'width': '350px',
                'display': 'inline-block',
                'verticalAlign': 'top'
            })
            
            kpi_cards.append(card)
    
    if not kpi_cards:
        return html.Div("No se encontraron datos KPI para mostrar", style={'padding': '20px', 'textAlign': 'center'})
    
    return html.Div([
        html.H3("Vista de KPIs", style={
            'textAlign': 'center', 
            'marginBottom': '25px',
            'color': '#2c3e50',
            'fontWeight': '600'
        }),
        html.Div(kpi_cards, style={
            'display': 'flex',
            'flexWrap': 'wrap',
            'justifyContent': 'center',
            'padding': '10px'
        })
    ])