#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gestione delle code RabbitMQ utilizzando l'API Management
"""
from rich.panel import Panel
from rich.console import Console
from utils.logger import log_message, log_error

# Import the API client functions
from rabbitmq.api_client import get_queues_from_api, filter_consumable_queues

console = Console()

def get_queues(config):
    """
    Recupera la lista di tutte le code dal vhost specificato usando l'API Management.
    
    Args:
        config (dict): Configurazione di connessione con host, vhost, user, password
    
    Returns:
        list: Lista di dizionari con i dettagli di ogni coda
    """
    # Check if we already have cached data
    if 'queues_data' in config and config.get('api_connected', False):
        queues_data = config['queues_data']
    else:
        # Get fresh data from API
        queues_data = get_queues_from_api(config)
        if queues_data:
            config['queues_data'] = queues_data
            config['api_connected'] = True
    
    # Format data for display
    formatted_queues = []
    for queue in queues_data:
        formatted_queues.append({
            'name': queue.get('name', 'Sconosciuta'),
            'messages': queue.get('messages', 0),
            'consumers': queue.get('consumers', 0),
            'state': queue.get('state', 'unknown')
        })
    
    log_message({
        'queue': 'system',
        'body': f"Recuperate {len(formatted_queues)} code da RabbitMQ API",
        'timestamp': None  # Will be added by log_message
    })
    
    return formatted_queues

def refresh_queues(config):
    """
    Aggiorna i dati delle code nella configurazione.
    
    Args:
        config (dict): Configurazione di connessione
        
    Returns:
        list: Lista aggiornata delle code
    """
    try:
        # Clear cached data
        if 'queues_data' in config:
            del config['queues_data']
        
        # Get fresh data
        return get_queues(config)
    except Exception as e:
        log_error(f"Errore nell'aggiornamento delle code: {e}")
        return []