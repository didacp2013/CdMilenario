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
