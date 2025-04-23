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

    def _normalize(self, val):
        if val is None:
            return ""
        return str(val).strip().upper()

    def process_data(self, debug=False):
        """
        Procesa los datos históricos y KPI para generar la estructura de datos completa
        """
        if debug:
            print("Iniciando procesamiento de datos...")

        result = {
            'cellData': {}
        }

        # Procesar los datos históricos
        self._process_historic_data(result, debug=debug)

        # Procesar los datos KPI
        self._process_kpi_data(result, debug=debug)

        # Verificar datos históricos procesados
        if debug:
            print("\n=== VERIFICACIÓN DE DATOS HISTÓRICOS PROCESADOS ===")
            cells_with_historic = sum(1 for cell in result['cellData'].values() if cell.get('hasHistoric', False))
            print(f"Total de celdas con datos históricos: {cells_with_historic}")
            for key, cell_data in result['cellData'].items():
                time_series = cell_data.get('timeSeries', [])
                print(f"Celda {key} ({cell_data.get('ROW', 'N/A')} - {cell_data.get('COLUMN', 'N/A')}) tiene {len(time_series)} registros históricos")
                if time_series and cells_with_historic <= 3:
                    print("  Ejemplos de datos históricos:")
                    for i, entry in enumerate(time_series[:3]):
                        print(f"    Registro {i+1}: period={entry.get('period', 'N/A')}, prev={entry.get('prev', 'N/A')}, ppto={entry.get('ppto', 'N/A')}, real={entry.get('real', 'N/A')}")
                    print()

        if debug:
            print(f"Procesamiento completado. Total de celdas: {len(result['cellData'])}")

        return result

    def _process_historic_data(self, result, debug=False):
        """
        Procesa los datos históricos
        """
        if debug:
            print(f"Procesando {len(self.historic_data)} registros históricos...")

        for idx, record in enumerate(self.historic_data):
            cia = self._normalize(record.get('CIA'))
            prjid = self._normalize(record.get('PRJID'))
            row = self._normalize(record.get('ROW'))
            column = self._normalize(record.get('COLUMN'))
            cell_key = f"{cia}|{prjid}|{row}|{column}"

            if debug:
                print(f"[{idx}] Procesando histórico: CIA={cia}, PRJID={prjid}, ROW={row}, COLUMN={column}, clave={cell_key}, PERIOD={record.get('PERIOD')}")

            # Inicializar la celda si no existe
            if cell_key not in result['cellData']:
                result['cellData'][cell_key] = {
                    'ROW': row,
                    'COLUMN': column,
                    'CIA': cia,
                    'PRJID': prjid,
                    'hasHistoric': True,
                    'timeSeries': []
                }
            else:
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

    def _process_kpi_data(self, result, debug=False):
        """
        Procesa los datos KPI
        """
        if debug:
            print(f"Procesando {len(self.kpi_data)} registros KPI...")

        for idx, record in enumerate(self.kpi_data):
            cia = self._normalize(record.get('CIA'))
            prjid = self._normalize(record.get('PRJID'))
            row = self._normalize(record.get('ROW'))
            column = self._normalize(record.get('COLUMN'))
            cell_key = f"{cia}|{prjid}|{row}|{column}"

            if debug:
                print(f"[{idx}] Procesando KPI: CIA={cia}, PRJID={prjid}, ROW={row}, COLUMN={column}, clave={cell_key}")

            if cell_key not in result['cellData']:
                result['cellData'][cell_key] = {
                    'ROW': row,
                    'COLUMN': column,
                    'CIA': cia,
                    'PRJID': prjid,
                    'hasHistoric': False
                }

            for key in ['REAL', 'PPTO', 'HPREV', 'KPREV', 'PDTE', 'REALPREV', 'PPTOPREV']:
                if key in record and record[key] is not None:
                    result['cellData'][cell_key][key] = record[key]

            if 'REAL' in record and record['REAL'] is not None:
                result['cellData'][cell_key]['VALUE'] = record['REAL']
            elif 'PPTO' in record and record['PPTO'] is not None:
                result['cellData'][cell_key]['VALUE'] = record['PPTO']
            elif 'HPREV' in record and record['HPREV'] is not None:
                result['cellData'][cell_key]['VALUE'] = record['HPREV']

        if debug:
            print(f"Datos KPI procesados. Total de celdas: {len(result['cellData'])}")


def process_data(historic_data, kpi_data, debug=False):
    """
    Procesa los datos históricos y KPI para crear una estructura unificada
    """
    if debug:
        print("=== PROCESANDO DATOS ===")
        print(f"Registros históricos: {len(historic_data)}")
        print(f"Registros KPI: {len(kpi_data)}")
        
        # Verificar campos disponibles en los datos históricos
        if historic_data:
            first_record = historic_data[0]
            print(f"Campos disponibles en el primer registro histórico: {list(first_record.keys())}")
            
            # Verificar si existe WKS
            if 'WKS' in first_record:
                print("Campo WKS encontrado en los datos históricos")
            else:
                print("¡ADVERTENCIA! No se encontró WKS en los datos históricos")
    
    # Crear estructura de datos
    result = {
        'cellData': {}
    }
    
    # Procesar datos históricos
    historic_cells_count = 0
    for record in historic_data:
        # Crear clave única para la celda
        cia = record.get('CIA', '')
        prjid = record.get('PRJID', '')
        row = record.get('ROW', '')
        column = record.get('COLUMN', '')
        
        cell_key = f"{cia}_{prjid}_{row}_{column}"
        
        # Verificar si la celda ya existe en el resultado
        if cell_key not in result['cellData']:
            result['cellData'][cell_key] = {
                'CIA': cia,
                'PRJID': prjid,
                'ROW': row,
                'COLUMN': column,
                'historicData': []
            }
            historic_cells_count += 1
        
        # Añadir datos históricos a la celda
        # Asegurarse de que los campos necesarios existen
        historic_entry = {
            'WKS': record.get('WKS', ''),  # Usar WKS como base temporal
            'PREV': record.get('HPREV', record.get('PREV', 0)),  # Intentar HPREV primero, luego PREV
            'PPTO': record.get('PPTO', 0),
            'REAL': record.get('REAL', 0)
        }
        
        # Añadir a la lista de datos históricos
        result['cellData'][cell_key]['historicData'].append(historic_entry)
    
    if debug:
        print(f"Celdas con datos históricos: {historic_cells_count}")
        
        # Mostrar ejemplo de datos históricos para la primera celda
        if historic_cells_count > 0:
            first_cell_key = next(iter(result['cellData']))
            first_cell = result['cellData'][first_cell_key]
            print(f"\nEjemplo de datos históricos para la celda {first_cell_key}:")
            print(f"  CIA: {first_cell.get('CIA')}")
            print(f"  PRJID: {first_cell.get('PRJID')}")
            print(f"  ROW: {first_cell.get('ROW')}")
            print(f"  COLUMN: {first_cell.get('COLUMN')}")
            print(f"  Número de registros históricos: {len(first_cell.get('historicData', []))}")
            
            # Mostrar los primeros 3 registros históricos
            for i, entry in enumerate(first_cell.get('historicData', [])[:3]):
                print(f"  Registro histórico {i+1}:")
                print(f"    WKS: {entry.get('WKS')}")
                print(f"    PREV: {entry.get('PREV')}")  # Ahora contiene el valor de HPREV
                print(f"    PPTO: {entry.get('PPTO')}")
                print(f"    REAL: {entry.get('REAL')}")
    
    # Procesar datos KPI
    kpi_cells_count = 0
    for record in kpi_data:
        # Crear clave única para la celda
        cia = record.get('CIA', '')
        prjid = record.get('PRJID', '')
        row = record.get('ROW', '')
        column = record.get('COLUMN', '')
        
        cell_key = f"{cia}_{prjid}_{row}_{column}"
        
        # Verificar si la celda ya existe en el resultado
        if cell_key not in result['cellData']:
            result['cellData'][cell_key] = {
                'CIA': cia,
                'PRJID': prjid,
                'ROW': row,
                'COLUMN': column,
                'historicData': []
            }
            kpi_cells_count += 1
        
        # Añadir datos KPI a la celda
        result['cellData'][cell_key]['KPREV'] = record.get('KPREV', 0)
        result['cellData'][cell_key]['PDTE'] = record.get('PDTE', 0)
        result['cellData'][cell_key]['REALPREV'] = record.get('REALPREV', 0)
        result['cellData'][cell_key]['PPTOPREV'] = record.get('PPTOPREV', 0)
    
    if debug:
        print(f"Celdas con datos KPI: {kpi_cells_count}")
    
    return result