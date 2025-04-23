import pandas as pd
import numpy as np
from datetime import datetime
import json

class DataProcessor:
    def __init__(self, historic_data=None, kpi_data=None):
        self.historic_data = historic_data
        self.kpi_data = kpi_data
    
    def process_data(self, debug=False):
        """Procesa los datos históricos y KPI para generar la estructura necesaria para el dashboard"""
        result = {
            'cellData': {},
            'rows': [],
            'columns': []
        }
        
        # Procesar datos KPI si están disponibles
        if self.kpi_data is not None:
            if debug:
                print("\n=== PROCESANDO DATOS KPI ===")
                print(f"Número de filas en datos KPI: {len(self.kpi_data)}")
            
            # Extraer filas y columnas únicas
            rows = sorted(self.kpi_data['ROW'].unique())
            columns = sorted(self.kpi_data['COLUMN'].unique())
            
            result['rows'] = rows
            result['columns'] = columns
            
            if debug:
                print(f"Filas detectadas: {rows}")
                print(f"Columnas detectadas: {columns}")
            
            # Procesar cada celda de los datos KPI
            for _, row in self.kpi_data.iterrows():
                cell_key = f"{row['ROW']}_{row['COLUMN']}"
                
                # Inicializar datos de la celda
                cell_data = {
                    'ROW': row['ROW'],
                    'COLUMN': row['COLUMN'],
                    'VALUE': row['VALUE'] if not pd.isna(row['VALUE']) else None,
                    'hasHistoric': False,
                    'timeSeries': []
                }
                
                # Añadir a la estructura de resultado
                result['cellData'][cell_key] = cell_data
            
            if debug:
                print(f"Procesadas {len(result['cellData'])} celdas de datos KPI")
        
        # Procesar datos históricos si están disponibles
        if self.historic_data is not None:
            if debug:
                print("\n=== PROCESANDO DATOS HISTÓRICOS ===")
                print(f"Número de filas en datos históricos: {len(self.historic_data)}")
                print("Primeras 5 filas de datos históricos:")
                print(self.historic_data.head())
            
            # Agrupar datos históricos por ROW y COLUMN
            grouped = self.historic_data.groupby(['ROW', 'COLUMN'])
            
            cells_with_historic = 0
            for (row, column), group in grouped:
                cell_key = f"{row}_{column}"
                
                if debug:
                    print(f"\nProcesando datos históricos para celda {cell_key} ({row}: {column})")
                    print(f"Número de puntos históricos: {len(group)}")
                
                # Verificar si la celda ya existe en los datos KPI
                if cell_key not in result['cellData']:
                    # Si no existe, crear una nueva entrada
                    cell_data = {
                        'ROW': row,
                        'COLUMN': column,
                        'VALUE': None,
                        'hasHistoric': True,
                        'timeSeries': []
                    }
                    result['cellData'][cell_key] = cell_data
                    
                    # Añadir la fila y columna a las listas si no existen
                    if row not in result['rows']:
                        result['rows'].append(row)
                    if column not in result['columns']:
                        result['columns'].append(column)
                else:
                    # Si existe, marcar que tiene datos históricos
                    result['cellData'][cell_key]['hasHistoric'] = True
                
                # Procesar cada punto de la serie temporal
                time_series = []
                for _, point in group.iterrows():
                    # Extraer y formatear el período
                    period = point['PERIOD']
                    
                    # Extraer valores
                    real = point['REAL'] if not pd.isna(point['REAL']) else None
                    ppto = point['PPTO'] if not pd.isna(point['PPTO']) else None
                    hprev = point['HPREV'] if not pd.isna(point['HPREV']) else None
                    
                    # Añadir punto a la serie temporal
                    time_point = {
                        'period': period,
                        'real': real,
                        'ppto': ppto,
                        'hprev': hprev
                    }
                    time_series.append(time_point)
                
                # Ordenar la serie temporal por período
                time_series.sort(key=lambda x: x['period'])
                
                # Actualizar la serie temporal en los datos de la celda
                result['cellData'][cell_key]['timeSeries'] = time_series
                
                cells_with_historic += 1
                
                if debug:
                    print(f"Serie temporal para {cell_key}:")
                    if time_series:
                        print(f"  Primer punto: {time_series[0]}")
                        print(f"  Último punto: {time_series[-1]}")
                        print(f"  Total puntos: {len(time_series)}")
                    else:
                        print("  No hay puntos en la serie temporal")
            
            if debug:
                print(f"\nTotal de celdas con datos históricos: {cells_with_historic}")
        
        # Ordenar las listas de filas y columnas
        result['rows'] = sorted(result['rows'])
        result['columns'] = sorted(result['columns'])
        
        if debug:
            # Guardar los datos procesados en un archivo JSON para análisis
            debug_file = "debug_processed_data.json"
            try:
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\nDatos procesados guardados para depuración en: {debug_file}")
            except Exception as e:
                print(f"Error al guardar archivo de depuración: {e}")
            
            # Verificar específicamente la celda "08: ROBCAD" si existe
            robcad_found = False
            for cell_key, cell_data in result['cellData'].items():
                if cell_data['ROW'] == '08' and 'ROBCAD' in cell_data['COLUMN']:
                    robcad_found = True
                    print("\n=== DEPURACIÓN ESPECÍFICA PARA 08: ROBCAD ===")
                    print(f"Clave de celda: {cell_key}")
                    print(f"Valor actual: {cell_data['VALUE']}")
                    print(f"Tiene datos históricos: {cell_data['hasHistoric']}")
                    
                    time_series = cell_data['timeSeries']
                    if time_series:
                        print(f"Serie temporal ({len(time_series)} puntos):")
                        print("Periodo\t\tREAL\t\tPPTO\t\tHPREV")
                        print("-" * 60)
                        for point in time_series[:5]:  # Mostrar solo los primeros 5 puntos
                            print(f"{point['period']}\t{point['real']}\t\t{point['ppto']}\t\t{point['hprev']}")
                        if len(time_series) > 5:
                            print("... (más puntos) ...")
                    else:
                        print("No hay datos históricos para esta celda.")
            
            if not robcad_found:
                print("\nNo se encontró la celda '08: ROBCAD' en los datos procesados.")
        
        return result