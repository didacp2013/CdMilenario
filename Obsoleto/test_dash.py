import os
import subprocess
from dash import Dash, html

app = Dash(__name__)
app.layout = html.Div("¡Hola Dash!")

def is_port_available(port):
    """Verifica si un puerto está disponible."""
    try:
        cmd = f"lsof -i :{port}"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return "LISTEN" not in process.stdout
    except Exception as e:
        print(f"Error al verificar el puerto {port}: {e}")
        return False

def get_process_using_port(port):
    """Obtiene información del proceso que está usando el puerto."""
    try:
        cmd = f"lsof -i :{port}"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if process.stdout:
            print(f"Detalles del proceso que usa el puerto {port}:\n{process.stdout}")
        else:
            print(f"No se encontró ningún proceso usando el puerto {port}.")
    except Exception as e:
        print(f"Error al obtener información del proceso en el puerto {port}: {e}")

def close_processes_on_port(port):
    """Cierra todos los procesos que están usando el puerto especificado y registra el nombre de la aplicación."""
    try:
        cmd = f"lsof -i :{port}"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if process.stdout:
            print(f"Procesos encontrados en el puerto {port}:\n{process.stdout}")
            lines = process.stdout.strip().split('\n')
            for line in lines[1:]:  # Saltar encabezado
                parts = line.split()
                if len(parts) > 1:
                    pid = parts[1]
                    try:
                        # Obtener el nombre de la aplicación asociada al PID
                        app_name_cmd = f"ps -p {pid} -o comm="
                        app_name_process = subprocess.run(app_name_cmd, shell=True, capture_output=True, text=True)
                        app_name = app_name_process.stdout.strip()
                        print(f"PID {pid} pertenece a la aplicación: {app_name}")
                    except Exception as e:
                        print(f"Error al obtener el nombre de la aplicación para PID {pid}: {e}")

                    print(f"Intentando cerrar proceso con PID {pid}...")
                    try:
                        subprocess.run(f"kill {pid}", shell=True, check=True)
                        print(f"Proceso con PID {pid} cerrado limpiamente.")
                    except Exception as e:
                        print(f"Error al cerrar proceso con PID {pid} limpiamente: {e}. Forzando cierre...")
                        subprocess.run(f"kill -9 {pid}", shell=True, check=True)
                        print(f"Proceso con PID {pid} cerrado forzosamente.")
        else:
            print(f"No se encontraron procesos en el puerto {port}.")
    except Exception as e:
        print(f"Error al cerrar procesos en el puerto {port}: {e}")

if __name__ == "__main__":
    port = 8051

    # Verificar y cerrar procesos antes de iniciar la aplicación
    print(f"Verificando si el puerto {port} está ocupado...")
    if not is_port_available(port):
        print(f"El puerto {port} está ocupado. Intentando cerrar procesos...")
        close_processes_on_port(port)

    # Verificar nuevamente si el puerto está libre
    if is_port_available(port):
        print(f"El puerto {port} está libre. Iniciando aplicación...")
        app.run(debug=True, port=port)
    else:
        print(f"El puerto {port} sigue ocupado. No se puede iniciar la aplicación.")