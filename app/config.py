import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the LeetCode Chatbot"""
    
    # API Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:4000/graphql")
    
    # Server Configuration
    PORT = int(os.getenv("PORT", 3001))
    HOST = os.getenv("HOST", "0.0.0.0")
    
    # Model Configuration
    MODEL_NAME = "gemini-2.5-flash"
    TEMPERATURE = 0.1
    MAX_OUTPUT_TOKENS = 2048
    
    # CORS Configuration
    ALLOW_ORIGINS = ["*"]
    ALLOW_CREDENTIALS = True
    ALLOW_METHODS = ["*"]
    ALLOW_HEADERS = ["*"]
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GOOGLE_API_KEY:
            print("⚠️  Warning: GOOGLE_API_KEY environment variable is not set")
            print("   The chatbot will work but Gemini AI features will be limited")
            print("   To enable full functionality, set GOOGLE_API_KEY in your .env file")
        
        return True 