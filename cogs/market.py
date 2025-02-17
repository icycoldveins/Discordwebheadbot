import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from datetime import datetime
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')

class Market(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://www.alphavantage.co/query"
        self.popular_symbols = {
            "stocks": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "AMD"],
            "crypto": ["BTC", "ETH", "BNB", "XRP", "DOGE"],
            "forex": ["EUR", "GBP", "JPY", "CAD", "AUD"]
        }

    async def symbol_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        all_symbols = sum([symbols for symbols in self.popular_symbols.values()], [])
        return [
            app_commands.Choice(name=symbol, value=symbol)
            for symbol in all_symbols if current.upper() in symbol.upper()
        ][:25]

    @app_commands.command(name="market", description="Get market data for a symbol")
    @app_commands.describe(symbol="Stock/Crypto/Forex symbol (e.g., AAPL, BTC, EUR)")
    @app_commands.autocomplete(symbol=symbol_autocomplete)
    async def market(self, interaction: discord.Interaction, symbol: str):
        await interaction.response.defer()

        try:
            # Determine the function based on symbol type
            function = "TIME_SERIES_INTRADAY"
            if symbol in self.popular_symbols["crypto"]:
                function = "CRYPTO_INTRADAY"
                symbol = f"{symbol}USD"
            elif symbol in self.popular_symbols["forex"]:
                function = "FX_INTRADAY"
                symbol = f"{symbol}USD"

            params = {
                "function": function,
                "symbol": symbol,
                "interval": "5min",
                "apikey": ALPHA_VANTAGE_KEY
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("Failed to fetch market data. Please try again later.")
                        return
                    
                    data = await resp.json()
                    
                    if "Error Message" in data:
                        await interaction.followup.send("No data available for this symbol.")
                        return

                    # Get the time series data
                    time_series_key = [key for key in data.keys() if "Time Series" in key][0]
                    time_series = data[time_series_key]
                    latest_data = list(time_series.items())[0][1]

                    # Extract prices
                    current_price = float(latest_data.get("4. close", 0))
                    high_price = float(latest_data.get("2. high", 0))
                    low_price = float(latest_data.get("3. low", 0))
                    open_price = float(latest_data.get("1. open", 0))

                    # Calculate change
                    change = current_price - open_price
                    change_percent = (change / open_price) * 100
                    emoji = "🟢" if change >= 0 else "🔴"

                    embed = discord.Embed(
                        title=f"📊 Market Data: {symbol.upper()}",
                        color=discord.Color.green() if change >= 0 else discord.Color.red(),
                        timestamp=datetime.now()
                    )

                    # Current price and change
                    price_info = (
                        f"💰 Current Price: ${current_price:,.2f}\n"
                        f"{emoji} Change: {change_percent:+.2f}%\n"
                        f"📈 Open: ${open_price:,.2f}"
                    )
                    embed.add_field(name="Price Information", value=price_info, inline=False)

                    # Trading range
                    range_info = (
                        f"⬆️ High: ${high_price:,.2f}\n"
                        f"⬇️ Low: ${low_price:,.2f}"
                    )
                    embed.add_field(name="Today's Range", value=range_info, inline=True)

                    embed.set_footer(text="Data provided by Alpha Vantage")
                    await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(Market(bot)) 