import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import asyncio

class DiscordStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="serverstats", description="Get detailed server statistics")
    async def serverstats(self, interaction: discord.Interaction):
        await interaction.response.defer()

        guild = interaction.guild
        
        # Get member statistics
        total_members = guild.member_count
        online_members = len([m for m in guild.members if m.status != discord.Status.offline])
        bot_count = len([m for m in guild.members if m.bot])
        human_count = total_members - bot_count

        # Get channel statistics
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)

        # Get role count
        role_count = len(guild.roles) - 1  # Subtract @everyone role

        # Create embed
        embed = discord.Embed(
            title=f"📊 Server Statistics: {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        # Server Info
        server_info = (
            f"📅 Created: {guild.created_at.strftime('%Y-%m-%d')}\n"
            f"👑 Owner: {guild.owner.mention}\n"
            f"🌟 Boost Level: {guild.premium_tier}\n"
            f"📈 Boost Count: {guild.premium_subscription_count}"
        )
        embed.add_field(name="Server Information", value=server_info, inline=False)

        # Member Stats
        member_stats = (
            f"👥 Total Members: {total_members}\n"
            f"🟢 Online Members: {online_members}\n"
            f"👤 Humans: {human_count}\n"
            f"🤖 Bots: {bot_count}"
        )
        embed.add_field(name="Member Statistics", value=member_stats, inline=True)

        # Channel Stats
        channel_stats = (
            f"💬 Text Channels: {text_channels}\n"
            f"🔊 Voice Channels: {voice_channels}\n"
            f"📁 Categories: {categories}\n"
            f"🎭 Roles: {role_count}"
        )
        embed.add_field(name="Channel Statistics", value=channel_stats, inline=True)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="userstats", description="Get statistics about a user")
    @app_commands.describe(user="The user to get stats for (defaults to you)")
    async def userstats(self, interaction: discord.Interaction, user: discord.Member = None):
        await interaction.response.defer()
        
        user = user or interaction.user
        guild = interaction.guild

        # Create embed
        embed = discord.Embed(
            title=f"👤 User Statistics: {user.display_name}",
            color=user.color if user.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.now()
        )

        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)

        # Basic Info
        basic_info = (
            f"🆔 User ID: {user.id}\n"
            f"📛 Display Name: {user.display_name}\n"
            f"🏷️ Username: {user.name}\n"
            f"🤖 Bot: {'Yes' if user.bot else 'No'}\n"
            f"🎭 Top Role: {user.top_role.mention}"
        )
        embed.add_field(name="Basic Information", value=basic_info, inline=False)

        # Dates
        join_position = sorted(guild.members, key=lambda m: m.joined_at or datetime.max).index(user) + 1
        dates_info = (
            f"📅 Account Created: <t:{int(user.created_at.timestamp())}:R>\n"
            f"📥 Server Joined: <t:{int(user.joined_at.timestamp())}:R>\n"
            f"📊 Join Position: #{join_position}"
        )
        embed.add_field(name="Dates", value=dates_info, inline=False)

        # Status and Activity
        status_emojis = {
            discord.Status.online: "🟢",
            discord.Status.idle: "🟡",
            discord.Status.dnd: "🔴",
            discord.Status.offline: "⚫"
        }
        
        status_info = f"{status_emojis.get(user.status, '⚪')} {str(user.status).title()}"
        if user.activity:
            if isinstance(user.activity, discord.Spotify):
                status_info += f"\n🎵 Listening to Spotify: {user.activity.title}"
            elif isinstance(user.activity, discord.Game):
                status_info += f"\n🎮 Playing: {user.activity.name}"
            elif isinstance(user.activity, discord.Streaming):
                status_info += f"\n📺 Streaming: {user.activity.name}"
        
        embed.add_field(name="Current Status", value=status_info, inline=True)

        # Roles
        roles = [role.mention for role in reversed(user.roles[1:])]  # Exclude @everyone
        roles_str = " ".join(roles) if roles else "No roles"
        embed.add_field(name=f"Roles [{len(roles)}]", value=roles_str[:1024], inline=False)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DiscordStats(bot)) 