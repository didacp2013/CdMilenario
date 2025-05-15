from excel_utils import extraer_itmids_hoja
import pickle
import pprint

# Cambia la ruta al archivo que contenga el árbol de la combinación deseada
TREE_PICKLE_PATH = 'arbol_temporal.pkl'  # Debes guardar el árbol previamente

# Cargar el árbol desde un archivo pickle (o reemplaza por tu método de carga)
with open(TREE_PICKLE_PATH, 'rb') as f:
    tree_structure = pickle.load(f)

print('Estructura del árbol cargado (primeros niveles):')
if isinstance(tree_structure, dict):
    print('Tipo: dict')
    print('Claves:', list(tree_structure.keys()))
    if 'children' in tree_structure:
        print('Número de hijos en root:', len(tree_structure['children']))
        for i, child in enumerate(tree_structure['children'][:5]):
            print(f'Hijo {i} claves:', list(child.keys()))
elif isinstance(tree_structure, list):
    print('Tipo: list')
    print('Longitud:', len(tree_structure))
    for i, elem in enumerate(tree_structure[:5]):
        print(f'Elemento {i} claves:', list(elem.keys()))
else:
    print('Tipo desconocido:', type(tree_structure))

print('Análisis aislado de los nodos hoja:')
itmids = extraer_itmids_hoja(tree_structure)
print('\nITMIDs de nodos hoja extraídos:')
for itmid in itmids:
    print(itmid) 