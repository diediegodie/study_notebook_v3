"""Header and Footer components for the Study Notebook UI.

This module provides reusable header and footer components that accept
theme configuration and event callbacks.
"""

from typing import Any, Callable, Optional

import flet as ft
from ui.themes.theme import theme


def build_header(
    page: ft.Page,
    on_minimize: Callable[[Any], None],
    on_maximize: Callable[[Any], None],
    on_close: Callable[[Any], None],
    on_half_size: Callable[[Any], None],
    on_search_change: Optional[Callable[[Any], None]] = None,
) -> ft.Container:
    """Build the header component with window controls and search.

    The header includes:
    - Window control buttons (minimize, maximize, close)
    - Half-size toggle button
    - Search field
    - Placeholder controls for visual balance

    Args:
        page: The Flet page instance.
        on_minimize: Callback for minimize button click.
        on_maximize: Callback for maximize button click.
        on_close: Callback for close button click.
        on_half_size: Callback for half-size toggle button click.
        on_search_change: Optional callback for search field changes.

    Returns:
        A Container representing the complete header with all controls.
    """
    from ui.widgets.window_controls import (
        build_window_controls_row,
        build_half_size_button,
        build_half_size_button_placeholder,
        build_window_controls_placeholder,
    )

    # Build actual window controls
    window_controls = build_window_controls_row(
        on_minimize=on_minimize,
        on_maximize=on_maximize,
        on_close=on_close,
    )

    # Build placeholder controls for visual balance
    window_controls_placeholder = build_window_controls_placeholder(
        opacity=theme["PLACEHOLDER_OPACITY"]
    )

    # Build half-size buttons
    half_size_button = build_half_size_button(on_click=on_half_size)
    half_size_button_placeholder = build_half_size_button_placeholder()

    # Search field
    search_field = ft.TextField(
        hint_text=theme["SEARCH_HINT"],
        width=theme["SEARCH_WIDTH"],
        bgcolor=theme["SEARCH_BG"],
        border_color=theme["SEARCH_BORDER_COLOR"],
        color=theme["SEARCH_COLOR"],
        border_radius=theme["SEARCH_BORDER_RADIUS"],
        filled=theme["SEARCH_FILLED"],
        text_align=theme["SEARCH_TEXT_ALIGN"],
        text_size=theme["SEARCH_FONT_SIZE"],
        text_vertical_align=theme["SEARCH_TEXT_VERTICAL_ALIGN"],
        on_change=on_search_change,
    )

    # Left cluster (placeholder for future alignment)
    left_cluster = ft.Container(
        expand=1,
        padding=ft.Padding(theme["HEADER_PADDING"], 0, 0, 0),
        content=ft.Row(
            [
                half_size_button_placeholder,
                window_controls_placeholder,
            ],
            spacing=theme["SPACING_SM"],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.START,
        ),
    )

    # Right cluster (actual controls)
    right_cluster = ft.Container(
        expand=1,
        padding=ft.Padding(0, 0, theme["WINDOW_CONTROL_EDGE_PADDING"], 0),
        content=ft.Row(
            [
                half_size_button,
                window_controls,
            ],
            spacing=theme["SPACING_SM"],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.END,
        ),
    )

    # Compose header
    header = ft.Container(
        content=ft.Row(
            [
                left_cluster,
                ft.Container(
                    content=search_field,
                    alignment=ft.alignment.center,
                    padding=ft.Padding(theme["SPACING_SM"], 0, theme["SPACING_SM"], 0),
                ),
                right_cluster,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=theme["SPACING_LG"],
        ),
        padding=ft.Padding(
            theme["HEADER_PADDING"],
            theme["HEADER_PADDING"],
            0,
            theme["HEADER_PADDING"],
        ),
        bgcolor=theme["HEADER_BG"],
        alignment=theme["HEADER_ALIGNMENT"],
        height=theme["HEADER_HEIGHT"],
        border_radius=theme["BORDER_RADIUS"],
    )

    return header


def build_footer() -> ft.Container:
    """Build the footer component.

    Returns:
        A Container representing the application footer with text.
    """
    footer = ft.Container(
        content=ft.Text(
            theme["FOOTER_TEXT"],
            size=theme["FOOTER_FONT_SIZE"],
            color=theme["FOOTER_COLOR"],
        ),
        padding=theme["FOOTER_PADDING"],
        bgcolor=theme["FOOTER_BG"],
        alignment=theme["FOOTER_ALIGNMENT"],
        height=theme["FOOTER_HEIGHT"],
        border_radius=theme["BORDER_RADIUS"],
    )

    return footer
