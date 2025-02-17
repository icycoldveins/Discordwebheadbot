import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from bs4 import BeautifulSoup

class LeetcodeProblem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://leetcode.com/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        }

    @app_commands.command(name="problem", description="Get a specific LeetCode problem by number")
    @app_commands.describe(number="The problem number you want to look up")
    async def problem(self, interaction: discord.Interaction, number: int):
        await interaction.response.defer()

        query = """
        query getQuestionDetail($titleSlug: String!) {
            question(titleSlug: $titleSlug) {
                title
                titleSlug
                difficulty
                contentk
                topicTags {
                    name
                }
            }
        }
        """

        try:
            # First, get the problem list to find the titleSlug
            async with aiohttp.ClientSession() as session:
                async with session.get('https://leetcode.com/api/problems/all/') as resp:
                    if resp.status != 200:
                        await interaction.followup.send("Failed to fetch problems from LeetCode")
                        return
                    data = await resp.json()

            # Find the problem with matching number
            problem_data = None
            for problem in data['stat_status_pairs']:
                if problem['stat']['frontend_question_id'] == number:
                    problem_data = problem
                    break

            if not problem_data:
                await interaction.followup.send(f"Could not find problem #{number}")
                return

            title_slug = problem_data['stat']['question__title_slug']

            # Now fetch the problem details
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(
                    self.base_url,
                    json={"query": query, "variables": {"titleSlug": title_slug}}
                ) as response:
                    if response.status != 200:
                        await interaction.followup.send("Failed to fetch problem details")
                        return
                    
                    result = await response.json()
                    question_data = result['data']['question']

                    if not question_data:
                        await interaction.followup.send(f"Could not fetch details for problem #{number}")
                        return

                    # Clean up HTML content
                    soup = BeautifulSoup(question_data['content'], 'html.parser')
                    description = soup.get_text()

                    # Create embed
                    difficulty_colors = {
                        'Easy': discord.Color.green(),
                        'Medium': discord.Color.gold(),
                        'Hard': discord.Color.red()
                    }

                    embed = discord.Embed(
                        title=f"#{number}. {question_data['title']}",
                        url=f"https://leetcode.com/problems/{title_slug}/",
                        color=difficulty_colors.get(question_data['difficulty'], discord.Color.blue())
                    )

                    # Add difficulty with emoji
                    difficulty_emojis = {'Easy': '🟢', 'Medium': '🟡', 'Hard': '🔴'}
                    embed.add_field(
                        name="Difficulty",
                        value=f"{difficulty_emojis.get(question_data['difficulty'], '❓')} {question_data['difficulty']}",
                        inline=True
                    )

                    # Add topics
                    topics = [tag['name'] for tag in question_data['topicTags']]
                    if topics:
                        embed.add_field(
                            name="Topics",
                            value=", ".join(f"`{topic}`" for topic in topics),
                            inline=True
                        )

                    # Split description if it's too long
                    if len(description) > 4096:
                        description = description[:4093] + "..."

                    # Add description
                    embed.description = description

                    await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(LeetcodeProblem(bot)) 