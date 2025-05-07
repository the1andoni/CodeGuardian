import logging
import os

def setup_logger():
    """Konfiguriert das Logging für den Bot."""
    # Bestimme den Pfad zum 'logs'-Ordner im Projektverzeichnis
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)  # Erstelle den Ordner 'logs', falls er nicht existiert

    # Konfiguriere das Logging
    logging.basicConfig(
        filename=os.path.join(log_dir, "bot.log"),  # Log-Datei im Ordner 'logs'
        level=logging.INFO,  # Log-Level
        format="%(asctime)s - %(levelname)s - %(message)s",  # Format der Log-Einträge
        datefmt="%Y-%m-%d %H:%M:%S",  # Datumsformat
    )
    logger = logging.getLogger("GithubBot")
    return logger

# Logger-Instanz erstellen
logger = setup_logger()