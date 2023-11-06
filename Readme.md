# WebHead Discord Bot

Welcome to the README for your Discord bot! This bot is built using Python and the discord.py library, offering a wide range of fun and useful commands, including dice rolling, trivia games, music recommendations, and more.

## Setup

To get started with this bot, follow these simple steps:

1. Clone this repository to your local machine.

2. Install the necessary dependencies by running the following command:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory and add your bot token and Spotify credentials in the following format:

   ```
   BOT_TOKEN=your_bot_token_here
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
   ```

4. Run `main.py` to start the bot.

## Commands

This bot supports the following commands:

- `!roll`: Rolls a six-sided die and returns the result.
- `!leetcode <username>`: Fetches and displays LeetCode stats for the specified user.
- `!conch <question>`: Asks the Magic Conch a question and returns a random answer.
- `!trivia [category]`: Starts a trivia game. Optionally, you can specify a category.
- `!recommend <query>`: Returns music recommendations based on a song or artist.
- `!playlist <username>`: Shows a user's Spotify playlists.

## Additional Information

For any issues or suggestions, please open an issue on this repository. We value your feedback and are here to help make your Discord bot experience even better!
