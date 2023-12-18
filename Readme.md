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
   SPOTIFY_CLIENT_ID=your_spotify_client_id_here
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
- `!participation`: Increments the participation count for the user who executed the command and sends a message displaying the updated count. If the user has not participated before, a new entry is created with a count of 1.

## MongoDB Integration

The `!participation` command utilizes MongoDB to store and retrieve participation counts for users. The `ParticipationCounter` class in the `cogs/participation.py` file establishes a connection to the MongoDB database using the `pymongo` library. The participation count for each user is stored in the `users` collection. When a user executes the `!participation` command, the count is incremented and updated in the database. If the user has not participated before, a new entry is created with a count of 1.

## Additional Information

For any issues or suggestions, please open an issue on this repository. We value your feedback and are here to help make your Discord bot experience even better!
