#!/usr/bin/env python3
"""
Run script for the LeetCode Chatbot
"""

import uvicorn
from app.config import Config

if __name__ == "__main__":
    # Validate configuration
    Config.validate()
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True,
        log_level="info"
    ) 