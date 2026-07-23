import os
import signal
import asyncio
import re
from pathlib import Path
from time import time
from dotenv import load_dotenv
import discord
from discord.ext import commands
from aiohttp import web
from discord.ui import Button, View
from datetime import datetime, timezone
from mcstatus import JavaServer
from functools import partial

# --- Load environment variables ---
dotenv_path = Path("C:/Users/harry/desktop/ineptbot/.env") # change to where ever u save the .env to
load_dotenv(dotenv_path)
TOKEN = os.getenv("DISCORD_TOKEN")

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = discord.Bot(intents=intents)

# --- Constants ---
GUILD_ID = 1386539630941175848
CHANNEL_ID = 1396847461494034472  # val-stores channel ID
MC_CHANNEL_ID = 1412246563526279291  # minecraft-status ID
# not needed anymore MC_SERVER_IP = ""  # Minecraft server IP or hostname 

# --- Channels ---
VERIFY_CHANNEL_ID = 1411718666348794059
WELCOME_CHANNEL_ID = 1386539632556249091
RULES_CHANNEL_ID = 1386539632556249092
LIVE_CHANNEL_ID = 1386539632556249094
SCHEDULE_CHANNEL_ID = 1386539632556249095
ROLES_CHANNEL_ID = 1386539632556249096

GENERAL_CHANNEL_ID = 1386539632799256616
MEMES_CHANNEL_ID = 1386539632799256617
MEDIA_CHANNEL_ID = 1386539632799256622
IDEAS_CHANNEL_ID = 1386539632799256620
CLIPS_CHANNEL_ID = 1386539632799256625
BOTCOMMANDS_CHANNEL_ID = 1386539632988258366
VAL_STORES_CHANNEL_ID = 1396847461494034472
SHAME_CHANNEL_ID = 1425875774812065812

CHANNEL_IDS = {
    "verify": VERIFY_CHANNEL_ID,
    "welcome": WELCOME_CHANNEL_ID,
    "rules": RULES_CHANNEL_ID,
    "live": LIVE_CHANNEL_ID,
    "schedule": SCHEDULE_CHANNEL_ID,
    "roles": ROLES_CHANNEL_ID,
    "general": GENERAL_CHANNEL_ID,
    "memes": MEMES_CHANNEL_ID,
    "media": MEDIA_CHANNEL_ID,
    "ideas": IDEAS_CHANNEL_ID,
    "clips": CLIPS_CHANNEL_ID,
    "valstores": VAL_STORES_CHANNEL_ID,
    "botcommands": BOTCOMMANDS_CHANNEL_ID,
    "shame": SHAME_CHANNEL_ID,
}

# --- Role Groups ---
RANK_ROLE_NAMES = ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ascendant", "Immortal", "Radiant"]
REGION_ROLE_NAMES = ["Europe", "North America", "South America", "Africa", "Asia", "Middle East", "Oceania"]
AGE_ROLE_NAMES = ["13", "14-17", "18+"]
PRONOUN_ROLE_NAMES = ["she", "her", "he", "him", "they", "them"]

try:
    from python_aternos import Client as AternosClient
except Exception:
    AternosClient = None

async def run_blocking(fn, *args, **kwargs):
    loop = asyncio.get_event_loop()
    p = partial(fn, *args, **kwargs)
    return await loop.run_in_executor(None, p)

# --- Assign/Remove Roles ---
def remove_and_add_role(interaction, role_name, role_group):
    async def inner():
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            await interaction.response.send_message(f"❌ Role '{role_name}' not found.", ephemeral=True)
            return

        to_remove = [r for r in interaction.user.roles if r.name in role_group and r != role]
        await interaction.user.remove_roles(*to_remove)

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"🗑️ Removed role: **{role.name}**", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Assigned role: **{role.name}**", ephemeral=True)
    return inner

# --- Role Button System ---
class CustomRoleButton(Button):
    def __init__(self, label, role_name, role_group):
        super().__init__(style=discord.ButtonStyle.primary, label=label, custom_id=f"role_{role_name}")
        self.role_name = role_name
        self.role_group = role_group

    async def callback(self, interaction: discord.Interaction):
        await remove_and_add_role(interaction, self.role_name, self.role_group)()

class RoleView(View):
    def __init__(self, roles, role_group):
        super().__init__(timeout=None)
        for label, name in roles:
            self.add_item(CustomRoleButton(label, name, role_group))

# --- Multi-Role Buttons ---
class MultiRoleButton(Button):
    def __init__(self, label, role_name):
        super().__init__(style=discord.ButtonStyle.primary, label=label, custom_id=f"multi_{role_name}")
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=self.role_name)
        if not role:
            await interaction.response.send_message(f"❌ Role '{self.role_name}' not found.", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"🗑️ Removed role: **{role.name}**", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Added role: **{role.name}**", ephemeral=True)

class MultiRoleView(View):
    def __init__(self, roles):
        super().__init__(timeout=None)
        for label, name in roles:
            self.add_item(MultiRoleButton(label, name))

# --- Daily Shop Ping Button ---
class DailyPingButton(Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="Get Daily Ping", custom_id="daily_ping_button")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name="Shop ping")
        if not role:
            await interaction.response.send_message("❌ Role 'Shop ping' not found.", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message("🗑️ Removed role: **Shop ping**", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("✅ Added role: **Shop ping**", ephemeral=True)

class DailyPingView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(DailyPingButton())

# --- Live Ping Button ---
class LivePingButton(Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="Get Live Ping", custom_id="live_ping_button")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name="Live ping")
        if not role:
            await interaction.response.send_message("❌ Role 'Live ping' not found.", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message("🗑️ Removed role: **Live ping**", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("✅ Added role: **Live ping**", ephemeral=True)

class LivePingView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(LivePingButton())

# --- Daily Shop Ping ---
async def daily_shop_ping():
    await bot.wait_until_ready()
    print("⏱️ Daily ping task started")

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("❌ Guild not found. Check GUILD_ID.")
        return

    try:
        channel = await bot.fetch_channel(CHANNEL_ID)
        print(f"📨 Found channel: {channel.name} ({channel.id})")
    except Exception as e:
        print(f"❌ Error fetching channel: {e}")
        return

    role = discord.utils.get(guild.roles, name="Shop ping")
    if not role:
        print("❌ Role 'Shop ping' not found.")
        return

    sent_today = False
    while not bot.is_closed():
        now = datetime.now(timezone.utc)
        if now.hour == 0 and now.minute == 0 and not sent_today:
            try:
                await channel.send(f"||{role.mention}||\nShop has reset!")  # Spoilered mention
                print(f"✅ Daily shop ping sent at {now.isoformat()}")
                sent_today = True
            except Exception as e:
                print(f"❌ Failed to send daily shop ping: {e}")
        elif now.hour != 0:
            sent_today = False
        await asyncio.sleep(20)


# --- "Streaming" Status ---
async def set_streaming_presence():
    await bot.change_presence(activity=discord.Streaming(
        name="twitch.tv/ineptateverything",
        url="https://www.twitch.tv/ineptateverything"
    ))

# --- Mc player counts ---
# async def get_mc_player_count():
#    try:
#        server = JavaServer(MC_SERVER_IP)
#        status = await asyncio.to_thread(server.status)
#        return status.players.online, status.players.max
#    except Exception:
#        return 0, 0



# --- Console Control Panel ---

async def console_control_panel():
    await bot.wait_until_ready()
    current_channel_id = CHANNEL_IDS["valstores"]
    channel = bot.get_channel(current_channel_id) or await bot.fetch_channel(current_channel_id)

    print(f"Console Control Panel Ready. Sending messages to #{channel.name}.")
    print("Commands: /channel <name>, /role <role_name>, /embed, /exit")
    loop = asyncio.get_running_loop()
    role_mention = ""

    while not bot.is_closed():
        user_input = await loop.run_in_executor(None, input, "> ")

        if user_input.startswith("/channel"):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 2 and parts[1] in CHANNEL_IDS:
                current_channel_id = CHANNEL_IDS[parts[1]]
                channel = bot.get_channel(current_channel_id) or await bot.fetch_channel(current_channel_id)
                print(f"Switched channel to #{channel.name}")
            else:
                print("Unknown channel. Available:", ", ".join(CHANNEL_IDS.keys()))
            continue

        if user_input.startswith("/role"):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 2:
                role_name = parts[1]
                role = discord.utils.get(channel.guild.roles, name=role_name)
                if role:
                    role_mention = role.mention
                    print(f"Role set to mention: {role.name}")
                else:
                    print(f"Role '{role_name}' not found.")
            else:
                print("Usage: /role <role_name>")
            continue

        if user_input.startswith("/embed"):
            try:
                title = await loop.run_in_executor(None, lambda: input("Embed Title: "))
                description = await loop.run_in_executor(None, lambda: input("Embed Description (use \\n for line breaks): "))
                author_name = await loop.run_in_executor(None, lambda: input("Author Name (leave blank if none): "))
                footer_text = await loop.run_in_executor(None, lambda: input("Footer Text (leave blank if none): "))
                thumbnail_url = await loop.run_in_executor(None, lambda: input("Thumbnail URL (leave blank if none): "))
                image_url = await loop.run_in_executor(None, lambda: input("Image URL (leave blank if none): "))
                timestamp_input = await loop.run_in_executor(None, lambda: input("Include timestamp? (y/n, default n): "))
                color_input = await loop.run_in_executor(None, lambda: input("Embed Color (hex, leave blank for blue): "))
                buttons_input = await loop.run_in_executor(None, lambda: input("Attach buttons? (none / rank / region / age / pronouns / daily): "))

                description = description.replace("\\n", "\n")

                if color_input:
                    try:
                        color = discord.Color(int(color_input.strip("#"), 16))
                    except Exception:
                        print("Invalid color, using blue instead.")
                        color = discord.Color.blue()
                else:
                    color = discord.Color.blue()

                embed = discord.Embed(title=title, description=description, color=color)
                if author_name:
                    embed.set_author(name=author_name)
                if footer_text:
                    embed.set_footer(text=footer_text)
                if thumbnail_url:
                    embed.set_thumbnail(url=thumbnail_url)
                if image_url:
                    embed.set_image(url=image_url)
                if timestamp_input.lower() == "y":
                    embed.timestamp = datetime.utcnow()

                view = None
                if buttons_input.lower() == "rank":
                    view = RoleView([(r, r) for r in RANK_ROLE_NAMES], RANK_ROLE_NAMES)
                elif buttons_input.lower() == "region":
                    view = RoleView([(r, r) for r in REGION_ROLE_NAMES], REGION_ROLE_NAMES)
                elif buttons_input.lower() == "age":
                    view = RoleView([(r, r) for r in AGE_ROLE_NAMES], AGE_ROLE_NAMES)
                elif buttons_input.lower() == "pronouns":
                    view = MultiRoleView([(r, r) for r in PRONOUN_ROLE_NAMES])
                elif buttons_input.lower() == "daily":
                    view = DailyPingView()

                await channel.send(embed=embed, view=view)
                print(f"✅ Embed sent to #{channel.name}")

            except Exception as e:
                print(f"❌ Failed to send embed: {e}")

            continue

        if user_input in ("/exit", "/quit"):
            break

        try:
            await channel.send(user_input)
        except Exception as e:
            print(f"Failed to send: {e}")

# --- Events ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.sync_commands()
    await set_streaming_presence()

    bot.add_view(RoleView([(r, r) for r in RANK_ROLE_NAMES], RANK_ROLE_NAMES))
    bot.add_view(RoleView([(r, r) for r in REGION_ROLE_NAMES], REGION_ROLE_NAMES))
    bot.add_view(RoleView([(r, r) for r in AGE_ROLE_NAMES], AGE_ROLE_NAMES))
    bot.add_view(MultiRoleView([(r, r) for r in PRONOUN_ROLE_NAMES]))
    bot.add_view(DailyPingView())
    bot.add_view(LivePingView())

    if not hasattr(bot, "daily_ping_started"):
        asyncio.create_task(daily_shop_ping())
        bot.daily_ping_started = True

    if not hasattr(bot, "console_started"):
        asyncio.create_task(console_control_panel())
        bot.console_started = True

    if not hasattr(bot, "web_server_started"):
        bot.loop.create_task(start_web_server())
        bot.web_server_started = True


# --- Keep-Alive Web Server ---
async def handle(request):
    return web.Response(text="Bot is running")

async def start_web_server():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Web server running on port {port}")

# --- Entry Point ---
if __name__ == "__main__":
    bot.run(TOKEN)