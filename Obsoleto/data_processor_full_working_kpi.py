#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo para procesar y transformar los datos para el cuadro de mando
"""
import json
from datetime import datetime

class DataProcessor:
    """Clase para procesar datos extraídos de Excel"""
    
    def __init__(self, historic_data=None, kpi_data=None):
        """Inicializa el procesador con datos históricos y KPI"""
        self.historic_data = historic_data if historic_data is not None else []
        self.kpi_data = kpi_data if kpi_data is not None else []
        self.cell_data = {}  # Diccionario para almacenar datos de celdas
    
    def process_data(self, data, is_kpi_data=False):
        self.data = data
        self.is_kpi_data = is_kpi_data
    
    def process_data(self, debug=False):
        """
        Procesa los datos históricos y KPI para generar la estructura de datos completa
        """
        if debug:
            print("Iniciando procesamiento de datos...")
        
        # Inicializar el diccionario de resultados
        result = {
            'cellData': {}
        }
        
        # Procesar los datos históricos
        self._process_historic_data(result, debug=debug)  # Changed from process_historic_data
        
        # Procesar datos KPI si existen
        if self.kpi_data:
            self.process_kpi_data(debug=debug)
        
        # Extraer categorías y subcategorías
        categories = set()
        subcategories = set()
        
        for cell_key, cell_data in self.cell_data.items():
            row = cell_data.get('ROW', '')
            column = cell_data.get('COLUMN', '')
            
            if row:
                categories.add(row)
            if column:
                subcategories.add(column)
        
        if debug:
            print(f"Procesados {len(self.cell_data)} registros de datos")
            print(f"Categorías encontradas: {len(categories)}")
            print(f"Subcategorías encontradas: {len(subcategories)}")
        
        # Crear la estructura de datos final
        result = {
            'categories': sorted(list(categories)),
            'subcategories': sorted(list(subcategories)),
            'cellData': self.cell_data
        }
        
        return result
    
    def process_kpi_data(self, debug=False):
        """Procesa los datos KPI y los integra en la estructura de celdas"""
        if not self.kpi_data:
            if debug:
                print("No hay datos KPI para procesar")
            return
        
        if debug:
            print(f"Procesando {len(self.kpi_data)} registros de datos KPI")
        
        # Contador para seguimiento
        kpi_cells_processed = 0
        
        # Procesar cada registro KPI
        for kpi_record in self.kpi_data:
            # Extraer información clave
            row = kpi_record.get('ROW')
            column = kpi_record.get('COLUMN')
            cia = kpi_record.get('CIA')
            prjid = kpi_record.get('PRJID')
            
            if not row or not column:
                if debug:
                    print(f"Registro KPI sin ROW o COLUMN: {kpi_record}")
                continue
            
            # Crear clave única para la celda
            cell_key = f"{cia}|{prjid}|{row}|{column}" if cia and prjid else f"{row}|{column}"
            
            # Verificar si la celda ya existe, si no, crearla
            if cell_key not in self.cell_data:
                self.cell_data[cell_key] = {
                    'CIA': cia,
                    'PRJID': prjid,
                    'ROW': row,
                    'COLUMN': column
                }
            
            # Añadir datos KPI a la celda - USAR DIRECTAMENTE LOS VALORES DEL EXCEL
            cell = self.cell_data[cell_key]
            
            # Transferir directamente los valores KPI sin procesamiento adicional
            if 'KPREV' in kpi_record:
                cell['KPREV'] = kpi_record['KPREV']
            if 'PDTE' in kpi_record:
                cell['PDTE'] = kpi_record['PDTE']
            if 'REALPREV' in kpi_record:
                cell['REALPREV'] = kpi_record['REALPREV']
            if 'PPTOPREV' in kpi_record:
                cell['PPTOPREV'] = kpi_record['PPTOPREV']
            
            if debug and (kpi_cells_processed < 5 or kpi_cells_processed % 20 == 0):
                print(f"Celda KPI {cell_key}:")
                print(f"  KPREV={cell.get('KPREV')}")
                print(f"  PDTE={cell.get('PDTE')}")
                print(f"  REALPREV={cell.get('REALPREV')}")
                print(f"  PPTOPREV={cell.get('PPTOPREV')}")
            
            kpi_cells_processed += 1
        
        if debug:
            print(f"Procesadas {kpi_cells_processed} celdas con datos KPI")


class DataProcessor:
    def __init__(self, historic_data, kpi_data):
        self.historic_data = historic_data
        self.kpi_data = kpi_data
        self.processed_data = {
            'cellData': {}
        }
    
    def process_data(self, debug=False):
        """
        Procesa los datos históricos y KPI para generar la estructura de datos completa
        """
        if debug:
            print("Iniciando procesamiento de datos...")
        
        # Inicializar el diccionario de resultados
        result = {
            'cellData': {}
        }
        
        # Procesar los datos históricos
        self._process_historic_data(result, debug=debug)  # Changed from process_historic_data
        
        # Procesar los datos KPI
        self._process_kpi_data(result, debug=debug)
        
        if debug:
            print(f"Procesamiento completado. Total de celdas: {len(result['cellData'])}")
        
        return result
    
    def _process_historic_data(self, result, debug=False):
        """
        Procesa los datos históricos
        """
        if debug:
            print(f"Procesando {len(self.historic_data)} registros históricos...")
        
        # Procesar cada registro histórico
        for record in self.historic_data:
            # Extraer información clave
            cia = record.get('CIA')
            prjid = record.get('PRJID')
            row = record.get('ROW')
            column = record.get('COLUMN')
            
            if not all([row, column]):  # CIA y PRJID pueden ser opcionales
                if debug:
                    print(f"Registro histórico incompleto: {record}")
                continue
            
            # Crear clave única para la celda
            cell_key = f"{row}_{column}"
            
            # Inicializar la celda si no existe
            if cell_key not in result['cellData']:
                result['cellData'][cell_key] = {
                    'ROW': row,
                    'COLUMN': column,
                    'hasHistoric': True,
                    'timeSeries': []
                }
                
                # Añadir CIA y PRJID si existen
                if cia:
                    result['cellData'][cell_key]['CIA'] = cia
                if prjid:
                    result['cellData'][cell_key]['PRJID'] = prjid
            else:
                # Marcar que tiene datos históricos
                result['cellData'][cell_key]['hasHistoric'] = True
                if 'timeSeries' not in result['cellData'][cell_key]:
                    result['cellData'][cell_key]['timeSeries'] = []
            
            # Añadir punto a la serie temporal
            time_point = {
                'period': record.get('PERIOD', ''),
                'real': record.get('REAL', 0),
                'ppto': record.get('PPTO', 0),
                'prev': record.get('HPREV', 0)
            }
            
            result['cellData'][cell_key]['timeSeries'].append(time_point)
        
        if debug:
            print(f"Datos históricos procesados. Celdas con histórico: {sum(1 for cell in result['cellData'].values() if cell.get('hasHistoric', False))}")
    
    def _process_kpi_data(self, result, debug=False):
        """
        Procesa los datos KPI
        """
        if debug:
            print(f"Procesando {len(self.kpi_data)} registros KPI...")
        
        # Procesar cada registro KPI
        for record in self.kpi_data:
            # Extraer información clave
            cia = record.get('CIA')
            prjid = record.get('PRJID')
            row = record.get('ROW')
            column = record.get('COLUMN')
            
            if not all([row, column]):  # CIA y PRJID pueden ser opcionales en algunos casos
                if debug:
                    print(f"Registro KPI incompleto: {record}")
                continue
            
            # Crear clave única para la celda
            cell_key = f"{row}_{column}"
            
            # Inicializar la celda si no existe
            if cell_key not in result['cellData']:
                result['cellData'][cell_key] = {
                    'ROW': row,
                    'COLUMN': column,
                    'hasHistoric': False
                }
                
                # Añadir CIA y PRJID si existen
                if cia:
                    result['cellData'][cell_key]['CIA'] = cia
                if prjid:
                    result['cellData'][cell_key]['PRJID'] = prjid
            
            # Añadir datos KPI
            for key in ['REAL', 'PPTO', 'HPREV', 'KPREV', 'PDTE', 'REALPREV', 'PPTOPREV']:
                if key in record and record[key] is not None:
                    result['cellData'][cell_key][key] = record[key]
            
            # Añadir el valor actual (puede ser REAL, PPTO o HPREV según prioridad)
            if 'REAL' in record and record['REAL'] is not None:
                result['cellData'][cell_key]['VALUE'] = record['REAL']
            elif 'PPTO' in record and record['PPTO'] is not None:
                result['cellData'][cell_key]['VALUE'] = record['PPTO']
            elif 'HPREV' in record and record['HPREV'] is not None:
                result['cellData'][cell_key]['VALUE'] = record['HPREV']
        
        if debug:
            print(f"Datos KPI procesados. Total de celdas: {len(result['cellData'])}")