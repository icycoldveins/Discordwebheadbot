import discord
from discord.ext import commands
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()


class ParticipationCounter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        mongo_url = os.getenv('MONGO_URL')
        self.client = MongoClient(mongo_url)
        self.db = self.client['ParticipationCount']
        self.collection = self.db['users']

    @commands.command()
    async def participation(self, ctx):
        user = ctx.author
        result = self.collection.find_one({'user_id': user.id})
        if result is None:
            count = 1
            self.collection.insert_one({'user_id': user.id, 'count': count})
        else:
            count = result['count'] + 1
            self.collection.update_one({'user_id': user.id}, {
                                       '$set': {'count': count}})
        await ctx.send(f"{user.name} has participated {count} times this semester.")

    @commands.command()
    async def wipe(self, ctx):
        self.collection.delete_many({})
        await ctx.send("Participation counter has been wiped.")

    @commands.command()
    async def undoparticipate(self, ctx):
        user = ctx.author
        result = self.collection.find_one({'user_id': user.id})
        if result is None:
            await ctx.send("You haven't participated yet.")
        else:
            count = result['count'] - 1
            self.collection.update_one({'user_id': user.id}, {
                                       '$set': {'count': count}})
            await ctx.send(f"{user.name} has participated {count} times.")

    def cog_unload(self):
        self.client.close()


async def setup(bot):
    await bot.add_cog(ParticipationCounter(bot))
