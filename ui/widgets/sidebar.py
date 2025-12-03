import flet as ft
from ui.themes.theme import theme
import sys

sys.path.append("../../backend")
from backend.files_manager import FOLDERS, list_markdown_files


def sidebar(expanded_folders, on_file_selected=None):
    def toggle_folder(folder):
        expanded_folders[folder] = not expanded_folders[folder]
        sidebar_view.controls.clear()
        sidebar_view.controls.extend(build_items())
        sidebar_view.update()

    def build_items():
        items = []
        for folder in FOLDERS:
            items.append(
                ft.ListTile(
                    title=ft.Text(
                        folder,
                        size=theme["SIDEBAR_TITLE_FONT_SIZE"],
                        weight=theme["SIDEBAR_TITLE_FONT_WEIGHT"],
                        color=theme["SIDEBAR_TITLE_COLOR"],
                    ),
                    hover_color=theme["COLOR_DIVIDER"],
                    dense=True,
                    on_click=lambda _, f=folder: toggle_folder(f),
                )
            )
            if expanded_folders[folder]:
                files = list_markdown_files(folder)
                for file in files:
                    items.append(
                        ft.ListTile(
                            title=ft.Text(
                                file,
                                color=theme["SIDEBAR_ITEM_COLOR"],
                            ),
                            hover_color=theme["COLOR_DIVIDER"],
                            dense=True,
                            on_click=lambda _, f=folder, fi=file: (
                                on_file_selected(f, fi) if on_file_selected else None
                            ),
                        )
                    )
            items.append(ft.Container(height=theme["SPACING_SM"]))
        return items

    sidebar_view = ft.Column(build_items(), expand=True)

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Text(
                        "Folders",
                        size=theme["SIDEBAR_TITLE_FONT_SIZE"],
                        weight=theme["SIDEBAR_TITLE_FONT_WEIGHT"],
                        color=theme["SIDEBAR_TITLE_COLOR"],
                    ),
                    margin=ft.Margin(0, 0, 0, theme["SPACING_LG"]),
                    alignment=ft.alignment.center,
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

    # (Removed unreachable duplicate return block)
