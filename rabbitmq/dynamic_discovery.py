#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scoperta dinamica delle code RabbitMQ - Versione avanzata con binding multipli
"""
import pika
import threading
import time
from datetime import datetime
from utils.logger import log_message, log_error
from utils.constants import add_message, get_live_instance, get_selected_index

# Rimuovere l'import circolare
# from ui.layouts import create_full_layout


class DynamicQueueDiscover:
    """
    Classe per la scoperta dinamica delle code RabbitMQ
    con supporto per binding multipli
    """
    def __init__(self):
        self.discovered_queues = {}  # { queue_name: count }
        self.stop_event = threading.Event()
        self.connection = None
        self.channel = None
        self.consumer_thread = None
    
    def connect(self, connection_config):
        """
        Stabilisce una connessione a RabbitMQ e configura il consumer
        con supporto per exchange e routing key multipli
        
        Args:
            connection_config (dict): Configurazione della connessione
            
        Returns:
            bool: True se la connessione è stabilita, False altrimenti
        """
        try:
            # Chiudi eventuali connessioni precedenti
            self.disconnect()
            
            # Crea la connessione
            credentials = pika.PlainCredentials(
                connection_config['user'], 
                connection_config['password']
            )
            
            connection_params = pika.ConnectionParameters(
                host=connection_config['host'],
                virtual_host=connection_config['vhost'],
                credentials=credentials,
                socket_timeout=5
            )
            
            self.connection = pika.BlockingConnection(connection_params)
            self.channel = self.connection.channel()
            
            # Crea una coda temporanea per intercettare i messaggi
            result = self.channel.queue_declare(queue='', exclusive=True)
            temp_queue_name = result.method.queue
            
            # Ottieni la configurazione di binding
            exchanges = connection_config.get('exchanges', [''])
            routing_patterns = connection_config.get('routing_patterns', ['#'])
            
            # Se non ci sono exchange specificati, usa solo l'exchange di default
            if not exchanges:
                exchanges = ['']  # Exchange di default
                
            # Se non ci sono pattern specificati, usa il wildcard
            if not routing_patterns:
                routing_patterns = ['#']  # Tutti i messaggi
                
            # Binding basati sulla configurazione
            bindings_count = 0
            for exchange in exchanges:
                for pattern in routing_patterns:
                    try:
                        self.channel.queue_bind(
                            exchange=exchange,
                            queue=temp_queue_name,
                            routing_key=pattern
                        )
                        bindings_count += 1
                        log_message({
                            'queue': 'system',
                            'body': f"Creato binding: exchange '{exchange}', routing key '{pattern}'",
                            'timestamp': datetime.now().isoformat()
                        })
                    except Exception as e:
                        log_error(f"Errore nel binding: exchange={exchange}, pattern={pattern}, error={e}")
            
            # Almeno un binding deve essere riuscito
            if bindings_count == 0:
                log_error("Nessun binding creato. Verifica le configurazioni di exchange e routing pattern.")
                return False
                
            # Configura il consumo della coda temporanea
            self.channel.basic_consume(
                queue=temp_queue_name,
                on_message_callback=self._message_callback,
                auto_ack=True
            )
            
            # Avvia il consumer thread
            self.stop_event.clear()
            self._start_consumer_thread()
            
            return True
            
        except Exception as e:
            log_error(f"Errore nella connessione a RabbitMQ: {e}")
            return False
    
    def _message_callback(self, ch, method, properties, body):
        """
        Callback per la gestione dei messaggi ricevuti
        
        Args:
            ch: Canale RabbitMQ
            method: Metodo di consegna
            properties: Proprietà del messaggio
            body: Corpo del messaggio
        """
        try:
            # Ottieni la routing key o identificativo della coda
            routing_key = method.routing_key
            exchange = method.exchange or "default"
            
            # Combinazione di exchange e routing key come identificatore della "coda"
            queue_id = f"{exchange}/{routing_key}"
            
            # Aggiorna il conteggio delle code scoperte
            if queue_id not in self.discovered_queues:
                self.discovered_queues[queue_id] = 0
            self.discovered_queues[queue_id] += 1
            
            # Decodifica il corpo del messaggio
            try:
                body_text = body.decode('utf-8')
            except UnicodeDecodeError:
                body_text = f"[Dati binari - {len(body)} bytes]"
            
            # Crea il dizionario del messaggio
            message_data = {
                'queue': queue_id,
                'routing_key': routing_key,
                'exchange': exchange,
                'properties': str(properties),
                'body': body_text,
                'timestamp': datetime.now().isoformat()
            }
            
            # Aggiungi il messaggio alla lista globale
            add_message(message_data)
            
            # Registra il messaggio nei log
            log_message(message_data)
            
            # Aggiorna l'interfaccia utente
            live = get_live_instance()
            if live:
                # Import ritardato per evitare l'importazione circolare
                from ui.layouts import create_full_layout
                selected_index = get_selected_index()
                live.update(create_full_layout(selected_index))
                
        except Exception as e:
            log_error(f"Errore nel processamento del messaggio: {e}")
    
    def _start_consumer_thread(self):
        """Avvia un thread separato per il consumer"""
        def consume_messages():
            try:
                while not self.stop_event.is_set():
                    # Processa gli eventi per un breve periodo
                    self.connection.process_data_events(time_limit=0.5)
                    time.sleep(0.05)  # Piccola pausa per ridurre l'uso della CPU
            except Exception as e:
                log_error(f"Errore nel consumer thread: {e}")
            finally:
                try:
                    if self.connection and self.connection.is_open:
                        self.connection.close()
                except Exception as e:
                    log_error(f"Errore nella chiusura della connessione: {e}")
        
        self.consumer_thread = threading.Thread(
            target=consume_messages, 
            name="dynamic_rabbit_consumer"
        )
        self.consumer_thread.daemon = True
        self.consumer_thread.start()
    
    def disconnect(self):
        """Chiude la connessione e ferma il consumer thread"""
        self.stop_event.set()
        
        # Attendi brevemente che il thread termini
        if self.consumer_thread and self.consumer_thread.is_alive():
            time.sleep(0.5)
        
        # Chiudi la connessione se ancora aperta
        try:
            if self.connection and self.connection.is_open:
                self.connection.close()
        except Exception as e:
            log_error(f"Errore nella chiusura della connessione: {e}")
        
        # Reset delle variabili
        self.connection = None
        self.channel = None
        self.consumer_thread = None
    
    def get_discovered_queues(self):
        """
        Ritorna le code scoperte e il numero di messaggi ricevuti
        
        Returns:
            list: Lista di dizionari con informazioni sulle code
        """
        queues_list = []
        for queue_id, count in self.discovered_queues.items():
            queues_list.append({
                'name': queue_id,
                'messages': count
            })
        return queues_list


# Funzione per integrare con il sistema esistente
def setup_dynamic_consumer(connection_config):
    """
    Configura un consumer dinamico per RabbitMQ
    
    Args:
        connection_config (dict): Configurazione della connessione
        
    Returns:
        tuple: (success, consumer_instance)
    """
    consumer = DynamicQueueDiscover()
    
    success = consumer.connect(connection_config)
    if success:
        # Aggiungi il riferimento al consumer nella configurazione
        connection_config['dynamic_consumer'] = consumer
    
    return success, consumer


# Funzione per ottenere le code scoperte
def get_discovered_queues(connection_config):
    """
    Ritorna le code scoperte dinamicamente
    
    Args:
        connection_config (dict): Configurazione della connessione
        
    Returns:
        list: Lista di dizionari con informazioni sulle code
    """
    consumer = connection_config.get('dynamic_consumer')
    if consumer:
        return consumer.get_discovered_queues()
    return []