#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Client per l'API Management di RabbitMQ
"""
import urllib.parse
import requests
from rich.console import Console
from rich.panel import Panel
from utils.logger import log_error

console = Console()

def get_queues_from_api(config):
    """
    Recupera la lista di tutte le code utilizzando l'API Management di RabbitMQ.
    
    Args:
        config (dict): Configurazione di connessione con host, vhost, user, password
    
    Returns:
        list: Lista di dizionari con i dettagli di ogni coda
    """
    try:
        # Build API URL
        host = config['host']
        vhost = urllib.parse.quote_plus(config['vhost'])
        api_url = f"http://{host}:15672/api/queues/{vhost}"
        
        # Authentication
        auth = (config['user'], config['password'])
        
        # Make request
        response = requests.get(api_url, auth=auth, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            console.print(
                Panel(
                    f"Errore nella richiesta API: {response.status_code} - {response.text}",
                    title="ERROR",
                    style="red",
                )
            )
            return []
    except Exception as e:
        log_error(f"Errore nella richiesta API: {e}")
        console.print(
            Panel(
                f"Errore nella connessione all'API RabbitMQ: {e}",
                title="ERROR",
                style="red",
            )
        )
        return []

def filter_consumable_queues(queues_data):
    """
    Filtra le code escludendo quelle "exclusive".
    
    Args:
        queues_data (list): Lista di dizionari con i dettagli delle code
    
    Returns:
        list: Lista di nomi delle code consumabili
    """
    if not queues_data:
        return []
    
    consumable_queues = []
    for queue in queues_data:
        # Skip exclusive queues
        if queue.get("exclusive", False):
            continue
        consumable_queues.append(queue["name"])
    
    return consumable_queues

def setup_api_client(connection_config):
    """
    Configura il client API per RabbitMQ Management
    
    Args:
        connection_config (dict): Configurazione della connessione
        
    Returns:
        tuple: (success, api_client_info)
    """
    try:
        # Test API connection
        queues = get_queues_from_api(connection_config)
        
        if queues:
            # Add API connection info to config
            connection_config['api_connected'] = True
            connection_config['queues_data'] = queues
            
            # Return success
            return True, {'type': 'api_client', 'queues_count': len(queues)}
        else:
            return False, None
    except Exception as e:
        log_error(f"Errore nella configurazione API client: {e}")
        return False, None

def get_all_exchanges(config):
    """
    Recupera la lista di tutti gli exchange utilizzando l'API Management.
    
    Args:
        config (dict): Configurazione di connessione
        
    Returns:
        list: Lista di dizionari con i dettagli degli exchange
    """
    try:
        # Build API URL
        host = config['host']
        vhost = urllib.parse.quote_plus(config['vhost'])
        api_url = f"http://{host}:15672/api/exchanges/{vhost}"
        
        # Authentication
        auth = (config['user'], config['password'])
        
        # Make request
        response = requests.get(api_url, auth=auth, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            log_error(f"Errore nella richiesta API exchanges: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        log_error(f"Errore nella richiesta API exchanges: {e}")
        return []

def get_queue_bindings(config, queue_name):
    """
    Recupera i binding per una coda specifica.
    
    Args:
        config (dict): Configurazione di connessione
        queue_name (str): Nome della coda
        
    Returns:
        list: Lista di dizionari con i dettagli dei binding
    """
    try:
        # Build API URL
        host = config['host']
        vhost = urllib.parse.quote_plus(config['vhost'])
        queue = urllib.parse.quote_plus(queue_name)
        api_url = f"http://{host}:15672/api/queues/{vhost}/{queue}/bindings"
        
        # Authentication
        auth = (config['user'], config['password'])
        
        # Make request
        response = requests.get(api_url, auth=auth, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            log_error(f"Errore nella richiesta API bindings: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        log_error(f"Errore nella richiesta API bindings: {e}")
        return []

def refresh_queues_data(config):
    """
    Aggiorna i dati delle code nella configurazione.
    
    Args:
        config (dict): Configurazione di connessione
        
    Returns:
        bool: True se l'aggiornamento è riuscito, False altrimenti
    """
    try:
        queues = get_queues_from_api(config)
        if queues:
            config['queues_data'] = queues
            return True
        return False
    except Exception as e:
        log_error(f"Errore nell'aggiornamento dei dati delle code: {e}")
        return False