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
    """
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: No se encuentra el archivo Excel en la ruta: {EXCEL_PATH}")
        return None

    try:
        # Extraer datos
        historic_data = extract_historic_data(EXCEL_PATH, HISTORIC_SHEET)
        kpi_data = extract_kpi_data(EXCEL_PATH, KPI_SHEET)

        # Estructurar los datos
        data = structure_data(historic_data, kpi_data)

        return data

    except Exception as e:
        print(f"Error al procesar los datos: {e}")
        return None

if __name__ == "__main__":
    main()