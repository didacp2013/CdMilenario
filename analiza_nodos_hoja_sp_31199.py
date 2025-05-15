from excel_main import main as extract_excel_data
from excel_utils import extraer_itmids_hoja

# Cargar los datos como en el flujo normal
result, fasg5_filtrados = extract_excel_data()

# Filtrar todos los árboles de tipo T para CIA='Sp' y PRJID='31199'
arboles = [
    item for item in result
    if (
        item.get('CIA', '').strip() == 'Sp' and
        item.get('PRJID', '').strip() == '31199' and
        item.get('DATATYPE', '') == 'T'
    )
]

print(f'Total de árboles encontrados para CIA=Sp y PRJID=31199: {len(arboles)}')

total_itmids = set()
for item in arboles:
    row = item.get('ROW', 'N/A')
    column = item.get('COLUMN', 'N/A')
    tree = item.get('DATACONTENTS')
    print(f'\nROW: {row} | COLUMN: {column}')
    itmids = extraer_itmids_hoja(tree)
    print(f'  ITMIDs hoja encontrados: {itmids}')
    total_itmids.update(itmids)

print(f'\nTotal de ITMIDs hoja únicos en todas las combinaciones: {len(total_itmids)}')
print('Listado único de ITMIDs hoja:')
for itmid in sorted(total_itmids):
    print(itmid) 