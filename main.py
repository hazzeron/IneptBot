import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import discord
from aiohttp import web

# Load token from .env
dotenv_path = Path('.') / '.env'
load_dotenv(dotenv_path)
token = os.getenv("DISCORD_TOKEN")

# Set intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

# Create the bot instance using py-cord's discord.Bot
bot = discord.Bot(intents=intents)

async def send_rules_embed(channel: discord.TextChannel):
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

# Slash command: /rules
@bot.slash_command(description="Send the server rules")
async def rules(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("🚫 You need Administrator permissions to use this command.", ephemeral=True)
        return

    await send_rules_embed(ctx.channel)
    await ctx.respond("✅ Rules message sent.", ephemeral=True)

# Event when the bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Streaming(
        name="twitch.tv/ineptateverything", url="https://twitch.tv/ineptateverything"))

# Aiohttp server to keep Fly.io happy
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

# Start both web server and Discord bot
async def main():
    await start_web_server()
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
