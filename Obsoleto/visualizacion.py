import pandas as pd
from pathlib import Path
import webbrowser
import json
import traceback

def generar_html_visualizacion(df, ruta_salida=None):
    """
    Genera un archivo HTML con visualización interactiva de los datos jerárquicos.
    
    Args:
        df: DataFrame con los datos procesados
        ruta_salida: Ruta donde guardar el archivo HTML (opcional)
    
    Returns:
        Ruta al archivo HTML generado
    """
    print("Generando visualización HTML...")
    
    # Si no se proporciona ruta, usar el directorio actual
    if ruta_salida is None:
        ruta_salida = Path.cwd() / "treemap_visualizacion.html"
    else:
        ruta_salida = Path(ruta_salida)
    
    # Prepara los datos para ser incluidos en el HTML
    json_data = df.to_json(orient='records')
    
    # Leer la plantilla HTML desde un archivo externo
    html_template_path = Path(__file__).parent / "template.html"
    
    if html_template_path.exists():
        with open(html_template_path, 'r', encoding='utf-8') as f:
            html_template = f.read()
    else:
        print("No se encontró el archivo de plantilla template.html en el directorio actual.")
        print(f"Buscando en: {html_template_path}")
        
        # Si no se encuentra, intentar usar la plantilla integrada
        html_template = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visualización Jerárquica</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            margin: 20px;
            background-color: #f5f7fa;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h1 {
            text-align: center;
            color: #1e3a8a;
        }
        
        #chart {
            width: 900px;
            height: 600px;
            margin: 0 auto;
        }
        
        .tooltip {
            position: absolute;
            background: white;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            pointer-events: none;
            opacity: 0;
        }
        
        .filters {
            display: flex;
            margin-bottom: 20px;
            gap: 20px;
        }
        
        .filter-group {
            flex: 1;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        
        select {
            width: 100%;
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        
        button {
            padding: 8px 15px;
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Visualización Jerárquica de Proyectos</h1>
        
        <div class="filters">
            <div class="filter-group">
                <label for="filter-parte">Parte Proyecto:</label>
                <select id="filter-parte" multiple size="5"></select>
            </div>
            <div class="filter-group">
                <label for="filter-coste">Componente Coste:</label>
                <select id="filter-coste" multiple size="5"></select>
            </div>
            <div>
                <button id="apply-filters">Aplicar Filtros</button>
                <button id="reset-filters">Resetear</button>
            </div>
        </div>
        
        <div id="chart"></div>
    </div>
    
    <div class="tooltip" id="tooltip"></div>
    
    <script>
    // Los datos vendrán de Python
    const data = DATA_PLACEHOLDER;
    
    // Llenar selectores de filtros
    const parteSelect = document.getElementById('filter-parte');
    const costeSelect = document.getElementById('filter-coste');
    
    // Obtener valores únicos
    const partes = [...new Set(data.map(d => d.Parte_Prj))];
    const costes = [...new Set(data.map(d => d.Compo_Coste))];
    
    // Llenar selectores
    partes.forEach(parte => {
        const option = document.createElement('option');
        option.value = parte;
        option.textContent = parte;
        parteSelect.appendChild(option);
    });
    
    costes.forEach(coste => {
        const option = document.createElement('option');
        option.value = coste;
        option.textContent = coste;
        costeSelect.appendChild(option);
    });
    
    // Crear estructura de datos jerárquica
    function buildHierarchy(data) {
        // Filtrar según selecciones
        const selectedPartes = Array.from(parteSelect.selectedOptions).map(o => o.value);
        const selectedCostes = Array.from(costeSelect.selectedOptions).map(o => o.value);
        
        let filteredData = data;
        
        if (selectedPartes.length > 0) {
            filteredData = filteredData.filter(d => selectedPartes.includes(d.Parte_Prj));
        }
        
        if (selectedCostes.length > 0) {
            filteredData = filteredData.filter(d => selectedCostes.includes(d.Compo_Coste));
        }
        
        // Crear jerarquía
        const root = {
            name: "Proyectos",
            children: []
        };
        
        // Mapa para proyectos
        const projectMap = new Map();
        
        // Mapa para niveles
        const levelMaps = [new Map(), new Map(), new Map()];
        
        // Procesar datos
        filteredData.forEach(row => {
            const nivel = row.Nivel;
            const prj = row.Prj;
            const parte = row.Parte_Prj;
            const compo = row.Compo_Coste;
            const valor = row.Valor;
            
            // Clave para proyecto
            const projKey = prj;
            
            // Clave para parte
            const parteKey = `${prj}-${parte}`;
            
            // Manejo según nivel
            if (nivel === 1) {
                // Primer nivel (proyecto)
                let projNode = projectMap.get(projKey);
                
                if (!projNode) {
                    projNode = {
                        name: `${prj}.${parte}`,
                        level: nivel,
                        value: valor,
                        children: []
                    };
                    
                    projectMap.set(projKey, projNode);
                    root.children.push(projNode);
                    levelMaps[0].set(parteKey, projNode);
                }
            } else if (nivel === 2) {
                // Segundo nivel
                const parentNode = levelMaps[0].get(parteKey);
                
                if (parentNode) {
                    const nodeKey = `${parteKey}-${compo}`;
                    let node = levelMaps[1].get(nodeKey);
                    
                    if (!node) {
                        node = {
                            name: `${prj}.${parte} - ${compo}`,
                            level: nivel,
                            value: valor,
                            children: []
                        };
                        
                        parentNode.children.push(node);
                        levelMaps[1].set(nodeKey, node);
                    }
                }
            } else if (nivel === 3) {
                // Tercer nivel
                const parentKey = `${prj}-${parte}-${compo}`;
                const parentNode = levelMaps[1].get(parentKey);
                
                if (parentNode) {
                    const nodeKey = `${parentKey}-${row.Descripcion}`;
                    
                    const node = {
                        name: row.Descripcion || `Item ${row.Nodo}`,
                        level: nivel,
                        value: valor
                    };
                    
                    parentNode.children.push(node);
                }
            }
        });
        
        return root;
    }
    
    // Crear Treemap
    function createTreemap(data) {
        // Limpiar visualización anterior
        d3.select("#chart").html("");
        
        const width = 900;
        const height = 600;
        
        // Colores por nivel
        const colors = {
            1: "#3b82f6",  // Azul
            2: "#10b981",  // Verde
            3: "#f59e0b"   // Naranja
        };
        
        // Crear jerarquía D3
        const hierarchy = d3.hierarchy(data)
            .sum(d => d.value)
            .sort((a, b) => b.value - a.value);
        
        // Crear layout
        const treemap = d3.treemap()
            .size([width, height])
            .padding(2)
            .round(true);
        
        // Aplicar layout
        treemap(hierarchy);
        
        // Crear SVG
        const svg = d3.select("#chart")
            .append("svg")
            .attr("width", width)
            .attr("height", height);
        
        // Crear nodos
        const nodes = svg.selectAll("g")
            .data(hierarchy.descendants())
            .enter()
            .append("g")
            .attr("transform", d => `translate(${d.x0},${d.y0})`);
        
        // Dibujar rectángulos
        nodes.append("rect")
            .attr("width", d => d.x1 - d.x0)
            .attr("height", d => d.y1 - d.y0)
            .attr("fill", d => colors[d.data.level] || "#ccc")
            .attr("stroke", "white")
            .on("mouseover", function(event, d) {
                // Mostrar tooltip
                const tooltip = d3.select("#tooltip");
                
                tooltip.html(`
                    <div style="font-weight: bold;">${d.data.name}</div>
                    <div>Valor: ${d.value.toLocaleString('es-ES', {
                        style: 'currency',
                        currency: 'EUR'
                    })}</div>
                `)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 28) + "px")
                .style("opacity", 1);
            })
            .on("mouseout", function() {
                d3.select("#tooltip").style("opacity", 0);
            });
        
        // Añadir textos
        nodes.append("text")
            .attr("x", 5)
            .attr("y", 15)
            .text(d => {
                // Solo mostrar texto si hay suficiente espacio
                const width = d.x1 - d.x0;
                const height = d.y1 - d.y0;
                
                if (width < 30 || height < 20) return "";
                
                return d.data.name;
            })
            .attr("font-size", "12px")
            .attr("fill", "white");
    }
    
    // Aplicar filtros
    document.getElementById("apply-filters").addEventListener("click", function() {
        const hierarchy = buildHierarchy(data);
        createTreemap(hierarchy);
    });
    
    // Resetear filtros
    document.getElementById("reset-filters").addEventListener("click", function() {
        parteSelect.selectedIndex = -1;
        costeSelect.selectedIndex = -1;
        
        const hierarchy = buildHierarchy(data);
        createTreemap(hierarchy);
    });
    
    // Inicializar visualización
    const hierarchy = buildHierarchy(data);
    createTreemap(hierarchy);
    </script>
</body>
</html>"""
    
    # Reemplazar el marcador de posición con los datos reales
    html_content = html_template.replace("DATA_PLACEHOLDER", json_data)
    
    # Guardar el archivo HTML
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Visualización HTML generada en: {ruta_salida}")
    
    # Abrir en el navegador
    webbrowser.open(f'file://{ruta_salida.absolute()}')
    
    return ruta_salida