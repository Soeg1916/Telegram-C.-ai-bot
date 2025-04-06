from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from character_manager import CharacterManager

async def request_share_character(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Request to share a custom character with the community"""
    character_manager = CharacterManager()
    
    # Get the user's selected character
    user_id = update.effective_user.id
    selected_character_id = context.user_data.get("selected_character") or character_manager.get_user_selected_character(user_id)
    
    if not selected_character_id:
        await update.message.reply_text(
            "You don't have a character selected. Use /characters to select one."
        )
        return
    
    character = character_manager.get_character(selected_character_id)
    if not character:
        await update.message.reply_text(
            "Error: Selected character not found."
        )
        return
    
    # Check if this is a custom character created by the user
    if not selected_character_id.startswith("custom_") or character.get("creator_id") != user_id:
        await update.message.reply_text(
            "You can only share custom characters that you've created yourself."
        )
        return
    
    # Check if the character is already public or pending approval
    if character.get("is_public", False):
        await update.message.reply_text(
            f"{character['name']} is already shared with the community!"
        )
        return
    
    if character.get("pending_approval", False):
        await update.message.reply_text(
            f"{character['name']} is already pending approval for community sharing."
        )
        return
    
    # Request to make the character public
    success = character_manager.request_public_character(user_id, selected_character_id)
    
    if success:
        await update.message.reply_text(
            f"Your character {character['name']} has been submitted for approval to be shared with the community.\n\n"
            "An admin will review your character and approve or reject it soon."
        )
    else:
        await update.message.reply_text(
            "There was an error submitting your character for approval. Please try again later."
        )

async def admin_list_pending_characters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all characters pending approval (admin only)"""
    character_manager = CharacterManager()
    
    # Check if the user is an admin (admin ID: 1159603709)
    user_id = update.effective_user.id
    if user_id != 1159603709:  # Replace with your admin ID
        await update.message.reply_text(
            "This command is for administrators only."
        )
        return
    
    # Get all pending characters
    pending_characters = character_manager.get_pending_characters()
    
    if not pending_characters:
        await update.message.reply_text(
            "There are no characters pending approval at this time."
        )
        return
    
    # Create the message text
    message_text = "📝 *Characters Pending Approval* 📝\n\n"
    
    for char_id, char in pending_characters.items():
        creator_id = char.get("creator_id", "Unknown")
        nsfw_status = "🔞 NSFW" if char.get("nsfw", False) else "SFW"
        
        message_text += f"*{char['name']}* (ID: `{char_id}`)\n"
        message_text += f"Creator ID: `{creator_id}`\n"
        message_text += f"Type: {nsfw_status}\n"
        message_text += f"Description: {char['description'][:100]}...\n\n"
    
    # Add instructions
    message_text += "Use `/approve <character_id>` to approve a character or `/reject <character_id>` to reject it."
    
    await update.message.reply_text(
        message_text,
        parse_mode="Markdown"
    )

async def admin_approve_character(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Approve a character for public sharing (admin only)"""
    character_manager = CharacterManager()
    
    # Check if the user is an admin
    user_id = update.effective_user.id
    if user_id != 1159603709:  # Replace with your admin ID
        await update.message.reply_text(
            "This command is for administrators only."
        )
        return
    
    # Check if the character ID was provided
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "Please provide a character ID to approve. Use the format `/approve <character_id>`"
        )
        return
    
    character_id = context.args[0]
    
    # Approve the character
    success = character_manager.approve_public_character(user_id, character_id)
    
    if success:
        character = character_manager.get_character(character_id)
        await update.message.reply_text(
            f"✅ Character {character['name']} has been approved and is now available to all users!"
        )
    else:
        await update.message.reply_text(
            "❌ Failed to approve character. Please check if the ID is correct and the character is pending approval."
        )

async def admin_reject_character(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reject a character for public sharing (admin only)"""
    character_manager = CharacterManager()
    
    # Check if the user is an admin
    user_id = update.effective_user.id
    if user_id != 1159603709:  # Replace with your admin ID
        await update.message.reply_text(
            "This command is for administrators only."
        )
        return
    
    # Check if the character ID was provided
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "Please provide a character ID to reject. Use the format `/reject <character_id>`"
        )
        return
    
    character_id = context.args[0]
    
    # Reject the character
    success = character_manager.reject_public_character(user_id, character_id)
    
    if success:
        character = character_manager.get_character(character_id)
        await update.message.reply_text(
            f"❌ Character {character['name']} has been rejected and will not be shared with the community."
        )
    else:
        await update.message.reply_text(
            "Failed to reject character. Please check if the ID is correct and the character is pending approval."
        )

async def list_public_characters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all publicly available custom characters"""
    character_manager = CharacterManager()
    
    # Get all public characters
    public_characters = character_manager.get_public_characters()
    
    if not public_characters:
        await update.message.reply_text(
            "There are no public custom characters available yet. Be the first to share one with /share!"
        )
        return
    
    # Create the message text
    message_text = "🌍 *Community Shared Characters* 🌍\n\n"
    
    # Create inline keyboard for character selection
    keyboard = []
    
    for char_id, char in public_characters.items():
        nsfw_mode = char.get("nsfw", False)
        button_text = f"{char['name']} {'🔞' if nsfw_mode else ''}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_character:{char_id}")])
        
        # Add details to message text
        message_text += f"*{char['name']}*"
        message_text += f" 🔞" if nsfw_mode else ""
        message_text += f"\n{char['description'][:100]}...\n\n"
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )