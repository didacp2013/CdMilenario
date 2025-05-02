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
    Columnas esperadas: CIA, PRJID, ROW, COLUMN, LEVEL, NODE, NODEP, ITMID, TYPE, VALUE
    """
    try:
        # Leer el Excel directamente con los nombres en mayúsculas
        df = pd.read_excel(excel_path, sheet_name=sheet_name, dtype={
            'CIA': str,
            'PRJID': str,
            'ROW': str,
            'COLUMN': str
        })
        
        # Imprimir columnas para diagnóstico
        print(f"Columnas en el Excel: {df.columns.tolist()}")
        
        # Asegurar que los tipos de datos son correctos para las columnas numéricas
        df['LEVEL'] = df['LEVEL'].astype(int)
        df['NODE'] = df['NODE'].astype(int)
        df['NODEP'] = df['NODEP'].astype(int)
        
        # Convertir VALUE a numérico si es necesario
        if df['VALUE'].dtype == object:
            df['VALUE'] = df['VALUE'].str.replace(',', '.').astype(float)
            
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"Error al extraer datos de árbol: {e}")
        traceback.print_exc()
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

def procesar_datos_arbol(items):
    """
    Procesa los datos de árbol para una combinación CIA+PRJID+ROW.
    
    Args:
        items: Lista de registros con la misma combinación CIA+PRJID+ROW.
        
    Returns:
        Un diccionario donde las claves son los valores de COLUMN y los valores
        son las estructuras de árbol correspondientes. Si una estructura tiene
        valor 0 después de la agregación, se establece como None.
    """
    # Paso 1: Agrupar por CIA+PRJID+ROW (ignorar COLUMN)
    items_by_row = {}
    for item in items:
        row_key = (item["CIA"], item["PRJID"], item["ROW"])
        if row_key not in items_by_row:
            items_by_row[row_key] = []
        items_by_row[row_key].append(item)
    
    # Si no hay datos, retornar un diccionario vacío
    if not items_by_row:
        return {}
    
    # Tomar el primer grupo (solo debería haber uno ya que filtramos por CIA+PRJID+ROW)
    row_items = list(items_by_row.values())[0]
    
    # Paso 2: Construir el árbol básico
    nodes_by_id = {}
    root_nodes = []
    
    for item in row_items:
        node = {
            "NODE": item["NODE"],
            "ITMID": item["ITMID"],
            "VALUE": item["VALUE"],
            "TYPE": item["TYPE"],
            "LEVEL": item["LEVEL"],
            "COLUMN": item["COLUMN"],  # Mantener COLUMN para identificación
            "children": []
        }
        nodes_by_id[item["NODE"]] = node
        
        if item["NODEP"] == 0:
            root_nodes.append(node)
        elif item["NODEP"] in nodes_by_id:
            nodes_by_id[item["NODEP"]]["children"].append(node)
    
    # Si no hay nodos raíz, retornar un diccionario vacío
    if not root_nodes:
        return {}
    
    # Paso 3: Identificar nodos hoja con VALUE≠0 y sus valores COLUMN
    valid_columns = set()
    
    def identify_valid_columns(node):
        if not node["children"]:
            # Es un nodo hoja
            if node["VALUE"] != 0:
                valid_columns.add(node["COLUMN"])
            return node["VALUE"] != 0
        
        # Para nodos con hijos, verificar recursivamente
        has_valid_child = False
        for child in node["children"]:
            if identify_valid_columns(child):
                has_valid_child = True
        
        return has_valid_child
    
    # Identificar columnas válidas
    for root in root_nodes:
        identify_valid_columns(root)
    
    # Paso 4: Calcular valores agregados y asignar COLUMN
    result = {}
    
    for column in valid_columns:
        # Crear una copia de la estructura para cada COLUMN válida
        column_structure = None
        
        def process_structure(node, parent=None):
            # Crear una copia del nodo
            new_node = {
                "NODE": node["NODE"],
                "ITMID": node["ITMID"],
                "VALUE": 0,  # Inicializar en 0, se recalculará
                "TYPE": node["TYPE"],
                "LEVEL": node["LEVEL"],
                "children": []
            }
            
            if parent is not None:
                parent["children"].append(new_node)
            
            # Procesar hijos
            for child in node["children"]:
                process_structure(child, new_node)
            
            # Calcular valor
            if not new_node["children"]:
                # Es un nodo hoja
                if node["COLUMN"] == column and node["VALUE"] != 0:
                    new_node["VALUE"] = node["VALUE"]
            else:
                # Es un nodo con hijos, calcular suma
                new_node["VALUE"] = sum(child["VALUE"] for child in new_node["children"])
            
            return new_node
        
        # Procesar cada raíz
        for root in root_nodes:
            root_copy = process_structure(root)
            
            # Solo incluir si el valor es diferente de 0
            if root_copy["VALUE"] != 0:
                column_structure = root_copy
                break
        
        # Solo incluir la estructura si tiene valor
        if column_structure and column_structure.get("VALUE", 0) != 0:
            result[column] = column_structure
        else:
            result[column] = None
    
    return result