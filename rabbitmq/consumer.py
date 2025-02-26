#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Funzionalità consumer per RabbitMQ
"""
import threading
from datetime import datetime

import pika

from utils.constants import add_message, get_live_instance, get_selected_index
from utils.logger import log_message, log_error
from ui.layouts import create_full_layout


def message_callback(ch, method, properties, body):
    """
    Callback per la gestione dei messaggi ricevuti.
    
    Args:
        ch: Canale RabbitMQ
        method: Metodo di consegna
        properties: Proprietà del messaggio
        body: Corpo del messaggio
    """
    try:
        # Ottieni informazioni sulla coda dal consumer tag
        try:
            queue_name = method.consumer_tag.split("_")[-1]
        except Exception:
            queue_name = "Sconosciuta"

        # Ottieni exchange e routing key
        exchange = method.exchange or "default"
        routing_key = method.routing_key
        
        # Decodifica il body
        try:
            body_text = body.decode()
        except UnicodeDecodeError:
            body_text = f"[Dati binari - lunghezza: {len(body)} bytes]"

        # Prepara i dati del messaggio
        message_data = {
            "queue": queue_name,
            "exchange": exchange,
            "routing_key": routing_key,
            "properties": str(properties),
            "body": body_text,
            "timestamp": datetime.now().isoformat()
        }

        # Aggiunge il messaggio alla lista globale
        add_message(message_data)
        
        # Registra il messaggio nel log
        log_message(message_data)

        # Aggiorna l'interfaccia LIVE immediatamente dopo aver ricevuto un messaggio
        live = get_live_instance()
        if live:
            selected_index = get_selected_index()
            live.update(create_full_layout(selected_index))
    except Exception as e:
        log_error(f"Errore nel callback del messaggio: {e}")


def setup_consumer(rmq_connection, channel, consumable_queues, connection_config):
    """
    Configura il consumer per le code specificate.
    
    Args:
        rmq_connection: Connessione RabbitMQ
        channel: Canale RabbitMQ
        consumable_queues (list): Lista di nomi delle code consumabili
        connection_config (dict): Configurazione di connessione
        
    Returns:
        bool: True se la configurazione è stata completata con successo, False altrimenti
    """
    # Questo metodo è mantenuto per retrocompatibilità, ma non viene utilizzato
    # nel nuovo approccio con scoperta dinamica
    
    log_error("Il metodo setup_consumer è deprecato. Utilizzare dynamic_discovery.setup_dynamic_consumer.")
    return False