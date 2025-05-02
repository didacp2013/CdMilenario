def main():
    """
    Extrae y procesa los datos desde el Excel hardcodeado.
    Devuelve una lista de dicts, cada uno con la estructura:
    {
        'CIA': str,
        'PRJID': str,
        'ROW': str,
        'COLUMN': str,
        'DATATYPE': 'K' o 'H' o 'T',
        'DATACONTENTS': dict (KPI) o lista de dicts (HISTÓRICO) o dict (ÁRBOL)
    }
    """
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: No se encuentra el archivo Excel en la ruta: {EXCEL_PATH}")
        return []

    historic_data = extract_historic_data(EXCEL_PATH, HISTORIC_SHEET)
    kpi_data = extract_kpi_data(EXCEL_PATH, KPI_SHEET)
    tree_data = extract_tree_data(EXCEL_PATH, TREE_SHEET)
    
    print(f"Registros extraídos de {HISTORIC_SHEET}: {len(historic_data)}")
    print(f"Registros extraídos de {KPI_SHEET}: {len(kpi_data)}")
    print(f"Registros extraídos de {TREE_SHEET}: {len(tree_data)}")
    
    # Diagnóstico adicional para tree_data
    if tree_data:
        print(f"Columnas en los datos de árbol: {list(tree_data[0].keys())}")
        print(f"Muestra de datos de árbol (primer registro): {tree_data[0]}")
        
        # Verificar si las columnas esperadas están presentes
        expected_columns = ['CIA', 'PRJID', 'ROW', 'COLUMN', 'LEVEL', 'NODE', 'NODEP', 'ITMID', 'TYPE', 'VALUE']
        missing_columns = [col for col in expected_columns if col not in tree_data[0]]
        if missing_columns:
            print(f"ADVERTENCIA: Faltan las siguientes columnas esperadas: {missing_columns}")
    
    # Obtener los índices de la función structure_data
    _, kpi_index, historic_index = structure_data(historic_data, kpi_data)
    
    # Simplificación del procesamiento de datos de árbol
    # Primero agrupamos por CIA+PRJID+ROW (sin COLUMN)
    tree_by_row = {}
    for record in tree_data:
        row_key = (
            str(record.get("CIA", "")),
            str(record.get("PRJID", "")),
            str(record.get("ROW", ""))
        )
        if row_key not in tree_by_row:
            tree_by_row[row_key] = []
        tree_by_row[row_key].append({
            "CIA": record.get("CIA", ""),
            "PRJID": record.get("PRJID", ""),
            "ROW": record.get("ROW", ""),
            "COLUMN": record.get("COLUMN", ""),
            "LEVEL": record.get("LEVEL", 0),
            "NODE": record.get("NODE", 0),
            "NODEP": record.get("NODEP", 0),
            "ITMID": record.get("ITMID", ""),
            "TYPE": record.get("TYPE", ""),
            "VALUE": record.get("VALUE", 0)
        })
    
    print(f"Número de combinaciones únicas CIA+PRJID+ROW: {len(tree_by_row)}")
    
    # Ahora procesamos cada grupo para construir la estructura jerárquica
    processed_tree_index = {}
    
    for row_key, items in tree_by_row.items():
        # Procesar los datos de árbol para esta combinación CIA+PRJID+ROW
        column_structures = procesar_datos_arbol(items)
        
        # column_structures es un diccionario donde las claves son los valores de COLUMN
        # y los valores son las estructuras de árbol correspondientes
        for column, tree_structure in column_structures.items():
            # Solo incluir estructuras no nulas
            if tree_structure is not None:
                full_key = row_key + (column,)
                processed_tree_index[full_key] = tree_structure
    
    # Ahora construimos el resultado final
    result = []
    all_keys = set(list(kpi_index.keys()) + list(historic_index.keys()) + list(processed_tree_index.keys()))
    
    # ... resto del código sin cambios ...