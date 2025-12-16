"""Window control components for the Study Notebook UI.

This module provides reusable window control buttons (minimize, maximize,
close) and the half-size toggle button with theme-driven styling.
"""

from typing import Any, Callable

import flet as ft
from ui.themes.theme import theme


def build_window_control_button(
    color: str, tooltip: str, handler: Callable[[Any], None]
) -> ft.Container:
    """Build a single window control button.

    Args:
        color: Background color of the control button.
        tooltip: Tooltip text displayed on hover.
        handler: Click event handler function.

    Returns:
        A styled Container representing the window control button.
    """
    return ft.Container(
        width=theme["WINDOW_CONTROL_SIZE"],
        height=theme["WINDOW_CONTROL_SIZE"],
        bgcolor=color,
        border=ft.border.all(1, theme["WINDOW_CONTROL_BORDER_COLOR"]),
        border_radius=theme["WINDOW_CONTROL_SIZE"] // 2,
        ink=True,
        tooltip=tooltip,
        on_click=handler,
    )


def build_window_controls_row(
    on_minimize: Callable[[Any], None],
    on_maximize: Callable[[Any], None],
    on_close: Callable[[Any], None],
    opacity: float = 1.0,
) -> ft.Row:
    """Build the window control buttons row (minimize, maximize, close).

    Args:
        on_minimize: Callback for minimize button click.
        on_maximize: Callback for maximize button click.
        on_close: Callback for close button click.
        opacity: Opacity level for the controls (0.0 to 1.0).
                 Used for placeholder controls.

    Returns:
        A Row containing all window control buttons.
    """
    return ft.Row(
        [
            build_window_control_button(
                theme["WINDOW_CONTROL_MINIMIZE_BG"],
                "Minimize",
                on_minimize,
            ),
            build_window_control_button(
                theme["WINDOW_CONTROL_MAXIMIZE_BG"],
                "Maximize",
                on_maximize,
            ),
            build_window_control_button(
                theme["WINDOW_CONTROL_CLOSE_BG"],
                "Close",
                on_close,
            ),
        ],
        spacing=theme["WINDOW_CONTROL_SPACING"],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        opacity=opacity,
    )


def build_half_size_button(on_click: Callable[[Any], None]) -> ft.IconButton:
    """Build the half-size toggle button.

    Args:
        on_click: Callback function for button click.

    Returns:
        An IconButton for toggling half-size window mode.
    """
    return ft.IconButton(
        icon=ft.Icons.VERTICAL_SPLIT,
        tooltip="Toggle Half Size",
        on_click=on_click,
        icon_size=theme["FULLSCREEN_BTN_ICON_SIZE"],
        style=ft.ButtonStyle(
            padding=theme["FULLSCREEN_BTN_PADDING"],
            shape=ft.CircleBorder(),
        ),
    )


def build_half_size_button_placeholder() -> ft.IconButton:
    """Build a disabled placeholder half-size button for visual balance.

    Returns:
        A disabled IconButton used for layout spacing.
    """
    return ft.IconButton(
        icon=ft.Icons.VERTICAL_SPLIT,
        disabled=True,
        icon_size=theme["FULLSCREEN_BTN_ICON_SIZE"],
        opacity=theme["PLACEHOLDER_OPACITY"],
        style=ft.ButtonStyle(
            padding=theme["FULLSCREEN_BTN_PADDING"],
            shape=ft.CircleBorder(),
        ),
    )


def build_window_controls_placeholder(opacity: float = 1.0) -> ft.Row:
    """Build a placeholder window controls row for visual balance.

    Args:
        opacity: Opacity level for the placeholder controls.

    Returns:
        A Row with placeholder window control buttons.
    """
    return ft.Row(
        [
            ft.Container(
                width=theme["WINDOW_CONTROL_SIZE"],
                height=theme["WINDOW_CONTROL_SIZE"],
            ),
            ft.Container(
                width=theme["WINDOW_CONTROL_SIZE"],
                height=theme["WINDOW_CONTROL_SIZE"],
            ),
            ft.Container(
                width=theme["WINDOW_CONTROL_SIZE"],
                height=theme["WINDOW_CONTROL_SIZE"],
            ),
        ],
        spacing=theme["WINDOW_CONTROL_SPACING"],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        opacity=opacity,
    )
