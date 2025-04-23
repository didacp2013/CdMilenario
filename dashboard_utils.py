#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utilidades para el dashboard
"""
import os
import sys
import socket
import signal
import subprocess

def check_and_kill_process_on_port(port, verbose=False):
    """
    Verifica si hay un proceso usando el puerto especificado y lo mata si es necesario.

    Args:
        port (int): El puerto a verificar.
        verbose (bool): Si es True, imprime mensajes detallados sobre las acciones realizadas.

    Returns:
        bool: True si el puerto fue liberado o estaba disponible, False si no se pudo liberar.
    """
    import socket
    import subprocess
    import os
    import signal

    try:
        # Verificar si el puerto está en uso
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()

        if result != 0:  # El puerto no está en uso
            if verbose:
                print(f"El puerto {port} está disponible.")
            return True

        if verbose:
            print(f"El puerto {port} está en uso. Intentando liberar...")

        # Usar lsof para encontrar el PID del proceso que usa el puerto
        try:
            cmd = f"lsof -i :{port} -t"
            pids_output = subprocess.check_output(cmd, shell=True).decode().strip()
            pids = [int(pid) for pid in pids_output.split('\n') if pid.strip()]

            for pid in pids:
                if verbose:
                    print(f"Matando proceso con PID {pid} en el puerto {port}...")
                os.kill(pid, signal.SIGTERM)

            # Verificar nuevamente si el puerto está libre
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()

            if result == 0:
                if verbose:
                    print(f"No se pudo liberar el puerto {port}.")
                return False

            if verbose:
                print(f"El puerto {port} fue liberado exitosamente.")
            return True

        except subprocess.CalledProcessError as e:
            if verbose:
                print(f"No se encontró ningún proceso usando el puerto {port}. Detalle: {e}")
            return False

    except Exception as e:
        if verbose:
            print(f"Error al verificar o liberar el puerto {port}: {e}")
        return False

def reserve_port(port, debug=False):
    """
    Reserva un puerto temporalmente para evitar que sea ocupado por otra aplicación.

    Args:
        port (int): El puerto a reservar.
        debug (bool): Si es True, imprime mensajes de depuración.

    Returns:
        socket: El socket que mantiene el puerto reservado.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1', port))
        if debug:
            print(f"Puerto {port} reservado temporalmente.")
        return sock
    except Exception as e:
        if debug:
            print(f"Error al reservar el puerto {port}: {e}")
        return None