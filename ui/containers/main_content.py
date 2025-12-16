"""Main content container for the Study Notebook UI.

This module provides the MainContent component that manages the editor
TextField and content display area with theme-driven styling.
"""

from typing import Callable, Optional

import flet as ft
from ui.themes.theme import theme


class MainContent:
    """Manages the main content editor and display area.

    Attributes:
        file_content: Reference to the main content TextField.
        container: The main Container holding the content view.
    """

    def __init__(
        self, on_change: Optional[Callable[[Optional[ft.ControlEvent]], None]] = None
    ):
        """Initialize the MainContent component.

        Args:
            on_change: Optional callback function called when content changes.
                      Receives a ControlEvent as parameter.
        """
        self.file_content = ft.Ref[ft.TextField]()
        self.on_change = on_change

        # Initialize the TextField
        self.file_content.current = ft.TextField(
            value="",
            multiline=True,
            min_lines=theme["FILECONTENT_MIN_LINES"],
            max_lines=theme["FILECONTENT_MAX_LINES"],
            expand=True,
            border_radius=theme["BORDER_RADIUS"],
            bgcolor=theme["MAIN_CONTENT_BG"],
            color=theme["MAIN_CONTENT_COLOR"],
            text_size=theme["MAIN_CONTENT_FONT_SIZE"],
            text_align=ft.TextAlign.LEFT,
            on_change=self.on_change,
        )

        # Create the main container
        self.container = self._build_container()

    def _build_container(self) -> ft.Container:
        """Build the main content container.

        Returns:
            A Container holding the content view.
        """
        return ft.Container(
            expand=True,
            bgcolor=theme["MAIN_CONTENT_BG"],
            padding=theme["MAIN_CONTENT_PADDING"],
            margin=ft.Margin(0, theme["SPACING_XS"], 0, 0),
            border_radius=theme["BORDER_RADIUS"],
        )

    def get_view(self, file_name: str = "") -> ft.Container:
        """Get the content view for a specific file.

        Args:
            file_name: The name of the currently open file.
                      If empty, returns an empty container.

        Returns:
            A Container with either content or empty state.
        """
        if not file_name:
            # Empty container when no file is open
            return ft.Container(
                expand=True,
                bgcolor=theme["MAIN_CONTENT_BG"],
                padding=theme["MAIN_CONTENT_PADDING"],
                margin=theme.get("MAIN_CONTENT_MARGIN", theme["SPACING_XS"]),
                border_radius=theme["BORDER_RADIUS"],
                content=ft.Container(expand=True),
            )

        # Content view with editor
        return ft.Container(
            content=self.file_content.current,
            expand=True,
            bgcolor=theme["MAIN_CONTENT_BG"],
            padding=theme["MAIN_CONTENT_PADDING"],
            margin=ft.Margin(0, theme["SPACING_XS"], 0, 0),
            border_radius=theme["BORDER_RADIUS"],
        )

    def set_content(self, content: str):
        """Set the content of the editor.

        Args:
            content: The content string to display.
        """
        if self.file_content.current:
            self.file_content.current.value = content

    def get_content(self) -> str:
        """Get the current content of the editor.

        Returns:
            The current content string.
        """
        if self.file_content.current:
            return self.file_content.current.value or ""
        return ""

    def update(self):
        """Update the content view."""
        if self.file_content.current and hasattr(self.file_content.current, "page"):
            if self.file_content.current.page is not None:
                self.file_content.current.update()
