import requests
import subprocess
import json
import yaml
import os 
from flake8.api import legacy as flake8
from black import format_file_in_place, FileMode
from bandit.core import manager as bandit_manager
from utils.logger import logger

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_path = os.path.join(base_dir, "config.yaml")
# Konfiguration laden
def load_config():
       with open(config_path, "r") as file:
        return yaml.safe_load(file)

config = load_config()

def format_message(title, url, author):
    """Formatiert eine Nachricht für Pull-Request-Benachrichtigungen."""
    return f"**{title}**\nSubmitted by: {author}\nView Pull Request: {url}"

def extract_repo_info(pull_request):
    """Extrahiert relevante Informationen aus einem Pull Request."""
    return {
        "title": pull_request.get("title"),
        "url": pull_request.get("html_url"),
        "author": pull_request.get("user", {}).get("login")
    }

def is_valid_pull_request(pull_request):
    """Überprüft, ob ein Pull Request gültig ist (offen und kein Entwurf)."""
    return pull_request.get("state") == "open" and pull_request.get("draft") is False

def handle_api_error(response):
    """Behandelt API-Fehler und gibt eine aussagekräftige Fehlermeldung aus."""
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code} - {response.text}")

def check_code_quality(file_path):
    """
    Führt eine Code-Qualitätsprüfung mit flake8 durch.
    Gibt eine Liste von Problemen zurück, falls welche gefunden werden.
    """
    try:
        result = subprocess.run(
            ["flake8", file_path, "--format=json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            logger.info("Code-Qualitätsprüfung bestanden: %s", file_path)
            return []  # Keine Probleme gefunden
        issues = json.loads(result.stdout)
        logger.warning("Code-Qualitätsprobleme gefunden in %s: %d", file_path, len(issues))
        return issues
    except Exception as e:
        logger.error("Fehler bei der Code-Qualitätsprüfung für %s: %s", file_path, str(e))
        raise Exception(f"Fehler bei der Code-Qualitätsprüfung: {str(e)}")

def suggest_code_changes(file_path):
    """
    Führt eine automatische Formatierung mit black durch und gibt die Änderungen zurück.
    """
    try:
        result = subprocess.run(
            ["black", "--diff", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            return result.stdout  # Gibt die vorgeschlagenen Änderungen zurück
        else:
            raise Exception(f"Fehler bei der Code-Formatierung: {result.stderr}")
    except Exception as e:
        raise Exception(f"Fehler bei der Code-Formatierung: {str(e)}")

def detect_security_issues(file_path):
    """
    Führt eine Sicherheitsprüfung mit bandit durch.
    Gibt eine Liste von Sicherheitslücken zurück, falls welche gefunden werden.
    """
    try:
        bandit_config = config.get("monitoring", {}).get("bandit_config", {})
        result = subprocess.run(
            ["bandit", "-f", "json", "-r", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            return []  # Keine Sicherheitsprobleme gefunden
        return json.loads(result.stdout)["results"]  # Gibt die Sicherheitsprobleme zurück
    except Exception as e:
        raise Exception(f"Fehler bei der Sicherheitsprüfung: {str(e)}")

def summarize_issues(file_path):
    """
    Führt Code-Qualitäts- und Sicherheitsprüfungen durch und gibt eine Zusammenfassung zurück.
    """
    quality_issues = check_code_quality(file_path)
    security_issues = detect_security_issues(file_path)

    summary = []
    if quality_issues:
        summary.append(f"Code-Qualitätsprobleme gefunden: {len(quality_issues)}")
    if security_issues:
        summary.append(f"Sicherheitsprobleme gefunden: {len(security_issues)}")

    return "\n".join(summary) if summary else "Keine Probleme gefunden."

def comment_on_pull_request(repo, pull_number, comment, headers):
    """
    Fügt einen Kommentar zu einem Pull Request hinzu.
    :param repo: Name des Repositories (z. B. "user/repo").
    :param pull_number: Nummer des Pull Requests.
    :param comment: Der Kommentartext.
    :param headers: HTTP-Header mit Authentifizierung.
    """
    url = f"https://api.github.com/repos/{repo}/issues/{pull_number}/comments"
    response = requests.post(url, headers=headers, json={"body": comment})
    if response.status_code == 201:
        logger.info(f"Kommentar erfolgreich hinzugefügt: {comment}")
    else:
        logger.error(f"Fehler beim Hinzufügen des Kommentars: {response.status_code} - {response.text}")

def send_discord_issue_notification(repo, pull, issues_summary):
    """
    Sendet eine Nachricht an Discord, wenn Issues gefunden wurden.
    """
    import os
    webhook_url = os.environ.get("DISCORD_ISSUE_WEBHOOK_URL")
    if not webhook_url:
        return
    embed = {
        "title": f"Issues in Pull Request: {pull['title']}",
        "description": f"Autor: {pull['user']['login']}\n[Zum Pull Request]({pull['html_url']})",
        "color": 0xFF0000,
        "fields": [
            {"name": "Prüfungsergebnisse", "value": issues_summary or "Keine Probleme gefunden."}
        ]
    }
    data = {"embeds": [embed]}
    try:
        requests.post(webhook_url, json=data)
    except Exception as e:
        logger.error(f"Fehler beim Senden der Discord-Issue-Nachricht: {e}")
