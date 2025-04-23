// Función para formatear números
        function formatNumber(value, decimals = 0) {
            // Aplicar formato con separador de miles y decimales especificados
            return new Intl.NumberFormat('es-ES', {
                maximumFractionDigits: decimals,
                minimumFractionDigits: decimals
            }).format(value);
        }
        
        // Función para crear mini gráficos
        function createMiniChart(container, data, valueClass) {
            // Obtener dimensiones del contenedor
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            // Crear SVG usando D3
            const svg = d3.select(container)
                .append('svg')
                .attr('width', width)
                .attr('height', height);
            
            // Definir escalas
            const x = d3.scaleLinear()
                .domain([0, data.length - 1])
                .range([0, width]);
            
            // Encontrar valores mínimo y máximo
            const values = data.map(d => d.value);
            const minValue = d3.min(values);
            const maxValue = d3.max(values);
            
            // Escala para valores con un pequeño margen
            const y = d3.scaleLinear()
                .domain([minValue < 0 ? minValue * 1.1 : 0, maxValue * 1.1])
                .range([height, 0]);
            
            // Crear línea
            const line = d3.line()
                .x((d, i) => x(i))
                .y(d => y(d.value))
                .curve(d3.curveMonotoneX);
            
            // Añadir línea al SVG
            svg.append('path')
                .datum(data)
                .attr('fill', 'none')
                .attr('stroke', valueClass === 'positive' ? '#3b82f6' : '#ef4444')
                .attr('stroke-width', 1.5)
                .attr('d', line);
            
            // Añadir área bajo la línea
            const area = d3.area()
                .x((d, i) => x(i))
                .y0(y(0))
                .y1(d => y(d.value))
                .curve(d3.curveMonotoneX);
            
            svg.append('path')
                .datum(data)
                .attr('fill', valueClass === 'positive' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(239, 68, 68, 0.2)')
                .attr('d', area);
        }
