#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo para la vista de KPIs del dashboard
"""
from dash import html, dcc
import plotly.graph_objects as go

def create_kpi_card(cell_data):
    """
    Crea una tarjeta individual para visualizar datos KPI
    """
    def clean_label(label):
        if label and ":" in label:
            return label.split(":", 1)[1].strip()
        return label or ""
    
    # Obtener datos KPI
    kpis = cell_data.get('DATACONTENTS', {})
    hprev = kpis.get('KPREV', 0)
    pdte = kpis.get('PDTE', 0)
    realprev = kpis.get('REALPREV', 0)
    pptoprev = kpis.get('PPTOPREV', 0)
    
    # Crear título de la tarjeta
    title = f"{clean_label(cell_data.get('ROW', ''))} - {clean_label(cell_data.get('COLUMN', ''))}"
    
    # Crear gráfico de barras más estrechas, etiquetas eje Y giradas 90º
    def format_val(val):
        if abs(val) >= 1000:
            return f"{int(val/1000)}k€"
        else:
            return f"{val:.0f}€"
    
    bar_fig = go.Figure()
    bar_fig.add_trace(go.Bar(
        x=[hprev],
        y=['HPREV'],
        orientation='h',
        marker_color='#28a745',
        name='HPREV',
        hoverinfo='skip',
        showlegend=False,
        width=0.3
    ))
    bar_fig.add_trace(go.Bar(
        x=[pdte],
        y=['PDTE'],
        orientation='h',
        marker_color='#dc3545',
        name='PDTE',
        hoverinfo='skip',
        showlegend=False,
        width=0.3
    ))
    bar_fig.update_layout(
        height=80,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        barmode='group',
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(showgrid=False, showticklabels=False, visible=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=14, color='#2c3e50'), tickangle=0, automargin=True),
    )
    # Valores alineados a la derecha, fuera del gráfico
    bar_values = html.Div([
        html.Div(format_val(pdte), style={'color': '#dc3545', 'fontWeight': 'bold', 'fontSize': '14px', 'textAlign': 'right', 'marginBottom': '8px', 'textShadow': '0 1px 2px #fff'}),
        html.Div(format_val(hprev), style={'color': '#28a745', 'fontWeight': 'bold', 'fontSize': '14px', 'textAlign': 'right', 'textShadow': '0 1px 2px #fff'})
    ], style={'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'space-between', 'height': '80px', 'minWidth': '50px'})
    
    # Crear gráficos circulares separados para REALPREV y PPTOPREV
    def donut_figure(value, color_main, label):
        # Redondear a 1 decimal y forzar a 1.0 si está cerca de 1
        if 0.99 <= value <= 1.01:
            value = 1.0
        val_rounded = round(abs(value), 1)
        val_int = int(round(val_rounded * 100))
        text_color = '#222'
        label_div = html.Div(label, style={
            'textAlign': 'center',
            'fontWeight': 'bold',
            'fontSize': '13px',
            'color': '#2c3e50',
            'marginBottom': '2px',
            'background': 'rgba(240,240,240,0.7)',
            'borderRadius': '8px 8px 0 0',
            'boxShadow': '0 1px 4px rgba(44,62,80,0.07)'
        })
        if value <= 0:
            fig = go.Figure(go.Pie(
                values=[1],
                marker_colors=['#dc3545'],
                textinfo='none',
                hole=0.5
            ))
        elif 0 < value < 1:
            fig = go.Figure(go.Pie(
                values=[val_rounded, 1-val_rounded],
                labels=['', ''],
                marker_colors=[color_main, '#f8f9fa'],
                textinfo='none',
                hole=0.5
            ))
        else:
            fig = go.Figure(go.Pie(
                values=[1],
                labels=[''],
                marker_colors=[color_main],
                textinfo='none',
                hole=0.5
            ))
        fig.update_layout(
            showlegend=False,
            annotations=[
                dict(text=f"{val_int}%", x=0.5, y=0.5, font_size=16, showarrow=False, font_color=text_color)
            ],
            margin=dict(l=0, r=0, t=0, b=0),
            height=90,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        return html.Div([
            label_div,
            dcc.Graph(figure=fig, config={'displayModeBar': False})
        ], style={'marginBottom': '0', 'marginTop': '0'})
    
    realprev_div = donut_figure(realprev, '#28a745' if realprev >= 0 else '#dc3545', 'REALPREV')
    pptoprev_div = donut_figure(pptoprev, '#4a6fa5' if pptoprev >= 0 else '#dc3545', 'PPTOPREV')
    
    # Crear la tarjeta
    return html.Div([
        html.Div([
            html.H5(title, style={
                'margin': '0',
                'color': '#fff',
                'fontWeight': '600',
                'fontSize': '16px',
                'textShadow': '0 2px 4px rgba(44,62,80,0.12)'
            })
        ], style={
            'borderBottom': '1px solid #dee2e6',
            'padding': '10px 15px',
            'borderRadius': '12px 12px 0 0',
            'background': 'linear-gradient(135deg, #4a6fa5 0%, #2c3e50 100%)'
        }),
        
        # Cuerpo de la tarjeta con los gráficos
        html.Div([
            html.Div([
                dcc.Graph(figure=bar_fig, config={'displayModeBar': False})
            ], style={'width': 'calc(100% - 60px)', 'display': 'inline-block', 'verticalAlign': 'top'}),
            html.Div(bar_values, style={'width': '60px', 'display': 'inline-block', 'verticalAlign': 'top'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '18px', 'marginTop': '5px'}),
        html.Div([
            html.Div(realprev_div, style={'width': '50%', 'display': 'inline-block', 'paddingRight': '8px'}),
            html.Div(pptoprev_div, style={'width': '50%', 'display': 'inline-block', 'paddingLeft': '8px'})
        ], style={'display': 'flex', 'paddingBottom': '10px'})
    ], style={
        'margin': '12px',
        'border': '1px solid #dee2e6',
        'borderRadius': '12px',
        'backgroundColor': '#ffffff',
        'boxShadow': '0 4px 12px rgba(44,62,80,0.10)',
        'width': '350px',
        'display': 'inline-block',
        'verticalAlign': 'top',
        'transition': 'box-shadow 0.2s',
        'overflow': 'hidden'
    })

def create_kpi_view(data):
    """
    Crea la vista de KPIs con tarjetas individuales para cada celda
    """
    if not data:
        return html.Div("No hay datos KPI disponibles", style={'padding': '20px', 'textAlign': 'center'})
    
    # Crear tarjetas para cada celda con datos KPI
    kpi_cards = []
    
    for cell_data in data:
        if cell_data.get('DATATYPE') == 'K' and cell_data.get('DATACONTENTS'):
            card = create_kpi_card(cell_data)
            kpi_cards.append(card)
    
    if not kpi_cards:
        return html.Div("No se encontraron datos KPI para mostrar", style={'padding': '20px', 'textAlign': 'center'})
    
    return html.Div([
        # html.H3("Vista de KPIs", style={
        #     'textAlign': 'center', 
        #     'marginBottom': '25px',
        #     'color': '#2c3e50',
        #     'fontWeight': '600'
        # }),
        html.Div(kpi_cards, style={
            'display': 'flex',
            'flexWrap': 'wrap',
            'justifyContent': 'center',
            'padding': '10px'
        })
    ])