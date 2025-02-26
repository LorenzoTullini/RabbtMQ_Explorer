#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Funzionalità di logging per l'applicazione
"""
import os
from datetime import datetime


def ensure_log_directory():
    """Crea la directory di log se non esiste"""
    log_dir = os.path.join(os.path.expanduser("~"), ".rmq_messages_log")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def log_message(message_data):
    """
    Registra un messaggio ricevuto nel file di log
    
    Args:
        message_data (dict): Dati del messaggio da registrare
    """
    try:
        log_dir = ensure_log_directory()
        log_file = os.path.join(log_dir, f"messages_{datetime.now().strftime('%Y%m%d')}.log")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n--- NUOVO MESSAGGIO: {datetime.now().isoformat()} ---\n")
            f.write(f"Coda: {message_data.get('queue', 'Sconosciuta')}\n")
            f.write(f"Routing Key: {message_data.get('routing_key', '')}\n")
            f.write(f"Proprietà: {message_data.get('properties', '')}\n")
            f.write(f"Corpo:\n{message_data.get('body', '')}\n")
    except Exception:
        # Ignoriamo errori di logging per non interrompere l'applicazione
        pass


def log_error(error_message):
    """
    Registra un errore nel file di log degli errori
    
    Args:
        error_message (str): Messaggio di errore da registrare
    """
    try:
        log_dir = ensure_log_directory()
        error_log = os.path.join(log_dir, "errors.log")
        
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"\n--- ERRORE: {datetime.now().isoformat()} ---\n")
            f.write(f"{error_message}\n")
    except Exception:
        # Ignoriamo errori di logging per non interrompere l'applicazione
        pass
