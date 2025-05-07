import discord
from discord.ext import commands, tasks
from discord import app_commands
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
tree = bot.tree  # Für App Commands (Slash-Befehle)

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
headers = {"Authorization": f"token {config['github']['token']}"}

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

    # Setze den Status und die Aktivität des Bots
    activity = discord.Game("Überwacht die Repositories")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    # Synchronisiere die App Commands
    await tree.sync()
    logger.info("Slash-Befehle synchronisiert.")

@tree.command(name="status", description="Zeigt den Status des Bots an.")
async def status(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Bot-Status",
        description="Ich bin online und überwache deine Repositories!",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@tree.command(name="repo", description="Zeigt Informationen zu einem Repository an.")
async def repo(interaction: discord.Interaction, repo_name: str):
    """Gibt Informationen zu einem Repository zurück."""
    # Falls kein "owner/" im Namen enthalten ist, füge den Standard-Owner hinzu
    if "/" not in repo_name:
        repo_name = f"the1andoni/{repo_name}"

    url = f"https://api.github.com/repos/{repo_name}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        repo_data = response.json()
        embed = discord.Embed(
            title=f"Repository: {repo_data['full_name']}",
            description=repo_data.get('description', 'Keine Beschreibung'),
            color=discord.Color.blue()
        )
        embed.add_field(name="Stars", value=repo_data['stargazers_count'], inline=True)
        embed.add_field(name="Forks", value=repo_data['forks_count'], inline=True)
        embed.add_field(name="Offene Issues", value=repo_data['open_issues_count'], inline=True)
        embed.set_thumbnail(url=repo_data['owner']['avatar_url'])  # Profilbild des Owners
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title="Fehler",
            description=f"Repository {repo_name} konnte nicht gefunden werden.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

@tasks.loop(minutes=5)  # Überprüft alle 5 Minuten auf neue Pull Requests
async def check_pull_requests():
    channel = bot.get_channel(int(discord_channel_id))
    if not channel:
        logger.error("Ungültige Discord-Kanal-ID: %s", discord_channel_id)
        await bot.change_presence(status=discord.Status.dnd, activity=discord.Game("Fehler: Kanal nicht gefunden"))
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

                        # Nachricht als Embed erstellen
                        embed = discord.Embed(
                            title=f"Neuer Pull Request: {pull['title']}",
                            description=f"Autor: {pull['user']['login']}\n[Zum Pull Request]({pull['html_url']})",
                            color=discord.Color.green()
                        )
                        embed.add_field(name="Prüfungsergebnisse", value=issues_summary or "Keine Probleme gefunden.")
                        await channel.send(embed=embed)

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
            await bot.change_presence(status=discord.Status.dnd, activity=discord.Game("Fehler: API-Problem"))

# Startet den Bot
bot.run(config["discord"]["token"])
