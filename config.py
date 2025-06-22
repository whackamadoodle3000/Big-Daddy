#!/usr/bin/env python3
"""
Configuration file for Smart Student Monitor
Loads settings from environment variables or provides defaults
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Gemini API Key for reporting
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# LMNT Configuration (speech synthesis)
LMNT_API_KEY = os.getenv("LMNT_API_KEY", "ak_GkxGopYg9FwhJaQkJ9huMC")

# Monitoring Intervals
BROWSER_INTERVAL = int(os.getenv("BROWSER_INTERVAL", "5"))
AI_INTERVAL = int(os.getenv("AI_INTERVAL", "8"))

# Speech Configuration
SPEECH_ENABLED = os.getenv("SPEECH_ENABLED", "true").lower() == "true"
SPEECH_COOLDOWN = int(os.getenv("SPEECH_COOLDOWN", "120"))

# Browser Configuration
HEADLESS_MODE = os.getenv("HEADLESS_MODE", "false").lower() == "true"

# File Paths
SCREENSHOTS_DIR = "screenshots"
LOGS_FILE = "logs.csv"
AI_ANALYSIS_FILE = "ai_analysis.csv"

# AI Model Configuration
DEFAULT_MODEL = "gpt-4o"
FAST_MODEL = "gpt-3.5-turbo"
TEMPERATURE = 0.3
MAX_TOKENS = 500

def validate_config():
    """Validate that required configuration is present"""
    if not OPENAI_API_KEY:
        print("⚠️ Warning: OPENAI_API_KEY not set")
        print("   Create a .env file with your OpenAI API key:")
        print("   OPENAI_API_KEY=your-api-key-here")
        return False
    return True

def get_config_summary():
    """Get a summary of current configuration"""
    return {
        "openai_api_key": "Set" if OPENAI_API_KEY else "Not Set",
        "gemini_api_key": "Set" if GEMINI_API_KEY else "Not Set",
        "lmnt_api_key": "Set" if LMNT_API_KEY else "Using Default",
        "browser_interval": BROWSER_INTERVAL,
        "ai_interval": AI_INTERVAL,
        "speech_enabled": SPEECH_ENABLED,
        "headless_mode": HEADLESS_MODE
    }