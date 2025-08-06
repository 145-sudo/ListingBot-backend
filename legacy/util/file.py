import os
import json
import logging


def save_json_to_dir(data, filename: str, dir_name="category"):
    """
    Save a Python object as a JSON file in the specified directory.

    Args:
        data: The Python object to save (e.g., list or dict).
        filename: The name of the JSON file (e.g., "ssi.json").
        dir_name: The directory to save the file in (default: "category").
    """
    filename = filename.lower()
    os.makedirs(dir_name, exist_ok=True)
    file_path = os.path.join(dir_name, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logging.info(f"Saved {len(data)} items to {file_path}")


def load_json_from_dir(filename: str, dir_name="category"):
    """
    Load a JSON file from the specified directory.
    """
    filename = filename.lower()
    file_path = os.path.join(dir_name, filename)
    with open(file_path, "r", encoding="utf-8") as f:
        logging.info(f"Loading {filename} from {file_path}")
        return json.load(f)
