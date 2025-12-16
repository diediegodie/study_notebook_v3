import flet as ft


def register_esc_to_close_dialog(page: ft.Page, dialog_ref):
    """
    Registers a keyboard event handler to close the given dialog when ESC is pressed.
    dialog_ref: a reference to the dialog (e.g., a variable or ft.Ref)
    """

    def on_key(e: ft.KeyboardEvent):
        if e.key == "Escape" and getattr(dialog_ref, "open", False):
            dialog_ref.open = False
            page.update()

    page.on_keyboard_event = on_key
