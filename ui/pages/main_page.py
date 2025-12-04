import flet as ft
from ui.themes.theme import theme
import sys

sys.path.append("../../backend")
from backend.files_manager import (
    read_markdown_file,
    save_markdown_file,
    list_markdown_files,
    list_folders,
    create_folder,
    delete_folder,
)


def main_page(page: ft.Page):
    def close_dialog(_):
        dialog.open = False
        page.update()

    page.title = "Study Notebook"
    page.bgcolor = theme["COLOR_BG_LIGHT"]
    page.vertical_alignment = ft.MainAxisAlignment.START

    # State for tabs and file content
    open_tabs = []  # List of (folder, filename) tuples
    file_content = ft.Ref[ft.TextField]()
    file_name = ft.Ref[str]()
    file_folder = ft.Ref[str]()
    expanded_folders = {folder: True for folder in list_folders()}
    selected_tab_idx = [0]

    # Dialog and snackbar controls
    snackbar_text = ft.Text("")
    snackbar = ft.SnackBar(
        content=snackbar_text, bgcolor=theme["COLOR_PRIMARY"], open=False
    )
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(""),
        content=ft.Column([], tight=True, spacing=theme["SPACING_MD"]),
        actions=[],
        actions_alignment=ft.MainAxisAlignment.END,
        open=False,
    )
    if page.controls is None:
        page.controls = []
    page.controls.append(snackbar)
    page.controls.append(dialog)

    def show_snackbar(message, color=None):
        snackbar_text.value = message
        snackbar.bgcolor = color or theme["COLOR_PRIMARY"]
        snackbar.open = True
        page.update()

    def show_create_file_dialog():
        filename_field = ft.TextField(
            label="Filename",
            hint_text="Enter filename (e.g. note.md)",
            autofocus=True,
            width=260,
        )
        folder_dropdown = ft.Dropdown(
            label="Folder",
            options=[ft.dropdown.Option(f) for f in list_folders()],
            value=(list_folders()[0] if list_folders() else None),
            width=180,
        )
        error_text = ft.Text("", color=theme["ERROR_COLOR"], size=theme["FONT_SIZE_SM"])

        def validate_and_create_file(_):
            fname = (filename_field.value or "").strip()
            folder = folder_dropdown.value
            if not folder:
                error_text.value = "A folder must be selected."
                dialog.update()
                return
            fname = fname.replace(" ", "_")
            if not fname:
                error_text.value = "Filename required."
                dialog.update()
                return
            if not fname.lower().endswith(".md"):
                fname += ".md"
            if folder not in list_folders():
                error_text.value = "Invalid folder."
                dialog.update()
                return
            files = list_markdown_files(folder)
            if fname in files:
                error_text.value = "File already exists."
                dialog.update()
                return
            if not folder:
                # This case should ideally not be hit if validation is done correctly
                return
            try:
                save_markdown_file(folder, fname, "")
            except Exception as ex:
                error_text.value = f"Error: {ex}"
                dialog.update()
                return
            tab = (folder, fname)
            open_tabs.append(tab)
            file_name.current = fname
            file_folder.current = folder
            file_content.current.value = ""
            selected_tab_idx[0] = len(open_tabs) - 1
            update_tabs()
            main_layout.controls[1] = get_main_content_view()
            main_layout.update()
            dialog.open = False
            page.update()
            show_snackbar(f"Created {fname} in {folder}", color=theme["SUCCESS_COLOR"])
            refresh_sidebar()

        dialog.title = ft.Text("Create New Note")
        dialog.content = ft.Column(
            [
                filename_field,
                folder_dropdown,
                error_text,
            ],
            tight=True,
            spacing=theme["SPACING_MD"],
        )
        dialog.actions = [
            ft.TextButton("Cancel", on_click=close_dialog),
            ft.TextButton("Create", on_click=validate_and_create_file),
        ]
        dialog.open = True
        page.update()

    def update_tabs():
        # Rebuild the custom tab row
        tab_controls = []
        for idx, (folder, fn) in enumerate(open_tabs):
            tab_controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(fn, size=theme["SIDEBAR_TITLE_FONT_SIZE"]),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                tooltip="Close tab",
                                on_click=lambda e, i=idx: close_tab(i),
                                icon_size=16,
                                style=ft.ButtonStyle(padding=0, shape=None),
                            ),
                        ],
                        spacing=0,
                    ),
                    bgcolor=(
                        theme["SIDEBAR_BG"]
                        if idx != selected_tab_idx[0]
                        else theme["MAIN_CONTENT_BG"]
                    ),
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
        main_layout.controls[1] = get_main_content_view()
        main_layout.update()

    def select_tab(index):
        if 0 <= index < len(open_tabs):
            selected_tab_idx[0] = index
            folder, filename = open_tabs[index]
            file_name.current = filename or ""
            file_folder.current = folder or ""
            content = read_markdown_file(folder, filename)
            file_content.current.value = content
            update_tabs()
            main_layout.controls[1] = get_main_content_view()
            main_layout.update()

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

    def get_main_content_view():
        if not file_name.current:
            return ft.Container(expand=True)  # Empty container when no file is open

        return ft.Container(
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

    main_content_view = get_main_content_view()

    from ui.widgets.sidebar import sidebar

    # Store sidebar container for real-time updates
    from ui.widgets.sidebar import sidebar as sidebar_component

    def on_delete_file(folder, filename):
        def do_delete_file(_):
            from backend.files_manager import delete_markdown_file

            try:
                delete_markdown_file(folder, filename)
                show_snackbar(
                    f"Deleted {filename} from {folder}", color=theme["SUCCESS_COLOR"]
                )
            except Exception as ex:
                show_snackbar(f"Error deleting file: {ex}", color=theme["ERROR_COLOR"])
            dialog.open = False
            refresh_sidebar()
            page.update()

        dialog.title = ft.Text("Delete File")
        dialog.content = ft.Text(
            f"Are you sure you want to delete '{filename}' from '{folder}'?"
        )
        dialog.actions = [
            ft.TextButton("Cancel", on_click=close_dialog),
            ft.TextButton(
                "Delete",
                on_click=do_delete_file,
                style=ft.ButtonStyle(bgcolor=theme["ERROR_COLOR"]),
            ),
        ]
        dialog.open = True
        page.update()

    def on_delete_folder(folder):
        def do_delete_folder(_):
            try:
                delete_folder(folder)
                show_snackbar(
                    f"Deleted folder '{folder}'", color=theme["SUCCESS_COLOR"]
                )
            except Exception as ex:
                show_snackbar(
                    f"Error deleting folder: {ex}", color=theme["ERROR_COLOR"]
                )
            dialog.open = False
            refresh_sidebar()
            page.update()

        dialog.title = ft.Text("Delete Folder")
        dialog.content = ft.Text(
            f"Are you sure you want to delete the folder '{folder}' and all its contents?"
        )
        dialog.actions = [
            ft.TextButton("Cancel", on_click=close_dialog),
            ft.TextButton(
                "Delete",
                on_click=do_delete_folder,
                style=ft.ButtonStyle(bgcolor=theme["ERROR_COLOR"]),
            ),
        ]
        dialog.open = True
        page.update()

    def show_create_folder_dialog(_=None):
        folder_name_field = ft.TextField(
            label="Folder Name",
            hint_text="Enter new folder name",
            autofocus=True,
            width=180,
        )
        error_text = ft.Text("", color=theme["ERROR_COLOR"], size=theme["FONT_SIZE_SM"])

        def validate_and_create_folder(_):
            name = (folder_name_field.value or "").strip()
            if not name:
                error_text.value = "Folder name required."
                dialog.update()
                return
            if name in list_folders():
                error_text.value = "Folder already exists."
                dialog.update()
                return
            try:
                create_folder(name)
            except Exception as ex:
                error_text.value = f"Error: {ex}"
                dialog.update()
                return
            dialog.open = False
            expanded_folders[name] = True
            refresh_sidebar()
            show_snackbar(f"Created folder '{name}'", color=theme["SUCCESS_COLOR"])

        dialog.title = ft.Text("Create Folder")
        dialog.content = ft.Column(
            [
                folder_name_field,
                error_text,
            ],
            tight=True,
            spacing=theme["SPACING_MD"],
        )
        dialog.actions = [
            ft.TextButton("Cancel", on_click=close_dialog),
            ft.TextButton("Create", on_click=validate_and_create_folder),
        ]
        dialog.open = True
        page.update()

    sidebar_container = ft.Container(
        content=sidebar_component(
            expanded_folders,
            on_file_selected=open_file,
            on_delete_file=on_delete_file,
            on_delete_folder=on_delete_folder,
            on_create_folder_dialog=show_create_folder_dialog,
        )
    )

    def refresh_sidebar():
        sidebar_container.content = sidebar_component(
            expanded_folders,
            on_file_selected=open_file,
            on_delete_file=on_delete_file,
            on_delete_folder=on_delete_folder,
            on_create_folder_dialog=show_create_folder_dialog,
        )
        sidebar_container.update()

    main_layout = ft.Row(
        [
            sidebar_container,
            main_content_view,
        ],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.START,
        expand=True,
    )

    page.add(
        header,
        tab_row,
        main_layout,
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
    # Initial sidebar build
    refresh_sidebar()
    update_tabs()

    def close_tab(idx):
        if 0 <= idx < len(open_tabs):
            open_tabs.pop(idx)
            if open_tabs:
                # Select previous tab if possible, else first tab
                new_index = max(0, selected_tab_idx[0] - 1)
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
            main_layout.controls[1] = get_main_content_view()
            main_layout.update()

    def new_tab():
        show_create_file_dialog()
