#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
User interface layout
"""
from rich.layout import Layout
from rich.panel import Panel

from ui.panels import (
    make_sidebar, 
    make_queue_list_panel, 
    make_messages_panel, 
    make_help_bar, 
    make_header_panel
)

from utils.constants import get_active_connection
from rabbitmq.queue_manager import get_queues


def make_main_content():
    """
    Creates the main content with queue and message information.
    
    Returns:
        Layout: Layout with the main content
    """
    # Informational header
    header_panel = make_header_panel()
    
    # Queues panel
    active_connection = get_active_connection()
    queues_data = []
    if active_connection:
        queues_data = get_queues(active_connection)
    queues_panel = make_queue_list_panel(queues_data)
    
    # Messages panel
    messages_panel = make_messages_panel()
    
    # Main layout
    main_layout = Layout()
    main_layout.split_column(
        Layout(header_panel, size=3),
        Layout(queues_panel, size=10),
        Layout(messages_panel)
    )
    
    return main_layout


def create_full_layout(selected_index=None):
    """
    Creates the complete layout with sidebar, main content, and command bar.
    
    Args:
        selected_index (int, optional): Selected connection index. Defaults to None.
    
    Returns:
        Layout: Complete application layout
    """
    layout = Layout()
    
    # Split into two parts: main content and help bar
    layout.split_column(
        Layout(name="main_area", ratio=24),
        Layout(make_help_bar(), size=3, name="help_bar")
    )
    
    # Split the main area into sidebar and content
    layout["main_area"].split_row(
        Layout(make_sidebar(selected_index), name="sidebar", size=30),
        Layout(name="main")
    )
    
    if get_active_connection():
        layout["main_area"]["main"].update(make_main_content())
    else:
        layout["main_area"]["main"].update(
            Panel("Select a connection with ↑/↓ and press ENTER", title="Welcome", style="cyan"))
    
    return layout