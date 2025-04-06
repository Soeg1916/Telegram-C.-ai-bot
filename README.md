# Character Personality Telegram Bot

A Telegram bot with AI-powered fictional character personalities using Mistral AI. Chat with characters from popular fiction or create your own custom personalities!

## Features

- 5 preset characters with unique personalities:
  - Sherlock Holmes - The brilliant detective with exceptional deduction skills
  - Tyrion Lannister - The witty and clever nobleman from Game of Thrones
  - Naruto Uzumaki - The hyperactive, optimistic ninja who dreams of becoming Hokage
  - Totoro - The gentle forest spirit from "My Neighbor Totoro"
  - Wednesday Addams - The morbid, deadpan teenage girl from the Addams Family

- Create your own custom characters with personalized traits
- Characters remember conversation history (up to 30 messages)
- Character moods change based on interactions
- Character stats and personality tracking
- Simple and intuitive Telegram interface with buttons
- Advanced emotional expression with formatting
- Share custom characters with the community (with admin approval)
- Web interface for browsing available characters

## Commands

- `/start` - Start the bot and select a character
- `/help` - Display bot usage instructions
- `/characters` - List all available characters
- `/character` - Show your currently selected character
- `/create` - Create a custom character
- `/delete` - Delete a custom character
- `/reset` - Reset conversation with current character
- `/stats` - Show current character mood and personality stats
- `/togglensfw` - Toggle NSFW mode for the current character
- `/sharerequest` - Request to share your custom character with the community
if you wanna try the bot - https://t.me/Character0_a1_bot
## Setup & Deployment

### Prerequisites

- Python 3.11 or higher
- A Telegram Bot Token (from [BotFather](https://t.me/botfather))
- A Mistral AI API Key
- PostgreSQL database

### Local Development

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: 
   - Windows: `venv\Scripts\activate`
   - Linux/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and add your API keys and database URL
6. Run the bot: `python main.py`

### Deployment on Koyeb

1. Fork this repository to your GitHub account
2. Create a new Koyeb app from your GitHub repository
3. Set the following environment variables in Koyeb:
   - `TELEGRAM_TOKEN`: Your Telegram bot token
   - `MISTRAL_API_KEY`: Your Mistral AI API key
   - `DATABASE_URL`: PostgreSQL database URL (Koyeb can provision one for you)
   - `SESSION_SECRET`: Random string for securing sessions
4. Deploy the app with the following settings:
   - Service Name: character-bot
   - Region: Choose the one closest to your users
   - Instance Type: Nano or Micro
   - Set up two services:
     1. Web Service: 
        - Build command: None
        - Start command: `gunicorn --bind 0.0.0.0:$PORT --reuse-port wsgi:application`
        - Port: 5000
     2. Worker Service:
        - Build command: None
        - Start command: `python main.py`
        - Port: N/A (Background worker)
5. Once deployed, your bot will be active on Telegram and the web interface will be available at your Koyeb app URL
