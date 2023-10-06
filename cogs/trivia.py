import discord
from discord.ext import commands
import requests
import html
import random

class Trivia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def trivia(self, ctx, category=None):
        # Forming the API endpoint
        endpoint = "https://opentdb.com/api.php?amount=10"
        if category:
            endpoint += f"&category={category}"

        # Making a request to the API
        response = requests.get(endpoint)
        data = response.json()

        # Check if we got a valid response
        if data["response_code"] != 0:
            await ctx.send("Error fetching trivia question.")
            return

        # Extract question and answers
        question = html.unescape(data["results"][0]["question"])
        correct_answer = html.unescape(data["results"][0]["correct_answer"])
        options = [html.unescape(ans) for ans in data["results"][0]["incorrect_answers"]]
        options.append(correct_answer)
        random.shuffle(options)  # Randomize the options

        # Send the question and options to the channel
        content = f"**{question}**\n"
        for idx, option in enumerate(options, 1):
            content += f"{idx}. {option}\n"

        await ctx.send(content)

        # Wait for a user response
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.isdigit() and 1 <= int(msg.content) <= len(options)

        try:
            msg = await self.bot.wait_for('message', timeout=60.0, check=check)
            if options[int(msg.content) - 1] == correct_answer:
                await ctx.send("Correct!")
            else:
                await ctx.send(f"Wrong! The correct answer was: {correct_answer}")

        except discord.TimeoutError:
            await ctx.send(f"Time's up! The correct answer was: {correct_answer}")
async def setup(bot):
    await bot.add_cog(Trivia(bot))
