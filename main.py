import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import discord
from aiohttp import web
from discord.ui import Button, View
from datetime import datetime, timedelta
import pytz

# --- Load environment variables ---
load_dotenv(Path('.') / '.env')
TOKEN = os.getenv("DISCORD_TOKEN")

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True  # Required to fetch roles/users
bot = discord.Bot(intents=intents)

# --- Role Groups ---
RANK_ROLE_NAMES = [
    "Iron", "Bronze", "Silver", "Gold",
    "Platinum", "Diamond", "Ascendant", "Immortal", "Radiant"
]

REGION_ROLE_NAMES = [
    "Europe", "North America", "South America",
    "Africa", "Asia", "Middle East", "Oceania"
]

AGE_ROLE_NAMES = [
    "13", "14-17", "18+"
]

PRONOUN_ROLE_NAMES = [
    "she", "her", "he", "him", "they", "them"
]

# --- Utility: Assign/Remove Roles ---
def remove_and_add_role(interaction, role_name, role_group):
    async def inner():
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            await interaction.response.send_message(
                f"❌ Role '{role_name}' not found. Ask an admin to create it.", ephemeral=True
            )
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
            await interaction.response.send_message(
                f"❌ Role '{self.role_name}' not found. Ask an admin to create it.", ephemeral=True
            )
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
        super().__init__(style=discord.ButtonStyle.success, label="Get Daily Ping", custom_id="daily_ping_button")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name="Shop ping")
        if not role:
            await interaction.response.send_message(
                "❌ Role 'Shop ping' not found. Ask an admin to create it.", ephemeral=True
            )
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

# --- Commands ---
@bot.slash_command(description="Send the server rules")
async def rules(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.respond("🚫 Insufficient Permissions.", ephemeral=True)

    embed = discord.Embed(
        title="Server Rules",
        description=(
            "**Discord TOS**\n"
            "- Users must follow Terms of Service and guidelines of Discord including the minimum age of 13.\n\n"
            "**Respect Others**\n"
            "- No discrimination, harassment, or hate speech.\n\n"
            "**No NSFW Content**\n"
            "- Don't send inappropriate or disturbing content.\n\n"
            "**Channel Usage**\n"
            "- Use channels as intended. No spam, ghost pings, or misuse.\n\n"
            "**Information**\n"
            "- No doxxing or personal info theft.\n\n"
            "**Maturity Level**\n"
            "- Use common sense.\n\n"
            "**Self Promo**\n"
            "- No self-promo without mod approval.\n\n"
            "**Ban evading**\n"
            "- No alt accounts to bypass punishment.\n\n"
            "Rules apply to DMs too. Reach out to moderators if needed."
        ),
        color=discord.Color.blue()
    )
    embed.set_footer(text="React below to agree to the rules")
    embed.set_thumbnail(url="https://i.imgur.com/dw8t44A.png")

    msg = await ctx.channel.send(embed=embed)
    await msg.add_reaction("✅")
    await ctx.respond("✅ Rules message sent.", ephemeral=True)

@bot.slash_command(description="Send the pronouns selector")
async def pronouns(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.respond("🚫 Insufficient Permissions.", ephemeral=True)

    embed = discord.Embed(
        title="Pronouns",
        description="Click to select your pronouns (you can select multiple)",
        color=discord.Color.purple()
    )
    embed.set_image(url="https://i.imgur.com/fRia4oS.png")

    roles = [(r, r) for r in PRONOUN_ROLE_NAMES]
    await ctx.channel.send(embed=embed, view=MultiRoleView(roles))
    await ctx.respond("✅ Pronoun selector sent!", ephemeral=True)

@bot.slash_command(description="Send the Valorant rank role selector")
async def ranks(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.respond("🚫 Insufficient Permissions.", ephemeral=True)

    embed = discord.Embed(
        title="Rank",
        description="Select your Valorant rank",
        color=discord.Color.purple()
    )
    embed.set_image(url="https://i.imgur.com/tcyM7nD.png")

    roles = [(r, r) for r in RANK_ROLE_NAMES]
    await ctx.channel.send(embed=embed, view=RoleView(roles, RANK_ROLE_NAMES))
    await ctx.respond("✅ Rank selector sent!", ephemeral=True)

@bot.slash_command(description="Send the Region role selector")
async def regions(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.respond("🚫 Insufficient Permissions.", ephemeral=True)

    embed = discord.Embed(
        title="Region",
        description="Select your region",
        color=discord.Color.purple()
    )
    embed.set_image(url="https://i.imgur.com/47KXBco.png")

    roles = [(r, r) for r in REGION_ROLE_NAMES]
    await ctx.channel.send(embed=embed, view=RoleView(roles, REGION_ROLE_NAMES))
    await ctx.respond("✅ Region selector sent!", ephemeral=True)

@bot.slash_command(description="Send the Age role selector")
async def ages(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.respond("🚫 Insufficient Permissions.", ephemeral=True)

    embed = discord.Embed(
        title="Age",
        description="Select your age group",
        color=discord.Color.purple()
    )

    roles = [(r, r) for r in AGE_ROLE_NAMES]
    await ctx.channel.send(embed=embed, view=RoleView(roles, AGE_ROLE_NAMES))
    await ctx.respond("✅ Age selector sent!", ephemeral=True)

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


# --- Scheduled Task: Daily Ping ---
async def daily_shop_ping():
    await bot.wait_until_ready()
    guild = discord.utils.get(bot.guilds)  # Get the first connected guild
    if not guild:
        print("No guilds connected.")
        return

    channel = guild.get_channel(1396847461494034472)
    if not channel:
        print("Channel not found.")
        return

    role = discord.utils.get(guild.roles, name="Shop ping")
    if not role:
        print("Role 'Shop ping' not found.")
        return

    gmt = pytz.timezone("GMT")

    while not bot.is_closed():
        now = datetime.now(gmt)
        target = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        wait_time = (target - now).total_seconds()
        await asyncio.sleep(wait_time)

        try:
            await channel.send(f"|| {role.mention} || \n Shop has reset!")
        except Exception as e:
            print(f"Failed to send ping: {e}")

# --- Events ---
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.sync_commands()
    await bot.change_presence(activity=discord.Streaming(
        name="twitch.tv/ineptateverything", url="https://twitch.tv/ineptateverything"
    ))

    # Register persistent views
    bot.add_view(RoleView([(r, r) for r in RANK_ROLE_NAMES], RANK_ROLE_NAMES))
    bot.add_view(RoleView([(r, r) for r in REGION_ROLE_NAMES], REGION_ROLE_NAMES))
    bot.add_view(RoleView([(r, r) for r in AGE_ROLE_NAMES], AGE_ROLE_NAMES))
    bot.add_view(MultiRoleView([(r, r) for r in PRONOUN_ROLE_NAMES]))
    bot.add_view(DailyPingView())

    # Start shop ping scheduler
    asyncio.create_task(daily_shop_ping())

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
    print(f"Web server running on port {port}")

# --- Entry Point ---
async def main():
    await start_web_server()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
