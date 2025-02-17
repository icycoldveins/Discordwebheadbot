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

    @app_commands.command(name="random", description="Get 5 random LeetCode problems")
    @app_commands.describe(difficulty="Problem difficulty (easy, medium, hard)")
    async def random(self, interaction: discord.Interaction, difficulty: str = None):
        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://leetcode.com/api/problems/all/') as resp:
                    data = await resp.json()

            if difficulty:
                difficulty = difficulty.lower()
                if difficulty not in ['easy', 'medium', 'hard']:
                    await interaction.followup.send("Invalid difficulty. Please choose 'easy', 'medium', or 'hard'.")
                    return

            problems = [Problem(p) for p in data['stat_status_pairs'] if not p['paid_only']]
            
            if difficulty:
                problems = [p for p in problems if p.difficulty == difficulty]

            if not problems:
                await interaction.followup.send("No problems found with the given criteria.")
                return

            selected_problems = random.sample(problems, min(5, len(problems)))
            
            embed = discord.Embed(
                title="🎲 Random LeetCode Problems",
                description=f"Here are {'5' if len(selected_problems) == 5 else len(selected_problems)} random "
                           f"{difficulty + ' ' if difficulty else ''}problems:",
                color=discord.Color.blue()
            )

            difficulty_emojis = {
                'easy': '🟢',
                'medium': '🟡',
                'hard': '🔴'
            }

            for problem in selected_problems:
                problem_url = f'https://leetcode.com/problems/{problem.titleSlug}/'
                difficulty_emoji = difficulty_emojis.get(problem.difficulty, '❓')
                embed.add_field(
                    name=f"{difficulty_emoji} {problem.title}",
                    value=f"[Solve Problem]({problem_url})",
                    inline=False
                )

            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(Leetcodeq(bot))