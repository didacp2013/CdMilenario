from excel_utils import extract_tree_data, procesar_datos_arbol
import plotly.graph_objects as go

EXCEL_PATH = '/Users/didac/Downloads/StoryMac/DashBTracker/PruebasCdM/Tchart_V06.xlsm'
TREE_SHEET = 'F_Asg3'
COLUMNA_OBJETIVO = '08:FABRICACIÓN MECÁNICA'

# Extraer los datos
all_data = extract_tree_data(EXCEL_PATH, TREE_SHEET)
items = [item for item in all_data if str(item['CIA']).upper() == 'SP' and str(item['PRJID']) == '31200' and str(item['ROW']).strip() == '11:FABRICACION UTILES/GARRAS']
arboles = procesar_datos_arbol(items)

rutas_hojas = []
acumulados = {}  # clave: (nivel, nodo, itmin), valor: suma acumulada
columnas_hoja_validas = set()

def recorrer_arbol(node, ruta_actual):
    nueva_ruta = ruta_actual + [[node['LEVEL'], node['NODE'], node['ITMIN']]]
    if not node.get('children'):
        if node.get('VALUE', 0) != 0:
            columnas_hoja_validas.add(node.get('COLUMN'))
        if node.get('VALUE', 0) != 0 and node.get('COLUMN') == COLUMNA_OBJETIVO:
            rutas_hojas.append({
                'ruta': nueva_ruta,
                'COLUMN': node.get('COLUMN'),
                'VALUE': node.get('VALUE')
            })
            # Acumular el valor en cada nodo de la ruta
            for nivel, nodo, itmin in nueva_ruta:
                clave = (nivel, nodo, itmin)
                acumulados[clave] = acumulados.get(clave, 0) + node.get('VALUE')
    else:
        for hijo in node.get('children', []):
            recorrer_arbol(hijo, nueva_ruta)

for arbol in arboles.values():
    if arbol:
        recorrer_arbol(arbol, [])

with open('rutas_acumuladas_fabricacion_mecanica.txt', 'w', encoding='utf-8') as f:
    f.write(f'Rutas de nodos hoja válidos (VALUE != 0, COLUMN={COLUMNA_OBJETIVO}) para ROW=11:FABRICACION UTILES/GARRAS\n\n')
    for hoja in rutas_hojas:
        ruta_str = ''.join([
            f"[{nivel},{nodo},{itmin}:{acumulados[(nivel,nodo,itmin)]}]" 
            for nivel, nodo, itmin in hoja['ruta']
        ])
        f.write(f"{ruta_str} hoja({hoja['VALUE']},{hoja['COLUMN']})\n")
    f.write('\nResumen de valores acumulados por nodo:\n')
    for clave, valor in sorted(acumulados.items()):
        f.write(f"Nodo (nivel={clave[0]}, nodo={clave[1]}, itmin={clave[2]}): {valor}\n")

# Escribir la lista exacta de COLUMN de hojas válidas
with open('columnas_hojas_validas.txt', 'w', encoding='utf-8') as f:
    f.write('Valores exactos de COLUMN en nodos hoja con VALUE != 0 para ROW=11:FABRICACION UTILES/GARRAS:\n')
    for col in sorted(columnas_hoja_validas):
        f.write(f'- {repr(col)}\n')

# --- Transformar árbol a formato treemap ---
def to_treemap(node):
    return {
        "id": f"{node['LEVEL']}-{node['NODE']}-{node['ITMIN']}",
        "value": node["VALUE"],
        "children": [to_treemap(child) for child in node.get("children", [])] if node.get("children") else []
    }

# Tomar el subárbol para la columna objetivo
arbol_t = arboles.get(COLUMNA_OBJETIVO)
if arbol_t:
    treemap_data = to_treemap(arbol_t)
    # --- Crear gráfico treemap con Plotly ---
    def flatten_tree(node, parent_id=None, labels=None, parents=None, values=None):
        if labels is None:
            labels = []
        if parents is None:
            parents = []
        if values is None:
            values = []
        labels.append(node["id"])
        parents.append(parent_id if parent_id else "")
        values.append(node["value"])
        for child in node.get("children", []):
            flatten_tree(child, node["id"], labels, parents, values)
        return labels, parents, values
    labels, parents, values = flatten_tree(treemap_data)
    fig = go.Figure(go.Treemap(labels=labels, parents=parents, values=values, branchvalues="total"))
    fig.update_layout(title=f"Treemap: 11:FABRICACION UTILES/GARRAS - 08:FABRICACIÓN MECÁNICA")
    fig.write_html("treemap_fabricacion_utiles_garras_08.html")
    print("Treemap generado: treemap_fabricacion_utiles_garras_08.html")
else:
    print("No hay árbol para la columna objetivo.") 