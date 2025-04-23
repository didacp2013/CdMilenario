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
            has_kpis = data.get('hasKpis', False)
            
            html_content = html_content.replace('$HAS_PROJECTS', 'true' if has_projects else 'false')
            html_content = html_content.replace('$HAS_PPTO', 'true' if has_ppto else 'false')
            html_content = html_content.replace('$HAS_PREV', 'true' if has_prev else 'false')
            html_content = html_content.replace('$HAS_KPIS', 'true' if has_kpis else 'false')
            
            # Generar filas de muestra
            sample_rows = self._generate_sample_rows(data, has_projects, has_ppto, has_prev, has_kpis)
            html_content = html_content.replace('${SAMPLE_TABLE_ROWS}', sample_rows)
            
            return html_content
            
        except Exception as e:
            raise Exception(f"Error al generar HTML: {str(e)}")
    
    def _generate_sample_rows(self, data, has_projects, has_ppto, has_prev, has_kpis):
        """
        Genera filas de muestra para la tabla de información
        
        Args:
            data (dict): Datos procesados
            has_projects (bool): Si hay datos de proyectos
            has_ppto (bool): Si hay datos de presupuesto
            has_prev (bool): Si hay datos de previsión
            has_kpis (bool): Si hay datos de KPIs
            
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
            
            # KPIs si existen
            kpis = cell.get('kpis', {})
            prev_value = kpis.get('prevValue', 0)
            real_prev_percent = kpis.get('realPrevPercent', 0)
            ppto_prev_percent = kpis.get('pptoPrevPercent', 0)
            pending_value = kpis.get('pendingValue', 0)
            
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
            
            # Añadir valores de KPIs si existen
            if has_kpis:
                row += f'<td>{prev_value:,.2f}</td>'
                row += f'<td>{real_prev_percent:,.1f}%</td>'
                row += f'<td>{ppto_prev_percent:,.1f}%</td>'
                row += f'<td>{pending_value:,.2f}</td>'
            
            row += '</tr>'
            samples.append(row)
        
        return '\n'.join(samples)
    
    def generate(self, data):
        """
        Genera el HTML a partir de la plantilla y los datos
        
        Args:
            data (dict): Datos procesados para insertar en la plantilla
            
        Returns:
            str: Contenido HTML generado
        """
        with open(self.template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Reemplazar la fecha de generación
        generated_date = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        template_content = template_content.replace('{{GENERATED_DATE}}', generated_date)
        
        # Extraer proyectos y compañías directamente de los datos
        projects = set()
        companies = set()
        
        # Imprimir información de depuración sobre los datos
        print(f"Número total de celdas: {len(data.get('cellData', {}))}")
        
        # Extraer proyectos y compañías
        for key, cell in data.get('cellData', {}).items():
            if 'project' in cell and cell['project']:
                project = str(cell['project']).strip()
                if project:
                    projects.add(project)
                    print(f"Proyecto encontrado en HTML generator: '{project}' en celda {key}")
            
            if 'company' in cell and cell['company']:
                company = str(cell['company']).strip()
                if company:
                    companies.add(company)
                    print(f"Compañía encontrada en HTML generator: '{company}' en celda {key}")
        
        print(f"Total de proyectos encontrados: {len(projects)}")
        print(f"Total de compañías encontradas: {len(companies)}")
        
        # Generar opciones de filtro
        project_options = ""
        for project in sorted(projects):
            project_options += f'<option value="{project}">{project}</option>\n'
        
        company_options = ""
        for company in sorted(companies):
            company_options += f'<option value="{company}">{company}</option>\n'
        
        # Generar HTML para las celdas
        cells_html = self._generate_cells_html(data)
        
        # Preparar el JSON para cellData
        import json
        try:
            # Limpiar datos para serialización JSON
            clean_data = {}
            for key, cell in data.get('cellData', {}).items():
                clean_cell = {}
                for k, v in cell.items():
                    if isinstance(v, (dict, list, str, int, float, bool, type(None))):
                        clean_cell[k] = v
                    else:
                        clean_cell[k] = str(v)
                clean_data[key] = clean_cell
            
            cell_data_json = json.dumps(clean_data)
        except Exception as e:
            print(f"Error al serializar datos: {str(e)}")
            cell_data_json = "{}"
        
        # Crear script para inicializar datos
        data_script = f"""
        <script>
            // Datos para gráficos y filtros
            const cellData = {cell_data_json};
            console.log("Datos cargados:", Object.keys(cellData).length, "celdas");
        </script>
        """
        
        # Insertar el script antes del cierre del body
        template_content = template_content.replace('</body>', f'{data_script}\n</body>')
        
        # Reemplazar otras variables en la plantilla
        template_content = template_content.replace('{{PROJECT_OPTIONS}}', project_options)
        template_content = template_content.replace('{{COMPANY_OPTIONS}}', company_options)
        template_content = template_content.replace('{{CELLS}}', cells_html)
        
        # Reemplazar la declaración de cellData en el template
        template_content = template_content.replace('const cellData = {};', '// cellData ya definido')
        
        return template_content
    
    def _generate_cells_html(self, data):
        """
        Genera el HTML para las celdas del cuadro de mando
        
        Args:
            data (dict): Datos procesados
            
        Returns:
            str: HTML para las celdas
        """
        cell_data = data.get('cellData', {})
        if not cell_data:
            return "<div class='no-data'>No hay datos para mostrar</div>"
        
        # Obtener categorías y subcategorías ordenadas
        categories = sorted(data.get('categories', []))
        subcategories = sorted(data.get('subcategories', []))
        
        # Generar tabla HTML
        html = "<table class='dashboard-table'>\n"
        
        # Fila de encabezado con subcategorías
        html += "<tr>\n"
        html += "<th class='corner-header'></th>\n"  # Celda vacía en la esquina superior izquierda
        
        # Añadir encabezados de subcategorías (horizontalmente)
        for subcategory in subcategories:
            html += f"<th class='subcategory-header'>{subcategory}</th>\n"
        
        html += "</tr>\n"  # Fin de la fila de encabezado
        
        # Filas para cada categoría
        for category in categories:
            html += f"<tr class='category-row'>\n"
            html += f"<th class='category-header'>{category}</th>\n"  # Título de categoría como encabezado de fila
            
            # Celdas para cada subcategoría en esta categoría
            for subcategory in subcategories:
                # Buscar la celda correspondiente
                cell_key = f"{category}|{subcategory}"
                cell = cell_data.get(cell_key)
                
                # Si no se encuentra, crear una celda vacía
                if cell is None:
                    html += "<td class='empty-cell'></td>\n"
                else:
                    # Obtener proyecto y compañía para filtrado
                    project = str(cell.get('project', '')).strip()
                    company = str(cell.get('company', '')).strip()
                    
                    # Crear una celda con datos
                    html += f"<td class='data-cell' data-cell-id='{cell_key}' data-category='{category}' data-subcategory='{subcategory}' data-project='{project}' data-company='{company}'>\n"
                    
                    # Añadir valor principal si existe
                    if 'lastValue' in cell:
                        try:
                            value = float(cell['lastValue'])
                            value_class = 'positive' if value >= 0 else 'negative'
                            html += f"<div class='cell-value {value_class}'>{value:,.2f}</div>\n"
                        except (ValueError, TypeError):
                            html += "<div class='cell-value'>N/A</div>\n"
                    
                    # Añadir indicador de KPI si tiene datos de KPI
                    if cell.get('hasKpis'):
                        html += "<div class='kpi-indicator'>KPI</div>\n"
                    
                    # Añadir indicador de histórico si tiene serie temporal
                    if cell.get('timeSeries') and len(cell.get('timeSeries', [])) > 0:
                        html += "<div class='history-indicator'>HIST</div>\n"
                    
                    html += "</td>\n"  # Fin de la celda
                
            html += "</tr>\n"  # Fin de la fila
        
        html += "</table>\n"  # Fin de la tabla
        
        return html
    
    def _format_number(self, value):
        """
        Formatea un número para mostrar en el HTML
        
        Args:
            value (float): Valor a formatear
            
        Returns:
            str: Valor formateado
        """
        try:
            value = float(value)
            # Formatear con separador de miles y 2 decimales
            return f"{value:,.2f}".replace(",", " ").replace(".", ",")
        except (ValueError, TypeError):
            return "0,00"
    
    def _format_percent(self, value):
        """
        Formatea un porcentaje para mostrar en el HTML
        
        Args:
            value (float): Valor a formatear
            
        Returns:
            str: Valor formateado como porcentaje
        """
        try:
            value = float(value)
            # Formatear como porcentaje con 1 decimal
            return f"{value * 100:.1f}%".replace(".", ",")
        except (ValueError, TypeError):
            return "0,0%"
    
    def _generate_info_html(self, data):
        """
        Genera el HTML para la pestaña de información
        
        Args:
            data (dict): Datos procesados
            
        Returns:
            str: HTML para la pestaña de información
        """
        # Extraer información relevante
        categories = len(data.get('categories', []))
        subcategories = len(data.get('subcategories', []))
        periods = len(data.get('periods', []))
        cells = len(data.get('cellData', {}))
        
        # Generar HTML
        html = f"""
        <div class="info-container">
            <h3>Información del Cuadro de Mando</h3>
            <div class="info-item">
                <strong>Categorías:</strong> {categories}
            </div>
            <div class="info-item">
                <strong>Subcategorías:</strong> {subcategories}
            </div>
            <div class="info-item">
                <strong>Períodos:</strong> {periods}
            </div>
            <div class="info-item">
                <strong>Total de celdas:</strong> {cells}
            </div>
            <div class="info-item">
                <strong>Generado el:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            </div>
        </div>
        """
        
        return html
    
    def _remove_csv_export_code(self, template):
        """
        Elimina el código relacionado con la exportación CSV
        
        Args:
            template (str): Plantilla HTML
            
        Returns:
            str: Plantilla sin código de exportación CSV
        """
        # Buscar y eliminar la función de exportación CSV
        start_marker = "// Función para exportar a CSV"
        end_marker = "});"
        
        start_pos = template.find(start_marker)
        if start_pos != -1:
            # Buscar el final de la función
            end_pos = template.find(end_marker, start_pos)
            if end_pos != -1:
                end_pos += len(end_marker)
                template = template[:start_pos] + template[end_pos:]
        
        return template
    
    def _clean_template(self, template):
        """
        Limpia la plantilla de código basura o de depuración
        
        Args:
            template (str): Plantilla HTML
            
        Returns:
            str: Plantilla limpia
        """
        # Eliminar cualquier código JavaScript visible que parezca depuración
        lines = template.split('\n')
        cleaned_lines = []
        
        in_debug_section = False
        for line in lines:
            # Detectar inicio de sección de depuración
            if "// Escala para valores con un pequeño margen" in line or "chartStatus.textContent =" in line:
                in_debug_section = True
            
            # Si no estamos en una sección de depuración, mantener la línea
            if not in_debug_section:
                cleaned_lines.append(line)
            
            # Detectar fin de sección de depuración
            if in_debug_section and "});" in line:
                in_debug_section = False
        
        # Asegurarse de que solo hay un div con la clase dashboard-container
        template = '\n'.join(cleaned_lines)
        
        # Eliminar duplicados de elementos principales
        template = self._remove_duplicate_elements(template)
        
        return template
    
    def _remove_duplicate_elements(self, template):
        """
        Elimina elementos duplicados del HTML
        
        Args:
            template (str): Plantilla HTML
            
        Returns:
            str: Plantilla sin elementos duplicados
        """
        # Buscar y eliminar duplicados de elementos principales
        main_elements = [
            '<div class="dashboard-container">',
            '<div class="tabs">',
            '<div class="tab-content">'
        ]
        
        for element in main_elements:
            first_pos = template.find(element)
            if first_pos != -1:
                second_pos = template.find(element, first_pos + 1)
                if second_pos != -1:
                    # Encontrar el cierre del primer elemento
                    close_tag = '</div>'
                    close_pos = template.find(close_tag, second_pos)
                    if close_pos != -1:
                        close_pos += len(close_tag)
                        # Eliminar el segundo elemento y su contenido
                        template = template[:second_pos] + template[close_pos:]
        
        return template

class HtmlGenerator:
    def __init__(self, template_path):
        """
        Inicializa el generador de HTML
        
        Args:
            template_path (str): Ruta a la plantilla HTML
        """
        self.template_path = template_path
        with open(template_path, 'r', encoding='utf-8') as f:
            self.template = f.read()
    
    def generate(self, data):
        """
        Genera el HTML del cuadro de mando
        
        Args:
            data (dict): Datos procesados
            
        Returns:
            str: HTML generado
        """
        # Verificar que tenemos datos
        if not data or 'cellData' not in data:
            raise ValueError("No hay datos para generar el HTML")
        
        # Imprimir información sobre los datos que se van a utilizar
        print(f"Número total de celdas: {len(data['cellData'])}")
        print(f"Total de proyectos encontrados: {len(data.get('projects', []))}")
        print(f"Total de compañías encontradas: {len(data.get('companies', []))}")
        
        # Generar el HTML para las celdas
        cells_html = self._generate_cells_html(data)
        
        # Generar el HTML para los filtros
        filters_html = self._generate_filters_html(data)
        
        # Generar el HTML para la información adicional
        info_html = self._generate_info_html(data)
        
        # Reemplazar las variables en la plantilla
        html = self.template
        html = html.replace('{{DASHBOARD_TITLE}}', 'Cuadro de Mando Excel')
        html = html.replace('{{GENERATED_DATE}}', f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        html = html.replace('{{FILTERS}}', filters_html)
        html = html.replace('{{INFO}}', info_html)
        html = html.replace('{{CELLS}}', cells_html)
        
        return html
    
    def _generate_filters_html(self, data):
        """
        Genera el HTML para los filtros
        
        Args:
            data (dict): Datos procesados
            
        Returns:
            str: HTML de los filtros
        """
        filters_html = '<div class="filters-container">'
        
        # Filtro de categorías
        if 'categories' in data and data['categories']:
            filters_html += '''
            <div class="filter">
                <label for="category-filter">Categoría:</label>
                <select id="category-filter" onchange="filterDashboard()">
                    <option value="all">Todas</option>
            '''
            
            for category in data['categories']:
                filters_html += f'<option value="{category}">{category}</option>'
                
            filters_html += '''
                </select>
            </div>
            '''
        
        # Filtro de subcategorías
        if 'subcategories' in data and data['subcategories']:
            filters_html += '''
            <div class="filter">
                <label for="subcategory-filter">Subcategoría:</label>
                <select id="subcategory-filter" onchange="filterDashboard()">
                    <option value="all">Todas</option>
            '''
            
            for subcategory in data['subcategories']:
                filters_html += f'<option value="{subcategory}">{subcategory}</option>'
                
            filters_html += '''
                </select>
            </div>
            '''
        
        # Filtro de proyectos
        if 'projects' in data and data['projects'] and data.get('hasProjects', False):
            filters_html += '''
            <div class="filter">
                <label for="project-filter">Proyecto:</label>
                <select id="project-filter" onchange="filterDashboard()">
                    <option value="all">Todos</option>
            '''
            
            for project in data['projects']:
                filters_html += f'<option value="{project}">{project}</option>'
                
            filters_html += '''
                </select>
            </div>
            '''
        
        # Filtro de compañías
        if 'companies' in data and data['companies'] and data.get('hasCompanies', False):
            filters_html += '''
            <div class="filter">
                <label for="company-filter">Compañía:</label>
                <select id="company-filter" onchange="filterDashboard()">
                    <option value="all">Todas</option>
            '''
            
            for company in data['companies']:
                filters_html += f'<option value="{company}">{company}</option>'
                
            filters_html += '''
                </select>
            </div>
            '''
        
        filters_html += '</div>'
        return filters_html
    
    def _generate_info_html(self, data):
        """
        Genera el HTML para la información adicional
        
        Args:
            data (dict): Datos procesados
            
        Returns:
            str: HTML de la información
        """
        # Contar el número de celdas, proyectos y compañías
        num_cells = len(data.get('cellData', {}))
        num_projects = len(data.get('projects', []))
        num_companies = len(data.get('companies', []))
        
        # Contar celdas con datos históricos y KPIs
        historic_cells = sum(1 for cell in data.get('cellData', {}).values() if cell.get('source') == 'historic')
        kpi_cells = sum(1 for cell in data.get('cellData', {}).values() if cell.get('source') == 'kpi')
        combined_cells = sum(1 for cell in data.get('cellData', {}).values() 
                            if cell.get('source') == 'historic' and cell.get('hasKpiValues', False))
        
        info_html = f'''
        <div class="dashboard-info">
            <h3>Información del Cuadro de Mando</h3>
            <ul>
                <li>Total de celdas: {num_cells}</li>
                <li>Celdas con datos históricos: {historic_cells}</li>
                <li>Celdas solo con KPIs: {kpi_cells}</li>
                <li>Celdas con ambos tipos de datos: {combined_cells}</li>
                <li>Total de proyectos: {num_projects}</li>
                <li>Total de compañías: {num_companies}</li>
            </ul>
        </div>
        '''
        
        return info_html
    
    def _generate_cells_html(self, data):
        """
        Genera el HTML para las celdas del cuadro de mando
        
        Args:
            data (dict): Datos procesados
            
        Returns:
            str: HTML de las celdas
        """
        cells_html = ''
        
        # Ordenar las celdas por categoría y subcategoría
        sorted_cells = []
        for cell_key, cell_data in data['cellData'].items():
            category = cell_data.get('Category', '')
            subcategory = cell_data.get('Subcategory', '')
            sorted_cells.append((category, subcategory, cell_key, cell_data))
        
        sorted_cells.sort()
        
        # Generar el HTML para cada celda
        for category, subcategory, cell_key, cell_data in sorted_cells:
            # Extraer atributos para filtrado
            project = str(cell_data.get('PRJID', ''))
            company = str(cell_data.get('CIA', ''))
            
            # Determinar el tipo de celda
            cell_type = 'historic'
            if cell_data.get('source') == 'kpi':
                cell_type = 'kpi'
            elif cell_data.get('hasKpiValues', False):
                cell_type = 'combined'
            
            # Crear el div de la celda con atributos para filtrado
            cells_html += f'''
            <div class="dashboard-cell" 
                 data-category="{category}" 
                 data-subcategory="{subcategory}" 
                 data-project="{project}" 
                 data-company="{company}"
                 data-cell-type="{cell_type}">
                <div class="cell-header">
                    <h3>{category} - {subcategory}</h3>
                    <div class="cell-meta">
                        {f'<span class="project-tag">Proyecto: {project}</span>' if project else ''}
                        {f'<span class="company-tag">Compañía: {company}</span>' if company else ''}
                    </div>
                </div>
            '''
            
            # Añadir contenido según el tipo de celda
            if cell_type == 'historic' or cell_type == 'combined':
                # Añadir gráfico de series temporales si hay datos
                if 'timeSeries' in cell_data and cell_data['timeSeries']:
                    cells_html += f'''
                    <div class="chart-container">
                        <canvas id="chart-{cell_key}" class="time-series-chart"></canvas>
                        <script>
                            createTimeSeriesChart(
                                'chart-{cell_key}', 
                                {json.dumps([item.get('period', '') for item in cell_data['timeSeries']])}, 
                                {json.dumps([item.get('value', 0) for item in cell_data['timeSeries']])},
                                {json.dumps([item.get('source', '') for item in cell_data['timeSeries']])}
                            );
                        </script>
                    </div>
                    '''
            
            # Añadir datos de KPI si están disponibles
            if cell_type == 'kpi' or cell_type == 'combined':
                kpi_values = cell_data.get('kpiValues', {})  # Cambiado de 'kpis' a 'kpiValues'
                if kpi_values:
                    cells_html += '''
                    <div class="kpi-container">
                        <h4>Indicadores KPI</h4>
                        <table class="kpi-table">
                            <tr>
                                <th>Indicador</th>
                                <th>Valor</th>
                            </tr>
                    '''
                    
                    # Mostrar los valores de KPI
                    for kpi_name, kpi_value in kpi_values.items():
                        # Formatear el valor según su tipo
                        formatted_value = kpi_value
                        if isinstance(kpi_value, (int, float)):
                            if kpi_name.startswith('%'):
                                formatted_value = f"{kpi_value:.2f}%"
                            else:
                                formatted_value = f"{kpi_value:,.2f}"
                        
                        cells_html += f'''
                        <tr>
                            <td>{kpi_name}</td>
                            <td>{formatted_value}</td>
                        </tr>
                        '''
                    
                    cells_html += '''
                        </table>
                    </div>
                    '''
            
            cells_html += '</div>'
        
        return cells_html
