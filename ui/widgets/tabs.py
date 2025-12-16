"""Tabs Bar component for the Study Notebook UI.

This module provides the TabsBar component that manages tab rendering,
selection, and closure with theme-driven styling.
"""

from typing import Callable, List

import flet as ft
from ui.themes.theme import theme


class TabsBar:
    """Manages the tabs bar UI and state.

    Attributes:
        open_tabs: List of tuples (folder, filename) representing open tabs.
        selected_idx: Reference list with single element indicating selected tab.
        on_select_tab: Callback function for tab selection.
        on_close_tab: Callback function for tab closure.
        on_new_tab: Callback function for new tab creation.
        container: The main Container holding the tab row.
    """

    def __init__(
        self,
        open_tabs: List,
        selected_idx: List,
        on_select_tab: Callable[[int], None],
        on_close_tab: Callable[[int], None],
        on_new_tab: Callable[[], None],
    ):
        """Initialize the TabsBar.

        Args:
            open_tabs: List of (folder, filename) tuples.
            selected_idx: List with single element: current tab index.
            on_select_tab: Callback called with tab index on selection.
            on_close_tab: Callback called with tab index on close.
            on_new_tab: Callback called when new tab button is clicked.
        """
        self.open_tabs = open_tabs
        self.selected_idx = selected_idx
        self.on_select_tab = on_select_tab
        self.on_close_tab = on_close_tab
        self.on_new_tab = on_new_tab

        # Create the tab row container
        self.tab_row = ft.Row(
            [],
            alignment=theme.get("TAB_ROW_ALIGNMENT", ft.MainAxisAlignment.START),
            spacing=theme.get("TAB_ROW_SPACING", theme["SPACING_XS"]),
            height=theme["TAB_ROW_HEIGHT"],
            scroll=ft.ScrollMode.AUTO,
        )

        self.container = ft.Container(
            content=self.tab_row,
            bgcolor=None,
            padding=theme.get("TAB_ROW_PADDING"),
            expand=False,
        )

    def build_tab_controls(self) -> list:
        """Build the list of tab controls including the + button.

        Returns:
            List of Container controls representing tabs and the add button.
        """
        tab_controls = []

        # Guard: ensure selected_idx[0] is valid
        if self.open_tabs:
            if self.selected_idx[0] < 0 or self.selected_idx[0] >= len(self.open_tabs):
                self.selected_idx[0] = 0
        else:
            self.selected_idx[0] = -1

        # Build individual tab containers
        for idx, (folder, fn) in enumerate(self.open_tabs):
            is_selected = idx == self.selected_idx[0]

            tab_controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                fn,
                                size=theme["TAB_FONT_SIZE"],
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                tooltip=fn,
                                width=theme.get("TAB_MIN_WIDTH"),
                                color=(
                                    theme["SIDEBAR_HIGHLIGHT_COLOR"]
                                    if is_selected
                                    else theme["SIDEBAR_ITEM_COLOR"]
                                ),
                                weight=(
                                    theme["SIDEBAR_HIGHLIGHT_WEIGHT"]
                                    if is_selected
                                    else None
                                ),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                tooltip="Close tab",
                                on_click=lambda e, i=idx: self.on_close_tab(i),
                                icon_size=theme["ICON_SIZE_SM"],
                                style=ft.ButtonStyle(
                                    padding=theme["TAB_CLOSE_BTN_PADDING"],
                                    shape=None,
                                ),
                            ),
                        ],
                        spacing=theme["ZERO_SPACING"],
                    ),
                    bgcolor=(
                        theme["SIDEBAR_HIGHLIGHT_BG"]
                        if is_selected
                        else theme["COLOR_BG_LIGHT"]
                    ),
                    padding=ft.Padding(*theme["TAB_CONTAINER_PADDING"]),
                    border_radius=theme["BORDER_RADIUS"],
                    on_click=lambda e, i=idx: self.on_select_tab(i),
                    margin=ft.Margin(
                        left=theme["TAB_CONTAINER_MARGIN"][0],
                        top=theme["TAB_CONTAINER_MARGIN"][1],
                        right=theme["TAB_CONTAINER_MARGIN"][2],
                        bottom=theme["TAB_CONTAINER_MARGIN"][3],
                    ),
                )
            )

        # Add the + button
        tab_controls.append(
            ft.Container(
                content=ft.IconButton(
                    icon=ft.Icons.ADD,
                    tooltip="New tab",
                    on_click=lambda e: self.on_new_tab(),
                    icon_size=theme["ICON_SIZE_LG"],
                    alignment=ft.alignment.center,
                    padding=theme["TAB_PLUS_PADDING"],
                ),
                width=theme["ICON_SIZE_XL"],
                height=theme["ICON_SIZE_XL"],
                padding=ft.Padding(
                    theme["TAB_PLUS_PADDING"],
                    theme["TAB_PLUS_PADDING"],
                    theme["TAB_PLUS_PADDING"],
                    theme["TAB_PLUS_PADDING"],
                ),
                border_radius=theme["ICON_SIZE_XL"] // 2,
                margin=ft.Margin(
                    theme["TAB_PLUS_MARGIN"],
                    theme["TAB_PLUS_MARGIN"],
                    theme["TAB_PLUS_MARGIN"],
                    theme["TAB_PLUS_MARGIN"],
                ),
                alignment=ft.alignment.center,
            )
        )

        # Layout guard: always at least one visible control
        if not tab_controls:
            tab_controls.append(ft.Container(expand=True))

        return tab_controls

    def update(self):
        """Update the tab row with current tab state.

        This method rebuilds and displays all tabs based on open_tabs
        and selected_idx state.
        """
        tab_controls = self.build_tab_controls()
        # Use slice assignment to update Row controls
        self.tab_row.controls[:] = tab_controls
        self.tab_row.update()
