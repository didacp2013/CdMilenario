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
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

def create_tree_view(data, fasg5_filtrados=None):
    """
    Crea la vista de árbol con los datos proporcionados.
    fasg5_filtrados: datos filtrados de F_Asg5 (tipo I)
    """
    # Crear el layout base
    layout = html.Div([
        dcc.Store(id='tree-data-store'),
        # --- INICIO: Callback popup desactivado temporalmente ---
        # dbc.Modal([
        #     dbc.ModalHeader("Detalles del Item"),
        #     dbc.ModalBody(id='item-details-content'),
        #     dbc.ModalFooter(
        #         dbc.Button("Cerrar", id="close-item-modal", className="ms-auto", n_clicks=0)
        #     ),
        # ], id="item-modal", is_open=False),
        html.Div(id='tree-view-container')
    ])

    # --- INICIO: Callback popup desactivado temporalmente ---
    # @dash.callback(
    #     [Output('item-modal', 'is_open'),
    #      Output('item-details-content', 'children')],
    #     [Input('treemap-graph', 'clickData')],
    #     [State('item-modal', 'is_open'),
    #      State('cia-filter', 'value'),
    #      State('prjid-filter', 'value')]
    # )
    # def toggle_item_modal(click_data, is_open, cia, prjid):
    #     ...
    # --- FIN: Callback popup desactivado temporalmente ---

    # --- INICIO: Callback cerrar modal desactivado temporalmente ---
    # @dash.callback(
    #     Output('item-modal', 'is_open', allow_duplicate=True),
    #     [Input('close-item-modal', 'n_clicks')],
    #     [State('item-modal', 'is_open')],
    #     prevent_initial_call=True
    # )
    # def close_modal(n_clicks, is_open):
    #     ...
    # --- FIN: Callback cerrar modal desactivado temporalmente ---

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
