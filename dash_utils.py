import socket
import subprocess
import os
import signal
from dash import callback, Output, Input, State, html
import dash_bootstrap_components as dbc

def check_and_kill_process_on_port(port, verbose=False):
    """
    Verifica si hay un proceso usando el puerto especificado y lo mata si es necesario.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result != 0:
            if verbose:
                print(f"El puerto {port} está disponible.")
            return True
        if verbose:
            print(f"El puerto {port} está en uso. Intentando liberar...")
        try:
            cmd = f"lsof -i :{port} -t"
            pids_output = subprocess.check_output(cmd, shell=True).decode().strip()
            pids = [int(pid) for pid in pids_output.split('\n') if pid.strip()]
            for pid in pids:
                if verbose:
                    print(f"Matando proceso con PID {pid} en el puerto {port}...")
                os.kill(pid, signal.SIGTERM)
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

def register_itmfrm_popup_callback(app, fasg5_filtrados):
    @app.callback(
        [Output('item-modal', 'is_open'),
         Output('item-details-content', 'children')],
        [Input('treemap-graph', 'clickData')],
        [State('item-modal', 'is_open'),
         State('cia-filter', 'value'),
         State('prjid-filter', 'value')]
    )
    def toggle_item_modal(click_data, is_open, cia, prjid):
        if not click_data:
            return is_open, []
        point = click_data['points'][0]
        node_id = point.get('id', '')
        # Solo si es nodo hoja (color rojo)
        if point.get('marker', {}).get('color') != 'red':
            return is_open, []
        # Solo si estamos en el último nivel de zoom
        if len(click_data['points']) > 1:
            return is_open, []
        # Extraer ITMID del id del nodo (formato: LEVEL+ID+ITMID+ITMTYP)
        parts = node_id.split('+')
        if len(parts) < 3:
            return is_open, []
        itmid = parts[2]
        # Buscar datos ITMFRM
        matching_items = [
            item for item in fasg5_filtrados
            if (not cia or str(item.get('CIA', '')) == str(cia)) and
               (not prjid or str(item.get('PRJID', '')) == str(prjid)) and
               str(item.get('ITMID', '')) == str(itmid)
        ]
        if matching_items:
            item = matching_items[0]
            table_rows = [
                html.Tr([
                    html.Td(key, style={'fontWeight': 'bold', 'padding': '8px', 'borderBottom': '1px solid #ddd'}),
                    html.Td(str(value), style={'padding': '8px', 'borderBottom': '1px solid #ddd'})
                ])
                for key, value in item.items() if key not in ['CIA', 'PRJID', 'ITMID']
            ]
            return True, html.Div([
                html.H5(f"Item ID: {itmid}"),
                html.Table([
                    html.Tbody(table_rows)
                ], style={'width': '100%', 'borderCollapse': 'collapse'}) if table_rows else html.P("No hay datos disponibles para este item.")
            ])
        return is_open, []

    @app.callback(
        Output('item-modal', 'is_open', allow_duplicate=True),
        [Input('close-item-modal', 'n_clicks')],
        [State('item-modal', 'is_open')],
        prevent_initial_call=True
    )
    def close_modal(n_clicks, is_open):
        if n_clicks:
            return False
        return is_open
