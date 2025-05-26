import socket
import subprocess
import os
import signal
from dash import callback, Output, Input, State, html, no_update, dcc
import dash_bootstrap_components as dbc

def check_and_kill_process_on_port(port):
    """
    Verifica si hay un proceso usando el puerto especificado y lo mata si es necesario.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result != 0:
            return True

        try:
            cmd = f"lsof -i :{port} -t"
            pids_output = subprocess.check_output(cmd, shell=True).decode().strip()
            pids = [int(pid) for pid in pids_output.split('\n') if pid.strip()]
            for pid in pids:
                os.kill(pid, signal.SIGTERM)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result != 0
            
        except subprocess.CalledProcessError:
            return False
            
    except Exception:
        return False

def reserve_port(port):
    """
    Reserva un puerto temporalmente para evitar que sea ocupado por otra aplicación.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1', port))
        return sock
    except Exception:
        return None

def create_modal(id, title, content, close_button_id):
    """
    Crea un modal con el contenido especificado
    """
    return dbc.Modal(
        id=id,
        children=[
            dbc.ModalHeader(title),
            dbc.ModalBody(content, id=f"{id}-content"),
            dbc.ModalFooter(
                dbc.Button("Cerrar", id=close_button_id, n_clicks=0)
            )
        ],
        is_open=False,
        style={
            'zIndex': '1000'
        }
    )
