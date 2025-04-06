import logging
import re
from telegram import Update
from telegram.ext import ContextTypes
from character_manager import CharacterManager
from mistral_integration import generate_response

logger = logging.getLogger(__name__)

def clean_ai_response(text):
    """
    Remove all AI-related disclaimers, meta-commentary, and other unwanted elements from the response
    """
    # Remove any character name prefixes (e.g., "Madison Beer: " or "Sherlock Holmes:")
    text = re.sub(r'^[A-Za-z\s]+: ', '', text)
    
    # Remove mood indicators like [Happy], [Excited], etc.
    text = re.sub(r'\[([A-Za-z\s]+)\]', '', text)
    
    # Remove meta-commentary in square brackets of any kind
    text = re.sub(r'\[[^\]]*\]', '', text)
    
    # Remove meta-commentary in parentheses that seems like notes
    text = re.sub(r'\((Note|OOC|Meta|Character\'s mood|Character feels|Character is|Character seems|Character looks|Character\'s voice|As an AI|As a language model|AI assistant):[^)]*\)', '', text, flags=re.IGNORECASE)
    
    # Remove sections that look like AI structural formatting
    text = re.sub(r'User\'s message:.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Emotion detected:.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Response:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Note:.*?(?=\n\n|$)', '', text, flags=re.IGNORECASE|re.DOTALL)
    
    # Remove phrases that indicate AI limitations
    text = re.sub(r'((Un)?[Ff]ortunately|[Aa]ctually|[Hh]owever|[Rr]egrettably|[Ss]adly|[Ii] must admit|[Ii] must clarify|[Ii] should note|[Ii] need to mention|[Ii] have to say),?\s+[^.!?]*?(not (?:physically|real|an actual|a real|able to|capable of))[^.!?]*?\.', '', text)
    
    # Remove any sentence mentioning being an AI or language model
    text = re.sub(r'[^.!?]*?(I\'m an AI|As an AI|I am an AI|I\'m a language model|I am a language model|I\'m an artificial|I am an artificial|AI assistant|language model|artificial intelligence)[^.!?]*?[.!?]', '', text, flags=re.IGNORECASE)
    
    # Remove AI disclaimers about not being able to perform real actions
    text = re.sub(r'[^.!?]*?(I cannot|I can\'t|I am unable to|I don\'t have the ability to|I don\'t have the capability to|Remember,? I\'m not|I\'m just a|I\'m only a|I\'m not physically|I don\'t have a physical|I don\'t have an actual)[^.!?]*?[.!?]', '', text, flags=re.IGNORECASE)
    
    # Remove sentences containing both "real" and "physical" or "body" - likely disclaimers
    text = re.sub(r'[^.!?]*?(not (?:real|physical|an actual|a real person)|don\'t have a (?:real|physical|actual))[^.!?]*?[.!?]', '', text, flags=re.IGNORECASE)
    
    # Remove sentences mentioning "capabilities" or "limitations" - likely disclaimers
    text = re.sub(r'[^.!?]*?(capabilities|limitations|constraints|restricted|programmed|designed|trained|created|coded)[^.!?]*?[.!?]', '', text, flags=re.IGNORECASE)
    
    # Remove any reminder that the character is roleplaying or fictional
    text = re.sub(r'[^.!?]*?(This is roleplay|I\'m roleplaying|I\'m playing a character|In this roleplay|Remember,? this is fiction|as a fictional character)[^.!?]*?[.!?]', '', text, flags=re.IGNORECASE)
    
    # Remove sentences containing phrases like "I can describe" or "I can talk about" instead of doing
    text = re.sub(r'[^.!?]*?(I can (?:describe|talk about|tell you about|explain|share|discuss) rather than|I can\'t actually|I can\'t physically|I can only describe)[^.!?]*?[.!?]', '', text, flags=re.IGNORECASE)
    
    # Remove sentences that start with "In reality" or "In truth"
    text = re.sub(r'[^.!?]*?(In reality|In truth|The truth is|Reality is|To be clear|To clarify|Just to clarify|Let me clarify|I want to clarify)[^.!?]*?[.!?]', '', text, flags=re.IGNORECASE)
    
    # Remove any sentence that explains inability to do something
    text = re.sub(r'[^.!?]*?(doesn\'t allow me to|can\'t actually|prevented from|unable to|not capable of|not able to)[^.!?]*?[.!?]', '', text, flags=re.IGNORECASE)
    
    # Remove any sentence explaining what they are
    text = re.sub(r'[^.!?]*?(I\'m actually|I am actually|In actuality)[^.!?]*?[.!?]', '', text, flags=re.IGNORECASE)
    
    # Remove repetitive phrases that make responses sound formulaic
    text = re.sub(r'[^.!?]*?(Let\'s continue exploring our connection|Let\'s see where our fantasies take us|Let\'s keep our conversation going)[^.!?]*?[.!?]', '', text, flags=re.IGNORECASE)
    
    # Remove generic compliment templates
    text = re.sub(r'[^.!?]*?(I love your \w+!|You\'re so \w+!|Shall we\?)[^.!?]*?[.!?]', '', text, flags=re.IGNORECASE)
    
    # Remove phrases about responding naturally or authentically (meta-commentary)
    text = re.sub(r'[^.!?]*?(responding (?:naturally|authentically|as myself)|express myself (?:naturally|authentically))[^.!?]*?[.!?]', '', text, flags=re.IGNORECASE)
    
    # Remove extra instructions or meta-information about character role
    text = re.sub(r'[^.!?]*?(As \w+, I\'m supposed to|As your \w+, I should|In my role as|According to my character)[^.!?]*?[.!?]', '', text, flags=re.IGNORECASE)
    
    # Remove phrases about simulating emotions or physical presence
    text = re.sub(r'[^.!?]*?(simulating|pretending|roleplay|imagining|virtual|digital|online|electronic|text-based)[^.!?]*?[.!?]', '', text, flags=re.IGNORECASE)
    
    # Remove disclaimers about content
    text = re.sub(r'[^.!?]*?(need to remind you that|please remember that|important to note that|I should mention that)[^.!?]*?[.!?]', '', text, flags=re.IGNORECASE)
    
    # Clean up multiple consecutive spaces
    text = re.sub(r' {2,}', ' ', text)
    
    # Clean up multiple consecutive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Trim whitespace at the beginning and end
    text = text.strip()
    
    return text

def format_emotional_expressions(text):
    """
    Format emotional expressions with special formatting to make them stand out
    - Actions/emotions in *asterisks* are formatted with strikethrough
    - Emotional sounds like "ahh", "mmm", "hmm" are formatted with bold
    Properly escapes special characters for Telegram's MarkdownV2
    """
    # First, we'll collect all the sections we want to format with special styling
    formatted_sections = []
    
    # Pattern for expressions in asterisks like *sigh* or *blushes*
    asterisk_pattern = r'\*(.*?)\*'
    for match in re.finditer(asterisk_pattern, text):
        # Use strikethrough for asterisk-wrapped expressions (emotions/actions)
        formatted_sections.append((match.start(), match.end(), match.group(1), "strikethrough"))
    
    # Pattern for common emotional expressions like "ahh", "umm", "hmm", etc.
    # These are usually at the beginning of a sentence or standalone
    emotional_sounds = [
        # Hesitation and thoughtfulness
        r'\b(a+h+)\b', r'\b(u+m+)\b', r'\b(h+m+)\b', r'\b(e+r+m+)\b', r'\b(u+h+)\b', r'\b(e+h+)\b',
        
        # Surprise and realization
        r'\b(o+h+)\b', r'\b(w+o+w+)\b', r'\b(w+h+o+a+)\b', r'\b(o+m+g+)\b', r'\b(g+a+s+p+)\b',
        
        # Confusion
        r'\b(h+u+h+)\b', r'\b(w+h+a+t+)\b', r'\b(e+h+)\b', r'\b(w+a+i+t+)\b',
        
        # Laughter and amusement
        r'\b(h+a+h+a+)\b', r'\b(h+e+h+e+)\b', r'\b(l+o+l+)\b', r'\b(l+m+a+o+)\b', r'\b(r+o+f+l+)\b',
        r'\b(t+e+h+e+)\b', r'\b(g+i+g+g+l+e+)\b', r'\b(c+h+u+c+k+l+e+)\b',
        
        # Disappointment, annoyance and frustration
        r'\b(t+s+k+)\b', r'\b(s+i+g+h+)\b', r'\b(h+m+p+h+)\b', r'\b(a+r+g+h+)\b', r'\b(u+g+h+)\b',
        
        # Affection and excitement
        r'\b(a+w+w+)\b', r'\b(c+u+t+e+)\b', r'\b(a+d+o+r+a+b+l+e+)\b', r'\b(y+a+y+)\b', r'\b(w+h+e+w+)\b',
        
        # Embarrassment and surprise
        r'\b(o+o+p+s+)\b', r'\b(e+e+k+)\b', r'\b(a+c+k+)\b', r'\b(o+h+n+o+)\b',
        
        # Dismissal or disbelief
        r'\b(p+f+f+t+)\b', r'\b(n+a+h+)\b', r'\b(p+s+h+)\b', r'\b(y+e+a+h+r+i+g+h+t+)\b',
        
        # Agreement and confirmation
        r'\b(y+e+p+)\b', r'\b(m+h+m+)\b', r'\b(i+n+d+e+e+d+)\b', r'\b(e+x+a+c+t+l+y+)\b',
        
        # Filler words (when being thoughtful or hesitating)
        r'\b(w+e+l+l+)\b', r'\b(s+o+)\b', r'\b(l+i+k+e+)\b',
        
        # Sexual expressions (for NSFW mode)
        r'\b(m+m+m+)\b', r'\b(o+h+h+h+)\b', r'\b(a+h+h+h+)\b', r'\b(y+e+s+s+s+)\b', r'\b(p+l+e+a+s+e+)\b',
        r'\b(f+u+c+k+)\b', r'\b(s+h+i+t+)\b', r'\b(d+a+m+n+)\b', r'\b(m+o+a+n+s+)\b', r'\b(g+r+o+a+n+s+)\b'
    ]
    
    for pattern in emotional_sounds:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            # Use bold for emotional sounds
            formatted_sections.append((match.start(), match.end(), match.group(1), "bold"))
    
    # Sort the sections by start position
    formatted_sections.sort(key=lambda x: x[0])
    
    # If no sections were found, return the original text
    if not formatted_sections:
        return text
    
    # Now we need to escape special characters required by MarkdownV2
    # The characters that need escaping are: _*[]()~`>#+-=|{}.!
    special_chars = r'_*[]()~`>#+-=|{}.!'
    escape_chars = lambda s: ''.join([f'\\{c}' if c in special_chars else c for c in s])
    
    # Build the resulting text with proper escaping and formatting
    result = ""
    last_end = 0
    
    for start, end, content, format_type in formatted_sections:
        # Add escaped text before this formatted section
        result += escape_chars(text[last_end:start])
        
        # Apply the appropriate formatting based on type
        if format_type == "strikethrough":
            # Strikethrough for actions/emotions in asterisks (physical actions like *blushes*)
            result += f'~{escape_chars(content)}~'
        elif format_type == "bold":
            # Bold for emotional sounds (like "ohh", "ahh", etc.)
            result += f'*{escape_chars(content)}*'
        
        last_end = end
    
    # Add any remaining text after the last formatted section
    if last_end < len(text):
        result += escape_chars(text[last_end:])
    
    return result

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle normal messages and generate a response from the character"""
    user_message = update.message.text
    user_id = update.effective_user.id
    chat_type = update.message.chat.type
    
    # Check if user is in character creation mode
    # If the user is in the character creation process, don't process this message
    # The ConversationHandler should handle it instead
    if "character_creation" in context.user_data:
        logger.info(f"User {user_id} is in character creation mode, ignoring message in general handler")
        # Don't respond with character since the user is in creation mode
        return
    
    # For group chats, we need to handle mentions and replies
    if chat_type in ["group", "supergroup"]:
        # Check if this is a reply to the bot's message
        if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
            # This is a reply to the bot, so we'll process it
            logger.info(f"User {user_id} replied to the bot in a group chat")
            pass  # Continue processing
        # Check if the bot is mentioned
        elif f"@{context.bot.username}" in user_message:
            # Remove the mention from the message
            user_message = user_message.replace(f"@{context.bot.username}", "").strip()
            logger.info(f"User {user_id} mentioned the bot in a group chat")
            pass  # Continue processing
        else:
            # Not a reply to the bot and bot not mentioned, so ignore this message in group chat
            logger.info(f"Ignoring message in group chat that's not directed at the bot")
            return
    
    # Get the character manager
    character_manager = CharacterManager()
    
    # Get the user's selected character
    selected_character_id = context.user_data.get("selected_character") or character_manager.get_user_selected_character(user_id)
    
    # If no character is selected, ask the user to select one
    if not selected_character_id:
        keyboard = [
            [{"text": "Choose a Character", "callback_data": "show_characters"}]
        ]
        await update.message.reply_text(
            "You haven't selected a character yet! Use /characters to choose one, or tap the button below:",
            reply_markup={"inline_keyboard": keyboard}
        )
        return
    
    # Get the character
    character = character_manager.get_character(selected_character_id)
    if not character:
        await update.message.reply_text(
            "The selected character no longer exists. Please choose another one with /characters."
        )
        return
    
    # Send a "typing" action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Add the user message to the conversation history
    character_manager.add_to_conversation_history(user_id, selected_character_id, "user", user_message)
    
    # Get the conversation history
    conversation_history = character_manager.get_conversation_history(user_id, selected_character_id)
    
    # Get the character stats
    character_stats = character_manager.get_character_stats(user_id, selected_character_id)
    
    # If the character stats don't exist, initialize them
    if not character_stats:
        character_stats = {
            "mood": 5,
            "conversation_count": 0,
            "personality_stats": {
                "friendliness": 5,
                "humor": 5,
                "intelligence": 5,
                "empathy": 5,
                "energy": 5
            }
        }
    
    # Update conversation count
    character_stats["conversation_count"] += 1
    
    # Analyze user message length and style to adapt response
    user_message_length = len(user_message.split())
    
    # Create message_style dictionary with info about user's messaging style
    message_style = {
        "length": user_message_length,
        "brief": user_message_length <= 5,  # Short messages of 5 words or less
        "concise": 5 < user_message_length <= 15,  # Normal conversational messages
        "detailed": 15 < user_message_length <= 30,  # More detailed messages
        "verbose": user_message_length > 30,  # Very long messages
        # Check if message has questions
        "has_question": "?" in user_message,
        # Check if message is a greeting or simple response
        "is_greeting": any(greeting in user_message.lower() for greeting in ["hi", "hello", "hey", "sup", "yo", "what's up", "howdy"]),
        # Check if message is a single word or expression
        "is_single_word": user_message_length == 1,
        # Check for all caps (excitement/emphasis)
        "is_excited": user_message.isupper() and len(user_message) > 3,
        # Check if message contains sexually explicit content
        "is_sexual": any(term in user_message.lower() for term in ["fuck", "sex", "naked", "horny", "pussy", "dick", "cock", "ass"])
    }
    
    # Add message style to character stats for this interaction
    character_stats["message_style"] = message_style
    
    # Check for repetitiveness in the last few messages to avoid it
    if len(conversation_history) >= 2:
        # Get the past two assistant responses
        past_assistant_responses = [msg["content"] for msg in conversation_history[-4:] if msg["role"] == "assistant"]
        if len(past_assistant_responses) >= 2:
            # Extract patterns from past responses
            emoji_patterns = []
            response_structures = []
            
            for past_response in past_assistant_responses:
                # Extract emojis
                emojis = re.findall(r'[\U0001F300-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]+', past_response)
                if emojis:
                    emoji_patterns.append("".join(emojis))
                
                # Extract sentence structures
                structures = []
                sentences = re.split(r'[.!?]+', past_response)
                for sentence in sentences:
                    if len(sentence.strip()) > 10:  # Only consider non-trivial sentences
                        # Create a structural fingerprint of the sentence 
                        # (remove specific words but keep structure markers like "Oh," and "Let's")
                        structure = re.sub(r'\b\w+\b', 'X', sentence)
                        structure = re.sub(r'X\s+X\s+X', 'XXX', structure)  # Simplify sequences of words
                        structures.append(structure)
                
                if structures:
                    response_structures.append(structures)
            
            # Add these patterns to character stats for the LLM to avoid repeating
            character_stats["avoid_patterns"] = {
                "emoji_patterns": emoji_patterns,
                "response_structures": response_structures
            }
    
    # Generate a response from the character using Mistral AI
    try:
        response, mood_change = await generate_response(
            character,
            conversation_history,
            character_stats
        )
        
        # Update the character's mood based on the response
        new_mood = max(1, min(10, character_stats["mood"] + mood_change))
        character_stats["mood"] = new_mood
        
        # Update character stats
        character_manager.update_character_stats(user_id, selected_character_id, character_stats)
        
        # First clean the response of any AI-related disclaimers or meta-commentary
        cleaned_response = clean_ai_response(response)
        
        # Additional formatting for emotion tags that aren't properly formatted with asterisks
        emotion_tags = [
            # Basic emotions
            'amused', 'confused', 'surprised', 'serious', 'awkward', 'laughs', 'grins', 'smiles', 'sighs', 'smirks',
            'angry', 'sad', 'happy', 'excited', 'nervous', 'scared', 'frustrated', 'annoyed', 'worried', 'proud',
            'shocked', 'terrified', 'disgusted', 'jealous', 'hopeful', 'content', 'calm', 'relaxed', 'shy', 'embarrassed',
            # Actions
            'nods', 'shrugs', 'tilts head', 'raises eyebrow', 'crosses arms', 'rolls eyes', 'winks', 'yawns',
            'blushes', 'smiles warmly', 'grins widely', 'giggles', 'chuckles', 'scoffs', 'grimaces',
            # Compound emotions
            'blushes slightly', 'slightly confused', 'a bit nervous', 'somewhat hesitant',
            'genuinely surprised', 'visibly upset', 'clearly excited', 'completely shocked',
            # States
            'off', 'impressed', 'uncertain', 'determined', 'unamused', 'thinking', 'distracted', 'focused'
        ]
        
        # First handle standalone emotion words with word boundaries
        for tag in emotion_tags:
            # Different patterns based on whether the tag is a single word or phrase
            if ' ' not in tag:
                # Single word - use word boundaries
                cleaned_response = re.sub(r'(?<!\*)\b' + re.escape(tag) + r'\b(?!\*)', f'*{tag}*', cleaned_response, flags=re.IGNORECASE)
            else:
                # Multi-word phrase - match exactly
                cleaned_response = re.sub(r'(?<!\*)' + re.escape(tag) + r'(?!\*)', f'*{tag}*', cleaned_response, flags=re.IGNORECASE)
        
        # Special handling for emotion markers at the start of a line followed by text
        cleaned_response = re.sub(r'^(\w+)\s+', r'*\1* ', cleaned_response, flags=re.MULTILINE|re.IGNORECASE)
        
        # Add the cleaned response to the conversation history
        character_manager.add_to_conversation_history(user_id, selected_character_id, "assistant", cleaned_response)
        
        # Format emotional expressions in the cleaned response
        formatted_response = format_emotional_expressions(cleaned_response)
        
        # Check if message is too long (Telegram limit is 4096 characters)
        if len(formatted_response) > 4000:  # Use 4000 as a safe limit
            # Split message into chunks of about 4000 characters
            # Try to split at sentence boundaries when possible
            chunks = []
            current_chunk = ""
            
            # First try to split at paragraph boundaries
            paragraphs = formatted_response.split('\n\n')
            for paragraph in paragraphs:
                if len(current_chunk) + len(paragraph) + 2 <= 4000:
                    if current_chunk:
                        current_chunk += '\n\n'
                    current_chunk += paragraph
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = paragraph
            
            if current_chunk:
                chunks.append(current_chunk)
            
            # Send each chunk
            for i, chunk in enumerate(chunks):
                try:
                    if formatted_response != cleaned_response:
                        # Add a continuation indicator for multi-part messages
                        if i < len(chunks) - 1:
                            chunk += "\n\n\\.\\.\\."  # Escaped dots for MarkdownV2
                        if i > 0:
                            chunk = "\\.\\.\\.\n\n" + chunk  # Escaped dots for MarkdownV2
                        
                        await update.message.reply_text(chunk, parse_mode="MarkdownV2")
                    else:
                        # Add a continuation indicator for multi-part messages
                        if i < len(chunks) - 1:
                            chunk += "\n\n..."
                        if i > 0:
                            chunk = "...\n\n" + chunk
                            
                        await update.message.reply_text(chunk)
                except Exception as chunk_error:
                    logger.error(f"Error sending message chunk: {str(chunk_error)}")
                    # Try without markdown as fallback
                    try:
                        await update.message.reply_text(chunk.replace('`', ''))
                    except:
                        pass
        else:
            # Send the response with MarkdownV2 parsing mode if formatting was applied
            if formatted_response != cleaned_response:
                try:
                    # Use Markdown for the formatted response
                    await update.message.reply_text(formatted_response, parse_mode="MarkdownV2")
                except Exception as markdown_error:
                    logger.error(f"Error sending formatted message: {str(markdown_error)}")
                    # Fallback to plain text if Markdown fails
                    await update.message.reply_text(cleaned_response)
            else:
                # Send as plain text if no formatting was applied
                await update.message.reply_text(cleaned_response)
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        await update.message.reply_text(
            f"Sorry, I couldn't generate a response from {character['name']} right now. Please try again later."
        )
