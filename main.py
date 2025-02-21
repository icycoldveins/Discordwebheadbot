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
intents = discord.Intents.default()
intents.members = True  # For member-related data
intents.presences = True  # For status and activity data
intents.message_content = True  # For message content
intents.guilds = True  # For server data

# Create a bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

async def load_extensions():
    extensions = [
        "cogs.trivia",
        "cogs.leetcode",
        "cogs.leetcoderandom",
        "cogs.leetcodeproblem",
        "cogs.nba_schedule",
        "cogs.nfl_schedule",
        "cogs.conch",
        "cogs.urban",
        "cogs.discordstats",
        "cogs.analytics",
        "cogs.horoscope",
        "cogs.market",
        "cogs.presentation_trivia",
        "cogs.mc_quiz",
        "cogs.spotify_stats"
    ]
    for extension in extensions:
        try:
            await bot.load_extension(extension)
            print(f"Loaded {extension} successfully.")
        except Exception as e:
            print(f"Failed to load {extension}: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('------')
    await load_extensions()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# Run the bot
bot.run(BOT_TOKEN)

