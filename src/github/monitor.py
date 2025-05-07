import requests
import yaml
from utils.helpers import comment_on_pull_request, summarize_issues, load_config

def monitor_repositories():
    config = load_config()
    if "github" not in config or "token" not in config["github"]:
        raise ValueError("Fehlende GitHub-Konfiguration in config.yaml")
    token = config["github"]["token"]
    repositories = config["github"].get("repositories", [])
    headers = {"Authorization": f"token {token}"}

    for repo in repositories:
        url = f"https://api.github.com/repos/{repo}/pulls"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            pulls = response.json()
            print(f"Repository: {repo} - {len(pulls)} offene Pull Requests")
            for pull in pulls:
                pull_number = pull["number"]
                files_url = pull["_links"]["self"]["href"] + "/files"
                files_response = requests.get(files_url, headers=headers)
                if files_response.status_code == 200:
                    files = files_response.json()
                    issues_summary = ""
                    for file in files:
                        file_path = file["filename"]
                        issues_summary += f"\n**{file_path}**:\n{summarize_issues(file_path)}"

                    if issues_summary.strip():
                        # Kommentar im Pull Request hinzufügen
                        comment = f"Automatische Prüfung abgeschlossen:\n{issues_summary}"
                        comment_on_pull_request(repo, pull_number, comment, headers)
        else:
            print(f"Fehler beim Abrufen von {repo}: {response.status_code}")

if __name__ == "__main__":
    monitor_repositories()