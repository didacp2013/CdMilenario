import pandas as pd
import numpy as np
from pathlib import Path
import sys
import openpyxl

# Aumentar el límite de recursión (opcional, usaremos métodos iterativos igualmente)
sys.setrecursionlimit(3000)

def procesar_datos_jerarquicos(df):
    """
    Procesa datos jerárquicos y construye estructura arbórea con métodos iterativos.
    
    Args:
        df (DataFrame): DataFrame con los datos jerárquicos
    
    Returns:
        DataFrame: Datos procesados con estructura jerárquica
    """
    print("Iniciando procesamiento de datos jerárquicos...")
    
    # Copiar el dataframe para no modificar el original
    df = df.copy()
    
    # Asegurar tipos de datos correctos
    print("Convirtiendo tipos de datos...")
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
    print("Generando claves jerárquicas...")
    df['ClaveJerarquica'] = df['Cia'] + '-' + df['Prj'] + '-' + df['Parte_Prj'] + '-' + df['Subnivel'].astype(str) + '-' + df['Nodo'].astype(str)
    df['ClavePadre'] = np.where(
        df['Nodo_Padre'] == 0,
        None,
        df['Cia'] + '-' + df['Prj'] + '-' + df['Parte_Prj'] + '-' + df['Subnivel'].astype(str) + '-' + df['Nodo_Padre'].astype(str)
    )
    df['Grupo'] = df['Cia'] + '-' + df['Prj'] + '-' + df['Parte_Prj']
    
    # Crear diccionario para búsqueda rápida
    clave_dict = dict(zip(df['ClaveJerarquica'], df.index))
    
    # MÉTODO ITERATIVO PARA CALCULAR NIVELES
    print("Calculando niveles de forma iterativa...")
    df['Nivel'] = 1  # Iniciamos todos con nivel 1
    
    # Para nodos con padre, inicialmente asignamos nivel 2
    df.loc[df['Nodo_Padre'] > 0, 'Nivel'] = 2
    
    # Iteramos hasta que no haya cambios (convergencia)
    cambios = True
    max_iteraciones = 100  # Límite de seguridad
    iteracion = 0
    
    while cambios and iteracion < max_iteraciones:
        cambios = False
        iteracion += 1
        
        # Iteramos sobre los registros con nivel > 1
        for idx, row in df[df['Nivel'] > 1].iterrows():
            clave_padre = row['ClavePadre']
            
            # Si el padre existe en el diccionario, calculamos nivel
            if clave_padre in clave_dict:
                parent_idx = clave_dict[clave_padre]
                nivel_padre = df.loc[parent_idx, 'Nivel']
                nuevo_nivel = nivel_padre + 1
                
                # Si hay un cambio, actualizamos
                if nuevo_nivel != row['Nivel']:
                    df.loc[idx, 'Nivel'] = nuevo_nivel
                    cambios = True
    
    print(f"Cálculo de niveles completado en {iteracion} iteraciones.")
    
    # Generar descripciones
    print("Generando descripciones...")
    df['Descripcion'] = np.where(
        (df['Artículo'].isna()) | (df['Artículo'] == 'null'),
        df['Prj'] + '.' + df['Parte_Prj'] + ' - ' + df['Compo_Coste'].astype(str) + ' - ' + df['Tipo'],
        df['Artículo'].astype(str) + ' (' + df['Tipo'] + ') - ' + df['Coste_real'].round(2).astype(str) + '€'
    )
    
    # Agregar columna de valor
    df['Valor'] = df['Coste_real']
    
    # Crear descripción árbol con indentación
    df['DescripcionArbol'] = df.apply(lambda row: '    ' * (row['Nivel'] - 1) + row['Descripcion'], axis=1)
    
    # MÉTODO ITERATIVO PARA CALCULAR RUTAS
    print("Calculando rutas completas de forma iterativa...")
    
    # Inicializar columna RutaCompleta
    df['RutaCompleta'] = df['Nodo'].astype(str)
    
    # Para nodos raíz (nivel 1), asignamos "0"
    df.loc[df['Nivel'] == 1, 'RutaCompleta'] = "0"
    
    # Ordenamos por nivel para procesar primero los niveles inferiores
    df_ordenado = df.sort_values('Nivel')
    
    # Diccionario para almacenar rutas por grupo y nodo
    rutas_dict = {}
    
    # Primero llenamos el diccionario con los nodos existentes
    for _, row in df_ordenado.iterrows():
        grupo = row['Grupo']
        nodo = row['Nodo']
        if grupo not in rutas_dict:
            rutas_dict[grupo] = {}
        rutas_dict[grupo][nodo] = row['RutaCompleta']
    
    # Ahora construimos las rutas de forma iterativa
    for nivel in range(2, df['Nivel'].max() + 1):
        for _, row in df[df['Nivel'] == nivel].iterrows():
            grupo = row['Grupo']
            nodo = row['Nodo']
            padre = row['Nodo_Padre']
            
            # Si el padre existe en nuestro diccionario, construimos la ruta
            if grupo in rutas_dict and padre in rutas_dict[grupo]:
                ruta_padre = rutas_dict[grupo][padre]
                if ruta_padre == "0":
                    nueva_ruta = str(nodo)
                else:
                    nueva_ruta = str(nodo) + ":" + ruta_padre
                
                # Actualizamos la ruta en el dataframe y el diccionario
                df.loc[df['ClaveJerarquica'] == row['ClaveJerarquica'], 'RutaCompleta'] = nueva_ruta
                rutas_dict[grupo][nodo] = nueva_ruta
    
    print("Cálculo de rutas completado.")
    
    # Eliminar duplicados por clave jerárquica
    df = df.drop_duplicates(subset=['ClaveJerarquica'])
    
    # Determinar nivel máximo
    nivel_maximo = df['Nivel'].max()
    print(f"Nivel máximo detectado: {nivel_maximo}")
    
    # Crear columnas para cada nivel
    print("Generando columnas de nivel...")
    for nivel in range(1, nivel_maximo + 1):
        col_name = f'Nivel{nivel}'
        df[col_name] = np.where(df['Nivel'] == nivel, df['DescripcionArbol'], None)
    
    # Agrupar por proyecto y parte de proyecto
    print("Aplicando relleno de columnas por grupo...")
    result_dfs = []
    for (prj, parte_prj), group_df in df.groupby(['Prj', 'Parte_Prj']):
        # Ordenar dentro del grupo para el relleno correcto
        group_df = group_df.sort_values('RutaCompleta')
        
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
    
    print("Procesamiento completado exitosamente.")
    return result_df[columns_to_keep]

def main():
    try:
        # Ruta del archivo Excel
        excel_path = Path(r"C:\Users\127839\Downloads\StoryMac\DashBTracker\PruebasCdM\F_Asg3.xlsx")
        print(f"Procesando archivo: {excel_path}")
        
        # Cargar datos
        df = pd.read_excel(excel_path, sheet_name="F_Asg3")
        print(f"Datos cargados: {len(df)} filas")
        
        # Procesar datos
        result_df = procesar_datos_jerarquicos(df)
        
        # Escribir resultados en una nueva hoja
        output_path = excel_path.parent / "Resultado_Jerarquico.xlsx"
        result_df.to_excel(output_path, sheet_name='Resultado_Jerarquico', index=False)
        
        print(f"Procesamiento completado. Resultados escritos en: {output_path}")
        
    except Exception as e:
        import traceback
        print(f"Error en el procesamiento: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
