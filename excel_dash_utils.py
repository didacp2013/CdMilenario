#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utilidades para el dashboard
"""
import os
import sys
import socket
import signal
import subprocess
import pandas as pd

def load_data(excel_path=None, historic_sheet=None, kpi_sheet=None, debug=False):
    """
    Carga datos desde un archivo Excel o JSON
    """
    try:
        if debug:
            print("\n=== CARGANDO DATOS ===")
            print(f"Archivo Excel: {excel_path}")
            print(f"Hoja histórica: {historic_sheet}")
            print(f"Hoja KPI: {kpi_sheet}")
        
        if not excel_path:
            print("No se especificó archivo Excel")
            return None
        
        historic_data = extract_historic_data(excel_path, historic_sheet) if historic_sheet else []
        kpi_data = extract_kpi_data(excel_path, kpi_sheet) if kpi_sheet else []
        
        processor = DataProcessor(historic_data, kpi_data)
        processed_data = processor.process_data()
        return processed_data
        
    except Exception as e:
        import traceback
        print(f"Error al cargar datos desde Excel: {e}")
        traceback.print_exc()
        return None

def extract_historic_data(excel_path, sheet_name):
    """
    Extrae datos históricos desde una hoja de Excel.

    Args:
        excel_path (str): Ruta al archivo Excel.
        sheet_name (str): Nombre de la hoja de datos históricos.

    Returns:
        list: Lista de registros históricos procesados.
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

    Args:
        excel_path (str): Ruta al archivo Excel.
        sheet_name (str): Nombre de la hoja de datos KPI.

    Returns:
        list: Lista de registros KPI procesados.
    """
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"Error al extraer datos KPI: {e}")
        return []

def format_historic_data(raw_historic_data):
    """
    Formats raw historical data into the new structure.
    """
    formatted_data = []
    for record in raw_historic_data:
        formatted_data.append({
            "WKS": record.get("WKS"),
            "REAL": record.get("REAL"),
            "PPTO": record.get("PPTO"),
            "HPREV": record.get("HPREV")
        })
    return formatted_data

def format_kpi_data(raw_kpi_data):
    """
    Formats raw KPI data into the new structure.
    """
    return {
        "KPREV": raw_kpi_data.get("KPREV"),
        "PDTE": raw_kpi_data.get("PDTE"),
        "REALPREV": raw_kpi_data.get("REALPREV"),
        "PPTOPREV": raw_kpi_data.get("PPTOPREV")
    }

def combine_data(historic_data, kpi_data):
    """
    Combines historical and KPI data into the final structure.
    """
    combined_data = []
    for hist_record in historic_data:
        key = f"{hist_record.get('CIA')}_{hist_record.get('PRJID')}_{hist_record.get('ROW')}_{hist_record.get('COLUMN')}"
        combined_data.append({
            "CIA": hist_record.get("CIA"),
            "PRJID": hist_record.get("PRJID"),
            "ROW": hist_record.get("ROW"),
            "COLUMN": hist_record.get("COLUMN"),
            "CONTENIDO": {
                "KPIS": format_kpi_data(kpi_data.get(key, {})),
                "HIST": format_historic_data(hist_record.get("timeSeries", []))
            }
        })
    return combined_data

class DataProcessor:
    """
    Clase para procesar datos históricos y KPI y estructurarlos según el modelo definido.
    """

    def __init__(self, historic_data, kpi_data):
        self.historic_data = historic_data
        self.kpi_data = kpi_data

    def process_data(self):
        """
        Procesa los datos históricos y KPI para generar la estructura final.
        """
        result = {}

        # Procesar datos históricos
        for record in self.historic_data:
            cia = record.get("CIA")
            prjid = record.get("PRJID")
            row = record.get("ROW")
            column = record.get("COLUMN")

            # Crear clave única para la celda
            cell_key = f"{cia}_{prjid}_{row}_{column}"

            # Crear la estructura base si no existe
            if cell_key not in result:
                result[cell_key] = {
                    "CIA": cia,
                    "PRJID": prjid,
                    "ROW": row,
                    "COLUMN": column,
                    "CONTENIDO": {
                        "KPIS": {},
                        "HIST": []
                    }
                }

            # Agregar datos históricos si son válidos
            if (
                record.get("CIA") == cia and
                record.get("PRJID") == prjid and
                record.get("ROW") == row and
                record.get("COLUMN") == column
            ):
                result[cell_key]["CONTENIDO"]["HIST"].append({
                    "WKS": record.get("WKS"),
                    "REAL": record.get("REAL"),
                    "PPTO": record.get("PPTO"),
                    "HPREV": record.get("HPREV")
                })

        # Agregar datos KPI
        for kpi_record in self.kpi_data:
            kpi_key = f"{kpi_record.get('CIA')}_{kpi_record.get('PRJID')}_{kpi_record.get('ROW')}_{kpi_record.get('COLUMN')}"
            if kpi_key in result:
                result[kpi_key]["CONTENIDO"]["KPIS"] = {
                    "KPREV": kpi_record.get("KPREV"),
                    "PDTE": kpi_record.get("PDTE"),
                    "REALPREV": kpi_record.get("REALPREV"),
                    "PPTOPREV": kpi_record.get("PPTOPREV")
                }

        return list(result.values())