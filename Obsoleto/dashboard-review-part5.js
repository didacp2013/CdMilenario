// Función para mostrar detalles de una celda
        function showCellDetails(cellKey) {
            if (!cellData[cellKey]) return;
            
            const cell = cellData[cellKey];
            
            // Configurar título del modal
            modalTitle.textContent = `${cell.category} - ${cell.subcategory}`;
            
            // Crear tabla de detalles
            let tableHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>Período</th>
                            <th>Valor</th>
                            ${data.hasPpto ? '<th>Presupuesto</th>' : ''}
                            ${data.hasPrev ? '<th>Previsión</th>' : ''}
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            // Ordenar series temporales para mostrar los más recientes primero
            const seriesData = [...cell.timeSeries].sort((a, b) => {
                // Intentar ordenar por período de forma descendente
                if (a.period < b.period) return 1;
                if (a.period > b.period) return -1;
                return 0;
            });
            
            // Añadir filas con datos
            seriesData.forEach(point => {
                const valueClass = point.value >= 0 ? 'positive' : 'negative';
                
                tableHTML += `
                    <tr>
                        <td>${point.period}</td>
                        <td class="${valueClass}">${formatNumber(point.value)}</td>
                        ${data.hasPpto ? `<td>${formatNumber(point.ppto || 0)}</td>` : ''}
                        ${data.hasPrev ? `<td>${formatNumber(point.prev || 0)}</td>` : ''}
                    </tr>
                `;
            });
            
            tableHTML += `
                    </tbody>
                </table>
            `;
            
            // Actualizar tabla en el modal
            detailTable.innerHTML = tableHTML;
            
            // Mostrar modal
            detailModal.style.display = 'block';
        }
        
        // Función para mostrar gráfico completo de una celda
        function showCellChart(cellKey) {
            if (!cellData[cellKey]) return;
            
            const cell = cellData[cellKey];
            
            // Configurar título del modal
            modalTitle.textContent = `Gráfico: ${cell.category} - ${cell.subcategory}`;
            
            // Limpiar contenedor del gráfico
            detailChart.innerHTML = '';
            
            // Ordenar serie temporal
            const seriesData = [...cell.timeSeries].sort((a, b) => {
                if (a.period < b.period) return -1;
                if (a.period > b.period) return 1;
                return 0;
            });
            
            // Verificar que hay datos suficientes
            if (seriesData.length <= 1) {
                detailChart.innerHTML = '<div style="text-align: center; padding: 20px;">No hay suficientes datos para mostrar un gráfico</div>';
                chartStatus.textContent = '';
                detailTable.innerHTML = '';
                detailModal.style.display = 'block';
                return;
            }
            
            // Crear gráfico detallado con D3
            createDetailChart(detailChart, seriesData, cell);
            
            // Actualizar estado del gráfico
            chartStatus.textContent = `Mostrando ${seriesData.length} períodos`;
            
            // Limpiar tabla para enfocarse en el gráfico
            detailTable.innerHTML = '';
            
            // Mostrar modal
            detailModal.style.display = 'block';
        }
        
        // Función para crear gráfico detallado
        function createDetailChart(container, data, cell) {
            // Configurar dimensiones
            const margin = {top: 20, right: 30, bottom: 50, left: 60};
            const width = container.clientWidth - margin.left - margin.right;
            const height = container.clientHeight - margin.top - margin.bottom;
            
            // Crear SVG
            const svg = d3.select(container)
                .append('svg')
                .attr('width', container.clientWidth)
                .attr('height', container.clientHeight)
                .append('g')
                .attr('transform', `translate(${margin.left},${margin.top})`);
            
            // Procesar datos para el gráfico
            const chartData = data.map(d => ({
                period: d.period,
                value: d.value,
                ppto: d.ppto || null,
                prev: d.prev || null
            }));
            
            // Configurar escalas
            const x = d3.scaleBand()
                .domain(chartData.map(d => d.period))
                .range([0, width])
                .padding(0.2);
            
            // Encontrar valores mínimo y máximo incluyendo ppto y prev si existen
            const allValues = [];
            chartData.forEach(d => {
                allValues.push(d.value);
                if (d.ppto !== null) allValues.push(d.ppto);
                if (d.prev !== null) allValues.push(d.prev);
            });
            
            const minValue = d3.min(allValues);
            const maxValue = d3.max(allValues);
            
            // Asegurar que el gráfico muestra el cero
            const yDomain = [
                minValue < 0 ? minValue * 1.1 : 0,
                maxValue > 0 ? maxValue * 1.1 : 0
            ];
            
            const y = d3.scaleLinear()
                .domain(yDomain)
                .range([height, 0]);
            
            // Añadir ejes
            svg.append('g')
                .attr('transform', `translate(0,${height})`)
                .call(d3.axisBottom(x))
                .selectAll('text')
                .style('text-anchor', 'end')
                .attr('dx', '-.8em')
                .attr('dy', '.15em')
                .attr('transform', 'rotate(-45)');
            
            svg.append('g')
                .call(d3.axisLeft(y)
                    .tickFormat(d => formatNumber(d)));
            
            // Añadir línea horizontal para cero
            svg.append('line')
                .attr('x1', 0)
                .attr('y1', y(0))
                .attr('x2', width)
                .attr('y2', y(0))
                .attr('stroke', '#ccc')
                .attr('stroke-width', 1)
                .attr('stroke-dasharray', '3,3');
            
            // Añadir barras para valores
            svg.selectAll('.bar')
                .data(chartData)
                .enter()
                .append('rect')
                .attr('class', 'bar')
                .attr('x', d => x(d.period))
                .attr('width', x.bandwidth())
                .attr('y', d => d.value >= 0 ? y(d.value) : y(0))
                .attr('height', d => Math.abs(y(d.value) - y(0)))
                .attr('fill', d => d.value >= 0 ? '#3b82f6' : '#ef4444');
            
            // Añadir línea para presupuesto si existe
            if (data.some(d => d.ppto !== undefined && d.ppto !== null)) {
                const line = d3.line()
                    .x(d => x(d.period) + x.bandwidth() / 2)
                    .y(d => y(d.ppto))
                    .defined(d => d.ppto !== null);
                
                svg.append('path')
                    .datum(chartData)
                    .attr('fill', 'none')
                    .attr('stroke', '#000')
                    .attr('stroke-width', 2)
                    .attr('stroke-dasharray', '5,5')
                    .attr('d', line);
                
                // Añadir puntos para presupuesto
                svg.selectAll('.ppto-point')
                    .data(chartData.filter(d => d.ppto !== null))
                    .enter()
                    .append('circle')
                    .attr('class', 'ppto-point')
                    .attr('cx', d => x(d.period) + x.bandwidth() / 2)
                    .attr('cy', d => y(d.ppto))
                    .attr('r', 4)
                    .attr('fill', '#000');
            }
            
            // Añadir línea para previsión si existe
            if (data.some(d => d.prev !== undefined && d.prev !== null)) {
                const line = d3.line()
                    .x(d => x(d.period) + x.bandwidth() / 2)
                    .y(d => y(d.prev))
                    .defined(d => d.prev !== null);
                
                svg.append('path')
                    .datum(chartData)
                    .attr('fill', 'none')
                    .attr('stroke', '#f97316')
                    .attr('stroke-width', 2)
                    .attr('d', line);
                
                // Añadir puntos para previsión
                svg.selectAll('.prev-point')
                    .data(chartData.filter(d => d.prev !== null))
                    .enter()
                    .append('circle')
                    .attr('class', 'prev-point')
                    .attr('cx', d => x(d.period) + x.bandwidth() / 2)
                    .attr('cy', d => y(d.prev))
                    .attr('r', 4)
                    .attr('fill', '#f97316');
            }
            
            // Añadir etiquetas de valor
            svg.selectAll('.value-label')
                .data(chartData)
                .enter()
                .append('text')
                .attr('class', 'value-label')
                .attr('text-anchor', 'middle')
                .attr('x', d => x(d.period) + x.bandwidth() / 2)
                .attr('y', d => d.value >= 0 ? y(d.value) - 5 : y(d.value) + 15)
                .text(d => formatNumber(d.value))
                .attr('font-size', '10px')
                .attr('fill', d => d.value >= 0 ? '#1d4ed8' : '#dc2626');
                
            // Añadir leyenda
            const legend = svg.append('g')
                .attr('transform', `translate(${width / 2}, ${height + margin.bottom - 10})`);
            
            legend.append('rect')
                .attr('x', -120)
                .attr('width', 12)
                .attr('height', 12)
                .attr('fill', '#3b82f6');
            
            legend.append('text')
                .attr('x', -100)
                .attr('y', 9)
                .text('Valor Real')
                .attr('font-size', '10px');
            
            if (data.some(d => d.ppto !== undefined && d.ppto !== null)) {
                legend.append('line')
                    .attr('x1', -60)
                    .attr('y1', 6)
                    .attr('x2', -40)
                    .attr('y2', 6)
                    .attr('stroke', '#000')
                    .attr('stroke-width', 2)
                    .attr('stroke-dasharray', '5,5');
                
                legend.append('text')
                    .attr('x', -35)
                    .attr('y', 9)
                    .text('Presupuesto')
                    .attr('font-size', '10px');
            }
            
            if (data.some(d => d.prev !== undefined && d.prev !== null)) {
                legend.append('line')
                    .attr('x1', 40)
                    .attr('y1', 6)
                    .attr('x2', 60)
                    .attr('y2', 6)
                    .attr('stroke', '#f97316')
                    .attr('stroke-width', 2);
                
                legend.append('text')
                    .attr('x', 65)
                    .attr('y', 9)
                    .text('Previsión')
                    .attr('font-size', '10px');
            }
        }
