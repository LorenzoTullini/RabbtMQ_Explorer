#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gestione degli input da tastiera
"""
import time
import keyboard
import sys

from rich.console import Console

from config.connections import add_new_connection, get_connections_config, get_connections_list
from rabbitmq.connection import run_consumer_for_connection
from ui.layouts import create_full_layout
from utils.constants import set_selected_index, get_selected_index
from utils.constants import get_active_connection, clear_messages

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
    def on_key_up():
        current_index = get_selected_index()
        connections = get_connections_list()
        # Seleziona il precedente (muovi in su)
        if current_index > 0:
            new_index = current_index - 1
        else:
            new_index = len(connections)  # Vai all'ultima opzione (Nuova connessione)
        
        set_selected_index(new_index)
        live.update(create_full_layout(new_index))
    
    def on_key_down():
        current_index = get_selected_index()
        connections = get_connections_list()
        # Seleziona il successivo (muovi in giù)
        if current_index < len(connections):
            new_index = current_index + 1
        else:
            new_index = 0  # Torna alla prima connessione
            
        set_selected_index(new_index)
        live.update(create_full_layout(new_index))
    
    def on_enter():
        current_index = get_selected_index()
        connections = get_connections_list()
        
        # Se è l'ultima opzione, crea una nuova connessione
        if current_index == len(connections):
            new_connection = add_new_connection()
            connections = get_connections_config()  # Ricarica le connessioni
            set_selected_index(len(connections) - 1)  # Seleziona la nuova connessione
            live.update(create_full_layout(len(connections) - 1))
        else:
            # Altrimenti, connettiti alla connessione selezionata
            if current_index < len(connections):
                run_consumer_for_connection(connections[current_index], live)
    
    def on_new():
        # Crea una nuova connessione
        new_connection = add_new_connection()
        connections = get_connections_config()  # Ricarica le connessioni
        set_selected_index(len(connections) - 1)  # Seleziona la nuova connessione
        live.update(create_full_layout(len(connections) - 1))
    
    def on_clear():
        # Pulisci i messaggi per la connessione attiva
        active_connection = get_active_connection()
        if active_connection:
            clear_messages()
            live.update(create_full_layout(get_selected_index()))
    
    def on_quit():
        # Esci dall'applicazione in modo sicuro
        console.print("\nUscita dall'applicazione...")
        # Solleva l'eccezione per uscire dal loop principale
        raise KeyboardInterrupt()
    
    # Registra i callback per i tasti con gestione più sicura
    keyboard.add_hotkey('up', lambda: on_key_up())
    keyboard.add_hotkey('down', lambda: on_key_down())
    keyboard.add_hotkey('enter', lambda: on_enter())
    keyboard.add_hotkey('n', lambda: on_new())
    keyboard.add_hotkey('c', lambda: on_clear())
    keyboard.add_hotkey('q', lambda: on_quit())