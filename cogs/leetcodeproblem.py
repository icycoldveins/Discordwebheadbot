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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    @app_commands.command(name="problem", description="Get a specific LeetCode problem by number")
    @app_commands.describe(number="The problem number you want to look up")
    async def problem(self, interaction: discord.Interaction, number: int):
        await interaction.response.defer()

        query = """
        query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
            problemsetQuestionList: questionList(
                categorySlug: $categorySlug
                limit: $limit
                skip: $skip
                filters: $filters
            ) {
                questions: data {
                    questionId
                    questionFrontendId
                    title
                    titleSlug
                    content
                    difficulty
                    topicTags {
                        name
                    }
                }
            }
        }
        """

        try:
            variables = {
                "categorySlug": "",
                "skip": 0,
                "limit": 2000,  # Large enough to get all problems
                "filters": {}
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=self.headers,
                    json={"query": query, "variables": variables}
                ) as response:
                    if response.status != 200:
                        await interaction.followup.send("Failed to fetch problem details")
                        return
                    
                    result = await response.json()
                    questions = result.get('data', {}).get('problemsetQuestionList', {}).get('questions', [])
                    
                    # Find the problem with matching number
                    question_data = None
                    for q in questions:
                        if int(q['questionFrontendId']) == number:
                            question_data = q
                            break

                    if not question_data:
                        await interaction.followup.send(f"Could not find problem #{number}")
                        return

                    # Clean up HTML content
                    soup = BeautifulSoup(question_data['content'], 'html.parser')
                    description = soup.get_text().strip()

                    # Create embed
                    difficulty_colors = {
                        'Easy': discord.Color.green(),
                        'Medium': discord.Color.gold(),
                        'Hard': discord.Color.red()
                    }

                    embed = discord.Embed(
                        title=f"#{number}. {question_data['title']}",
                        url=f"https://leetcode.com/problems/{question_data['titleSlug']}/",
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
                        parts = [description[i:i+4096] for i in range(0, len(description), 4096)]
                        embed.description = parts[0]
                        
                        # Send the first embed
                        await interaction.followup.send(embed=embed)
                        
                        # Send remaining parts as separate messages
                        for part in parts[1:]:
                            continuation_embed = discord.Embed(
                                description=part,
                                color=embed.color
                            )
                            await interaction.followup.send(embed=continuation_embed)
                    else:
                        embed.description = description
                        await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(LeetcodeProblem(bot)) 