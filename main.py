import os
import logging
from bot import setup_bot
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Set up logging
# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Configure logging to console and file
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

def main():
    """Main function to start the Telegram bot"""
    # Get the telegram token from environment variable
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    
    if not telegram_token:
        logging.error("TELEGRAM_TOKEN environment variable not set!")
        return
    
    if not mistral_api_key:
        logging.error("MISTRAL_API_KEY environment variable not set!")
        return
    
    # Setup and start the bot
    bot = setup_bot(telegram_token)
    logging.info("Bot started!")
    
    # Run the bot until the user presses Ctrl-C
    bot.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
