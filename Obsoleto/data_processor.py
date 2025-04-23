#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo para procesar y transformar los datos para el cuadro de mando
"""
import pandas as pd
import numpy as np
import json
from datetime import datetime

class DataProcessor:
    """Clase para procesar los datos extraídos de Excel"""
    
    def __init__(self, data_frame, is_kpi_data=False):
        """
        Inicializa el procesador de datos
        
        Args:
            data_frame (pandas.DataFrame): DataFrame con los datos extraídos de Excel
            is_kpi_data (bool): Si son datos de KPIs
        """
        self.df = data_frame.copy()
        self.is_kpi_data = is_kpi_data
        self.processed_data = {}
        self.column_mappings = self._detect_columns()
    
    def _detect_columns(self):
        """
        Detecta automáticamente las columnas relevantes en el DataFrame
        
        Returns:
            dict: Mapeo de columnas detectadas
        """
        # Convertir nombres de columnas a minúsculas para facilitar la detección
        columns_lower = [col.lower() for col in self.df.columns]
        
        # Opciones de nombres de columnas para cada tipo de dato
        category_options = ['row', 'categoría', 'categoria', 'category']
        subcategory_options = ['column', 'subcategoría', 'subcategoria', 'subcategory']
        period_options = ['wks', 'período', 'periodo', 'period', 'date', 'fecha']
        value_options = ['value', 'valor', 'amount', 'importe', 'real']
        project_options = ['prjid', 'projectid', 'id_proyecto', 'proyecto', 'project']
        ppto_options = ['ppto', 'presupuesto', 'budget']
        prev_options = ['prev', 'previsión', 'prevision', 'forecast']
        
        # Opciones adicionales para datos de KPIs
        prev_value_options = ['prev_eur', 'prevision_valor', 'prev_value']
        real_prev_percent_options = ['real_prev', '%real_prev', 'real_prev_%']
        ppto_prev_percent_options = ['ppto_prev', '%ppto_prev', 'ppto_prev_%']
        pending_value_options = ['pending', 'pendiente', 'real_menos_prev']
        
        # Inicializar mapeo
        mappings = {
            'category': None,
            'subcategory': None,
            'period': None,
            'value': None,
            'project': None,
            'ppto': None,
            'prev': None,
            # Campos para KPIs
            'prev_value': None,
            'real_prev_percent': None,
            'ppto_prev_percent': None,
            'pending_value': None
        }
        
        # Detectar cada tipo de columna
        for i, col in enumerate(columns_lower):
            # Buscar coincidencias exactas primero
            if col in category_options and mappings['category'] is None:
                mappings['category'] = self.df.columns[i]
            elif col in subcategory_options and mappings['subcategory'] is None:
                mappings['subcategory'] = self.df.columns[i]
            elif col in period_options and mappings['period'] is None:
                mappings['period'] = self.df.columns[i]
            elif col in value_options and mappings['value'] is None:
                mappings['value'] = self.df.columns[i]
            elif col in project_options and mappings['project'] is None:
                mappings['project'] = self.df.columns[i]
            elif col in ppto_options and mappings['ppto'] is None:
                mappings['ppto'] = self.df.columns[i]
            elif col in prev_options and mappings['prev'] is None:
                mappings['prev'] = self.df.columns[i]
            # KPI específicos
            elif col in prev_value_options and mappings['prev_value'] is None:
                mappings['prev_value'] = self.df.columns[i]
            elif col in real_prev_percent_options and mappings['real_prev_percent'] is None:
                mappings['real_prev_percent'] = self.df.columns[i]
            elif col in ppto_prev_percent_options and mappings['ppto_prev_percent'] is None:
                mappings['ppto_prev_percent'] = self.df.columns[i]
            elif col in pending_value_options and mappings['pending_value'] is None:
                mappings['pending_value'] = self.df.columns[i]
            
            # Si no hay coincidencia exacta, buscar coincidencias parciales
            else:
                for option_list, key in [
                    (category_options, 'category'),
                    (subcategory_options, 'subcategory'),
                    (period_options, 'period'),
                    (value_options, 'value'),
                    (project_options, 'project'),
                    (ppto_options, 'ppto'),
                    (prev_options, 'prev'),
                    # KPI específicos
                    (prev_value_options, 'prev_value'),
                    (real_prev_percent_options, 'real_prev_percent'),
                    (ppto_prev_percent_options, 'ppto_prev_percent'),
                    (pending_value_options, 'pending_value')
                ]:
                    for option in option_list:
                        if option in col and mappings[key] is None:
                            mappings[key] = self.df.columns[i]
                            break
        
        # Si no se encuentran algunas columnas, usar columnas por orden
        if mappings['category'] is None and len(self.df.columns) > 0:
            mappings['category'] = self.df.columns[0]
        
        if mappings['subcategory'] is None and len(self.df.columns) > 1:
            mappings['subcategory'] = self.df.columns[1]
        
        if mappings['period'] is None and len(self.df.columns) > 2:
            mappings['period'] = self.df.columns[2]
        
        if mappings['value'] is None and len(self.df.columns) > 3:
            mappings['value'] = self.df.columns[3]
        
        print("Mapeo de columnas detectado:")
        print(json.dumps({k: v for k, v in mappings.items() if v is not None}, indent=2))
        
        return mappings
    
    def process(self):
        """
        Procesa los datos para generar la estructura necesaria para el cuadro de mando
        
        Returns:
            dict: Datos procesados en formato adecuado para la visualización
        """
        try:
            # Verificar que se detectaron las columnas mínimas necesarias
            required_cols = ['category', 'subcategory']
            
            if not self.is_kpi_data:
                required_cols.extend(['period', 'value'])
            else:
                # Para datos de KPIs, necesitamos al menos uno de estos campos
                kpi_fields = ['prev_value', 'real_prev_percent', 'ppto_prev_percent', 'pending_value']
                if not any(self.column_mappings[field] is not None for field in kpi_fields):
                    raise ValueError(f"No se pudo detectar ninguna columna de KPI: {', '.join(kpi_fields)}")
            
            for col_type in required_cols:
                if self.column_mappings[col_type] is None:
                    raise ValueError(f"No se pudo detectar la columna de tipo '{col_type}'")
            
            # Extraer columnas con nombres detectados
            cat_col = self.column_mappings['category']
            subcat_col = self.column_mappings['subcategory']
            period_col = self.column_mappings['period']
            value_col = self.column_mappings['value']
            project_col = self.column_mappings['project']
            ppto_col = self.column_mappings['ppto']
            prev_col = self.column_mappings['prev']
            
            # Columnas específicas para KPIs
            prev_value_col = self.column_mappings['prev_value']
            real_prev_percent_col = self.column_mappings['real_prev_percent']
            ppto_prev_percent_col = self.column_mappings['ppto_prev_percent']
            pending_value_col = self.column_mappings['pending_value']
            
            # Crear copia trabajar con ella
            df = self.df.copy()
            
            # Asegurar que las columnas necesarias existen
            required_cols_actual = [cat_col, subcat_col]
            if not self.is_kpi_data:
                required_cols_actual.extend([period_col, value_col])
            
            missing_cols = [col for col in required_cols_actual if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Faltan columnas requeridas: {', '.join(missing_cols)}")
            
            # Eliminar filas con valores faltantes en columnas críticas
            df = df.dropna(subset=required_cols_actual)
            
            # Convertir valores a tipos adecuados (solo para datos históricos)
            if not self.is_kpi_data and value_col in df.columns:
                df[value_col] = pd.to_numeric(df[value_col], errors='coerce')
                # Eliminar filas con valores no numéricos
                df = df.dropna(subset=[value_col])
            
            # Convertir valores numéricos para KPIs
            if self.is_kpi_data:
                for col in [prev_value_col, real_prev_percent_col, ppto_prev_percent_col, pending_value_col]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Extraer listas únicas ordenadas
            categories = sorted(df[cat_col].unique().tolist())
            subcategories = sorted(df[subcat_col].unique().tolist())
            
            # Solo para datos históricos
            periods = []
            if not self.is_kpi_data and period_col in df.columns:
                periods = sorted(df[period_col].unique().tolist())
            
            # Si existe columna de proyecto, extraer proyectos únicos
            projects = []
            if project_col and project_col in df.columns:
                projects = sorted(df[project_col].unique().tolist())
            
            # Organizar datos para la visualización
            self.processed_data = {
                'categories': categories,
                'subcategories': subcategories,
                'periods': periods,
                'projects': projects,
                'hasProjects': len(projects) > 0,
                'hasPpto': ppto_col is not None and ppto_col in df.columns,
                'hasPrev': prev_col is not None and prev_col in df.columns,
                'cellData': {}
            }
            
            # Configuración específica para KPIs
            if self.is_kpi_data:
                self.processed_data['isKpiData'] = True
                self.processed_data['hasPrevValue'] = prev_value_col is not None and prev_value_col in df.columns
                self.processed_data['hasRealPrevPercent'] = real_prev_percent_col is not None and real_prev_percent_col in df.columns
                self.processed_data['hasPptoPrevPercent'] = ppto_prev_percent_col is not None and ppto_prev_percent_col in df.columns
                self.processed_data['hasPendingValue'] = pending_value_col is not None and pending_value_col in df.columns
            
            # Añadir información de fechas y generación
            self.processed_data['generatedAt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Procesar datos de celdas
            if not self.is_kpi_data:
                # Procesamiento para datos históricos
                self._process_historic_cell_data(df, cat_col, subcat_col, period_col, value_col, project_col, ppto_col, prev_col)
            else:
                # Procesamiento para datos de KPIs
                self._process_kpi_cell_data(df, cat_col, subcat_col, project_col, prev_value_col, real_prev_percent_col, ppto_prev_percent_col, pending_value_col)
            
            # Calcular totales
            self._calculate_totals()
            
            return self.processed_data
            
        except Exception as e:
            raise Exception(f"Error al procesar datos: {str(e)}")
    
    def _process_historic_cell_data(self, df, cat_col, subcat_col, period_col, value_col, project_col, ppto_col, prev_col):
        """
        Procesa los datos históricos de celdas para preparar la estructura del cuadro de mando
        
        Args:
            df (pandas.DataFrame): DataFrame a procesar
            cat_col, subcat_col, period_col, value_col: Nombres de columnas
            project_col, ppto_col, prev_col: Nombres de columnas opcionales
        """
        # Agrupar por categoría, subcategoría y período
        group_cols = [cat_col, subcat_col, period_col]
        
        # Añadir proyecto si existe
        if project_col and project_col in df.columns:
            group_cols = [project_col] + group_cols
        
        # Si no hay columnas opcionales, usar simple agrupación por suma
        if (not ppto_col or ppto_col not in df.columns) and (not prev_col or prev_col not in df.columns):
            grouped = df.groupby(group_cols)[value_col].sum().reset_index()
            
            # Procesar cada fila agrupada
            for _, row in grouped.iterrows():
                # Crear clave de celda
                if project_col and project_col in df.columns:
                    cell_key = f"{row[project_col]}|{row[cat_col]}|{row[subcat_col]}"
                else:
                    cell_key = f"{row[cat_col]}|{row[subcat_col]}"
                
                # Inicializar datos de celda si no existe
                if cell_key not in self.processed_data['cellData']:
                    if project_col and project_col in df.columns:
                        self.processed_data['cellData'][cell_key] = {
                            'projectId': row[project_col],
                            'category': row[cat_col],
                            'subcategory': row[subcat_col],
                            'timeSeries': [],
                            'periodsWithData': 0,
                            'lastValue': 0
                        }
                    else:
                        self.processed_data['cellData'][cell_key] = {
                            'category': row[cat_col],
                            'subcategory': row[subcat_col],
                            'timeSeries': [],
                            'periodsWithData': 0,
                            'lastValue': 0
                        }
                
                # Añadir punto de serie temporal
                self.processed_data['cellData'][cell_key]['timeSeries'].append({
                    'period': row[period_col],
                    'value': float(row[value_col])
                })
                
                # Incrementar contador de períodos
                self.processed_data['cellData'][cell_key]['periodsWithData'] += 1
        
        # Si hay columnas adicionales, incluirlas
        else:
            # Preparar diccionario para agrupar
            agg_dict = {value_col: 'sum'}
            
            if ppto_col and ppto_col in df.columns:
                agg_dict[ppto_col] = 'sum'
            
            if prev_col and prev_col in df.columns:
                agg_dict[prev_col] = 'sum'
            
            # Agrupar con todas las columnas
            grouped = df.groupby(group_cols).agg(agg_dict).reset_index()
            
            # Procesar cada fila agrupada
            for _, row in grouped.iterrows():
                # Crear clave de celda
                if project_col and project_col in df.columns:
                    cell_key = f"{row[project_col]}|{row[cat_col]}|{row[subcat_col]}"
                else:
                    cell_key = f"{row[cat_col]}|{row[subcat_col]}"
                
                # Inicializar datos de celda si no existe
                if cell_key not in self.processed_data['cellData']:
                    initial_data = {
                        'category': row[cat_col],
                        'subcategory': row[subcat_col],
                        'timeSeries': [],
                        'periodsWithData': 0,
                        'lastValue': 0
                    }
                    
                    if project_col and project_col in df.columns:
                        initial_data['projectId'] = row[project_col]
                        
                    self.processed_data['cellData'][cell_key] = initial_data
                
                # Preparar punto de serie temporal
                time_point = {
                    'period': row[period_col],
                    'value': float(row[value_col])
                }
                
                # Añadir valores adicionales si existen
                if ppto_col and ppto_col in df.columns:
                    time_point['ppto'] = float(row[ppto_col]) if not pd.isna(row[ppto_col]) else 0
                
                if prev_col and prev_col in df.columns:
                    time_point['prev'] = float(row[prev_col]) if not pd.isna(row[prev_col]) else 0
                
                # Añadir punto de serie temporal
                self.processed_data['cellData'][cell_key]['timeSeries'].append(time_point)
                
                # Incrementar contador de períodos
                self.processed_data['cellData'][cell_key]['periodsWithData'] += 1
        
        # Procesar cada celda para calcular últimos valores y métricas comparativas
        for cell_key, cell_data in self.processed_data['cellData'].items():
            # Ordenar series temporales por período (para tener el último período al final)
            cell_data['timeSeries'] = sorted(cell_data['timeSeries'], key=lambda x: x['period'])
            
            # Actualizar último valor
            if cell_data['timeSeries']:
                cell_data['lastValue'] = cell_data['timeSeries'][-1]['value']
                
                # Si hay PPTO y PREV, añadir métricas comparativas
                has_ppto = ppto_col and ppto_col in df.columns
                has_prev = prev_col and prev_col in df.columns
                
                if has_ppto or has_prev:
                    last_point = cell_data['timeSeries'][-1]
                    
                    # Inicializar valores comparativos
                    cell_data['lastPptoValue'] = last_point.get('ppto', 0) if has_ppto else 0
                    cell_data['lastPrevValue'] = last_point.get('prev', 0) if has_prev else 0
                    
                    # Calcular métricas comparativas
                    prvPtoPercent = 0
                    if has_ppto and has_prev and cell_data['lastPptoValue'] != 0:
                        prvPtoPercent = (cell_data['lastPrevValue'] / cell_data['lastPptoValue']) * 100
                    
                    realPrvPercent = 0
                    if has_prev and cell_data['lastPrevValue'] != 0:
                        realPrvPercent = (cell_data['lastValue'] / cell_data['lastPrevValue']) * 100
                    
                    pending = 0
                    if has_prev:
                        pending = cell_data['lastPrevValue'] - cell_data['lastValue']
                    
                    cell_data['comparative'] = {
                        'prvPtoPercent': prvPtoPercent,
                        'realPrvPercent': realPrvPercent,
                        'pending': pending
                    }
    
    def _process_kpi_cell_data(self, df, cat_col, subcat_col, project_col, prev_value_col, real_prev_percent_col, ppto_prev_percent_col, pending_value_col):
        """
        Procesa los datos de KPIs para preparar la estructura del cuadro de mando
        
        Args:
            df (pandas.DataFrame): DataFrame a procesar
            cat_col, subcat_col: Nombres de columnas obligatorias
            project_col, prev_value_col, real_prev_percent_col, ppto_prev_percent_col, pending_value_col: Nombres de columnas opcionales
        """
        # Agrupar por categoría y subcategoría
        group_cols = [cat_col, subcat_col]
        
        # Añadir proyecto si existe
        if project_col and project_col in df.columns:
            group_cols = [project_col] + group_cols
        
        # Preparar diccionario para agrupar por las columnas de KPIs disponibles
        agg_dict = {}
        
        if prev_value_col and prev_value_col in df.columns:
            agg_dict[prev_value_col] = 'sum'
        
        if real_prev_percent_col and real_prev_percent_col in df.columns:
            agg_dict[real_prev_percent_col] = 'mean'
        
        if ppto_prev_percent_col and ppto_prev_percent_col in df.columns:
            agg_dict[ppto_prev_percent_col] = 'mean'
        
        if pending_value_col and pending_value_col in df.columns:
            agg_dict[pending_value_col] = 'sum'
        
        # Si no hay columnas de KPIs, no procesar
        if not agg_dict:
            return
        
        # Agrupar con todas las columnas
        grouped = df.groupby(group_cols).agg(agg_dict).reset_index()
        
        # Procesar cada fila agrupada
        for _, row in grouped.iterrows():
            # Crear clave de celda
            if project_col and project_col in df.columns:
                cell_key = f"{row[project_col]}|{row[cat_col]}|{row[subcat_col]}"
            else:
                cell_key = f"{row[cat_col]}|{row[subcat_col]}"
            
            # Inicializar datos de celda si no existe
            if cell_key not in self.processed_data['cellData']:
                initial_data = {
                    'category': row[cat_col],
                    'subcategory': row[subcat_col]
                }
                
                if project_col and project_col in df.columns:
                    initial_data['projectId'] = row[project_col]
                    
                self.processed_data['cellData'][cell_key] = initial_data
            
            # Añadir valores de KPIs si existen
            if prev_value_col and prev_value_col in df.columns:
                self.processed_data['cellData'][cell_key]['prevValue'] = float(row[prev_value_col]) if not pd.isna(row[prev_value_col]) else 0
            
            if real_prev_percent_col and real_prev_percent_col in df.columns:
                self.processed_data['cellData'][cell_key]['realPrevPercent'] = float(row[real_prev_percent_col]) if not pd.isna(row[real_prev_percent_col]) else 0
            
            if ppto_prev_percent_col and ppto_prev_percent_col in df.columns:
                self.processed_data['cellData'][cell_key]['pptoPrevPercent'] = float(row[ppto_prev_percent_col]) if not pd.isna(row[ppto_prev_percent_col]) else 0
            
            if pending_value_col and pending_value_col in df.columns:
                self.processed_data['cellData'][cell_key]['pendingValue'] = float(row[pending_value_col]) if not pd.isna(row[pending_value_col]) else 0
    
    def _calculate_totals(self):
        """Calcula los totales por categoría y subcategoría"""
        # Crear diccionarios para almacenar totales
        cat_totals = {}
        subcat_totals = {}
        
        # Calcular totales basados en el valor absoluto del último valor
        for _, cell_data in self.processed_data['cellData'].items():
            category = cell_data['category']
            subcategory = cell_data['subcategory']
            
            # Para datos históricos, usar el último valor
            if not self.is_kpi_data and 'lastValue' in cell_data:
                last_value = abs(cell_data['lastValue'])
                
                # Acumular por categoría
                if category not in cat_totals:
                    cat_totals[category] = 0
                cat_totals[category] += last_value
                
                # Acumular por subcategoría
                if subcategory not in subcat_totals:
                    subcat_totals[subcategory] = 0
                subcat_totals[subcategory] += last_value
            
            # Para datos de KPIs, usar el valor de previsión si está disponible
            elif self.is_kpi_data and 'prevValue' in cell_data:
                prev_value = abs(cell_data['prevValue'])
                
                # Acumular por categoría
                if category not in cat_totals:
                    cat_totals[category] = 0
                cat_totals[category] += prev_value
                
                # Acumular por subcategoría
                if subcategory not in subcat_totals:
                    subcat_totals[subcategory] = 0
                subcat_totals[subcategory] += prev_value
        
        # Añadir totales a los datos procesados
        self.processed_data['categoryTotals'] = cat_totals
        self.processed_data['subcategoryTotals'] = subcat_totals
    
    def get_processed_data(self):
        """
        Devuelve los datos procesados
        
        Returns:
            dict: Datos procesados
        """
        return self.processed_data
    
    def to_json(self, pretty=True):
        """
        Convierte los datos procesados a formato JSON
        
        Args:
            pretty (bool): Si se formatea el JSON para legibilidad
            
        Returns:
            str: Datos en formato JSON
        """
        if pretty:
            return json.dumps(self.processed_data, indent=2)
        else:
            return json.dumps(self.processed_data)