import requests
import yaml

def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)

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
        else:
            print(f"Fehler beim Abrufen von {repo}: {response.status_code}")

if __name__ == "__main__":
    monitor_repositories()