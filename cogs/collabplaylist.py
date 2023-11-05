from discord.ext import commands
from spotipy import Spotify, SpotifyClientCredentials
import os


class SpotifyPlaylist(commands.Cog):
    """Cog for interacting with a Spotify playlist."""

    def __init__(self, bot):
        self.bot = bot
        self.playlist_id = os.getenv("SPOTIFY_PLAYLIST_ID")
        self.spotify_client = self.setup_spotify_client()
        self.playlist_link = os.getenv("SPOTIFY_PLAYLIST_LINK")

    def setup_spotify_client(self):
        """Set up the Spotify client with Client Credentials Flow."""
        client_credentials_manager = SpotifyClientCredentials(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
        )
        return Spotify(client_credentials_manager=client_credentials_manager)


@commands.command()
async def addtoplaylist(self, ctx, *, song_name: str):
    """Add a song to a Spotify playlist, ensuring no duplicates."""
    try:
        # Search for the song to get its URI
        results = self.spotify_client.search(
            q=song_name, limit=1, type='track')

        if not results['tracks']['items']:
            await ctx.send(f"No track found for '{song_name}'.")
            return

        track_uri = results['tracks']['items'][0]['uri']

        # Get the current tracks in the playlist
        current_tracks = self.spotify_client.playlist_tracks(self.playlist_id)

        # Check if the song is already in the playlist
        for item in current_tracks['items']:
            if track_uri == item['track']['uri']:
                await ctx.send(f"'{song_name}' is already in the playlist.")
                return

        # If the song is not in the playlist, add it
        self.spotify_client.playlist_add_items(self.playlist_id, [track_uri])
        await ctx.send(f"Added '{song_name}' to the playlist.")

    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error adding track to Spotify playlist: {e}")
        await ctx.send("An error occurred while adding the track to the playlist.")

    @commands.command()
    async def showplaylist(self, ctx):
        """Send the playlist link to the Discord chat."""
        await ctx.send(f"Here's the link to our Spotify playlist: {self.playlist_link}")

    @commands.command()
    async def deletefromplaylist(self, ctx, *, song_name: str):
        """Delete a song from a Spotify playlist."""
        try:
            # Search for the song to get its URI
            results = self.spotify_client.search(
                q=song_name, limit=1, type='track')

            if not results['tracks']['items']:
                await ctx.send(f"No track found for '{song_name}'.")
                return

            # Get the track URI
            track_uri = results['tracks']['items'][0]['uri']

            # Remove all occurrences of the specified tracks from the playlist
            self.spotify_client.playlist_remove_all_occurrences_of_items(
                self.playlist_id, [track_uri])
            await ctx.send(f"Deleted '{song_name}' from the playlist.")

        except Exception as e:
            # Log the error for debugging purposes
            print(f"Error deleting track from Spotify playlist: {e}")
            await ctx.send("An error occurred while deleting the track from the playlist.")


async def setup(bot):
    await bot.add_cog(SpotifyPlaylist(bot))
