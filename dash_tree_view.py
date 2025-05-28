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
        return html.Div(
            html.Div([
                html.I(className="fas fa-sitemap", style={'fontSize': '48px', 'color': '#4a6fa5', 'marginBottom': '15px'}),
                html.H4("No hay datos de árbol de costes disponibles", style={'color': '#2c3e50', 'marginBottom': '10px'}),
                html.P("Seleccione otra combinación de filtros o vista.", style={'color': '#6c757d'})
            ], style={'textAlign': 'center', 'padding': '40px'})
        )
    
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
            
            # Extraer ITMTYP (la parte entre paréntesis)
            itmtyp = ""
            if itmfrm_str != "-" and "(" in itmfrm_str and ")" in itmfrm_str:
                start = itmfrm_str.find("(")
                end = itmfrm_str.find(")")
                if start < end:
                    itmtyp = itmfrm_str[start:end+1]
            
            # Procesar ITMFRM para poner una palabra por línea
            if itmfrm_str != "-":
                # Primero, separar por espacios para obtener palabras individuales
                parts = []
                
                # Verificar si hay texto como "GEN:2240044GEN:2240805GEN:2240640"
                if "GEN:" in itmfrm_str:
                    # Separar por "GEN:" y luego procesar cada parte
                    gen_parts = itmfrm_str.replace("GEN:", "\nGEN:").split("\n")
                    for part in gen_parts:
                        if part.strip():
                            if part.startswith("GEN:"):
                                parts.append(part)
                            else:
                                # Para otras partes, dividir por espacios
                                parts.extend(part.split())
                else:
                    # Dividir por espacios normalmente
                    parts = itmfrm_str.split()
                
                # Eliminar cualquier parte entre paréntesis (ITMTYP)
                filtered_words = []
                for word in parts:
                    if not (word.startswith("(") or ")" in word):
                        filtered_words.append(word)
                
                # Unir las palabras filtradas con saltos de línea HTML
                if filtered_words:
                    # Usar salto de línea HTML explícito
                    formatted_itmfrm = "<br>".join(filtered_words)
                    # Etiqueta sin LEVEL-NODE, solo ITMFRM con una palabra por línea
                    label = formatted_itmfrm
                else:
                    label = ""
            else:
                label = ""
            
            # Información para el tooltip (sin línea en blanco)
            if itmtyp:
                hover_info = f"{node_id}<br>{itmtyp}<br>{value_str}"
            else:
                hover_info = f"{node_id}<br>{value_str}"
            
            nodes.append({
                "id": node_id,
                "parent": parent_id,
                "value": value,
                "label": label,
                "hover_info": hover_info,
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
            hover_infos = [n["hover_info"] for n in flat_nodes]
            itmfrms = [n["itmfrm"] for n in flat_nodes]
            
            # Asignar colores más claros para mejorar la visibilidad del texto
            colors = []
            for i, (node_id, itmfrm) in enumerate(zip(ids, itmfrms)):
                parent = parents[i]
                # Nodo raíz (sin padre) - color más claro
                if parent == "":
                    colors.append('#5a8bc9')  # Azul claro para el nodo raíz
                # Nodos intermedios - color medio
                elif itmfrm == "-":
                    colors.append('#4a6fa5')  # Azul medio para nodos intermedios
                # Nodos hoja - color más oscuro
                else:
                    colors.append('#3a5d7c')  # Azul oscuro para nodos hoja
            
            fig = go.Figure(go.Treemap(
                ids=ids,
                parents=parents,
                values=values,
                labels=labels,
                branchvalues="total",
                textinfo="label",
                textposition="top left",  # Posicionar texto arriba a la izquierda
                insidetextfont=dict(
                    size=11,  # Texto ligeramente más grande
                    family="Arial, sans-serif",
                    color="white",
                    weight="bold"  # Texto en negrita para mejor visibilidad
                ),
                marker=dict(
                    colors=colors,
                    line=dict(width=1, color='#ffffff')
                ),
                hovertemplate="%{customdata}<extra></extra>",
                customdata=hover_infos  # Usar la información personalizada para el tooltip
            ))
            
            fig.update_layout(
                margin=dict(t=40, l=0, r=0, b=0),
                height=600,
                uniformtext=dict(
                    minsize=9,
                    mode='show'
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                hoverlabel=dict(
                    bgcolor="#dc3545",  # Fondo rojo
                    font_size=12,
                    font_family="Arial, sans-serif",
                    font_color="white",  # Texto blanco
                    bordercolor="#b02a37"  # Borde rojo oscuro
                )
            )
            
            card = html.Div([
                html.Div([
                    html.H5(title, style={
                        'margin': '0',
                        'color': '#fff',
                        'fontWeight': '600',
                        'letterSpacing': '0.5px',
                        'textShadow': '0 2px 4px rgba(44,62,80,0.12)'
                    })
                ], style={
                    'padding': '12px 15px',
                    'borderRadius': '8px 8px 0 0',
                    'background': 'linear-gradient(135deg, #4a6fa5 0%, #2c3e50 100%)',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1) inset',
                    'borderBottom': '1px solid #dee2e6'
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
                'borderRadius': '8px',
                'backgroundColor': '#ffffff',
                'boxShadow': '0 6px 16px rgba(44,62,80,0.12)',
                'width': '900px',
                'display': 'inline-block',
                'verticalAlign': 'top',
                'transition': 'all 0.3s ease'
            })
            tree_cards.append(card)
        except Exception as e:
            continue

    return html.Div(
        tree_cards,
        style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center', 'gap': '20px', 'padding': '20px', 'marginTop': '10px'}
    )
