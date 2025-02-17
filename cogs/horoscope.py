import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from datetime import datetime
import asyncio

class Horoscope(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.signs = {
            "aries": "♈", "taurus": "♉", "gemini": "♊",
            "cancer": "♋", "leo": "♌", "virgo": "♍",
            "libra": "♎", "scorpio": "♏", "sagittarius": "♐",
            "capricorn": "♑", "aquarius": "♒", "pisces": "♓"
        }
        self.date_ranges = {
            "aries": "March 21 - April 19",
            "taurus": "April 20 - May 20",
            "gemini": "May 21 - June 20",
            "cancer": "June 21 - July 22",
            "leo": "July 23 - August 22",
            "virgo": "August 23 - September 22",
            "libra": "September 23 - October 22",
            "scorpio": "October 23 - November 21",
            "sagittarius": "November 22 - December 21",
            "capricorn": "December 22 - January 19",
            "aquarius": "January 20 - February 18",
            "pisces": "February 19 - March 20"
        }

    async def sign_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        signs = self.signs.keys()
        return [
            app_commands.Choice(name=sign.title(), value=sign)
            for sign in signs if current.lower() in sign.lower()
        ][:25]

    @app_commands.command(name="horoscope", description="Get your daily horoscope")
    @app_commands.describe(sign="Your zodiac sign")
    @app_commands.autocomplete(sign=sign_autocomplete)
    async def horoscope(self, interaction: discord.Interaction, sign: str):
        await interaction.response.defer()

        sign = sign.lower()
        if sign not in self.signs:
            await interaction.followup.send("Please provide a valid zodiac sign!")
            return

        try:
            params = {
                "sign": sign,
                "day": "today"
            }
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        await interaction.followup.send("Failed to fetch horoscope. Please try again later.")
                        return
                    
                    data = await response.json()
                    
                    if not data or "data" not in data:
                        await interaction.followup.send("Invalid response from horoscope service.")
                        return

                    horoscope_data = data["data"]
                    
                    embed = discord.Embed(
                        title=f"Daily Horoscope: {sign.title()} {self.signs[sign]}",
                        description=horoscope_data.get("horoscope_data", "No horoscope available for today."),
                        color=discord.Color.purple(),
                        timestamp=datetime.now()
                    )

                    embed.set_footer(text=f"Date Range: {self.date_ranges[sign]}")
                    await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(Horoscope(bot)) 