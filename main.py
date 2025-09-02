import os
import signal
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import discord
from aiohttp import web
from discord.ui import Button, View
from datetime import datetime, timezone
from mcstatus.server import MinecraftServer


# Minecraft monitor settings
MC_SERVER_IP = "atom.aternos.org"  # your server IP or hostname
MC_CHANNEL_ID = 1412246563526279291  # channel ID where updates will be sent
MC_CHECK_INTERVAL = 5  # seconds

async def minecraft_monitor():
    await bot.wait_until_ready()
    print("🎮 Minecraft monitor task started")

    channel = bot.get_channel(MC_CHANNEL_ID)
    if not channel:
        print(f"❌ Could not find channel with ID {MC_CHANNEL_ID}")
        return

    last_online = None
    last_players = set()

    while not bot.is_closed():
        try:
            server = MinecraftServer.lookup(MC_SERVER_IP)
            status = server.status()
            online = True
            players = set(p.name for p in status.players.sample or [])
        except Exception:
            online = False
            players = set()

        # Server online/offline status change
        if last_online is None:
            last_online = online
        elif online != last_online:
            await channel.send(f"Server is now **{'online' if online else 'offline'}**!")
            last_online = online

        # Player join/leave detection
        joined = players - last_players
        left = last_players - players

        for player in joined:
            await channel.send(f"**{player}** joined the server!")
        for player in left:
            await channel.send(f"**{player}** left the server!")

        last_players = players
        await asyncio.sleep(MC_CHECK_INTERVAL)



# --- Load environment variables ---
load_dotenv(Path('.') / '.env')
TOKEN = os.getenv("DISCORD_TOKEN")

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.presences = True
bot = discord.Bot(intents=intents)

# --- Constants ---
GUILD_ID = 1386539630941175848  # Your server ID
CHANNEL_ID = 1396847461494034472  # Your target text channel ID

# --- Role Groups ---
RANK_ROLE_NAMES = ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ascendant", "Immortal", "Radiant"]
REGION_ROLE_NAMES = ["Europe", "North America", "South America", "Africa", "Asia", "Middle East", "Oceania"]
AGE_ROLE_NAMES = ["13", "14-17", "18+"]
PRONOUN_ROLE_NAMES = ["she", "her", "he", "him", "they", "them"]

# --- Utility: Assign/Remove Roles ---
def remove_and_add_role(interaction, role_name, role_group):
    async def inner():
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            await interaction.response.send_message(f"❌ Role '{role_name}' not found. Ask an admin to create it.", ephemeral=True)
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

# --- Role Button System (Single Role) ---
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

# --- Multi-Role Button System (For Pronouns) ---
class MultiRoleButton(Button):
    def __init__(self, label, role_name):
        super().__init__(style=discord.ButtonStyle.primary, label=label, custom_id=f"multi_{role_name}")
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=self.role_name)
        if not role:
            await interaction.response.send_message(f"❌ Role '{self.role_name}' not found. Ask an admin to create it.", ephemeral=True)
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

# --- Daily shop ping ---
class DailyPingButton(Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="Get Daily Ping", custom_id="daily_ping_button")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name="Shop ping")
        if not role:
            await interaction.response.send_message("❌ Role 'Shop ping' not found. Ask an admin to create it.", ephemeral=True)
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

# --- Streaming Status Handler ---
async def set_streaming_presence():
    await bot.change_presence(activity=discord.Streaming(
        name="twitch.tv/ineptateverything",
        url="https://www.twitch.tv/ineptateverything"
    ))

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

    asyncio.create_task(daily_shop_ping())
    asyncio.create_task(minecraft_monitor())


@bot.event
async def on_connect():
    await set_streaming_presence()

# --- Scheduled Task: Daily Ping ---
async def daily_shop_ping():
    await bot.wait_until_ready()
    print("⏱️ Daily ping task started")

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("❌ Guild not found. Check GUILD_ID and if the bot is in the server.")
        return

    try:
        channel = await bot.fetch_channel(CHANNEL_ID)
        print(f"📨 Found channel: {channel.name} ({channel.id})")
    except discord.NotFound:
        print("❌ Channel not found. Check if the bot has access to the channel ID.")
        return
    except discord.Forbidden:
        print("❌ Bot lacks permission to access the channel.")
        return
    except discord.HTTPException as e:
        print(f"❌ HTTP error while fetching channel: {e}")
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
                await channel.send(f"|| {role.mention} || \nShop has reset!")
                print(f"✅ Daily shop ping sent at {now.isoformat()}")
                sent_today = True
            except Exception as e:
                print(f"❌ Failed to send daily shop ping: {e}")
        elif now.hour != 0:
            sent_today = False

        await asyncio.sleep(60)

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