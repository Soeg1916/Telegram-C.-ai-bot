import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
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

# Health check server class
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'OK - Bot is running')
    
    def log_message(self, format, *args):
        # Suppress log messages from health check requests
        return

def run_health_server():
    """Run a simple HTTP server for health checks"""
    try:
        server = HTTPServer(('0.0.0.0', 8000), HealthCheckHandler)
        logging.info("Health check server started on port 8000")
        server.serve_forever()
    except Exception as e:
        logging.error(f"Health check server error: {e}")

def main():
    """Main function to start the Telegram bot"""
    # Start health check server in a separate thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
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
