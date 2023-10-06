import discord
from discord.ext import commands
import random

class Roll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, ctx):
        result = random.randint(1, 6)
        await ctx.send(f'You rolled a {result}!')

async def setup(bot):
    await bot.add_cog(Roll(bot))
