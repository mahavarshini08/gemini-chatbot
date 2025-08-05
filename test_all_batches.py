#!/usr/bin/env python3
"""
Test script to demonstrate all-batches behavior
"""

import asyncio
from app.agent.agent import ChatbotAgent

async def test_all_batches_behavior():
    """Test queries with and without specific batch mentions"""
    
    # Initialize the enhanced agent
    agent = ChatbotAgent()
    
    # Test queries
    test_queries = [
        # Queries without specific batch (should default to all batches)
        "Show me top 5 students",
        "How many sections are there?",
        "What contests are available?",
        
        # Queries with specific batch
        "Show me top 5 students in batch24-25",
        "How many sections are in batch24-25?",
        # Note: Contest queries don't need batch specification since contest details are same across all batches
    ]
    
    print("🧪 Testing All-Batches Behavior")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 40)
        
        try:
            result = await agent.chat(query)
            
            print(f"✅ Success: {result['success']}")
            print(f"📊 Tools Used: {result['tools_used']}")
            print(f"🔧 Tool Names: {result['tool_names']}")
            print(f"🔗 Multi-Collection: {result['is_multi_collection']}")
            print(f"💬 Response:")
            print(result['response'])
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("-" * 40)
    
    print("\n🎯 Expected Behavior:")
    print("• Queries without batch mention → Should show data from ALL batches")
    print("• Queries with specific batch → Should show data from that batch only")
    print("• Contest queries → Same details across all batches (no batch specification needed)")
    print("• Clear scope indicators (📊, **bold text**) should be present")

if __name__ == "__main__":
    asyncio.run(test_all_batches_behavior()) 