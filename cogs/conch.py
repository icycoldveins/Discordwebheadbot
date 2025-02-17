import discord
from discord.ext import commands
from discord import app_commands
import random

class Conch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="conch", description="Ask the Magic Conch a question")
    @app_commands.describe(question="The question you want to ask the Magic Conch")
    async def conch_slash(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()

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
            "No"
        ]

        answer = random.choice(answers)
        
        embed = discord.Embed(
            title="🐚 The Magic Conch Shell",
            color=discord.Color.purple()
        )
        embed.add_field(
            name="❓ Question",
            value=question,
            inline=False
        )
        embed.add_field(
            name="💭 Answer",
            value=answer,
            inline=False
        )

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Conch(bot))

