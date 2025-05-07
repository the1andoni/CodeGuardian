import json
import os

def load_json(file_path):
    """Lädt Daten aus einer JSON-Datei."""
    if not os.path.exists(file_path):
        return {}  # Gibt ein leeres Dictionary zurück, wenn die Datei nicht existiert
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def save_json(file_path, data):
    """Speichert Daten in einer JSON-Datei."""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)