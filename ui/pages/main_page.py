import flet as ft
from ui.themes.theme import theme
import sys

sys.path.append("../../backend")
from backend.files_manager import FOLDERS, read_markdown_file, save_markdown_file


def main_page(page: ft.Page):
    page.title = "Study Notebook"
    page.bgcolor = theme["COLOR_BG_LIGHT"]
    page.vertical_alignment = ft.MainAxisAlignment.START

    # State for tabs and file content
    open_tabs = []  # List of (folder, filename) tuples
    file_content = ft.Ref[ft.TextField]()
    file_name = ft.Ref[str]()
    file_folder = ft.Ref[str]()
    expanded_folders = {folder: True for folder in FOLDERS}

    # Track selected tab index (mutable for closures)
    selected_tab_idx = [0]

    def close_selected_tab(e=None):
        idx = selected_tab_idx[0]
        if open_tabs and idx < len(open_tabs):
            close_tab(idx)

    def new_tab():
        file_name.current = ""
        file_folder.current = ""
        file_content.current.value = ""
        if not open_tabs:
            selected_tab_idx[0] = -1
        update_tabs()
        main_content_view.update()

    def close_tab(index):
        if 0 <= index < len(open_tabs):
            open_tabs.pop(index)
            # If the closed tab is currently selected, select another tab
            if open_tabs:
                new_index = max(0, index - 1)
                folder, filename = open_tabs[new_index]
                file_name.current = filename
                file_folder.current = folder
                content = read_markdown_file(folder, filename)
                file_content.current.value = content
                selected_tab_idx[0] = new_index
            else:
                file_name.current = ""
                file_folder.current = ""
                file_content.current.value = ""
                selected_tab_idx[0] = -1
            update_tabs()
            main_content_view.update()

    def update_tabs():
        # Rebuild the custom tab row
        tab_controls = []
        for idx, (folder, fn) in enumerate(open_tabs):
            tab_controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(fn, size=theme["SIDEBAR_TITLE_FONT_SIZE"]),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            tooltip="Close tab",
                            on_click=lambda e, i=idx: close_tab(i),
                            icon_size=16,
                            style=ft.ButtonStyle(padding=0, shape=None),
                        ),
                    ], spacing=0),
                    bgcolor=theme["SIDEBAR_BG"] if idx != selected_tab_idx[0] else theme["MAIN_CONTENT_BG"],
                    padding=ft.Padding(8, 4, 8, 4),
                    border_radius=theme["BORDER_RADIUS"],
                    on_click=lambda e, i=idx: select_tab(i),
                    margin=ft.Margin(0, 0, 4, 0),
                )
            )
        # Add the + button
        tab_controls.append(
            ft.Container(
                content=ft.IconButton(
                    icon=ft.Icons.ADD,
                    tooltip="New tab",
                    on_click=lambda e: new_tab(),
                    icon_size=18,
                ),
                padding=ft.Padding(8, 4, 8, 4),
                border_radius=theme["BORDER_RADIUS"],
                margin=ft.Margin(0, 0, 4, 0),
            )
        )
        tab_row.controls = tab_controls
        tab_row.update()

    def open_file(folder, filename):
        tab = (folder, filename)
        if tab not in open_tabs:
            open_tabs.append(tab)
        file_name.current = filename or ""
        file_folder.current = folder or ""
        content = read_markdown_file(folder, filename)
        file_content.current.value = content
        selected_tab_idx[0] = open_tabs.index(tab)
        update_tabs()
        main_content_view.update()

    def select_tab(index):
        if 0 <= index < len(open_tabs):
            selected_tab_idx[0] = index
            folder, filename = open_tabs[index]
            file_name.current = filename or ""
            file_folder.current = folder or ""
            content = read_markdown_file(folder, filename)
            file_content.current.value = content
            update_tabs()
            main_content_view.update()

    header = ft.Container(
        content=ft.Row(
            [
                ft.TextField(
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
                )
            ],
            alignment=theme["HEADER_ROW_ALIGNMENT"],
        ),
        padding=theme["HEADER_PADDING"],
        bgcolor=theme["HEADER_BG"],
        alignment=theme["HEADER_ALIGNMENT"],
        height=theme["HEADER_HEIGHT"],
        border_radius=theme["BORDER_RADIUS"],
    )

    tab_row = ft.Row([], alignment=ft.MainAxisAlignment.START)

    file_content.current = ft.TextField(
        value="",
        multiline=True,
        min_lines=20,
        max_lines=40,
        expand=True,
        border_radius=theme["BORDER_RADIUS"],
        bgcolor=theme["MAIN_CONTENT_BG"],
        color=theme["MAIN_CONTENT_COLOR"],
        text_size=theme["MAIN_CONTENT_FONT_SIZE"],
        text_align=ft.TextAlign.LEFT,
    )

    import threading
    import time

    autosave_running = True

    def autosave_loop():
        last_content = None
        while autosave_running:
            if file_name.current and file_folder.current:
                current_content = file_content.current.value or ""
                if current_content != last_content:
                    save_markdown_file(
                        file_folder.current or "",
                        file_name.current or "",
                        current_content,
                    )
                    last_content = current_content
            time.sleep(2)

    autosave_thread = threading.Thread(target=autosave_loop, daemon=True)
    autosave_thread.start()

    main_content_view = ft.Container(
        content=ft.Column(
            [file_content.current],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        ),
        expand=True,
        bgcolor=theme["MAIN_CONTENT_BG"],
        padding=theme["MAIN_CONTENT_PADDING"],
        margin=theme["SPACING_XS"],
        border_radius=theme["BORDER_RADIUS"],
    )

    from ui.widgets.sidebar import sidebar


    page.add(
        header,
        tab_row,
        ft.Row(
            [
                sidebar(expanded_folders, on_file_selected=open_file),
                main_content_view,
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
            expand=True,
        ),
        ft.Container(
            content=ft.Text(
                "© 2025 Study Notebook - by Diego Rodriguez.",
                size=theme["FOOTER_FONT_SIZE"],
                color=theme["FOOTER_COLOR"],
            ),
            padding=theme["FOOTER_PADDING"],
            bgcolor=theme["FOOTER_BG"],
            alignment=theme["FOOTER_ALIGNMENT"],
            height=theme["FOOTER_HEIGHT"],
            border_radius=theme["BORDER_RADIUS"],
        ),
    )
    update_tabs()
