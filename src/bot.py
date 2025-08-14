import discord
from discord.ext import commands, tasks
import aiohttp
import yaml
import os
import datetime
from database import Database
from command import CustomCommands

# Token aus config.yaml laden
with open("config.yaml", "r", encoding="utf-8") as f:
	config = yaml.safe_load(f)
TOKEN = config["token"]

CHECK_INTERVAL = 60  # Sekunden
LOG_FILE = os.path.join("Logs", "Bot.log")
db = Database()

def log_event(message, max_age_days=7):
	timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	log_line = f"[{timestamp}] {message}\n"

	# Alte Log-Zeilen entfernen
	try:
		if os.path.exists(LOG_FILE):
			with open(LOG_FILE, "r", encoding="utf-8") as f:
				lines = f.readlines()
			new_lines = []
			cutoff = datetime.datetime.now() - datetime.timedelta(days=max_age_days)
			for line in lines:
				if line.startswith("["):
					try:
						date_str = line.split("]")[0][1:]
						log_time = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
						if log_time >= cutoff:
							new_lines.append(line)
					except Exception:
						new_lines.append(line)
				else:
					new_lines.append(line)
		else:
			new_lines = []
	except Exception:
		new_lines = []

	new_lines.append(log_line)
	with open(LOG_FILE, "w", encoding="utf-8") as f:
		f.writelines(new_lines)

	# Log-Channel
	log_channel_id = db.get_log_channel_id()
	if log_channel_id:
		channel = bot.get_channel(log_channel_id)
		if channel:
			embed = discord.Embed(title="Bot Log", description=message, color=discord.Color.dark_grey())
			try:
				import asyncio
				asyncio.create_task(channel.send(embed=embed))
			except Exception:
				pass

class SiteMonitor:
	def __init__(self, db):
		self.db = db
		self.sites = self.db.load_sites()  # Lade aus DB
		self.stats = {}
		self.downtime_log = {}

	def add_site(self, url):
		self.sites[url] = True
		self.db.save_site(url)
		self.stats.setdefault(url, {"up": 0, "down": 0, "response_times": []})
		self.downtime_log.setdefault(url, [])
		log_event(f"Website hinzugefügt: {url}")

	def remove_site(self, url):
		self.sites.pop(url, None)
		self.db.delete_site(url)
		self.stats.pop(url, None)
		self.downtime_log.pop(url, None)
		log_event(f"Website entfernt: {url}")

	def get_status(self):
		return self.sites

	def log_downtime(self, url, timestamp):
		self.downtime_log[url].append(timestamp)
		log_event(f"Downtime bei {url} um {timestamp}")

monitor = SiteMonitor(db)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
	print(f"Bot online als {bot.user}")
	log_event(f"Bot online als {bot.user}")
	bot.add_cog(CustomCommands(bot, db, monitor))
	check_websites.start()

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_websites():
	async with aiohttp.ClientSession() as session:
		for url in list(monitor.sites.keys()):
			try:
				async with session.get(url, timeout=10) as resp:
					response_time = resp.elapsed.total_seconds() if hasattr(resp, 'elapsed') else None
					if resp.status == 200:
						monitor.stats[url]["up"] += 1
						if response_time:
							monitor.stats[url]["response_times"].append(response_time)
						monitor.sites[url] = True
					else:
						monitor.stats[url]["down"] += 1
						monitor.sites[url] = False
						await notify_downtime(url)
						monitor.log_downtime(url, discord.utils.utcnow())
						log_event(f"Seite offline: {url}")
			except Exception as e:
				monitor.stats[url]["down"] += 1
				monitor.sites[url] = False
				await notify_downtime(url)
				monitor.log_downtime(url, discord.utils.utcnow())
				log_event(f"Fehler beim Check von {url}: {e}")

async def notify_downtime(url):
	channel_id = db.get_channel_id()
	if not channel_id:
		return
	channel = bot.get_channel(channel_id)
	if channel:
		embed = discord.Embed(title="Seite offline", description=f"{url}", color=discord.Color.red())
		await channel.send(embed=embed)

if __name__ == "__main__":
	bot.run(TOKEN)
