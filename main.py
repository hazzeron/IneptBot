import discord
import os

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')
    await client.change_presence(activity=discord.Streaming(
        name="twitch.tv/ineptateverything",
        url="https://twitch.tv/ineptateverything"
    ))

client.run(os.getenv("DISCORD_TOKEN"))
