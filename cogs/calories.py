import discord
from discord.ext import commands
import aiohttp
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class NutritionInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.nutritionix_app_id = os.getenv('NUTRITIONIX_APP_ID')
        self.nutritionix_app_key = os.getenv('NUTRITIONIX_APP_KEY')
        self.nutritionix_url = 'https://trackapi.nutritionix.com/v2/natural/nutrients'
        
        # Debug prints to check if environment variables are loaded
        print("Nutritionix App ID:", self.nutritionix_app_id)
        print("Nutritionix App Key:", self.nutritionix_app_key)
    
    @commands.command()
    async def calories(self, ctx, *, food_item: str):
        """
        Get the number of calories in a food item.

        Usage:
        !calories <food_item>
        """
        headers = {
            'x-app-id': self.nutritionix_app_id,
            'x-app-key': self.nutritionix_app_key,
            'Content-Type': 'application/json'
        }
        body = {
            'query': food_item
        }

        # Debug print to check headers and body
        print("Headers:", headers)
        print("Body:", body)

        async with aiohttp.ClientSession() as session:
            async with session.post(self.nutritionix_url, headers=headers, data=json.dumps(body)) as response:
                if response.status == 200:
                    data = await response.json()
                    calories = self.parse_calories(data)
                    if calories is not None:
                        await ctx.send(f"'{food_item}' contains about {calories} calories.")
                    else:
                        await ctx.send("Could not determine the calories for the specified food item.")
                elif response.status == 401:
                    await ctx.send("Unauthorized. Please check your Nutritionix API credentials.")
                else:
                    await ctx.send(f"Error: Could not retrieve nutritional information. API responded with status code: {response.status}")

    def parse_calories(self, data):
        """
        Parse the calorie information from the Nutritionix API response.

        :param data: Response data from the API
        :return: Calorie count or None if not found
        """
        if data.get('foods'):
            return data['foods'][0].get('nf_calories')
        return None

async def setup(bot):
    await bot.add_cog(NutritionInfo(bot))
