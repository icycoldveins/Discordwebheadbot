import discord
from discord.ext import commands
import random

class Roll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, ctx):
        """
        Roll a six-sided die.

        This command simulates rolling a six-sided die and returns the result.

        Usage:
        !roll

        Example:
        !roll
        """
        result = random.randint(1, 6)
        await ctx.send(f'You rolled a {result}!')

async def setup(bot):
    await bot.add_cog(Roll(bot))
