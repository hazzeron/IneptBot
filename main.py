import os
from pathlib import Path
from dotenv import load_dotenv
import discord

# Debug prints to confirm dotenv loading and token
print("Current working directory:", Path('.').resolve())

dotenv_path = Path('.') / '.env'
print("Loading .env from:", dotenv_path.resolve())

loaded = load_dotenv(dotenv_path)
print("load_dotenv returned:", loaded)

token = os.getenv("DISCORD_TOKEN")
print("DISCORD_TOKEN after loading .env:", token, type(token))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    await client.change_presence(activity=discord.Streaming(name="twitch.tv/ineptateverything", url="https://twitch.tv/ineptateverything"))

client.run(token)
