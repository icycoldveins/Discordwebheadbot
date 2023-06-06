import os
import random

import discord
from discord.ext import commands, tasks

import config
from datetime import datetime, timedelta  # Add this line to import datetime

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all()) 
reminders = []


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def insult(ctx, user: discord.Member):
    insults = [
        f"Hey {user.mention}, you're as useless as the 'g' in lasagna.",
        f"{user.mention}, your face makes onions cry.",
        f"{user.mention}, you're so dumb, you think a quarterback is a refund.",
        f"Roses are red, violets are blue, {user.mention} is ugly, and that's true.",
        f"{user.mention}, you must have been born on a highway because that's where most accidents happen.",
        f"{user.mention}, you're so ugly, even Hello Kitty says goodbye.",
        f"Is your name Google? Because you have everything I'm not looking for, {user.mention}.",
        f"{user.mention}, you're the reason why aliens won't talk to us.",
        f"{user.mention}, if you were a vegetable, you'd be a 'cute-cumber'.",
        f"Are you made of copper and tellurium? Because you're Cu-Te, {user.mention}.",
        f"{user.mention}, you're so clumsy, you could trip over a cordless phone.",
        f"Calling you an idiot would be an insult to all the stupid people, {user.mention}.",
        f"{user.mention}, if laughter is the best medicine, your face must be curing the world.",
        f"{user.mention}, if brains were dynamite, you wouldn't have enough to blow your nose.",
        f"You're so slow, {user.mention}, you could count the grains of sand in an hourglass.",
        f"{user.mention}, you're like a light switch - even a little kid can turn you on.",
        f"Did your parents ever ask you to run away from home, {user.mention}? They missed out on a great opportunity.",
        f"{user.mention}, you're so short, you can play handball on the curb.",
        f"Is your name Wi-Fi? Because I'm feeling a connection with you...not, {user.mention}."
    ]
    insult = random.choice(insults)
    await ctx.send(insult)

@bot.command()
async def compliment(ctx, user: discord.Member):
    compliments = [
        f"Hey {user.mention}, you light up the room with your smile.",
        f"{user.mention}, you have the most contagious laughter.",
        f"{user.mention}, you're incredibly talented and creative.",
        f"Roses are red, violets are blue, {user.mention}, you make the world a better place, it's true.",
        f"{user.mention}, your positive energy is truly uplifting.",
        f"{user.mention}, you have a heart of gold and a beautiful soul.",
        f"You're so intelligent, {user.mention}, and your ideas are always inspiring.",
        f"{user.mention}, your kindness and compassion touch the lives of everyone around you.",
        f"{user.mention}, you're a great listener and always offer the best advice.",
        f"Your perseverance and determination, {user.mention}, are admirable qualities.",
        f"{user.mention}, you have an incredible sense of style and always look amazing.",
        f"{user.mention}, you're an amazing friend and always know how to make others feel valued.",
        f"You have a voice that could melt anyone's heart, {user.mention}.",
        f"{user.mention}, your talent and hard work never cease to amaze me.",
        f"{user.mention}, you're a ray of sunshine on even the cloudiest of days.",
        f"Your positivity and optimism, {user.mention}, are truly inspiring.",
        f"{user.mention}, you're an absolute gem, and the world is lucky to have you.",
        f"Is your name Google? Because you have everything I'm searching for, {user.mention}.",
        f"{user.mention}, your presence brings joy and warmth wherever you go.",
        f"{user.mention}, you're a true source of strength and support for those around you."
    ]
    compliment = random.choice(compliments)
    await ctx.send(compliment)
@bot.command()
async def roll(ctx, num_dice: int = 1, num_faces: int = 6):
    if num_dice <= 0 or num_faces <= 1:
        await ctx.send("Invalid parameters. Please provide a positive number of dice and faces.")
        return
    
    results = []
    for _ in range(num_dice):
        result = random.randint(1, num_faces)
        results.append(str(result))
    
    if num_dice == 1:
        await ctx.send(f"The dice rolled and you got: {results[0]}")
    else:
        total = sum(int(result) for result in results)
        await ctx.send(f"The dice rolled and you got: {' '.join(results)} (Total: {total})")
@bot.command()
async def conch(ctx, question: str):
    answers = [
        "Maybe someday.",
        "Nothing.",
        "Neither.",
        "I don't think so.",
        "No.",
        "Yes.",
        "Try asking again.",
        "You cannot get to the top by sitting on your bottom.",
        "I see a new sauce in your future.",
        "Ask next time.",
        "Follow the seahorse."
    ]
    answer = random.choice(answers)
    await ctx.send(f"The Magic Conch says: {answer}")
    
@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")
@bot.command()
async def remindme(ctx, time: str, *, reminder: str):
    """Set a reminder in minutes/hours/days/months/years."""
    time_value = int(time[:-1])
    time_unit = time[-1]
    reminder_time = calculate_reminder_time(time_value, time_unit)
    reminders.append((reminder_time, reminder, ctx.author))
    await ctx.send(f"Okay, I will remind you in {time} about: {reminder}")

def calculate_reminder_time(value, unit):
    now = datetime.now()
    if unit == 'm':
        return now + timedelta(minutes=value)
    elif unit == 'h':
        return now + timedelta(hours=value)
    elif unit == 'd':
        return now + timedelta(days=value)
    elif unit == 'M':
        return now.replace(month=now.month + value)
    elif unit == 'y':
        return now.replace(year=now.year + value)

@tasks.loop(seconds=10)
async def check_reminders():
    if len(reminders) > 0:
        for reminder in reminders:
            reminder_time, reminder_text, author = reminder
            if reminder_time <= datetime.now():
                user = bot.get_user(author.id)
                await user.send(f"Reminder: {reminder_text}")
                reminders.remove(reminder)

@check_reminders.before_loop
async def before_check_reminders():
    await bot.wait_until_ready()

check_reminders.start()

bot.run(config.BOT_TOKEN)
 