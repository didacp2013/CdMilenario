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


def extraer_itmids_hoja(tree_structure):
    """
    Extrae todos los ITMID de los nodos hoja (sin hijos y valor distinto de 0) de una estructura de árbol.
    El id tiene el formato LEVEL-NODO-ITMIN(ITMTYP) y necesitamos extraer solo el ITMID.
    """
    itmids = []
    def recorrer(nodo):
        if isinstance(nodo, list):
            for n in nodo:
                recorrer(n)
            return
        if not nodo.get("children") and nodo.get("value", 0) != 0:
            # Extraer el ITMIN del id (formato: LEVEL-NODO-ITMIN(ITMTYP))
            itmin = str(nodo.get("id", "")).split("-")[2]
            # Extraer solo el ITMID del ITMIN (formato: ITMID(ITMTYP))
            itmid = itmin.split("(")[0].strip()
            itmids.append(itmid)
        for hijo in nodo.get("children", []):
            recorrer(hijo)
    recorrer(tree_structure)
    return itmids

def filtrar_fasg5_por_itmids(fasg5_data, itmids):
    """
    Filtra la lista F_Asg5 dejando solo los registros cuyo ITMID está en la lista de itmids.
    """
    return [row for row in fasg5_data if str(row.get("ITMID")) in itmids]