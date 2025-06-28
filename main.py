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

# Slash command: /rules

@bot.slash_command(description="Send the server rules")
async def rules(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("🚫 Insufficient Permissions.", ephemeral=True)
        return

    await send_rules_embed(ctx.channel)
    await ctx.respond("✅ Rules message sent.", ephemeral=True)

# /ranks code

class RankRoleView(View):
    def __init__(self):
        super().__init__(timeout=None)  # No timeout; stays persistent

        # Define button-label and corresponding role names
        self.ranks = [
            ("Iron", "Iron"),
            ("Bronze", "Bronze"),
            ("Silver", "Silver"),
            ("Gold", "Gold"),
            ("Platinum", "Platinum"),
            ("Diamond", "Diamond"),
            ("Ascendant", "Ascendant"),
            ("Immortal", "Immortal"),
            ("Radiant", "Radiant"),
        ]

        for label, role_name in self.ranks:
            self.add_item(RankButton(label=label, role_name=role_name))

class RankButton(Button):
    def __init__(self, label, role_name):
        super().__init__(style=discord.ButtonStyle.primary, label=label)
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=self.role_name)
        if not role:
            await interaction.response.send_message(
                f"❌ Role '{self.role_name}' not found. Ask an admin to create it.",
                ephemeral=True
            )
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"🗑️ Removed role: **{role.name}**", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Added role: **{role.name}**", ephemeral=True)

# Slash command: /ranks

@bot.slash_command(description="Send the Valorant rank role selector")
async def ranks(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("🚫 You need Administrator permissions to use this command.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🏆 Rank",
        description="Select your rank",
        color=discord.Color.purple()
    )
    embed.set_image(url="https://i.imgur.com/9g4SmZQ.png")  # Replace with your own hosted image if needed

    await ctx.channel.send(embed=embed, view=RankRoleView())
    await ctx.respond("✅ Rank selector sent!", ephemeral=True)




# Event when the bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.sync_commands()
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
