import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from aiohttp import web
import asyncio

# Load environment variables
load_dotenv()
BOT_TOKEN = os.environ.get('BOT_TOKEN')
PORT = int(os.getenv('PORT', 10000))

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

# Create web app
app = web.Application()

async def handle(request):
    return web.Response(text="Bot is running!")

app.router.add_get("/", handle)

async def run_web_server():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"Web server running on port {PORT}")

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
        "cogs.analytics"  # Add the Analytics cog
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
    try:
        print("Syncing commands...")
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.command()
async def reload(ctx, extension_name: str):
    try:
        await bot.reload_extension(extension_name)
        await ctx.send(f"Reloaded {extension_name}!")
    except Exception as e:
        await ctx.send(f"Error reloading {extension_name}: {e}")

async def start_bot():
    try:
        await bot.start(BOT_TOKEN)
    except KeyboardInterrupt:
        await bot.close()

# Run both the web server and the bot
async def main():
    await asyncio.gather(run_web_server(), start_bot())

if __name__ == "__main__":
    asyncio.run(main())

