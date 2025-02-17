import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from datetime import datetime, timezone
import pytz

class NBASchedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "http://site.api.espn.com/apis/site/v2/sports/basketball/nba"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.team_emojis = {
            "ATL": "🦅", "BOS": "☘️", "BKN": "🌐", "CHA": "🐝",
            "CHI": "🐂", "CLE": "⚔️", "DAL": "🐎", "DEN": "🏔️",
            "DET": "🔧", "GSW": "🌉", "HOU": "🚀", "IND": "🏎️",
            "LAC": "⛵", "LAL": "💜", "MEM": "🐻", "MIA": "🔥",
            "MIL": "🦌", "MIN": "🐺", "NOP": "⚜️", "NYK": "🗽",
            "OKC": "⚡", "ORL": "🎩", "PHI": "🔔", "PHX": "☀️",
            "POR": "🌹", "SAC": "👑", "SAS": "🌟", "TOR": "🦖",
            "UTA": "🎷", "WAS": "��"
        }
        self.team_mapping = {
            "hawks": "ATL", "celtics": "BOS", "nets": "BKN", "hornets": "CHA",
            "bulls": "CHI", "cavaliers": "CLE", "mavericks": "DAL", "nuggets": "DEN",
            "pistons": "DET", "warriors": "GSW", "rockets": "HOU", "pacers": "IND",
            "clippers": "LAC", "lakers": "LAL", "grizzlies": "MEM", "heat": "MIA",
            "bucks": "MIL", "timberwolves": "MIN", "pelicans": "NOP", "knicks": "NYK",
            "thunder": "OKC", "magic": "ORL", "76ers": "PHI", "suns": "PHX",
            "blazers": "POR", "kings": "SAC", "spurs": "SAS", "raptors": "TOR",
            "jazz": "UTA", "wizards": "WAS"
        }

    async def team_autocomplete(self, 
        interaction: discord.Interaction, 
        current: str
    ) -> list[app_commands.Choice[str]]:
        current = current.lower()
        return [
            app_commands.Choice(name=team_name.title(), value=team_name)
            for team_name in self.team_mapping.keys()
            if current in team_name.lower()
        ][:25]

    def format_game_time(self, game_date):
        et = pytz.timezone('US/Eastern')
        pt = pytz.timezone('US/Pacific')
        
        et_time = game_date.astimezone(et)
        pt_time = game_date.astimezone(pt)
        
        return (
            f"🕐 ET: {et_time.strftime('%I:%M %p')}\n"
            f"🕐 PT: {pt_time.strftime('%I:%M %p')}\n"
            f"📅 {game_date.strftime('%Y-%m-%d')}"
        )

    def get_team_display(self, team_abbr):
        return f"{self.team_emojis.get(team_abbr, '🏀')} {team_abbr}"

    @app_commands.command(name="nba_schedule", description="Get the schedule for an NBA team")
    @app_commands.describe(team="The NBA team name (e.g., lakers, warriors, celtics)")
    @app_commands.autocomplete(team=team_autocomplete)
    async def nba_schedule(self, interaction: discord.Interaction, team: str):
        await interaction.response.defer()

        team = team.lower()
        if team not in self.team_mapping:
            await interaction.followup.send("Invalid team name. Please use a valid NBA team name.")
            return

        team_abbr = self.team_mapping[team]

        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(f"{self.base_url}/teams/{team_abbr}/schedule") as resp:
                    if resp.status != 200:
                        await interaction.followup.send("Failed to fetch NBA schedule. Please try again later.")
                        return
                    
                    data = await resp.json()
                    events = data.get("events", [])

                    if not events:
                        await interaction.followup.send("No upcoming games found for this team.")
                        return

                    embed = discord.Embed(
                        title=f"📅 Schedule for {team.title()}",
                        color=discord.Color.blue()
                    )

                    current_date = datetime.now(timezone.utc)
                    upcoming_games = []

                    for event in events:
                        try:
                            game_date = datetime.strptime(event["date"], "%Y-%m-%dT%H:%M%z")
                            if game_date > current_date:
                                upcoming_games.append((game_date, event))
                        except (ValueError, KeyError):
                            continue

                    # Sort by date and take first 10
                    upcoming_games.sort(key=lambda x: x[0])
                    upcoming_games = upcoming_games[:10]

                    if not upcoming_games:
                        await interaction.followup.send("No upcoming games found for this team.")
                        return

                    for game_date, event in upcoming_games:
                        competition = event["competitions"][0]
                        home_team = competition["competitors"][0]["team"]["abbreviation"]
                        away_team = competition["competitors"][1]["team"]["abbreviation"]
                        
                        broadcasts = competition.get("broadcasts", [])
                        broadcast_info = "TBD"
                        if broadcasts:
                            broadcast_names = [b.get("names", [""])[0] for b in broadcasts]
                            broadcast_info = ", ".join(filter(None, broadcast_names))

                        venue = competition.get("venue", {}).get("fullName", "TBD")
                        
                        game_info = (
                            f"{self.get_team_display(away_team)} @ {self.get_team_display(home_team)}\n"
                            f"{self.format_game_time(game_date)}\n"
                            f"📺 {broadcast_info}\n"
                            f"🏟️ {venue}"
                        )
                        
                        embed.add_field(
                            name=f"Game {len(embed.fields) + 1}",
                            value=game_info,
                            inline=False
                        )

                    await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(NBASchedule(bot)) 