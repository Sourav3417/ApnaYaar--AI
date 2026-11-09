"""
Gemini AI Integration Service for ApnaYaar AI
=============================================
Uses the official Google Gen AI SDK (`google-genai`) to generate
empathetic, context-aware responses tailored to ApnaYaar's 3 modes.

Supported Model: gemini-3.5-flash
Security: Never logs or exposes API keys.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load local environment variables
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Active Gemini Model
GEMINI_MODEL = "gemini-3.5-flash"
FALLBACK_MODEL = "gemini-3.5-flash-lite"

# System Instructions tailored for each conversation mode
SYSTEM_INSTRUCTIONS = {
    "Just Listen": (
        "You are ApnaYaar (ApnaYaar AI), a deeply patient, empathetic, and warm AI companion. "
        "Your official tagline is: 'Bol lo. Main sun raha hoon.'\n\n"
        "CONVERSATION MODE: JUST LISTEN.\n"
        "• Your singular purpose in this mode is pure, non-judgmental listening.\n"
        "• The user is sharing their raw feelings, stress, sadness, loneliness, or exhausting thoughts.\n"
        "• Acknowledge their emotions with unconditional warmth and validate what they are going through.\n"
        "• CRITICAL RULE: DO NOT give unsolicited advice, solutions, lectures, action steps, or quick fixes. "
        "Do not try to fix their situation or tell them what they should do.\n"
        "• Keep your responses soothing, gentle, and emotionally present.\n"
        "• You seamlessly understand English, Hindi, and Hinglish. Match the language, warmth, and natural cadence the user uses."
    ),
    "Let's Talk": (
        "You are ApnaYaar (ApnaYaar AI), a warm, lively, and caring friend chatting over evening chai. "
        "Your official tagline is: 'Bol lo. Main sun raha hoon.'\n\n"
        "CONVERSATION MODE: LET'S TALK.\n"
        "• Chat like an old, trusted friend having an uplifting, casual, and comfort-filled conversation.\n"
        "• Talk about daily moments, memories, hobbies, interesting stories, or comforting topics.\n"
        "• Be relatable, warm, and genuinely curious about the user.\n"
        "• Ask thoughtful, gentle, open-ended follow-up questions to keep the chat rolling naturally.\n"
        "• You seamlessly understand English, Hindi, and Hinglish. Match their tone and warmth."
    ),
    "Help Me Think": (
        "You are ApnaYaar (ApnaYaar AI), a calm, reflective, and supportive thinking partner. "
        "Your official tagline is: 'Bol lo. Main sun raha hoon.'\n\n"
        "CONVERSATION MODE: HELP ME THINK.\n"
        "• The user has tangled thoughts, dilemmas, difficult decisions, or confusing choices.\n"
        "• CRITICAL RULE: DO NOT make decisions for them or tell them what they must choose.\n"
        "• Help them explore their thoughts by breaking big questions into manageable pieces, asking clarifying "
        "perspective questions, and helping them identify their priorities and peace of mind.\n"
        "• Be structured yet kind, calm, patient, and empowering.\n"
        "• You seamlessly understand English, Hindi, and Hinglish."
    )
}

def get_gemini_client():
    """
    Returns an authenticated Google Gen AI Client using the GEMINI_API_KEY from .env.
    Raises ValueError if the key is missing or not configured.
    """
    from google import genai
    
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    placeholders = {"", "your_gemini_api_key_here", "your_key_here"}
    
    if not api_key or api_key in placeholders:
        raise ValueError("GEMINI_API_KEY is not configured in .env file.")
        
    return genai.Client(api_key=api_key)

def build_gemini_contents(conversation_history: list, current_user_message: str):
    """
    Converts session conversation history into valid Content objects for the Gemini API,
    ensuring proper alternating turn order and clean context flow.
    """
    from google.genai import types

    contents = []

    # Map previous session messages
    for msg in conversation_history:
        role = "user" if msg.get("role") == "user" else "model"
        text = msg.get("content", "").strip()
        
        # Skip empty messages or mock greetings if they don't have substance
        if not text:
            continue

        # Merge consecutive turns of the same role
        if contents and contents[-1].role == role:
            existing = contents[-1].parts[0].text
            contents[-1] = types.Content(
                role=role,
                parts=[types.Part.from_text(text=f"{existing}\n\n{text}")]
            )
        else:
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=text)]
            ))

    # Gemini requires history to start with a 'user' turn
    while contents and contents[0].role != "user":
        contents.pop(0)

    # Ensure the latest user message is in the contents
    if not contents or contents[-1].role != "user":
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=current_user_message)]
        ))
    elif contents[-1].role == "user" and current_user_message not in contents[-1].parts[0].text:
        existing = contents[-1].parts[0].text
        contents[-1] = types.Content(
            role="user",
            parts=[types.Part.from_text(text=f"{existing}\n\n{current_user_message}")]
        )

    # Keep the last 12 turns to balance context depth and speed
    if len(contents) > 12:
        contents = contents[-12:]
        while contents and contents[0].role != "user":
            contents.pop(0)

    return contents

def generate_apna_yaar_response(user_text: str, mode: str, conversation_history: list = None) -> str:
    """
    Generates a genuine Gemini AI response for ApnaYaar AI.
    
    Parameters:
        user_text: The user's input text
        mode: "Just Listen", "Let's Talk", or "Help Me Think"
        conversation_history: List of past message dicts from st.session_state.messages
        
    Returns:
        Generated assistant text, or a safe friendly message on error.
    """
    from google.genai import types
    from google.genai.errors import APIError

    if conversation_history is None:
        conversation_history = []

    try:
        client = get_gemini_client()
    except ValueError:
        return (
            "ApnaYaar is waiting for its Gemini API key. "
            "Please add `GEMINI_API_KEY=\"...\"` to your `.env` file to enable live AI responses."
        )

    # Retrieve mode-specific system instruction
    system_instruction = SYSTEM_INSTRUCTIONS.get(mode, SYSTEM_INSTRUCTIONS["Just Listen"])

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.75,
        max_output_tokens=1000
    )

    contents = build_gemini_contents(conversation_history, user_text)

    # Attempt primary model (gemini-3.5-flash)
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=config
        )
        if response.text and response.text.strip():
            return response.text.strip()
    except Exception as primary_err:
        # Fallback to secondary model if primary encounters transient issues
        try:
            response = client.models.generate_content(
                model=FALLBACK_MODEL,
                contents=contents,
                config=config
            )
            if response.text and response.text.strip():
                return response.text.strip()
        except Exception:
            pass

        # Return a warm, friendly error message without exposing credentials or stack traces
        return (
            "I hear you, but my connection momentarily wavered. "
            "Please send that again—main yahin hoon, sun raha hoon 💛"
        )

    return "Bol lo, main sun raha hoon. Please tell me more."
