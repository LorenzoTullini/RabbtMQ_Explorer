#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LT Superstar - Monitoraggio code RabbitMQ
Punto di ingresso dell'applicazione con gestione migliorata della connessione
"""
import sys
import time
import os
import traceback

try:
    import keyboard
except ImportError:
    print("Installazione del pacchetto keyboard...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "keyboard"])
    import keyboard

# Import dai moduli interni
from ui.animations import boot_animation
from ui.layouts import create_full_layout
from config.connections import get_connections_config, add_new_connection
from rabbitmq.connection import run_consumer_for_connection
from utils.constants import initialize_globals, get_active_connection, set_live_instance, get_selected_index
from utils.logger import log_message, log_error, ensure_log_directory

from rich.live import Live
from rich.console import Console
from rich.panel import Panel
from rich.traceback import install


def check_python_version():
    """Verifica la versione di Python e mostra un avviso se necessario."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 6):
        print("ATTENZIONE: Questa applicazione richiede Python 3.6 o superiore.")
        print(f"Versione attuale: {version.major}.{version.minor}.{version.micro}")
        print("Potrebbero verificarsi errori imprevisti.")
        input("Premi un tasto per continuare comunque...")


def setup_environment():
    """Configura l'ambiente di esecuzione."""
    # Pulizia log vecchi
    try:
        log_dir = ensure_log_directory()
        current_date = time.strftime('%Y%m%d')
        
        # Elimina log più vecchi di 7 giorni
        for filename in os.listdir(log_dir):
            if filename.startswith('messages_') and filename.endswith('.log'):
                file_date = filename[9:17]  # Estrae YYYYMMDD dal nome
                try:
                    # Verifica se il file è vecchio (più di 7 giorni)
                    if file_date != current_date and int(current_date) - int(file_date) > 7:
                        os.remove(os.path.join(log_dir, filename))
                except (ValueError, OSError):
                    pass  # Ignora errori di conversione o eliminazione
    except Exception as e:
        print(f"Errore nella pulizia dei log: {e}")


def main():
    """Funzione principale dell'applicazione."""
    # Verifica la versione di Python
    check_python_version()
    
    # Configura l'ambiente
    setup_environment()
    
    # Inizializza variabili globali e configurazioni
    initialize_globals()
    
    # Abilita traceback avanzati per il debug
    install(show_locals=True)
    console = Console()
    
    # Avvia il log dell'applicazione
    log_message({
        'queue': 'system',
        'body': f"Avvio applicazione RabbitMQ Explorer v2.0",
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })
    
    try:
        # Mostra la boot animation
        boot_animation(duration=2)
        
        # Mostra messaggio di benvenuto per la nuova versione con scoperta dinamica
        console.print(Panel(
            "LT Superstar - Versione con Scoperta Dinamica delle Code\n"
            "Questa versione non richiede l'accesso alla API Management di RabbitMQ.",
            title="Benvenuto",
            style="bold cyan"
        ))
        time.sleep(1)
        
        # Carica le connessioni salvate
        connections = get_connections_config()
        
        # Se non ci sono connessioni, chiede all'utente di crearne una nuova
        if not connections:
            console.print(Panel("Nessuna connessione salvata. Crea una nuova connessione.", style="cyan"))
            connection = add_new_connection()
            connections = get_connections_config()  # Ricarica le connessioni
        
        # Inizializza variabili di controllo per l'interfaccia
        selected_index = 0
        last_refresh_time = time.time()
        auto_refresh_interval = 1.0  # Aggiorna ogni secondo
        connection_status_check_interval = 5.0  # Controlla stato connessione ogni 5 secondi
        last_connection_check_time = time.time()
        
        # Avvia l'interfaccia interattiva
        with Live(create_full_layout(selected_index), refresh_per_second=4, screen=True) as live:
            # Imposta l'istanza live globalmente per l'uso nei callback
            set_live_instance(live)
            
            # Importa il gestore tastiera
            from ui.keyboard_handler import handle_keyboard_events
            
            # Registra il gestore degli eventi della tastiera
            handle_keyboard_events(live, connections, selected_index)
            
            try:
                # Loop principale dell'applicazione
                while True:
                    current_time = time.time()
                    
                    # Aggiorna la schermata a intervalli regolari
                    if current_time - last_refresh_time >= auto_refresh_interval:
                        live.update(create_full_layout(get_selected_index()))
                        last_refresh_time = current_time
                    
                    # Controlla lo stato della connessione a intervalli regolari
                    if current_time - last_connection_check_time >= connection_status_check_interval:
                        active_connection = get_active_connection()
                        if active_connection:
                            # Verifica se la connessione ha un consumer e se è attivo
                            consumer = active_connection.get('dynamic_consumer')
                            if consumer and hasattr(consumer, 'connection_active'):
                                if not consumer.connection_active:
                                    # La connessione è stata persa
                                    log_message({
                                        'queue': 'system',
                                        'body': "Rilevata perdita di connessione nel loop principale",
                                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                                    })
                                    
                                    # Notifica visivamente la perdita di connessione
                                    from ui.animations import show_status_message
                                    show_status_message(
                                        "Connessione persa. Seleziona nuovamente la connessione per riconnetterti.",
                                        title="DISCONNESSO",
                                        style="red",
                                        duration=2
                                    )
                                    
                                    # Reset della connessione attiva
                                    from utils.constants import set_active_connection
                                    set_active_connection(None)
                                    
                                    # Aggiorna l'interfaccia
                                    live.update(create_full_layout(get_selected_index()))
                        
                        last_connection_check_time = current_time
                    
                    # MODIFICA: Verifica direttamente i tasti premuti
                    if keyboard.is_pressed('q'):
                        print("\nUscita dall'applicazione...")
                        break
                    
                    # Evita utilizzo elevato della CPU
                    time.sleep(0.1)
                    
            except KeyboardInterrupt:
                # Gestisci uscita con Ctrl+C
                console.print("\nUscita dall'applicazione...")
            except Exception as e:
                # Log dettagliato dell'errore
                log_error(f"Errore non gestito nel loop principale: {e}")
                log_error(traceback.format_exc())
                console.print(f"\n[bold red]Errore non gestito:[/bold red] {str(e)}")
                raise
    
    except Exception as startup_error:
        # Gestisci errori durante l'avvio
        log_error(f"Errore durante l'avvio dell'applicazione: {startup_error}")
        log_error(traceback.format_exc())
        console.print(f"\n[bold red]Errore di avvio:[/bold red] {str(startup_error)}")
        raise
    
    finally:
        # Pulizia finale
        log_message({
            'queue': 'system',
            'body': "Chiusura applicazione",
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Chiudi eventuali connessioni attive
        try:
            active_connection = get_active_connection()
            if active_connection:
                consumer = active_connection.get('dynamic_consumer')
                if consumer and hasattr(consumer, 'disconnect'):
                    consumer.disconnect()
        except Exception as shutdown_error:
            log_error(f"Errore durante la chiusura: {shutdown_error}")


if __name__ == "__main__":
    main()