import socket
import subprocess
import os
import signal
from dash import callback, Output, Input, State, html, no_update
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
        matching_items = []
        key = (str(cia).strip(), str(prjid).strip())
        if isinstance(fasg5_filtrados, dict) and key in fasg5_filtrados:
            item_data = fasg5_filtrados[key].get(itmid.strip().upper())
            if item_data:
                matching_items.append(item_data)
        if matching_items:
            item = matching_items[0]
            table_rows = [
                html.Tr([
                    html.Td(key, style={'fontWeight': 'bold', 'padding': '8px', 'borderBottom': '1px solid #ddd'}),
                    html.Td(str(value), style={'padding': '8px', 'borderBottom': '1px solid #ddd'})
                ])
                for key, value in item.items()
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

def show_itmfrm_popup(n_clicks, id, cia, prjid, trigger, fasg5_filtrados):
    """
    Muestra un popup con la información ITMFRM para el nodo seleccionado.
    """
    print("\nDEBUG: show_itmfrm_popup llamado")
    print(f"DEBUG: id={id}")
    print(f"DEBUG: cia={cia}, prjid={prjid}")
    print(f"DEBUG: trigger={trigger}")
    
    # Mostrar muestra filtrada de fasg5_filtrados para CIA='Sp' y PRJID='31199'
    print("\nMUESTRA DE fasg5_filtrados (solo CIA='Sp' y PRJID='31199'):")
    muestra = [item for item in fasg5_filtrados if str(item.get('CIA', '')) == 'Sp' and str(item.get('PRJID', '')) == '31199']
    for i, item in enumerate(muestra[:10]):
        print(f"  {i}: {item}")
    print(f"Total elementos en muestra filtrada: {len(muestra)}")
    print(f"Total elementos en fasg5_filtrados: {len(fasg5_filtrados)}")
    
    if not id or not cia or not prjid:
        return no_update
    
    # Extraer ITMID desde id (tercer campo, antes del paréntesis)
    parts = id.split('-')
    if len(parts) >= 3:
        itmin = parts[2].strip()
        itmid = itmin.split(' (')[0].strip()
        print(f"DEBUG: itmin extraído={itmin}")
        print(f"DEBUG: itmid extraído={itmid}")
        
        # Filtrar por CIA, PRJID e ITMID
        filtered_info = [
            item for item in fasg5_filtrados
            if str(item.get('CIA', '')).strip() == str(cia).strip() and
               str(item.get('PRJID', '')).strip() == str(prjid).strip() and
               str(item.get('ITMID', '')).strip() == str(itmid).strip()
        ]
        
        print("\nDEBUG: Valores que se están comparando:")
        print(f"DEBUG: CIA buscada: '{cia}'")
        print(f"DEBUG: PRJID buscado: '{prjid}'")
        print(f"DEBUG: ITMID buscado: '{itmid}'")
        print(f"DEBUG: filtered_info encontrados={len(filtered_info)}")
        
        if not filtered_info:
            print("\nDEBUG: No se encontraron coincidencias. Valores en los primeros 3 items:")
            for i, item in enumerate(fasg5_filtrados[:3]):
                print(f"  {i}: CIA='{item.get('CIA')}', PRJID='{item.get('PRJID')}', ITMID='{item.get('ITMID')}'")
        
        if filtered_info:
            itmfrm = filtered_info[0].get('ITMFRM', 'No disponible')
            return html.Div([
                html.H4("Información ITMFRM"),
                html.P(f"ITMID: {itmid}"),
                html.P(f"ITMFRM: {itmfrm}"),
                html.Button("Cerrar", id="close-popup-datos-i", n_clicks=0)
            ], style={
                'position': 'fixed',
                'top': '50%',
                'left': '50%',
                'transform': 'translate(-50%, -50%)',
                'background-color': 'white',
                'padding': '20px',
                'border': '1px solid black',
                'z-index': '1000'
            })
    
    return no_update
