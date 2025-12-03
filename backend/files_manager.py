import os
from typing import List

BASE_DIR = os.path.join(os.path.dirname(__file__), "../notebooks")
FOLDERS = ["Notebooks", "Resources", "Archive"]


def list_markdown_files(folder: str) -> List[str]:
    folder_path = os.path.join(BASE_DIR, folder)
    if not os.path.exists(folder_path):
        return []
    return [f for f in os.listdir(folder_path) if f.endswith(".md")]


def read_markdown_file(folder: str, filename: str) -> str:
    file_path = os.path.join(BASE_DIR, folder, filename)
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def save_markdown_file(folder: str, filename: str, content: str) -> None:
    folder_path = os.path.join(BASE_DIR, folder)
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def delete_markdown_file(folder: str, filename: str) -> None:
    file_path = os.path.join(BASE_DIR, folder, filename)
    if os.path.exists(file_path):
        os.remove(file_path)


def rename_markdown_file(folder: str, old_filename: str, new_filename: str) -> None:
    folder_path = os.path.join(BASE_DIR, folder)
    old_path = os.path.join(folder_path, old_filename)
    new_path = os.path.join(folder_path, new_filename)
    if os.path.exists(old_path):
        os.rename(old_path, new_path)
