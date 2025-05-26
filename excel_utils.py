import pandas as pd
import numpy as np
import unicodedata
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
    except Exception:
        return []

def to_treemap(node):
    """
    Transforma un nodo de árbol purgado al formato compatible con Plotly treemap.
    """
    result = {
        'name': node['description'],
        'id': node['id'],
        'value': node['value']
    }
    if node.get('parent'):
        result['parent'] = node['parent']
    if node.get('children'):
        result['children'] = [to_treemap(child) for child in node['children']]
    return result

def normaliza(s):
    """
    Normaliza un string eliminando espacios y convirtiéndolo a mayúsculas
    """
    if not isinstance(s, str):
        return str(s).strip().upper()
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn').strip().upper()

def buscar_itmid_completo(fasg5_data, itmin_base):
    """
    Busca el ITMID completo en la tabla F_Asg5 que corresponde al ITMIN.
    """
    if not fasg5_data:
        return None
    itmin_base = normaliza(itmin_base)
    for record in fasg5_data:
        if normaliza(record['ITMID']).startswith(itmin_base):
            return record['ITMID']
    return None

def limpiar_campo_texto(valor, campo=""):
    """
    Limpia un campo de texto
    """
    if pd.isna(valor) or valor is None:
        return ""
    return str(valor).strip()

def extraer_itmid(id_str):
    """
    Extrae el ITMID de una cadena que puede contener información adicional
    """
    if not id_str:
        return ""
    
    partes = id_str.split('-')
    if len(partes) < 3:
        return id_str.strip()
    
    # Tomar la tercera parte (índice 2)
    resto = partes[2]
    
    # Manejar casos con paréntesis
    if ' (' in resto:
        itmid = resto.split(' (')[0]
    else:
        itmid = resto.split('(')[0]
    
    return itmid.strip()

def build_itmfrm_lookup(fasg5_data):
    """
    Construye un diccionario de búsqueda para ITMFRM basado en CIA+PRJID+ITMID
    """
    if not fasg5_data:
        return {}
    
    lookup = {}
    for record in fasg5_data:
        cia = normaliza(record['CIA'])
        prjid = normaliza(record['PRJID'])
        itmid = normaliza(record['ITMID'])
        itmfrm = record['ITMFRM']
        
        key = (cia, prjid, itmid)
        lookup[key] = itmfrm
    
    return lookup

def procesar_datos_arbol(items, itmfrm_lookup=None, fasg5_data=None):
    """
    Procesa los datos del árbol y devuelve una estructura jerárquica
    """
    result = {}
    # Agrupar por columna
    column_groups = {}
    for item in items:
        column = limpiar_campo_texto(item.get("COLUMN", ""))
        if column not in column_groups:
            column_groups[column] = []
        column_groups[column].append(item)
    
    # Procesar cada columna por separado
    for column, column_items in column_groups.items():
        # FASE 1: Construcción del árbol
        tree = None
        node_map = {}  # NODE -> nodo
        
        # Crear todos los nodos con su estructura básica
        for item in column_items:
            # Limpiar campos clave para la estructura
            cia = limpiar_campo_texto(item.get("CIA", ""))
            prjid = limpiar_campo_texto(item.get("PRJID", ""))
            itmin = limpiar_campo_texto(item.get("ITMIN", ""))
            
            # El id incluye ITMID y potencialmente ITMTYP
            full_id = f"{item['LEVEL']}-{item['NODE']}-{itmin}"
            node = {
                "id": full_id,
                "value": item["VALUE"],
                "children": [],
                "CIA": cia,
                "PRJID": prjid
            }
            node_map[item["NODE"]] = node
            
            # Si es el nodo raíz, establecerlo como árbol
            if item["LEVEL"] == 1:
                tree = node
        
        # Conectar los nodos según NODEP
        for item in column_items:
            node = node_map[item["NODE"]]
            if item["LEVEL"] > 1:  # No es la raíz
                parent = node_map[item["NODEP"]]
                parent["children"].append(node)
        
        # FASE 2: Enriquecimiento con ITMFRM
        if tree and (itmfrm_lookup or fasg5_data):
            # Recorrer el árbol y añadir ITMFRM a los nodos hoja
            def enrich_node(node):
                if not node["children"]:  # Es un nodo hoja
                    # Extraer ITMID del id completo
                    itmid = extraer_itmid(node["id"])
                    
                    # Para la búsqueda en F_Asg5 solo usamos CIA+PRJID+ITMID
                    cia = limpiar_campo_texto(node["CIA"])
                    prjid = limpiar_campo_texto(node["PRJID"])
                    itmid = limpiar_campo_texto(itmid)
                    
                    # La clave de búsqueda solo usa CIA+PRJID+ITMID
                    key = (normaliza(cia), normaliza(prjid), normaliza(itmid))
                    itmfrm = itmfrm_lookup.get(key, "")
                    if itmfrm:
                        node["itmfrm"] = itmfrm
                else:
                    for child in node["children"]:
                        enrich_node(child)
            
            enrich_node(tree)

        result[column] = tree if tree else None
    
    return result

def extraer_itmids_hoja(tree_structure):
    """
    Extrae los ITMIDs de los nodos hoja de un árbol
    """
    itmids = []
    
    def process_node(node):
        if not node.get('children'):  # Es un nodo hoja
            itmid = extraer_itmid(node.get('id', ''))
            if itmid:
                itmids.append(itmid)
        else:
            for child in node.get('children', []):
                process_node(child)
    
    process_node(tree_structure)
    return itmids