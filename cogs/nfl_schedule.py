import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from datetime import datetime, timezone, timedelta
from pytz import timezone

class NFLSchedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "http://site.api.espn.com/apis/site/v2/sports/football/nfl"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.team_emojis = {
            "ARI": "🌵", "ATL": "🦅", "BAL": "🦅", "BUF": "🐃",
            "CAR": "🐆", "CHI": "🐻", "CIN": "🐯", "CLE": "🐕",
            "DAL": "🤠", "DEN": "🐎", "DET": "🦁", "GB": "🧀",
            "HOU": "🐂", "IND": "🐎", "JAX": "🐆", "KC": "🏹",
            "LV": "☠️", "LAC": "⚡", "LAR": "🐏", "MIA": "🐬",
            "MIN": "🛡️", "NE": "🎭", "NO": "⚜️", "NYG": "🗽",
            "NYJ": "✈️", "PHI": "🦅", "PIT": "⚔️", "SF": "⛏️",
            "SEA": "🦅", "TB": "🏴‍☠️", "TEN": "🗡️", "WSH": "��"
        }
        self.team_mapping = {
            "cardinals": "ARI", "falcons": "ATL", "ravens": "BAL", "bills": "BUF",
            "panthers": "CAR", "bears": "CHI", "bengals": "CIN", "browns": "CLE",
            "cowboys": "DAL", "broncos": "DEN", "lions": "DET", "packers": "GB",
            "texans": "HOU", "colts": "IND", "jaguars": "JAX", "chiefs": "KC",
            "raiders": "LV", "chargers": "LAC", "rams": "LAR", "dolphins": "MIA",
            "vikings": "MIN", "patriots": "NE", "saints": "NO", "giants": "NYG",
            "jets": "NYJ", "eagles": "PHI", "steelers": "PIT", "niners": "SF",
            "seahawks": "SEA", "buccaneers": "TB", "titans": "TEN", "commanders": "WSH"
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
        et = timezone('US/Eastern')
        pt = timezone('US/Pacific')
        
        et_time = game_date.astimezone(et)
        pt_time = game_date.astimezone(pt)
        
        return (
            f"🕐 ET: {et_time.strftime('%I:%M %p')}\n"
            f"🕐 PT: {pt_time.strftime('%I:%M %p')}\n"
            f"📅 {game_date.strftime('%Y-%m-%d')}"
        )

    def get_team_display(self, team_abbr):
        return f"{self.team_emojis.get(team_abbr, '🏈')} {team_abbr}"

    @app_commands.command(name="nfl", description="Get NFL schedule for a specific date (MM/DD/YYYY)")
    async def nfl(self, interaction: discord.Interaction, date: str = None):
        if date is None:
            # Use current date when no parameter is provided
            current_date = datetime.now(timezone('US/Eastern'))
            date = current_date.strftime("%m/%d/%Y")

        await interaction.response.defer()

        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                url = f"{self.base_url}/scoreboard?dates={date}"
                async with session.get(url) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("Failed to fetch NFL schedule. Please try again later.")
                        return
                    
                    data = await resp.json()
                    events = data.get("events", [])

                    if not events:
                        await interaction.followup.send("No games found for this week.")
                        return

                    embed = discord.Embed(
                        title="🏈 NFL Games This Week",
                        color=discord.Color.green()
                    )

                    upcoming_games = []
                    for event in events:
                        try:
                            game_date = datetime.strptime(event["date"], "%Y-%m-%dT%H:%M%z")
                            upcoming_games.append((game_date, event))
                        except (ValueError, KeyError):
                            continue

                    upcoming_games.sort(key=lambda x: x[0])

                    if not upcoming_games:
                        await interaction.followup.send("No games scheduled for this week.")
                        return

                    # Group games by date
                    current_date = None
                    games_text = ""
                    week_detail = upcoming_games[0][1].get("week", {}).get("text", "")
                    
                    for game_date, event in upcoming_games:
                        date_str = game_date.strftime('%Y-%m-%d')
                        
                        if date_str != current_date:
                            # Add previous date's games if exists
                            if games_text:
                                embed.add_field(
                                    name=f"📅 {current_date_display}",
                                    value=games_text,
                                    inline=False
                                )
                                games_text = ""
                            
                            current_date = date_str
                            current_date_display = game_date.strftime('%A, %B %d')
                            games_text = ""

                        competition = event["competitions"][0]
                        home_team = competition["competitors"][0]["team"]["abbreviation"]
                        away_team = competition["competitors"][1]["team"]["abbreviation"]
                        
                        broadcasts = competition.get("broadcasts", [])
                        broadcast_info = "TBD"
                        if broadcasts:
                            broadcast_names = [b.get("names", [""])[0] for b in broadcasts]
                            broadcast_info = ", ".join(filter(None, broadcast_names))

                        game_text = (
                            f"{self.get_team_display(away_team)} @ {self.get_team_display(home_team)}\n"
                            f"🕐 {game_date.strftime('%I:%M %p')} ET\n"
                            f"📺 {broadcast_info}\n"
                            "───────────────\n"
                        )
                        games_text += game_text

                    # Add the last day's games
                    if games_text:
                        embed.add_field(
                            name=f"📅 {current_date_display}",
                            value=games_text,
                            inline=False
                        )

                    season_type = data.get("season", {}).get("type", {}).get("name", "")
                    if season_type:
                        footer_text = f"Season: {season_type}"
                        if week_detail:
                            footer_text = f"{week_detail} | {footer_text}"
                        embed.set_footer(text=footer_text)

                    await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

    async def get_team_schedule(self, interaction: discord.Interaction, team: str):
        team = team.lower()
        if team not in self.team_mapping:
            await interaction.followup.send("Invalid team name. Please use a valid NFL team name.")
            return

        team_abbr = self.team_mapping[team]

        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(f"{self.base_url}/teams/{team_abbr}/schedule") as resp:
                    if resp.status != 200:
                        await interaction.followup.send("Failed to fetch NFL schedule. Please try again later.")
                        return
                    
                    data = await resp.json()
                    events = data.get("events", [])

                    if not events:
                        await interaction.followup.send("No upcoming games found for this team.")
                        return

                    embed = discord.Embed(
                        title=f"🏈 Schedule for {team.title()}",
                        color=discord.Color.green()
                    )

                    upcoming_games = []

                    for event in events:
                        try:
                            game_date = datetime.strptime(event["date"], "%Y-%m-%dT%H:%M%z")
                            if game_date > datetime.now(timezone.utc):
                                upcoming_games.append((game_date, event))
                        except (ValueError, KeyError):
                            continue

                    upcoming_games.sort(key=lambda x: x[0])
                    upcoming_games = upcoming_games[:10]

                    if not upcoming_games:
                        await interaction.followup.send("No upcoming games found for this team.")
                        return

                    for game_date, event in upcoming_games:
                        competition = event["competitions"][0]
                        home_team = competition["competitors"][0]["team"]["abbreviation"]
                        away_team = competition["competitors"][1]["team"]["abbreviation"]
                        week_detail = event.get("week", {}).get("text", "")
                        
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
                            name=f"{week_detail}",
                            value=game_info,
                            inline=False
                        )

                    season_type = data.get("season", {}).get("type", {}).get("name", "")
                    if season_type:
                        embed.set_footer(text=f"Season: {season_type}")

                    await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(NFLSchedule(bot)) 