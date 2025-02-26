#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scoperta dinamica delle code RabbitMQ - Versione avanzata con debugging dettagliato
"""
import pika
import threading
import time
import traceback
from datetime import datetime

from utils.logger import log_message, log_error
from utils.constants import add_message, get_live_instance, get_selected_index


class DynamicQueueDiscover:
    """
    Classe per la scoperta dinamica delle code RabbitMQ con debugging avanzato
    """
    def __init__(self):
        self.discovered_queues = {}  # { queue_name: count }
        self.stop_event = threading.Event()
        self.connection = None
        self.channel = None
        self.consumer_thread = None
        self.connection_active = False
        self.last_heartbeat_time = None
        self.reconnect_delay = 3  # Secondi tra i tentativi di riconnessione
        self.debug_level = 2  # Livello di dettaglio per il debug (0-3)
    
    def connect(self, connection_config):
        """
        Establish connection to RabbitMQ with advanced debugging
        
        Args:
            connection_config (dict): Connection configuration
            
        Returns:
            bool: True if connection is established, False otherwise
        """
        try:
            # Debug log
            self._debug_log(f"Inizializzazione connessione a {connection_config['host']}/{connection_config['vhost']}", level=1)
            
            # Close any previous connections
            self.disconnect()
            
            # Create connection with optimized parameters
            credentials = pika.PlainCredentials(
                connection_config['user'], 
                connection_config['password']
            )
            
            # Add parameters for connection status
            connection_params = pika.ConnectionParameters(
                host=connection_config['host'],
                virtual_host=connection_config['vhost'],
                credentials=credentials,
                heartbeat=5,
                blocked_connection_timeout=30,
                socket_timeout=5,
                retry_delay=2,
                stack_timeout=10,
                connection_attempts=3
            )
            
            self._debug_log("Parametri di connessione configurati", level=2)
            
            # Connection attempt
            try:
                self.connection = pika.BlockingConnection(connection_params)
                self._debug_log("Connessione stabilita con successo", level=1)
                self.channel = self.connection.channel()
                self._debug_log("Canale creato con successo", level=1)
                self.connection_active = True
                self.last_heartbeat_time = time.time()
                
                log_message({
                    'queue': 'system',
                    'body': f"Connessione stabilita a {connection_config['host']}/{connection_config['vhost']}",
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                log_error(f"Errore nella connessione: {e}")
                log_error(traceback.format_exc())
                return False
            
            # Get configuration
            exchanges = connection_config.get('exchanges', [])
            routing_patterns = connection_config.get('routing_patterns', ['#'])
            
            # Handle discovery based on available exchanges
            if not exchanges or (len(exchanges) == 1 and exchanges[0] == ''):
                # If no specific exchanges are defined or only default exchange is specified,
                # use a different strategy: create a temp queue without explicit bindings
                self._debug_log("Nessun exchange specifico definito, utilizzo modalità di consumo diretto", level=1)
                
                # Create a temporary queue
                result = self.channel.queue_declare(queue='', exclusive=True)
                temp_queue_name = result.method.queue
                self._debug_log(f"Coda temporanea creata: {temp_queue_name}", level=1)
                
                # Set up to consume directly without binding to default exchange
                try:
                    self._debug_log(f"Configurazione consumer diretto per coda {temp_queue_name}", level=1)
                    self.channel.basic_consume(
                        queue=temp_queue_name,
                        on_message_callback=self._message_callback,
                        auto_ack=True
                    )
                    self._debug_log("Consumer configurato con successo", level=1)
                    
                    log_message({
                        'queue': 'system',
                        'body': f"Ascolto messaggi diretti su coda temporanea {temp_queue_name}",
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception as consume_err:
                    log_error(f"Errore nella configurazione del consumer: {consume_err}")
                    log_error(traceback.format_exc())
                    return False
                    
            else:
                # If specific exchanges are defined, bind temporary queue to each exchange
                self._debug_log(f"Utilizzo modalità binding a exchanges specifici: {exchanges}", level=1)
                
                # Create a temporary queue
                result = self.channel.queue_declare(queue='', exclusive=True)
                temp_queue_name = result.method.queue
                self._debug_log(f"Coda temporanea creata: {temp_queue_name}", level=1)
                
                # Binding based on config (skip default exchange)
                bindings_count = 0
                
                for exchange in exchanges:
                    if exchange == '':
                        self._debug_log(f"Saltato binding al default exchange (non consentito)", level=1)
                        continue
                        
                    for pattern in routing_patterns:
                        try:
                            self._debug_log(f"Binding coda a exchange '{exchange}' con pattern '{pattern}'", level=1)
                            self.channel.queue_bind(
                                exchange=exchange,
                                queue=temp_queue_name,
                                routing_key=pattern
                            )
                            bindings_count += 1
                            log_message({
                                'queue': 'system',
                                'body': f"Binding creato: exchange '{exchange}', routing key '{pattern}'",
                                'timestamp': datetime.now().isoformat()
                            })
                        except Exception as bind_err:
                            log_error(f"Errore nel binding: exchange={exchange}, pattern={pattern}, error={bind_err}")
                            log_error(traceback.format_exc())
                
                # Check bindings
                if bindings_count == 0:
                    log_error("Nessun binding valido creato. Verifica le configurazioni di exchange.")
                    
                    # Fallback to direct consumption without binding
                    self._debug_log("Fallback a modalità di consumo diretto", level=1)
                    try:
                        self.channel.basic_consume(
                            queue=temp_queue_name,
                            on_message_callback=self._message_callback,
                            auto_ack=True
                        )
                        log_message({
                            'queue': 'system',
                            'body': f"Ascolto messaggi diretti su coda temporanea {temp_queue_name} (fallback)",
                            'timestamp': datetime.now().isoformat()
                        })
                    except Exception as fallback_err:
                        log_error(f"Errore nella configurazione del consumer fallback: {fallback_err}")
                        log_error(traceback.format_exc())
                        return False
                else:
                    # Set up consumer for the temporary queue
                    try:
                        self._debug_log(f"Configurazione consumer per coda {temp_queue_name}", level=1)
                        self.channel.basic_consume(
                            queue=temp_queue_name,
                            on_message_callback=self._message_callback,
                            auto_ack=True
                        )
                        self._debug_log("Consumer configurato con successo", level=1)
                    except Exception as consume_err:
                        log_error(f"Errore nella configurazione del consumer: {consume_err}")
                        log_error(traceback.format_exc())
                        return False
            
            # Start consumer thread
            self._debug_log("Avvio thread consumer...", level=1)
            self.stop_event.clear()
            self._start_consumer_thread()
            
            log_message({
                'queue': 'system',
                'body': "Configurazione di RabbitMQ completata con successo",
                'timestamp': datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            log_error(f"Errore generale nella configurazione di RabbitMQ: {e}")
            log_error(traceback.format_exc())
            return False
    
    def _debug_log(self, message, level=1):
        """Log di debug con livello di dettaglio"""
        if level <= self.debug_level:
            log_message({
                'queue': 'debug',
                'body': f"DEBUG: {message}",
                'timestamp': datetime.now().isoformat()
            })
    
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
            # Aggiorna l'ultimo timestamp di heartbeat
            self.last_heartbeat_time = time.time()
            
            # Ottieni la routing key o identificativo della coda
            routing_key = method.routing_key
            exchange = method.exchange or "default"
            
            # Debug
            self._debug_log(f"Ricevuto messaggio da {exchange}/{routing_key}", level=3)
            
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
            try:
                live = get_live_instance()
                if live:
                    # Import ritardato per evitare l'importazione circolare
                    from ui.layouts import create_full_layout
                    selected_index = get_selected_index()
                    live.update(create_full_layout(selected_index))
            except Exception as ui_err:
                log_error(f"Errore nell'aggiornamento UI: {ui_err}")
                
        except Exception as e:
            log_error(f"Errore nel processamento del messaggio: {e}")
            log_error(traceback.format_exc())
    
    def _start_consumer_thread(self):
        """Avvia un thread separato per il consumer con monitoraggio della connessione"""
        def consume_messages():
            self._debug_log("Thread consumer avviato", level=1)
            
            while not self.stop_event.is_set():
                try:
                    # Verifica se la connessione è attiva
                    if self.connection_active and self.connection and self.connection.is_open:
                        # Processa gli eventi per un breve periodo
                        self.connection.process_data_events(time_limit=1.0)
                        
                        # Verifica timeout dell'heartbeat (30 secondi senza attività)
                        current_time = time.time()
                        if self.last_heartbeat_time and (current_time - self.last_heartbeat_time) > 30:
                            self._debug_log("Rilevato timeout heartbeat, invio heartbeat manuale", level=2)
                            try:
                                # Prova a inviare un heartbeat manuale
                                self.connection.process_data_events(0)
                                self.last_heartbeat_time = current_time
                            except Exception as hb_err:
                                log_error(f"Errore nell'invio del heartbeat: {hb_err}")
                                self.connection_active = False
                    else:
                        # La connessione non è attiva o è stata chiusa
                        # Segnala il problema
                        log_message({
                            'queue': 'system',
                            'body': "⚠️ Connessione a RabbitMQ persa o non attiva",
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        # Imposta connessione come non attiva
                        self.connection_active = False
                        
                        # Attendi prima di tentare di riconnettere
                        for i in range(self.reconnect_delay):
                            if self.stop_event.is_set():
                                break
                            time.sleep(1)
                        
                        # Se il thread è stato fermato, esci
                        if self.stop_event.is_set():
                            break
                        
                        # Tenta di ricreare la connessione e il canale
                        try:
                            self._debug_log("Tentativo di riconnessione dopo disconnessione", level=1)
                            # Chiudere la vecchia connessione se ancora presente
                            try:
                                if self.connection:
                                    self.connection.close()
                            except:
                                pass
                            
                            # Qui bisognerebbe riconfigurare la connessione,
                            # ma non abbiamo la configurazione originale nel thread
                            self._debug_log("Connessione non ripristinabile dal thread consumer", level=1)
                            log_message({
                                'queue': 'system',
                                'body': "⚠️ Impossibile riconnettere automaticamente. Seleziona nuovamente la connessione.",
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            # Aggiorna lo stato nella UI
                            try:
                                from utils.constants import set_active_connection
                                set_active_connection(None)
                                
                                live = get_live_instance()
                                if live:
                                    from ui.layouts import create_full_layout
                                    selected_index = get_selected_index()
                                    live.update(create_full_layout(selected_index))
                            except Exception as update_err:
                                log_error(f"Errore nell'aggiornamento UI dopo perdita connessione: {update_err}")
                            
                            # Usciamo dal loop, è necessario un intervento manuale
                            break
                            
                        except Exception as reconnect_err:
                            log_error(f"Errore nel tentativo di riconnessione: {reconnect_err}")
                            log_error(traceback.format_exc())
                    
                    # Pausa breve per ridurre l'uso della CPU
                    time.sleep(0.1)
                    
                except pika.exceptions.AMQPConnectionError as conn_err:
                    log_error(f"Errore connessione AMQP nel thread consumer: {conn_err}")
                    self.connection_active = False
                    time.sleep(self.reconnect_delay)
                    
                except pika.exceptions.ConnectionClosedByBroker as close_err:
                    log_error(f"Connessione chiusa dal broker: {close_err}")
                    self.connection_active = False
                    time.sleep(self.reconnect_delay)
                    
                except pika.exceptions.StreamLostError as stream_err:
                    log_error(f"Stream perso: {stream_err}")
                    self.connection_active = False
                    time.sleep(self.reconnect_delay)
                    
                except Exception as e:
                    log_error(f"Errore non gestito nel thread consumer: {e}")
                    log_error(traceback.format_exc())
                    time.sleep(1)  # Breve pausa prima di continuare
            
            self._debug_log("Thread consumer terminato", level=1)
                
            # Chiudi la connessione quando il thread termina
            try:
                if self.connection and self.connection.is_open:
                    self.connection.close()
                    self._debug_log("Connessione chiusa correttamente", level=1)
            except Exception as close_err:
                log_error(f"Errore nella chiusura della connessione: {close_err}")
                log_error(traceback.format_exc())
        
        self.consumer_thread = threading.Thread(
            target=consume_messages, 
            name="dynamic_rabbit_consumer"
        )
        self.consumer_thread.daemon = True
        self.consumer_thread.start()
    
    def disconnect(self):
        """Chiude la connessione e ferma il consumer thread"""
        self._debug_log("Richiesta disconnessione", level=1)
        self.stop_event.set()
        self.connection_active = False
        
        # Attendi brevemente che il thread termini
        if self.consumer_thread and self.consumer_thread.is_alive():
            self._debug_log("In attesa che il thread consumer termini", level=2)
            time.sleep(0.5)
        
        # Chiudi la connessione se ancora aperta
        try:
            if self.connection and self.connection.is_open:
                self._debug_log("Chiusura connessione", level=1)
                self.connection.close()
        except Exception as e:
            log_error(f"Errore nella chiusura della connessione: {e}")
            log_error(traceback.format_exc())
        
        # Reset delle variabili
        self.connection = None
        self.channel = None
        self.consumer_thread = None
        self._debug_log("Disconnessione completata", level=1)
    
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
        
        # Aggiungi info sullo stato di connessione
        if self.connection_active:
            queues_list.append({
                'name': '_system/status',
                'messages': 1,
                'is_system': True
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
    # Log l'inizio del setup
    log_message({
        'queue': 'system',
        'body': f"Avvio configurazione consumer per {connection_config['host']}",
        'timestamp': datetime.now().isoformat()
    })
    
    # Crea il consumer
    consumer = DynamicQueueDiscover()
    
    # Tenta la connessione
    success = consumer.connect(connection_config)
    
    if success:
        # Log il successo
        log_message({
            'queue': 'system',
            'body': f"Consumer configurato con successo per {connection_config['host']}",
            'timestamp': datetime.now().isoformat()
        })
        
        # Aggiungi il riferimento al consumer nella configurazione
        connection_config['dynamic_consumer'] = consumer
    else:
        # Log il fallimento
        log_message({
            'queue': 'system',
            'body': f"Configurazione consumer fallita per {connection_config['host']}",
            'timestamp': datetime.now().isoformat()
        })
    
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