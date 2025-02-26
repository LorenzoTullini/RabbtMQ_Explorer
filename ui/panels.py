#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Componenti dell'interfaccia utente (pannelli, tabelle, ecc.)
"""
from rich.panel import Panel
from rich.table import Table
from rich import box

from config.connections import get_connections_list
from rabbitmq.queue_manager import get_queues
from utils.constants import get_active_connection, get_messages

def make_sidebar(selected_index=None):
    """
    Crea la sidebar con l'elenco delle connessioni disponibili.
    Evidenzia sia la connessione attiva che quella attualmente selezionata.
    
    Args:
        selected_index (int, optional): Indice della connessione selezionata. Defaults to None.
    
    Returns:
        Panel: Pannello con la sidebar
    """
    connections = get_connections_list()
    active_connection = get_active_connection()

    sidebar_table = Table(show_header=True, header_style="bold", box=box.SIMPLE)
    sidebar_table.add_column("#", justify="center", style="dim", width=3)
    sidebar_table.add_column("Nome", style="cyan")
    sidebar_table.add_column("Host", style="green")

    for i, conn in enumerate(connections, 1):
        name = conn.get("name", "Senza nome")
        host = f"{conn['host']}/{conn['vhost']}"

        # Stile predefinito
        style = ""

        # Evidenzia la connessione attiva in blu
        if active_connection and active_connection.get("id") == conn.get("id"):
            style = "bold white on blue"

        # Evidenzia la connessione selezionata (ma non attiva) in grigio
        if selected_index is not None and i - 1 == selected_index and not style:
            style = "bold white on grey23"

        # Applica stile, se presente
        if style:
            sidebar_table.add_row(f"[{style}]{i}[/]", f"[{style}]{name}[/]", f"[{style}]{host}[/]")
        else:
            sidebar_table.add_row(f"{i}", name, host)

    # Aggiungi opzione per nuova connessione
    if selected_index is not None and selected_index == len(connections):
        # Evidenzia "Nuova connessione" se selezionata
        sidebar_table.add_row("[bold white on grey23]N[/]", "[bold white on grey23]Nuova connessione[/]", "")
    else:
        sidebar_table.add_row("[bold green]N[/]", "[bold green]Nuova connessione[/]", "")

    sidebar_panel = Panel(
        sidebar_table,
        title="Connessioni RabbitMQ",
        border_style="blue",
        padding=(1, 2),
        expand=True
    )

    return sidebar_panel


def make_queue_list_panel(queues=None):
    """
    Crea un pannello con l'elenco delle code scoperte.
    
    Args:
        queues (list, optional): Lista delle code. Se None, le code vengono recuperate.
    
    Returns:
        Panel: Pannello con l'elenco delle code
    """
    if queues is None:
        active_connection = get_active_connection()
        if active_connection:
            queues = get_queues(active_connection)
        else:
            queues = []

    if not queues:
        return Panel("Nessuna coda scoperta. In attesa di messaggi...", 
                    title="Code Scoperte", 
                    style="magenta")

    queues_table = Table(box=box.SIMPLE)
    queues_table.add_column("Exchange/Routing Key", justify="left", style="bold white")
    queues_table.add_column("Messaggi", justify="right", style="cyan")

    for queue in queues:
        queue_name = queue.get("name", "Sconosciuta")
        message_count = queue.get("messages", 0)
        queues_table.add_row(queue_name, str(message_count))

    return Panel(queues_table, title="Code Scoperte", border_style="magenta", padding=(1, 2))


def make_messages_panel():
    """
    Crea un pannello con i messaggi ricevuti.
    
    Returns:
        Panel: Pannello con i messaggi ricevuti
    """
    messages = get_messages()

    if not messages:
        return Panel("In attesa di messaggi...", title="Messaggi Ricevuti", style="green")

    messages_content = ""
    for msg in reversed(messages):  # Ultimi messaggi in cima
        exchange = msg.get("exchange", "default")
        queue_name = msg.get("queue", "Sconosciuta")
        routing_key = msg.get("routing_key", "")
        body = msg.get("body", "")

        messages_content += f"[bold yellow]Da: {exchange}/{routing_key}[/]\n"
        messages_content += f"{body}\n"
        messages_content += "[dim]" + "-" * 50 + "[/]\n"

    return Panel(messages_content, title="Messaggi Ricevuti", style="green", padding=(1, 2))


def make_help_bar():
    """
    Crea una barra di aiuto con i comandi disponibili.
    
    Returns:
        Panel: Pannello con la barra di aiuto
    """
    help_text = "[bold white]Comandi:[/] "
    help_text += "[yellow]↑/↓[/] Naviga connessioni "
    help_text += "[yellow]ENTER[/] Seleziona "
    help_text += "[yellow]N[/] Nuova connessione "
    help_text += "[yellow]C[/] Pulisci messaggi "
    help_text += "[yellow]Q[/] Esci"

    return Panel(help_text, border_style="dim", padding=(0, 0))


def make_header_panel():
    """
    Crea un pannello di intestazione con informazioni sulla connessione attiva.
    
    Returns:
        Panel: Pannello di intestazione
    """
    active_connection = get_active_connection()
    
    if active_connection:
        header = f"[bold]Host:[/] {active_connection['host']} - [bold]VHost:[/] {active_connection['vhost']} - [bold]Modalità:[/] Scoperta Dinamica"
    else:
        header = "Nessuna connessione attiva"

    return Panel(header, title="Connessione Attiva", style="bold green")