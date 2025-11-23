"""LLM Service for Email Productivity Agent.

This module handles interactions with Google's Gemini API for email processing,
categorization, and draft generation.
"""
import os
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')) # Load from email_agent/.env

API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)

def get_model() -> genai.GenerativeModel:
    """Get the Gemini model instance.
    
    Returns:
        Configured Gemini GenerativeModel instance.
        
    Raises:
        ValueError: If GEMINI_API_KEY is not set in environment.
    """
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    return genai.GenerativeModel('gemini-2.5-flash')

def generate_response(prompt_template: str, email_body: str, 
                     additional_context: str = "") -> str:
    """Generate a response from the LLM using a prompt template and email content.
    
    Args:
        prompt_template: The prompt template with placeholders.
        email_body: The email content to process.
        additional_context: Optional additional context to append to prompt.
        
    Returns:
        Generated response text from the LLM.
        
    Raises:
        Exception: If LLM call fails.
    """
    try:
        model = get_model()
        
        # Construct the full prompt
        full_prompt = prompt_template.replace("{email_body}", email_body)
        if additional_context:
            full_prompt += f"\n\nUSER_QUERY: {additional_context}"
            
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        raise


def extract_json(text: str) -> str:
    """Extract JSON content from LLM response by removing markdown formatting.
    
    Args:
        text: Raw LLM response that may contain markdown code blocks.
        
    Returns:
        Cleaned JSON string with markdown formatting removed.
    """
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()
