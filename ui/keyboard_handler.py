#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gestione degli input da tastiera
"""
import keyboard
from rich.console import Console

from config.connections import add_new_connection, get_connections_config, get_connections_list
from rabbitmq.connection import run_consumer_for_connection
from ui.layouts import create_full_layout
from utils.constants import set_selected_index, get_selected_index
from utils.constants import get_active_connection, clear_messages
from utils.logger import log_message

console = Console()


def handle_keyboard_events(live, connections, selected_index):
    """
    Gestisce gli eventi della tastiera nel loop principale.
    
    Args:
        live (Live): Istanza di Live per l'aggiornamento dell'interfaccia
        connections (list): Lista delle connessioni disponibili
        selected_index (int): Indice iniziale selezionato
    """
    set_selected_index(selected_index)
    
    # Registra i callback per gli eventi tastiera
    def on_key_up(e):
        if e.event_type == keyboard.KEY_DOWN:  # Rispondi solo all'evento KEY_DOWN
            current_index = get_selected_index()
            connections = get_connections_list()
            # Seleziona il precedente (muovi in su)
            if current_index > 0:
                new_index = current_index - 1
            else:
                new_index = len(connections)  # Vai all'ultima opzione (Nuova connessione)
            
            set_selected_index(new_index)
            live.update(create_full_layout(new_index))
    
    def on_key_down(e):
        if e.event_type == keyboard.KEY_DOWN:  # Rispondi solo all'evento KEY_DOWN
            current_index = get_selected_index()
            connections = get_connections_list()
            # Seleziona il successivo (muovi in giù)
            if current_index < len(connections):
                new_index = current_index + 1
            else:
                new_index = 0  # Torna alla prima connessione
                
            set_selected_index(new_index)
            live.update(create_full_layout(new_index))
    
    def on_enter(e):
        if e.event_type == keyboard.KEY_DOWN:  # Rispondi solo all'evento KEY_DOWN
            current_index = get_selected_index()
            connections = get_connections_list()
            
            # Se è l'ultima opzione, crea una nuova connessione
            if current_index == len(connections):
                live.stop()
                console.clear()
                new_connection = add_new_connection()
                console.clear()
                live.start()
                
                connections = get_connections_config()  # Ricarica le connessioni
                set_selected_index(len(connections) - 1)  # Seleziona la nuova connessione
                live.update(create_full_layout(len(connections) - 1))
                
                if new_connection:
                    # Attiva la nuova connessione
                    run_consumer_for_connection(new_connection, live)
            else:
                # Altrimenti, connettiti alla connessione selezionata
                if current_index < len(connections):
                    run_consumer_for_connection(connections[current_index], live)
    
    def on_new(e):
        if e.event_type == keyboard.KEY_DOWN:  # Rispondi solo all'evento KEY_DOWN
            # Crea una nuova connessione
            live.stop()
            console.clear()
            new_connection = add_new_connection()
            console.clear()
            live.start()
            
            connections = get_connections_config()  # Ricarica le connessioni
            set_selected_index(len(connections) - 1)  # Seleziona la nuova connessione
            live.update(create_full_layout(len(connections) - 1))
            
            if new_connection:
                run_consumer_for_connection(new_connection, live)
    
    def on_clear(e):
        if e.event_type == keyboard.KEY_DOWN:  # Rispondi solo all'evento KEY_DOWN
            # Pulisci i messaggi per la connessione attiva
            active_connection = get_active_connection()
            if active_connection:
                clear_messages()
                live.update(create_full_layout(get_selected_index()))
                log_message({
                    'queue': 'system',
                    'body': "Messaggi cancellati dall'utente",
                    'timestamp': None
                })
    
    # Rimuovi eventuali hotkey esistenti per evitare duplicati
    keyboard.unhook_all()
    
    # Registra i callback per gli eventi
    keyboard.hook_key('up', on_key_up)
    keyboard.hook_key('down', on_key_down)
    keyboard.hook_key('enter', on_enter) 
    keyboard.hook_key('n', on_new)
    keyboard.hook_key('c', on_clear)
    
    # Non è necessario registrare 'q' qui poiché verrà gestito direttamente nel loop principale