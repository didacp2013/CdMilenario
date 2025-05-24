import pandas as pd
import numpy as np
from pathlib import Path
import time
import traceback
import webbrowser
import json
import os

def procesar_datos_jerarquicos(df, timeout_minutos=5):
    """
    Procesa datos jerárquicos con totalizaciones y formato simplificado.
    """
    tiempo_inicio = time.time()
    timeout_segundos = timeout_minutos * 60
    
    print(f"Iniciando procesamiento ({len(df)} filas)...")
    
    # Función para verificar si se ha excedido el tiempo
    def verificar_tiempo():
        tiempo_actual = time.time() - tiempo_inicio
        if tiempo_actual > timeout_segundos:
            print(f"⚠️ TIMEOUT: Procesamiento interrumpido después de {timeout_minutos} minutos")
            return True
        return False
    
    # Preparación de datos
    print("Preparando datos...")
    try:
        # Copia del dataframe
        df = df.copy()
        
        # Convertir tipos usando la nueva nomenclatura
        df['PrjId'] = df['PrjId'].astype(str)
        df['Row'] = df['Row'].astype(str).str.zfill(4)
        df['Cia'] = df['Cia'].astype(str)
        df['Subnivel'] = df['Subnivel'].astype(int)
        df['Nodo'] = df['Nodo'].astype(int)
        df['Nodo_Padre'] = df['Nodo_Padre'].astype(int)
        
        # Convertir Column a texto para mejor manejo
        df['Column'] = df['Column'].astype(str)
        
        # Convertir Cur si tiene comas
        if df['Cur'].dtype == object:
            df['Cur'] = df['Cur'].str.replace(',', '.').astype(float)
        
        # Añadir claves
        df['ClaveJerarquica'] = df['Cia'] + '-' + df['PrjId'] + '-' + df['Row'] + '-' + df['Subnivel'].astype(str) + '-' + df['Nodo'].astype(str)
        df['ClavePadre'] = np.where(
            df['Nodo_Padre'] == 0,
            None,
            df['Cia'] + '-' + df['PrjId'] + '-' + df['Row'] + '-' + df['Subnivel'].astype(str) + '-' + df['Nodo_Padre'].astype(str)
        )
        df['Grupo'] = df['Cia'] + '-' + df['PrjId'] + '-' + df['Row']
        
        # Análisis de la estructura de niveles
        print("\nAnálisis de estructura de datos:")
        print(f"Valores únicos de Subnivel: {sorted(df['Subnivel'].unique())}")
        subnivel_counts = df['Subnivel'].value_counts().sort_index()
        print(f"Conteo por Subnivel: {subnivel_counts.to_dict()}")
    except Exception as e:
        print(f"Error en preparación de datos: {str(e)}")
        traceback.print_exc()
        return None
    
    # PASO 1: DETERMINAR NIVELES CORRECTAMENTE
    print("\nCalculando niveles basados en Subnivel...")
    try:
        # Usar Subnivel como base para el Nivel
        df['Nivel'] = df['Subnivel']
        
        # Verificar distribución de niveles
        print(f"Distribución de niveles: {df['Nivel'].value_counts().sort_index().to_dict()}")
    except Exception as e:
        print(f"Error en cálculo de niveles: {str(e)}")
        traceback.print_exc()
        return None
    
    # PASO 2: GENERAR DESCRIPCIONES SIMPLIFICADAS
    print("\nGenerando descripciones simplificadas...")
    try:
        # Crear descripciones simplificadas para cada nivel
        df['Descripcion'] = np.where(
            (df['ItmId'].isna()) | (df['ItmId'] == 'null'),
            np.where(
                df['Nivel'] == 1,  # Para nivel 1 simplificamos aún más
                df['PrjId'] + "." + df['Row'],  # Solo proyecto.parte_proyecto
                df['PrjId'] + "." + df['Row'] + " - " + df['Column']
            ),
            df['ItmId'].astype(str)  # Para los artículos, solo el código
        )
        
        # Agregar valor directo
        df['Valor'] = df['Cur']
        
        # Crear descripción de árbol con indentación
        df['DescripcionArbol'] = df.apply(lambda row: '    ' * (row['Nivel'] - 1) + row['Descripcion'], axis=1)
    except Exception as e:
        print(f"Error en generación de descripciones: {str(e)}")
        traceback.print_exc()
        return None
    
    # PASO 3: CALCULAR TOTALES POR NIVELES
    print("\nCalculando totales por niveles...")
    try:
        # Primero ordenamos los datos por nivel (procesando primero los niveles más bajos)
        df_ordenado = df.sort_values(['PrjId', 'Row', 'Nivel'], ascending=[True, True, False])
        
        # Función para obtener clave de agrupación
        def get_key(row):
            return f"{row['PrjId']}-{row['Row']}-{row['Nivel']}-{row['Nodo']}"
        
        # Diccionario para guardar valores calculados
        valores_calculados = {}
        
        # Calcular totales para nodos hoja primero
        for _, row in df_ordenado.iterrows():
            key = get_key(row)
            
            # Los nodos hoja (que no son padres de nadie) mantienen su valor original
            # Para los nodos que son padres, calculamos la suma de sus hijos
            if row['Nivel'] == df['Nivel'].max():  # Si es el nivel más bajo
                valores_calculados[key] = row['Valor']
            else:
                # Encontrar todos los hijos de este nodo
                hijos = df[(df['PrjId'] == row['PrjId']) & 
                           (df['Row'] == row['Row']) & 
                           (df['Nivel'] > row['Nivel']) &
                           (df['Nodo_Padre'] == row['Nodo'])]
                
                if len(hijos) > 0:
                    # Si tiene hijos, calcular suma de valores
                    suma_hijos = sum(hijos['Valor'])
                    valores_calculados[key] = suma_hijos
                else:
                    # Si no tiene hijos, usar el valor original
                    valores_calculados[key] = row['Valor']
        
        # Actualizar valores en el DataFrame
        for key, valor in valores_calculados.items():
            partes = key.split('-')
            prj, parte, nivel, nodo = partes[0], partes[1], int(partes[2]), int(partes[3])
            
            # Localizar la fila correspondiente
            mask = (df['PrjId'] == prj) & (df['Row'] == parte) & (df['Nivel'] == nivel) & (df['Nodo'] == nodo)
            if any(mask):
                df.loc[mask, 'Valor'] = valor
        
        print("Totales calculados correctamente.")
    except Exception as e:
        print(f"Error en cálculo de totales: {str(e)}")
        traceback.print_exc()
        return None
    
    # PASO 4: GENERAR COLUMNAS DE NIVEL CON FORMATO SIMPLIFICADO
    print("\nGenerando columnas de nivel simplificadas...")
    try:
        # Determinar nivel máximo
        nivel_maximo = df['Nivel'].max()
        print(f"Nivel máximo detectado: {nivel_maximo}")
        
        # Formato de valores monetarios
        def formato_monetario(valor):
            if pd.isna(valor) or valor == 0:
                return ""
            return f"{valor:,.2f}€".replace(",", "X").replace(".", ",").replace("X", ".")
        
        # Añadir el valor monetario formateado a las descripciones
        df['DescripcionConValor'] = df.apply(
            lambda row: f"{row['Descripcion']} - {formato_monetario(row['Valor'])}", 
            axis=1
        )
        
        # SOLUCIÓN AL PROBLEMA DE BROADCAST: Usar un enfoque de aplicación directa
        nuevas_columnas = pd.DataFrame(index=df.index)
        
        for nivel in range(1, nivel_maximo + 1):
            col_name = f'Nivel{nivel}'
            # Inicializar columna con valores nulos
            nuevas_columnas[col_name] = None
            
            # Obtener solo las filas del nivel actual
            mask_nivel = df['Nivel'] == nivel
            indices_nivel = df[mask_nivel].index
            
            # Para cada fila de este nivel, añadir la descripción formateada
            for idx in indices_nivel:
                indentacion = '    ' * (nivel - 1)
                nuevas_columnas.loc[idx, col_name] = indentacion + df.loc[idx, 'DescripcionConValor']
        
        # Concatenar con el DataFrame original
        df = pd.concat([df, nuevas_columnas], axis=1)
        
        print("Columnas de nivel generadas correctamente.")
    except Exception as e:
        print(f"Error en generación de columnas: {str(e)}")
        traceback.print_exc()
        return None
    
    # PASO 5: APLICAR RELLENO POR GRUPO
    print("\nAplicando relleno por grupo...")
    try:
        result_dfs = []
        
        # Procesar cada grupo
        for nombre_grupo, grupo_df in df.groupby(['PrjId', 'Row']):
            print(f"  Procesando grupo {nombre_grupo}...")
            
            # Ordenar dentro del grupo
            grupo_df = grupo_df.sort_values(['Nivel', 'Nodo'])
            
            # Rellenar valores
            for nivel in range(1, nivel_maximo + 1):
                col_name = f'Nivel{nivel}'
                grupo_df[col_name] = grupo_df[col_name].ffill()
            
            result_dfs.append(grupo_df)
            
            if verificar_tiempo():
                return None
        
        # Combinar resultados
        result_df = pd.concat(result_dfs)
        
        # Ordenar resultado final
        result_df = result_df.sort_values(['PrjId', 'Row', 'Nivel', 'Nodo'])
        
        # Seleccionar columnas para el resultado final - incluir Column para permitir filtrado
        columns_to_keep = ['Cia', 'PrjId', 'Row', 'Nivel', 'Column', 'Valor', 'Descripcion'] + [f'Nivel{i}' for i in range(1, nivel_maximo + 1)]
        
        result_df = result_df[columns_to_keep]
    except Exception as e:
        print(f"Error en relleno por grupo: {str(e)}")
        traceback.print_exc()
        return None
    
    tiempo_total = time.time() - tiempo_inicio
    print(f"\n✅ Procesamiento completado en {tiempo_total:.2f} segundos")
    return result_df