#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extractor de datos desde Excel para el dashboard
"""
import os
import sys
import pandas as pd
import datetime
from excel_utils import extract_tree_data, procesar_datos_arbol, build_tree_structure, simplify_tree

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
    
    print("\n=== Estadísticas de comparación KPI vs Árbol ===")
    print(f"Total registros KPI: {len(kpi_keys)}")
    print(f"Total registros Árbol: {len(tree_keys)}")
    print(f"KPIs sin árbol correspondiente: {len(kpi_without_tree)}")
    print(f"De los cuales tienen valor 0: {kpi_zero_without_tree}")
    print(f"Árboles sin KPI correspondiente: {len(tree_without_kpi)}")

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

    print(f"\n=== Comparación FINAL tras transformación ===")
    print(f"Coincidencias KPI-Árbol: {len(comunes)}")
    print(f"Solo KPI: {len(solo_kpi)}")
    print(f"Solo Árbol: {len(solo_tree)}")
    if solo_kpi:
        print("Ejemplo solo KPI:", list(solo_kpi)[:3])
    if solo_tree:
        print("Ejemplo solo Árbol:", list(solo_tree)[:3])

def main():
    """
    Función principal que extrae y procesa los datos del Excel
    """
    # Extraer datos
    historic_data = extract_historic_data(EXCEL_PATH, HISTORIC_SHEET)
    kpi_data = extract_kpi_data(EXCEL_PATH, KPI_SHEET)
    tree_data = extract_tree_data(EXCEL_PATH, TREE_SHEET)
    
    # Depuración: Verificar datos de árbol
    print("\n=== VERIFICACIÓN DE DATOS DE ÁRBOL ===")
    target_items = [
        item for item in tree_data 
        if str(item["CIA"]).upper() == "SP" and 
           str(item["PRJID"]) == "31200" and 
           "FABRICACIÓN UTILES" in str(item["ROW"]).strip().upper() and
           "FABRICACIÓN MECÁNICA" in str(item["COLUMN"]).strip().upper()
    ]
    
    if target_items:
        print(f"\nEncontrados {len(target_items)} registros para CIA=Sp, PRJID=31200, ROW=FABRICACIÓN UTILES, COLUMN=FABRICACIÓN MECÁNICA")
        print("\nRegistros encontrados:")
        for item in sorted(target_items, key=lambda x: (x["LEVEL"], x["NODE"])):
            print(f"  Nivel {item['LEVEL']}, Nodo {item['NODE']}, Padre {item['NODEP']}, ITMIN={item['ITMIN']}, VALUE={item['VALUE']}")
    else:
        print("\nNo se encontraron registros para CIA=Sp, PRJID=31200, ROW=FABRICACIÓN UTILES, COLUMN=FABRICACIÓN MECÁNICA")
    
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
    # Mostrar solo la casilla específica solicitada
    print("\n=== Casilla específica: CIA=Sp, PRJID=31200, ROW=FABRICACIÓN UTILES, COLUMN=FABRICACIÓN MECÁNICA ===")
    tipos = ["K", "H", "T"]
    for tipo in tipos:
        for r in result:
            if (str(r["CIA"]).upper() == "SP" and
                str(r["PRJID"]) == "31200" and
                "FABRICACIÓN UTILES" in str(r["ROW"]).strip().upper() and
                "FABRICACIÓN MECÁNICA" in str(r["COLUMN"]).strip().upper() and
                r["DATATYPE"] == tipo):
                print(f"  DATATYPE {tipo}: {r['DATACONTENTS']}")
                # Si es tipo T, mostrar el árbol simplificado
                if tipo == "T" and r["DATACONTENTS"] is not None:
                    import pprint
                    print("  Árbol simplificado (primeros niveles):")
                    pprint.pprint(r["DATACONTENTS"])
    return result

if __name__ == "__main__":
    main()