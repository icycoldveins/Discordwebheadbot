import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import html
import asyncio
import random

class Trivia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.categories = {
            'General Knowledge': 9,
            'Books': 10,
            'Film': 11,
            'Music': 12,
            'Television': 14,
            'Video Games': 15,
            'Science & Nature': 17,
            'Sports': 21,
            'Geography': 22,
            'History': 23,
            'Animals': 27
        }

    async def category_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        current = current.lower()
        return [
            app_commands.Choice(name=category, value=str(category_id))
            for category, category_id in self.categories.items()
            if current in category.lower()
        ]

    @app_commands.command(name="trivia", description="Start a trivia game!")
    @app_commands.describe(category="Select a category (optional)")
    @app_commands.autocomplete(category=category_autocomplete)
    async def trivia(self, interaction: discord.Interaction, category: str = None):
        await interaction.response.defer()

        # Prepare API URL
        base_url = "https://opentdb.com/api.php?amount=1&type=multiple"
        if category:
            base_url += f"&category={category}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url) as response:
                    if response.status != 200:
                        await interaction.followup.send("Failed to fetch trivia question. Please try again.")
                        return

                    data = await response.json()
                    if not data['results']:
                        await interaction.followup.send("No trivia questions found. Please try again.")
                        return

                    question_data = data['results'][0]
                    
                    # Decode HTML entities and prepare question
                    question = html.unescape(question_data['question'])
                    correct_answer = html.unescape(question_data['correct_answer'])
                    incorrect_answers = [html.unescape(ans) for ans in question_data['incorrect_answers']]
                    
                    # Prepare answers
                    all_answers = incorrect_answers + [correct_answer]
                    random.shuffle(all_answers)
                    
                    # Create embed
                    embed = discord.Embed(
                        title="🎯 Trivia Time!",
                        description=f"**Category:** {question_data['category']}\n**Difficulty:** {question_data['difficulty'].capitalize()}\n\n**Question:**\n{question}",
                        color=discord.Color.blue()
                    )

                    # Add answers as fields
                    for idx, answer in enumerate(all_answers, 1):
                        embed.add_field(
                            name=f"Option {idx}",
                            value=answer,
                            inline=False
                        )

                    # Add footer with time limit
                    embed.set_footer(text="You have 30 seconds to answer! React with the number corresponding to your answer.")

                    # Send question
                    message = await interaction.followup.send(embed=embed)

                    # Add reaction options
                    reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
                    for reaction in reactions:
                        await message.add_reaction(reaction)

                    def check(reaction, user):
                        return user != self.bot.user and str(reaction.emoji) in reactions and reaction.message.id == message.id

                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                        
                        # Get user's answer
                        selected_idx = reactions.index(str(reaction.emoji))
                        selected_answer = all_answers[selected_idx]
                        
                        # Create result embed
                        result_embed = discord.Embed(
                            title="🎯 Trivia Result",
                            color=discord.Color.green() if selected_answer == correct_answer else discord.Color.red()
                        )
                        
                        if selected_answer == correct_answer:
                            result_embed.description = f"✅ Correct, {user.mention}! The answer was **{correct_answer}**"
                        else:
                            result_embed.description = f"❌ Sorry {user.mention}, that's incorrect. The correct answer was **{correct_answer}**"
                        
                        await interaction.followup.send(embed=result_embed)

                    except asyncio.TimeoutError:
                        timeout_embed = discord.Embed(
                            title="⏰ Time's Up!",
                            description=f"The correct answer was **{correct_answer}**",
                            color=discord.Color.orange()
                        )
                        await interaction.followup.send(embed=timeout_embed)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(Trivia(bot)) 