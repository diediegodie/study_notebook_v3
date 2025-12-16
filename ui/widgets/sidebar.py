import flet as ft
from ui.themes.theme import theme
from backend.files_manager import list_folders


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
    reorder_mode=False,
    on_toggle_reorder_mode=None,
    on_reorder=None,
    page=None,
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
    if on_toggle_reorder_mode is None:
        on_toggle_reorder_mode = lambda *_: None
    if on_reorder is None:
        on_reorder = lambda *_: None

    def build_items():
        items = []

        def parse_drag_data(data_str: str):
            if data_str and "|" in data_str:
                parts = data_str.split("|", 1)
                return parts[0], parts[1]
            return None, None

        # Global folder creation button and reorder button
        items.append(
            ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.FOLDER_SPECIAL,
                        tooltip="Create top-level folder",
                        icon_size=theme.get("ICON_SIZE_MD", 20),
                        style=ft.ButtonStyle(
                            padding=theme["SIDEBAR_BUTTON_PADDING_ZERO"], shape=None
                        ),
                        on_click=lambda _: (
                            on_create_folder() if on_create_folder else None
                        ),
                    ),
                    ft.Container(expand=True),  # Spacer to push action button to right
                    (
                        ft.IconButton(
                            icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                            tooltip="Confirm reorder",
                            icon_size=theme.get("ICON_SIZE_MD"),
                            icon_color=theme.get("SIDEBAR_ITEM_COLOR"),
                            style=ft.ButtonStyle(
                                padding=theme["SIDEBAR_BUTTON_PADDING_ZERO"], shape=None
                            ),
                            on_click=lambda _: on_toggle_reorder_mode(),
                        )
                        if reorder_mode
                        else ft.IconButton(
                            icon=ft.Icons.SWAP_VERT_OUTLINED,
                            tooltip="Enable reorder mode",
                            icon_size=theme.get("ICON_SIZE_MD"),
                            style=ft.ButtonStyle(
                                padding=theme["SIDEBAR_BUTTON_PADDING_ZERO"], shape=None
                            ),
                            on_click=lambda _: on_toggle_reorder_mode(),
                        )
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=theme["SIDEBAR_ROW_SPACING"],
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        )
        # Divider line above first folder
        items.append(
            ft.Container(
                content=ft.Divider(
                    height=theme["DIVIDER_HEIGHT"],
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
            is_folder_ancestor = is_ancestor_folder(folder_path, current_folder)
            is_expanded = expanded_folders.get(folder_path, False)
            from backend.files_manager import BASE_DIR, _ensure_order_file
            import os

            abs_folder_path = os.path.join(BASE_DIR, folder_path)
            # Children ordering comes from the folder's .order.json.
            # This allows persisted reorders (including mixing files/folders) to render correctly.
            try:
                fs_entries = [
                    e for e in os.listdir(abs_folder_path) if not e.startswith(".")
                ]
            except Exception:
                fs_entries = []
            fs_files = [
                e
                for e in fs_entries
                if e.endswith(".md")
                and os.path.isfile(os.path.join(abs_folder_path, e))
            ]
            fs_subfolders = [
                e for e in fs_entries if os.path.isdir(os.path.join(abs_folder_path, e))
            ]

            try:
                order = _ensure_order_file(abs_folder_path)
            except Exception:
                order = {"items": []}

            children_in_order = []
            names_in_order = set()
            for item in order.get("items", []) or []:
                name = item.get("name")
                item_type = item.get("type")
                if not name or item_type not in ("file", "folder"):
                    continue
                if item_type == "file":
                    if name in fs_files:
                        children_in_order.append({"name": name, "type": "file"})
                        names_in_order.add(name)
                else:
                    if name in fs_subfolders:
                        children_in_order.append({"name": name, "type": "folder"})
                        names_in_order.add(name)

            # Fallback: add any missing items at the start (keeps UI robust if order file is stale)
            for name in fs_subfolders:
                if name not in names_in_order:
                    children_in_order.insert(0, {"name": name, "type": "folder"})
                    names_in_order.add(name)
            for name in fs_files:
                if name not in names_in_order:
                    children_in_order.insert(0, {"name": name, "type": "file"})
                    names_in_order.add(name)

            prefix = build_tree_prefix(is_last_childs, depth)

            # Create folder row container
            folder_container = ft.Container(
                content=ft.Row(
                    [
                        (
                            ft.Text(
                                prefix,
                                font_family=theme.get(
                                    "SIDEBAR_TREE_LINE_FONT_FAMILY", "monospace"
                                ),
                                color=theme["SIDEBAR_TREE_LINE_DARK"],
                                size=theme["SIDEBAR_TREE_LINE_SIZE"],
                                selectable=False,
                                width=(
                                    len(prefix)
                                    * theme.get("SIDEBAR_TREE_LINE_WIDTH_FACTOR", 8)
                                    if prefix
                                    else 0
                                ),
                            )
                            if prefix
                            else ft.Container(width=theme["SIDEBAR_ZERO_WIDTH"])
                        ),
                        (
                            ft.Icon(
                                ft.Icons.DRAG_INDICATOR,
                                size=theme["SIDEBAR_DRAG_ICON_SIZE"],
                                color=theme.get("SIDEBAR_ITEM_COLOR"),
                            )
                            if reorder_mode
                            else ft.Container(width=theme["SIDEBAR_ZERO_WIDTH"])
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
                            max_lines=theme["SIDEBAR_TEXT_MAX_LINES"],
                            overflow=ft.TextOverflow.ELLIPSIS,
                            tooltip=folder_path,
                        ),
                        (
                            ft.PopupMenuButton(
                                icon=ft.Icons.MORE_VERT,
                                icon_size=theme.get("ICON_SIZE_SM", 16),
                                style=ft.ButtonStyle(
                                    padding=theme["SIDEBAR_BUTTON_PADDING_ZERO"],
                                    shape=None,
                                ),
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
                            )
                            if not reorder_mode
                            else ft.Container(width=theme["SIDEBAR_ZERO_WIDTH"])
                        ),
                    ],
                    alignment=theme.get(
                        "PAGE_VERTICAL_ALIGNMENT", ft.MainAxisAlignment.START
                    ),
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=theme["SIDEBAR_GROUP_SPACING"],
                ),
                bgcolor=(
                    theme.get("SIDEBAR_HIGHLIGHT_BG") if is_folder_ancestor else None
                ),
                border_radius=(
                    theme.get("SIDEBAR_FILE_ROW_RADIUS") if is_folder_ancestor else 0
                ),
                height=theme.get("SIDEBAR_FILE_ROW_HEIGHT"),
                padding=theme.get("SIDEBAR_ROW_PADDING", ft.Padding(2, 2, 16, 2)),
                on_click=lambda _, f=folder_path: (
                    on_toggle_folder(f)
                    if on_toggle_folder and not reorder_mode
                    else None
                ),
            )

            # Wrap in Draggable; use dedicated drop bars for clarity
            if reorder_mode:
                parent_folder_for_reorder = parent_path if parent_path else ""

                folder_draggable = ft.Draggable(
                    group="reorder",
                    content=folder_container,
                    content_when_dragging=ft.Container(
                        height=theme.get("SIDEBAR_FILE_ROW_HEIGHT"),
                        bgcolor=theme["SIDEBAR_HIGHLIGHT_BG"],
                        border=ft.border.all(1, theme.get("COLOR_PRIMARY")),
                        border_radius=theme.get("SIDEBAR_FILE_ROW_RADIUS", 0),
                    ),
                    content_feedback=ft.Container(
                        content=ft.Text(
                            folder,
                            size=theme["SIDEBAR_DRAG_FEEDBACK_TEXT_SIZE"],
                            color=theme["SIDEBAR_DRAG_FEEDBACK_TEXT_COLOR"],
                        ),
                        bgcolor=theme.get("COLOR_PRIMARY"),
                        padding=theme["SIDEBAR_DRAG_FEEDBACK_PADDING"],
                        border_radius=theme["SIDEBAR_DRAG_FEEDBACK_RADIUS"],
                        opacity=theme["SIDEBAR_DROP_BAR_HOVER_OPACITY"],
                    ),
                    data=f"{parent_folder_for_reorder}|{folder}",
                )

                def drop_bar(insert_before: bool):
                    def on_accept_bar(
                        e,
                        parent_folder=parent_folder_for_reorder,
                        target_folder=folder,
                        before=insert_before,
                    ):
                        dragged_parent, dragged_item = (None, None)
                        if page and hasattr(e, "src_id"):
                            try:
                                src_control = page.get_control(f"{e.src_id}")
                                if src_control and hasattr(src_control, "data"):
                                    dragged_parent, dragged_item = parse_drag_data(
                                        src_control.data
                                    )
                            except Exception:
                                dragged_parent, dragged_item = (None, None)

                        if (
                            dragged_parent == parent_folder
                            and dragged_item
                            and dragged_item != target_folder
                        ):
                            on_reorder(
                                parent_folder, dragged_item, target_folder, before
                            )

                    def on_will_accept_bar(
                        e, parent_folder=parent_folder_for_reorder, target_folder=folder
                    ):
                        # Per Flet docs, e.data is "true"/"false" indicating group match.
                        will_accept = getattr(e, "data", None) == "true"
                        bar = e.control.content.content
                        bar.bgcolor = (
                            theme["SIDEBAR_DROP_BAR_HOVER_BG"]
                            if will_accept
                            else theme["SIDEBAR_DROP_BAR_BG"]
                        )
                        bar.height = (
                            theme["SIDEBAR_DROP_BAR_HOVER_HEIGHT"]
                            if will_accept
                            else theme["SIDEBAR_DROP_BAR_HEIGHT"]
                        )
                        bar.opacity = (
                            theme["SIDEBAR_DROP_BAR_HOVER_OPACITY"]
                            if will_accept
                            else theme["SIDEBAR_DROP_BAR_OPACITY"]
                        )
                        e.control.update()

                    def on_leave_bar(e):
                        bar = e.control.content.content
                        bar.bgcolor = theme["SIDEBAR_DROP_BAR_BG"]
                        bar.height = theme["SIDEBAR_DROP_BAR_HEIGHT"]
                        bar.opacity = theme["SIDEBAR_DROP_BAR_OPACITY"]
                        e.control.update()

                    return ft.DragTarget(
                        group="reorder",
                        content=ft.Container(
                            padding=ft.Padding(
                                0,
                                theme["SIDEBAR_DROP_BAR_PADDING_Y"],
                                0,
                                theme["SIDEBAR_DROP_BAR_PADDING_Y"],
                            ),
                            expand=True,
                            content=ft.Container(
                                height=theme["SIDEBAR_DROP_BAR_HEIGHT"],
                                bgcolor=theme["SIDEBAR_DROP_BAR_BG"],
                                opacity=theme["SIDEBAR_DROP_BAR_OPACITY"],
                                expand=True,
                            ),
                        ),
                        on_accept=on_accept_bar,
                        on_will_accept=on_will_accept_bar,
                        on_leave=on_leave_bar,
                    )

                folder_block = ft.Column(
                    [
                        drop_bar(True),
                        folder_draggable,
                        drop_bar(False),
                    ],
                    spacing=theme["ZERO_SPACING"],
                )
                items.append(folder_block)
            else:
                items.append(folder_container)
            # Child rows (if expanded)
            if is_expanded:
                for child_idx, child in enumerate(children_in_order):
                    is_last_child = child_idx == len(children_in_order) - 1

                    if child["type"] == "folder":
                        subfolder = child["name"]
                        add_folder_items(
                            subfolder,
                            folder_path,
                            depth + 1,
                            is_last_childs + [is_last_child],
                        )
                        continue

                    file = child["name"]
                    is_selected = file == current_file and folder_path == current_folder
                    file_prefix = build_tree_prefix(
                        is_last_childs + [is_last_child], depth + 1
                    )

                    # Create file row container
                    file_container = ft.Container(
                        content=ft.Row(
                            [
                                (
                                    ft.Text(
                                        file_prefix,
                                        font_family=theme.get(
                                            "SIDEBAR_TREE_LINE_FONT_FAMILY",
                                            "monospace",
                                        ),
                                        color=theme["SIDEBAR_TREE_LINE_DARK"],
                                        size=theme["SIDEBAR_TREE_LINE_SIZE"],
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
                                    else ft.Container(width=theme["SIDEBAR_ZERO_WIDTH"])
                                ),
                                (
                                    ft.Icon(
                                        ft.Icons.DRAG_INDICATOR,
                                        size=theme["SIDEBAR_DRAG_ICON_SIZE"],
                                        color=theme.get("SIDEBAR_ITEM_COLOR"),
                                    )
                                    if reorder_mode
                                    else ft.Container(width=theme["SIDEBAR_ZERO_WIDTH"])
                                ),
                                ft.Text(
                                    file,
                                    color=(
                                        theme["SIDEBAR_HIGHLIGHT_COLOR"]
                                        if is_selected
                                        else theme["SIDEBAR_ITEM_COLOR"]
                                    ),
                                    max_lines=theme["SIDEBAR_TEXT_MAX_LINES"],
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    tooltip=file,
                                    expand=True,
                                    style=theme.get("SIDEBAR_FILE_TEXT_STYLE", None),
                                ),
                                (
                                    ft.PopupMenuButton(
                                        icon=ft.Icons.MORE_VERT,
                                        icon_size=theme.get("ICON_SIZE_SM", 16),
                                        style=ft.ButtonStyle(
                                            padding=theme[
                                                "SIDEBAR_BUTTON_PADDING_ZERO"
                                            ],
                                            shape=None,
                                        ),
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
                                    )
                                    if not reorder_mode
                                    else ft.Container(width=theme["SIDEBAR_ZERO_WIDTH"])
                                ),
                            ],
                            alignment=theme.get(
                                "PAGE_VERTICAL_ALIGNMENT",
                                ft.MainAxisAlignment.START,
                            ),
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=theme["SIDEBAR_GROUP_SPACING"],
                        ),
                        bgcolor=(
                            theme.get("SIDEBAR_HIGHLIGHT_BG") if is_selected else None
                        ),
                        border_radius=(
                            theme.get("SIDEBAR_FILE_ROW_RADIUS") if is_selected else 0
                        ),
                        height=theme.get("SIDEBAR_FILE_ROW_HEIGHT"),
                        padding=theme.get(
                            "SIDEBAR_ROW_PADDING", ft.Padding(2, 2, 16, 2)
                        ),
                        on_click=lambda _, f=folder_path, fi=file: (
                            on_file_selected(f, fi) if not reorder_mode else None
                        ),
                    )

                    if reorder_mode:
                        file_draggable = ft.Draggable(
                            group="reorder",
                            content=file_container,
                            content_when_dragging=ft.Container(
                                height=theme.get("SIDEBAR_FILE_ROW_HEIGHT"),
                                bgcolor=theme["SIDEBAR_HIGHLIGHT_BG"],
                                border=ft.border.all(1, theme.get("COLOR_PRIMARY")),
                                border_radius=theme.get("SIDEBAR_FILE_ROW_RADIUS", 0),
                            ),
                            content_feedback=ft.Container(
                                content=ft.Text(
                                    file,
                                    size=theme["SIDEBAR_DRAG_FEEDBACK_TEXT_SIZE"],
                                    color=theme["SIDEBAR_DRAG_FEEDBACK_TEXT_COLOR"],
                                ),
                                bgcolor=theme.get("COLOR_PRIMARY"),
                                padding=theme["SIDEBAR_DRAG_FEEDBACK_PADDING"],
                                border_radius=theme["SIDEBAR_DRAG_FEEDBACK_RADIUS"],
                                opacity=theme["SIDEBAR_DROP_BAR_HOVER_OPACITY"],
                            ),
                            data=f"{folder_path}|{file}",
                        )

                        def drop_bar(insert_before: bool):
                            def on_accept_bar(
                                e,
                                parent_folder=folder_path,
                                target_file=file,
                                before=insert_before,
                            ):
                                dragged_parent, dragged_item = (None, None)
                                if page and hasattr(e, "src_id"):
                                    try:
                                        src_control = page.get_control(f"{e.src_id}")
                                        if src_control and hasattr(src_control, "data"):
                                            dragged_parent, dragged_item = (
                                                parse_drag_data(src_control.data)
                                            )
                                    except Exception:
                                        dragged_parent, dragged_item = (None, None)

                                if (
                                    dragged_parent == parent_folder
                                    and dragged_item
                                    and dragged_item != target_file
                                ):
                                    on_reorder(
                                        parent_folder, dragged_item, target_file, before
                                    )

                            def on_will_accept_bar(e):
                                will_accept = getattr(e, "data", None) == "true"
                                bar = e.control.content.content
                                bar.bgcolor = (
                                    theme["SIDEBAR_DROP_BAR_HOVER_BG"]
                                    if will_accept
                                    else theme["SIDEBAR_DROP_BAR_BG"]
                                )
                                bar.height = (
                                    theme["SIDEBAR_DROP_BAR_HOVER_HEIGHT"]
                                    if will_accept
                                    else theme["SIDEBAR_DROP_BAR_HEIGHT"]
                                )
                                bar.opacity = (
                                    theme["SIDEBAR_DROP_BAR_HOVER_OPACITY"]
                                    if will_accept
                                    else theme["SIDEBAR_DROP_BAR_OPACITY"]
                                )
                                e.control.update()

                            def on_leave_bar(e):
                                bar = e.control.content.content
                                bar.bgcolor = theme["SIDEBAR_DROP_BAR_BG"]
                                bar.height = theme["SIDEBAR_DROP_BAR_HEIGHT"]
                                bar.opacity = theme["SIDEBAR_DROP_BAR_OPACITY"]
                                e.control.update()

                            return ft.DragTarget(
                                group="reorder",
                                content=ft.Container(
                                    padding=ft.Padding(
                                        0,
                                        theme["SIDEBAR_DROP_BAR_PADDING_Y"],
                                        0,
                                        theme["SIDEBAR_DROP_BAR_PADDING_Y"],
                                    ),
                                    expand=True,
                                    content=ft.Container(
                                        height=theme["SIDEBAR_DROP_BAR_HEIGHT"],
                                        bgcolor=theme["SIDEBAR_DROP_BAR_BG"],
                                        opacity=theme["SIDEBAR_DROP_BAR_OPACITY"],
                                        expand=True,
                                    ),
                                ),
                                on_accept=on_accept_bar,
                                on_will_accept=on_will_accept_bar,
                                on_leave=on_leave_bar,
                            )

                        file_block = ft.Column(
                            [
                                drop_bar(True),
                                file_draggable,
                                drop_bar(False),
                            ],
                            spacing=theme["ZERO_SPACING"],
                        )
                        items.append(file_block)
                    else:
                        items.append(file_container)

        for idx, folder in enumerate(folders):
            add_folder_items(folder, depth=0, is_last_childs=[idx == len(folders) - 1])
            items.append(
                ft.Container(
                    content=ft.Divider(
                        height=theme["DIVIDER_HEIGHT"],
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
                    width=theme[
                        "SIDEBAR_SCROLLBAR_SPACER_WIDTH"
                    ],  # Reserve space for scrollbar
                    expand=True,
                    alignment=ft.alignment.center_right,
                    bgcolor=theme["COLOR_TRANSPARENT"],
                ),
            ]
        ),
        width=theme.get("SIDEBAR_WIDTH"),
        bgcolor=theme.get("SIDEBAR_BG"),
        padding=theme.get("SIDEBAR_PADDING"),
        border_radius=theme.get("BORDER_RADIUS"),
        expand=True,  # Responsive: fill available space
    )
