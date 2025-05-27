#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para cerrar la aplicación dashboard
"""
import os
import signal
import subprocess
import sys

def find_and_kill_process():
    """
    Encuentra y termina el proceso de la aplicación dashboard
    """
    try:
        # Buscar procesos de Python ejecutando dash_main.py
        result = subprocess.run(
            ["pgrep", "-f", "python3 dash_main.py"], 
            capture_output=True, 
            text=True
        )
        
        if result.stdout:
            pid = int(result.stdout.strip())
            print(f"Encontrado proceso de dashboard con PID: {pid}")
            
            # Enviar señal SIGTERM para terminar el proceso
            os.kill(pid, signal.SIGTERM)
            print("Aplicación dashboard cerrada correctamente")
            return True
        else:
            print("No se encontró ningún proceso de dashboard en ejecución")
            return False
    except Exception as e:
        print(f"Error al cerrar la aplicación: {str(e)}")
        return False

if __name__ == "__main__":
    find_and_kill_process()
