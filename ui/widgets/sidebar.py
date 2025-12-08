import flet as ft
from ui.themes.theme import theme
from backend.files_manager import list_folders, list_markdown_files


def sidebar(
    expanded_folders,
    on_file_selected=None,
    on_delete_file=None,
    on_delete_folder=None,
    on_create_folder=None,
    on_create_subfolder=None,
    on_create_file=None,
    on_toggle_folder=None,
    on_rename_file=None,
    on_rename_folder=None,
    current_file=None,
    current_folder=None,
    sidebar_column_ref=None,
    on_sidebar_scroll=None,
):
    expanded_folders = expanded_folders or {}
    folders = list_folders()
    if not expanded_folders:
        expanded_folders = {f: False for f in folders}

    if on_delete_folder is None:
        on_delete_folder = lambda *_: None
    if on_file_selected is None:
        on_file_selected = lambda *_: None
    if on_delete_file is None:
        on_delete_file = lambda *_: None
    if on_create_folder is None:
        on_create_folder = lambda *_: None
    if on_create_subfolder is None:
        on_create_subfolder = lambda *_: None
    if on_create_file is None:
        on_create_file = lambda *_: None
    if on_rename_file is None:
        on_rename_file = lambda *_: None
    if on_rename_folder is None:
        on_rename_folder = lambda *_: None

    def build_items():
        items = []
        # Global folder creation button
        items.append(
            ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.FOLDER_SPECIAL,
                        tooltip="Create top-level folder",
                        icon_size=theme.get("ICON_SIZE_MD", 20),
                        style=ft.ButtonStyle(padding=0, shape=None),
                        on_click=lambda _: (
                            on_create_folder() if on_create_folder else None
                        ),
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        )
        # Divider line above first folder
        items.append(
            ft.Container(
                content=ft.Divider(
                    height=1,
                    color=theme.get("SIDEBAR_LINE_COLOR"),
                ),
                padding=ft.Padding(
                    0,
                    theme.get("SIDEBAR_DIVIDER_MARGIN", 8),
                    0,
                    theme.get("SIDEBAR_DIVIDER_MARGIN", 8),
                ),
            )
        )

        def is_ancestor_folder(folder_path, current_folder):
            if not current_folder:
                return False
            if folder_path == current_folder:
                return True
            return current_folder.startswith(folder_path + "/")

        def build_tree_prefix(is_last_childs, depth):
            # Build tree prefix with growing dashes for depth
            if not is_last_childs:
                return ""
            dash_base = theme.get("SIDEBAR_TREE_LINE_DASH_BASE", 2)
            dash_step = theme.get("SIDEBAR_TREE_LINE_DASH_STEP", 2)
            dash_count = dash_base + dash_step * depth
            if is_last_childs[-1]:
                return "└" + ("─" * dash_count) + " "
            else:
                return "├" + ("─" * dash_count) + " "

        def add_folder_items(folder, parent_path="", depth=0, is_last_childs=None):
            if is_last_childs is None:
                is_last_childs = []
            folder_path = folder if not parent_path else f"{parent_path}/{folder}"
            is_folder_selected = folder_path == current_folder
            is_folder_ancestor = is_ancestor_folder(folder_path, current_folder)
            is_expanded = expanded_folders.get(folder_path, False)
            from backend.files_manager import BASE_DIR
            import os

            abs_folder_path = os.path.join(BASE_DIR, folder_path)
            try:
                all_entries = [
                    e for e in os.listdir(abs_folder_path) if not e.startswith(".")
                ]
            except Exception:
                all_entries = []
            files = [f for f in all_entries if f.endswith(".md")]
            subfolders = [
                sf
                for sf in all_entries
                if os.path.isdir(os.path.join(abs_folder_path, sf))
            ]

            prefix = build_tree_prefix(is_last_childs, depth)
            items.append(
                ft.Container(
                    content=ft.Row(
                        [
                            (
                                ft.Text(
                                    prefix,
                                    font_family=theme.get(
                                        "SIDEBAR_TREE_LINE_FONT_FAMILY", "monospace"
                                    ),
                                    color=theme.get(
                                        "SIDEBAR_TREE_LINE_DARK",
                                        theme.get("SIDEBAR_TREE_LINE_COLOR", "#37474F"),
                                    ),
                                    size=theme.get("SIDEBAR_TREE_LINE_SIZE", 14),
                                    selectable=False,
                                    width=(
                                        len(prefix)
                                        * theme.get("SIDEBAR_TREE_LINE_WIDTH_FACTOR", 8)
                                        if prefix
                                        else 0
                                    ),
                                )
                                if prefix
                                else ft.Container(width=0)
                            ),
                            ft.Text(
                                folder,
                                color=(
                                    theme.get("SIDEBAR_HIGHLIGHT_COLOR")
                                    if is_folder_ancestor
                                    else theme.get("SIDEBAR_ITEM_COLOR")
                                ),
                                weight=theme.get("SIDEBAR_TITLE_FONT_WEIGHT"),
                                size=theme.get("SIDEBAR_TITLE_FONT_SIZE"),
                                expand=True,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                tooltip=folder_path,
                            ),
                            ft.PopupMenuButton(
                                icon=ft.Icons.MORE_VERT,
                                icon_size=theme.get("ICON_SIZE_SM", 16),
                                style=ft.ButtonStyle(padding=0, shape=None),
                                items=[
                                    ft.PopupMenuItem(
                                        text="Create File",
                                        icon=ft.Icons.NOTE_ADD,
                                        on_click=lambda _, f=folder_path: (
                                            on_create_file(f)
                                            if on_create_file
                                            else None
                                        ),
                                    ),
                                    ft.PopupMenuItem(
                                        text="Create Folder",
                                        icon=ft.Icons.CREATE_NEW_FOLDER,
                                        on_click=lambda _, f=folder_path: (
                                            on_create_subfolder(f)
                                            if on_create_subfolder
                                            else None
                                        ),
                                    ),
                                    ft.PopupMenuItem(
                                        text="Rename",
                                        icon=ft.Icons.EDIT,
                                        on_click=lambda _, f=folder_path: (
                                            on_rename_folder(f)
                                            if on_rename_folder
                                            else None
                                        ),
                                    ),
                                    ft.PopupMenuItem(
                                        text="Delete Folder",
                                        icon=ft.Icons.DELETE,
                                        on_click=lambda _, f=folder_path: on_delete_folder(
                                            f
                                        ),
                                    ),
                                ],
                            ),
                        ],
                        alignment=theme.get(
                            "PAGE_VERTICAL_ALIGNMENT", ft.MainAxisAlignment.START
                        ),
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=1,
                    ),
                    bgcolor=(
                        theme.get("SIDEBAR_HIGHLIGHT_BG")
                        if is_folder_ancestor
                        else None
                    ),
                    border_radius=(
                        theme.get("SIDEBAR_FILE_ROW_RADIUS")
                        if is_folder_ancestor
                        else 0
                    ),
                    height=theme.get("SIDEBAR_FILE_ROW_HEIGHT"),
                    padding=theme.get("SIDEBAR_ROW_PADDING", ft.Padding(2, 2, 16, 2)),
                    on_click=lambda _, f=folder_path: (
                        on_toggle_folder(f) if on_toggle_folder else None
                    ),
                )
            )
            # File rows (if expanded)
            if is_expanded:
                for idx, file in enumerate(files):
                    is_selected = file == current_file and folder_path == current_folder
                    is_last_file = (idx == len(files) - 1) and not subfolders
                    file_prefix = build_tree_prefix(
                        is_last_childs + [is_last_file], depth + 1
                    )
                    items.append(
                        ft.Container(
                            content=ft.Row(
                                [
                                    (
                                        ft.Text(
                                            file_prefix,
                                            font_family=theme.get(
                                                "SIDEBAR_TREE_LINE_FONT_FAMILY",
                                                "monospace",
                                            ),
                                            color=theme.get(
                                                "SIDEBAR_TREE_LINE_DARK",
                                                theme.get(
                                                    "SIDEBAR_TREE_LINE_COLOR", "#37474F"
                                                ),
                                            ),
                                            size=theme.get(
                                                "SIDEBAR_TREE_LINE_SIZE", 14
                                            ),
                                            selectable=False,
                                            width=(
                                                len(file_prefix)
                                                * theme.get(
                                                    "SIDEBAR_TREE_LINE_WIDTH_FACTOR", 8
                                                )
                                                if file_prefix
                                                else 0
                                            ),
                                        )
                                        if file_prefix
                                        else ft.Container(width=0)
                                    ),
                                    ft.Text(
                                        file,
                                        color=(
                                            theme.get(
                                                "SIDEBAR_HIGHLIGHT_COLOR", "#003E6D"
                                            )
                                            if is_selected
                                            else theme.get(
                                                "SIDEBAR_ITEM_COLOR", "#212121"
                                            )
                                        ),
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                        tooltip=file,
                                        expand=True,
                                        style=theme.get(
                                            "SIDEBAR_FILE_TEXT_STYLE", None
                                        ),
                                    ),
                                    ft.PopupMenuButton(
                                        icon=ft.Icons.MORE_VERT,
                                        icon_size=theme.get("ICON_SIZE_SM", 16),
                                        style=ft.ButtonStyle(padding=0, shape=None),
                                        items=[
                                            ft.PopupMenuItem(
                                                text="Rename",
                                                icon=ft.Icons.EDIT,
                                                on_click=lambda _, f=folder_path, fi=file: (
                                                    on_rename_file(f, fi)
                                                    if on_rename_file
                                                    else None
                                                ),
                                            ),
                                            ft.PopupMenuItem(
                                                text="Delete",
                                                icon=ft.Icons.DELETE,
                                                on_click=lambda _, f=folder_path, fi=file: on_delete_file(
                                                    f, fi
                                                ),
                                            ),
                                        ],
                                    ),
                                ],
                                alignment=theme.get(
                                    "PAGE_VERTICAL_ALIGNMENT",
                                    ft.MainAxisAlignment.START,
                                ),
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=1,
                            ),
                            bgcolor=(
                                theme.get("SIDEBAR_HIGHLIGHT_BG", "#B3E5FC")
                                if is_selected
                                else None
                            ),
                            border_radius=(
                                theme.get("SIDEBAR_FILE_ROW_RADIUS")
                                if is_selected
                                else 0
                            ),
                            height=theme.get("SIDEBAR_FILE_ROW_HEIGHT"),
                            padding=theme.get(
                                "SIDEBAR_ROW_PADDING", ft.Padding(2, 2, 16, 2)
                            ),
                            on_click=lambda _, f=folder_path, fi=file: on_file_selected(
                                f, fi
                            ),
                        )
                    )
                # Recursively add subfolders
                for idx, subfolder in enumerate(subfolders):
                    add_folder_items(
                        subfolder,
                        folder_path,
                        depth + 1,
                        is_last_childs + [idx == len(subfolders) - 1],
                    )

        for idx, folder in enumerate(folders):
            add_folder_items(folder, depth=0, is_last_childs=[idx == len(folders) - 1])
            items.append(
                ft.Container(
                    content=ft.Divider(
                        height=1,
                        color=theme.get("SIDEBAR_LINE_COLOR"),
                    ),
                    padding=ft.Padding(
                        0,
                        theme.get("SIDEBAR_DIVIDER_MARGIN", 8),
                        0,
                        theme.get("SIDEBAR_DIVIDER_MARGIN", 8),
                    ),
                )
            )
        return items

    controls_list = build_items()
    if not isinstance(controls_list, list):
        controls_list = [controls_list] if controls_list is not None else []
    sidebar_column = ft.Column(
        controls=controls_list,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        expand=True,  # Responsive: fill available space
        scroll=ft.ScrollMode.AUTO,
        auto_scroll=False,
        ref=sidebar_column_ref if sidebar_column_ref is not None else None,
        on_scroll=on_sidebar_scroll if on_sidebar_scroll is not None else None,
    )
    return ft.Container(
        content=ft.Stack(
            [
                sidebar_column,
                ft.Container(
                    width=16,  # Reserve space for scrollbar
                    expand=True,
                    alignment=ft.alignment.center_right,
                    bgcolor="transparent",
                ),
            ]
        ),
        width=theme.get("SIDEBAR_WIDTH"),
        bgcolor=theme.get("SIDEBAR_BG"),
        padding=theme.get("SIDEBAR_PADDING"),
        border_radius=theme.get("BORDER_RADIUS"),
        expand=True,  # Responsive: fill available space
    )
