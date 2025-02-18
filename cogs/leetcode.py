import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
from datetime import datetime
from typing import Optional
import random
import json
from bs4 import BeautifulSoup

class Problem:
    def __init__(self, problemObject, description=None):
        self.id = problemObject['stat']['question_id']
        self.title = problemObject['stat']['question__title']
        self.titleSlug = problemObject['stat']['question__title_slug']
        difficulty_map = {1: 'easy', 2: 'medium', 3: 'hard'}
        self.difficulty = difficulty_map[problemObject['difficulty']['level']]
        self.paidOnly = problemObject['paid_only']
        self.description = description

class Leetcode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://leetcode.com/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://leetcode.com"
        }

    @app_commands.command(name="lookup", description="Search for a LeetCode user")
    @app_commands.describe(username="Partial username to search for")
    async def lookup(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()

        # Profile query
        profile_query = """
        query getUserProfile($username: String!) {
            matchedUser(username: $username) {
                username
                submitStats: submitStatsGlobal {
                    acSubmissionNum {
                        difficulty
                        count
                    }
                }
                profile {
                    realName
                    ranking
                    userAvatar
                }
            }
        }
        """

        # Recent submissions query
        recent_query = """
        query recentAcSubmissions($username: String!) {
            recentAcSubmissionList(username: $username) {
                title
                titleSlug
                timestamp
                lang
            }
        }
        """

        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                # Fetch profile data
                profile_response = await session.post(
                    self.base_url,
                    json={"query": profile_query, "variables": {"username": username}}
                )
                profile_data = await profile_response.json()

                # Fetch recent submissions
                recent_response = await session.post(
                    self.base_url,
                    json={"query": recent_query, "variables": {"username": username}}
                )
                recent_data = await recent_response.json()

                if "errors" in profile_data:
                    error_msg = profile_data["errors"][0].get("message", "Unknown error occurred")
                    await interaction.followup.send(f"Error: {error_msg}")
                    return

                user_data = profile_data.get("data", {}).get("matchedUser")
                if not user_data:
                    await interaction.followup.send(f"User '{username}' not found!")
                    return

                # Create embed
                embed = discord.Embed(
                    title=f"LeetCode Profile: {username}",
                    url=f"https://leetcode.com/{username}",
                    color=discord.Color.blue()
                )

                # Set avatar if available
                if user_data["profile"].get("userAvatar"):
                    embed.set_thumbnail(url=user_data["profile"]["userAvatar"])

                # Profile info
                profile = user_data["profile"]
                stats = user_data["submitStats"]["acSubmissionNum"]
                
                user_info = (
                    f"👤 Name: {profile.get('realName', 'N/A')}\n"
                    f"🏆 Rank: #{profile.get('ranking', 'N/A')}\n"
                    f"Problem Breakdown:"
                )
                
                # Add solving statistics
                for stat in stats:
                    difficulty = stat["difficulty"]
                    if difficulty == "All":
                        emoji = "💫"
                    elif difficulty == "Easy":
                        emoji = "🟢"
                    elif difficulty == "Medium":
                        emoji = "🟡"
                    elif difficulty == "Hard":
                        emoji = "🔴"
                    user_info += f"\n{emoji} {difficulty}: {stat['count']}"

                embed.add_field(name="User Statistics", value=user_info, inline=False)

                # Add recent submissions
                submissions = recent_data.get("data", {}).get("recentAcSubmissionList", [])
                if submissions:
                    recent_info = ""
                    language_emojis = {
                        "python": "🐍",
                        "python3": "🐍",
                        "java": "☕",
                        "javascript": "🟨",
                        "cpp": "🔵",
                        "c++": "🔵",
                        "c": "©️",
                        "csharp": "©️#",
                        "ruby": "💎",
                        "swift": "🕊️",
                        "golang": "🐹",
                        "go": "🐹",
                        "scala": "⚡",
                        "kotlin": "🎯",
                        "rust": "🦀",
                        "php": "🐘",
                        "typescript": "💙"
                    }
                    
                    for sub in submissions[:5]:
                        try:
                            timestamp = datetime.fromtimestamp(int(sub["timestamp"]))
                            problem_link = f"https://leetcode.com/problems/{sub['titleSlug']}/"
                            lang = sub.get("lang", "").lower()
                            lang_emoji = language_emojis.get(lang, "💻")
                            recent_info += f"• [{sub['title']}]({problem_link})\n  {lang_emoji} {lang.capitalize()}\n"
                        except (ValueError, TypeError) as e:
                            continue
                    
                    if recent_info:
                        embed.add_field(
                            name="📝 Recent Accepted Submissions",
                            value=recent_info,
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name="📝 Recent Accepted Submissions",
                            value="No recent submissions",
                            inline=False
                        )

                await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(Leetcode(bot)) 