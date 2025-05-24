#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpiar el directorio de trabajo eliminando archivos innecesarios
"""
import os
import glob
import shutil

def cleanup_workspace():
    """Elimina archivos innecesarios del directorio de trabajo"""
    # Directorio base
    base_dir = "/Users/didac/Downloads/StoryMac/DashBTracker/PruebasCdM/Inicio_Es_Bueno"
    
    # Tipos de archivos a eliminar
    html_files = glob.glob(os.path.join(base_dir, "*.html"))
    template_files = glob.glob(os.path.join(base_dir, "templates", "*.html"))
    static_files = glob.glob(os.path.join(base_dir, "static", "*"))
    
    # Archivos específicos que ya no son necesarios
    specific_files = [
        "dashboard_flask.py",
        "dashboard_html.py",
        "dashboard_web.py",
        "flask_app.py",
        "web_dashboard.py",
        "dashboard_server.py",
        "html_generator.py",
        "template_generator.py",
        "web_interface.py"
    ]
    
    specific_paths = [os.path.join(base_dir, f) for f in specific_files]
    
    # Crear una lista de todos los archivos a eliminar
    files_to_remove = html_files + template_files + static_files
    
    # Añadir archivos específicos que existen
    for file_path in specific_paths:
        if os.path.exists(file_path):
            files_to_remove.append(file_path)
    
    # Directorios a eliminar si existen
    dirs_to_remove = [
        os.path.join(base_dir, "templates"),
        os.path.join(base_dir, "static"),
        os.path.join(base_dir, "assets"),
        os.path.join(base_dir, "css"),
        os.path.join(base_dir, "js")
    ]
    
    # Eliminar archivos
    print("Eliminando archivos innecesarios...")
    for file_path in files_to_remove:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Eliminado: {file_path}")
        except Exception as e:
            print(f"Error al eliminar {file_path}: {e}")
    
    # Eliminar directorios
    print("\nEliminando directorios innecesarios...")
    for dir_path in dirs_to_remove:
        try:
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                shutil.rmtree(dir_path)
                print(f"Eliminado directorio: {dir_path}")
        except Exception as e:
            print(f"Error al eliminar directorio {dir_path}: {e}")
    
    print("\nLimpieza completada.")

if __name__ == "__main__":
    # Pedir confirmación antes de proceder
    print("Este script eliminará archivos HTML y otros archivos innecesarios del directorio de trabajo.")
    response = input("¿Desea continuar? (s/n): ")
    
    if response.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        cleanup_workspace()
    else:
        print("Operación cancelada.")