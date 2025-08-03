#!/usr/bin/env python3
"""
Test script to verify the chatbot setup
"""

import sys
import os

def test_imports():
    """Test that all imports work correctly"""
    try:
        # Test core imports
        from app.config import Config
        print("✓ Config imported successfully")
        
        from app.models import ChatRequest, ChatResponse
        print("✓ Models imported successfully")
        
        from app.services.api_service import ApiService
        print("✓ API Service imported successfully")
        
        from app.tools.base_tools import get_all_tools
        print("✓ Tools imported successfully")
        
        from app.agent.chatbot_agent import ChatbotAgent
        print("✓ Chatbot Agent imported successfully")
        
        from app.api.routes import router
        print("✓ API Routes imported successfully")
        
        from app.main import app
        print("✓ Main app imported successfully")
        
        print("\n🎉 All imports successful! The chatbot is ready to run.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_config():
    """Test configuration validation"""
    try:
        from app.config import Config
        
        # Test config validation (this will fail if GOOGLE_API_KEY is not set)
        try:
            Config.validate()
            print("✓ Configuration validation passed")
        except ValueError as e:
            print(f"⚠️  Configuration warning: {e}")
            print("   This is expected if GOOGLE_API_KEY is not set in environment")
        
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def main():
    """Main test function"""
    print("Testing LeetCode Chatbot Setup...\n")
    
    # Test imports
    imports_ok = test_imports()
    
    print("\n" + "="*50 + "\n")
    
    # Test configuration
    config_ok = test_config()
    
    print("\n" + "="*50 + "\n")
    
    if imports_ok and config_ok:
        print("✅ Setup test completed successfully!")
        print("\nTo run the chatbot:")
        print("1. Set your GOOGLE_API_KEY in a .env file")
        print("2. Run: python run.py")
        print("3. Visit: http://localhost:3001/docs")
    else:
        print("❌ Setup test failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 