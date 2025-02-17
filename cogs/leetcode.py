import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
from typing import Optional

class Leetcode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://leetcode.com/graphql"
        self.cache = {}

    @app_commands.command(name="leetcode_user", description="Get LeetCode user statistics")
    async def leetcode_user(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()

        query = """
        query userProfile($username: String!) {
            matchedUser(username: $username) {
                username
                submitStats {
                    acSubmissionNum {
                        difficulty
                        count
                    }
                }
                profile {
                    ranking
                    rating
                }
                recentSubmissionList {
                    title
                    titleSlug
                    timestamp
                    statusDisplay
                }
            }
        }
        """

        variables = {"username": username}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                json={"query": query, "variables": variables}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    user_data = data.get("data", {}).get("matchedUser")
                    
                    if not user_data:
                        await interaction.followup.send(f"User {username} not found!")
                        return

                    # Create embed
                    embed = discord.Embed(
                        title=f"LeetCode Profile: {username}",
                        url=f"https://leetcode.com/{username}",
                        color=discord.Color.blue()
                    )

                    # Add solving statistics
                    stats = user_data["submitStats"]["acSubmissionNum"]
                    solved_problems = "\n".join([
                        f"**{stat['difficulty']}**: {stat['count']}"
                        for stat in stats
                    ])
                    embed.add_field(
                        name="Solved Problems",
                        value=solved_problems,
                        inline=False
                    )

                    # Add ranking and rating
                    profile = user_data["profile"]
                    embed.add_field(
                        name="Ranking",
                        value=str(profile["ranking"]),
                        inline=True
                    )
                    embed.add_field(
                        name="Rating",
                        value=str(profile["rating"]),
                        inline=True
                    )

                    # Add recent submissions
                    recent_subs = user_data["recentSubmissionList"][:5]
                    if recent_subs:
                        recent = "\n".join([
                            f"• {sub['title']} - {sub['statusDisplay']}"
                            for sub in recent_subs
                        ])
                        embed.add_field(
                            name="Recent Submissions",
                            value=recent,
                            inline=False
                        )

                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send("Error fetching user data")

async def setup(bot):
    leetcode_cog = Leetcode(bot)
    await bot.add_cog(leetcode_cog)
    try:
        await bot.tree.sync()
    except Exception as e:
        print(f"Failed to sync Leetcode commands: {e}")
