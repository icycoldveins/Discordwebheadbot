import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from collections import Counter
import re
import asyncio

class MessageAnalytics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emoji_pattern = re.compile(r'<a?:.+?:\d+>|[\U0001F300-\U0001F9FF]|[\u2600-\u26FF\u2700-\u27BF]')

    @app_commands.command(name="analytics", description="Get message analytics for the server")
    @app_commands.describe(days="Number of days to analyze (default: 7, max: 30)")
    async def analytics(self, interaction: discord.Interaction, days: int = 7):
        await interaction.response.defer()

        if days > 30:
            await interaction.followup.send("Maximum analysis period is 30 days!")
            return

        start_time = datetime.utcnow() - timedelta(days=days)
        
        # Initialize counters
        channel_messages = Counter()
        user_messages = Counter()
        emoji_usage = Counter()
        hour_activity = Counter()
        day_activity = Counter()

        # Get list of text channels with permissions
        text_channels = [
            channel for channel in interaction.guild.text_channels 
            if channel.permissions_for(interaction.guild.me).read_message_history
        ]
        
        # Status message
        status = await interaction.followup.send(f"📊 Analyzing messages from {len(text_channels)} channels...")
        total_messages = 0
        channels_processed = 0

        try:
            for channel in text_channels:
                try:
                    async for message in channel.history(after=start_time, limit=None):
                        total_messages += 1
                        
                        # Channel activity
                        channel_messages[channel] += 1
                        
                        # User activity (skip bots)
                        if not message.author.bot:
                            user_messages[message.author] += 1
                        
                        # Emoji usage
                        emojis = self.emoji_pattern.findall(message.content)
                        emoji_usage.update(emojis)
                        for reaction in message.reactions:
                            if isinstance(reaction.emoji, str):
                                emoji_usage[reaction.emoji] += reaction.count
                        
                        # Time analysis
                        hour_activity[message.created_at.hour] += 1
                        day_name = message.created_at.strftime('%A')
                        day_activity[day_name] += 1

                        # Update status every 1000 messages
                        if total_messages % 1000 == 0:
                            await status.edit(content=f"📊 Analyzed {total_messages:,} messages from {channels_processed}/{len(text_channels)} channels...")

                    channels_processed += 1
                    await status.edit(content=f"📊 Analyzed {total_messages:,} messages from {channels_processed}/{len(text_channels)} channels...")

                except discord.Forbidden:
                    continue
                except Exception as e:
                    print(f"Error in channel {channel.name}: {e}")
                    continue

            # Create embed
            embed = discord.Embed(
                title=f"📊 Message Analytics for {interaction.guild.name}",
                description=f"Analysis of {total_messages:,} messages from the last {days} days",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )

            # Top Channels
            top_channels = sorted(channel_messages.items(), key=lambda x: x[1], reverse=True)[:5]
            channels_text = "\n".join(f"#{channel.name}: {count:,} messages" for channel, count in top_channels)
            embed.add_field(name="📝 Most Active Channels", value=channels_text or "No data", inline=False)

            # Top Users
            top_users = sorted(user_messages.items(), key=lambda x: x[1], reverse=True)[:5]
            users_text = "\n".join(f"{user.display_name}: {count:,} messages" for user, count in top_users)
            embed.add_field(name="👥 Most Active Users", value=users_text or "No data", inline=False)

            # Top Emojis
            top_emojis = sorted(emoji_usage.items(), key=lambda x: x[1], reverse=True)[:10]
            emojis_text = "\n".join(f"{emoji}: {count}" for emoji, count in top_emojis)
            embed.add_field(name="😀 Most Used Emojis", value=emojis_text or "No emojis found", inline=False)

            # Most Active Times
            most_active_hour = max(hour_activity.items(), key=lambda x: x[1])[0]
            most_active_day = max(day_activity.items(), key=lambda x: x[1])[0]
            
            activity_info = (
                f"⏰ Most Active Hour: {most_active_hour:02d}:00 UTC\n"
                f"📅 Most Active Day: {most_active_day}\n"
                f"💬 Total Messages: {total_messages:,}"
            )
            embed.add_field(name="⚡ Activity Overview", value=activity_info, inline=False)

            await status.delete()
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await status.edit(content=f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(MessageAnalytics(bot)) 