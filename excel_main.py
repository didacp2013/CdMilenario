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
from excel_utils import extraer_itmids_hoja

# Valores hardcodeados del Excel y sus hojas
# Cambiar la línea 11:
# EXCEL_PATH = "/Users/didac/Downloads/StoryMac/DashBTracker/PruebasCdM/DataKHT_V06.xlsm"

# Por esta ruta que apunta al directorio padre:
EXCEL_PATH = "/Users/didac/Downloads/StoryMac/DashBTracker/PruebasCdM/DataKHT_V06.xlsm"
HISTORIC_SHEET = "FrmBB_2"
KPI_SHEET = "FrmBB_3"
TREE_SHEET = "F_Asg3"
ITM_SHEET = "F_Asg5"

def wks_to_date(wks):
    """
    Convierte una semana de excel a fecha y número serial.
    Soporta formatos 'YYYY.WW' y 'YYYY-WWW'
    """
    try:
        # Verificar el formato y extraer año y semana
        if '.' in wks:  # Formato YYYY.WW
            parts = wks.split('.')
            if len(parts) != 2:
                print(f"Formato WKS inválido: {wks}")
                return None, None
            year = int(parts[0])
            week = int(parts[1])
        elif '-W' in wks:  # Formato YYYY-WWW
            parts = wks.split('-W')
            if len(parts) != 2:
                print(f"Formato WKS inválido: {wks}")
                return None, None
            year = int(parts[0])
            week = int(parts[1])
        else:
            print(f"Formato WKS no reconocido: {wks}")
            return None, None
            
        # Asegurar que la semana esté en el rango válido (1-53)
        if week < 1 or week > 53:
            print(f"Número de semana fuera de rango: {week}")
            return None, None
            
        from datetime import datetime, timedelta
        # Convertir a fecha usando el formato ISO
        date = datetime.strptime(f'{year}-W{week:02d}-1', '%Y-W%W-%w').date()
        excel_base = datetime(1899, 12, 30).date()
        excel_serial = (date - excel_base).days
        return date, excel_serial
    except Exception as e:
        print(f"Error al convertir WKS '{wks}': {str(e)}")
        return None, None

def extract_historic_data(excel_path, sheet_name):
    """
    Extrae datos históricos desde una hoja de Excel.
    """
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        records = []
        for _, row in df.iterrows():
            record = {
                'CIA': str(row['CIA']).strip(),
                'PRJID': str(row['PRJID']).strip(),
                'ROW': str(row['ROW']).strip(),
                'COLUMN': str(row['COLUMN']).strip(),
                'HPREV': float(row['HPREV']) if pd.notna(row['HPREV']) else 0,
                'PPTO': float(row['PPTO']) if pd.notna(row['PPTO']) else 0,
                'REAL': float(row['REAL']) if pd.notna(row['REAL']) else 0,
                'WKS': str(row['WKS']).strip()
            }
            date, serial = wks_to_date(record['WKS'])
            record['WKS_DATE'] = date
            record['WKS_SERIAL'] = serial
            records.append(record)
        return records
    except Exception:
        return []

def extract_kpi_data(excel_path, sheet_name):
    """
    Extrae datos KPI desde una hoja de Excel.
    """
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        records = []
        for _, row in df.iterrows():
            record = {
                'CIA': str(row['CIA']).strip(),
                'PRJID': str(row['PRJID']).strip(),
                'ROW': str(row['ROW']).strip(),
                'COLUMN': str(row['COLUMN']).strip(),
                'KPREV': float(row['KPREV']) if pd.notna(row['KPREV']) else 0,
                'PDTE': float(row['PDTE']) if pd.notna(row['PDTE']) else 0,
                'REALPREV': float(row['REALPREV']) if pd.notna(row['REALPREV']) else 0,
                'PPTOPREV': float(row['PPTOPREV']) if pd.notna(row['PPTOPREV']) else 0
            }
            records.append(record)
        return records
    except Exception:
        return []

def extract_itm_data(excel_path, sheet_name=ITM_SHEET):
    """
    Extrae datos de la tabla F_Asg5 (datos de items).
    Asegura que todos los campos sean texto.
    """
    try:
        # Leer el Excel asegurando que todos los campos sean texto
        df = pd.read_excel(excel_path, sheet_name=sheet_name, dtype={
            'CIA': str,
            'PRJID': str,
            'ITMID': str,
            'ITMFRM': str
        })
        
        # Convertir a lista de diccionarios y asegurar que todos los campos sean texto
        records = []
        for _, row in df.iterrows():
            record = {
                'CIA': str(row['CIA']).strip(),
                'PRJID': str(row['PRJID']).strip(),
                'ITMID': str(row['ITMID']).strip(),
                'ITMFRM': str(row['ITMFRM']).strip()
            }
            records.append(record)
        
        return records
    except Exception:
        return []

def structure_data(historic_data, kpi_data, tree_data, fasg5_data=None):
    """
    Estructura los datos en un formato jerárquico por CIA, PRJID, ROW, COLUMN
    """
    structured_data = {}

    # Procesar datos históricos (H)
    for record in historic_data:
        cia = record.get("CIA")
        prjid = str(record.get("PRJID"))
        row = str(record.get("ROW", "")).strip()
        column = str(record.get("COLUMN", "")).strip()

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
        prjid = str(record.get("PRJID"))
        row = str(record.get("ROW", "")).strip()
        column = str(record.get("COLUMN", "")).strip()

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

    # Construir lookup de ITMFRM
    from excel_utils import build_itmfrm_lookup
    itmfrm_lookup = build_itmfrm_lookup(fasg5_data) if fasg5_data else {}

    # Procesar datos tipo T (árbol), solo si se proporciona y no está vacío
    if tree_data:
        tree_by_row = {}
        for record in tree_data:
            row = str(record.get("ROW", "")).strip()
            column = str(record.get("COLUMN", "")).strip()
            row_key = (record.get("CIA"), record.get("PRJID"), row)
            if row_key not in tree_by_row:
                tree_by_row[row_key] = []
            tree_by_row[row_key].append(record)
        
        for row_key, items in tree_by_row.items():
            cia, prjid, row = row_key
            column_structures = procesar_datos_arbol(items, itmfrm_lookup=itmfrm_lookup, fasg5_data=fasg5_data)

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

    # Correspondencia 1:1 en las claves para K, H, T
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

    return structured_data

def main():
    """
    Función principal que extrae y procesa los datos del Excel
    """
    # Extraer datos
    historic_data = extract_historic_data(EXCEL_PATH, HISTORIC_SHEET)
    kpi_data = extract_kpi_data(EXCEL_PATH, KPI_SHEET)
    tree_data = extract_tree_data(EXCEL_PATH, TREE_SHEET)
    fasg5_data = extract_itm_data(EXCEL_PATH, sheet_name="F_Asg5")
    
    # Estructurar datos K+H+T+I
    structured_data = structure_data(historic_data, kpi_data, tree_data, fasg5_data=fasg5_data)
    
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
    return result

if __name__ == "__main__":
    main()