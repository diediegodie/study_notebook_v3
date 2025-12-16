"""Window state management for the Study Notebook UI.

This module provides the WindowState class that manages window sizing,
maximized state, and half-size toggle functionality with theme-driven
configuration.
"""

import flet as ft
from ui.themes.theme import theme


class WindowState:
    """Manages window size, maximize state, and snap behavior.

    Attributes:
        is_half_size: Boolean indicating if window is in half-size mode.
        is_maximized: Boolean indicating if window is maximized.
        normal_width: Width when window is in normal (non-maximized) state.
        normal_height: Height when window is in normal (non-maximized) state.
        max_height: Current maximum height (updated on resize).
        taskbar_offset: Vertical offset to account for OS taskbar.
    """

    def __init__(self):
        """Initialize the WindowState with theme-driven defaults."""
        self.is_half_size = False
        self.is_maximized = False
        self.normal_width = theme["NORMAL_WINDOW_WIDTH"]
        self.normal_height = theme["NORMAL_WINDOW_HEIGHT"]
        self.max_height = theme["SCREEN_HEIGHT_FULLHD"]
        self.taskbar_offset = theme["TASKBAR_OFFSET"]

    def on_window_resized(self, e: ft.WindowResizeEvent):
        """Handle window resize events.

        Updates max_height to track actual window height during resizing.

        Args:
            e: The WindowResizeEvent.
        """
        self.max_height = (
            e.page.window.height if hasattr(e, "page") else self.max_height
        )

    def toggle_maximize(self, page: ft.Page):
        """Toggle between maximized and normal window size.

        Args:
            page: The Flet page instance.
        """
        if self.is_maximized:
            # Restore to normal size
            page.window.maximized = False
            page.window.width = theme["NORMAL_WINDOW_WIDTH"]
            page.window.height = theme["NORMAL_WINDOW_HEIGHT"]
            self.is_maximized = False
            self.is_half_size = False
        else:
            # Maximize to Full HD
            page.window.maximized = True
            page.window.width = theme["SCREEN_WIDTH_FULLHD"]
            page.window.height = theme["SCREEN_HEIGHT_FULLHD"]
            self.is_maximized = True
            self.is_half_size = False

        page.update()

    def toggle_half_size(self, page: ft.Page):
        """Toggle between full/maximized size and half-size snap.

        When toggling to half-size, the window snaps to the left or right
        side of the screen based on current position. When expanding back,
        it restores to full width while maintaining current height.

        Args:
            page: The Flet page instance.
        """
        # Exit maximized mode if in it
        if self.is_maximized:
            page.window.maximized = False
            self.is_maximized = False

        # Prefer live window height to better match current display
        current_height = page.window.height or self.max_height

        if self.is_half_size:
            # Expand back to full size using current available height
            page.window.width = theme["SCREEN_WIDTH_FULLHD"]
            page.window.height = current_height
            self.is_half_size = False
        else:
            # Collapse to half size, subtract taskbar offset to prevent footer cutoff
            collapse_height = max(
                current_height - self.taskbar_offset,
                theme["MIN_COLLAPSE_HEIGHT"],
            )

            # Decide snap side based on current horizontal position
            screen_width = theme["SCREEN_WIDTH_FULLHD"]
            half_width = theme["SNAP_HALF_WIDTH"]
            current_left = page.window.left or 0
            target_left = (
                0 if current_left < (screen_width / 2) else screen_width - half_width
            )

            page.window.top = theme["WINDOW_TOP_SNAP"]
            page.window.left = target_left
            page.window.width = half_width
            page.window.height = collapse_height
            self.is_half_size = True

        page.update()

    def to_dict(self) -> dict:
        """Convert state to dictionary for serialization.

        Returns:
            Dictionary representation of the window state.
        """
        return {
            "is_half_size": self.is_half_size,
            "is_maximized": self.is_maximized,
            "normal_width": self.normal_width,
            "normal_height": self.normal_height,
            "max_height": self.max_height,
        }

    def from_dict(self, data: dict):
        """Restore state from dictionary.

        Args:
            data: Dictionary containing window state values.
        """
        self.is_half_size = data.get("is_half_size", False)
        self.is_maximized = data.get("is_maximized", False)
        self.normal_width = data.get("normal_width", theme["NORMAL_WINDOW_WIDTH"])
        self.normal_height = data.get("normal_height", theme["NORMAL_WINDOW_HEIGHT"])
        self.max_height = data.get("max_height", theme["SCREEN_HEIGHT_FULLHD"])
