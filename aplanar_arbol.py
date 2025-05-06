def aplanar_arbol(node, path=None, max_niveles=10):
    """
    Aplana un árbol con estructura LEVEL/children en una lista de diccionarios.
    Cada diccionario representa una rama desde la raíz hasta un nodo hoja.
    """
    if path is None:
        path = []
    nivel_actual = len(path) + 1
    fila = path + [node.get("LEVEL", None)]
    if not node.get("children"):
        # Rellenar hasta el máximo de niveles con None
        fila += [None] * (max_niveles - len(fila))
        return [fila]
    else:
        filas = []
        for hijo in node["children"]:
            filas.extend(aplanar_arbol(hijo, fila, max_niveles))
        return filas

# Ejemplo de uso:
# filas = aplanar_arbol(estructura_T)
# for fila in filas:
#     print(fila)