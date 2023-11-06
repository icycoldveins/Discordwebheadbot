import discord
from discord.ext import commands
import requests


class Leetcode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def leetcode(self, ctx, username):
        url = f"https://leetcode-stats-api.herokuapp.com/{username}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()

            total_easy_solved = data['easySolved']
            total_medium_solved = data['mediumSolved']
            total_hard_solved = data['hardSolved']

            await ctx.send(f"Total solved questions: {data['totalSolved']}")
            await ctx.send(f"Easy problems solved: {total_easy_solved}")
            await ctx.send(f"Medium problems solved: {total_medium_solved}")
            await ctx.send(f"Hard problems solved: {total_hard_solved}")
            await ctx.send(f"Acceptance rate: {data['acceptanceRate']}")
        else:
            await ctx.send(f"Error: {response.status_code}")


async def setup(bot):
    await bot.add_cog(Leetcode(bot))
