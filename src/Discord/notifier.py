import discord
from discord.ext import commands, tasks
import requests
import yaml
from utils.helpers import summarize_issues
from utils.logger import logger
from utils.json_helper import load_json, save_json
import os

# Bot-Setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Aktiviert den Zugriff auf Nachrichteninhalte
bot = commands.Bot(command_prefix="!", intents=intents)

# Konfiguration laden
def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)

config = load_config()

if "discord" not in config or "token" not in config["discord"]:
    raise ValueError("Fehlende Discord-Konfiguration in config.yaml")

discord_token = config["discord"]["token"]
repositories = config["discord"].get("repositories", [])
discord_channel_id = config["discord"]["channel_id"]
headers = {"Authorization": f"token {discord_token}"}

# JSON-Datei für gesendete Pull Requests
DATA_DIR = "data"
SENT_PULL_REQUESTS_FILE = os.path.join(DATA_DIR, "sent_pull_requests.json")

# Sicherstellen, dass der Ordner 'data' existiert
os.makedirs(DATA_DIR, exist_ok=True)

# Lade bereits gesendete Pull Requests
sent_pull_requests = load_json(SENT_PULL_REQUESTS_FILE)

@bot.event
async def on_ready():
    logger.info("Bot is online as %s", bot.user)
    print(f"Bot is online as {bot.user}")
    check_pull_requests.start()  # Startet die Überwachung von Pull Requests

@bot.command()
async def status(ctx):
    await ctx.send("Ich bin online und überwache deine Repositories!")

@bot.command()
async def repo(ctx, repo_name: str):
    """Gibt Informationen zu einem Repository zurück."""
    url = f"https://api.github.com/repos/{repo_name}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        repo_data = response.json()
        message = (
            f"**Repository:** {repo_data['full_name']}\n"
            f"**Beschreibung:** {repo_data.get('description', 'Keine Beschreibung')}\n"
            f"**Stars:** {repo_data['stargazers_count']}\n"
            f"**Forks:** {repo_data['forks_count']}\n"
            f"**Offene Issues:** {repo_data['open_issues_count']}"
        )
        await ctx.send(message)
    else:
        await ctx.send(f"Fehler: Repository {repo_name} konnte nicht gefunden werden.")

@tasks.loop(minutes=5)  # Überprüft alle 5 Minuten auf neue Pull Requests
async def check_pull_requests():
    channel = bot.get_channel(int(discord_channel_id))
    if not channel:
        logger.error("Ungültige Discord-Kanal-ID: %s", discord_channel_id)
        return

    for repo in repositories:
        url = f"https://api.github.com/repos/{repo}/pulls"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            pulls = response.json()
            for pull in pulls:
                if str(pull["id"]) not in sent_pull_requests:
                    # Geänderte Dateien abrufen
                    files_url = pull["url"] + "/files"
                    files_response = requests.get(files_url, headers=headers)
                    if files_response.status_code == 200:
                        files = files_response.json()
                        issues_summary = ""
                        for file in files:
                            file_path = file["filename"]
                            issues_summary += f"\n**{file_path}**:\n{summarize_issues(file_path)}"

                        # Nachricht erstellen
                        message = (
                            f"**Neuer Pull Request:** {pull['title']}\n"
                            f"**Autor:** {pull['user']['login']}\n"
                            f"**Link:** {pull['html_url']}\n"
                            f"**Prüfungsergebnisse:**\n{issues_summary}"
                        )
                        await channel.send(message)
                        logger.info(
                            "Neuer Pull Request geprüft: %s von %s",
                            pull["title"],
                            pull["user"]["login"],
                        )
                        # Speichere den Pull Request in der JSON-Datei
                        sent_pull_requests[str(pull["id"])] = {
                            "title": pull["title"],
                            "author": pull["user"]["login"],
                            "url": pull["html_url"],
                        }
                        save_json(SENT_PULL_REQUESTS_FILE, sent_pull_requests)
        else:
            logger.error(
                "Fehler beim Abrufen von Pull Requests für %s: %s",
                repo,
                response.status_code,
            )

# Startet den Bot
bot.run(config["discord"]["token"])
