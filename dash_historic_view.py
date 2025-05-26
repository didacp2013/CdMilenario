#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo para la vista histórica del dashboard
"""
import plotly.graph_objects as go
from dash import html, dcc

def create_historic_view(data):
    """
    Crea la vista de datos históricos con gráficos de línea
    """
    if not data:
        return html.Div("No hay datos históricos disponibles", style={'padding': '20px', 'textAlign': 'center'})
    historic_cards = []
    # Filtrar y ordenar las celdas por ROW y COLUMN
    historic_cells = [cell_data for cell_data in data if cell_data.get('DATATYPE') == 'H' and cell_data.get('DATACONTENTS')]
    historic_cells.sort(key=lambda x: (x.get('ROW', ''), x.get('COLUMN', '')))
    def clean_label(label):
        if label and ":" in label:
            return label.split(":", 1)[1].strip()
        return label or ""
    for cell_data in historic_cells:
        row = cell_data.get('ROW', 'N/A')
        column = cell_data.get('COLUMN', 'N/A')
        historic_data = cell_data.get('DATACONTENTS', [])
        fig = go.Figure()
        serials = []
        date_labels = []
        hprev_values = []
        ppto_values = []
        real_values = []
        for entry in historic_data:
            wks_serial = entry.get('WKS_SERIAL', None)
            wks_date = entry.get('WKS_DATE', '')
            hprev = entry.get('HPREV', 0)
            ppto = entry.get('PPTO', 0)
            real = entry.get('REAL', 0)
            if wks_serial is not None:
                serials.append(float(wks_serial))
                date_labels.append(str(wks_date))
                hprev_values.append(float(hprev) if hprev is not None else 0)
                ppto_values.append(float(ppto) if ppto is not None else 0)
                real_values.append(float(real) if real is not None else 0)
        if serials and date_labels:
            data_dict = list(zip(serials, date_labels, hprev_values, ppto_values, real_values))
            data_dict.sort(key=lambda x: x[0])
            serials, date_labels, hprev_values, ppto_values, real_values = zip(*data_dict)
            serials = list(serials)
            date_labels = list(date_labels)
            fig.add_trace(go.Scatter(
                x=serials,
                y=hprev_values,
                mode='lines+markers',
                line=dict(color='#4a6fa5', width=3),
                marker=dict(size=8, color='#4a6fa5'),
                name='HPREV',
                text=date_labels,
                hovertemplate='%{text}<br>HPREV: %{y}'
            ))
            fig.add_trace(go.Scatter(
                x=serials,
                y=ppto_values,
                mode='lines+markers',
                line=dict(color='#28a745', width=3),
                marker=dict(size=8, color='#28a745'),
                name='PPTO',
                text=date_labels,
                hovertemplate='%{text}<br>PPTO: %{y}'
            ))
            fig.add_trace(go.Scatter(
                x=serials,
                y=real_values,
                mode='lines+markers',
                line=dict(color='#dc3545', width=3),
                marker=dict(size=8, color='#dc3545'),
                name='REAL',
                text=date_labels,
                hovertemplate='%{text}<br>REAL: %{y}'
            ))
            fig.update_layout(
                margin=dict(l=20, r=20, t=20, b=80),
                height=420,
                width=1260,
                showlegend=False,
                xaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(211, 211, 211, 0.3)',
                    tickangle=45,
                    tickmode='array',
                    tickvals=serials,
                    ticktext=date_labels,
                    showticklabels=True,
                    title=None,
                    automargin=True,
                    tickfont=dict(size=9, family="Consolas, Menlo, monospace")
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(211, 211, 211, 0.3)',
                    title=None,
                    automargin=True,
                    tickfont=dict(size=14)
                ),
                plot_bgcolor='rgba(255, 255, 255, 0.9)',
                paper_bgcolor='rgba(255, 255, 255, 0.9)',
                hovermode='closest',
            )
            cell_title = f"{clean_label(row)} - {clean_label(column)}"
            card = html.Div([
                html.Div([
                    html.H5(cell_title, style={
                        'margin': '0',
                        'color': '#fff',
                        'fontWeight': '600',
                        'textShadow': '1px 1px 2px rgba(0,0,0,0.2)'
                    })
                ], style={
                    'borderBottom': '1px solid #dee2e6',
                    'padding': '12px 15px',
                    'borderRadius': '5px 5px 0 0',
                    'background': 'linear-gradient(135deg, #4a6fa5 0%, #2c3e50 100%)'
                }),
                html.Div([
                    dcc.Graph(
                        figure=fig,
                        config={'displayModeBar': False},
                        style={'width': '1260px', 'height': '420px', 'margin': '0 auto'}
                    )
                ])
            ], style={
                'margin': '12px',
                'border': '1px solid #dee2e6',
                'borderRadius': '6px',
                'backgroundColor': '#ffffff',
                'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
                'width': '1260px',
                'display': 'block',
                'verticalAlign': 'top'
            })
            historic_cards.append(card)
    if not historic_cards:
        return html.Div("No se encontraron datos históricos para mostrar", style={'padding': '20px', 'textAlign': 'center'})
    return html.Div([
        # html.H3("Vista Histórica", style={
        #     'textAlign': 'center',
        #     'marginBottom': '25px',
        #     'color': '#2c3e50',
        #     'fontWeight': '600'
        # }),
        html.Div(historic_cards, style={
            'display': 'block',
            'padding': '10px'
        })
    ])