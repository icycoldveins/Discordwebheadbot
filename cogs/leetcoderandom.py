import aiohttp
import discord
from discord.ext import commands
import requests
import random
import json
from bs4 import BeautifulSoup
from discord import Embed

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
    ...

    @commands.command(name='leetcode')
    async def problem(self, ctx, difficulty=None):
        problemUrlBase = 'https://leetcode.com/problems/'
        headers = {'Accept': 'application/json'}
        async with aiohttp.ClientSession() as session:
            async with session.get('https://leetcode.com/api/problems/all/', headers=headers) as resp:
                data = await resp.text()
                data = json.loads(data)
        problems = [Problem(p) for p in data['stat_status_pairs']]
        if difficulty:
            problems = [p for p in problems if p.difficulty == difficulty]

        if not problems:
            await ctx.send("No problems found with the given criteria.")
            return

        problem = random.choice(problems)
        # Fetch problem description
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
            async with session.post('https://leetcode.com/graphql', json=query) as resp:
                data = await resp.json()
        html_description = data['data']['question']['content']
        soup = BeautifulSoup(html_description, 'html.parser')
        problem.description = soup.get_text()

        if problem.description is None:
            problem.description = "No description available"
        
        # Create embed
        embed = Embed(title=f"{problem.title} - {problem.difficulty.capitalize()}", url=problemUrlBase + problem.titleSlug, description=problem.description[:2048])

        # Split description into chunks of 1024 characters and add each chunk as a field in the embed
        chunks = [problem.description[i:i+1024] for i in range(2000, len(problem.description), 1024)]
        for i, chunk in enumerate(chunks):
            embed.add_field(name=f"Description (cont'd {i+1})", value=chunk, inline=False)

        # Send embed
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leetcodeq(bot))