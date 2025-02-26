#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gestione delle connessioni a RabbitMQ
"""
import time
import traceback
from rich.console import Console
from rich.panel import Panel

from utils.constants import set_active_connection, get_active_connection
from utils.logger import log_error, log_message
from config.connections import update_connection_last_used

console = Console()


def run_consumer_for_connection(connection, live):
    """
    Esegue un consumer per la connessione RabbitMQ specificata.
    Utilizza la scoperta dinamica delle code con debugging esteso.
    
    Args:
        connection (dict): Configurazione di connessione con host, vhost, user, password
        live (Live): Istanza di Live per l'aggiornamento dell'interfaccia
    
    Returns:
        bool: True se il consumer è avviato con successo, False altrimenti
    """
    try:
        # Import delayed to prevent circular imports
        from ui.animations import show_status_message
        
        log_message({
            'queue': 'system',
            'body': f"Tentativo di connessione a {connection['host']}/{connection['vhost']}...",
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
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
        
        # Debug import della scoperta dinamica
        try:
            from rabbitmq.dynamic_discovery import setup_dynamic_consumer
            log_message({
                'queue': 'system',
                'body': "Modulo dynamic_discovery importato con successo",
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            })
        except Exception as import_err:
            log_error(f"Errore importazione dynamic_discovery: {import_err}")
            log_error(traceback.format_exc())
            show_status_message(
                f"Errore importazione: {str(import_err)}",
                title="ERRORE",
                style="red",
                duration=2
            )
            set_active_connection(None)
            return False
        
        # Configura il consumer utilizzando la scoperta dinamica con più informazioni di debug
        try:
            log_message({
                'queue': 'system',
                'body': "Avvio setup_dynamic_consumer...",
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            })
            
            # Aggiungi un campo per tracciare meglio la connessione 
            connection['connection_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Estendi la configurazione con pattern di routing più ampi se non presenti
            if 'exchanges' not in connection:
                connection['exchanges'] = ['']  # Default exchange
            if 'routing_patterns' not in connection:
                connection['routing_patterns'] = ['#']  # Tutti i messaggi
            
            success, consumer = setup_dynamic_consumer(connection)
            
            log_message({
                'queue': 'system',
                'body': f"setup_dynamic_consumer completato con risultato: {success}",
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            })
        except Exception as setup_err:
            log_error(f"Errore in setup_dynamic_consumer: {setup_err}")
            log_error(traceback.format_exc())
            show_status_message(
                f"Errore setup: {str(setup_err)}",
                title="ERRORE",
                style="red",
                duration=2
            )
            set_active_connection(None)
            return False
        
        if success:
            # Ora la connessione è configurata e avviata con successo
            try:
                # Delayed import to prevent circular imports
                from ui.layouts import create_full_layout
                live.update(create_full_layout(0))  # 0 è l'indice predefinito
                
                log_message({
                    'queue': 'system',
                    'body': f"Connesso con successo a {connection['host']}/{connection['vhost']}",
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                })
                
                show_status_message(
                    f"Connesso a {connection['host']}/{connection['vhost']}",
                    title="CONNESSO",
                    style="green",
                    duration=1
                )
                
                return True
            except Exception as ui_err:
                log_error(f"Errore aggiornamento UI dopo connessione: {ui_err}")
                log_error(traceback.format_exc())
                return True  # Connessione riuscita ma con errore UI
        else:
            # Fallimento nella configurazione
            log_error("Connessione non riuscita, consumer non avviato")
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
        log_error(traceback.format_exc())
        show_status_message(
            f"Errore: {str(e)}",
            title="ERRORE",
            style="red",
            duration=2
        )
        set_active_connection(None)
        return False