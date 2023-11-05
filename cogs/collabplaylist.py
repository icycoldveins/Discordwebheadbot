from discord.ext import commands
from spotipy import Spotify, SpotifyClientCredentials
import os
from spotipy.oauth2 import SpotifyOAuth


def setup_spotify_client(self):
    """Set up the Spotify client with Authorization Code Flow."""
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope="playlist-modify-public playlist-modify-private"
    )
    return Spotify(auth_manager=auth_manager)


class SpotifyPlaylist(commands.Cog):
    """Cog for interacting with a Spotify playlist. You can use the following commands:
    - !addtoplaylist [song name]: Add a song to the playlist by providing the song name or a portion of its name.
    - !showplaylist: Provides a link to the Spotify playlist.
    - !deletefromplaylist [song name]: Remove a song from the playlist by providing the exact song name.
    """

    def __init__(self, bot):
        self.bot = bot
        self.playlist_id = os.getenv("SPOTIFY_PLAYLIST_ID")
        self.spotify_client = self.setup_spotify_client()
        self.playlist_link = os.getenv("SPOTIFY_PLAYLIST_LINK")

    def setup_spotify_client(self):
        """Set up the Spotify client with Authorization Code Flow."""
        auth_manager = SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
            scope="playlist-modify-public playlist-modify-private"
        )
        return Spotify(auth_manager=auth_manager)

    # Helper function to check if a track is in the playlist
    def is_track_in_playlist(self, track_uri):
        results = self.spotify_client.playlist_items(self.playlist_id)
        while results:
            track_uris = [item['track']['uri']
                          for item in results['items'] if item['track']]
            if track_uri in track_uris:
                return True
            if results['next']:
                results = self.spotify_client.next(results)
            else:
                break
        return False

    @commands.command()
    async def addtoplaylist(self, ctx, *, song_name: str):
        """
        Add a song to the Spotify playlist.

        Usage: !addtoplaylist <song name>
        Example: !addtoplaylist Never Gonna Give You Up
        This will search for the song on Spotify and add it to the playlist if it's not already present.
        """
        try:
            # Search for the song to get its URI
            results = self.spotify_client.search(
                q=song_name, limit=1, type='track')

            if not results['tracks']['items']:
                await ctx.send(f"No track found for '{song_name}'.")
                return

            track_uri = results['tracks']['items'][0]['uri']

            # Check if the track is already in the playlist
            if self.is_track_in_playlist(track_uri):
                await ctx.send(f"'{song_name}' is already in the playlist.")
                return

            # Add the track to the playlist if it's not a duplicate
            self.spotify_client.playlist_add_items(
                self.playlist_id, [track_uri])
            await ctx.send(f"Added '{song_name}' to the playlist.")

        except Exception as e:
            # Log the error for debugging purposes
            print(f"Error adding track to Spotify playlist: {e}")
            await ctx.send("An error occurred while adding the track to the playlist.")

    @commands.command()
    async def showplaylist(self, ctx):
        """
        Send the playlist link to the Discord chat.

        Usage: !showplaylist
        This command will provide you with the link to the Spotify playlist.
        """
        await ctx.send(f"Here's the link to our Spotify playlist: {self.playlist_link}")

    @commands.command()
    async def deletefromplaylist(self, ctx, *, song_name: str):
        """
        Delete a song from the Spotify playlist.

        Usage: !deletefromplaylist <song name>
        Example: !deletefromplaylist Never Gonna Give You Up
        If the song is in the playlist, it will be removed.
        """
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
