#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Aplicación para generar un cuadro de mando a partir de datos en Excel
"""
import argparse
import os
import sys
import webbrowser
from pathlib import Path
from datetime import datetime  # Añadir esta importación
import json  # Añadir importación de json

# Importar los módulos de nuestra aplicación
from excel_extractor import ExcelDataExtractor
from data_processor_full import DataProcessor
# Import HtmlGenerator class from the local module
from html_generator_full import HtmlGenerator as ExternalHtmlGenerator

# Configuración predeterminada específica para tu proyecto
DEFAULT_EXCEL_PATH = "/Users/didac/Downloads/StoryMac/DashBTracker/PruebasCdM/Tchart_V06.xlsm"
DEFAULT_HISTORIC_SHEET = "FrmBB_2"  # Actualizado para usar la hoja correcta
DEFAULT_KPI_SHEET = "FrmBB_3"       # Actualizado para usar la hoja correcta
DEFAULT_OUTPUT_HTML = "dashboard_output.html"
DEFAULT_TEMPLATE = "dashboard_template_fixed.html"  # Usar la nueva plantilla

# Move the LocalHtmlGenerator class definition here, before it's used
class LocalHtmlGenerator:
    def __init__(self, template_path):
        self.template_path = template_path
        
    def generate(self, data):
        # Leer la plantilla
        with open(self.template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Extraer compañías y proyectos únicos de los datos
        unique_companies = set()
        unique_projects = set()
        unique_categories = set()
        
        # Actualizar la extracción de compañías, proyectos y categorías
        for cell_key, cell_data in data['cellData'].items():
            if 'CIA' in cell_data and cell_data['CIA']:
                unique_companies.add(cell_data['CIA'])
            if 'PRJID' in cell_data and cell_data['PRJID']:
                unique_projects.add(cell_data['PRJID'])
            if 'ROW' in cell_data and cell_data['ROW']:
                unique_categories.add(cell_data['ROW'])
        
        # Convertir a listas ordenadas
        unique_companies = sorted(list(unique_companies))
        unique_projects = sorted(list(unique_projects))
        unique_categories = sorted(list(unique_categories))
        
        print(f"Compañías únicas encontradas: {len(unique_companies)}")
        print(f"Proyectos únicos encontrados: {len(unique_projects)}")
        print(f"Categorías únicas encontradas: {len(unique_categories)}")
        
        # Crear un mapa de proyectos por compañía para usar en JavaScript
        company_projects_map = {}
        for cell_key, cell_data in data['cellData'].items():
            company = cell_data.get('CIA', '')
            project = cell_data.get('PRJID', '')
            if company and project:
                if company not in company_projects_map:
                    company_projects_map[company] = []
                if project not in company_projects_map[company]:
                    company_projects_map[company].append(project)
        
        # Ordenar los proyectos de cada compañía
        for company in company_projects_map:
            company_projects_map[company].sort()
        
        # Añadir filtro de categorías
        filters_html = '''
        <div class="filter-container">
            <div class="filter-row">
                <div class="filter-group">
                    <label for="companySelect">Compañía:</label>
                    <select id="companySelect" class="form-control">
        '''
        
        # Añadir opciones de compañía
        for company in unique_companies:
            filters_html += f'<option value="{company}">{company}</option>\n'
        
        filters_html += '''
                    </select>
                </div>
                <div class="filter-group">
                    <label for="projectSelect">Proyecto:</label>
                    <select id="projectSelect" class="form-control">
                        <!-- Se llenará dinámicamente -->
                    </select>
                </div>
            </div>
            <div class="filter-row">
                <div class="filter-group">
                    <label for="categoryFilter">Categoría:</label>
                    <select id="categoryFilter" class="form-control">
                        <option value="all">Todas las categorías</option>
        '''
        
        # Añadir opciones de categoría
        for category in unique_categories:
            filters_html += f'<option value="{category}">{category}</option>\n'
        
        filters_html += '''
                    </select>
                </div>
                <div class="btn-group" role="group">
                    <button id="viewKpis" class="btn btn-primary">Ver KPIs</button>
                    <button id="viewHistoric" class="btn btn-secondary">Ver Histórico</button>
                </div>
            </div>
            <div class="filter-row">
                <div class="filter-actions">
                    <button id="applyFilters" class="btn btn-success">Aplicar Filtros</button>
                    <button id="resetFilters" class="btn btn-outline-secondary">Restablecer</button>
                </div>
            </div>
        </div>
        
        <script>
        // Mapa de proyectos por compañía
        const companyProjectsMap = ''' + json.dumps(company_projects_map) + ''';
        
        document.addEventListener('DOMContentLoaded', function() {
            // Referencias a elementos del DOM
            const companySelect = document.getElementById('companySelect');
            const projectSelect = document.getElementById('projectSelect');
            const categoryFilter = document.getElementById('categoryFilter');
            const viewKpisBtn = document.getElementById('viewKpis');
            const viewHistoricBtn = document.getElementById('viewHistoric');
            const applyFiltersBtn = document.getElementById('applyFilters');
            const resetFiltersBtn = document.getElementById('resetFilters');
            const cells = document.querySelectorAll('.dashboard-cell');
            
            // Estado actual de visualización
            let currentView = 'kpi'; // 'kpi' o 'historic'
            
            // Función para actualizar los proyectos según la compañía seleccionada
            function updateProjects() {
                const selectedCompany = companySelect.value;
                
                // Limpiar opciones actuales
                projectSelect.innerHTML = '';
                
                // Añadir proyectos para la compañía seleccionada
                if (selectedCompany && companyProjectsMap[selectedCompany]) {
                    companyProjectsMap[selectedCompany].forEach(project => {
                        const option = document.createElement('option');
                        option.value = project;
                        option.textContent = project;
                        projectSelect.appendChild(option);
                    });
                }
            }
            
            // Función para aplicar filtros
            function applyFilters() {
                const selectedCompany = companySelect.value;
                const selectedProject = projectSelect.value;
                const selectedCategory = categoryFilter.value;
                
                if (!selectedCompany || !selectedProject) {
                    alert('Por favor, seleccione compañía y proyecto');
                    return;
                }
                
                // Ocultar todas las celdas primero
                cells.forEach(cell => {
                    cell.style.display = 'none';
                });
                
                // Mostrar solo las celdas que coinciden con los filtros
                cells.forEach(cell => {
                    const cellCompany = cell.getAttribute('data-company');
                    const cellProject = cell.getAttribute('data-project');
                    const cellCategory = cell.getAttribute('data-category');
                    const cellType = cell.getAttribute('data-cell-type');
                    
                    // Verificar si la celda coincide con los filtros
                    const categoryMatch = selectedCategory === 'all' || cellCategory === selectedCategory;
                    
                    if (cellCompany === selectedCompany && cellProject === selectedProject && categoryMatch) {
                        // Verificar el tipo de visualización
                        if (currentView === 'kpi' && (cellType === 'kpi' || cellType === 'both')) {
                            cell.style.display = 'block';
                            // Mostrar contenido KPI, ocultar gráfico
                            const kpiContent = cell.querySelector('.kpi-content');
                            const chartContainer = cell.querySelector('.chart-container');
                            
                            if (kpiContent) kpiContent.style.display = 'block';
                            if (chartContainer) chartContainer.style.display = 'none';
                        } 
                        else if (currentView === 'historic' && (cellType === 'historic' || cellType === 'both')) {
                            cell.style.display = 'block';
                            // Mostrar gráfico, ocultar contenido KPI
                            const kpiContent = cell.querySelector('.kpi-content');
                            const chartContainer = cell.querySelector('.chart-container');
                            
                            if (kpiContent) kpiContent.style.display = 'none';
                            if (chartContainer) chartContainer.style.display = 'block';
                        }
                    }
                });
                
                // Actualizar contador de celdas visibles
                updateVisibleCellsCount();
            }
            
            // Función para actualizar el contador de celdas visibles
            function updateVisibleCellsCount() {
                const visibleCells = document.querySelectorAll('.dashboard-cell[style*="display: block"]').length;
                const infoElement = document.getElementById('dashboard-info');
                if (infoElement) {
                    infoElement.textContent = `Mostrando ${visibleCells} elementos`;
                }
            }
            
            // Cambiar a vista de KPIs
            viewKpisBtn.addEventListener('click', function() {
                currentView = 'kpi';
                viewKpisBtn.classList.add('btn-primary');
                viewKpisBtn.classList.remove('btn-secondary');
                viewHistoricBtn.classList.add('btn-secondary');
                viewHistoricBtn.classList.remove('btn-primary');
                applyFilters();
            });
            
            // Cambiar a vista histórica
            viewHistoricBtn.addEventListener('click', function() {
                currentView = 'historic';
                viewHistoricBtn.classList.add('btn-primary');
                viewHistoricBtn.classList.remove('btn-secondary');
                viewKpisBtn.classList.add('btn-secondary');
                viewKpisBtn.classList.remove('btn-primary');
                applyFilters();
            });
            
            // Aplicar filtros al hacer clic en el botón
            applyFiltersBtn.addEventListener('click', applyFilters);
            
            // Restablecer filtros
            resetFiltersBtn.addEventListener('click', function() {
                if (companySelect.options.length > 0) {
                    companySelect.selectedIndex = 0;
                    categoryFilter.selectedIndex = 0;
                    updateProjects();
                    applyFilters();
                }
            });
            
            // Actualizar proyectos cuando cambia la compañía
            companySelect.addEventListener('change', updateProjects);
            
            // Inicializar los proyectos para la primera compañía
            if (companySelect.options.length > 0) {
                updateProjects();
                applyFilters();
            }
            
            // Permitir expandir gráficos con doble clic
            cells.forEach(cell => {
                cell.addEventListener('dblclick', function() {
                    // Solo expandir si estamos en vista histórica y la celda tiene datos históricos
                    if (currentView === 'historic' && 
                        (cell.getAttribute('data-cell-type') === 'historic' || 
                         cell.getAttribute('data-cell-type') === 'both')) {
                        
                        // Verificar si ya está expandido
                        const isExpanded = cell.classList.contains('expanded');
                        
                        // Restablecer todas las celdas
                        cells.forEach(c => {
                            c.classList.remove('expanded');
                            c.style.flex = '';
                        });
                        
                        if (!isExpanded) {
                            // Expandir esta celda
                            cell.classList.add('expanded');
                            cell.style.flex = '0 0 100%';
                            
                            // Redimensionar el gráfico para que se vea mejor
                            const chartContainer = cell.querySelector('.chart-container');
                            if (chartContainer) {
                                chartContainer.style.height = '400px';
                                
                                // Forzar redimensionamiento del gráfico
                                const chartId = chartContainer.querySelector('canvas').id;
                                const chart = Chart.getChart(chartId);
                                if (chart) {
                                    chart.resize();
                                }
                            }
                        }
                    }
                });
            });
        });
        </script>
        '''
        
        template_content = template_content.replace('{{FILTERS}}', filters_html)
        
        # Añadir CSS mejorado para el dashboard
        css_styles = '''
        <style>
        /* Estilos generales */
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }
        
        h1 {
            margin-bottom: 5px;
        }
        
        /* Estilos para los filtros */
        .filter-container {
            background-color: #fff;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .filter-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
        }
        
        .filter-group {
            flex: 1;
            margin-right: 15px;
        }
        
        .filter-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        
        .form-control {
            width: 100%;
            padding: 8px;
            border: 1px solid #ced4da;
            border-radius: 4px;
        }
        
        .filter-actions {
            display: flex;
            align-items: flex-end;
        }
        
        .btn {
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            border: none;
            margin-left: 10px;
        }
        
        .btn-primary {
            background-color: #007bff;
            color: white;
        }
        
        .btn-secondary {
            background-color: #6c757d;
            color: white;
        }
        
        .btn-success {
            background-color: #28a745;
            color: white;
        }
        
        .btn-outline-secondary {
            background-color: transparent;
            border: 1px solid #6c757d;
            color: #6c757d;
        }
        
        /* Estilos para el dashboard */
        .dashboard-container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .dashboard-cell {
            flex: 0 0 calc(33.333% - 20px);
            background-color: #fff;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: none; /* Oculto por defecto, se mostrará con JS */
            transition: all 0.3s ease;
        }
        
        .dashboard-cell.expanded {
            flex: 0 0 100%;
        }
        
        .cell-header {
            font-weight: bold;
            padding-bottom: 10px;
            margin-bottom: 15px;
            border-bottom: 1px solid #e9ecef;
        }
        
        .kpi-content {
            display: flex;
            flex-direction: column;
        }
        
        .cell-value {
            font-size: 28px;
            font-weight: bold;
            text-align: center;
            margin: 15px 0;
            color: #007bff;
        }
        
        .cell-kpis {
            display: flex;
            flex-wrap: wrap;
        }
        
        .kpi-item {
            flex: 0 0 50%;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
        }
        
        .kpi-label {
            font-weight: bold;
            color: #495057;
        }
        
        .chart-container {
            height: 250px;
            margin-top: 15px;
            transition: height 0.3s ease;
        }
        
        /* Leyenda */
        .legend {
            display: flex;
            flex-wrap: wrap;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            margin-right: 20px;
            margin-bottom: 10px;
        }
        
        .legend-color {
            width: 16px;
            height: 16px;
            margin-right: 8px;
            border-radius: 3px;
        }
        
        .positive {
            background-color: #28a745;
        }
        
        .negative {
            background-color: #dc3545;
        }
        
        /* Información del dashboard */
        .dashboard-info {
            background-color: #fff;
            border-radius: 8px;
            padding: 10px 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        @media (max-width: 992px) {
            .dashboard-cell {
                flex: 0 0 calc(50% - 20px);
            }
        }
        
        @media (max-width: 768px) {
            .dashboard-cell {
                flex: 0 0 100%;
            }
            
            .filter-row {
                flex-direction: column;
            }
            
            .filter-group {
                margin-right: 0;
                margin-bottom: 15px;
            }
            
            .legend {
                flex-direction: column;
            }
            
            .legend-item {
                margin-bottom: 8px;
            }
        }
        </style>
        '''
        
        # Insertar el CSS antes del cierre de </head>
        head_close_pos = template_content.find('</head>')
        if head_close_pos != -1:
            template_content = template_content[:head_close_pos] + css_styles + template_content[head_close_pos:]
        
        # Añadir información del dashboard
        info_html = '''
        <div class="dashboard-info">
            <div id="dashboard-info">Mostrando 0 elementos</div>
            <div>Doble clic en un gráfico para expandirlo</div>
        </div>
        '''
        
        # Generar las celdas del dashboard
        dashboard_cells = '<div class="dashboard-container">\n'
        
        for cell_key, cell_data in data['cellData'].items():
            # Determinar el tipo de celda
            cell_type = "unknown"
            if cell_data['hasHistoric'] and cell_data['hasKpi']:
                cell_type = "both"
            elif cell_data['hasHistoric']:
                cell_type = "historic"
            elif cell_data['hasKpi']:
                cell_type = "kpi"
            
            # Generar HTML para la celda
            cell_html = f'''
            <div class="dashboard-cell" 
                 data-category="{cell_data['ROW']}" 
                 data-subcategory="{cell_data['COLUMN']}" 
                 data-project="{cell_data['PRJID']}" 
                 data-company="{cell_data['CIA']}"
                 data-cell-type="{cell_type}">
                <div class="cell-header">{cell_data['ROW']} - {cell_data['COLUMN']}</div>
            '''
            
            # Añadir contenido KPI si existe
            if cell_data['hasKpi']:
                kpi_values = cell_data.get('kpiValues', {})
                real_prev = kpi_values.get('REALPREV', 0)
                
                # Determinar si es positivo o negativo para el color
                value_class = "positive" if real_prev < 0 else "negative"
                
                cell_html += f'''
                <div class="kpi-content">
                    <div class="cell-value {value_class}">{real_prev:,.2f}</div>
                    <div class="cell-kpis">
                        <div class="kpi-item">
                            <span class="kpi-label">KPREV:</span>
                            <span class="kpi-value">{kpi_values.get('KPREV', 0):,.2f}</span>
                        </div>
                        <div class="kpi-item">
                            <span class="kpi-label">PPTOPREV:</span>
                            <span class="kpi-value">{kpi_values.get('PPTOPREV', 0):,.2f}</span>
                        </div>
                        <div class="kpi-item">
                            <span class="kpi-label">PDTE:</span>
                            <span class="kpi-value">{kpi_values.get('PDTE', 0):,.2f}</span>
                        </div>
                    </div>
                </div>
                '''
            
            # Añadir gráfico si hay datos históricos
            if cell_data['hasHistoric'] and 'timeSeries' in cell_data and cell_data['timeSeries']:
                chart_id = f"chart_{cell_data['CIA']}_{cell_data['PRJID']}_{cell_data['ROW']}_{cell_data['COLUMN']}".replace(" ", "_").replace(":", "_")
                
                # Preparar datos para el gráfico
                periods = [point.get('period', '') for point in cell_data['timeSeries']]
                real_values = [point.get('REAL', 0) for point in cell_data['timeSeries']]
                ppto_values = [point.get('PPTO', 0) for point in cell_data['timeSeries']]
                hprev_values = [point.get('HPREV', 0) for point in cell_data['timeSeries']]
                
                cell_html += f'''
                <div class="chart-container" style="display: none;">
                    <canvas id="{chart_id}"></canvas>
                </div>
                <script>
                    document.addEventListener('DOMContentLoaded', function() {{
                        const ctx = document.getElementById('{chart_id}').getContext('2d');
                        
                        // Formatear etiquetas de período
                        const labels = {json.dumps(periods)}.map(period => {{
                            if (!period) return '';
                            const match = period.match(/^(\\d{{4}})\\.(\\d{{2}})$/);
                            if (match) {{
                                return `S${{match[2]}}-${{match[1]}}`;
                            }}
                            return period;
                        }});
                        
                        new Chart(ctx, {{
                            type: 'line',
                            data: {{
                                labels: labels,
                                datasets: [
                                    {{
                                        label: 'REAL',
                                        data: {json.dumps(real_values)},
                                        borderColor: 'rgba(75, 192, 192, 1)',
                                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                                        tension: 0.1
                                    }},
                                    {{
                                        label: 'PPTO',
                                        data: {json.dumps(ppto_values)},
                                        borderColor: 'rgba(255, 159, 64, 1)',
                                        backgroundColor: 'rgba(255, 159, 64, 0.2)',
                                        tension: 0.1
                                    }},
                                    {{
                                        label: 'HPREV',
                                        data: {json.dumps(hprev_values)},
                                        borderColor: 'rgba(54, 162, 235, 1)',
                                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                                        tension: 0.1
                                    }}
                                ]
                            }},
                            options: {{
                                responsive: true,
                                maintainAspectRatio: false,
                                scales: {{
                                    y: {{
                                        beginAtZero: false
                                    }}
                                }}
                            }}
                        }});
                    }});
                </script>
                '''
            
            cell_html += '</div>'
            dashboard_cells += cell_html
        
        dashboard_cells += '</div>'
        
        # Añadir leyenda para los valores
        legend_html = '''
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color positive"></div>
                <span>Valores positivos: Costes/Gastos</span>
            </div>
            <div class="legend-item">
                <div class="legend-color negative"></div>
                <span>Valores negativos: Ingresos/Ahorros</span>
            </div>
            <div class="legend-item">
                <span>Doble clic para ver gráfico histórico completo</span>
            </div>
        </div>
        '''
        
        # Reemplazar el marcador de posición de las celdas
        template_content = template_content.replace('{{CELLS}}', legend_html + dashboard_cells)
        
        # Reemplazar cualquier otro marcador de posición que pueda quedar
        template_content = template_content.replace('{{INFO}}', '')
        
        return template_content

# Después de la clase LocalHtmlGenerator y antes de if __name__ == "__main__":

def main():
    """Función principal de la aplicación"""
    parser = argparse.ArgumentParser(description='Genera un cuadro de mando a partir de un archivo Excel')
    parser.add_argument('--excel', '-e', default=DEFAULT_EXCEL_PATH, 
                      help=f'Ruta al archivo Excel (por defecto: {DEFAULT_EXCEL_PATH})')
    parser.add_argument('--historic', '-i', default=DEFAULT_HISTORIC_SHEET, 
                      help=f'Nombre de la hoja con datos históricos (por defecto: {DEFAULT_HISTORIC_SHEET})')
    parser.add_argument('--kpi', '-k', default=DEFAULT_KPI_SHEET, 
                      help=f'Nombre de la hoja con datos de KPIs (por defecto: {DEFAULT_KPI_SHEET})')
    parser.add_argument('--template', '-t', default=DEFAULT_TEMPLATE, 
                      help=f'Plantilla HTML a utilizar (por defecto: {DEFAULT_TEMPLATE})')
    parser.add_argument('--output', '-o', default=DEFAULT_OUTPUT_HTML,
                      help=f'Nombre del archivo HTML de salida (por defecto: {DEFAULT_OUTPUT_HTML})')
    parser.add_argument('--open', '-b', action='store_true', help='Abrir el cuadro de mando en el navegador')
    
    args = parser.parse_args()
    
    # Verificar que el archivo Excel existe
    if not os.path.exists(args.excel):
        print(f"Error: El archivo {args.excel} no existe.")
        sys.exit(1)
    
    # Verificar que la plantilla HTML existe
    template_path = args.template
    if not os.path.exists(template_path):
        # Buscar en el directorio de la aplicación
        app_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(app_dir, args.template)
        if not os.path.exists(template_path):
            print(f"Error: La plantilla HTML {args.template} no existe.")
            sys.exit(1)
    
    try:
        # Extraer datos históricos del Excel
        print(f"Extrayendo datos históricos de {args.excel}, hoja: {args.historic}...")
        excel_extractor = ExcelDataExtractor(args.excel)
        historic_data = excel_extractor.extract_data(args.historic)
        
        # Extraer datos de KPIs del Excel
        print(f"Extrayendo datos de KPIs de {args.excel}, hoja: {args.kpi}...")
        kpi_data = excel_extractor.extract_data(args.kpi)
        
        # Procesar los datos históricos
        print("Procesando datos históricos...")
        historic_processor = DataProcessor(historic_data)
        historic_processed = historic_processor.process()
        
        # Procesar los datos de KPIs
        print("Procesando datos de KPIs...")
        kpi_processor = DataProcessor(kpi_data, is_kpi_data=True)
        kpi_processed = kpi_processor.process()
        
        # Combinar los datos procesados
        print("Combinando datos históricos y KPIs...")
        combined_data = combine_data(historic_processed, kpi_processed)
        
        # Generar el HTML
        print(f"Generando HTML utilizando la plantilla {template_path}...")
        generator = LocalHtmlGenerator(template_path)
        html_content = generator.generate(combined_data)
        
        # Verificar que el HTML generado no contiene duplicados o código basura
        if html_content.count('<div class="dashboard-container">') > 1:
            print("Advertencia: Se detectaron elementos duplicados en el HTML generado. Limpiando...")
            # Limpiar manualmente si es necesario
            first_container = html_content.find('<div class="dashboard-container">')
            if first_container != -1:
                second_container = html_content.find('<div class="dashboard-container">', first_container + 1)
                if second_container != -1:
                    # Encontrar el final del documento
                    end_html = html_content.find('</html>')
                    if end_html != -1:
                        html_content = html_content[:second_container] + html_content[end_html:]
                    else:
                        html_content = html_content[:second_container] + "</div></body></html>"
        
        # Verificar y reemplazar variables de plantilla no sustituidas
        placeholders = ['${TITLE}', '${GENERATED_DATE}', '{{DASHBOARD_TITLE}}', '{{GENERATED_DATE}}', '{{FILTERS}}', '{{INFO}}', '{{CELLS}}']
        for placeholder in placeholders:
            if placeholder in html_content:
                print(f"Advertencia: La variable de plantilla {placeholder} no fue reemplazada.")
                if placeholder == '${TITLE}' or placeholder == '{{DASHBOARD_TITLE}}':
                    html_content = html_content.replace(placeholder, 'Cuadro de Mando Excel')
                elif placeholder == '${GENERATED_DATE}' or placeholder == '{{GENERATED_DATE}}':
                    html_content = html_content.replace(placeholder, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
                else:
                    html_content = html_content.replace(placeholder, '')
        
        # Guardar el HTML generado
        output_path = args.output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Cuadro de mando generado correctamente: {output_path}")
        
        # Abrir en el navegador si se solicitó
        if args.open:
            # Convertir a ruta absoluta
            abs_path = os.path.abspath(output_path)
            url = f"file://{abs_path}"
            print(f"Abriendo en el navegador: {url}")
            webbrowser.open(url)
        
        return 0  # Éxito
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Verificar si se generó algún resultado parcial
        if 'combined_data' in locals() and combined_data and 'cellData' in combined_data and combined_data['cellData']:
            print(f"\nSe encontraron {len(combined_data['cellData'])} celdas de datos combinados.")
            print("A pesar del error, se intentará generar un resultado parcial.")
            
            try:
                # Intentar generar HTML con los datos parciales
                generator = LocalHtmlGenerator(template_path)
                html_content = generator.generate(combined_data)
                
                # Guardar el HTML generado
                output_path = args.output
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                print(f"Se ha generado un resultado parcial en: {output_path}")
                
                # Abrir en el navegador si se solicitó
                if args.open:
                    abs_path = os.path.abspath(output_path)
                    url = f"file://{abs_path}"
                    print(f"Abriendo resultado parcial en el navegador: {url}")
                    webbrowser.open(url)
                
                return 2  # Éxito parcial
            except Exception as inner_e:
                print(f"No se pudo generar un resultado parcial: {str(inner_e)}")
        
        return 1  # Error

def combine_data(historic_data, kpi_data):
    """
    Combina los datos históricos y los datos de KPIs manteniendo su independencia
    
    Args:
        historic_data (dict): Datos históricos procesados
        kpi_data (dict): Datos de KPIs procesados
        
    Returns:
        dict: Datos combinados
    """
    # Crear una estructura de datos combinada
    combined = {
        'categories': historic_data.get('categories', []),
        'subcategories': [],  # Se llenará con las subcategorías estáticas
        'cellData': {},
        'hasKpis': True,
        'historicData': historic_data.get('cellData', {}),
        'kpiData': kpi_data.get('cellData', {})
    }
    
    # Organizar los datos por compañía, proyecto, categoría y subcategoría
    data_by_hierarchy = {}
    
    # Procesar primero los datos históricos
    for historic_key, historic_cell in historic_data.get('cellData', {}).items():
        # Usar los nombres correctos para la jerarquía
        company = historic_cell.get('CIA', '')
        project = historic_cell.get('PRJID', '')
        category = historic_cell.get('ROW', '')
        subcategory = historic_cell.get('COLUMN', '')
        
        # Ignorar entradas sin compañía o proyecto específico
        if not company or not project:
            continue
        
        # Crear la estructura jerárquica si no existe
        if company not in data_by_hierarchy:
            data_by_hierarchy[company] = {}
        if project not in data_by_hierarchy[company]:
            data_by_hierarchy[company][project] = {}
        if category not in data_by_hierarchy[company][project]:
            data_by_hierarchy[company][project][category] = {}
        
        # Guardar datos históricos
        if subcategory in data_by_hierarchy[company][project][category]:
            # Actualizar celda existente con datos históricos
            data_by_hierarchy[company][project][category][subcategory]['historic'] = historic_cell
            data_by_hierarchy[company][project][category][subcategory]['historicKey'] = historic_key
        else:
            # Crear nueva celda solo con datos históricos
            data_by_hierarchy[company][project][category][subcategory] = {
                'historic': historic_cell,
                'kpi': None,
                'historicKey': historic_key,
                'kpiKey': None
            }
    
    # Luego procesar los datos KPI
    for kpi_key, kpi_cell in kpi_data.get('cellData', {}).items():
        # Usar los nombres correctos para la jerarquía
        company = kpi_cell.get('CIA', '')
        project = kpi_cell.get('PRJID', '')
        category = kpi_cell.get('ROW', '')
        subcategory = kpi_cell.get('COLUMN', '')
        
        # Ignorar entradas sin compañía o proyecto específico
        if not company or not project:
            continue
        
        # Crear la estructura jerárquica si no existe
        if company not in data_by_hierarchy:
            data_by_hierarchy[company] = {}
        if project not in data_by_hierarchy[company]:
            data_by_hierarchy[company][project] = {}
        if category not in data_by_hierarchy[company][project]:
            data_by_hierarchy[company][project][category] = {}
        
        # Guardar o actualizar datos KPI
        if subcategory in data_by_hierarchy[company][project][category]:
            # Actualizar celda existente con datos KPI
            data_by_hierarchy[company][project][category][subcategory]['kpi'] = kpi_cell
            data_by_hierarchy[company][project][category][subcategory]['kpiKey'] = kpi_key
        else:
            # Crear nueva celda solo con datos KPI
            data_by_hierarchy[company][project][category][subcategory] = {
                'historic': None,
                'kpi': kpi_cell,
                'historicKey': None,
                'kpiKey': kpi_key
            }
    
    # Crear estructura plana para el frontend
    for company, projects in data_by_hierarchy.items():
        for project, categories in projects.items():
            for category, subcategories in categories.items():
                for subcategory, data in subcategories.items():
                    # Crear clave única para esta celda
                    cell_key = f"{company}|{project}|{category}|{subcategory}"
                    
                    # Crear celda con datos combinados - usando los nombres correctos para la jerarquía
                    cell_data = {
                        'CIA': company,
                        'PRJID': project,
                        'ROW': category,
                        'COLUMN': subcategory,
                        'hasHistoric': data['historic'] is not None,
                        'hasKpi': data['kpi'] is not None,
                        'historicKey': data['historicKey'],
                        'kpiKey': data['kpiKey']
                    }
                    
                    # Añadir datos históricos si existen
                    if data['historic']:
                        # Usar directamente la serie temporal de los datos históricos si existe
                        if 'timeSeries' in data['historic']:
                            # Mantener los nombres originales de los campos en la serie temporal
                            cell_data['timeSeries'] = data['historic']['timeSeries']
                        else:
                            cell_data['timeSeries'] = []
                        
                        # Copiar todos los campos históricos relevantes sin modificar nombres
                        cell_data['historicData'] = {}
                        for field, value in data['historic'].items():
                            cell_data['historicData'][field] = value
                    
                    # Añadir datos KPI si existen
                    if data['kpi']:
                        # Guardar valores KPI manteniendo los nombres originales
                        cell_data['kpiValues'] = {}
                        for field, value in data['kpi'].items():
                            # Solo incluir los campos de valores KPI específicos
                            if field in ['KPREV', 'PDTE', 'REALPREV', 'PPTOPREV']:
                                try:
                                    cell_data['kpiValues'][field] = float(value)
                                except (ValueError, TypeError):
                                    cell_data['kpiValues'][field] = 0.0
                        
                        # Copiar todos los campos KPI sin modificar nombres
                        cell_data['kpiData'] = {}
                        for field, value in data['kpi'].items():
                            cell_data['kpiData'][field] = value
                    
                    # Guardar la celda en la estructura combinada
                    combined['cellData'][cell_key] = cell_data
    
    # Mostrar distribución de datos
    cells_with_historic = sum(1 for cell in combined['cellData'].values() if cell['hasHistoric'])
    cells_with_kpi = sum(1 for cell in combined['cellData'].values() if cell['hasKpi'])
    cells_with_both = sum(1 for cell in combined['cellData'].values() if cell['hasHistoric'] and cell['hasKpi'])
    
    print(f"\n=== DISTRIBUCIÓN DE DATOS ===")
    print(f"Celdas con datos históricos: {cells_with_historic}")
    print(f"Celdas con datos KPI: {cells_with_kpi}")
    print(f"Celdas con ambos tipos de datos: {cells_with_both}")
    
    return combined


if __name__ == "__main__":
    sys.exit(main())