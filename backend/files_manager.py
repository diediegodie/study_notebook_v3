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
        # Update .order.json
        order = _ensure_order_file(folder_path)
        for item in order["items"]:
            if item["name"] == old_filename:
                item["name"] = new_filename
                break
        _save_order(folder_path, order)


def rename_folder(old_folder_path: str, new_folder_name: str) -> None:
    """Rename a folder (top-level or nested) and update .order.json in parent directory.

    Args:
        old_folder_path: Path to the folder being renamed (e.g., "Notebooks" or "Notebooks/Archive")
        new_folder_name: New name for the folder (just the name, not the full path)
    """
    # Determine the parent folder and the old folder name
    if "/" in old_folder_path:
        parts = old_folder_path.split("/")
        parent_path = "/".join(parts[:-1])
        old_folder_name = parts[-1]
        parent_full_path = os.path.join(BASE_DIR, parent_path)
    else:
        # Top-level folder
        old_folder_name = old_folder_path
        parent_full_path = BASE_DIR

    old_full_path = os.path.join(BASE_DIR, old_folder_path)
    new_full_path = os.path.join(parent_full_path, new_folder_name)

    # Rename the folder on filesystem
    if os.path.exists(old_full_path):
        os.rename(old_full_path, new_full_path)

        # Update .order.json in parent directory
        parent_order = _ensure_order_file(parent_full_path)
        for item in parent_order["items"]:
            if item["name"] == old_folder_name:
                item["name"] = new_folder_name
                break
        _save_order(parent_full_path, parent_order)


# Manual reorder for files in a folder
def reorder_files(folder: str, new_order: list) -> None:
    """Reorder files in the specified folder according to new_order (list of filenames)."""
    folder_path = os.path.join(BASE_DIR, folder)
    order = _ensure_order_file(folder_path)
    # Only reorder files, keep folders in place
    files = [item for item in order["items"] if item["type"] == "file"]
    # Build new file order
    name_to_item = {item["name"]: item for item in files}
    new_file_items = [name_to_item[name] for name in new_order if name in name_to_item]
    # Add any files not in new_order at the end (should not happen, but safe)
    remaining = [item for item in files if item["name"] not in new_order]
    new_file_items.extend(remaining)
    # Merge folders and files, keeping folders in their original order
    new_items = []
    for item in order["items"]:
        if item["type"] == "folder":
            new_items.append(item)
    new_items.extend(new_file_items)
    order["items"] = new_items
    _save_order(folder_path, order)


def reorder_items(parent_folder: str, new_order: list) -> None:
    """Reorder both files and folders in the specified parent folder.

    Args:
        parent_folder: Parent folder path (e.g., "" for root, "Notebooks" for nested)
        new_order: List of item names in desired order (both files and folders)
    """
    if parent_folder == "":
        folder_path = BASE_DIR
    else:
        folder_path = os.path.join(BASE_DIR, parent_folder)

    order = _ensure_order_file(folder_path)

    # Build a map of name to item
    name_to_item = {item["name"]: item for item in order["items"]}

    # Build new order based on new_order list
    new_items = []
    for name in new_order:
        if name in name_to_item:
            new_items.append(name_to_item[name])

    # Add any items not in new_order at the end (safety fallback)
    for item in order["items"]:
        if item["name"] not in new_order:
            new_items.append(item)

    order["items"] = new_items
    _save_order(folder_path, order)
