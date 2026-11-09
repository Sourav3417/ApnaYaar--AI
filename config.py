"""
Configuration Manager for ApnaYaar AI
=====================================
Safely loads and manages local environment variables from .env.
Ensures API keys are never hardcoded or logged in plaintext.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Path to the project root directory
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# Load environment variables from .env if it exists
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Placeholders to ignore
_PLACEHOLDERS = {"", "your_gnani_api_key_here", "your_gemini_api_key_here", "your_key_here"}

# Gnani AI Configuration
_RAW_GNANI_API_KEY = os.getenv("GNANI_API_KEY", "").strip()
GNANI_API_KEY = "" if _RAW_GNANI_API_KEY in _PLACEHOLDERS else _RAW_GNANI_API_KEY

# Gemini AI Configuration
_RAW_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_API_KEY = "" if _RAW_GEMINI_API_KEY in _PLACEHOLDERS else _RAW_GEMINI_API_KEY

# Gemini Model Selection
GEMINI_MODEL_NAME = "gemini-3.5-flash"

def is_gnani_configured() -> bool:
    """Returns True if a valid Gnani API key is loaded."""
    return bool(GNANI_API_KEY)

def is_gemini_configured() -> bool:
    """Returns True if a valid Gemini API key is loaded."""
    return bool(GEMINI_API_KEY)

def get_config_status() -> dict:
    """
    Returns safe diagnostic information about the configuration
    without exposing any sensitive key characters.
    """
    has_env_file = ENV_PATH.exists()
    gnani_ok = is_gnani_configured()
    gemini_ok = is_gemini_configured()
    
    return {
        "env_file_exists": has_env_file,
        "gnani_configured": gnani_ok,
        "gnani_key_length": len(GNANI_API_KEY) if gnani_ok else 0,
        "gemini_configured": gemini_ok,
        "gemini_key_length": len(GEMINI_API_KEY) if gemini_ok else 0,
        "gemini_model": GEMINI_MODEL_NAME
    }

if __name__ == "__main__":
    # Safe verification test that can be run directly from terminal
    status = get_config_status()
    print("=" * 55)
    print("       ApnaYaar AI - Configuration Check")
    print("=" * 55)
    print(f"[OK] .env file found: {'[YES]' if status['env_file_exists'] else '[NO]'}")
    
    # Gnani status
    if status["gnani_configured"]:
        print(f"[OK] Gnani API Key:  [DETECTED] ({status['gnani_key_length']} characters)")
    else:
        print("[!]  Gnani API Key:  [NOT SET / EMPTY]")
        
    # Gemini status
    if status["gemini_configured"]:
        print(f"[OK] Gemini API Key: [DETECTED] ({status['gemini_key_length']} characters)")
        print(f"[OK] Gemini Model:   {status['gemini_model']}")
    else:
        print("[!]  Gemini API Key: [NOT SET / EMPTY]")
        
    print("=" * 55)
    print("(Note: For security, actual secret values are never displayed)")
