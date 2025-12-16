import flet as ft
from ui.themes.theme import theme
import sys
from typing import Optional

sys.path.append("../../backend")
from backend.files_manager import (
    read_markdown_file,
    save_markdown_file,
    list_markdown_files,
    list_folders,
    create_folder,
    delete_folder,
)
from ui.widgets.header_footer import build_header, build_footer
from ui.widgets.tabs import TabsBar
from ui.containers.main_content import MainContent
from ui.state.window_state import WindowState


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
            width=theme["DIALOG_INPUT_WIDTH_SM"],
            label="Folder name",
            autofocus=True,
        )
        error_text = ft.Text("", color=theme["ERROR_COLOR"], size=theme["ERROR_TEXT_SIZE"])

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
            width=theme["DIALOG_INPUT_WIDTH_SM"],
            label="File name",
            autofocus=True,
        )
        error_text = ft.Text("", color=theme["ERROR_COLOR"], size=theme["ERROR_TEXT_SIZE"])

        def on_create(_):
            file_name_val = name_field.value or ""
            err = validate_file_name(file_name_val, folder)
            if err:
                error_text.value = err
                page.update()
                return
            from backend.files_manager import create_file

            # Add .md extension if not present
            if not file_name_val.endswith(".md"):
                file_name_val += ".md"

            create_file(str(folder), str(file_name_val.replace(".md", "")))
            dialog.open = False
            show_success("File created.")
            refresh_sidebar()
            # Open the created file
            open_file(folder, file_name_val)
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

    def update_app_state(**updates):
        """Merge updates into persisted app state.

        This avoids overwriting unrelated keys when we persist open tabs or
        last opened file.
        """
        nonlocal app_state
        app_state.update(updates)
        save_app_state(app_state)

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
    update_app_state(open_tabs=open_tabs)
    file_name = ft.Ref[str]()
    file_folder = ft.Ref[str]()
    expanded_folders = {folder: False for folder in list_folders()}
    reorder_mode = {"active": False}  # Use dict to allow mutation in nested functions
    selected_tab_idx = [0]

    # Initialize window state
    window_state = WindowState()

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

    def open_file(folder, filename):
        instant_save()
        tab = normalize_tab((folder, filename))
        # Only add the tab if it does not already exist
        if tab not in open_tabs:
            open_tabs.append(tab)
            update_app_state(open_tabs=open_tabs)
        # Always set selected_tab_idx to the opened tab
        selected_tab_idx[0] = open_tabs.index(tab)
        file_name.current = tab[1] or ""
        file_folder.current = tab[0] or ""
        update_app_state(
            last_opened={"folder": file_folder.current, "filename": file_name.current}
        )
        content = read_markdown_file(tab[0], tab[1])
        main_content_component.set_content(content)
        main_content_component.update()
        tabs_bar.update()
        main_column.controls[1] = main_content_component.get_view(file_name.current)
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
            update_app_state(
                last_opened={
                    "folder": file_folder.current,
                    "filename": file_name.current,
                }
            )
            content = read_markdown_file(folder, filename)
            main_content_component.set_content(content)
            main_content_component.update()
            tabs_bar.update()
            main_column.controls[1] = main_content_component.get_view(file_name.current)
            if getattr(main_column, "page", None) is not None:
                main_column.update()
            # Update sidebar highlight on tab selection
            refresh_sidebar()

    # Window control handlers
    def on_minimize_window(_):
        """Minimize the window to taskbar/dock."""
        page.window.minimized = True
        page.update()

    def on_maximize_window(_):
        """Toggle between maximized and normal window size."""
        window_state.toggle_maximize(page)

    def on_close_window(_):
        """Close the application window."""
        page.window.close()

    def on_page_resized(e: ft.WindowResizeEvent):
        """Handle window resize events."""
        window_state.on_window_resized(e)

    page.on_resized = on_page_resized

    def toggle_half_size(_):
        """Toggle between full/maximized size and half-size snap."""
        window_state.toggle_half_size(page)

    # Build header using new modular component
    header = build_header(
        page,
        on_minimize=on_minimize_window,
        on_maximize=on_maximize_window,
        on_close=on_close_window,
        on_half_size=toggle_half_size,
        on_search_change=None,  # Implement search functionality later
    )

    # Create TabsBar instance with callbacks
    def on_select_tab_callback(idx):
        """Handle tab selection."""
        select_tab(idx)

    def on_close_tab_callback(idx):
        """Handle tab closure."""
        close_tab(idx)

    def on_new_tab_callback():
        """Handle new tab creation."""
        new_tab()

    tabs_bar = TabsBar(
        open_tabs=open_tabs,
        selected_idx=selected_tab_idx,
        on_select_tab=on_select_tab_callback,
        on_close_tab=on_close_tab_callback,
        on_new_tab=on_new_tab_callback,
    )

    # Create the tab row container
    tab_row = tabs_bar.container

    def instant_save(e=None):
        if file_name.current and file_folder.current:
            current_content = main_content_component.get_content()
            save_markdown_file(
                file_folder.current,
                file_name.current,
                current_content,
            )
        # Persist open tabs only
        update_app_state(open_tabs=open_tabs)

    # Initialize main content with instant save callback
    main_content_component = MainContent(on_change=instant_save)

    from ui.widgets.sidebar import sidebar

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

    def on_rename_file(folder, old_filename):
        name_field = ft.TextField(
            width=theme["RENAME_INPUT_WIDTH"],
            label="New file name",
            value=old_filename.replace(".md", ""),
            autofocus=True,
        )
        error_text = ft.Text("", color=theme["ERROR_COLOR"], size=theme["ERROR_TEXT_SIZE"])

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
                # Update open tabs to reflect the new filename
                for idx, tab in enumerate(open_tabs):
                    if tab == (folder, old_filename):
                        open_tabs[idx] = (folder, new_filename)
                # Keep persisted state consistent
                last = app_state.get("last_opened") or {}
                if (
                    last.get("folder") == folder
                    and last.get("filename") == old_filename
                ):
                    update_app_state(
                        open_tabs=open_tabs,
                        last_opened={"folder": folder, "filename": new_filename},
                    )
                else:
                    update_app_state(open_tabs=open_tabs)

                dialog.open = False
                show_success(f"File renamed to '{new_filename}'")

                # If the file is currently open, update references and refresh UI
                if file_name.current == old_filename and file_folder.current == folder:
                    file_name.current = new_filename
                    update_app_state(
                        last_opened={
                            "folder": file_folder.current,
                            "filename": file_name.current,
                        }
                    )
                    tabs_bar.update()
                    main_column.controls[1] = main_content_component.get_view(
                        file_name.current
                    )
                    if getattr(main_column, "page", None) is not None:
                        main_column.update()
                else:
                    tabs_bar.update()

                refresh_sidebar()
                page.update()
            except Exception as ex:
                show_error(f"Error renaming file: {ex}")

        dialog.title = ft.Text("Rename File")
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
            width=theme["RENAME_INPUT_WIDTH"],
            label="New folder name",
            value=folder_name,
            autofocus=True,
        )
        error_text = ft.Text("", color=theme["ERROR_COLOR"], size=theme["ERROR_TEXT_SIZE"])

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

                # Build new folder path for open tabs
                if "/" in folder_path:
                    parent_path = folder_path.rsplit("/", 1)[0]
                    new_folder_path = f"{parent_path}/{new_name}"
                else:
                    new_folder_path = new_name

                # Update any open tabs that point to the renamed folder (including children)
                for idx, tab in enumerate(open_tabs):
                    tab_folder, tab_file = tab
                    if tab_folder == folder_path:
                        open_tabs[idx] = (new_folder_path, tab_file)
                    elif tab_folder.startswith(folder_path + "/"):
                        suffix = tab_folder[len(folder_path) :]
                        open_tabs[idx] = (new_folder_path + suffix, tab_file)

                # Update currently open file folder if it was inside the renamed folder
                if file_folder.current:
                    if file_folder.current == folder_path:
                        file_folder.current = new_folder_path
                    elif file_folder.current.startswith(folder_path + "/"):
                        suffix = file_folder.current[len(folder_path) :]
                        file_folder.current = new_folder_path + suffix

                # Keep persisted state consistent
                last = app_state.get("last_opened") or {}
                last_folder_value = last.get("folder")
                if last_folder_value == folder_path:
                    update_app_state(
                        open_tabs=open_tabs,
                        last_opened={
                            "folder": new_folder_path,
                            "filename": last.get("filename"),
                        },
                    )
                elif isinstance(
                    last_folder_value, str
                ) and last_folder_value.startswith(folder_path + "/"):
                    suffix = last_folder_value[len(folder_path) :]
                    update_app_state(
                        open_tabs=open_tabs,
                        last_opened={
                            "folder": new_folder_path + suffix,
                            "filename": last.get("filename"),
                        },
                    )
                else:
                    update_app_state(open_tabs=open_tabs)

                dialog.open = False
                show_success(f"Folder renamed to '{new_name}'")
                tabs_bar.update()
                main_column.controls[1] = main_content_component.get_view(
                    file_name.current
                )
                if getattr(main_column, "page", None) is not None:
                    main_column.update()
                refresh_sidebar()
                page.update()
            except Exception as ex:
                show_error(f"Error renaming folder: {ex}")

        dialog.title = ft.Text("Rename Folder")
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

    # Callback wrappers for sidebar integration
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

    def on_toggle_reorder_mode():
        """Toggle reorder mode on/off."""
        reorder_mode["active"] = not reorder_mode["active"]
        mode_text = "enabled" if reorder_mode["active"] else "disabled"
        show_snackbar(f"Reorder mode {mode_text}", color=theme.get("COLOR_PRIMARY"))
        refresh_sidebar()

    def on_reorder(parent_folder, item_name, target_item_name, insert_before=True):
        """Handle reordering of items via drag and drop."""
        from backend.files_manager import reorder_items, BASE_DIR, _ensure_order_file
        import os

        if parent_folder == "":
            folder_path = BASE_DIR
        else:
            folder_path = os.path.join(BASE_DIR, parent_folder)

        try:
            order = _ensure_order_file(folder_path)
            items = [i.get("name") for i in order.get("items", []) if i.get("name")]

            if item_name in items:
                items.remove(item_name)

            if target_item_name in items:
                target_idx = items.index(target_item_name)
                insert_pos = target_idx if insert_before else target_idx + 1
                items.insert(insert_pos, item_name)
            else:
                items.append(item_name)

            reorder_items(parent_folder, items)
            refresh_sidebar()
        except Exception as ex:
            show_snackbar(f"Error reordering: {ex}", color=theme["ERROR_COLOR"])

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
            reorder_mode=reorder_mode["active"],
            on_toggle_reorder_mode=on_toggle_reorder_mode,
            on_reorder=on_reorder,
            page=page,
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
                except Exception:
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
            reorder_mode=reorder_mode["active"],
            on_toggle_reorder_mode=on_toggle_reorder_mode,
            on_reorder=on_reorder,
            page=page,
        ),
        width=theme.get("SIDEBAR_WIDTH", 250),
        expand=False,
        bgcolor=theme["SIDEBAR_BG"],
        padding=theme.get("SIDEBAR_PADDING", 8),
        border_radius=theme.get("BORDER_RADIUS", 6),
        opacity=1,
        animate_opacity=ft.Animation(150, ft.AnimationCurve.EASE_IN_OUT),
    )

    main_column = ft.Column(
        [
            tab_row,
            main_content_component.get_view(file_name.current),
        ],
        spacing=theme["ZERO_SPACING"],
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

    # Build footer using new modular component
    footer = build_footer()

    # Compose the page: header (top), main_layout (row), footer (bottom)
    page.add(
        header,
        main_layout,
        footer,
    )
    # Initial sidebar build
    refresh_sidebar()
    tabs_bar.update()

    def _auto_open_startup_file():
        """Open the last opened file on startup only if app was closed with a file open."""
        state_last = app_state.get("last_opened") or {}
        last_folder = state_last.get("folder")
        last_filename = state_last.get("filename")

        def is_valid(folder: Optional[str], filename: Optional[str]) -> bool:
            if not folder or not filename:
                return False
            try:
                return filename in list_markdown_files(folder)
            except Exception:
                return False

        # Only open if last_opened is valid; otherwise start empty
        if is_valid(last_folder, last_filename):
            open_file(last_folder, last_filename)

    _auto_open_startup_file()

    def close_tab(idx):
        instant_save()
        if 0 <= idx < len(open_tabs):
            open_tabs.pop(idx)
            update_app_state(open_tabs=open_tabs)
            if open_tabs:
                # Select previous tab if possible, else first tab
                new_index = max(0, selected_tab_idx[0] - 1)
                folder, filename = open_tabs[new_index]
                file_name.current = filename
                file_folder.current = folder
                update_app_state(
                    last_opened={
                        "folder": file_folder.current,
                        "filename": file_name.current,
                    }
                )
                content = read_markdown_file(folder, filename)
                main_content_component.set_content(content)
                main_content_component.update()
                selected_tab_idx[0] = new_index
            else:
                file_name.current = ""
                file_folder.current = ""
                main_content_component.set_content("")
                selected_tab_idx[0] = -1
                update_app_state(last_opened=None)
            tabs_bar.update()
            main_column.controls[1] = main_content_component.get_view(file_name.current)
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
            width=theme["DIALOG_INPUT_WIDTH_SM"],
            options=[ft.dropdown.Option(f) for f in list_folders()],
            value=list_folders()[0],
            label="Select Folder",
        )
        filename_field = ft.TextField(
            width=theme["DIALOG_INPUT_WIDTH_SM"],
            label="File name",
            autofocus=True,
        )
        error_text = ft.Text("", color=theme["ERROR_COLOR"], size=theme["ERROR_TEXT_SIZE"])

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

            # Close dialog and provide feedback, mirroring sidebar behavior
            dialog.open = False
            show_success("File created.")
            refresh_sidebar()

            # Only open the tab if it does not already exist
            tab = normalize_tab((folder, file_name_val))
            if tab not in open_tabs:
                open_file(folder, file_name_val)
            else:
                # If already exists, load and focus it to mirror pre-refactor behavior
                select_tab(open_tabs.index(tab))

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
