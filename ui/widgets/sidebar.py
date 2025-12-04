import flet as ft
from ui.themes.theme import theme
from backend.files_manager import (
    list_folders,
    list_markdown_files,
    create_folder,
    delete_folder,
)


def sidebar(
    expanded_folders,
    on_file_selected=None,
    on_delete_file=None,
    on_delete_folder=None,
    on_create_folder_dialog=None,
    on_create_folder=None,
):
    expanded_folders = expanded_folders or {}
    folders = list_folders()
    if not expanded_folders:
        expanded_folders = {f: i == 0 for i, f in enumerate(folders)}

    # Ensure all handlers are always callable
    if on_delete_folder is None:
        on_delete_folder = lambda *_: None
    if on_file_selected is None:
        on_file_selected = lambda *_: None
    if on_delete_file is None:
        on_delete_file = lambda *_: None

    def build_items():
        items = []
        for folder in folders:
            items.append(
                ft.Row(
                    [
                        ft.Text(
                            folder,
                            size=theme["SIDEBAR_TITLE_FONT_SIZE"],
                            weight=theme["SIDEBAR_TITLE_FONT_WEIGHT"],
                            color=theme["SIDEBAR_TITLE_COLOR"],
                        ),
                        ft.PopupMenuButton(
                            icon=ft.Icons.MORE_VERT,
                            items=[
                                ft.PopupMenuItem(
                                    text="Delete",
                                    icon=ft.Icons.DELETE,
                                    on_click=(
                                        (lambda _e, f=folder: on_delete_folder(f))
                                        if on_delete_folder
                                        else None
                                    ),
                                )
                            ],
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )
            if expanded_folders.get(folder, False):
                files = list_markdown_files(folder)
                for file in files:
                    items.append(
                        ft.Row(
                            [
                                ft.TextButton(
                                    text=file,
                                    on_click=(
                                        (
                                            lambda _e, f=folder, fi=file: on_file_selected(
                                                f, fi
                                            )
                                        )
                                        if on_file_selected
                                        else None
                                    ),
                                ),
                                ft.PopupMenuButton(
                                    icon=ft.Icons.MORE_VERT,
                                    items=[
                                        ft.PopupMenuItem(
                                            text="Delete",
                                            icon=ft.Icons.DELETE,
                                            on_click=(
                                                (
                                                    lambda _e, f=folder, fi=file: on_delete_file(
                                                        f, fi
                                                    )
                                                )
                                                if on_delete_file
                                                else None
                                            ),
                                        )
                                    ],
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        )
                    )
            items.append(ft.Container(height=theme["SPACING_SM"]))
        return items

    sidebar_view = ft.ListView(
        controls=build_items(),
        expand=True,
        spacing=theme["SPACING_XS"],
        padding=0,
    )
    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(
                            "Folders",
                            size=theme["SIDEBAR_TITLE_FONT_SIZE"],
                            weight=theme["SIDEBAR_TITLE_FONT_WEIGHT"],
                            color=theme["SIDEBAR_TITLE_COLOR"],
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CREATE_NEW_FOLDER,
                            icon_size=theme["ICON_SIZE_MD"],
                            tooltip="Create Folder",
                            on_click=(
                                on_create_folder_dialog
                                if on_create_folder_dialog
                                else (lambda e: None)
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                sidebar_view,
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            expand=True,
        ),
        width=theme["SIDEBAR_WIDTH"],
        bgcolor=theme["SIDEBAR_BG"],
        padding=theme["SIDEBAR_PADDING"],
        border_radius=theme["BORDER_RADIUS"],
    )
