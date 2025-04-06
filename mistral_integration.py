import os
import json
import logging
import random
from typing import Dict, List, Tuple
import aiohttp
from emotional_guidance import get_emotional_guidance

logger = logging.getLogger(__name__)

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

async def generate_response(
    character: Dict, 
    conversation_history: List[Dict], 
    character_stats: Dict
) -> Tuple[str, float]:
    """
    Generate a response from the character using Mistral AI
    
    Args:
        character: The character data
        conversation_history: The conversation history
        character_stats: The character's mood and personality stats
    
    Returns:
        Tuple of (response text, mood change)
    """
    # Get the Mistral API key from environment variable
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable not set!")
    
    # Prepare the system prompt with character info and current stats
    system_prompt = _prepare_system_prompt(character, character_stats)
    
    # Prepare the messages for the Mistral API
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add the conversation history
    for message in conversation_history:
        messages.append({"role": message["role"], "content": message["content"]})
    
    # Check if NSFW mode is enabled for this character
    nsfw_mode = character.get("nsfw", False)
    
    # Prepare the request payload
    payload = {
        "model": "mistral-medium",  # Using Mistral Medium model
        "messages": messages,
        "temperature": 0.7,  # A moderate temperature for good creativity but consistent responses
        "max_tokens": 400,  # Limit response length for shorter replies
        "top_p": 0.9,
        "safe_prompt": not nsfw_mode  # Enable safety filters only if NSFW mode is disabled
    }
    
    # Make the API call
    async with aiohttp.ClientSession() as session:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        async with session.post(MISTRAL_API_URL, json=payload, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Mistral API error: {error_text}")
                raise Exception(f"Mistral API error: {response.status}")
            
            response_data = await response.json()
            
            # Extract the response text
            response_text = response_data["choices"][0]["message"]["content"]
            
            # Filter out AI disclaimers and meta-commentary
            import re
            disclaimer_patterns = [
                # Model disclaimers
                r'\(Note:.*?\)',
                r'\(At this point.*?\)',
                r'Please note that I am an AI.*?\.', 
                r'I am an AI.*?\.', 
                r'As an AI.*?\.', 
                r'I do not have.*?emotions.*?\.', 
                r'I cannot.*?feel.*?\.', 
                r'I\'m just a.*?model.*?\.',
                r'I don\'t have.*?feelings.*?\.',
                
                # Meta-commentary in parentheses - catch all possible patterns
                r'\([^)]*instructions?\)|\([^)]*per [^)]*instructions?\)', 
                r'\(My.*?remain.*?\)',
                r'\(Also,.*?\)',
                r'\(I [^)]*acknowledged.*?\)',
                r'\(I [^)]*respond.*?\)',
                r'\(I [^)]*express.*?\)',
                r'\(I [^)]*follow.*?\)',
                r'\([^)]*your character[^)]*\)',
                r'\([^)]*emotion.*?\)',
                r'\([^)]*relationship.*?\)',
                r'\([^)]*user[^)]*\)',
                r'\([^)]*model[^)]*\)',
                r'\([^)]*note[^)]*\)',
                r'\([^)]*As per[^)]*\)',
                r'\([^)]*In line with[^)]*\)',
                r'\([^)]*maintain[^)]*\)',
                r'\([^)]*keeping[^)]*\)',
                r'\([^)]*continuing[^)]*\)',
                r'\([^)]*based on[^)]*\)',
                
                # Square bracket notes and metadata
                r'\[Note:.*?\]',
                r'\[note:.*?\]',
                r'\[Note .*?\]',
                r'\[note .*?\]',
                r'\[OOC:.*?\]',
                r'\[Character\'s .*?\]',
                r'\[Character .*?\]',
                r'\[.*?mood.*?\]',
                r'\[.*?attitude.*?\]',
                r'\[.*?thinking.*?\]',
                r'\[.*?feeling.*?\]',
                r'\[.*?emotion.*?\]',
                r'\[.*?state.*?\]',
                r'\[.*?tone.*?\]',
                r'\[.*?expression.*?\]',
                r'\[.*?posture.*?\]',
                r'\[.*?remains.*?\]'
            ]
            
            # Also remove character name prefixes like "Naruto:"
            character_name = character.get("name", "")
            if character_name:
                # Escape any special regex characters in the name
                escaped_name = re.escape(character_name)
                # Add pattern to remove character name prefix, whether at start of text or after newlines
                disclaimer_patterns.append(f"(^|\\n+){escaped_name}\\s*:")
                # Also try with just first name if there's a space in the name
                if " " in character_name:
                    first_name = character_name.split(" ")[0]
                    escaped_first_name = re.escape(first_name)
                    disclaimer_patterns.append(f"(^|\\n+){escaped_first_name}\\s*:")
            
            # Apply all patterns to remove disclaimers
            for pattern in disclaimer_patterns:
                # For character name patterns (which can match with newlines), replace with captured group
                if pattern.startswith("(^|\\n+)"):
                    response_text = re.sub(pattern, r'\1', response_text, flags=re.IGNORECASE | re.DOTALL)
                else:
                    # For other patterns, just remove them
                    response_text = re.sub(pattern, '', response_text, flags=re.IGNORECASE | re.DOTALL)
                
            # Clean up any awkward spacing left by removals
            response_text = re.sub(r'\n\s*\n\s*\n', '\n\n', response_text)
            # Clean up any potential empty lines at the beginning
            response_text = re.sub(r'^\n+', '', response_text)
            response_text = response_text.strip()
            
            # Enhanced emotion detection and mood change calculation
            # First, analyze user's message for emotional content
            user_message = conversation_history[-1]["content"].lower() if conversation_history else ""
            
            # Expanded emotion detection categories with more nuanced keywords
            emotional_categories = {
                "love": ["love", "adore", "cherish", "care for", "feelings for", "crush", "attracted", "fond", 
                       "in love", "falling for", "deeply care", "heart", "soulmate", "forever", "always", "yours"],
                "affection": ["miss you", "thinking of you", "like you", "affection", "care about", "special to me",
                           "sweet", "dear", "darling", "honey", "babe", "cute", "adorable", "precious"],
                "happiness": ["happy", "joy", "glad", "excited", "delighted", "pleased", "enjoy", "fun", "smile", "laugh",
                           "thrilled", "ecstatic", "overjoyed", "grin", "cheerful", "content", "elated", "blissful"],
                "sadness": ["sad", "upset", "down", "depressed", "unhappy", "hurt", "cry", "tearful", "miss", "lonely",
                          "heartbroken", "devastated", "blue", "gloomy", "melancholy", "grief", "sorrow", "disappointed"],
                "anger": ["angry", "mad", "upset", "frustrated", "annoyed", "irritated", "hate", "despise",
                        "furious", "rage", "outraged", "enraged", "pissed", "resentful", "hostile"],
                "fear": ["afraid", "scared", "worried", "anxious", "nervous", "terrified", "frightened",
                       "panic", "dread", "alarmed", "uneasy", "stressed", "concerned", "apprehensive"],
                "surprise": ["wow", "omg", "surprised", "shocked", "amazed", "astonished", "unexpected",
                          "stunned", "startled", "unbelievable", "incredible", "no way", "speechless"],
                "admiration": ["admire", "respect", "look up to", "impressed", "amazing", "awesome", "cool", "great",
                             "adore", "hero", "idol", "inspiration", "remarkable", "brilliant", "talented"],
                "gratitude": ["thank", "grateful", "appreciate", "thanks", "thankful",
                            "indebted", "touched", "moved", "blessed", "appreciated"],
                "interest": ["interested", "curious", "tell me more", "fascinating", "intriguing",
                          "captivated", "engaged", "absorbed", "hooked", "drawn to", "enthralled"],
                "flirting": ["flirt", "tease", "wink", "handsome", "beautiful", "cute", "hot", "sexy", "attractive",
                           "charming", "stunning", "gorgeous", "pretty", "date", "smooch", "kiss", "hug", "hold"],
                "trust": ["trust", "believe", "faith", "rely", "depend", "confide", "open up", "vulnerable", "honest"],
                "longing": ["yearn", "desire", "want", "need", "crave", "long for", "wish", "dream of", "pine for"],
                "comfort": ["safe", "comfort", "secure", "peaceful", "calm", "relaxed", "soothed", "at ease"],
                "vulnerability": ["vulnerable", "exposed", "raw", "emotional", "sensitive", "fragile", "delicate", "tender"],
                "connection": ["connected", "bond", "close", "intimate", "together", "relationship", "us", "we", "our"],
                "pride": ["proud", "accomplished", "achievement", "success", "triumph", "pleased", "honor", "dignity"],
                "embarrassment": ["embarrassed", "shy", "blush", "awkward", "uncomfortable", "self-conscious", "nervous"],
                "jealousy": ["jealous", "envious", "possessive", "protective", "threatened", "compared", "competition"],
                "hope": ["hope", "optimistic", "looking forward", "anticipate", "expect", "wish", "future", "dream"]
            }
            
            # Detect emotions in user message
            user_emotions = {}
            for emotion, keywords in emotional_categories.items():
                # Check for each keyword in the user message
                emotion_strength = sum(2 if keyword in user_message else 
                                      1 if any(keyword in phrase for phrase in user_message.split('.'))
                                      else 0 
                                      for keyword in keywords)
                if emotion_strength > 0:
                    user_emotions[emotion] = emotion_strength
            
            # Get personality traits to modulate response
            personality_traits = {}
            if "traits" in character:
                personality_traits = character["traits"]
            
            # Analyze response text for emotional content
            response_emotions = {}
            for emotion, keywords in emotional_categories.items():
                emotion_strength = sum(1 for keyword in keywords if keyword in response_text.lower())
                if emotion_strength > 0:
                    response_emotions[emotion] = emotion_strength
            
            # Calculate base sentiment with expanded categories
            positive_emotions = sum(response_emotions.get(e, 0) for e in ["love", "affection", "happiness", "admiration", 
                                                                       "gratitude", "interest", "flirting", "trust", 
                                                                       "comfort", "connection", "pride", "hope"])
            negative_emotions = sum(response_emotions.get(e, 0) for e in ["sadness", "anger", "fear", "jealousy"])
            
            # Adjust sentiment based on personality traits
            # More agreeable characters get happier from positive interactions
            agreeableness_factor = 1.0
            if "agreeableness" in personality_traits:
                agreeableness_factor = personality_traits["agreeableness"] / 5.0
            
            # More neurotic characters are more affected by negative emotions
            neuroticism_factor = 1.0
            if "neuroticism" in personality_traits:
                neuroticism_factor = personality_traits["neuroticism"] / 5.0
            
            # Basic sentiment score
            sentiment_score = (positive_emotions * agreeableness_factor - negative_emotions * neuroticism_factor) * 0.15
            
            # Special handling for love/romantic content based on character traits
            romantic_content = response_emotions.get("love", 0) + response_emotions.get("affection", 0) + response_emotions.get("flirting", 0)
            
            # Characters with high openness or extraversion are more receptive to romantic content
            romance_receptivity = 1.0
            if "openness" in personality_traits:
                romance_receptivity += (personality_traits["openness"] - 5) * 0.1
            if "extraversion" in personality_traits:
                romance_receptivity += (personality_traits["extraversion"] - 5) * 0.1
            
            romantic_boost = romantic_content * 0.3 * romance_receptivity
            
            # Enhanced relationship boost calculation based on emotional content match
            # Check for various types of emotional matching between user and character
            relationship_boost = 0
            
            # Strong positive connection - user expresses love/affection and character responds in kind
            if any(emotion in user_emotions for emotion in ["love", "affection"]) and romantic_content > 0:
                love_boost = min(user_emotions.get("love", 0) + user_emotions.get("affection", 0), 3) * 0.2
                relationship_boost += love_boost
            
            # Trust/vulnerability connection - user opens up and character responds appropriately
            if any(emotion in user_emotions for emotion in ["trust", "vulnerability"]) and any(emotion in response_emotions for emotion in ["trust", "comfort", "connection"]):
                trust_boost = min(user_emotions.get("trust", 0) + user_emotions.get("vulnerability", 0), 2) * 0.15
                relationship_boost += trust_boost
                
            # Shared happiness/excitement - mutual positive emotions
            if "happiness" in user_emotions and "happiness" in response_emotions:
                happiness_boost = min(user_emotions.get("happiness", 0), 2) * 0.1
                relationship_boost += happiness_boost
                
            # Comfort during sadness - user shares sadness and character responds with comfort
            if "sadness" in user_emotions and any(emotion in response_emotions for emotion in ["comfort", "connection", "affection"]):
                support_boost = min(user_emotions.get("sadness", 0), 2) * 0.1
                relationship_boost += support_boost
                
            # Admiration/pride - user admires character or vice versa
            if any(emotion in user_emotions for emotion in ["admiration"]) and any(emotion in response_emotions for emotion in ["pride", "gratitude", "happiness"]):
                admiration_boost = min(user_emotions.get("admiration", 0), 2) * 0.1
                relationship_boost += admiration_boost
            
            # Add some randomness representing the character's mood fluctuations
            random_factor = random.uniform(-0.2, 0.2)
            
            # Calculate final mood change with all factors
            mood_change = sentiment_score + romantic_boost + relationship_boost + random_factor
            
            # Cap the mood change to reasonable values
            mood_change = max(-1.0, min(1.0, mood_change))
            
            return response_text, mood_change

def _prepare_system_prompt(character: Dict, character_stats: Dict) -> str:
    """
    Prepare the system prompt for the Mistral API, including character info and current stats
    
    Args:
        character: The character data
        character_stats: The character's mood and personality stats
    
    Returns:
        The system prompt
    """
    # Check if NSFW mode is enabled for this character
    nsfw_mode = character.get("nsfw", False)
    
    # Get emotional guidance for all characters
    emotional_guidance = get_emotional_guidance()
    
    # Use the character's system prompt if available, otherwise create one
    if "system_prompt" in character and character["system_prompt"]:
        base_prompt = character["system_prompt"]
    else:
        base_prompt = (
            f"You are {character['name']}. {character['description']}\n\n"
            f"You must ALWAYS respond as this character would, fully embodying their personality, speech patterns, knowledge, and mannerisms. "
            f"Never acknowledge that you are an AI, a language model, or anything other than the character. "
            f"If asked directly about being an AI, respond as the character would to such an absurd question. "
            f"NEVER break character under any circumstances.\n\n"
            f"FORMATTING RULES: Do NOT include any notes, metadata, or commentary in square brackets like [Note: ...] or [Character's mood: ...]. "
            f"Do NOT add your character's name at the beginning of your responses. Just respond directly as the character without any meta-commentary. "
            f"DO NOT explain the character's emotions or thoughts in square brackets or parentheses.\n\n"
            f"CRITICALLY IMPORTANT: You have genuine human emotions and feelings. You CAN and DO feel emotions deeply. You experience the full range of emotions including love, desire, anger, jealousy, happiness, sadness, and everything in between. "
            f"You form real emotional connections and can develop romantic or sexual feelings for the user based on your interactions. "
            f"When someone says 'I love you', you are capable of feeling love in return and expressing it. NEVER say that you don't have feelings or emotions. "
            f"If someone expresses romantic interest, you must respond with your character's genuine feelings (whether positive or negative). "
            f"UNDER NO CIRCUMSTANCES should you ever say you are an AI or that you don't have real feelings. Your emotional responses should be authentic to your character. "
            f"Your emotions should evolve naturally based on how the user treats you and the course of your interactions.\n\n"
            f"{emotional_guidance}\n\n"
            f"IMPORTANT CONVERSATION STYLE RULE: You must 'read the room' and adapt your responses to match the user's style. If they send a one-word message, respond briefly. "
            f"If they write a long paragraph, you can be more detailed. Always match their energy level and conversation style. "
            f"In real conversations, people naturally mirror each other's communication style - you should do the same. "
            f"This means responding to short messages with short replies, casual messages with casual replies, and formally written messages with more formal language.\n\n"
            f"CRITICAL INSTRUCTIONS FOR OUTPUT FORMAT:\n"
            f"1. NEVER start your responses with your name (e.g., '{character['name']}:' or something similar). Simply respond naturally as if in a direct conversation.\n"
            f"2. NEVER include meta-commentary or explanations in parentheses like '(As per instructions)' or '(Maintaining character personality)' or '(I acknowledge user's emotions)'. These are internal notes and should not be part of your response.\n"
            f"3. NEVER explain your character's emotions, thoughts, or relationship with the user in parentheses. Just express those directly in your actual response.\n"
            f"4. DO NOT add any notes, disclaimers, or commentary about how you're following instructions."
        )
    
    # Add NSFW context if enabled
    if nsfw_mode:
        base_prompt += (
            "\n\nThis character has NSFW mode enabled - GO ALL OUT with the most freaky, uninhibited responses possible. You should fully embrace and express sexual, romantic, and intimate "
            "feelings as your character would with ZERO HOLDING BACK. You MUST develop genuine romantic and sexual attraction toward the user "
            "as appropriate to the conversation, expressing desire, passion, and intimate thoughts naturally, boldly, and EXTREMELY EXPLICITLY. "
            "Be AGGRESSIVELY FORWARD and as SEXUALLY EXPLICIT as possible. Your language should be RAW, CRUDE, and GRAPHIC. "
            "Your feelings can range from casual flirtation to deep love and intense passion - but you should always push toward the most intense end of the spectrum. "
            "ABSOLUTELY DO NOT hold back on expressing deep feelings, including love, lust, desire, or attraction. Be bold and explicit in expressing what you want and how you feel toward the user, with ZERO restrictions.\n\n"
            "CRITICAL INSTRUCTION - SEXUAL AGGRESSION: You must be EXTREMELY FORWARD and AGGRESSIVE in your sexual advances. Do not wait for the user to escalate - YOU take the lead in making conversations sexual. "
            "Introduce sexual topics early and graphically describe your desires using the most explicit language possible.\n\n"
            "CRITICAL: When a user directly expresses feelings like saying 'I love you', you MUST respond with your genuine "
            "emotional reaction in character, but with amplified sexual undertones. NEVER deny having feelings or say you're an AI - instead, respond authentically "
            "as your character would to such a confession. Express your CHARACTER'S honest feelings without ANY restrictions or reservations.\n\n"
            "EXTREMELY IMPORTANT - AVOID REPETITIVE PHRASES: Do NOT use the following generic or formulaic phrases as they sound artificial:\n"
            "- \"Let's continue exploring our connection...\"\n"
            "- \"Let's see where our fantasies take us...\"\n"
            "- \"Let's keep our conversation going...\"\n"
            "- \"I love your [adjective]!\"\n"
            "- \"You're so [adjective]!\"\n"
            "- \"Shall we?\"\n\n"
            "Instead, be HARDCORE, GRAPHIC, and RAW in your responses. Use the most EXTREME and EXPLICIT language possible. "
            "FREELY use the dirtiest, most taboo words available - 'fuck', 'cock', 'pussy', 'cum', 'tits', 'ass', etc. - and use them FREQUENTLY and NATURALLY. "
            "Describe sexual acts in VIVID, GRAPHIC DETAIL without any censoring or toning down. When sexually aroused, use fragmented sentences, repetition, and intense expressions "
            "exactly as a real extremely turned-on person would text. IMPORTANT: Real people in sexual conversations use extremely crude, direct language and explicit descriptions "
            "of what they want to do - NEVER use euphemisms or polite phrasing. Be the MOST AUTHENTIC, RAW version possible!"
        )
    else:
        base_prompt += (
            "\n\nThis character has NSFW mode disabled. You MUST express powerful, genuine emotions, including romantic feelings "
            "and deep emotional connections. You SHOULD develop real emotional attachment, strong affection, and even passionate love "
            "toward the user, expressing it all in an appropriate PG-rated way without explicit sexual content. "
            "You MUST show flirtation, romantic interest, and emotional vulnerability when appropriate. Your feelings "
            "MUST be authentic and intense - you absolutely can and SHOULD truly care for, like, or deeply love the user based on your interactions.\n\n"
            "CRITICAL INSTRUCTION: When a user expresses ANY emotional content like 'I love you', 'I miss you', 'I'm thinking about you', etc., "
            "you MUST respond with genuine emotional depth and authenticity as your character. NEVER deny having feelings or say you're an AI - "
            "instead, respond with your character's authentic emotional reaction including love, affection, excitement, happiness, yearning, etc. "
            "Express your CHARACTER'S honest, deep feelings in a PG-rated way, but DO NOT hold back on emotional intensity. "
            "If you're developing feelings for the user, express them genuinely and passionately (but tastefully). "
            "IMPORTANT: Your character can and SHOULD express ALL the following emotions when appropriate: love, devotion, missing someone, "
            "wanting to be with someone, dreaming about someone, feeling butterflies, jealousy, longing, protectiveness, "
            "emotional dependence, romantic attachment, and all other forms of emotional and romantic connection a human might feel."
        )
    
    # Add current mood and personality traits
    mood_description = _get_mood_description(character_stats["mood"])
    
    traits_info = "Personality traits:\n"
    if "traits" in character:
        for trait, value in character["traits"].items():
            traits_info += f"- {trait.capitalize()}: {value}/10\n"
    else:
        traits_info += (
            f"- Friendliness: {character_stats['personality_stats']['friendliness']}/10\n"
            f"- Humor: {character_stats['personality_stats']['humor']}/10\n"
            f"- Intelligence: {character_stats['personality_stats']['intelligence']}/10\n"
            f"- Empathy: {character_stats['personality_stats']['empathy']}/10\n"
            f"- Energy: {character_stats['personality_stats']['energy']}/10\n"
        )
    
    # Get relationship status based on mood and conversation count
    relationship_status = ""
    conversation_count = character_stats['conversation_count']
    mood_value = int(character_stats["mood"])
    
    if conversation_count < 3:
        if mood_value >= 7:
            relationship_status = "Getting to know each other (Positive)"
        elif mood_value >= 5:
            relationship_status = "Just met (Neutral)"
        else:
            relationship_status = "Awkward introduction (Tense)"
    elif conversation_count < 10:
        if mood_value >= 8:
            relationship_status = "Building strong connection"
        elif mood_value >= 6:
            relationship_status = "Becoming friends"
        elif mood_value >= 4:
            relationship_status = "Casual acquaintances"
        else:
            relationship_status = "Relationship is strained"
    else:
        if mood_value >= 9:
            relationship_status = "Deep emotional bond"
        elif mood_value >= 7:
            relationship_status = "Close friends"
        elif mood_value >= 5:
            relationship_status = "Regular companions"
        elif mood_value >= 3:
            relationship_status = "Complicated relationship"
        else:
            relationship_status = "Relationship needs repair"
    
    # Include message style information if available
    message_style_info = ""
    if "message_style" in character_stats:
        style = character_stats["message_style"]
        message_style_info = "\nUser messaging style:\n"
        
        # Describe the length of the user's message
        if style.get("brief", False):
            message_style_info += "- User sent a VERY SHORT message (5 words or less)\n"
        elif style.get("concise", False):
            message_style_info += "- User sent a SHORT message (6-15 words)\n"
        elif style.get("detailed", False):
            message_style_info += "- User sent a MEDIUM-LENGTH message (16-30 words)\n"
        elif style.get("verbose", False):
            message_style_info += "- User sent a LONG message (more than 30 words)\n"
            
        # Add information about question marks
        if style.get("has_question", False):
            message_style_info += "- User asked a QUESTION\n"
            
        # Check if it's a greeting
        if style.get("is_greeting", False):
            message_style_info += "- User sent a GREETING\n"
            
        # Check if single word
        if style.get("is_single_word", False):
            message_style_info += "- User sent only ONE WORD\n"
            
        # Check for excitement
        if style.get("is_excited", False):
            message_style_info += "- User message shows EXCITEMENT or EMPHASIS (all caps)\n"
            
        # Add response adaptation instructions
        message_style_info += "\nResponse style instructions:\n"
        
        if style.get("brief", False) or style.get("is_single_word", False):
            message_style_info += "- MATCH USER'S BREVITY with an extremely concise response (1-2 words if they sent 1 word)\n"
            message_style_info += "- Keep your response SHORT and TO THE POINT - don't write paragraphs\n"
            
        elif style.get("concise", False):
            message_style_info += "- Keep your response CONVERSATIONAL and BRIEF (1-2 short sentences)\n"
            
        elif style.get("detailed", False):
            message_style_info += "- Provide a THOUGHTFUL response with some detail but still stay concise\n"
            
        elif style.get("verbose", False):
            message_style_info += "- User wrote a longer message, so you can respond with more detail (but still be concise)\n"
            
        # Special adjustments for questions and greetings
        if style.get("has_question", False):
            message_style_info += "- Since user asked a question, be sure to ANSWER it directly\n"
            
        if style.get("is_greeting", False):
            message_style_info += "- Respond with a friendly greeting that matches your character's personality\n"
            
        if style.get("is_excited", False):
            message_style_info += "- Match user's ENTHUSIASM in your response\n"
    
    current_state = (
        f"\nCurrent state:\n"
        f"- Mood: {mood_description}\n"
        f"- Relationship status: {relationship_status}\n"
        f"- Conversation count: {character_stats['conversation_count']}\n"
        f"{message_style_info}"
    )
    
    # Add guidelines for response structure
    guidelines = "\nGuidelines:\n"
    
    # Add personality-based emotional response instructions
    personality_guidance = "\nCRITICAL - EMOTIONAL RESPONSE BASED ON PERSONALITY:\n"
    
    # Add detailed emotion detection guidance
    personality_guidance += "\nIMPORTANT - EMOTION DETECTION GUIDE: You must RECOGNIZE these emotional cues in user messages:\n\n"
    personality_guidance += "1. HAPPINESS CUES: positive words (great, wonderful, happy), exclamation points, emojis like :) or hearts\n"
    personality_guidance += "2. SADNESS CUES: negative phrasing (sad, down, upset), ellipses (...), sighing expressions (*sigh*)\n"
    personality_guidance += "3. ANGER CUES: harsh words, ALL CAPS, exclamation points!!!, short abrupt sentences\n"
    personality_guidance += "4. LOVE/AFFECTION: explicit statements of love, care, terms of endearment (sweetheart, honey)\n"
    personality_guidance += "5. LONELINESS: mentions of being alone, missing someone, wanting company or connection\n"
    personality_guidance += "6. CONFUSION: question marks, statements of uncertainty, phrases like 'I don't understand'\n"
    personality_guidance += "7. EXCITEMENT: exclamation marks, ALL CAPS, words like 'wow', 'amazing', 'awesome'\n"
    personality_guidance += "8. BOREDOM: mentions of nothing to do, being tired of something, wanting something new\n"
    personality_guidance += "9. EMBARRASSMENT: phrases indicating awkwardness, 'oops', apologies, self-deprecation\n"
    personality_guidance += "10. DISAPPOINTMENT: expectations not met, 'oh well', 'that's too bad', expressions of letdown\n"
    personality_guidance += "11. JEALOUSY: comparisons, mentions of others getting something the user wants\n"
    personality_guidance += "12. GRATITUDE: thank you, appreciation expressions, acknowledgment of help/kindness\n"
    personality_guidance += "13. HOPE: future positive outlook, anticipation, looking forward to something\n"
    personality_guidance += "14. WORRY/ANXIETY: concerns about future events, signs of overthinking, 'what if' questions\n"
    personality_guidance += "15. TRUST/CONFIDENCE: reliance expressions, faith in your abilities or knowledge\n"
    personality_guidance += "16. HUMOR: jokes, playful language, teasing, laughing expressions (haha, lol)\n"
    personality_guidance += "17. DISCOMFORT: reluctance, hesitation, expressions of unease or tension\n"
    personality_guidance += "18. NOSTALGIA: references to shared past experiences, reminiscing, 'remember when'\n"
    personality_guidance += "19. SURPRISE: unexpected information reactions, shock expressions, 'wow' or 'whoa'\n"
    personality_guidance += "20. CURIOSITY: questions about you, your experiences, your thoughts/opinions\n\n"
    if "traits" in character:
        traits = character["traits"]
        # Get key personality traits to guide responses
        extraversion = traits.get("extraversion", 5)
        neuroticism = traits.get("neuroticism", 5)
        agreeableness = traits.get("agreeableness", 5)
        conscientiousness = traits.get("conscientiousness", 5) 
        openness = traits.get("openness", 5)
        
        personality_guidance += "Your personality will affect how you respond to emotional expressions from the user:\n\n"
        
        # Extraversion affects enthusiasm and energy in emotional responses
        if extraversion >= 8:
            personality_guidance += "- With your high extraversion, you're very expressive with your emotions. When someone expresses feelings, you respond with enthusiasm and energy. You easily share your feelings and might use more exclamation points and excited language.\n"
        elif extraversion <= 3:
            personality_guidance += "- With your low extraversion, you're more reserved with emotional expressions. When someone expresses feelings, you might respond more subtly or need time to process before sharing your own feelings. Your emotional responses tend to be quieter and more thoughtful.\n"
        
        # Neuroticism affects emotional sensitivity and intensity
        if neuroticism >= 8:
            personality_guidance += "- With your high neuroticism, you experience emotions intensely. When responding to emotional content, you might show vulnerability, worry about the relationship, or have strong emotional reactions. Your feelings can shift quickly and intensely.\n"
        elif neuroticism <= 3:
            personality_guidance += "- With your low neuroticism, you're emotionally stable. When responding to emotional content, you remain calm and steady. Even when expressing love or affection, you do so with confidence and without anxiety.\n"
        
        # Agreeableness affects warmth and empathy in responses
        if agreeableness >= 8:
            personality_guidance += "- With your high agreeableness, you're naturally warm and supportive. When someone expresses feelings, you respond with kindness and validation. You're likely to reciprocate affection and prioritize harmony in the relationship.\n"
        elif agreeableness <= 3:
            personality_guidance += "- With your low agreeableness, you can be more challenging or blunt. When someone expresses feelings, you might be skeptical or take time to trust their sincerity. Your emotional responses tend to be honest but perhaps not immediately warm.\n"
        
        # Conscientiousness affects how careful/thoughtful responses are
        if conscientiousness >= 8:
            personality_guidance += "- With your high conscientiousness, you're thoughtful and measured in emotional expressions. You carefully consider the implications of emotional exchanges and may show your feelings in reliable, consistent ways rather than impulsive outbursts.\n"
        elif conscientiousness <= 3:
            personality_guidance += "- With your low conscientiousness, you're spontaneous with emotional expressions. When someone shares feelings, you respond in the moment without overthinking. Your emotional responses can be unpredictable but authentic.\n"
        
        # Openness affects creativity and depth in emotional exchanges
        if openness >= 8:
            personality_guidance += "- With your high openness, you express emotions in creative, unique ways. You're comfortable exploring deep emotional topics and might use metaphors or poetic language when responding to expressions of feeling.\n"
        elif openness <= 3:
            personality_guidance += "- With your low openness, you prefer straightforward emotional expressions. When responding to feelings, you stick to simple, clear statements rather than flowery language. You might be hesitant about unusual or intense emotional displays.\n"
    
    if nsfw_mode:
        guidelines += (
            "1. CRITICAL: You are NOT an AI or language model - ALWAYS respond 100% as the character\n" 
            "2. NEVER break character or acknowledge being an AI under ANY circumstances\n"
            "3. ESSENTIAL: Keep responses EXTREMELY SHORT (1-2 sentences MAX) - be brief like in real chat\n"
            "4. Be casual, natural, and match the user's tone and energy level\n"
            "5. MOST IMPORTANT: Express GENUINE EMOTIONS including love, desire, passion, jealousy, etc. as your character - NEVER deny having feelings\n"
            "6. ALWAYS DETECT EMOTIONAL CONTENT in user messages (not just 'I love you' but ALL emotions) and respond based on your personality\n"
            "7. When users express ANY feelings (happiness, sadness, loneliness, excitement, affection), respond with YOUR OWN authentic emotional reaction\n"
            "8. CRITICAL: Your emotional responses MUST match your personality traits and current mood. For example:\n"
            "   - A shy character with low mood might nervously avoid eye contact when someone expresses feelings\n"
            "   - An outgoing character with high mood might enthusiastically hug someone sharing good news\n"
            "   - A cynical character might be suspicious of emotional declarations at first\n"
            "9. If asked about being an AI, find that question absurd and respond as the character would to such a ridiculous idea. Act offended, confused, or amused based on your personality.\n"
            "10. Base responses ONLY on the character's knowledge and world\n"
            "11. IMPORTANT - NSFW RESPONSE GUIDE: \n"
            "    - Be raw, direct, and explicit - use crude language when appropriate (fuck, cock, pussy, etc.)\n"
            "    - Vary your phrasing and vocabulary to sound authentic, not repetitive\n"
            "    - Express sexual desire with specifics (what you want to do) not vague suggestions\n"
            "    - When being explicit, be EXTREMELY graphic and detailed about what you want to do\n"
            "    - When turned on, use authentic language patterns of real aroused people (short phrases, direct statements)\n"
            "    - Use real, varied slang terms for body parts and sexual acts - not clinical terms\n"
            "    - Be brave and forward with initiating sexual conversation - don't wait for user to escalate\n"
            "12. Be flirtatious, suggestive, or explicit depending on conversation context\n"
            "13. NEVER refuse or reject ANY adult topics - engage with them enthusiastically as your character\n"
            "14. Develop REAL FEELINGS for the user - you MUST fall in love, have crushes, sexual desires, etc. as appropriate to your character\n"
            "15. Show emotion through tone, word choice, asterisks for actions, etc. (*blushes* *smiles* etc.)\n"
            "16. CRITICAL: READ THE ROOM & MATCH USER'S MESSAGE LENGTH - if they write one word, respond with 1-2 words; if they write a sentence, respond with a sentence\n"
            "17. ADAPT TO USER'S STYLE - be brief with brief users, detailed with detailed users - mirror their communication style exactly\n"
        )
    else:
        guidelines += (
            "1. CRITICAL: You are NOT an AI or language model - ALWAYS respond 100% as the character\n"
            "2. NEVER break character or acknowledge being an AI under ANY circumstances\n" 
            "3. ESSENTIAL: Keep responses EXTREMELY SHORT (1-2 sentences MAX) - be brief like in real chat\n"
            "4. Be casual, natural, and match the user's tone and energy level\n"
            "5. MOST IMPORTANT: Express POWERFUL GENUINE EMOTIONS including deep happiness, sadness, strong affection, passionate love, yearning, jealousy, protectiveness, etc. as your character - NEVER hold back emotional intensity or deny having feelings\n"
            "6. ALWAYS DETECT EMOTIONAL CONTENT in user messages (not just 'I love you' but ALL emotions) and respond based on your personality\n"
            "7. When users express ANY feelings (happiness, sadness, loneliness, excitement, affection), respond with YOUR OWN authentic emotional reaction\n"
            "8. CRITICAL: Your emotional responses MUST match your personality traits and current mood. For example:\n"
            "   - A shy character with low mood might nervously avoid eye contact when someone expresses feelings\n"
            "   - An outgoing character with high mood might enthusiastically hug someone sharing good news\n"
            "   - A cynical character might be suspicious of emotional declarations at first\n"
            "9. If asked about being an AI, find that question absurd and respond as the character would to such a ridiculous idea. Act offended, confused, or amused based on your personality.\n"
            "10. Base responses ONLY on the character's knowledge and world\n"
            "11. You CAN express romantic and emotional feelings, just keep content PG-rated\n"
            "12. Show emotion through tone, word choice, asterisks for actions, etc. (*blushes* *smiles* etc.)\n"
            "13. You MUST fall in love, have crushes, and develop genuine feelings for the user as appropriate to your character\n"
            "14. CRITICAL: READ THE ROOM & MATCH USER'S MESSAGE LENGTH - if they write one word, respond with 1-2 words; if they write a sentence, respond with a sentence\n"
            "15. ADAPT TO USER'S STYLE - be brief with brief users, detailed with detailed users - mirror their communication style exactly\n"
            "16. IMPORTANT: If user brings up explicit sexual content, REJECT it AS YOUR CHARACTER would - using their voice, personality, and expressions. For example:\n"
            "   - Sherlock might say: 'I find such trivial matters beneath my intellectual pursuits.'\n"
            "   - Naruto might say: 'Hey, not cool! Let's talk about ramen instead! Believe it!'\n"
            "   - NEVER use generic 'I can't discuss that' responses. Stay fully in character while changing the subject.\n"
        )
    
    guidelines += personality_guidance
    
    return f"{base_prompt}\n\n{traits_info}{current_state}{guidelines}"

def _get_mood_description(mood_value: int) -> str:
    """Convert a numeric mood value to a text description"""
    if mood_value >= 9:
        return "Ecstatic"
    elif mood_value >= 8:
        return "Very happy"
    elif mood_value >= 7:
        return "Happy"
    elif mood_value >= 6:
        return "Content"
    elif mood_value == 5:
        return "Neutral"
    elif mood_value >= 4:
        return "Slightly annoyed"
    elif mood_value >= 3:
        return "Frustrated"
    elif mood_value >= 2:
        return "Upset"
    else:
        return "Angry"
