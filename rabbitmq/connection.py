#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gestione delle connessioni a RabbitMQ
"""
import time
from rich.console import Console
from rich.panel import Panel

from utils.constants import set_active_connection, get_active_connection
from utils.logger import log_error
from config.connections import update_connection_last_used
from rabbitmq.dynamic_discovery import setup_dynamic_consumer

# Import ritardato per evitare l'importazione circolare
# from ui.layouts import create_full_layout

console = Console()


def run_consumer_for_connection(connection, live):
    """
    Esegue un consumer per la connessione RabbitMQ specificata.
    Utilizza la scoperta dinamica delle code.
    
    Args:
        connection (dict): Configurazione di connessione con host, vhost, user, password
        live (Live): Istanza di Live per l'aggiornamento dell'interfaccia
    
    Returns:
        bool: True se il consumer è avviato con successo, False altrimenti
    """
    try:
        # Aggiorna la UI per mostrare il tentativo di connessione
        from ui.animations import show_status_message
        show_status_message(
            f"Connessione a {connection['host']}/{connection['vhost']}...",
            title="CONNESSIONE",
            style="cyan",
            duration=1
        )
        
        # Imposta questa connessione come attiva
        set_active_connection(connection)
        
        # Aggiorna l'ultima data di utilizzo
        update_connection_last_used(connection)
        
        # Configura il consumer utilizzando la scoperta dinamica
        success, consumer = setup_dynamic_consumer(connection)
        
        if success:
            # Ora la connessione è configurata e avviata con successo
            # Aggiorna l'interfaccia
            from ui.layouts import create_full_layout
            live.update(create_full_layout(0))  # 0 è l'indice predefinito
            
            show_status_message(
                f"Connesso a {connection['host']}/{connection['vhost']}",
                title="CONNESSO",
                style="green",
                duration=1
            )
            
            return True
        else:
            # Fallimento nella configurazione
            show_status_message(
                f"Impossibile connettersi a {connection['host']}/{connection['vhost']}",
                title="ERRORE",
                style="red",
                duration=2
            )
            set_active_connection(None)
            return False
            
    except Exception as e:
        log_error(f"Errore nella connessione a RabbitMQ: {e}")
        show_status_message(
            f"Errore: {str(e)}",
            title="ERRORE",
            style="red",
            duration=2
        )
        set_active_connection(None)
        return False