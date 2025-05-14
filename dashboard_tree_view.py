"""
Dashboard Tree View (Árbol de Costes)
-------------------------------------
Visualización específica para los datos de tipo árbol de costes (DATATYPE="T").
"""

import plotly.graph_objects as go
from dash import html, dcc
import json
import pandas as pd
import dash
from dash import html, dcc, Input, Output, State, MATCH
import dash_bootstrap_components as dbc
from dash_utils import register_itmfrm_popup_callback

def create_tree_view(data, fasg5_filtrados=None, app=None):
    """
    Crea la vista de árbol con los datos proporcionados.
    fasg5_filtrados: datos filtrados de F_Asg5 (tipo I)
    app: instancia de Dash para registrar el callback
    """
    print("DEBUG: Iniciando create_tree_view")
    print(f"DEBUG: app es None? {app is None}")
    print(f"DEBUG: fasg5_filtrados es None? {fasg5_filtrados is None}")
    
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
            label = node_id
            children = node.get("children", [])
            nodes.append({
                "id": node_id,
                "parent": parent_id,
                "value": value,
                "label": label,
                "is_leaf": not children
            })
            for child in children:
                nodes.extend(flatten_tree(child, node_id))
            return nodes
        flat_nodes = flatten_tree(tree_structure)
        ids = [n["id"] for n in flat_nodes]
        parents = [n["parent"] for n in flat_nodes]
        values = [n["value"] for n in flat_nodes]
        labels = [n["label"] for n in flat_nodes]
        colors = ['red' if n["is_leaf"] else '#4a6fa5' for n in flat_nodes]
        fig = go.Figure(go.Treemap(
            ids=ids,
            parents=parents,
            values=values,
            labels=labels,
            branchvalues="total",
            textinfo="label+value",
            marker=dict(colors=colors)
        ))
        fig.update_layout(margin=dict(t=40, l=0, r=0, b=0))
        card = html.Div([
            html.H5(title, style={'margin': '0', 'color': '#fff', 'fontWeight': '600', 'padding': '12px 15px', 'borderRadius': '5px 5px 0 0', 'background': 'linear-gradient(135deg, #4a6fa5 0%, #2c3e50 100%)'}),
            html.Div([
                dcc.Graph(figure=fig, id={'type': 'treemap-graph', 'index': idx}, config={'displayModeBar': False}),
                dbc.Button("Incomings", id={'type': 'incomings-btn', 'index': idx}, color="primary", style={"marginTop": "10px"}),
                dcc.Store(id={'type': 'treemap-store', 'index': idx}),
                dbc.Modal([
                    dbc.ModalHeader("Detalle ITMFRM"),
                    dbc.ModalBody(id={'type': 'popup-body-datos-i', 'index': idx}),
                    dbc.ModalFooter(
                        dbc.Button("Cerrar", id={'type': 'close-popup-datos-i', 'index': idx}, className="ml-auto")
                    ),
                ], id={'type': 'popup-modal-datos-i', 'index': idx}, is_open=False),
            ], style={'padding': '15px'})
        ], style={
            'margin': '12px',
            'border': '1px solid #dee2e6',
            'borderRadius': '6px',
            'backgroundColor': '#ffffff',
            'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
            'width': '800px',
            'display': 'inline-block',
            'verticalAlign': 'top'
        })
        tree_cards.append(card)
    
    layout = html.Div([
        html.Div(tree_cards, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center', 'gap': '20px', 'padding': '20px'}),
        html.Div(id='tree-view-container'),
        html.Div(id='debug-output', style={'margin': '20px', 'padding': '10px', 'border': '1px solid red', 'backgroundColor': '#fff3cd'})
    ])

    # Registrar callback para guardar el id del nodo hoja clicado
    # (El callback se registrará globalmente en dashboard_main.py)
    return layout

def export_tree_to_excel(tree_structure, filename="tree_structure.xlsx"):
    """
    Exporta la estructura jerárquica a un archivo Excel
    """
    # Lista para almacenar los datos planos
    flat_data = []
    
    def process_node(node, level=0, parent_path=""):
        item_id = node.get('itm_id', '')
        description = node.get('description', '')
        value = node.get('value', 0)
        
        # Crear path completo
        current_path = f"{parent_path}/{item_id}" if parent_path else item_id
        
        # Añadir a la lista plana
        flat_data.append({
            'Nivel': level,
            'ID': item_id,
            'Descripción': description,
            'Valor': value,
            'Path': current_path,
            'Indentación': '  ' * level + item_id
        })
        
        # Procesar hijos
        for child in node.get('children', []):
            process_node(child, level + 1, current_path)
    
    # Procesar el árbol
    process_node(tree_structure)
    
    # Crear DataFrame
    df = pd.DataFrame(flat_data)
    
    # Exportar a Excel
    df.to_excel(filename, index=False)
    print(f"Estructura del árbol exportada a {filename}")

# Añade estos componentes a tu layout donde corresponda:
layout = html.Div([
    dcc.Store(id='selected-leaf-node-datos-i', data=None),
    dbc.Modal(
        [
            dbc.ModalHeader("Detalle ITMFRM"),
            dbc.ModalBody(id="popup-body-datos-i"),
            dbc.ModalFooter(
                dbc.Button("Cerrar", id="close-popup-datos-i", className="ml-auto")
            ),
        ],
        id="popup-modal-datos-i",
        is_open=False,
    ),
    html.Div(id='tree-view-container')
])
