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
    # Sidebar scroll position preservation
    sidebar_column_ref = ft.Ref[ft.Column]()
    # Persistent scroll offset for sidebar
    prev_scroll_offset = 0
    # Global dialog reference for ESC handling
    current_dialog = None

    def esc_handler(e: ft.KeyboardEvent):
        nonlocal current_dialog
        if (
            e.key == "Escape"
            and current_dialog
            and getattr(current_dialog, "open", False)
        ):
            current_dialog.open = False
            page.update()

    page.on_keyboard_event = esc_handler

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
        nonlocal current_dialog
        current_dialog = dialog
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
        nonlocal current_dialog
        current_dialog = dialog
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

    # Deduplicate open_tabs and normalize folder paths (remove trailing slashes)
    def normalize_tab(tab):
        folder, filename = tab
        folder = folder.rstrip("/") if isinstance(folder, str) else folder
        return (folder, filename)

    open_tabs_raw = app_state.get("open_tabs", [])
    seen_tabs = set()
    open_tabs = []
    for tab in open_tabs_raw:
        norm_tab = normalize_tab(tab)
        if norm_tab not in seen_tabs:
            open_tabs.append(norm_tab)
            seen_tabs.add(norm_tab)
    # Save deduplicated state back
    from backend.app_state import save_app_state

    save_app_state({"open_tabs": open_tabs})
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
        tab = normalize_tab((folder, filename))
        # Only add the tab if it does not already exist
        if tab not in open_tabs:
            open_tabs.append(tab)
            save_app_state({"open_tabs": open_tabs})
        # Always set selected_tab_idx to the opened tab
        selected_tab_idx[0] = open_tabs.index(tab)
        file_name.current = tab[1] or ""
        file_folder.current = tab[0] or ""
        content = read_markdown_file(tab[0], tab[1])
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

    # Fullscreen toggle logic
    def toggle_fullscreen(e):
        page.window.full_screen = not page.window.full_screen
        page.update()

    fullscreen_icon = ft.Container(
        content=ft.IconButton(
            icon=ft.Icons.FULLSCREEN,
            tooltip="Toggle Fullscreen",
            on_click=toggle_fullscreen,
            icon_size=theme["FULLSCREEN_BTN_ICON_SIZE"],
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=theme["BORDER_RADIUS"]),
                bgcolor=theme["HEADER_BG"],
                icon_color=theme["SEARCH_COLOR"],
                padding=theme["FULLSCREEN_BTN_PADDING"],
            ),
        ),
        height=theme["FULLSCREEN_BTN_HEIGHT"],
        width=theme["FULLSCREEN_BTN_WIDTH"],
        alignment=ft.alignment.center,
    )

    header = ft.Container(
        content=ft.Row(
            [
                fullscreen_icon,
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
        nonlocal current_dialog
        current_dialog = dialog
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
        nonlocal current_dialog
        current_dialog = dialog
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
        nonlocal current_dialog
        current_dialog = dialog
        dialog.open = True
        page.update()

    def on_rename_file(folder, old_filename):
        name_field = ft.TextField(
            width=200,
            label="New file name",
            value=old_filename.replace(".md", ""),
            autofocus=True,
        )
        error_text = ft.Text("", color=theme["ERROR_COLOR"], size=12)

        def on_rename(_):
            new_name = name_field.value or ""
            # Validate new name (exclude the old filename from the check)
            files = list_markdown_files(folder)
            if new_name.endswith(".md"):
                new_filename = new_name
            else:
                new_filename = new_name + ".md"
            if not new_name or not new_name.strip():
                error_text.value = "Name cannot be empty."
                page.update()
                return
            if new_filename in files and new_filename != old_filename:
                error_text.value = "File with this name already exists."
                page.update()
                return
            if any(c in new_name for c in '/\\:*?"<>|'):
                error_text.value = "Invalid file name."
                page.update()
                return
            from backend.files_manager import rename_markdown_file

            try:
                rename_markdown_file(folder, old_filename, new_filename)
                dialog.open = False
                show_success(f"File renamed to '{new_filename}'")
                # If the file is currently open, update the tab
                if file_name.current == old_filename and file_folder.current == folder:
                    file_name.current = new_filename
                    update_tabs()
                refresh_sidebar()
                page.update()
            except Exception as ex:
                show_error(f"Error renaming file: {ex}")

        dialog.title = ft.Text(f"Rename File")
        dialog.content = ft.Container(
            content=ft.Column([name_field, error_text], spacing=theme["SPACING_MD"]),
            width=theme.get("DIALOG_WIDTH"),
            height=theme.get("DIALOG_HEIGHT"),
            alignment=theme.get("DIALOG_ALIGNMENT"),
        )
        dialog.actions = [
            ft.TextButton("Cancel", on_click=close_dialog),
            ft.ElevatedButton(
                "Rename", on_click=on_rename, height=theme["BUTTON_HEIGHT"]
            ),
        ]
        nonlocal current_dialog
        current_dialog = dialog
        dialog.open = True
        page.update()

    def on_rename_folder(folder_path):
        # Extract folder name from path (e.g., "Notebooks/Archive" -> "Archive")
        folder_name = folder_path.split("/")[-1]
        name_field = ft.TextField(
            width=200,
            label="New folder name",
            value=folder_name,
            autofocus=True,
        )
        error_text = ft.Text("", color=theme["ERROR_COLOR"], size=12)

        def on_rename(_):
            new_name = name_field.value or ""
            # Validate new name
            if not new_name or not new_name.strip():
                error_text.value = "Name cannot be empty."
                page.update()
                return
            # Check if folder with this name already exists in the same parent
            parent_path = (
                "/".join(folder_path.split("/")[:-1]) if "/" in folder_path else None
            )
            err = validate_folder_name(new_name, parent_path)
            if err and new_name != folder_name:
                error_text.value = err
                page.update()
                return
            from backend.files_manager import rename_folder

            try:
                rename_folder(folder_path, new_name)
                dialog.open = False
                show_success(f"Folder renamed to '{new_name}'")
                refresh_sidebar()
                page.update()
            except Exception as ex:
                show_error(f"Error renaming folder: {ex}")

        dialog.title = ft.Text(f"Rename Folder")
        dialog.content = ft.Container(
            content=ft.Column([name_field, error_text], spacing=theme["SPACING_MD"]),
            width=theme.get("DIALOG_WIDTH"),
            height=theme.get("DIALOG_HEIGHT"),
            alignment=theme.get("DIALOG_ALIGNMENT"),
        )
        dialog.actions = [
            ft.TextButton("Cancel", on_click=close_dialog),
            ft.ElevatedButton(
                "Rename", on_click=on_rename, height=theme["BUTTON_HEIGHT"]
            ),
        ]
        nonlocal current_dialog
        current_dialog = dialog
        dialog.open = True
        page.update()

    def on_toggle_folder(folder):
        expanded_folders[folder] = not expanded_folders.get(folder, False)
        refresh_sidebar()

    # Sidebar scrollable container
    def refresh_sidebar():
        # Update persistent scroll offset before sidebar rebuild
        nonlocal prev_scroll_offset
        # Debug prints removed

        def on_sidebar_scroll(e):
            nonlocal prev_scroll_offset
            if hasattr(e, "pixels"):
                prev_scroll_offset = e.pixels

        # Hide sidebar before update to mask flicker
        sidebar_view.opacity = 0
        sidebar_view.update()
        sidebar_view.content = sidebar(
            expanded_folders=expanded_folders,
            on_file_selected=open_file,
            on_delete_file=on_delete_file,
            on_delete_folder=on_delete_folder,
            on_create_folder=on_create_folder,
            on_create_subfolder=on_create_subfolder,
            on_create_file=on_create_file,
            on_toggle_folder=on_toggle_folder,
            on_rename_file=on_rename_file,
            on_rename_folder=on_rename_folder,
            current_file=file_name.current,
            current_folder=file_folder.current,
            sidebar_column_ref=sidebar_column_ref,
            on_sidebar_scroll=on_sidebar_scroll,
        )
        sidebar_view.update()
        # Restore scroll offset after sidebar_column_ref is re-attached, with a longer delay and repeated attempts
        import threading

        max_attempts = 3
        delay = 0.03  # 30ms, try to minimize blink

        def restore_scroll(attempt=1):
            if sidebar_column_ref.current is not None:
                try:
                    sidebar_column_ref.current.scroll_to(offset=prev_scroll_offset)
                except Exception as e:
                    pass
                else:
                    # After successful scroll restore, show sidebar again
                    sidebar_view.opacity = 1
                    sidebar_view.update()
                    return  # Success
            if attempt < max_attempts:
                threading.Timer(delay, lambda: restore_scroll(attempt + 1)).start()

        threading.Timer(delay, restore_scroll).start()

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
            on_rename_file=on_rename_file,
            on_rename_folder=on_rename_folder,
            current_file=file_name.current,
            current_folder=file_folder.current,
            sidebar_column_ref=sidebar_column_ref,
        ),
        width=theme.get("SIDEBAR_WIDTH", 250),
        expand=False,
        bgcolor=theme.get("SIDEBAR_BG", "#CCCCCC"),
        padding=theme.get("SIDEBAR_PADDING", 8),
        border_radius=theme.get("BORDER_RADIUS", 6),
        opacity=1,
        animate_opacity=ft.Animation(150, ft.AnimationCurve.EASE_IN_OUT),
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
            # Only open the tab if it does not already exist
            tab = normalize_tab((folder, file_name_val))
            if tab not in open_tabs:
                open_file(folder, file_name_val)
            else:
                # If already exists, just select it
                selected_tab_idx[0] = open_tabs.index(tab)
                update_tabs()
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
        nonlocal current_dialog
        current_dialog = dialog
        dialog.open = True
        page.update()
