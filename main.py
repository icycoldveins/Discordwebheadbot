import discord
from discord.ext import commands
intents = discord.Intents.all()
# Create a bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

# Load extension on bot startup
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - {bot.user.id}")
    await bot.load_extension("cogs.conch")

# Command to reload an extension (useful for development)
@bot.command()
async def reload(ctx, extension_name: str):
    try:
        bot.reload_extension(extension_name)
        await ctx.send(f"Reloaded {extension_name}!")
    except Exception as e:
        await ctx.send(f"Error reloading {extension_name}: {e}")

# Start the bot
bot.run(BOT_TOKEN)
