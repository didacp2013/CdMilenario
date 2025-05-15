import pickle
from excel_main import main as extract_excel_data

# Cargar los datos como en el flujo normal
result, fasg5_filtrados = extract_excel_data()

# Buscar el árbol de la combinación deseada
arbol = None
for item in result:
    if (
        item.get('CIA', '').strip() == 'Sp' and
        item.get('PRJID', '').strip() == '31199' and
        item.get('DATATYPE', '') == 'T'
    ):
        arbol = item.get('DATACONTENTS')
        break

if arbol is not None:
    with open('arbol_temporal.pkl', 'wb') as f:
        pickle.dump(arbol, f)
    print('Árbol guardado en arbol_temporal.pkl')
else:
    print('No se encontró el árbol para CIA=Sp y PRJID=31199') 