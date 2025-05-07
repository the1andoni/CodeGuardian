import yaml
import asyncio
from github.monitor import monitor_repositories
from Discord.notifier import bot
from utils.logger import logger

def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)

config = load_config()

async def start_monitoring():
    """Asynchroner Task für die GitHub-Überwachung."""
    try:
        while True:
            monitor_repositories()
            await asyncio.sleep(300)  # Alle 5 Minuten ausführen
    except asyncio.CancelledError:
        logger.info("GitHub-Monitoring-Task wurde beendet.")

async def main():
    """Startet den Discord-Bot und die GitHub-Überwachung parallel."""
    logger.info("Bot wird gestartet...")
    # Starte die GitHub-Überwachung und den Discord-Bot parallel
    monitoring_task = asyncio.create_task(start_monitoring())
    try:
        await bot.start(config["discord"]["token"])
    except Exception as e:
        logger.error(f"Ein Fehler ist aufgetreten: {e}")
    finally:
        # Beende den Monitoring-Task, wenn der Bot gestoppt wird
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            logger.info("Monitoring-Task wurde erfolgreich abgebrochen.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot wurde durch KeyboardInterrupt beendet.")
