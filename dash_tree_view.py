"""
Dashboard Tree View (Árbol de Costes)
-------------------------------------
Visualización específica para los datos de tipo árbol de costes (DATATYPE="T").
"""

import plotly.graph_objects as go
from dash import html, dcc
import pandas as pd

def create_tree_view(data):
    """
    Crea la vista de árbol con los datos proporcionados.
    """
    tree_data = [row for row in data if row.get("DATATYPE") == "T"]
    if not tree_data:
        return html.Div("No hay datos de árbol de costes disponibles", style={'text-align': 'center', 'margin-top': '20px'})
    
    tree_cards = []
    for idx, row in enumerate(tree_data):
        if not row.get("DATACONTENTS"):
            continue
        tree_structure = row.get("DATACONTENTS", {})
        
        def clean_label(label):
            if label and ":" in label:
                return label.split(":", 1)[1].strip()
            return label or ""
        
        title = f"{clean_label(row.get('ROW', ''))} - {clean_label(row.get('COLUMN', ''))}"
        
        def flatten_tree(node, parent_id=""):
            nodes = []
            node_id = node.get("id", "")
            value = node.get("value", 0)
            value_str = f"{int(round(value)):,} €".replace(",", ".")
            itmfrm = node.get("itmfrm", None)
            children = node.get("children", [])
            
            # Si tiene hijos o no hay ITMFRM, mostrar "-"
            if children or not itmfrm or not isinstance(itmfrm, str) or not itmfrm.strip():
                itmfrm_str = "-"
            else:
                itmfrm_str = itmfrm.strip()
            
            # Etiqueta en 3 líneas: LEVEL-NODE-ITMIN, VALUE, ITMFRM
            # Usar <br> para forzar saltos de línea en Plotly
            label = f"{node_id}<br>{value_str}<br>{itmfrm_str}"
            
            nodes.append({
                "id": node_id,
                "parent": parent_id,
                "value": value,
                "label": label,
                "itmfrm": itmfrm_str
            })
            
            for child in children:
                nodes.extend(flatten_tree(child, node_id))
            return nodes
        
        try:
            flat_nodes = flatten_tree(tree_structure)
            ids = [n["id"] for n in flat_nodes]
            parents = [n["parent"] for n in flat_nodes]
            values = [n["value"] for n in flat_nodes]
            labels = [n["label"] for n in flat_nodes]
            itmfrms = [n["itmfrm"] for n in flat_nodes]
            
            # Colores diferentes para nodos hoja con ITMFRM
            colors = ['#2c3e50' if itmfrm == "-" else '#4a6fa5' for itmfrm in itmfrms]
            
            fig = go.Figure(go.Treemap(
                ids=ids,
                parents=parents,
                values=values,
                labels=labels,
                branchvalues="total",
                textinfo="label",
                textposition="middle center",
                insidetextfont=dict(
                    size=11,
                    family="Arial",
                    color="white"
                ),
                marker=dict(
                    colors=colors,
                    line=dict(width=1, color='#ffffff')
                ),
                hovertemplate="<b>%{label}</b><br>Valor: %{value:,.0f}€<extra></extra>"
            ))
            
            fig.update_layout(
                margin=dict(t=40, l=0, r=0, b=0),
                height=600,
                uniformtext=dict(
                    minsize=10,
                    mode='show'
                ),
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            card = html.Div([
                html.H5(title, style={
                    'margin': '0',
                    'color': '#fff',
                    'fontWeight': '600',
                    'padding': '12px 15px',
                    'borderRadius': '5px 5px 0 0',
                    'background': 'linear-gradient(135deg, #4a6fa5 0%, #2c3e50 100%)'
                }),
                html.Div([
                    dcc.Graph(
                        figure=fig,
                        config={'displayModeBar': False}
                    ),
                ], style={'padding': '15px'})
            ], style={
                'margin': '12px',
                'border': '1px solid #dee2e6',
                'borderRadius': '6px',
                'backgroundColor': '#ffffff',
                'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
                'width': '900px',
                'display': 'inline-block',
                'verticalAlign': 'top'
            })
            tree_cards.append(card)
        except Exception as e:
            continue

    return html.Div(
        tree_cards,
        style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center', 'gap': '20px', 'padding': '20px'}
    )
