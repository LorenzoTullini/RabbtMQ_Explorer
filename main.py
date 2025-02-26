#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LT Superstar - Monitoraggio code RabbitMQ
Punto di ingresso dell'applicazione
"""
import sys
import time

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
from utils.constants import initialize_globals

from rich.live import Live
from rich.console import Console
from rich.panel import Panel
from rich.traceback import install


def main():
    """Funzione principale dell'applicazione."""
    # Inizializza variabili globali e configurazioni
    initialize_globals()
    
    # Abilita traceback avanzati per il debug
    install()
    console = Console()
    
    # Mostra la boot animation
    boot_animation(duration=3)
    
    # Mostra messaggio di benvenuto per la nuova versione con scoperta dinamica
    console.print(Panel(
        "LT Superstar - Versione con Scoperta Dinamica delle Code\n"
        "Questa versione non richiede l'accesso alla API Management di RabbitMQ.",
        title="Benvenuto",
        style="bold cyan"
    ))
    time.sleep(2)
    
    # Carica le connessioni salvate
    connections = get_connections_config()
    
    # Se non ci sono connessioni, chiede all'utente di crearne una nuova
    if not connections:
        console.print(Panel("Nessuna connessione salvata. Crea una nuova connessione.", style="cyan"))
        connection = add_new_connection()
        connections = get_connections_config()  # Ricarica le connessioni
    
    # Inizializza variabili di controllo per l'interfaccia
    selected_index = 0
    exit_app = False
    last_refresh_time = time.time()
    auto_refresh_interval = 1.0  # Aggiorna ogni secondo
    
    # Avvia l'interfaccia interattiva
    with Live(create_full_layout(selected_index), refresh_per_second=4, screen=True) as live:
        from utils.constants import set_live_instance
        set_live_instance(live)  # Imposta l'istanza live globalmente per l'uso nei callback
        
        # Importa il gestore tastiera
        from ui.keyboard_handler import handle_keyboard_events
        
        # Registra il gestore degli eventi della tastiera
        try:
            # handle_keyboard_events registra i callback per gli eventi tastiera
            handle_keyboard_events(live, connections, selected_index)
            
            # Loop principale che mantiene l'applicazione in esecuzione
            # Gli eventi della tastiera vengono gestiti dai callback registrati
            while True:
                # Aggiorna la schermata a intervalli regolari
                current_time = time.time()
                if current_time - last_refresh_time >= auto_refresh_interval:
                    live.update(create_full_layout(selected_index))
                    last_refresh_time = current_time
                
                # Pausa per ridurre l'utilizzo della CPU
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            # Gestisci uscita con Ctrl+C
            console.print("\nUscita dall'applicazione...")
        except Exception as e:
            console.print(f"\n[bold red]Errore non gestito:[/bold red] {str(e)}")
            raise


if __name__ == "__main__":
    main()