import discord
from discord.ext import commands
import os
import random

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all()) 

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def insult(ctx, user: discord.ext.commands.MemberConverter):
    insults = [
        f"Hey {user.mention}, you're as useless as the 'g' in lasagna.",
        f"{user.mention}, your face makes onions cry.",
        f"{user.mention}, you're so dumb, you think a quarterback is a refund.",
        f"Roses are red, violets are blue, {user.mention} is ugly, and that's true.",
        f"{user.mention}, you must have been born on a highway because that's where most accidents happen.",
        f"{user.mention}, you're so ugly, even Hello Kitty says goodbye.",
        f"Is your name Google? Because you have everything I'm not looking for, {user.mention}."
    ]
    insult = random.choice(insults)
    await ctx.send(insult)

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

bot.run(os.environ['DISCORD_TOKEN'])