"""
Dashboard Tree View (Árbol de Costes)
-------------------------------------
Visualización específica para los datos de tipo árbol de costes (DATATYPE="T").
"""

import plotly.graph_objects as go
from dash import html, dcc
import json
import pandas as pd
import numpy as np

# Función create_tree_view eliminada

def create_treemap_figure(tree_structure, title=""):
    """
    Crea una figura de treemap usando Plotly Express a partir de una estructura de árbol jerárquica.
    Usa 'id' como etiqueta visible.
    """
    import plotly.express as px

    # Si tree_structure es una lista de raíces, pásala directamente
    # Si es un solo dict raíz, conviértelo en lista
    if isinstance(tree_structure, dict):
        tree_structure = [tree_structure]

    # Plotly Express espera un DataFrame o una lista de dicts con claves 'id', 'parent', 'value'
    # Pero si tienes jerarquía, puedes usar el parámetro path
    # Vamos a construir un DataFrame solo si es necesario, pero intentaremos usar path

    # Si tus nodos tienen 'children', necesitas convertir la jerarquía a un DataFrame con path
    # Pero si tienes una estructura simple, puedes hacer:
    import pandas as pd

    def extract_paths(node, path=None):
        if path is None:
            path = []
        current_path = path + [node["id"]]
        rows = []
        if "children" in node and node["children"]:
            for child in node["children"]:
                rows.extend(extract_paths(child, current_path))
        else:
            # Nodo hoja
            rows.append({"path": current_path, "value": node.get("value", 0)})
        return rows

    flat_rows = []
    for root in tree_structure:
        flat_rows.extend(extract_paths(root))

    df = pd.DataFrame(flat_rows)

    fig = px.treemap(
        df,
        path=['path'],
        values='value',
        title=title
    )
    fig.update_layout(margin=dict(t=40, l=0, r=0, b=0))
    return fig

def debug_tree_json(tree_structure):
    """
    Imprime la estructura del árbol en formato JSON con indentación
    """
    pass


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


def debug_tree_structure(tree_structure, level=0, prefix=""):
    """
    Imprime la estructura jerárquica del árbol en la terminal
    """
    pass


def render_tree_view(data):
    """
    Renderiza la vista de árbol utilizando los datos de tipo T
    """
    from dash import html, dcc  # Asegúrate de importar si no está
    def clean_label(label):
        if label and ":" in label:
            return label.split(":", 1)[1].strip()
        return label or ""
    
    tree_data = [row for row in data if row.get("DATATYPE") == "T"]
    if not tree_data:
        return html.Div("No hay datos de árbol de costes disponibles", style={'text-align': 'center', 'margin-top': '20px'})
    
    # Procesamos los datos para convertirlos en estructura de árbol
    tree_cards = []
    for row in tree_data:
        if not row.get("DATACONTENTS"):
            continue
        
        tree_structure = row.get("DATACONTENTS", [])
        title = f"{clean_label(row.get('ROW', ''))} - {clean_label(row.get('COLUMN', ''))}"
        
        fig = create_treemap_figure(tree_structure, title="")
        card = html.Div([
            html.H5(title, style={'margin': '0', 'color': '#fff', 'fontWeight': '600', 'padding': '12px 15px', 'borderRadius': '5px 5px 0 0', 'background': 'linear-gradient(135deg, #4a6fa5 0%, #2c3e50 100%)'}),
            html.Div([
                dcc.Graph(figure=fig, id='treemap-graph', config={'displayModeBar': False})
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
    
    return html.Div([
        html.Div(tree_cards, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center', 'gap': '20px', 'padding': '20px'}),
        html.Div(id='node-info-modal', style={'display': 'none'})  # Contenedor para el modal
    ])
