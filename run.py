#!/usr/bin/env python3
"""
Enhanced LeetCode Chatbot Runner
Supports multi-collection queries and smart data access patterns
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Run the enhanced chatbot server"""
    print("🚀 Starting Enhanced LeetCode Chatbot...")
    print("=" * 50)
    print("✨ Enhanced Features:")
    print("• Multi-collection queries")
    print("• Smart data access patterns")
    print("• Contest information separate from student performance")
    print("• Student performance limited to latest 5 contests")
    print("• Top students with both rating and problems solved rankings")
    print("• Total sections calculation across all batches")
    print("=" * 50)
    
    # Check for required environment variables
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Warning: GOOGLE_API_KEY not found in environment variables")
        print("   The chatbot will still start but may not function properly")
    
    if not os.getenv("BACKEND_API_URL"):
        print("⚠️  Warning: BACKEND_API_URL not found in environment variables")
        print("   Using default: http://localhost:4000/graphql")
    
    # Get port from config
    from app.config import Config
    port = Config.PORT
    host = Config.HOST
    
    print(f"\n🌐 Server will be available at: http://localhost:{port}")
    print(f"📊 Stats endpoint: http://localhost:{port}/api/v1/stats")
    print(f"🛠️  Tools endpoint: http://localhost:{port}/api/v1/tools")
    print(f"🔧 Capabilities endpoint: http://localhost:{port}/api/v1/capabilities")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Run the enhanced server
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {str(e)}")

if __name__ == "__main__":
    main() 