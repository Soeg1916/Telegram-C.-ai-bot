from flask import Flask, request, jsonify
import os
import sys
import json
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import bot setup
from bot import setup_bot

# This is necessary for Vercel serverless deployment
from app import app

# Get bot token from environment variable
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("No TELEGRAM_BOT_TOKEN found in environment variables!")

# Setup the bot application
bot_app = setup_bot(TOKEN)

@app.route('/api/webhook', methods=['POST'])
async def webhook():
    """Handle webhook requests from Telegram"""
    if request.method == "POST":
        try:
            # Get the update from Telegram
            update_data = request.get_json()
            logger.info(f"Received update: {update_data}")
            
            # Process the update
            update = Update.de_json(update_data, bot_app.bot)
            await bot_app.process_update(update)
            
            return jsonify({"status": "success"})
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({"status": "error", "message": "Method not allowed"}), 405

@app.route('/api/set_webhook', methods=['GET'])
def set_webhook():
    """Set the Telegram webhook to this URL"""
    webhook_url = request.args.get('url')
    
    if not webhook_url:
        return jsonify({"status": "error", "message": "No webhook URL provided"}), 400
    
    try:
        # Set the webhook
        import asyncio
        asyncio.run(bot_app.bot.set_webhook(url=webhook_url))
        
        return jsonify({
            "status": "success", 
            "message": f"Webhook set to {webhook_url}"
        })
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500