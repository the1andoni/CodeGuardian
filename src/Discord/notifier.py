import discord
from discord.ext import commands, tasks
from discord import app_commands
import requests
import yaml
from utils.helpers import summarize_issues
from utils.logger import logger
from utils.json_helper import load_json, save_json
import os
from github.monitor import get_pull_request_issues
import time

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
repositories = config["github"].get("repositories", [])  # <-- github statt discord!
discord_channel_id = config["discord"]["channel_id"]
headers = {"Authorization": f"token {config['github']['token']}"}

# Templates aus der Config laden
notifications = config.get("notifications", {})
pr_template = notifications.get(
    "message_template",
    "A new pull request has been created: **{title}** by **{author}**. View it here: {url}"
)
issue_template = notifications.get(
    "issue_template",
    "Problems were found in pull request **{title}** by **{author}**:\n{issues}\n[View PR]({url})"
)

# JSON-Datei für gesendete Pull Requests
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))  # Gehe drei Ebenen nach oben
DATA_DIR = os.path.join(BASE_DIR, "data")
SENT_PULL_REQUESTS_FILE = os.path.join(DATA_DIR, "sent_pull_requests.json")
ISSUES_FILE = os.path.join(DATA_DIR, "sent_issues.json")

# Sicherstellen, dass der Ordner 'data' existiert
os.makedirs(DATA_DIR, exist_ok=True)

# Lade bereits gesendete Pull Requests und Issues
sent_pull_requests = load_json(SENT_PULL_REQUESTS_FILE)
sent_issues = load_json(ISSUES_FILE)

@bot.event
async def on_ready():
    try:
        logger.info("Bot is online as %s", bot.user)
        print(f"Bot is online as {bot.user}")

        # Setze den Status und die Aktivität des Bots
        activity = discord.Game("Überwacht die Repositories")
        await bot.change_presence(status=discord.Status.online, activity=activity)

        # Synchronisiere die App Commands
        await tree.sync()
        logger.info("Slash-Befehle synchronisiert.")

        # Starte die neue Überwachungs-Task
        check_all_pull_requests_and_issues.start()
        check_github_issues.start()
    except Exception as e:
        # Fehler beim Starten des Bots
        logger.error("Fehler beim Starten des Bots: %s", str(e))
        activity = discord.Game("Fehler: Bot konnte nicht starten")
        await bot.change_presence(status=discord.Status.dnd, activity=activity)

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

@tasks.loop(minutes=5)
async def check_all_pull_requests_and_issues():
    try:
        channel = bot.get_channel(int(discord_channel_id))
        if not channel:
            raise ValueError(f"Ungültige Discord-Kanal-ID: {discord_channel_id}")

        pr_issues = get_pull_request_issues()
        for repo, pull, issues_summary in pr_issues:
            pr_id = str(pull["id"])
            is_new = pr_id not in sent_pull_requests
            has_issues = issues_summary.strip() and issues_summary.strip() != "Keine Probleme gefunden."

            # Nur neue PRs oder neue Issues melden
            if is_new or has_issues:
                if has_issues:
                    # Issue-Template verwenden
                    msg = issue_template.format(
                        title=pull["title"],
                        author=pull["user"]["login"],
                        issues=issues_summary,
                        url=pull["html_url"]
                    )
                    embed = discord.Embed(
                        title=f"Issues in Pull Request: {pull['title']}",
                        description=f"Autor: {pull['user']['login']}\n[Zum Pull Request]({pull['html_url']})",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="Prüfungsergebnisse", value=issues_summary or "Keine Probleme gefunden.")
                else:
                    # PR-Template verwenden
                    msg = pr_template.format(
                        title=pull["title"],
                        author=pull["user"]["login"],
                        url=pull["html_url"]
                    )
                    embed = discord.Embed(
                        title=f"Neuer Pull Request: {pull['title']}",
                        description=f"Autor: {pull['user']['login']}\n[Zum Pull Request]({pull['html_url']})",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Prüfungsergebnisse", value=issues_summary or "Keine Probleme gefunden.")

                await channel.send(content=msg, embed=embed)

                logger.info(
                    "Pull Request geprüft: %s von %s",
                    pull["title"],
                    pull["user"]["login"],
                )
                sent_pull_requests[pr_id] = {
                    "title": pull["title"],
                    "author": pull["user"]["login"],
                    "url": pull["html_url"],
                }
                save_json(SENT_PULL_REQUESTS_FILE, sent_pull_requests)
    except Exception as e:
        logger.error("Fehler beim Überprüfen der Pull Requests: %s", str(e))
        activity = discord.Game("Fehler: Überprüfung fehlgeschlagen")
        await bot.change_presence(status=discord.Status.dnd, activity=activity)

@tasks.loop(minutes=5)
async def check_github_issues():
    try:
        channel = bot.get_channel(int(discord_channel_id))
        if not channel:
            raise ValueError(f"Ungültige Discord-Kanal-ID: {discord_channel_id}")

        for repo in repositories:
            url = f"https://api.github.com/repos/{repo}/issues"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                issues = response.json()
                for issue in issues:
                    # Pull Requests sind auch Issues, aber haben einen 'pull_request'-Key
                    if "pull_request" in issue:
                        continue
                    issue_id = str(issue["id"])
                    if issue_id not in sent_issues:
                        embed = discord.Embed(
                            title=f"New Issue: {issue['title']}",
                            description=issue.get("body", "No description"),
                            color=discord.Color.orange(),
                            url=issue["html_url"]
                        )
                        embed.add_field(name="Author", value=issue["user"]["login"])
                        embed.add_field(name="Repository", value=repo)
                        await channel.send(embed=embed)
                        sent_issues[issue_id] = {
                            "title": issue["title"],
                            "author": issue["user"]["login"],
                            "url": issue["html_url"],
                            "created_at": issue["created_at"]
                        }
                        save_json(ISSUES_FILE, sent_issues)
            else:
                logger.error(f"Fehler beim Abrufen der Issues von {repo}: {response.status_code}")
    except Exception as e:
        logger.error("Fehler beim Überprüfen der Issues: %s", str(e))

# Startet den Bot
bot.run(config["discord"]["token"])
