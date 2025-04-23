<script>
        // Datos cargados desde Python
        const initialData = ${DATA_JSON};
        
        // Referencias a elementos DOM
        const headerRow = document.getElementById('headerRow');
        const tableBody = document.getElementById('tableBody');
        const statusIndicator = document.getElementById('statusIndicator');
        const viewMode = document.getElementById('viewMode');
        const maxRows = document.getElementById('maxRows');
        const maxCols = document.getElementById('maxCols');
        const periodFilter = document.getElementById('periodFilter');
        const projectSelectorContainer = document.getElementById('projectSelectorContainer');
        const btnExport = document.getElementById('btnExport');
        
        // Modal de detalle
        const detailModal = document.getElementById('detailModal');
        const closeModal = document.getElementById('closeModal');
        const modalTitle = document.getElementById('modalTitle');
        const detailChart = document.getElementById('detailChart');
        const detailTable = document.getElementById('detailTable');
        const chartStatus = document.getElementById('chartStatus');
        
        // Variables para almacenar datos procesados
        let data = null;
        let categories = [];
        let subcategories = [];
        let periods = [];
        let projects = [];
        let cellData = {};
        
        // Inicializar aplicación
        document.addEventListener('DOMContentLoaded', function() {
            initializeApp();
        });
        
        function initializeApp() {
            // Cargar datos
            data = JSON.parse(JSON.stringify(initialData));
            
            // Extraer datos principales
            categories = data.categories || [];
            subcategories = data.subcategories || [];
            periods = data.periods || [];
            projects = data.projects || [];
            cellData = data.cellData || {};
            
            // Inicializar selectores de período
            initializePeriodSelector();
            
            // Inicializar selector de proyecto si es aplicable
            if (data.hasProjects && projects.length > 0) {
                initializeProjectSelector();
            }
            
            // Generar la matriz
            generateMatrix();
            
            // Event listeners
            setupEventListeners();
            
            // Inicializar pestañas
            initializeTabs();
            
            // Inicializar tooltip
            initializeTooltip();
        }
        
        function initializePeriodSelector() {
            // Limpiar opciones existentes
            periodFilter.innerHTML = '<option value="all">Todos los períodos</option>';
            
            // Añadir períodos en orden
            periods.forEach(period => {
                const option = document.createElement('option');
                option.value = period;
                option.textContent = period;
                periodFilter.appendChild(option);
            });
            
            // Seleccionar el último período por defecto si hay períodos
            if (periods.length > 0) {
                periodFilter.value = periods[periods.length - 1];
            }
        }
        
        function initializeProjectSelector() {
            const projectSelector = document.createElement('div');
            projectSelector.className = 'project-selector';
            projectSelector.innerHTML = `
                <label>Proyecto:</label>
                <select id="projectFilter">
                    <option value="all">Todos los proyectos</option>
                </select>
            `;
            
            // Añadir al contenedor
            projectSelectorContainer.appendChild(projectSelector);
            
            // Obtener referencia al select
            const projectFilter = document.getElementById('projectFilter');
            
            // Añadir proyectos
            projects.forEach(project => {
                const option = document.createElement('option');
                option.value = project;
                option.textContent = project;
                projectFilter.appendChild(option);
            });
            
            // Event listener para cambios en el proyecto
            projectFilter.addEventListener('change', generateMatrix);
        }
        
        function setupEventListeners() {
            // Event listeners para controles
            viewMode.addEventListener('change', generateMatrix);
            maxRows.addEventListener('change', generateMatrix);
            maxCols.addEventListener('change', generateMatrix);
            periodFilter.addEventListener('change', generateMatrix);
            btnExport.addEventListener('click', exportToCSV);
            
            // Event listeners para modales
            closeModal.addEventListener('click', function() {
                detailModal.style.display = 'none';
            });
            
            window.addEventListener('click', function(event) {
                if (event.target === detailModal) {
                    detailModal.style.display = 'none';
                }
            });
            
            // Event listeners para las pestañas
            document.querySelectorAll('.tab').forEach(tab => {
                tab.addEventListener('click', function() {
                    const tabName = this.getAttribute('data-tab');
                    switchTab(tabName);
                });
            });
        }
        
        function initializeTabs() {
            // Referencias a pestañas
            const tabs = document.querySelectorAll('.tab');
            const tabContents = document.querySelectorAll('.tab-content');
            
            // Inicializar primera pestaña como activa
            tabs[0].classList.add('active');
            document.getElementById('tabDashboard').classList.add('active');
            
            // Funcionalidad para cambiar entre pestañas
            tabs.forEach(tab => {
                tab.addEventListener('click', function() {
                    // Remover clase activa de todas las pestañas
                    tabs.forEach(t => t.classList.remove('active'));
                    tabContents.forEach(c => c.classList.remove('active'));
                    
                    // Activar pestaña seleccionada
                    this.classList.add('active');
                    const tabId = 'tab' + this.getAttribute('data-tab').charAt(0).toUpperCase() + this.getAttribute('data-tab').slice(1);
                    document.getElementById(tabId).classList.add('active');
                });
            });
        }
        
        function switchTab(tabName) {
            // Desactivar todas las pestañas
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Activar pestaña seleccionada
            document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');
            document.getElementById(`tab${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`).classList.add('active');
        }
        
        function initializeTooltip() {
            // Crear elemento tooltip
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            document.body.appendChild(tooltip);
            
            // Variables para controlar el tooltip
            let tooltipTimer;
            
            // Función para mostrar tooltip
            window.showTooltip = function(event, content) {
                clearTimeout(tooltipTimer);
                tooltip.innerHTML = content;
                tooltip.style.opacity = 1;
                tooltip.style.left = (event.pageX + 10) + 'px';
                tooltip.style.top = (event.pageY + 10) + 'px';
            };
            
            // Función para ocultar tooltip
            window.hideTooltip = function() {
                tooltipTimer = setTimeout(() => {
                    tooltip.style.opacity = 0;
                }, 200);
            };
        }
