import webbrowser
import threading
import time
from dash import Dash, html
from dashboard_utils import check_and_kill_process_on_port, reserve_port

PORT = 8050
DEBUG = False

# Verificar si el puerto está disponible
if not check_and_kill_process_on_port(PORT, verbose=DEBUG):
    print(f"El puerto {PORT} no está disponible. Saliendo...")
    exit(1)

# Reservar el puerto temporalmente
reserved_socket = reserve_port(PORT, debug=DEBUG)
if not reserved_socket:
    print(f"No se pudo reservar el puerto {PORT}. Saliendo...")
    exit(1)

print(f"Puerto {PORT} reservado correctamente.")

# Liberar el puerto reservado antes de iniciar Dash
reserved_socket.close()
print(f"Puerto {PORT} liberado antes de iniciar Dash.")

# Crear una aplicación Dash básica
app = Dash(__name__)

# Layout básico
app.layout = html.Div([
    html.H1("Dashboard Placeholder"),
    html.Div("Este es un dashboard básico en construcción.")
])

# Ejecutar app.run en un hilo separado para permitir que el flujo continúe
def run_dash():
    app.run(debug=False, port=PORT)

# Iniciar el servidor Dash en un hilo separado
thread = threading.Thread(target=run_dash)
thread.start()

# Continuar con el flujo del programa
print("El servidor Dash se está ejecutando en un hilo separado. Puedes continuar con otras tareas.")

# Abrir el navegador automáticamente después de iniciar el servidor
webbrowser.open(f"http://127.0.0.1:{PORT}")