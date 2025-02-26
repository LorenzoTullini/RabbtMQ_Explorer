#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gestione delle configurazioni di connessione
"""
import os
import json
import getpass
import uuid
from datetime import datetime

from rich.console import Console
from rich.panel import Panel

# Import from relative paths instead of absolute paths
# Removed circular import: from config.connections import update_connection_last_used

# Global variables for connection management
CONNECTIONS_LIST = []

def set_connections_list(connections):
    """Set the global connections list"""
    global CONNECTIONS_LIST
    CONNECTIONS_LIST = connections


def get_connections_list():
    """Return the global connections list"""
    return CONNECTIONS_LIST


def get_connections_config():
    """
    Recupera le configurazioni delle connessioni da un file nascosto nella home dell'utente.
    Ritorna una lista di dizionari con i dettagli di ogni connessione.
    """
    console = Console()
    config_path = os.path.join(os.path.expanduser("~"), ".rmq_connections_config")

    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                connections = json.load(f)
            
            # Aggiorna la variabile globale
            set_connections_list(connections)
            return connections
        except Exception as e:
            console.print(
                Panel(
                    f"Errore nella lettura del file di configurazione:\n{e}",
                    title="ERROR",
                    style="red",
                )
            )
            return []
    else:
        return []


def save_connections_config(connections):
    """
    Salva le configurazioni delle connessioni in un file nascosto nella home dell'utente.
    
    Args:
        connections (list): Lista di dizionari con le configurazioni di connessione
    """
    console = Console()
    config_path = os.path.join(os.path.expanduser("~"), ".rmq_connections_config")

    try:
        with open(config_path, "w") as f:
            json.dump(connections, f)
        
        # Aggiorna la variabile globale
        set_connections_list(connections)
        
        # Imposta i permessi a 600 (solo lettura/scrittura per il proprietario)
        try:
            os.chmod(config_path, 0o600)
        except Exception as e:
            console.print(
                Panel(
                    f"Non è stato possibile impostare i permessi per il file di configurazione:\n{e}",
                    title="WARNING",
                    style="yellow",
                )
            )
    except Exception as e:
        console.print(
            Panel(
                f"Errore nel salvataggio del file di configurazione:\n{e}",
                title="ERROR",
                style="red",
            )
        )


def add_new_connection():
    """
    Aggiunge una nuova configurazione di connessione.
    Ritorna un dizionario con i dettagli della nuova connessione.
    """
    console = Console()
    console.print(
        Panel(
            "Configurazione - Inserisci i dettagli di RabbitMQ",
            title="Nuova Connessione",
            style="bold blue",
        )
    )
    
    name = input("Inserisci un nome per questa connessione: ").strip()
    host = input("Inserisci RabbitMQ Host [localhost]: ").strip() or "localhost"
    user = input("Inserisci RabbitMQ User: ").strip()
    password = getpass.getpass("Inserisci RabbitMQ Password: ").strip()
    vhost = input("Inserisci RabbitMQ VHost [/]: ").strip() or "/"

    connection_id = str(uuid.uuid4())
    connection = {
        "id": connection_id,
        "name": name,
        "host": host,
        "user": user,
        "password": password,
        "vhost": vhost,
        "last_used": datetime.now().isoformat()
    }

    connections = get_connections_config()
    connections.append(connection)
    save_connections_config(connections)

    return connection


def update_connection_last_used(connection):
    """
    Aggiorna la data di ultimo utilizzo della connessione.
    
    Args:
        connection (dict): Configurazione di connessione da aggiornare
    """
    connections = get_connections_list()
    
    # Aggiorna la data di ultimo utilizzo
    connection["last_used"] = datetime.now().isoformat()
    
    # Aggiorna la connessione nella lista
    updated = False
    for i, conn in enumerate(connections):
        if conn.get("id") == connection.get("id"):
            connections[i] = connection
            updated = True
            break
    
    if updated:
        save_connections_config(connections)