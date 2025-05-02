#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extractor de datos desde Excel para el dashboard
"""
import os
import sys
import pandas as pd
import datetime
from excel_utils import extract_tree_data, procesar_datos_arbol, build_tree_structure

# Valores hardcodeados del Excel y sus hojas
EXCEL_PATH = "/Users/didac/Downloads/StoryMac/DashBTracker/PruebasCdM/Tchart_V06.xlsm"
HISTORIC_SHEET = "FrmBB_2"
KPI_SHEET = "FrmBB_3"
TREE_SHEET = "F_Asg3"  # Corregido: F_Asg3 en lugar de FrmBB_4

def wks_to_date(wks):
    """
    Convierte un valor WKS (YYYY.WW) en una fecha real (domingo de la semana ISO).
    Devuelve también el número de serie Excel (días desde 1899-12-30).
    """
    import datetime
    try:
        wks_str = str(wks).replace(',', '').replace(' ', '').strip()
        if '.' in wks_str:
            year, week = wks_str.split('.', 1)
            year = int(year)
            week = int(week)
            date = datetime.date.fromisocalendar(year, week, 7)  # 7 = domingo
        elif wks_str.isdigit() and len(wks_str) == 4:
            year = int(wks_str)
            date = datetime.date.fromisocalendar(year, 1, 7)
        else:
            return None, None
        # Número de serie Excel: días desde 1899-12-30
        excel_base = datetime.date(1899, 12, 30)
        excel_serial = (date - excel_base).days
        return date, excel_serial
    except Exception:
        return None, None

def extract_historic_data(excel_path, sheet_name):
    """
    Extrae datos históricos desde una hoja de Excel.
    """
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name, dtype={'WKS': str})
        # Añadir columna WKS_DATE y WKS_SERIAL
        wks_dates_and_serials = df['WKS'].apply(wks_to_date)
        df['WKS_DATE'] = wks_dates_and_serials.apply(lambda x: x[0])
        df['WKS_SERIAL'] = wks_dates_and_serials.apply(lambda x: x[1])
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"Error al extraer datos históricos: {e}")
        return []

def extract_kpi_data(excel_path, sheet_name):
    """
    Extrae datos KPI desde una hoja de Excel.
    """
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"Error al extraer datos KPI: {e}")
        return []

# Eliminada la función extract_tree_data duplicada, ahora se importa de excel_utils

def structure_data(historic_data, kpi_data, tree_data):
    """
    Estructura los datos en la jerarquía correcta, usando DATATYPE como clave y DATACONTENTS como valor.
    """
    structured_data = {}

    # Procesar datos históricos (H)
    for record in historic_data:
        cia = record.get("CIA")
        prjid = record.get("PRJID")
        row = record.get("ROW")
        column = record.get("COLUMN")

        if cia not in structured_data:
            structured_data[cia] = {}
        if prjid not in structured_data[cia]:
            structured_data[cia][prjid] = {}
        if row not in structured_data[cia][prjid]:
            structured_data[cia][prjid][row] = {}
        if column not in structured_data[cia][prjid][row]:
            structured_data[cia][prjid][row][column] = {}

        if "H" not in structured_data[cia][prjid][row][column]:
            structured_data[cia][prjid][row][column]["H"] = []

        structured_data[cia][prjid][row][column]["H"].append({
            "HPREV": record.get("HPREV"),
            "PPTO": record.get("PPTO"),
            "REAL": record.get("REAL")
        })

    # Procesar datos KPI (K)
    for record in kpi_data:
        cia = record.get("CIA")
        prjid = record.get("PRJID")
        row = record.get("ROW")
        column = record.get("COLUMN")

        if cia not in structured_data:
            structured_data[cia] = {}
        if prjid not in structured_data[cia]:
            structured_data[cia][prjid] = {}
        if row not in structured_data[cia][prjid]:
            structured_data[cia][prjid][row] = {}
        if column not in structured_data[cia][prjid][row]:
            structured_data[cia][prjid][row][column] = {}

        structured_data[cia][prjid][row][column]["K"] = {
            "KPREV": record.get("KPREV"),
            "PDTE": record.get("PDTE"),
            "REALPREV": record.get("REALPREV"),
            "PPTOPREV": record.get("PPTOPREV")
        }

    # Procesar datos tipo T (árbol), solo si se proporciona y no está vacío
    if tree_data:
        tree_by_row = {}
        for record in tree_data:
            row_key = (record.get("CIA"), record.get("PRJID"), record.get("ROW"))
            if row_key not in tree_by_row:
                tree_by_row[row_key] = []
            tree_by_row[row_key].append(record)

        for row_key, items in tree_by_row.items():
            cia, prjid, row = row_key
            column_structures = procesar_datos_arbol(items)
            for column, tree_structure in column_structures.items():
                if tree_structure is not None:
                    if cia not in structured_data:
                        structured_data[cia] = {}
                    if prjid not in structured_data[cia]:
                        structured_data[cia][prjid] = {}
                    if row not in structured_data[cia][prjid]:
                        structured_data[cia][prjid][row] = {}
                    if column not in structured_data[cia][prjid][row]:
                        structured_data[cia][prjid][row][column] = {}
                    structured_data[cia][prjid][row][column]["T"] = tree_structure

    return structured_data

def main():
    """
    Extrae y procesa los datos desde el Excel hardcodeado.
    Devuelve una lista de dicts, cada uno con la estructura:
    {
        'CIA': str,
        'PRJID': str,
        'ROW': str,
        'COLUMN': str,
        'DATATYPE': 'K' o 'H' o 'T',
        'DATACONTENTS': dict (KPI) o lista de dicts (HISTÓRICO) o dict (ÁRBOL)
    }
    """
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: No se encuentra el archivo Excel en la ruta: {EXCEL_PATH}")
        return []

    historic_data = extract_historic_data(EXCEL_PATH, HISTORIC_SHEET)
    kpi_data = extract_kpi_data(EXCEL_PATH, KPI_SHEET)
    tree_data = extract_tree_data(EXCEL_PATH, TREE_SHEET)

    print(f"Registros extraídos de {HISTORIC_SHEET}: {len(historic_data)}")
    print(f"Registros extraídos de {KPI_SHEET}: {len(kpi_data)}")
    print(f"Registros extraídos de {TREE_SHEET}: {len(tree_data)}")

    # Usar la estructura unificada
    structured_data = structure_data(historic_data, kpi_data, tree_data)

    result = []
    for cia, cia_data in structured_data.items():
        for prjid, prjid_data in cia_data.items():
            for row, row_data in prjid_data.items():
                for column, col_data in row_data.items():
                    # KPI
                    if "K" in col_data and col_data["K"]:
                        result.append({
                            "CIA": cia,
                            "PRJID": prjid,
                            "ROW": row,
                            "COLUMN": column,
                            "DATATYPE": "K",
                            "DATACONTENTS": col_data["K"]
                        })
                    # HISTÓRICOS
                    if "H" in col_data and col_data["H"]:
                        result.append({
                            "CIA": cia,
                            "PRJID": prjid,
                            "ROW": row,
                            "COLUMN": column,
                            "DATATYPE": "H",
                            "DATACONTENTS": col_data["H"]
                        })
                    # ÁRBOL
                    if "T" in col_data and col_data["T"]:
                        result.append({
                            "CIA": cia,
                            "PRJID": prjid,
                            "ROW": row,
                            "COLUMN": column,
                            "DATATYPE": "T",
                            "DATACONTENTS": col_data["T"]
                        })

    print(f"Registros KPI procesados: {sum(1 for r in result if r['DATATYPE']=='K')}")
    print(f"Registros Históricos procesados: {sum(1 for r in result if r['DATATYPE']=='H')}")
    print(f"Registros Árbol procesados: {sum(1 for r in result if r['DATATYPE']=='T')}")

    return result

# Funciones auxiliares para depuración y análisis
def simplify_tree(node, max_depth=2, current_depth=0):
    """
    Simplifica un árbol para visualización, limitando la profundidad.
    """
    if current_depth >= max_depth:
        return {"...": f"(hay {len(node.get('children', []))} hijos más)"}
    
    result = {
        "NODE": node.get("NODE"),
        "ITMID": node.get("ITMID"),
        "VALUE": node.get("VALUE"),
        "TYPE": node.get("TYPE"),
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

if __name__ == "__main__":
    main()