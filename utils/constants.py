#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Application constants and global variables
"""

# Global variables initialized as None
ACTIVE_CONNECTION = None
CURRENT_MESSAGES = []
MAX_MESSAGES = 100  # Maximum number of messages to keep in memory
LIVE_INSTANCE = None  # Live instance for UI updates from callbacks
SELECTED_INDEX = 0  # Global selected index for UI updates


def initialize_globals():
    """Initialize global variables with default values"""
    global ACTIVE_CONNECTION, CURRENT_MESSAGES
    ACTIVE_CONNECTION = None
    CURRENT_MESSAGES = []
    # Note: We don't reset CONNECTIONS_LIST here as it's managed in connections.py


def set_live_instance(live):
    """Set the global Live instance"""
    global LIVE_INSTANCE
    LIVE_INSTANCE = live


def get_live_instance():
    """Return the global Live instance"""
    return LIVE_INSTANCE


def set_selected_index(index):
    """Set the global selected index"""
    global SELECTED_INDEX
    SELECTED_INDEX = index


def get_selected_index():
    """Return the global selected index"""
    return SELECTED_INDEX


def set_active_connection(connection):
    """Set the global active connection"""
    global ACTIVE_CONNECTION
    ACTIVE_CONNECTION = connection


def get_active_connection():
    """Return the global active connection"""
    return ACTIVE_CONNECTION


# Removed connection list functions since they're now in connections.py

def add_message(message):
    """Add a message to the current messages list"""
    global CURRENT_MESSAGES
    CURRENT_MESSAGES.append(message)
    if len(CURRENT_MESSAGES) > MAX_MESSAGES:
        CURRENT_MESSAGES = CURRENT_MESSAGES[-MAX_MESSAGES:]


def get_messages():
    """Return the list of current messages"""
    return CURRENT_MESSAGES


def clear_messages():
    """Clear the list of current messages"""
    global CURRENT_MESSAGES
    CURRENT_MESSAGES = []