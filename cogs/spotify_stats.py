import discord
from discord.ext import commands
from discord import app_commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from datetime import datetime
import asyncio

class SpotifyStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize Spotify client with client credentials flow (no user auth needed)
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
        ))

    @app_commands.command(name="artiststats", description="Look up Spotify stats for an artist")
    async def artist_stats(self, interaction: discord.Interaction, artist_name: str):
        await interaction.response.defer()
        
        try:
            # Search for the artist
            results = self.sp.search(q=artist_name, type='artist', limit=1)
            
            if not results['artists']['items']:
                await interaction.followup.send(f"Could not find artist: {artist_name}")
                return
                
            artist = results['artists']['items'][0]
            
            # Create embed
            embed = discord.Embed(
                title=f"🎵 {artist['name']} - Spotify Stats",
                description=f"Genre(s): {', '.join(artist['genres'][:3]) if artist['genres'] else 'No genres listed'}",
                color=discord.Color.green()
            )
            
            # Add artist image if available
            if artist['images']:
                embed.set_thumbnail(url=artist['images'][0]['url'])
            
            # Add popularity score
            embed.add_field(
                name="Popularity Score",
                value=f"{artist['popularity']}/100",
                inline=True
            )
            
            # Add follower count
            followers = artist['followers']['total']
            embed.add_field(
                name="Followers",
                value=f"{followers:,}",
                inline=True
            )
            
            # Get top tracks (with error handling)
            try:
                top_tracks = self.sp.artist_top_tracks(artist['id'])
                top_tracks_text = ""
                for idx, track in enumerate(top_tracks['tracks'][:5], 1):
                    popularity = track['popularity']
                    top_tracks_text += f"{idx}. {track['name']} ({popularity}/100)\n"
                
                if top_tracks_text:
                    embed.add_field(
                        name="Top Tracks",
                        value=top_tracks_text,
                        inline=False
                    )
            except Exception as e:
                embed.add_field(
                    name="Top Tracks",
                    value="Could not fetch top tracks",
                    inline=False
                )
            
            # Get related artists (with error handling)
            try:
                related = self.sp.artist_related_artists(artist['id'])
                if related and related['artists']:
                    related_text = ", ".join(artist['name'] for artist in related['artists'][:5])
                    embed.add_field(
                        name="Similar Artists",
                        value=related_text,
                        inline=False
                    )
            except Exception as e:
                embed.add_field(
                    name="Similar Artists",
                    value="Could not fetch related artists",
                    inline=False
                )
            
            # Add Spotify link
            embed.add_field(
                name="Spotify Link",
                value=f"[Open in Spotify]({artist['external_urls']['spotify']})",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Error fetching artist stats: {str(e)}")

async def setup(bot):
    await bot.add_cog(SpotifyStats(bot)) 