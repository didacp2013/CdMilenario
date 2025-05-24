import pandas as pd
import numpy as np
from pathlib import Path
import openpyxl
from openpyxl import load_workbook

def procesar_datos_jerarquicos(df):
    """
    Procesa datos jerárquicos y construye estructura arbórea.
    
    Args:
        df (DataFrame): DataFrame con los datos jerárquicos
    
    Returns:
        DataFrame: Datos procesados con estructura jerárquica
    """
    # Asegurar tipos de datos correctos
    df['Prj'] = df['Prj'].astype(str)
    df['Parte_Prj'] = df['Parte_Prj'].astype(str).str.zfill(4)  # Padding con ceros
    df['Cia'] = df['Cia'].astype(str)
    df['Subnivel'] = df['Subnivel'].astype(int)
    df['Nodo'] = df['Nodo'].astype(int)
    df['Nodo_Padre'] = df['Nodo_Padre'].astype(int)
    
    # Si Coste_real tiene comas como separador decimal, convertirlo
    if df['Coste_real'].dtype == object:
        df['Coste_real'] = df['Coste_real'].str.replace(',', '.').astype(float)
    
    # Generar claves e identificadores
    df['ClaveJerarquica'] = df['Cia'] + '-' + df['Prj'] + '-' + df['Parte_Prj'] + '-' + df['Subnivel'].astype(str) + '-' + df['Nodo'].astype(str)
    df['ClavePadre'] = np.where(
        df['Nodo_Padre'] == 0,
        None,
        df['Cia'] + '-' + df['Prj'] + '-' + df['Parte_Prj'] + '-' + df['Subnivel'].astype(str) + '-' + df['Nodo_Padre'].astype(str)
    )
    df['Grupo'] = df['Cia'] + '-' + df['Prj'] + '-' + df['Parte_Prj']
    
    # Crear diccionario para búsqueda rápida de claves padres
    clave_dict = dict(zip(df['ClaveJerarquica'], df.index))
    
    # Función recursiva para calcular nivel
    def calcular_nivel(clave, clave_padre):
        if clave_padre is None or pd.isna(clave_padre):
            return 1
        
        if clave_padre not in clave_dict:
            return 2
        
        idx = clave_dict[clave_padre]
        padre_del_padre = df.loc[idx, 'ClavePadre']
        return 1 + calcular_nivel(clave_padre, padre_del_padre)
    
    # Aplicar cálculo de nivel
    df['Nivel'] = [
        1 if row['Nodo_Padre'] == 0 else calcular_nivel(row['ClaveJerarquica'], row['ClavePadre'])
        for _, row in df.iterrows()
    ]
    
    # Generar descripciones
    df['Descripcion'] = np.where(
        (df['Artículo'].isna()) | (df['Artículo'] == 'null'),
        df['Prj'] + '.' + df['Parte_Prj'] + ' - ' + df['Compo_Coste'].astype(str) + ' - ' + df['Tipo'],
        df['Artículo'].astype(str) + ' (' + df['Tipo'] + ') - ' + df['Coste_real'].round(2).astype(str) + '€'
    )
    
    # Agregar columna de valor
    df['Valor'] = df['Coste_real']
    
    # Crear descripción árbol con indentación
    df['DescripcionArbol'] = df.apply(lambda row: '    ' * (row['Nivel'] - 1) + row['Descripcion'], axis=1)
    
    # Diccionario para guardar rutas calculadas (memoización para mejorar rendimiento)
    rutas_cache = {}
    
    # Función recursiva para obtener ruta completa
    def obtener_ruta(nodo, padre, nivel, grupo):
        # Caso base
        if nivel == 1:
            return "0"
        
        # Verificar si ya calculamos esta ruta antes
        cache_key = f"{nodo}_{padre}_{nivel}_{grupo}"
        if cache_key in rutas_cache:
            return rutas_cache[cache_key]
        
        # Buscar fila padre
        mask = (
            (df['Nodo'].astype(str) == str(padre)) & 
            (df['Nivel'] == nivel - 1) & 
            (df['Grupo'] == grupo)
        )
        
        filas_padre = df[mask]
        
        if filas_padre.empty:
            ruta = str(nodo)
        else:
            padre_row = filas_padre.iloc[0]
            ruta = str(nodo) + ":" + obtener_ruta(
                padre_row['Nodo'],
                padre_row['Nodo_Padre'],
                nivel - 1,
                grupo
            )
        
        # Guardar en caché para futuras consultas
        rutas_cache[cache_key] = ruta
        return ruta
    
    # Aplicar cálculo de ruta
    df['RutaCompleta'] = [
        obtener_ruta(
            row['Nodo'],
            row['Nodo_Padre'],
            row['Nivel'],
            row['Grupo']
        )
        for _, row in df.iterrows()
    ]
    
    # Eliminar duplicados por clave jerárquica
    df = df.drop_duplicates(subset=['ClaveJerarquica'])
    
    # Determinar nivel máximo
    nivel_maximo = df['Nivel'].max()
    
    # Crear columnas para cada nivel
    for nivel in range(1, nivel_maximo + 1):
        col_name = f'Nivel{nivel}'
        df[col_name] = np.where(df['Nivel'] == nivel, df['DescripcionArbol'], None)
    
    # Agrupar por proyecto y parte de proyecto
    result_dfs = []
    for (prj, parte_prj), group_df in df.groupby(['Prj', 'Parte_Prj']):
        # Rellenar valores hacia abajo en cada columna de nivel
        for nivel in range(1, nivel_maximo + 1):
            col_name = f'Nivel{nivel}'
            group_df[col_name] = group_df[col_name].ffill()
        
        result_dfs.append(group_df)
    
    # Combinar resultados
    result_df = pd.concat(result_dfs)
    
    # Ordenar por proyecto, parte y ruta
    result_df = result_df.sort_values(['Prj', 'Parte_Prj', 'RutaCompleta'])
    
    # Seleccionar columnas finales
    columns_to_keep = ['Cia', 'Prj', 'Parte_Prj', 'Nivel', 'Valor', 
                      'Descripcion', 'DescripcionArbol', 'RutaCompleta'] + [f'Nivel{i}' for i in range(1, nivel_maximo + 1)]
    
    return result_df[columns_to_keep]

def main():
    try:
        # Ruta del archivo Excel
        excel_path = Path(r"C:\Users\127839\Downloads\StoryMac\DashBTracker\PruebasCdM\F_Asg3.xlsx")  # Ajusta la ruta según sea necesario
        
        # Cargar datos
        df = pd.read_excel(excel_path, sheet_name="F_Asg3")
        
        # Procesar datos
        result_df = procesar_datos_jerarquicos(df)
        
        # Escribir resultados en una nueva hoja
        with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            result_df.to_excel(writer, sheet_name='Resultado_Jerarquico', index=False)
        
        print(f"Procesamiento completado. Resultados escritos en la hoja 'Resultado_Jerarquico'")
        
    except Exception as e:
        print(f"Error en el procesamiento: {str(e)}")

if __name__ == "__main__":
    main()
