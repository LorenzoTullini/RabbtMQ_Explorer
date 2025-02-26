#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gestione delle code RabbitMQ
"""
import urllib.parse
import requests
from rich.panel import Panel
from rich.console import Console
from rabbitmq.dynamic_discovery import get_discovered_queues

console = Console()


def get_queues(config):
    """
    Recupera la lista di tutte le code dal vhost specificato.
    Ora utilizza il sistema di scoperta dinamica invece dell'API Management.
    
    Args:
        config (dict): Configurazione di connessione con host, vhost, user, password
    
    Returns:
        list: Lista di dizionari con i dettagli di ogni coda
    """
    # Utilizziamo la nuova funzionalità di scoperta dinamica
    return get_discovered_queues(config)


def filter_consumable_queues(queues_data):
    """
    Filtra le code escludendo quelle "exclusive".
    Mantenuta per compatibilità con il codice esistente.
    
    Args:
        queues_data (list): Lista di dizionari con i dettagli delle code
    
    Returns:
        list: Lista di nomi delle code consumabili
    """
    if not queues_data:
        return []
        
    # Nel nuovo approccio, tutte le code scoperte sono consumabili
    # Quindi ritorniamo semplicemente i nomi delle code
    consumable_queues = []
    for queue in queues_data:
        consumable_queues.append(queue["name"])
    
    return consumable_queues