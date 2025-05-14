#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extractor de datos desde Excel para el dashboard
"""
import os
import sys
import pandas as pd
import datetime
from excel_utils import extract_tree_data, procesar_datos_arbol
from excel_utils import extraer_itmids_hoja, filtrar_fasg5_por_itmids

# Valores hardcodeados del Excel y sus hojas
EXCEL_PATH = "/Users/didac/Downloads/StoryMac/DashBTracker/PruebasCdM/DataKHT_V06.xlsm"
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
            year = int(year)  # CORREGIDO: Usar year en lugar de wks_str
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
        df = pd.read_excel(excel_path, sheet_name=sheet_name, dtype={'WKS': str, 'PRJID': str})
        # Añadir columna WKS_DATE y WKS_SERIAL
        wks_dates_and_serials = df['WKS'].apply(wks_to_date)
        df['WKS_DATE'] = wks_dates_and_serials.apply(lambda x: x[0])
        df['WKS_SERIAL'] = wks_dates_and_serials.apply(lambda x: x[1])
        return df.to_dict(orient="records")
    except Exception as e:
        return []

def extract_kpi_data(excel_path, sheet_name):
    """
    Extrae datos KPI desde una hoja de Excel.
    """
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name, dtype={'PRJID': str})
        return df.to_dict(orient="records")
    except Exception as e:
        return []

# Eliminada la función extract_tree_data duplicada, ahora se importa de excel_utils

def structure_data(historic_data, kpi_data, tree_data):
    """
    Estructura los datos en la jerarquía correcta, usando DATATYPE como clave y DATACONTENTS como valor.
    Si todos los valores de un registro KPI o histórico son 0, se establece DATACONTENTS como None.
    """
    structured_data = {}

    # Procesar datos históricos (H)
    for record in historic_data:
        cia = record.get("CIA")
        prjid = str(record.get("PRJID"))  # Asegurar string
        row = str(record.get("ROW", "")).strip()  # Asegurar string y eliminar espacios
        column = str(record.get("COLUMN", "")).strip()  # Asegurar string y eliminar espacios

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

        # Verificar si todos los valores históricos son 0
        all_zeros = True
        for key in ["HPREV", "PPTO", "REAL"]:
            if record.get(key, 0) != 0:
                all_zeros = False
                break

        if all_zeros:
            structured_data[cia][prjid][row][column]["H"].append(None)
        else:
            structured_data[cia][prjid][row][column]["H"].append({
                "HPREV": record.get("HPREV"),
                "PPTO": record.get("PPTO"),
                "REAL": record.get("REAL"),
                "WKS_DATE": record.get("WKS_DATE"),
                "WKS_SERIAL": record.get("WKS_SERIAL")
            })

    # Procesar datos KPI (K)
    for record in kpi_data:
        cia = record.get("CIA")
        prjid = str(record.get("PRJID"))  # Asegurar string
        row = str(record.get("ROW", "")).strip()  # Asegurar string y eliminar espacios
        column = str(record.get("COLUMN", "")).strip()  # Asegurar string y eliminar espacios

        if cia not in structured_data:
            structured_data[cia] = {}
        if prjid not in structured_data[cia]:
            structured_data[cia][prjid] = {}
        if row not in structured_data[cia][prjid]:
            structured_data[cia][prjid][row] = {}
        if column not in structured_data[cia][prjid][row]:
            structured_data[cia][prjid][row][column] = {}

        # Verificar si todos los valores KPI son 0
        all_zeros = True
        for key in ["KPREV", "PDTE", "REALPREV", "PPTOPREV"]:
            if record.get(key, 0) != 0:
                all_zeros = False
                break

        if all_zeros:
            structured_data[cia][prjid][row][column]["K"] = None
        else:
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
            row = str(record.get("ROW", "")).strip()  # Asegurar string y eliminar espacios
            column = str(record.get("COLUMN", "")).strip()  # Asegurar string y eliminar espacios

            row_key = (record.get("CIA"), record.get("PRJID"), row)
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

    # Limpieza final: eliminar elementos None en listas de históricos (H)
    for cia in structured_data:
        for prjid in structured_data[cia]:
            for row in structured_data[cia][prjid]:
                for column in structured_data[cia][prjid][row]:
                    cell = structured_data[cia][prjid][row][column]
                    if "H" in cell and isinstance(cell["H"], list):
                        cell["H"] = [h for h in cell["H"] if h is not None]
                        if not cell["H"]:
                            cell["H"] = None

    # --- NUEVO: Correspondencia 1:1 en las claves para K, H, T ---
    # Construir el conjunto de todas las claves posibles
    all_keys = set()
    # De históricos
    for record in historic_data:
        all_keys.add((str(record.get("CIA")), str(record.get("PRJID")), str(record.get("ROW")), str(record.get("COLUMN"))))
    # De KPIs
    for record in kpi_data:
        all_keys.add((str(record.get("CIA")), str(record.get("PRJID")), str(record.get("ROW")), str(record.get("COLUMN"))))
    # De árbol
    for record in tree_data:
        all_keys.add((str(record.get("CIA")), str(record.get("PRJID")), str(record.get("ROW")), str(record.get("COLUMN"))))

    # Para cada clave y cada tipo, asegurar que hay un registro (aunque sea None)
    for cia, prjid, row, column in all_keys:
        if cia not in structured_data:
            structured_data[cia] = {}
        if prjid not in structured_data[cia]:
            structured_data[cia][prjid] = {}
        if row not in structured_data[cia][prjid]:
            structured_data[cia][prjid][row] = {}
        if column not in structured_data[cia][prjid][row]:
            structured_data[cia][prjid][row][column] = {}
        cell = structured_data[cia][prjid][row][column]
        if "K" not in cell:
            cell["K"] = None
        if "H" not in cell:
            cell["H"] = None
        if "T" not in cell:
            cell["T"] = None
    # --- FIN NUEVO ---
    return structured_data

def compare_kpi_tree_data(kpi_data, tree_data, historic_data):
    """
    Compara los datos KPI con los datos de árbol y muestra estadísticas.
    """
    # Crear conjuntos de claves únicas para KPI y árbol
    kpi_keys = set()
    tree_keys = set()
    
    # Procesar datos KPI
    for record in kpi_data:
        key = (record["CIA"], record["PRJID"], record["ROW"], record["COLUMN"])
        kpi_keys.add(key)
    
    # Procesar datos de árbol
    for record in tree_data:
        key = (record["CIA"], record["PRJID"], record["ROW"], record["COLUMN"])
        tree_keys.add(key)
    
    # Encontrar diferencias
    kpi_without_tree = kpi_keys - tree_keys
    tree_without_kpi = tree_keys - kpi_keys
    
    # Contar KPIs con valor 0 que no tienen árbol
    kpi_zero_without_tree = 0
    for record in kpi_data:
        key = (record["CIA"], record["PRJID"], record["ROW"], record["COLUMN"])
        if key in kpi_without_tree and record.get("REALPREV", 0) == 0:
            kpi_zero_without_tree += 1

def comparar_resultados_finales(result):
    kpi_keys = set()
    tree_keys = set()

    for r in result:
        key = (r["CIA"], r["PRJID"], r["ROW"], r["COLUMN"])
        if r["DATATYPE"] == "K":
            kpi_keys.add(key)
        elif r["DATATYPE"] == "T":
            tree_keys.add(key)

    comunes = kpi_keys & tree_keys
    solo_kpi = kpi_keys - tree_keys
    solo_tree = tree_keys - kpi_keys

def extract_itm_data(excel_path, sheet_name="F_Asg5"):
    """
    Extrae datos de la tabla F_Asg5 (datos de items).
    """
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name, dtype={
            'CIA': str,
            'PRJID': str,
            'itm_id': str  # Aseguramos que itm_id sea string para comparaciones consistentes
        })
        
        # Convertir a lista de diccionarios
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"Error al extraer datos de {sheet_name}: {e}")
        return []

def main():
    """
    Función principal que extrae y procesa los datos del Excel
    """
    # Extraer datos
    historic_data = extract_historic_data(EXCEL_PATH, HISTORIC_SHEET)
    kpi_data = extract_kpi_data(EXCEL_PATH, KPI_SHEET)
    tree_data = extract_tree_data(EXCEL_PATH, TREE_SHEET)
    
    # Estructurar datos
    structured_data = structure_data(historic_data, kpi_data, tree_data)
    
    # Convertir a lista plana
    result = []
    for cia, cia_data in structured_data.items():
        for prjid, prjid_data in cia_data.items():
            for row, row_data in prjid_data.items():
                for column, col_data in row_data.items():
                    # Verificar KPI
                    if "K" in col_data and col_data["K"] is not None:
                        result.append({
                            "CIA": cia,
                            "PRJID": prjid,
                            "ROW": row,
                            "COLUMN": column,
                            "DATATYPE": "K",
                            "DATACONTENTS": col_data["K"]
                        })
                    # Verificar Histórico
                    if "H" in col_data and col_data["H"] is not None:
                        result.append({
                            "CIA": cia,
                            "PRJID": prjid,
                            "ROW": row,
                            "COLUMN": column,
                            "DATATYPE": "H",
                            "DATACONTENTS": col_data["H"]
                        })
                    # Verificar Árbol
                    if "T" in col_data and col_data["T"] is not None:
                        # El árbol ya está en formato treemap
                        result.append({
                            "CIA": cia,
                            "PRJID": prjid,
                            "ROW": row,
                            "COLUMN": column,
                            "DATATYPE": "T",
                            "DATACONTENTS": col_data["T"]
                        })
    # Ordenar el resultado final por las mismas claves y DATATYPE
    result.sort(key=lambda r: (str(r["CIA"]), str(r["PRJID"]), str(r["ROW"]), str(r["COLUMN"]), r["DATATYPE"]))
    comparar_resultados_finales(result)
    
    # Procesar datos para F_Asg5 (ahora llamada itm_data)
    fasg5_filtrados_por_cia_prjid = {}
    
    # Extraer datos de F_Asg5
    itm_data = extract_itm_data(EXCEL_PATH)
    
    # Crear un diccionario para almacenar las estructuras de árbol por CIA+PRJID
    arbol_cia_prjid = {}
    
    # Agrupar los datos de árbol por CIA+PRJID
    for item in result:
        if item["DATATYPE"] == "T":
            key = (item["CIA"], item["PRJID"])
            if key not in arbol_cia_prjid:
                arbol_cia_prjid[key] = item["DATACONTENTS"]
    
    # Para cada combinación CIA+PRJID, filtrar los datos de F_Asg5
    for key, tree in arbol_cia_prjid.items():
        cia, prjid = key
        # Extraer los IDs de los nodos hoja del árbol
        itmids_hoja = extraer_itmids_hoja(tree)
        # Filtrar los datos de F_Asg5 por los IDs de los nodos hoja
        filtrados = [
            item for item in itm_data 
            if str(item.get("CIA", "")) == str(cia) and 
               str(item.get("PRJID", "")) == str(prjid) and 
               str(item.get("itm_id", "")) in itmids_hoja
        ]
        fasg5_filtrados_por_cia_prjid[key] = filtrados
    
    # Devolver ambos valores: los datos del dashboard y los datos filtrados de F_Asg5
    return result, fasg5_filtrados_por_cia_prjid

    # Supón que tienes:
    # - arbol_cia_prjid: estructura de árbol por cada combinación CIA+PRJID (de F_Asg3)
    # - fasg5_data: lista de diccionarios de F_Asg5
    
    # Ejemplo de integración:
    fasg5_filtrados_por_cia_prjid = {}
    for key, tree in arbol_cia_prjid.items():
        itmids_hoja = extraer_itmids_hoja(tree)
        fasg5_filtrados = filtrar_fasg5_por_itmids(fasg5_data, itmids_hoja)
        fasg5_filtrados_por_cia_prjid[key] = fasg5_filtrados
    
    # Al final de la función, asegúrate de devolver dos valores:
    # 1. Los datos del dashboard (como ya lo hace)
    # 2. Los datos filtrados de F_Asg5
    
    # Si ya tienes los datos filtrados de F_Asg5:
    return datos_dashboard, fasg5_filtrados_por_cia_prjid
    
    # Si no tienes los datos filtrados, devuelve un diccionario vacío como segundo valor:
    # return datos_dashboard, {}

if __name__ == "__main__":
    main()