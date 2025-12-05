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
    # noinspection PyUnresolvedReference
    # Variables defined later in this function scope
    def close_dialog(_):
        dialog.open = False
        page.update()

    def show_error(msg):
        snackbar_text.value = msg
        snackbar.bgcolor = theme["ERROR_COLOR"]
        snackbar.open = True
        page.update()

    def show_success(msg):
        snackbar_text.value = msg
        snackbar.bgcolor = theme["SUCCESS_COLOR"]
        snackbar.open = True
        page.update()

    def validate_folder_name(name, parent=None):
        if not name or not name.strip():
            return "Name cannot be empty."
        if parent:
            import os

            parent_path = os.path.join(
                os.path.dirname(__file__), "../../notebooks", parent
            )
            try:
                existing = (
                    os.listdir(parent_path) if os.path.exists(parent_path) else []
                )
            except:
                existing = []
            if name in existing:
                return "Folder already exists."
        else:
            if name in list_folders():
                return "Folder already exists."
        if any(c in name for c in '/\\:*?"<>|'):
            return "Invalid folder name."
        return None

    def validate_file_name(name, folder):
        if not name or not name.strip():
            return "Name cannot be empty."
        files = list_markdown_files(folder)
        if name.endswith(".md"):
            fname = name
        else:
            fname = name + ".md"
        if fname in files:
            return "File already exists."
        if any(c in name for c in '/\\:*?"<>|'):
            return "Invalid file name."
        return None

    def open_create_folder_dialog(parent=None):
        name_field = ft.TextField(
            width=200,
            label="Folder name",
            autofocus=True,
        )
        error_text = ft.Text("", color=theme["ERROR_COLOR"], size=12)

        def on_create(_):
            folder_name = name_field.value or ""
            err = validate_folder_name(folder_name, parent)
            if err:
                error_text.value = err
                page.update()
                return
            if parent:
                from backend.files_manager import create_subfolder

                create_subfolder(str(parent), str(folder_name))
            else:
                create_folder(str(folder_name))
            dialog.open = False
            show_success("Folder created.")
            expanded_folders[folder_name] = True
            refresh_sidebar()
            page.update()

        dialog.title = ft.Text("Create Folder")
        dialog.content = ft.Container(
            content=ft.Column([name_field, error_text], spacing=theme["SPACING_MD"]),
            width=theme.get("DIALOG_WIDTH"),
            height=theme.get("DIALOG_HEIGHT"),
            alignment=theme.get("DIALOG_ALIGNMENT"),
        )
        dialog.actions = [
            ft.TextButton("Cancel", on_click=close_dialog),
            ft.ElevatedButton(
                "Create", on_click=on_create, height=theme["BUTTON_HEIGHT"]
            ),
        ]
        dialog.open = True
        page.update()

    def open_create_file_dialog(folder):
        name_field = ft.TextField(
            width=200,
            label="File name",
            autofocus=True,
        )
        error_text = ft.Text("", color=theme["ERROR_COLOR"], size=12)

        def on_create(_):
            file_name = name_field.value or ""
            err = validate_file_name(file_name, folder)
            if err:
                error_text.value = err
                page.update()
                return
            from backend.files_manager import create_file

            create_file(str(folder), str(file_name))
            dialog.open = False
            show_success("File created.")
            refresh_sidebar()
            page.update()

        dialog.title = ft.Text(f"Create File in {folder}")
        dialog.content = ft.Container(
            content=ft.Column([name_field, error_text], spacing=theme["SPACING_MD"]),
            width=theme.get("DIALOG_WIDTH"),
            height=theme.get("DIALOG_HEIGHT"),
            alignment=theme.get("DIALOG_ALIGNMENT"),
        )
        dialog.actions = [
            ft.TextButton("Cancel", on_click=close_dialog),
            ft.ElevatedButton(
                "Create", on_click=on_create, height=theme["BUTTON_HEIGHT"]
            ),
        ]
        dialog.open = True
        page.update()

    # Set up page properties
    page.title = theme.get("APP_TITLE", "Study Notebook")
    page.bgcolor = theme["COLOR_BG_LIGHT"]
    page.padding = ft.Padding(
        theme["PAGE_PADDING_LEFT"],
        theme["PAGE_PADDING_TOP"],
        theme["PAGE_PADDING_RIGHT"],
        theme["PAGE_PADDING_BOTTOM"],
    )
    page.vertical_alignment = theme.get(
        "PAGE_VERTICAL_ALIGNMENT", ft.MainAxisAlignment.START
    )

    # State for tabs and file content
    from backend.app_state import save_app_state, load_app_state

    app_state = load_app_state()
    open_tabs = app_state.get("open_tabs", [])  # List of (folder, filename) tuples
    file_content = ft.Ref[ft.TextField]()
    file_name = ft.Ref[str]()
    file_folder = ft.Ref[str]()
    expanded_folders = {folder: False for folder in list_folders()}
    selected_tab_idx = [0]

    # Dialog and snackbar controls
    snackbar_text = ft.Text("")
    snackbar = ft.SnackBar(
        content=snackbar_text, bgcolor=theme["COLOR_PRIMARY"], open=False
    )
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(""),
        content=ft.Container(
            content=ft.Column([], tight=True, spacing=theme["SPACING_MD"]),
            width=theme.get("DIALOG_WIDTH"),
            height=theme.get("DIALOG_HEIGHT"),
            alignment=theme.get("DIALOG_ALIGNMENT"),
        ),
        actions=[],
        actions_alignment=theme.get(
            "DIALOG_ACTIONS_ALIGNMENT", ft.MainAxisAlignment.END
        ),
        open=False,
    )
    if not hasattr(page, "controls") or page.controls is None:
        page.controls = []
    else:
        page.controls.clear()
    page.controls.append(snackbar)
    page.controls.append(dialog)

    from ui.widgets.sidebar import sidebar

    def on_create_folder():
        open_create_folder_dialog(parent=None)

    def on_create_subfolder(parent):
        open_create_folder_dialog(parent=parent)

    def on_create_file(folder):
        open_create_file_dialog(folder)

    def show_snackbar(message, color=None):
        snackbar_text.value = message
        snackbar.bgcolor = color or theme["COLOR_PRIMARY"]
        snackbar.open = True
        page.update()

    def update_tabs():
        # Rebuild the custom tab row
        tab_controls = []
        # Guard: ensure selected_tab_idx[0] is valid
        if open_tabs:
            if selected_tab_idx[0] < 0 or selected_tab_idx[0] >= len(open_tabs):
                selected_tab_idx[0] = 0
        else:
            selected_tab_idx[0] = -1
        for idx, (folder, fn) in enumerate(open_tabs):
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
                                width=theme.get("TAB_MIN_WIDTH", 90),
                                color=(
                                    theme["SIDEBAR_HIGHLIGHT_COLOR"]
                                    if idx == selected_tab_idx[0]
                                    else theme["SIDEBAR_ITEM_COLOR"]
                                ),
                                weight=(
                                    theme["SIDEBAR_HIGHLIGHT_WEIGHT"]
                                    if idx == selected_tab_idx[0]
                                    else None
                                ),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                tooltip="Close tab",
                                on_click=lambda e, i=idx: close_tab(i),
                                icon_size=theme["ICON_SIZE_SM"],
                                style=ft.ButtonStyle(padding=0, shape=None),
                            ),
                        ],
                        spacing=0,
                    ),
                    bgcolor=(
                        theme["SIDEBAR_HIGHLIGHT_BG"]
                        if idx == selected_tab_idx[0]
                        else theme["COLOR_BG_LIGHT"]
                    ),
                    padding=ft.Padding(*theme["TAB_CONTAINER_PADDING"]),
                    border_radius=theme["BORDER_RADIUS"],
                    on_click=lambda e, i=idx: select_tab(i),
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
                    on_click=lambda e: new_tab(),
                    icon_size=theme["ICON_SIZE_LG"],
                    alignment=ft.alignment.center,
                    padding=0,
                ),
                width=theme["ICON_SIZE_XL"],
                height=theme["ICON_SIZE_XL"],
                padding=ft.Padding(0, 0, 0, 0),
                border_radius=theme["ICON_SIZE_XL"] // 2,
                margin=ft.Margin(0, 0, 0, 0),
                alignment=ft.alignment.center,
            )
        )
        # Layout guard: always at least one visible control
        if not tab_controls:
            tab_controls.append(ft.Container(expand=True))
        # Use slice assignment to update Row controls
        tab_row.content.controls[:] = tab_controls  # type: ignore
        tab_row.content.update()  # type: ignore
        main_layout.update()

    def open_file(folder, filename):
        instant_save()
        tab = (folder, filename)
        # Only add the tab if it does not already exist
        if tab not in open_tabs:
            open_tabs.append(tab)
            from backend.app_state import save_app_state

            save_app_state({"open_tabs": open_tabs})
        else:
            # If already exists, do not add again
            pass
        # Always set selected_tab_idx to the opened tab
        selected_tab_idx[0] = open_tabs.index(tab)
        file_name.current = filename or ""
        file_folder.current = folder or ""
        content = read_markdown_file(folder, filename)
        file_content.current.value = content
        if getattr(file_content.current, "page", None) is not None:
            file_content.current.update()
        update_tabs()
        main_column.controls[1] = get_main_content_view()
        if getattr(main_column, "page", None) is not None:
            main_column.update()
        # Ensure sidebar reflects the newly opened file immediately
        refresh_sidebar()

    def select_tab(index):
        instant_save()
        if 0 <= index < len(open_tabs):
            selected_tab_idx[0] = index
            folder, filename = open_tabs[index]
            file_name.current = filename or ""
            file_folder.current = folder or ""
            content = read_markdown_file(folder, filename)
            file_content.current.value = content
            if getattr(file_content.current, "page", None) is not None:
                file_content.current.update()
            update_tabs()
            main_column.controls[1] = get_main_content_view()
            if getattr(main_column, "page", None) is not None:
                main_column.update()
            # Update sidebar highlight on tab selection
            refresh_sidebar()

    header = ft.Container(
        content=ft.Row(
            [
                # Add more features here at the beginning as needed
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
                ),
            ],
            alignment=ft.MainAxisAlignment.END,
        ),
        padding=theme["HEADER_PADDING"],
        bgcolor=theme["HEADER_BG"],
        alignment=theme["HEADER_ALIGNMENT"],
        height=theme["HEADER_HEIGHT"],
        border_radius=theme["BORDER_RADIUS"],
    )

    tab_row = ft.Container(
        content=ft.Row(
            [],
            alignment=theme.get("TAB_ROW_ALIGNMENT", ft.MainAxisAlignment.START),
            spacing=theme["SPACING_XS"],
            height=theme["TAB_ROW_HEIGHT"],
            scroll=ft.ScrollMode.AUTO,
        ),
        bgcolor=None,
        padding=theme.get("TAB_ROW_PADDING"),
        expand=False,
    )
    # noinspection PyUnresolvedReference

    def instant_save(e=None):
        if file_name.current and file_folder.current:
            current_content = file_content.current.value or ""
            save_markdown_file(
                file_folder.current,
                file_name.current,
                current_content,
            )
        # Persist open tabs only
        save_app_state({"open_tabs": open_tabs})

    file_content.current = ft.TextField(
        value="",
        multiline=True,
        min_lines=1,
        max_lines=None,
        expand=True,
        border_radius=theme["BORDER_RADIUS"],
        bgcolor=theme["MAIN_CONTENT_BG"],
        color=theme["MAIN_CONTENT_COLOR"],
        text_size=theme["MAIN_CONTENT_FONT_SIZE"],
        text_align=ft.TextAlign.LEFT,
        on_change=instant_save,
    )

    def get_main_content_view():
        if not file_name.current:
            # Layout guard: always at least one visible control
            return ft.Container(
                expand=True,
                bgcolor=theme["MAIN_CONTENT_BG"],
                padding=theme["MAIN_CONTENT_PADDING"],
                margin=theme.get("MAIN_CONTENT_MARGIN", theme["SPACING_XS"]),
                border_radius=theme["BORDER_RADIUS"],
                content=ft.Container(expand=True),
            )  # Empty container when no file is open

        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=file_content.current,
                        expand=True,
                        border_radius=theme["BORDER_RADIUS"],
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            ),
            expand=True,
            bgcolor=theme["MAIN_CONTENT_BG"],
            padding=theme["MAIN_CONTENT_PADDING"],
            # Add top margin to avoid overlap with tab row
            margin=ft.Margin(0, theme["SPACING_XS"], 0, 0),
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
        dialog.content = ft.Container(
            content=ft.Text(
                f"Are you sure you want to delete '{filename}' from '{folder}'?"
            ),
            width=theme.get("DIALOG_WIDTH"),
            height=theme.get("DIALOG_HEIGHT"),
            alignment=theme.get("DIALOG_ALIGNMENT"),
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
        dialog.content = ft.Container(
            content=ft.Text(
                f"Are you sure you want to delete the folder '{folder}' and all its contents?"
            ),
            width=theme.get("DIALOG_WIDTH"),
            height=theme.get("DIALOG_HEIGHT"),
            alignment=theme.get("DIALOG_ALIGNMENT"),
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
            width=theme.get("FOLDER_NAME_FIELD_WIDTH", 180),
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
        dialog.content = ft.Container(
            content=ft.Column(
                [
                    folder_name_field,
                    error_text,
                ],
                tight=True,
                spacing=theme["SPACING_MD"],
            ),
            width=theme.get("DIALOG_WIDTH"),
            height=theme.get("DIALOG_HEIGHT"),
            alignment=theme.get("DIALOG_ALIGNMENT"),
        )
        dialog.actions = [
            ft.TextButton("Cancel", on_click=close_dialog),
            ft.TextButton("Create", on_click=validate_and_create_folder),
        ]
        dialog.open = True
        page.update()

    def on_toggle_folder(folder):
        expanded_folders[folder] = not expanded_folders.get(folder, False)
        refresh_sidebar()

    # Sidebar scrollable container
    def refresh_sidebar():
        sidebar_view.content = sidebar(
            expanded_folders=expanded_folders,
            on_file_selected=open_file,
            on_delete_file=on_delete_file,
            on_delete_folder=on_delete_folder,
            on_create_folder=on_create_folder,
            on_create_subfolder=on_create_subfolder,
            on_create_file=on_create_file,
            on_toggle_folder=on_toggle_folder,
            current_file=file_name.current,
            current_folder=file_folder.current,
        )
        sidebar_view.update()

    sidebar_view = ft.Container(
        content=sidebar(
            expanded_folders=expanded_folders,
            on_file_selected=open_file,
            on_delete_file=on_delete_file,
            on_delete_folder=on_delete_folder,
            on_create_folder=on_create_folder,
            on_create_subfolder=on_create_subfolder,
            on_create_file=on_create_file,
            on_toggle_folder=on_toggle_folder,
            current_file=file_name.current,
            current_folder=file_folder.current,
        ),
        width=theme.get("SIDEBAR_WIDTH", 250),
        expand=False,
        bgcolor=theme.get("SIDEBAR_BG", "#CCCCCC"),
        padding=theme.get("SIDEBAR_PADDING", 8),
        border_radius=theme.get("BORDER_RADIUS", 6),
    )

    main_column = ft.Column(
        [
            tab_row,
            main_content_view,
        ],
        spacing=0,
        expand=True,
    )

    main_layout = ft.Row(
        [
            sidebar_view,
            main_column,
        ],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.START,
        expand=True,
    )

    # Compose the page: header (top), main_layout (row), footer (bottom)
    page.add(
        header,
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
        instant_save()
        if 0 <= idx < len(open_tabs):
            open_tabs.pop(idx)
            from backend.app_state import save_app_state

            save_app_state({"open_tabs": open_tabs})
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
                if getattr(file_content.current, "page", None) is not None:
                    file_content.current.update()
                selected_tab_idx[0] = -1
            update_tabs()
            main_column.controls[1] = get_main_content_view()
            if getattr(main_column, "page", None) is not None:
                main_column.update()
            # Update sidebar highlight when closing tabs changes selection
            refresh_sidebar()

    def new_tab():
        # Create a new tab with file selection and creation
        if not list_folders():
            show_error("No folders available. Create a folder first.")
            return

        # Show file creation dialog with folder selection
        folder_dropdown = ft.Dropdown(
            width=200,
            options=[ft.dropdown.Option(f) for f in list_folders()],
            value=list_folders()[0],
            label="Select Folder",
        )
        filename_field = ft.TextField(
            width=200,
            label="File name",
            autofocus=True,
        )
        error_text = ft.Text("", color=theme["ERROR_COLOR"], size=12)

        def on_create_new_file(e):
            file_name_val = (filename_field.value or "").strip()
            folder = folder_dropdown.value
            # Validate folder selection
            if not folder or folder is None:
                error_text.value = "Please select a folder"
                dialog.update()
                return

            # Validate filename
            if not file_name_val:
                error_text.value = "Please enter a filename"
                dialog.update()
                return

            # Add .md extension if not present
            if not file_name_val.endswith(".md"):
                file_name_val += ".md"

            from backend.files_manager import create_file

            # Create file without the .md extension (create_file adds it)
            create_file(folder, file_name_val.replace(".md", ""))

            dialog.open = False
            open_file(folder, file_name_val)
            refresh_sidebar()
            page.update()

        dialog.title = ft.Text("Create New File")
        dialog.content = ft.Container(
            content=ft.Column(
                [folder_dropdown, filename_field, error_text],
                spacing=theme["SPACING_MD"],
            ),
            width=theme.get("DIALOG_WIDTH"),
            height=theme.get("DIALOG_HEIGHT"),
            alignment=theme.get("DIALOG_ALIGNMENT"),
        )
        dialog.actions = [
            ft.TextButton("Cancel", on_click=close_dialog),
            ft.ElevatedButton(
                "Create & Open",
                on_click=on_create_new_file,
                height=theme["BUTTON_HEIGHT"],
            ),
        ]
        dialog.open = True
        page.update()
