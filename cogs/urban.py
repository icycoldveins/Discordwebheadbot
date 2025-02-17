import discord
from discord.ext import commands
from discord import app_commands
import aiohttp

class UrbanDictionary(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://api.urbandictionary.com/v0/define"

    @app_commands.command(name="define", description="Look up a word or phrase on Urban Dictionary")
    @app_commands.describe(term="The word or phrase you want to look up")
    async def define(self, interaction: discord.Interaction, term: str):
        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}?term={term}") as response:
                if response.status != 200:
                    await interaction.followup.send("Failed to fetch definition. Please try again.")
                    return
                
                data = await response.json()
                definitions = data.get('list', [])

                if not definitions:
                    await interaction.followup.send(f"No definitions found for '{term}'")
                    return

                # Get the top definition (most upvoted)
                top_def = definitions[0]
                
                embed = discord.Embed(
                    title=f"📚 Urban Dictionary: {term}",
                    url=top_def['permalink'],
                    color=discord.Color.green()
                )

                # Clean up definition and example
                definition = top_def['definition'][:1024] if len(top_def['definition']) > 1024 else top_def['definition']
                example = top_def['example'][:1024] if len(top_def['example']) > 1024 else top_def['example']

                embed.add_field(
                    name="Definition",
                    value=definition,
                    inline=False
                )

                if example:
                    embed.add_field(
                        name="Example",
                        value=f"*{example}*",
                        inline=False
                    )

                embed.add_field(
                    name="👍 Upvotes",
                    value=str(top_def['thumbs_up']),
                    inline=True
                )
                embed.add_field(
                    name="👎 Downvotes",
                    value=str(top_def['thumbs_down']),
                    inline=True
                )

                embed.set_footer(text=f"Definition by {top_def['author']} | Written on {top_def['written_on'][:10]}")

                await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UrbanDictionary(bot)) 