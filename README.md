# CodeGuardian

## Beschreibung
CodeGuardian ist ein Bot, der entwickelt wurde, um automatisierte Aufgaben auf GitHub zu erleichtern. Er bietet Funktionen wie Pull-Request-Überwachung, Code-Qualitätsprüfung und Sicherheitsprüfungen.

## Features
- **Automatische Überwachung von Pull Requests**: Erkennt neue Pull Requests und prüft die geänderten Dateien.
- **Code-Qualitätsprüfung**: Überprüft geänderte Dateien in Pull Requests mit `flake8`.
- **Sicherheitsprüfung**: Erkennt Sicherheitslücken in geänderten Dateien mit `bandit`.
- **Discord-Benachrichtigungen**: Sendet Ergebnisse der Prüfungen in einen Discord-Channel.
- **Interaktive Befehle**: Unterstützt Befehle wie `!status` und `!repo <repository_name>` im Discord-Channel.
- **Persistenz mit JSON**: Speichert gesendete Pull Requests in einer JSON-Datei, um doppelte Benachrichtigungen zu vermeiden.
- **Logging**: Protokolliert alle Ereignisse (z. B. neue Pull Requests, Fehler) in einer Log-Datei im Ordner `logs`.

## Projektstruktur

```
CodeGuardian
├── src
│   ├── bot.py                # Hauptdatei zum Starten des Bots
|   ├── config.yaml               # Konfigurationsdatei für den Bot
│   ├── github
│   │   ├── __init__.py       # Initialisierung des GitHub-Moduls
│   │   └── monitor.py        # Überwachung und Analyse von Pull Requests
│   ├── Discord
│   │   ├── __init__.py       # Initialisierung des Discord-Moduls
│   │   └── notifier.py       # Discord-Benachrichtigungslogik
│   └── utils
│       ├── __init__.py       # Initialisierung der Hilfsfunktionen
│       ├── helpers.py        # Hilfsfunktionen für verschiedene Aufgaben
│       ├── json_helper.py    # Funktionen zum Lesen/Schreiben von JSON-Dateien
│       └── logger.py         # Logger-Konfiguration
├── data
│   └── sent_pull_requests.json  # JSON-Datei zum Speichern gesendeter Pull Requests
├── logs
│   └── bot.log               # Log-Datei für Bot-Ereignisse
├── requirements.txt          # Abhängigkeiten des Projekts
├── LICENSE                   # Lizenzinformationen
└── README.md                 # Projektdokumentation
```

## Installation
1. Klone das Repository:
   ```bash
   git clone https://github.com/the1andoni/CodeGuardian.git
   ```
2. Navigiere in das Verzeichnis:
   ```bash
   cd CodeGuardian
   ```
3. Installiere die Abhängigkeiten:
   ```bash
   pip install -r requirements.txt
   ```
4. Stelle sicher, dass die Tools `flake8`, `black` und `bandit` installiert sind:
   ```bash
   pip install flake8 black bandit
   ```

## Nutzung
1. Konfiguriere die `config.yaml` Datei mit deinen GitHub- und Discord-Zugangsdaten sowie den zu überwachenden Repositories.
2. Starte den Bot:
   ```bash
   python src/bot.py
   ```

## Logging
- Alle Ereignisse werden in einer Log-Datei gespeichert, die sich im Ordner `logs` befindet.
- Die Log-Datei enthält Informationen wie Datum, Uhrzeit, Log-Level und die Nachricht.
- Beispiel für die Log-Datei:
  ```
  2025-05-07 06:00:00 - INFO - Bot wird gestartet...
  2025-05-07 06:00:05 - INFO - Bot is online as CodeGuardian#1234
  2025-05-07 06:05:00 - INFO - Neuer Pull Request geprüft: Fix Bug #42 von user123
  2025-05-07 06:05:05 - WARNING - Code-Qualitätsprobleme gefunden in src/utils/helpers.py: 3
  2025-05-07 06:10:00 - ERROR - Fehler beim Abrufen von Pull Requests für user/repo1: 403
  ```

## JSON-Daten
- Gesendete Pull Requests werden in der Datei `data/sent_pull_requests.json` gespeichert.
- Diese Datei wird automatisch erstellt und verwaltet.
- Beispiel für die JSON-Datei:
  ```json
  {
      "123456": {
          "title": "Fix Bug #42",
          "author": "user123",
          "url": "https://github.com/user/repo/pull/42"
      }
  }
  ```

## .gitignore
Um sicherzustellen, dass sensible oder temporäre Dateien nicht versehentlich veröffentlicht werden, enthält das Projekt eine `.gitignore`-Datei. Diese Datei ignoriert unter anderem:
- Log-Dateien (`logs/`)
- JSON-Daten (`data/sent_pull_requests.json`)
- Konfigurationsdateien (`config.yaml`)

Falls du weitere Dateien oder Ordner ignorieren möchtest, kannst du die `.gitignore`-Datei im Root-Verzeichnis des Projekts anpassen.

## Beiträge
Beiträge sind willkommen! Bitte erstelle einen Fork des Repositories und reiche einen Pull Request ein.

## Lizenz
Dieses Projekt steht unter der **CyberSpaceConsulting Public License v1.0**.  
Die vollständigen Lizenzbedingungen findest du in der [LICENSE](LICENSE)-Datei.

### Wichtige Punkte der Lizenz:
1. **Keine Weiterveräußerung oder öffentliche Verbreitung**:  
   Die Software darf nicht verkauft, unterlizenziert oder öffentlich weiterverbreitet werden, ohne vorherige schriftliche Genehmigung von CyberSpaceConsulting.
   
2. **Zentrale Verwaltung**:  
   Alle offiziellen Versionen und Updates werden ausschließlich über das ursprüngliche Repository verwaltet.

3. **Attribution erforderlich**:  
   Jede Nutzung oder Bereitstellung der Software muss die Herkunft des Projekts klar angeben:  
   "CyberSpaceConsulting – Original source available at the official repository."

4. **Kommerzielle Nutzung erlaubt (mit Einschränkungen)**:  
   Die Software darf in kommerziellen Kontexten verwendet werden, jedoch nicht als eigenständiges Produkt oder Dienstleistung weiterverkauft werden.

5. **Keine Garantie**:  
   Die Software wird "wie besehen" bereitgestellt, ohne jegliche Garantien oder Gewährleistungen.

6. **Verbotene Nutzung in KI-Training**:  
   Die Software darf nicht für das Training oder Fine-Tuning von KI-Modellen verwendet werden, ohne ausdrückliche Genehmigung.

Für weitere Informationen oder Genehmigungen, kontaktiere:  
📧 license@cyberspaceconsulting.de

## Kontakt
Bei Fragen oder Problemen, kontaktiere uns unter [info@cyberspaceconsulting.de](mailto:info@cyberspaceconsulting.de).