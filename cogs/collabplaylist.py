from discord.ext import commands
from spotipy import Spotify, oauth2
import os

class SpotifyPlaylist(commands.Cog):
    """Cog for interacting with a Spotify playlist."""

    def __init__(self, bot):
        self.bot = bot
        self.playlist_id = os.getenv("SPOTIFY_PLAYLIST_ID")
        self.spotify_client = self.setup_spotify_client()
        self.playlist_link = os.getenv("SPOTIFY_PLAYLIST_LINK")

    def setup_spotify_client(self):
        """Set up the Spotify client with OAuth."""
        spotify_oauth = oauth2.SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
            
            scope="playlist-modify-public playlist-modify-private"
        )
        return Spotify(auth_manager=spotify_oauth)

    @commands.command()
    async def addtoplaylist(self, ctx, *, song_name: str):
        """Add a song to a Spotify playlist."""
        try:
            results = self.spotify_client.search(q=song_name, limit=1, type='track')
            
            if not results['tracks']['items']:
                await ctx.send(f"No track found for '{song_name}'.")
                return

            track_uri = results['tracks']['items'][0]['uri']
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
async def setup(bot):
    await bot.add_cog(SpotifyPlaylist(bot))
