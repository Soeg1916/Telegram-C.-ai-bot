import os
import json
import logging
import asyncio
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

async def test_generate_response():
    """Test the Mistral API response format"""
    # Get the Mistral API key from environment variable
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable not set!")
    
    # Simple system prompt for testing
    system_prompt = "You are Lilith, a character from One Piece."
    
    # Test message
    test_message = "Hi Lilith!"
    
    # Prepare the messages for the Mistral API
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": test_message}
    ]
    
    # Prepare the request payload
    payload = {
        "model": "mistral-medium",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 400,
        "top_p": 0.9,
        "safe_prompt": False
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
            
            # Log the entire response for inspection
            logger.info(f"Complete API response: {json.dumps(response_data, indent=2)}")
            
            # Extract the response text
            response_text = response_data["choices"][0]["message"]["content"]
            logger.info(f"Raw response text: {response_text}")
            
            # Check if there are any parenthetical notes or hidden instructions in the response
            if "(" in response_text and ")" in response_text:
                logger.info("Found parentheses in response, checking for notes:")
                parenthetical_parts = []
                current_text = response_text
                
                # Simple extraction of text in parentheses
                while "(" in current_text and ")" in current_text:
                    start_idx = current_text.find("(")
                    end_idx = current_text.find(")", start_idx)
                    if start_idx != -1 and end_idx != -1:
                        parenthetical_parts.append(current_text[start_idx:end_idx+1])
                        current_text = current_text[end_idx+1:]
                    else:
                        break
                
                logger.info(f"Parenthetical parts found: {parenthetical_parts}")
            
            # Check for "Note:" or similar indicators
            if "Note:" in response_text or "note:" in response_text:
                logger.info("Found 'Note:' indicator in response")
                note_parts = []
                for line in response_text.split('\n'):
                    if "Note:" in line or "note:" in line:
                        note_parts.append(line)
                
                logger.info(f"Note parts found: {note_parts}")
                
            # Return the response text
            return response_text

# Run the test
if __name__ == "__main__":
    asyncio.run(test_generate_response())