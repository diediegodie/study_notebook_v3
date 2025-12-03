import flet as ft
from ui.themes.theme import theme


def main_container():
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Welcome to your notebook!",
                    size=theme["MAIN_CONTENT_FONT_SIZE"],
                    color=theme["MAIN_CONTENT_COLOR"],
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
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
