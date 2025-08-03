from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any, Optional

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    success: bool
    response: str
    tools_used: int = 0

class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str
    timestamp: str
    service: str

class ToolInfo(BaseModel):
    """Model for tool information"""
    name: str
    description: str

class ToolsResponse(BaseModel):
    """Response model for tools endpoint"""
    success: bool
    tools: List[ToolInfo]

class ExampleQuery(BaseModel):
    """Model for example query"""
    category: str
    queries: List[str]

class ExampleQueriesResponse(BaseModel):
    """Response model for example queries endpoint"""
    success: bool
    examples: List[ExampleQuery]

class ConversationMessage(BaseModel):
    """Model for conversation history messages"""
    type: str  # "user" or "assistant"
    content: str

class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history endpoint"""
    success: bool
    history: List[ConversationMessage]

class ClearHistoryResponse(BaseModel):
    """Response model for clear history endpoint"""
    success: bool
    message: str 