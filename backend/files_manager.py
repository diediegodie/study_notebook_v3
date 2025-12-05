import os
from typing import List

import time
import json

BASE_DIR = os.path.join(os.path.dirname(__file__), "../notebooks")

ORDER_FILENAME = ".order.json"


def _order_file_path(folder_path):
    return os.path.join(folder_path, ORDER_FILENAME)


def _load_order(folder_path):
    order_path = _order_file_path(folder_path)
    if os.path.exists(order_path):
        with open(order_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {"items": []}
    return {"items": []}


def _save_order(folder_path, order):
    order_path = _order_file_path(folder_path)
    with open(order_path, "w", encoding="utf-8") as f:
        json.dump(order, f, indent=2)


def _sync_order_with_fs(folder_path):
    # Ensure .order.json matches actual files/folders
    items = []
    for name in os.listdir(folder_path):
        if name.startswith(".") or name == ORDER_FILENAME:
            continue
        abs_path = os.path.join(folder_path, name)
        if os.path.isdir(abs_path):
            item_type = "folder"
        elif name.endswith(".md"):
            item_type = "file"
        else:
            continue
        try:
            created = int(os.path.getctime(abs_path))
        except Exception:
            created = int(time.time())
        items.append({"name": name, "type": item_type, "created": created})
    # Remove duplicates, keep only one per name
    seen = set()
    unique_items = []
    for item in items:
        if item["name"] not in seen:
            unique_items.append(item)
            seen.add(item["name"])
    # Sort by created desc
    unique_items.sort(key=lambda x: -x["created"])
    order = {"items": unique_items}
    _save_order(folder_path, order)
    return order


def _ensure_order_file(folder_path):
    order_path = _order_file_path(folder_path)
    if not os.path.exists(order_path):
        return _sync_order_with_fs(folder_path)
    return _load_order(folder_path)


# Default folders (used for initial state/UI)
DEFAULT_FOLDERS = ["Notebooks", "Resources", "Archive"]


def list_folders() -> list:
    """List all folders in BASE_DIR, ordered by .order.json (most recent first)."""
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR, exist_ok=True)
    order = _ensure_order_file(BASE_DIR)
    # Only folders
    folders = [item["name"] for item in order["items"] if item["type"] == "folder"]
    # Fallback: add any missing folders
    fs_folders = [
        f
        for f in os.listdir(BASE_DIR)
        if os.path.isdir(os.path.join(BASE_DIR, f)) and not f.startswith(".")
    ]
    for f in fs_folders:
        if f not in folders:
            folders.insert(0, f)
    return folders


def create_folder(folder: str) -> None:
    """Create a new top-level folder in BASE_DIR and update .order.json."""
    folder_path = os.path.join(BASE_DIR, folder)
    os.makedirs(folder_path, exist_ok=True)
    order = _ensure_order_file(BASE_DIR)
    now = int(time.time())
    # Remove if already exists (avoid duplicates)
    order["items"] = [i for i in order["items"] if i["name"] != folder]
    order["items"].insert(0, {"name": folder, "type": "folder", "created": now})
    _save_order(BASE_DIR, order)
    # Create .order.json in new folder
    _ensure_order_file(folder_path)


def create_subfolder(parent_folder: str, subfolder_name: str) -> None:
    """Create a subfolder inside parent_folder and update .order.json."""
    parent_path = os.path.join(BASE_DIR, parent_folder)
    folder_path = os.path.join(parent_path, subfolder_name)
    os.makedirs(folder_path, exist_ok=True)
    order = _ensure_order_file(parent_path)
    now = int(time.time())
    order["items"] = [i for i in order["items"] if i["name"] != subfolder_name]
    order["items"].insert(0, {"name": subfolder_name, "type": "folder", "created": now})
    _save_order(parent_path, order)
    _ensure_order_file(folder_path)


def create_file(folder: str, filename: str) -> None:
    """Create a new markdown file in the specified folder and update .order.json."""
    folder_path = os.path.join(BASE_DIR, folder)
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, filename)
    if not filename.endswith(".md"):
        file_path += ".md"
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("")
        order = _ensure_order_file(folder_path)
        now = int(time.time())
        order["items"] = [
            i for i in order["items"] if i["name"] != os.path.basename(file_path)
        ]
        order["items"].insert(
            0, {"name": os.path.basename(file_path), "type": "file", "created": now}
        )
        _save_order(folder_path, order)


def delete_folder(folder: str) -> None:
    """Delete a folder and all its contents from BASE_DIR and update .order.json."""
    import shutil

    folder_path = os.path.join(BASE_DIR, folder)
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        shutil.rmtree(folder_path)
        order = _ensure_order_file(BASE_DIR)
        order["items"] = [i for i in order["items"] if i["name"] != folder]
        _save_order(BASE_DIR, order)


FOLDERS = DEFAULT_FOLDERS  # For legacy compatibility; prefer list_folders() in UI


def list_markdown_files(folder: str) -> List[str]:
    folder_path = os.path.join(BASE_DIR, folder)
    if not os.path.exists(folder_path):
        return []
    order = _ensure_order_file(folder_path)
    files = [item["name"] for item in order["items"] if item["type"] == "file"]
    # Fallback: add any missing files
    fs_files = [f for f in os.listdir(folder_path) if f.endswith(".md")]
    for f in fs_files:
        if f not in files:
            files.insert(0, f)
    return files


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
        order = _ensure_order_file(os.path.join(BASE_DIR, folder))
        order["items"] = [i for i in order["items"] if i["name"] != filename]
        _save_order(os.path.join(BASE_DIR, folder), order)


def rename_markdown_file(folder: str, old_filename: str, new_filename: str) -> None:
    folder_path = os.path.join(BASE_DIR, folder)
    old_path = os.path.join(folder_path, old_filename)
    new_path = os.path.join(folder_path, new_filename)
    if os.path.exists(old_path):
        os.rename(old_path, new_path)
