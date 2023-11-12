import discord
from discord.ext import commands
import sqlite3


class ParticipationCounter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('counter.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS participation_counter
                          (user_id INTEGER PRIMARY KEY, count INTEGER)''')
        self.conn.commit()

    @commands.command()
    async def participation(self, ctx):
        user = ctx.author
        self.c.execute(
            "SELECT count FROM participation_counter WHERE user_id=?", (user.id,))
        result = self.c.fetchone()
        if result is None:
            count = 1
            self.c.execute(
                "INSERT INTO participation_counter VALUES (?, ?)", (user.id, count))
        else:
            count = result[0] + 1
            self.c.execute(
                "UPDATE participation_counter SET count=? WHERE user_id=?", (count, user.id))
        self.conn.commit()
        await ctx.send(f"{user.name} has participated {count} times this semester.")

    @commands.command()
    async def wipe(self, ctx):
        self.c.execute("DELETE FROM participation_counter")
        self.conn.commit()
        await ctx.send("Participation counter has been wiped.")

    @commands.command()
    async def undoparticipate(self, ctx):
        user = ctx.author
        self.c.execute(
            "SELECT count FROM participation_counter WHERE user_id=?", (user.id,))
        result = self.c.fetchone()
        if result is None:
            await ctx.send("You haven't participated yet.")
        else:
            count = result[0] - 1
            self.c.execute(
                "UPDATE participation_counter SET count=? WHERE user_id=?", (count, user.id))
            self.conn.commit()
            await ctx.send(f"{user.name} has participated {count} times.")

    def cog_unload(self):
        self.conn.close()


async def setup(bot):
    await bot.add_cog(ParticipationCounter(bot))
