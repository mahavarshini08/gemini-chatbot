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
    MAX_OUTPUT_TOKENS = 100000
    
    # Rate Limiting Configuration
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", 8))  # Conservative limit
    MAX_REQUESTS_PER_DAY = int(os.getenv("MAX_REQUESTS_PER_DAY", 200))      # Conservative limit
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    
    # CORS Configuration
    ALLOW_ORIGINS = ["*"]
    ALLOW_CREDENTIALS = True
    ALLOW_METHODS = ["*"]
    ALLOW_HEADERS = ["*"]
    
    # Environment Configuration
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = ENVIRONMENT == "development"
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GOOGLE_API_KEY:
            print("⚠️  Warning: GOOGLE_API_KEY environment variable is not set")
            print("   The chatbot will work but Gemini AI features will be limited")
            print("   To enable full functionality, set GOOGLE_API_KEY in your .env file")
        
        # Rate limiting warnings
        if cls.RATE_LIMIT_ENABLED:
            print(f"🔄 Rate limiting enabled: {cls.MAX_REQUESTS_PER_MINUTE} req/min, {cls.MAX_REQUESTS_PER_DAY} req/day")
        else:
            print("⚠️  Rate limiting disabled - be careful with API usage")
        
        return True 