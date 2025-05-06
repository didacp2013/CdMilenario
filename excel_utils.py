import pandas as pd
import numpy as np
import traceback
import copy
import os

# Definir constantes para rutas de Excel (ajustar según sea necesario)
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "data", "dashboard_data.xlsx")
TREE_SHEET = "F_Asg3"

def extract_tree_data(excel_path, sheet_name):
    """
    Extrae datos de la estructura jerárquica desde una hoja de Excel.
    Columnas esperadas: CIA, PRJID, ROW, COLUMN, LEVEL, NODE, NODEP, ITMIN, VALUE
    """
    try:
        # Leer el Excel directamente con los nombres en mayúsculas
        df = pd.read_excel(excel_path, sheet_name=sheet_name, dtype={
            'CIA': str,
            'PRJID': str,
            'ROW': str,
            'COLUMN': str,
            'ITMIN': str  # Usamos ITMIN directamente
        })
        
        # Eliminar la columna TYPE si existe
        if 'TYPE' in df.columns:
            df = df.drop(columns=['TYPE'])
        
        df['LEVEL'] = df['LEVEL'].astype(int)
        df['NODE'] = df['NODE'].astype(int)
        df['NODEP'] = df['NODEP'].astype(int)
        
        if df['VALUE'].dtype == object:
            df['VALUE'] = df['VALUE'].str.replace(',', '.').astype(float)
            
        return df.to_dict(orient="records")
    except Exception as e:
        return []

def build_tree_structure(items):
    """
    Construye una estructura de árbol a partir de una lista de registros planos.
    Esta función se mantiene para compatibilidad con el código existente.
    
    Args:
        items: Lista de registros con la misma combinación CIA+PRJID+ROW+COLUMN.
        
    Returns:
        La estructura de árbol o None si no hay datos o el valor es 0.
    """
    if not items:
        return None
    
    # Extraer COLUMN del primer elemento (todos deberían tener el mismo COLUMN)
    column = items[0]["COLUMN"]
    
    # Procesar los datos
    result = procesar_datos_arbol(items)
    
    # Verificar que result sea un diccionario antes de usar get()
    if isinstance(result, dict):
        return result.get(column)
    else:
        return None

def to_treemap(node):
    """
    Transforma un nodo de árbol purgado al formato compatible con Plotly treemap.
    """
    return {
        "id": f"{node['LEVEL']}-{node['NODE']}-{node['ITMIN']}",
        "value": node["VALUE"],
        "children": [to_treemap(child) for child in node.get("children", [])] if node.get("children") else []
    }

def procesar_datos_arbol(items):
    """
    Procesa los datos de árbol para una combinación CIA+PRJID+ROW.
    Args:
        items: Lista de registros con la misma combinación CIA+PRJID+ROW.
    Returns:
        Un diccionario donde las claves son los valores de COLUMN y los valores
        son las estructuras de árbol correspondientes en formato treemap.
    """
    for item in items:
        if 'ITMIN' not in item:
            return {}
    items_by_row = {}
    for item in items:
        row_key = (item["CIA"], item["PRJID"], item["ROW"])
        if row_key not in items_by_row:
            items_by_row[row_key] = []
        items_by_row[row_key].append(item)
    if not items_by_row:
        return {}
    result = {}
    for row_key, row_items in items_by_row.items():
        cia, prjid, row = row_key
        nodes_by_id = {}
        root_nodes = []
        for item in row_items:
            node = {
                "NODE": item["NODE"],
                "ITMIN": item["ITMIN"],
                "VALUE": item["VALUE"],
                "LEVEL": item["LEVEL"],
                "COLUMN": item["COLUMN"],
                "children": []
            }
            nodes_by_id[(item["NODE"], item["LEVEL"])] = node
            if item["NODEP"] == 0:
                root_nodes.append(node)
            elif (item["NODEP"], item["LEVEL"]-1) in nodes_by_id:
                nodes_by_id[(item["NODEP"], item["LEVEL"]-1)]["children"].append(node)
        if not root_nodes:
            continue
        leaf_columns = set()
        for node in nodes_by_id.values():
            if not node["children"]:
                leaf_columns.add(node["COLUMN"])
        for column in leaf_columns:
            def purge_tree(node):
                if not node["children"]:
                    if node["COLUMN"] == column and node["VALUE"] != 0:
                        return {
                            "NODE": node["NODE"],
                            "ITMIN": node["ITMIN"],
                            "VALUE": node["VALUE"],
                            "LEVEL": node["LEVEL"],
                            "COLUMN": column,
                            "children": []
                        }
                    return None
                new_children = []
                for child in node["children"]:
                    purged_child = purge_tree(child)
                    if purged_child is not None:
                        new_children.append(purged_child)
                if not new_children:
                    return None
                total_value = sum(child["VALUE"] for child in new_children if child["VALUE"] is not None)
                if total_value == 0:
                    return None
                return {
                    "NODE": node["NODE"],
                    "ITMIN": node["ITMIN"],
                    "VALUE": total_value,
                    "LEVEL": node["LEVEL"],
                    "COLUMN": column,
                    "children": new_children
                }
            purged_roots = []
            for root in root_nodes:
                purged_root = purge_tree(root)
                if purged_root is not None:
                    purged_roots.append(purged_root)
            if purged_roots:
                # Transformar a formato treemap antes de asignar
                treemap = to_treemap(purged_roots[0]) if len(purged_roots) == 1 else [to_treemap(r) for r in purged_roots]
                result[column] = treemap
            else:
                result[column] = None
    return result

def simplify_tree(node, max_depth=2, current_depth=0):
    """
    Simplifica un árbol para visualización, limitando la profundidad.
    """
    if current_depth >= max_depth:
        return {"...": f"(hay {len(node.get('children', []))} hijos más)"}
    
    result = {
        "NODE": node.get("NODE"),
        "ITMIN": node.get("ITMIN"),
        "VALUE": node.get("VALUE"),
        "LEVEL": node.get("LEVEL")
    }
    
    children = node.get("children", [])
    if children:
        if current_depth < max_depth - 1:
            result["children"] = [simplify_tree(child, max_depth, current_depth + 1) for child in children[:3]]
            if len(children) > 3:
                result["children"].append({"...": f"(hay {len(children) - 3} hijos más)"})
        else:
            result["children"] = f"[{len(children)} hijos]"
    
    return result

def count_nodes(node):
    """
    Cuenta el número total de nodos en un árbol.
    """
    count = 1  # Contar el nodo actual
    for child in node.get("children", []):
        count += count_nodes(child)
    return count

def count_by_level(node, levels=None, current_level=0):
    """
    Cuenta el número de nodos por nivel en un árbol.
    """
    if levels is None:
        levels = {}
    
    levels[current_level] = levels.get(current_level, 0) + 1
    
    for child in node.get("children", []):
        count_by_level(child, levels, current_level + 1)
    
    return levels