from dotenv import load_dotenv
import os
import discord
from discord.ext import commands
import cogs.participation

intents = discord.Intents.all()

load_dotenv()
BOT_TOKEN = os.environ.get('BOT_TOKEN')
# Create a bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

# Load extension on bot startup


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - {bot.user.id}")
    await bot.load_extension("cogs.conch")
    await bot.load_extension("cogs.roll")
    await bot.load_extension("cogs.trivia")
    await bot.load_extension("cogs.spotify")
    await bot.load_extension("cogs.leetcode")
    await bot.load_extension("cogs.participation")
    await bot.load_extension("cogs.leetcoderandom")



@bot.command()
async def reload(ctx, extension_name: str):
    try:
        bot.reload_extension(extension_name)
        await ctx.send(f"Reloaded {extension_name}!")
    except Exception as e:
        await ctx.send(f"Error reloading {extension_name}: {e}")

# Start the bot
bot.run(BOT_TOKEN)
