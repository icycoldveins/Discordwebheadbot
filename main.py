import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Check if the BOT_TOKEN is loaded correctly
if not BOT_TOKEN:
    print("Error: BOT_TOKEN environment variable is not set.")
    exit(1)

# Define intents
intents = discord.Intents.all()

# Create a bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

async def load_extensions():
    extensions = [
        "cogs.conch",
        "cogs.roll",
        "cogs.trivia",
        "cogs.spotify",
        "cogs.leetcode",
        "cogs.participation",
        "cogs.leetcoderandom",
        "cogs.calories"
    ]
    for extension in extensions:
        try:
            await bot.load_extension(extension)
            print(f"Loaded {extension} successfully.")
        except Exception as e:
            print(f"Failed to load {extension}: {e}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - {bot.user.id}")
    await load_extensions()

@bot.command()
async def reload(ctx, extension_name: str):
    try:
        await bot.reload_extension(extension_name)
        await ctx.send(f"Reloaded {extension_name}!")
    except Exception as e:
        await ctx.send(f"Error reloading {extension_name}: {e}")

# Start the bot
bot.run(BOT_TOKEN)
