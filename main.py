import os
import signal
import asyncio
import re
from pathlib import Path
from dotenv import load_dotenv
import discord
from aiohttp import web
from discord.ui import Button, View
from datetime import datetime, timezone
from mcstatus import JavaServer
from functools import partial

# --- Load environment variables ---
load_dotenv(Path('.') / '.env')
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
MC_SERVER_IP = "atom.aternos.me"  # Minecraft server IP or hostname

# --- Role Groups ---
RANK_ROLE_NAMES = ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ascendant", "Immortal", "Radiant"]
REGION_ROLE_NAMES = ["Europe", "North America", "South America", "Africa", "Asia", "Middle East", "Oceania"]
AGE_ROLE_NAMES = ["13", "14-17", "18+"]
PRONOUN_ROLE_NAMES = ["she", "her", "he", "him", "they", "them"]

# --- Aternos Client Import ---
try:
    from python_aternos import Client as AternosClient
except Exception:
    AternosClient = None

async def run_blocking(fn, *args, **kwargs):
    """Run blocking code in an executor."""
    loop = asyncio.get_event_loop()
    p = partial(fn, *args, **kwargs)
    return await loop.run_in_executor(None, p)

# --- Utility: Assign/Remove Roles ---
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

# --- Multi-Role Button System ---
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

# --- Daily Shop Ping ---
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

# --- Scheduled Task: Daily Ping ---
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

# --- Slash Commands ---
@bot.slash_command(description="Send the Daily ping role option")
async def dailyping(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.respond("🚫 Insufficient Permissions.", ephemeral=True)

    embed = discord.Embed(
        title="Daily ping",
        description="Press the button to get notified each time the Valorant store resets",
        color=discord.Color.purple()
    )

    await ctx.channel.send(embed=embed, view=DailyPingView())
    await ctx.respond("✅ Daily ping selector sent!", ephemeral=True)

# --- NEW Slash Command: Start Aternos Server ---
@bot.slash_command(description="Start the Minecraft server if it is offline")
@discord.commands.cooldown(1, 300, discord.commands.BucketType.guild)  # 1 use per 5 min per guild
async def startserver(ctx: discord.ApplicationContext):
    await ctx.defer()
    if AternosClient is None:
        return await ctx.respond("❌ Aternos library not installed on the bot.")

    try:
        def create_and_login():
            client = AternosClient()
            client.login(os.getenv("ATERNOS_USER"), os.getenv("ATERNOS_PASS"))
            return client

        client = await run_blocking(create_and_login)

        def get_server(c):
            servers = c.list_servers()
            return servers[0]

        server = await run_blocking(get_server, client)

        status = getattr(server, "status", None)
        is_online = (isinstance(status, str) and status.lower() == "online") or bool(status)

        if is_online:
            return await ctx.respond("❌ Server already online")

        await ctx.respond("⏳ Server offline. Sending start command...")
        await run_blocking(server.start)
        await ctx.send_followup("✅ Start command sent. Server should boot shortly!")

    except Exception as e:
        await ctx.respond(f"❌ Failed to start server: {e}")

# --- Streaming Status Handler ---
async def set_streaming_presence():
    await bot.change_presence(activity=discord.Streaming(
        name="twitch.tv/ineptateverything",
        url="https://www.twitch.tv/ineptateverything"
    ))

# --- Helper: Get Minecraft Player Count ---
async def get_mc_player_count():
    try:
        server = JavaServer(MC_SERVER_IP)
        status = await asyncio.to_thread(server.status)
        return status.players.online, status.players.max
    except Exception:
        return 0, 0

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

    # ✅ Prevent multiple daily_shop_ping loops
    if not hasattr(bot, "daily_ping_started"):
        asyncio.create_task(daily_shop_ping())
        bot.daily_ping_started = True

# --- DiscordSRV Event Listener with Player Counts ---
@bot.event
async def on_message(message):
    if message.channel.id != MC_CHANNEL_ID or message.author.bot:
        return

    content = message.content
    online, max_players = await get_mc_player_count()

    join_match = re.search(r"(.+?) joined the server", content)
    leave_match = re.search(r"(.+?) left the server", content)

    if join_match:
        player = join_match.group(1)
        await message.channel.send(f"✅ {player} joined the server! ({online}/{max_players})")
    elif leave_match:
        player = leave_match.group(1)
        await message.channel.send(f"❌ {player} left the server! ({online}/{max_players})")
    elif "server started" in content.lower() or "server is now online" in content.lower():
        await message.channel.send("🔔 Server is now online!")
    elif "server stopped" in content.lower() or "server is now offline" in content.lower():
        await message.channel.send("🔔 Server is now offline!")

# --- Server start message ---

@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error):
    # Check if the error is a CommandOnCooldown (slash command cooldown)
    if isinstance(error, discord.ApplicationCommandOnCooldown):
        # error.retry_after gives the remaining cooldown in seconds
        retry_seconds = int(error.retry_after)
        minutes, seconds = divmod(retry_seconds, 60)
        if minutes > 0:
            await ctx.respond(f"⏳ Please wait {minutes}m {seconds}s before starting the server again.", ephemeral=True)
        else:
            await ctx.respond(f"⏳ Please wait {seconds}s before starting the server again.", ephemeral=True)
    else:
        # For any other errors, print to console
        print(f"❌ Command error: {error}")


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
async def main():
    await start_web_server()
    await bot.start(TOKEN)

async def shutdown():
    print("🛑 Shutdown signal received. Logging out...")
    await bot.close()

def handle_signal():
    asyncio.create_task(shutdown())

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
