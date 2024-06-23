import discord
from discord.ext import commands
import aiohttp
import asyncio

class Leetcode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}

    @commands.command(name='leetcodeuser')
    async def leetcode(self, ctx, username: str):
        if username in self.cache:
            await ctx.send(f"Fetching stats for {username} from cache...")
            await ctx.send(self.cache[username])
            return

        await ctx.send(f"Fetching stats for {username}...")
        url = f"https://leetcode-stats-api.herokuapp.com/{username}"

        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        package = (
                            f"Stats for {username}:\n"
                            f"Total solved questions: {data['totalSolved']}\n"
                            f"Easy problems solved: {data['easySolved']}\n"
                            f"Medium problems solved: {data['mediumSolved']}\n"
                            f"Hard problems solved: {data['hardSolved']}\n"
                            f"Acceptance rate: {data['acceptanceRate']}\n"
                        )
                        self.cache[username] = package
                        await ctx.send(package)
                        break
                    elif response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 0))
                        await ctx.send(f"Rate limited. Retrying after {retry_after} seconds.")
                        await asyncio.sleep(retry_after)
                    else:
                        await ctx.send(f"Error: {response.status}")
                        break

async def setup(bot):
    await bot.add_cog(Leetcode(bot))
