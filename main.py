import os
import signal
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import discord
from aiohttp import web
from discord.ui import Button, View
from datetime import datetime, timezone

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
CHANNEL_ID = 1396847461494034472  #val-stores channel ID
MC_CHANNEL_ID = 1412246563526279291  #minecraft-status ID

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

# --- DiscordSRV Event Listener ---
@bot.event
async def on_message(message):
    # Only process messages in the DiscordSRV Minecraft channel
    if message.channel.id != MC_CHANNEL_ID:
        return
    if message.author.bot:
        return

    content = message.content.lower()

    if "joined the game" in content:
        await message.channel.send(f"✅ {content}")
    elif "left the game" in content:
        await message.channel.send(f"❌ {content}")
    elif "server started" in content or "server is now online" in content:
        await message.channel.send("🔔 Server is now online!")
    elif "server stopped" in content or "server is now offline" in content:
        await message.channel.send("🔔 Server is now offline!")

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
