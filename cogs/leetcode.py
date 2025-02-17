import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
from datetime import datetime
from typing import Optional
import random
import json

class Leetcode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://leetcode.com/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://leetcode.com"
        }

    @app_commands.command(name="leetcode", description="Get a random LeetCode problem")
    @app_commands.describe(difficulty="Problem difficulty (easy, medium, hard)")
    async def leetcode(self, interaction: discord.Interaction, difficulty: Optional[str] = None):
        await interaction.response.defer()
        problemUrlBase = 'https://leetcode.com/problems/'
        headers = {'Accept': 'application/json'}
        async with aiohttp.ClientSession() as session:
            async with session.get('https://leetcode.com/api/problems/all/', headers=headers) as resp:
                data = await resp.text()
                data = json.loads(data)
        problems = [Problem(p) for p in data['stat_status_pairs']]
        if difficulty:
            problems = [p for p in problems if p.difficulty.lower() == difficulty.lower()]

        if not problems:
            await interaction.followup.send("No problems found with the given criteria.")
            return

        problem = random.choice(problems)
        query = {
            "operationName": "questionData",
            "variables": {
                "titleSlug": problem.titleSlug
            },
            "query": """query questionData($titleSlug: String!) {
                question(titleSlug: $titleSlug) {
                    content
                }
            }"""
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, json=query) as resp:
                data = await resp.json()
        
        embed = discord.Embed(
            title=f"{problem.title} - {problem.difficulty.capitalize()}", 
            url=f"{problemUrlBase}{problem.titleSlug}",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="leetcode_user", description="Get detailed LeetCode user statistics")
    @app_commands.describe(username="LeetCode username to look up")
    async def leetcode_user(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()
        # ... rest of user stats code

    @app_commands.command(name="leetcode_lookup", description="Search for a LeetCode user")
    @app_commands.describe(search_term="Partial username or name to search for")
    async def leetcode_lookup(self, interaction: discord.Interaction, search_term: str):
        await interaction.response.defer()

        query = """
        query searchUser($keyword: String!) {
            userProfileList(keyword: $keyword, limit: 10) {
                username
                profile {
                    realName
                    userAvatar
                    ranking
                }
                submitStats: submitStatsGlobal {
                    acSubmissionNum {
                        difficulty
                        count
                    }
                }
            }
        }
        """

        variables = {"keyword": search_term}
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(
                    self.base_url,
                    json={"query": query, "variables": variables}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "errors" in data:
                            error_msg = data["errors"][0].get("message", "Unknown error occurred")
                            await interaction.followup.send(f"GraphQL Error: {error_msg}")
                            return

                        users = data.get("data", {}).get("userProfileList", [])
                        
                        if not users:
                            await interaction.followup.send(f"No users found matching '{search_term}'")
                            return

                        embed = discord.Embed(
                            title=f"LeetCode Users Matching: {search_term}",
                            color=discord.Color.blue(),
                            description="Use `/leetcode_user <username>` to see detailed stats"
                        )

                        for user in users[:5]:
                            profile = user["profile"]
                            stats = user["submitStats"]["acSubmissionNum"]
                            total_solved = sum(stat["count"] for stat in stats)
                            
                            user_info = (
                                f"👤 Name: {profile.get('realName', 'N/A')}\n"
                                f"🏆 Rank: #{profile.get('ranking', 'N/A')}\n"
                                f"✅ Problems Solved: {total_solved}"
                            )
                            
                            embed.add_field(
                                name=f"Username: {user['username']}",
                                value=user_info,
                                inline=False
                            )

                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send(f"Error: HTTP {response.status}")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(Leetcode(bot)) 