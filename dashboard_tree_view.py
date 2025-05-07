"""
Dashboard Tree View (Árbol de Costes)
-------------------------------------
Visualización específica para los datos de tipo árbol de costes (DATATYPE="T").
"""

import plotly.graph_objects as go
from dash import html, dcc
import json
import pandas as pd

def create_tree_view(data):
    """
    Crea la vista de árbol de costes para datos tipo T
    """
    tree_data = [row for row in data if row.get("DATATYPE") == "T"]
    
    if not tree_data:
        return html.Div("No hay datos de árbol de costes disponibles", style={'text-align': 'center', 'margin-top': '20px'})
    
    # Procesamos los datos para convertirlos en estructura de árbol
    tree_cards = []
    for row in tree_data:
        if not row.get("DATACONTENTS"):
            continue
        
        # Ya no necesitamos construir la estructura jerárquica aquí
        # Los datos ya deben venir estructurados desde excel_data_extractor
        tree_structure = row.get("DATACONTENTS", {})
        
        # Obtener título para la tarjeta
        def clean_label(label):
            if label and ":" in label:
                return label.split(":", 1)[1].strip()
            return label or ""
        
        title = f"{clean_label(row.get('ROW', ''))} - {clean_label(row.get('COLUMN', ''))}"
        
        # Crear figura de treemap
        fig = create_treemap_figure(tree_structure, title="")
        
        # Crear tarjeta con el treemap
        card = html.Div([
            html.H5(title, style={'margin': '0', 'color': '#fff', 'fontWeight': '600', 'padding': '12px 15px', 'borderRadius': '5px 5px 0 0', 'background': 'linear-gradient(135deg, #4a6fa5 0%, #2c3e50 100%)'}),
            dcc.Graph(figure=fig, config={'displayModeBar': False})
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
    
    if not tree_cards:
        return html.Div("No hay datos de árbol de costes disponibles", style={'text-align': 'center', 'margin-top': '20px'})
    
    return html.Div(tree_cards, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center', 'gap': '20px', 'padding': '20px'})

def create_treemap_figure(tree_structure, title=""):
    """
    Crea una figura de treemap usando Plotly
    """
    labels = []
    parents = []
    values = []
    hover_texts = []

    def process_node(node, parent=""):
        # Usar 'id' como etiqueta
        item_id = node.get('id', '')
        display_label = str(item_id)
        labels.append(display_label)
        parents.append(parent)
        values.append(node.get('value', 0))
        hover_text = f"ID: {item_id}<br>Valor: {node.get('value', 0):,.2f} €"
        hover_texts.append(hover_text)
        for child in node.get('children', []):
            process_node(child, display_label)

    # Procesar el árbol recursivamente
    process_node(tree_structure)

    # Crear la figura de treemap
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        hovertext=hover_texts,
        hoverinfo="text",
        textinfo="label+value",
        marker=dict(
            colorscale='Blues',
            cmid=0
        ),
        pathbar=dict(
            visible=True
        )
    ))

    # Configurar el layout
    fig.update_layout(
        title=title,
        margin=dict(t=50, l=25, r=25, b=25),
        height=600,
        font=dict(
            family="Arial, sans-serif",
            size=12
        )
    )
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
