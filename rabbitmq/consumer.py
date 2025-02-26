#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Funzionalità consumer per RabbitMQ con API Management
"""
import threading
from datetime import datetime

import pika

from utils.constants import add_message, get_live_instance, get_selected_index
from utils.logger import log_message, log_error
from ui.layouts import create_full_layout


def message_callback(ch, method, properties, body, queue_name):
    """
    Callback per la gestione dei messaggi ricevuti.
    
    Args:
        ch: Canale RabbitMQ
        method: Metodo di consegna
        properties: Proprietà del messaggio
        body: Corpo del messaggio
        queue_name: Nome della coda
    """
    try:
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
    try:
        # Se non ci sono code consumabili, crea una coda temporanea
        if not consumable_queues:
            log_message({
                'queue': 'system',
                'body': "Nessuna coda consumabile trovata. Creazione coda temporanea...",
                'timestamp': datetime.now().isoformat()
            })
            
            # Crea una coda temporanea per l'ascolto di tutto il traffico
            result = channel.queue_declare(queue='', exclusive=True)
            temp_queue = result.method.queue
            
            # Binding al default exchange
            channel.queue_bind(exchange='amq.topic', queue=temp_queue, routing_key='#')
            
            # Configura il consumer per la coda temporanea
            channel.basic_consume(
                queue=temp_queue,
                on_message_callback=lambda ch, method, props, body: message_callback(
                    ch, method, props, body, f"temp:{temp_queue}"
                ),
                auto_ack=True
            )
            
            log_message({
                'queue': 'system',
                'body': f"Consumer configurato per coda temporanea: {temp_queue}",
                'timestamp': datetime.now().isoformat()
            })
        else:
            # Configura consumer per ogni coda consumabile
            for queue_name in consumable_queues:
                try:
                    # Binding della callback con il nome della coda
                    callback = lambda ch, method, props, body, q=queue_name: message_callback(
                        ch, method, props, body, q
                    )
                    
                    # Configura il consumer
                    channel.basic_consume(
                        queue=queue_name,
                        on_message_callback=callback,
                        auto_ack=True
                    )
                    
                    log_message({
                        'queue': 'system',
                        'body': f"Consumer configurato per coda: {queue_name}",
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception as queue_err:
                    log_error(f"Errore nella configurazione del consumer per {queue_name}: {queue_err}")
        
        # Avvia un thread per processare i messaggi in background
        def consume_loop():
            try:
                log_message({
                    'queue': 'system',
                    'body': "Thread consumer avviato",
                    'timestamp': datetime.now().isoformat()
                })
                
                # Start consuming (this will block the thread)
                channel.start_consuming()
            except Exception as e:
                log_error(f"Errore nel thread consumer: {e}")
        
        consumer_thread = threading.Thread(target=consume_loop, daemon=True)
        consumer_thread.start()
        
        # Store thread reference in the config
        connection_config['consumer_thread'] = consumer_thread
        
        return True
    except Exception as e:
        log_error(f"Errore nella configurazione dei consumer: {e}")
        return False