#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extractor de datos desde Excel para el dashboard
"""
import os
import sys
import pandas as pd

# Valores hardcodeados del Excel y sus hojas
EXCEL_PATH = "/Users/didac/Downloads/StoryMac/DashBTracker/PruebasCdM/Tchart_V06.xlsm"
HISTORIC_SHEET = "FrmBB_2"
KPI_SHEET = "FrmBB_3"

def extract_historic_data(excel_path, sheet_name):
    """
    Extrae datos históricos desde una hoja de Excel.
    """
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
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

def structure_data(historic_data, kpi_data):
    """
    Estructura los datos en la jerarquía correcta.
    """
    structured_data = {}

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
            structured_data[cia][prjid][row][column] = {
                "CONTENEDOR": {
                    "KPI": {},
                    "HISTORICOS": {"WKS": []}
                }
            }

        structured_data[cia][prjid][row][column]["CONTENEDOR"]["HISTORICOS"]["WKS"].append({
            "HPREV": record.get("HPREV"),
            "PPTO": record.get("PPTO"),
            "REAL": record.get("REAL")
        })

    for record in kpi_data:
        cia = record.get("CIA")
        prjid = record.get("PRJID")
        row = record.get("ROW")
        column = record.get("COLUMN")

        if cia in structured_data and prjid in structured_data[cia] and row in structured_data[cia][prjid] and column in structured_data[cia][prjid][row]:
            structured_data[cia][prjid][row][column]["CONTENEDOR"]["KPI"] = {
                "KPREV": record.get("KPREV"),
                "PDTE": record.get("PDTE"),
                "REALPREV": record.get("REALPREV"),
                "PPTOPREV": record.get("PPTOPREV")
            }

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
        'DATATYPE': 'K' o 'H',
        'DATACONTENTS': dict (KPI) o lista de dicts (HISTÓRICO)
    }
    """
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: No se encuentra el archivo Excel en la ruta: {EXCEL_PATH}")
        return []

    historic_data = extract_historic_data(EXCEL_PATH, HISTORIC_SHEET)
    kpi_data = extract_kpi_data(EXCEL_PATH, KPI_SHEET)

    # Indexar los KPI por la clave jerárquica
    kpi_index = {}
    for record in kpi_data:
        key = (
            str(record.get("CIA", "")),
            str(record.get("PRJID", "")),
            str(record.get("ROW", "")),
            str(record.get("COLUMN", ""))
        )
        kpi_index[key] = {
            "KPREV": record.get("KPREV"),
            "PDTE": record.get("PDTE"),
            "REALPREV": record.get("REALPREV"),
            "PPTOPREV": record.get("PPTOPREV")
        }

    # Agrupar históricos por la clave jerárquica
    historic_index = {}
    for record in historic_data:
        key = (
            str(record.get("CIA", "")),
            str(record.get("PRJID", "")),
            str(record.get("ROW", "")),
            str(record.get("COLUMN", ""))
        )
        if key not in historic_index:
            historic_index[key] = []
        historic_index[key].append({
            "WKS": record.get("WKS"),
            "PPTO": record.get("PPTO"),
            "REAL": record.get("REAL"),
            "HPREV": record.get("HPREV")
        })

    # Unir ambas fuentes en una lista plana, una entrada por tipo de dato
    result = []
    all_keys = set(list(kpi_index.keys()) + list(historic_index.keys()))
    for key in all_keys:
        cia, prjid, row, column = key
        # KPI
        if key in kpi_index:
            result.append({
                "CIA": cia,
                "PRJID": prjid,
                "ROW": row,
                "COLUMN": column,
                "DATATYPE": "K",
                "DATACONTENTS": kpi_index[key]
            })
        # HISTÓRICO
        if key in historic_index:
            result.append({
                "CIA": cia,
                "PRJID": prjid,
                "ROW": row,
                "COLUMN": column,
                "DATATYPE": "H",
                "DATACONTENTS": historic_index[key]
            })
    return result

if __name__ == "__main__":
    main()