import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import discord
from aiohttp import web

# Debug prints to confirm dotenv loading and token
print("Current working directory:", Path('.').resolve())

dotenv_path = Path('.') / '.env'
print("Loading .env from:", dotenv_path.resolve())

loaded = load_dotenv(dotenv_path)
print("load_dotenv returned:", loaded)

token = os.getenv("DISCORD_TOKEN")
print("DISCORD_TOKEN after loading .env:", token, type(token))

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True  # Needed to receive message events
intents.guilds = True    # Needed for guild and permission info
client = discord.Client(intents=intents)

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

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    await client.change_presence(activity=discord.Streaming(name="twitch.tv/ineptateverything", url="https://twitch.tv/ineptateverything"))

@client.event
async def on_message(message):
    print(f"Message received: {message.content} from {message.author}")  # Add this
    # Ignore messages from bots (including self)
    if message.author.bot:
        return

    # Only respond to "!rules" command
    if message.content.lower() == "!rules":
        # Ensure command is used in a guild text channel
        if not message.guild:
            await message.channel.send("This command can only be used in a server.")
            return

        # Check if author has Administrator permissions
        if not message.author.guild_permissions.administrator:
            await message.channel.send("🚫 You need Administrator permissions to use this command.")
            return

        await send_rules_embed(message.channel)

# Minimal aiohttp web server to keep Fly.io happy
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

# Main async function to start both web server and Discord bot
async def main():
    await start_web_server()
    await client.start(token)

if __name__ == "__main__":
    asyncio.run(main())
