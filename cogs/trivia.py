import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import html
import asyncio
import random

class TriviaView(discord.ui.View):
    def __init__(self, cog, interaction, category):
        super().__init__(timeout=None)
        self.cog = cog
        self.original_interaction = interaction
        self.category = category
        self.active = True
        self.current_timeout_task = None

    @discord.ui.button(label="End Game", style=discord.ButtonStyle.red)
    async def end_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.original_interaction.user:
            self.active = False
            # Cancel current timeout task if it exists
            if self.current_timeout_task and not self.current_timeout_task.done():
                self.current_timeout_task.cancel()
            await interaction.response.send_message("Trivia game ended! Thanks for playing! 🎮")
            self.stop()
        else:
            await interaction.response.send_message("Only the person who started the trivia can end the game!", ephemeral=True)

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

    async def get_trivia_question(self, category: str = None):
        base_url = "https://opentdb.com/api.php?amount=1&type=multiple"
        if category:
            base_url += f"&category={category}"

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url) as response:
                if response.status != 200:
                    return None
                data = await response.json()
                return data['results'][0] if data['results'] else None

    async def handle_trivia(self, interaction: discord.Interaction, category: str = None, view: TriviaView = None):
        if not view:
            view = TriviaView(self, interaction, category)

        if not view.active:
            return

        question_data = await self.get_trivia_question(category)
        if not question_data:
            if interaction.response.is_done():
                await interaction.followup.send("Failed to fetch trivia question. Please try again.")
            else:
                await interaction.response.send_message("Failed to fetch trivia question. Please try again.")
            return

        # Decode HTML entities and prepare question
        question = html.unescape(question_data['question'])
        correct_answer = html.unescape(question_data['correct_answer'])
        incorrect_answers = [html.unescape(ans) for ans in question_data['incorrect_answers']]
        
        all_answers = incorrect_answers + [correct_answer]
        random.shuffle(all_answers)
        
        embed = discord.Embed(
            title="🎯 Trivia Time!",
            description=f"**Category:** {question_data['category']}\n**Difficulty:** {question_data['difficulty'].capitalize()}\n\n**Question:**\n{question}",
            color=discord.Color.blue()
        )

        for idx, answer in enumerate(all_answers, 1):
            embed.add_field(
                name=f"Option {idx}",
                value=answer,
                inline=False
            )

        embed.set_footer(text="You have 30 seconds to answer! React with the number corresponding to your answer.")

        # Handle different interaction states
        if interaction.response.is_done():
            message = await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.response.send_message(embed=embed, view=view)
            message = await interaction.original_response()

        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        for reaction in reactions:
            await message.add_reaction(reaction)

        def check(reaction, user):
            return user != self.bot.user and str(reaction.emoji) in reactions and reaction.message.id == message.id

        try:
            # Create a timeout task that can be cancelled
            view.current_timeout_task = asyncio.create_task(
                self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            )
            reaction, user = await view.current_timeout_task
            
            if not view.active:  # Check if game was ended while waiting
                return
                
            selected_idx = reactions.index(str(reaction.emoji))
            selected_answer = all_answers[selected_idx]
            
            result_embed = discord.Embed(
                title="🎯 Trivia Result",
                color=discord.Color.green() if selected_answer == correct_answer else discord.Color.red()
            )
            
            if selected_answer == correct_answer:
                result_embed.description = f"✅ Correct, {user.mention}! The answer was **{correct_answer}**"
            else:
                result_embed.description = f"❌ Sorry {user.mention}, that's incorrect. The correct answer was **{correct_answer}**"
            
            await interaction.followup.send(embed=result_embed)
            
            # Automatically ask next question if game is still active
            if view.active:
                await asyncio.sleep(3)  # Brief pause between questions
                await self.handle_trivia(interaction, category, view)

        except asyncio.TimeoutError:
            if view.active:  # Only show timeout message if game wasn't ended
                timeout_embed = discord.Embed(
                    title="⏰ Time's Up!",
                    description=f"The correct answer was **{correct_answer}**\nGame ended due to timeout!",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=timeout_embed)
                view.active = False
                view.stop()
        except asyncio.CancelledError:
            # Question was cancelled (game ended), do nothing
            pass

    @app_commands.command(name="trivia", description="Start a trivia game!")
    @app_commands.describe(category="Select a category (optional)")
    @app_commands.autocomplete(category=category_autocomplete)
    async def trivia(self, interaction: discord.Interaction, category: str = None):
        await interaction.response.defer()
        await self.handle_trivia(interaction, category)

async def setup(bot):
    await bot.add_cog(Trivia(bot)) 