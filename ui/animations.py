#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Interface animations and visual effects
"""
import time
from rich.align import Align
from rich.panel import Panel
from rich.live import Live
from rich.console import Console

from utils.constants import set_live_instance


def boot_animation(duration=3):
    """
    Shows a fullscreen boot animation for 'duration' seconds.
    The screen displays a centered ASCII art and the title "LT Superstar".
    
    Args:
        duration (int): Animation duration in seconds
    """
    # ASCII art for the logo
    ascii_art = r"""
    ___ _________
|\ \ |\___     ___
\ \ \\|___ \ \_|
    \ \ \     \ \
    \ \ \____\ \
     \ \_______\ \__\
     \|_______|\|__|


        """.strip("\n")

    console = Console()
    start_time = time.time()
    
    with console.screen():
        with Live(screen=True, refresh_per_second=6) as live:
            set_live_instance(live)
            
            while time.time() - start_time < duration:
                # Create an animated effect on the "Connecting" status
                for i in range(4):
                    status = "Connecting" + "." * i
                    full_text = ascii_art + "\n\n" + status
                    
                    # Center both horizontally and vertically
                    aligned_text = Align.center(full_text, vertical="middle")
                    panel = Panel(
                        aligned_text,
                        title="[bold]LT Superstar[/bold]",
                        border_style="",
                        expand=True,
                    )
                    live.update(panel)
                    time.sleep(0.3)
                    
                    if time.time() - start_time >= duration:
                        break
    
    console.clear()


def show_status_message(message, title="STATUS", style="blue", duration=2):
    """
    Shows a temporary status message.
    
    Args:
        message (str): Message to display
        title (str): Panel title
        style (str): Style to apply
        duration (float): Message duration in seconds
    """
    from utils.constants import get_live_instance
    live = get_live_instance()
    if live:
        panel = Panel(message, title=title, style=style)
        live.update(panel)
        time.sleep(duration)