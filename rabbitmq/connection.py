#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gestione delle connessioni a RabbitMQ utilizzando l'API Management
"""
import time
import traceback
import pika
import threading
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

from utils.constants import set_active_connection, get_active_connection, add_message
from utils.logger import log_error, log_message
from config.connections import update_connection_last_used
from rabbitmq.api_client import setup_api_client
from rabbitmq.consumer import setup_consumer

console = Console()

def run_consumer_for_connection(connection, live):
    """
    Esegue un consumer per la connessione RabbitMQ specificata utilizzando l'API Management.
    
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
        
        # Set this connection as active
        set_active_connection(connection)
        
        # Update last used timestamp
        update_connection_last_used(connection)
        
        # First, try to connect to the API
        try:
            from rabbitmq.api_client import setup_api_client
            
            log_message({
                'queue': 'system',
                'body': "Connessione all'API Management...",
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            })
            
            api_success, api_info = setup_api_client(connection)
            
            if not api_success:
                log_error("Impossibile connettersi all'API Management di RabbitMQ")
                show_status_message(
                    f"Impossibile connettersi all'API Management di {connection['host']}",
                    title="ERRORE",
                    style="red",
                    duration=2
                )
                set_active_connection(None)
                return False
            
            # Add API info to connection
            connection['api_info'] = api_info
            
            log_message({
                'queue': 'system',
                'body': f"Connessione API riuscita, trovate {api_info.get('queues_count', 0)} code",
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as api_err:
            log_error(f"Errore nella connessione all'API: {api_err}")
            log_error(traceback.format_exc())
            show_status_message(
                f"Errore API: {str(api_err)}",
                title="ERRORE",
                style="red",
                duration=2
            )
            set_active_connection(None)
            return False
        
        # Now set up the AMQP connection
        try:
            # Create a connection to RabbitMQ
            credentials = pika.PlainCredentials(connection['user'], connection['password'])
            parameters = pika.ConnectionParameters(
                host=connection['host'],
                virtual_host=connection['vhost'],
                credentials=credentials,
                heartbeat=15,  # Seconds
                blocked_connection_timeout=30,
                connection_attempts=3
            )
            
            # Connect to RabbitMQ
            rmq_connection = pika.BlockingConnection(parameters)
            channel = rmq_connection.channel()
            
            # Add connection objects to the config
            connection['rmq_connection'] = rmq_connection
            connection['channel'] = channel
            
            # Get list of queues from API data
            from rabbitmq.api_client import filter_consumable_queues
            queues_data = connection.get('queues_data', [])
            consumable_queues = filter_consumable_queues(queues_data)
            
            # Set up consumer
            consumer_setup = setup_consumer(rmq_connection, channel, consumable_queues, connection)
            
            if consumer_setup:
                # Start monitoring thread for connection health
                start_connection_monitor(connection)
                
                # Update UI
                from ui.layouts import create_full_layout
                live.update(create_full_layout(0))
                
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
            else:
                log_error("Configurazione consumer fallita")
                show_status_message(
                    "Configurazione consumer fallita",
                    title="ERRORE",
                    style="red",
                    duration=2
                )
                set_active_connection(None)
                return False
                
        except Exception as e:
            log_error(f"Errore nella connessione AMQP: {e}")
            log_error(traceback.format_exc())
            show_status_message(
                f"Errore: {str(e)}",
                title="ERRORE",
                style="red",
                duration=2
            )
            set_active_connection(None)
            return False
            
    except Exception as e:
        log_error(f"Errore generale nella connessione: {e}")
        log_error(traceback.format_exc())
        show_status_message(
            f"Errore: {str(e)}",
            title="ERRORE",
            style="red",
            duration=2
        )
        set_active_connection(None)
        return False

def start_connection_monitor(connection):
    """
    Avvia un thread per monitorare lo stato della connessione.
    
    Args:
        connection (dict): Configurazione di connessione
    """
    def monitor_connection():
        while True:
            try:
                # Check if we're still the active connection
                active_connection = get_active_connection()
                if not active_connection or active_connection.get('id') != connection.get('id'):
                    # Not active anymore, stop monitoring
                    break
                
                # Check connection health
                rmq_connection = connection.get('rmq_connection')
                if not rmq_connection or not rmq_connection.is_open:
                    log_error("Connessione RabbitMQ persa")
                    
                    # Signal connection loss
                    connection['connection_lost'] = True
                    
                    # Update UI
                    from ui.animations import show_status_message
                    show_status_message(
                        f"Connessione a {connection['host']} persa. Seleziona nuovamente per riconnettere.",
                        title="DISCONNESSO",
                        style="red",
                        duration=2
                    )
                    
                    # Clear active connection
                    set_active_connection(None)
                    break
                
                # Add heartbeat message occasionally
                add_message({
                    'queue': 'system',
                    'body': "Heartbeat connessione attiva",
                    'timestamp': datetime.now().isoformat(),
                    'is_heartbeat': True
                })
                
                # Sleep for a while
                time.sleep(10)
                
            except Exception as e:
                log_error(f"Errore nel monitoraggio connessione: {e}")
                time.sleep(5)
    
    # Start monitor thread
    monitor_thread = threading.Thread(target=monitor_connection, daemon=True)
    monitor_thread.start()
    connection['monitor_thread'] = monitor_thread

def disconnect_connection(connection):
    """
    Chiude la connessione RabbitMQ.
    
    Args:
        connection (dict): Configurazione di connessione
    """
    try:
        rmq_connection = connection.get('rmq_connection')
        if rmq_connection and rmq_connection.is_open:
            rmq_connection.close()
            log_message({
                'queue': 'system',
                'body': f"Connessione a {connection['host']}/{connection['vhost']} chiusa",
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            })
    except Exception as e:
        log_error(f"Errore nella chiusura della connessione: {e}")