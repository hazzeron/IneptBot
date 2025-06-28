import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import discord
from aiohttp import web
from discord.ui import Button, View

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

# --- Shared Role Lists ---
RANK_ROLE_NAMES = [
    "Iron", "Bronze", "Silver", "Gold",
    "Platinum", "Diamond", "Ascendant", "Immortal", "Radiant"
]

REGION_ROLE_NAMES = [
    "Europe", "North America", "South America",
    "Africa", "Asia", "Middle East", "Oceania"
]

AGE_ROLE_NAMES = ["13", "14-17", "18+"]

# --- Slash Command: /rules ---

async def send_rules_embed(channel: discord.TextChannel):
    embed = discord.Embed(
        title="Server Rules",
        description=(
            "**Discord TOS**\n"
            "-Users must follow Terms of Service and guidelines of Discord including the mandatory minimum age to be on discord is 13.\n\n"
            "**Respect Others**\n"
            "-Treat everyone with respect, any type of discrimination/racism/harassment/hate speech towards any member regardless of who will not be tolerated.\n\n"
            "**No NSFW Content**\n"
            "-Sending any type of inappropriate or disturbing content via media/links/messages/etc…\n\n"
            "**Channel Usage**\n"
            "-The moderation has created channels under certain categories for a reason. Use them properly for sending messages or images. Useless pings, Ghost pinging, and Spamming will result in a punishment.\n\n"
            "**Information**\n"
            "-Any type of acquiring personal information through malicious acts or doxxing will result in a permanent ban. If a user doesn’t feel comfortable sharing a certain piece of information with others, respect it.\n\n"
            "**Maturity Level**\n"
            "-Not forcing you to act mature of your current age but at least use common sense!\n\n"
            "**Self Promo**\n"
            "-Do not promote your own socials or servers without the permission from a moderator. This includes DMing members\n\n"
            "**Ban evading**\n"
            "-Do not create alternatives accounts to bypass punishments assigned to you.\n\n"
            "As a community we are trying to set the example for others. All these rules will apply to DMs. If you do not feel comfortable with someone, feel free to reach out to any moderator. We will do our best to assist you and hand out correct punishments to rule breakers.\n"
        ),
        color=discord.Color.blue()
    )
    embed.set_footer(text="React below to agree to the rules")
    embed.set_thumbnail(url="https://i.imgur.com/dw8t44A.png")
    message = await channel.send(embed=embed)
    await message.add_reaction("✅")

@bot.slash_command(description="Send the server rules")
async def rules(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("🚫 Insufficient Permissions.", ephemeral=True)
        return

    await send_rules_embed(ctx.channel)
    await ctx.respond("✅ Rules message sent.", ephemeral=True)

# --- Role Button Classes ---

def remove_and_add_role(interaction, role_name, role_group):
    async def inner():
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            await interaction.response.send_message(
                f"❌ Role '{role_name}' not found. Ask an admin to create it.", ephemeral=True
            )
            return

        roles_to_remove = [r for r in interaction.user.roles if r.name in role_group and r != role]

        await interaction.user.remove_roles(*roles_to_remove)

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"🗑️ Removed role: **{role.name}**", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Added role: **{role.name}**", ephemeral=True)

    return inner

class CustomRoleButton(Button):
    def __init__(self, label, role_name, role_group):
        super().__init__(style=discord.ButtonStyle.primary, label=label, custom_id=f"role_button_{role_name}")
        self.role_name = role_name
        self.role_group = role_group

    async def callback(self, interaction: discord.Interaction):
        await remove_and_add_role(interaction, self.role_name, self.role_group)()

class RoleView(View):
    def __init__(self, roles, role_group):
        super().__init__(timeout=None)
        for label, name in roles:
            self.add_item(CustomRoleButton(label, name, role_group))

# --- Slash Command: /ranks ---

@bot.slash_command(description="Send the Valorant rank role selector")
async def ranks(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("Insufficient Permissions", ephemeral=True)
        return

    embed = discord.Embed(
        title="Rank",
        description="Select your rank",
        color=discord.Color.purple()
    )
    embed.set_image(url="https://i.imgur.com/tcyM7nD.png")

    rank_roles = [(r, r) for r in RANK_ROLE_NAMES]
    await ctx.channel.send(embed=embed, view=RoleView(rank_roles, RANK_ROLE_NAMES))
    await ctx.respond("✅ Rank selector sent!", ephemeral=True)

# --- Slash Command: /regions ---

@bot.slash_command(description="Send the Region role selector")
async def regions(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("Insufficient Permissions", ephemeral=True)
        return

    embed = discord.Embed(
        title="Region",
        description="Select your region",
        color=discord.Color.purple()
    )
    embed.set_image(url="https://i.imgur.com/47KXBco.png")

    region_roles = [(r, r) for r in REGION_ROLE_NAMES]
    await ctx.channel.send(embed=embed, view=RoleView(region_roles, REGION_ROLE_NAMES))
    await ctx.respond("✅ Region selector sent!", ephemeral=True)

# --- Slash Command: /age ---

@bot.slash_command(description="Send the Age role selector")
async def age(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("Insufficient Permissions", ephemeral=True)
        return

    embed = discord.Embed(
        title="Age",
        description="Select your age group",
        color=discord.Color.orange()
    )
    embed.set_thumbnail(url="https://i.imgur.com/dw8t44A.png")

    age_roles = [(r, r) for r in AGE_ROLE_NAMES]
    await ctx.channel.send(embed=embed, view=RoleView(age_roles, AGE_ROLE_NAMES))
    await ctx.respond("✅ Age selector sent!", ephemeral=True)

# --- Bot Events ---

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.sync_commands()
    await bot.change_presence(activity=discord.Streaming(
        name="twitch.tv/ineptateverything", url="https://twitch.tv/ineptateverything"))

    # Register persistent views
    bot.add_view(RoleView([(r, r) for r in RANK_ROLE_NAMES], RANK_ROLE_NAMES))
    bot.add_view(RoleView([(r, r) for r in REGION_ROLE_NAMES], REGION_ROLE_NAMES))
    bot.add_view(RoleView([(r, r) for r in AGE_ROLE_NAMES], AGE_ROLE_NAMES))

# --- Aiohttp Keep-Alive Server (Fly.io) ---

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

# --- Entry Point ---

async def main():
    await start_web_server()
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
