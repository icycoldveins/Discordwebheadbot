import discord
from discord.ext import commands
import random

class Conch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def conch(self, ctx, question: str):
        answers = [
           "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes, definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful.",
            "No",
        ]
        answer = random.choice(answers)
        await ctx.send(f"The Magic Conch says: {answer}")

async def setup(bot):
    await bot.add_cog(Conch(bot))

