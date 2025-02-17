import aiohttp
import discord
from discord.ext import commands
import requests
import random
import json
from bs4 import BeautifulSoup
from discord import Embed
from discord import app_commands

class Problem:
    def __init__(self, problemObject, description=None):
        self.id = problemObject['stat']['question_id']
        self.title = problemObject['stat']['question__title']
        self.titleSlug = problemObject['stat']['question__title_slug']
        difficulty_map = {1: 'easy', 2: 'medium', 3: 'hard'}
        self.difficulty = difficulty_map[problemObject['difficulty']['level']]
        self.paidOnly = problemObject['paid_only']
        self.description = description


class Leetcodeq(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.difficulties = ["easy", "medium", "hard"]

    async def difficulty_autocomplete(
        self, 
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        current = current.lower()
        return [
            app_commands.Choice(name=diff.capitalize(), value=diff)
            for diff in self.difficulties
            if current in diff.lower()
        ]

    @app_commands.command(name="random", description="Get 5 random LeetCode problems")
    @app_commands.describe(difficulty="Problem difficulty (easy, medium, hard)")
    @app_commands.autocomplete(difficulty=difficulty_autocomplete)
    async def random(self, interaction: discord.Interaction, difficulty: str = None):
        await interaction.response.defer()
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }
        
        query = """
        query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
            problemsetQuestionList: questionList(
                categorySlug: $categorySlug
                limit: $limit
                skip: $skip
                filters: $filters
            ) {
                total: totalNum
                questions: data {
                    questionId
                    title
                    titleSlug
                    difficulty
                    isPaidOnly
                }
            }
        }
        """
        
        variables = {
            "categorySlug": "",
            "skip": 0,
            "limit": 100,
            "filters": {}
        }
        
        if difficulty:
            difficulty = difficulty.upper()
            variables["filters"] = {"difficulty": difficulty}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://leetcode.com/graphql',
                    headers=headers,
                    json={"query": query, "variables": variables}
                ) as resp:
                    if resp.status != 200:
                        await interaction.followup.send(f"Failed to fetch problems. Status: {resp.status}")
                        return
                    
                    data = await resp.json()
                    
                    if not data or 'data' not in data or 'problemsetQuestionList' not in data['data']:
                        await interaction.followup.send("Invalid response format from LeetCode")
                        return

                    questions = [q for q in data['data']['problemsetQuestionList']['questions'] 
                               if not q['isPaidOnly']]

                    if not questions:
                        await interaction.followup.send("No problems found with the given criteria.")
                        return

                    selected_problems = random.sample(questions, min(5, len(questions)))
                    
                    embed = discord.Embed(
                        title="🎲 Random LeetCode Problems",
                        description=f"Here are {'5' if len(selected_problems) == 5 else len(selected_problems)} random "
                                   f"{difficulty.lower() + ' ' if difficulty else ''}problems:",
                        color=discord.Color.blue()
                    )

                    difficulty_emojis = {
                        'EASY': '🟢',
                        'MEDIUM': '🟡',
                        'HARD': '🔴'
                    }

                    for problem in selected_problems:
                        problem_url = f'https://leetcode.com/problems/{problem["titleSlug"]}/'
                        difficulty_emoji = difficulty_emojis.get(problem['difficulty'], '❓')
                        embed.add_field(
                            name=f"{difficulty_emoji} {problem['title']}",
                            value=f"[Solve Problem]({problem_url})",
                            inline=False
                        )

                    await interaction.followup.send(embed=embed)
                    
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(Leetcodeq(bot))