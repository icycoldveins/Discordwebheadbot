import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv
load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")


class MusicRecommendation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))

    @commands.command()
    async def recommend(self, ctx, *, query):
        """
        Get music recommendations based on a song or artist.

        Arguments:
        - query (str): The song or artist you want recommendations for.

        Example usage:
        !recommend Queen
        """
        # Rest of your command logic here...

        # Search for the track or artist on Spotify
        # Start by looking for tracks
        results = self.sp.search(q=query, limit=1, type='track')

        if not results['tracks']['items']:
            await ctx.send("Couldn't find the song or artist.")
            return

        track_id = results['tracks']['items'][0]['id']
        # Get recommendations based on the track
        recommendations = self.sp.recommendations(
            seed_tracks=[track_id], limit=5)

        if not recommendations['tracks']:
            await ctx.send("Couldn't get recommendations for this song or artist.")
            return

        # Construct the message with song recommendations
        message = "Here are some recommendations:\n"
        for track in recommendations['tracks']:
            message += f"- {track['name']} by {track['artists'][0]['name']}\n"

        await ctx.send(message)

    @commands.command()
    async def playlist(self, ctx, *, username):
        """
        Show a user's Spotify playlists.

        Arguments:
        - username (str): The Spotify username.

        Example usage:
        !playlist spotify_user
        """
        # Rest of your command logic here...

        # Get the user's playlists
        playlists = self.sp.user_playlists(username)

        # Construct the message with the playlist names
        message = f"Here are {username}'s playlists:\n"
        for playlist in playlists['items']:
            message += f"- {playlist['name']}\n"

        await ctx.send(message)


async def setup(bot):
    await bot.add_cog(MusicRecommendation(bot))
