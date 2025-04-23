#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo para generar HTML a partir de los datos procesados
"""
import json
import os
from datetime import datetime
import random

class HtmlGenerator:
    """Clase para generar HTML a partir de datos procesados"""
    
    def __init__(self, template_path):
        """
        Inicializa el generador de HTML
        
        Args:
            template_path (str): Ruta al archivo de plantilla HTML
        """
        self.template_path = template_path
        
        # Comprobar si el archivo existe
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"La plantilla {template_path} no existe")
        
        # Cargar la plantilla
        with open(template_path, 'r', encoding='utf-8') as f:
            self.template = f.read()
    
    def generate(self, data):
        """
        Genera el HTML con los datos procesados
        
        Args:
            data (dict): Datos procesados
            
        Returns:
            str: Contenido HTML generado
        """
        try:
            # Crear una copia del template
            html_content = self.template
            
            # Obtener fecha actual
            current_date = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            
            # Reemplazar variables en el template
            html_content = html_content.replace('${TITLE}', 'Cuadro de Mando Excel')
            html_content = html_content.replace('${GENERATED_DATE}', current_date)
            html_content = html_content.replace('${DATA_JSON}', json.dumps(data))
            
            # Reemplazar variables de información
            html_content = html_content.replace('${CATEGORY_COUNT}', str(len(data.get('categories', []))))
            html_content = html_content.replace('${SUBCATEGORY_COUNT}', str(len(data.get('subcategories', []))))
            html_content = html_content.replace('${PERIOD_COUNT}', str(len(data.get('periods', []))))
            
            # Configurar variables condicionales
            has_projects = data.get('hasProjects', False)
            has_ppto = data.get('hasPpto', False)
            has_prev = data.get('hasPrev', False)
            
            html_content = html_content.replace('$HAS_PROJECTS', 'true' if has_projects else 'false')
            html_content = html_content.replace('$HAS_PPTO', 'true' if has_ppto else 'false')
            html_content = html_content.replace('$HAS_PREV', 'true' if has_prev else 'false')
            
            # Generar filas de muestra
            sample_rows = self._generate_sample_rows(data, has_projects, has_ppto, has_prev)
            html_content = html_content.replace('${SAMPLE_TABLE_ROWS}', sample_rows)
            
            return html_content
            
        except Exception as e:
            raise Exception(f"Error al generar HTML: {str(e)}")
    
    def _generate_sample_rows(self, data, has_projects, has_ppto, has_prev):
        """
        Genera filas de muestra para la tabla de información
        
        Args:
            data (dict): Datos procesados
            has_projects (bool): Si hay datos de proyectos
            has_ppto (bool): Si hay datos de presupuesto
            has_prev (bool): Si hay datos de previsión
            
        Returns:
            str: HTML con las filas de muestra
        """
        # Obtener datos de celda
        cell_data = data.get('cellData', {})
        
        # Si no hay datos, crear una fila de muestra
        if not cell_data:
            return '<tr><td colspan="4">No hay datos disponibles</td></tr>'
        
        # Tomar hasta 5 muestras aleatorias
        samples = []
        sample_keys = random.sample(list(cell_data.keys()), min(5, len(cell_data)))
        
        for key in sample_keys:
            cell = cell_data[key]
            
            # Obtener valores de la celda
            category = cell.get('category', '')
            subcategory = cell.get('subcategory', '')
            project_id = cell.get('projectId', '')
            
            # Obtener último valor o primer período si existe
            last_value = cell.get('lastValue', 0)
            
            # Valores comparativos
            comparative = cell.get('comparative', {})
            prv_pto = comparative.get('prvPtoPercent', 0)
            real_prv = comparative.get('realPrvPercent', 0)
            pending = comparative.get('pending', 0)
            
            # Generar HTML para la fila
            row = '<tr>'
            
            # Añadir proyecto si aplica
            if has_projects:
                row += f'<td>{project_id}</td>'
            
            # Añadir categoría y subcategoría
            row += f'<td>{category}</td>'
            row += f'<td>{subcategory}</td>'
            
            # Añadir valor
            row += f'<td>{last_value:,.2f}</td>'
            
            # Añadir valores comparativos si aplican
            if has_ppto and has_prev:
                row += f'<td>{prv_pto:,.1f}%</td>'
                row += f'<td>{real_prv:,.1f}%</td>'
                row += f'<td>{pending:,.2f}</td>'
            
            row += '</tr>'
            samples.append(row)
        
        return '\n'.join(samples)