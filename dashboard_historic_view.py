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
    
    # Depuración: Verificar datos históricos
    print("\n=== VERIFICACIÓN DE DATOS HISTÓRICOS PARA VISUALIZACIÓN ===")
    cells_with_historic = 0
    
    for cell_data in data:
        if 'CONTENIDO' in cell_data and 'HISTORICOS' in cell_data['CONTENIDO']:
            cells_with_historic += 1
            historic_data = cell_data['CONTENIDO']['HISTORICOS']
            print(f"Celda {cell_data.get('ROW')} tiene {len(historic_data)} registros históricos")
            
            # Mostrar el primer registro para verificar la estructura
            if len(historic_data) > 0:
                first_entry = historic_data[0]
                print(f"  Primer registro: WKS={first_entry.get('WKS')}, PREV={first_entry.get('PREV')}, PPTO={first_entry.get('PPTO')}, REAL={first_entry.get('REAL')}")
    
    print(f"Total de celdas con datos históricos: {cells_with_historic}")
    
    if cells_with_historic == 0:
        return html.Div("No se encontraron datos históricos para mostrar", 
                       style={'padding': '20px', 'textAlign': 'center'})
    
    # Crear tarjetas para cada celda con datos históricos
    historic_cards = []
    
    # Filtrar y ordenar las celdas por ROW y COLUMN
    historic_cells = []
    for cell_data in data:
        # Solo incluir celdas con datos históricos
        if 'CONTENIDO' in cell_data and 'HISTORICOS' in cell_data['CONTENIDO']:
            historic_data = cell_data['CONTENIDO']['HISTORICOS']
            # Verificar que hay al menos un registro con datos no nulos
            has_valid_data = False
            for entry in historic_data:
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
                print(f"Celda {cell_data.get('ROW')} añadida a historic_cells con datos válidos")
            else:
                print(f"Celda {cell_data.get('ROW')} tiene datos históricos pero todos son cero o nulos")
    
    # Ordenar por ROW y COLUMN
    historic_cells.sort(key=lambda x: (x.get('ROW', ''), x.get('COLUMN', '')))
    
    for cell_data in historic_cells:
        row = cell_data.get('ROW', 'N/A')
        column = cell_data.get('COLUMN', 'N/A')
        cia = cell_data.get('CIA', 'N/A')
        prjid = cell_data.get('PRJID', 'N/A')
        
        # Obtener datos históricos
        historic_data = cell_data['CONTENIDO']['HISTORICOS']
        
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
                
                # Cuerpo de la tarjeta con el gráfico y los valores actuales
                html.Div([
                    # Gráfico de línea
                    dcc.Graph(
                        figure=fig,
                        config={'displayModeBar': False}
                    ),
                    
                    # Valores actuales
                    html.Div([
                        html.Div([
                            html.Span("PREV: ", style={'fontWeight': 'bold', 'color': prev_color}),
                            html.Span(prev_formatted, style={'color': prev_color})
                        ], style={'marginBottom': '10px'}),
                        
                        html.Div([
                            html.Span("PPTO: ", style={'fontWeight': 'bold', 'color': ppto_color}),
                            html.Span(ppto_formatted, style={'color': ppto_color})
                        ], style={'marginBottom': '10px'}),
                        
                        html.Div([
                            html.Span("REAL: ", style={'fontWeight': 'bold', 'color': real_color}),
                            html.Span(real_formatted, style={'color': real_color})
                        ])
                    ], style={'padding': '15px'})
                ])
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
            
            historic_cards.append(card)
    
    if not historic_cards:
        return html.Div("No se encontraron datos históricos para mostrar", style={'padding': '20px', 'textAlign': 'center'})
    
    return html.Div([
        html.H3("Vista Histórica", style={
            'textAlign': 'center', 
            'marginBottom': '25px',
            'color': '#2c3e50',
            'fontWeight': '600'
        }),
        html.Div(historic_cards, style={
            'display': 'flex',
            'flexWrap': 'wrap',
            'justifyContent': 'center',
            'padding': '10px'
        })
    ])