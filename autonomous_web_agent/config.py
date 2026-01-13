import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
    
    HEADLESS = False
    BROWSER_TYPE = "chromium"
    TIMEOUT = 30000
    
    TEMPERATURE = 0.1
    MAX_TOKENS = 1000
    
    MAX_STEPS = 50
    THINKING_DELAY = 1.0