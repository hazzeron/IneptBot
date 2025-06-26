import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import discord
from discord import app_commands
from aiohttp import web

# Load .env and token
print("Current working directory:", Path('.').resolve())
dotenv_path = Path('.') / '.env'
print("Loading .env from:", dotenv_path.resolve())
load_dotenv(dotenv_path)
token = os.getenv("DISCORD_TOKEN")
print("DISCORD_TOKEN after loading .env:", token)

# Set up intents
intents = discord.Intents.default()
intents.guilds = True

# Client and command tree
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Embed function
async def send_rules_embed(channel):
    embed = discord.Embed(
        title="📜 Server Rules",
        description=(
            "**1. Be respectful**\n"
            "No hate speech, personal attacks, or harassment.\n\n"
            "**2. No spamming**\n"
            "Avoid excessive messages, emojis, or mentions.\n\n"
            "**3. Keep it on-topic**\n"
            "Use channels for their intended purpose.\n\n"
            "**4. No NSFW content**\n"
            "Keep everything safe for work and all ages.\n\n"
            "**5. Follow Discord's TOS**\n"
            "[Discord TOS](https://discord.com/terms)"
        ),
        color=discord.Color.blue()
    )
    embed.set_footer(text="React below to agree to the rules")

    message = await channel.send(embed=embed)
    await message.add_reaction("✅")

# Slash command
@tree.command(name="rules", description="Post the server rules embed.")
async def rules_command(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("🚫 You need Administrator permissions to use this command.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=False)
    await send_rules_embed(interaction.channel)

# on_ready
@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")
    await client.change_presence(activity=discord.Streaming(name="twitch.tv/ineptateverything", url="https://twitch.tv/ineptateverything"))

# Fly.io web handler
async def handle(request):
    return web.Response(text="Bot is running")

async def start_web_server():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server running on port {port}")

# Main function
async def main():
    await start_web_server()
    await client.start(token)

if __name__ == "__main__":
    asyncio.run(main())
