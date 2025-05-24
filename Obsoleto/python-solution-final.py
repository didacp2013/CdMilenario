import pandas as pd
import numpy as np
from pathlib import Path
import time
import traceback

def procesar_datos_jerarquicos(df, timeout_minutos=5):
    """
    Procesa datos jerárquicos respetando la estructura original de subniveles.
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
        
        # Convertir tipos
        df['Prj'] = df['Prj'].astype(str)
        df['Parte_Prj'] = df['Parte_Prj'].astype(str).str.zfill(4)
        df['Cia'] = df['Cia'].astype(str)
        df['Subnivel'] = df['Subnivel'].astype(int)
        df['Nodo'] = df['Nodo'].astype(int)
        df['Nodo_Padre'] = df['Nodo_Padre'].astype(int)
        
        # Convertir Coste_real si tiene comas
        if df['Coste_real'].dtype == object:
            df['Coste_real'] = df['Coste_real'].str.replace(',', '.').astype(float)
        
        # Añadir claves
        df['ClaveJerarquica'] = df['Cia'] + '-' + df['Prj'] + '-' + df['Parte_Prj'] + '-' + df['Subnivel'].astype(str) + '-' + df['Nodo'].astype(str)
        df['ClavePadre'] = np.where(
            df['Nodo_Padre'] == 0,
            None,
            df['Cia'] + '-' + df['Prj'] + '-' + df['Parte_Prj'] + '-' + df['Subnivel'].astype(str) + '-' + df['Nodo_Padre'].astype(str)
        )
        df['Grupo'] = df['Cia'] + '-' + df['Prj'] + '-' + df['Parte_Prj']
        
        # IMPORTANTE: Análisis de la estructura de niveles
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
        # CLAVE: Usar Subnivel como base para el Nivel
        # El nivel jerárquico debe basarse en el Subnivel, no calcularse recursivamente
        df['Nivel'] = df['Subnivel']
        
        # Verificar distribución de niveles
        print(f"Distribución de niveles: {df['Nivel'].value_counts().sort_index().to_dict()}")
    except Exception as e:
        print(f"Error en cálculo de niveles: {str(e)}")
        traceback.print_exc()
        return None
    
    # PASO 2: GENERAR DESCRIPCIONES
    print("\nGenerando descripciones...")
    try:
        # Crear descripciones
        df['Descripcion'] = np.where(
            (df['Artículo'].isna()) | (df['Artículo'] == 'null'),
            df['Prj'] + '.' + df['Parte_Prj'] + ' - ' + df['Compo_Coste'].astype(str) + ' - ' + df['Tipo'],
            df['Artículo'].astype(str) + ' (' + df['Tipo'] + ') - ' + df['Coste_real'].round(2).astype(str) + '€'
        )
        
        # Agregar valor y descripción de árbol
        df['Valor'] = df['Coste_real']
        df['DescripcionArbol'] = df.apply(lambda row: '    ' * (row['Nivel'] - 1) + row['Descripcion'], axis=1)
    except Exception as e:
        print(f"Error en generación de descripciones: {str(e)}")
        traceback.print_exc()
        return None
    
    # PASO 3: CALCULAR RUTAS
    print("\nCalculando rutas completas...")
    try:
        # Inicializar rutas
        df['RutaCompleta'] = df['Nodo'].astype(str)
        df.loc[df['Nodo_Padre'] == 0, 'RutaCompleta'] = "0"
        
        # Crear un diccionario para búsqueda rápida
        nodos_dict = {}
        for _, row in df.iterrows():
            grupo = row['Grupo']
            nodo = row['Nodo']
            clave = f"{grupo}-{nodo}"
            
            if grupo not in nodos_dict:
                nodos_dict[grupo] = {}
            
            nodos_dict[grupo][nodo] = row
        
        # Función para obtener ruta (enfoque iterativo)
        def obtener_ruta(grupo, nodo):
            if nodo == 0:
                return "0"
            
            # Si el nodo no existe en el diccionario
            if nodo not in nodos_dict.get(grupo, {}):
                return str(nodo)
            
            ruta = [str(nodo)]
            nodo_actual = nodo
            visitados = set([nodo])  # Evitar ciclos
            
            while True:
                nodo_padre = nodos_dict[grupo][nodo_actual]['Nodo_Padre']
                
                # Si llegamos a la raíz o hay un ciclo, terminamos
                if nodo_padre == 0 or nodo_padre in visitados:
                    break
                
                # Si el padre no existe en nuestro diccionario, terminamos
                if nodo_padre not in nodos_dict.get(grupo, {}):
                    break
                
                # Agregar a la ruta y continuar
                ruta.append(str(nodo_padre))
                visitados.add(nodo_padre)
                nodo_actual = nodo_padre
            
            # La ruta ya está en orden inverso, solo debemos unirla
            return ":".join(ruta)
        
        # Calcular rutas para todos los nodos
        for idx, row in df.iterrows():
            if row['Nodo_Padre'] != 0:  # Solo para nodos no raíz
                grupo = row['Grupo']
                nodo = row['Nodo']
                df.at[idx, 'RutaCompleta'] = obtener_ruta(grupo, nodo)
            
            # Verificar timeout ocasionalmente
            if idx % 1000 == 0 and verificar_tiempo():
                return None
        
        # Eliminar duplicados
        df = df.drop_duplicates(subset=['ClaveJerarquica'])
    except Exception as e:
        print(f"Error en cálculo de rutas: {str(e)}")
        traceback.print_exc()
        return None
    
    # PASO 4: GENERAR COLUMNAS DE NIVEL
    print("\nGenerando columnas de nivel...")
    try:
        # Determinar nivel máximo y verificar que es razonable
        nivel_maximo = df['Nivel'].max()
        print(f"Nivel máximo detectado: {nivel_maximo}")
        
        if nivel_maximo > 10:  # Un valor de seguridad razonable
            print(f"⚠️ Nivel máximo sospechosamente alto: {nivel_maximo}")
            print("Ajustando para usar solo los niveles reales en los datos...")
            nivel_maximo = min(10, nivel_maximo)  # Limitar a un máximo razonable
        
        # Crear todas las columnas a la vez para evitar fragmentación
        nuevas_columnas = {}
        for nivel in range(1, nivel_maximo + 1):
            col_name = f'Nivel{nivel}'
            nuevas_columnas[col_name] = np.where(df['Nivel'] == nivel, df['DescripcionArbol'], None)
        
        # Añadir todas las columnas de una vez
        df = pd.concat([df, pd.DataFrame(nuevas_columnas, index=df.index)], axis=1)
    except Exception as e:
        print(f"Error en generación de columnas: {str(e)}")
        traceback.print_exc()
        return None
    
    # PASO 5: APLICAR RELLENO POR GRUPO
    print("\nAplicando relleno por grupo...")
    try:
        result_dfs = []
        
        # Procesar cada grupo
        for nombre_grupo, grupo_df in df.groupby(['Prj', 'Parte_Prj']):
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
        result_df = result_df.sort_values(['Prj', 'Parte_Prj', 'Nivel', 'Nodo'])
        
        # Seleccionar columnas finales
        columns_to_keep = ['Cia', 'Prj', 'Parte_Prj', 'Nivel', 'Valor', 
                          'Descripcion', 'DescripcionArbol', 'RutaCompleta'] + [f'Nivel{i}' for i in range(1, nivel_maximo + 1)]
        
        result_df = result_df[columns_to_keep]
    except Exception as e:
        print(f"Error en relleno por grupo: {str(e)}")
        traceback.print_exc()
        return None
    
    tiempo_total = time.time() - tiempo_inicio
    print(f"\n✅ Procesamiento completado en {tiempo_total:.2f} segundos")
    return result_df

def main():
    try:
        # Ruta del archivo Excel
        excel_path = Path(r"C:\Users\127839\Downloads\StoryMac\DashBTracker\PruebasCdM\F_Asg3.xlsx")
        print(f"Procesando archivo: {excel_path}")
        
        # Cargar datos
        print("Cargando datos...")
        df = pd.read_excel(excel_path, sheet_name="F_Asg3")
        print(f"Datos cargados: {len(df)} filas")
        
        # Procesar datos con límite de tiempo
        result_df = procesar_datos_jerarquicos(df, timeout_minutos=5)
        
        if result_df is not None:
            # Escribir resultados en una nueva hoja
            output_path = excel_path.parent / "Resultado_Jerarquico.xlsx"
            print(f"Guardando resultados en: {output_path}")
            result_df.to_excel(output_path, sheet_name='Resultado_Jerarquico', index=False)
            print(f"✅ Resultados guardados exitosamente.")
        else:
            print("❌ No se pudo completar el procesamiento.")
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
