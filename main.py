import flet as ft
from ui.pages.main_page import main_page


def main(page: ft.Page):
    main_page(page)


ft.app(target=main)
