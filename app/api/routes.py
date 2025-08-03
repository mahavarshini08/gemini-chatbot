from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
import google.generativeai as genai
from app.models import (
    ChatRequest, ChatResponse, HealthResponse, ToolsResponse, 
    ExampleQueriesResponse, ConversationHistoryResponse, ClearHistoryResponse
)
from app.agent.chatbot_agent import ChatbotAgent
from app.config import Config

# Initialize router
router = APIRouter()

# Initialize chatbot agent
chatbot_agent = ChatbotAgent()

# Configure Gemini for test connection
genai.configure(api_key=Config.GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        service="LeetCode Chatbot API"
    )

@router.get("/test-connection")
async def test_connection():
    """Test connection to Gemini API"""
    try:
        response = model.generate_content("Hello! Please respond with 'Connection successful' if you can hear me.")
        return {
            "success": True,
            "message": response.text
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}"
        }

@router.post("/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    try:
        result = await chatbot_agent.chat(request.message)
        return ChatResponse(
            success=result["success"],
            response=result["response"],
            tools_used=result.get("tools_used", 0)
        )
    except Exception as e:
        return ChatResponse(
            success=False,
            response=f"I encountered an error while processing your request: {str(e)}. Please try rephrasing your question or contact support if the issue persists."
        )

@router.get("/conversation-history")
async def get_conversation_history():
    """Get conversation history"""
    history = chatbot_agent.get_conversation_history()
    return ConversationHistoryResponse(success=True, history=history)

@router.post("/clear-history")
async def clear_history():
    """Clear conversation history"""
    chatbot_agent.clear_history()
    return ClearHistoryResponse(success=True, message="Conversation history cleared")

@router.get("/tools")
async def get_tools():
    """Get available tools information"""
    tools_info = chatbot_agent.get_tools_info()
    return ToolsResponse(success=True, tools=tools_info)

@router.get("/example-queries")
async def get_example_queries():
    """Get example queries for users"""
    examples = [
        {
            "category": "Batch Analysis",
            "queries": [
                "Show me all available batches",
                "Get all students in batch23-27",
                "Compare secA and secB in batch24-28 by rating",
                "Compare secA and secB in batch24-28 by solved problems",
            ]
        },
        {
            "category": "Student Analysis",
            "queries": [
                "Get details for student luvitta-stina in batch23-27",
                "Find top 10 students by rating across all batches",
                "Find top 5 students by solved problems across all batches",
                "Find inactive students in batch24-28 who haven't participated in the last 7 days",
            ]
        },
        {
            "category": "Contest Analysis",
            "queries": [
                "Get all contests for batch23-27",
                "Show contest leaderboard for weekly-contest-460 in batch23-27",
                "Which students participated in the last contest?",
            ]
        },
        {
            "category": "Advanced Analytics",
            "queries": [
                "Which section has the highest average rating?",
                "Find students with rating above 1800 and solved problems above 100",
                "Show me students who improved their rating in the last 3 contests",
                "Which batch has the most active participants?",
            ]
        }
    ]
    return ExampleQueriesResponse(success=True, examples=examples) 