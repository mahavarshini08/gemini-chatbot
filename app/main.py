from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from app.agent.agent import ChatbotAgent
from app.services.cache_monitor import start_cache_monitoring, get_cache_monitor_status
from app.middleware.rate_limiter import rate_limit_middleware, rate_limiter
import time
import json

load_dotenv()

app = FastAPI(title="LeetCode Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Initialize agent
agent = ChatbotAgent()

# Start automatic cache monitoring
cache_monitor = start_cache_monitoring(agent.api_service, check_interval=14400)  # Check every 4 hours

class ChatRequest(BaseModel):
    message: str

class UsageTracker:
    """Track usage statistics"""
    
    def __init__(self):
        self.total_requests = 0
        self.total_tool_calls = 0
        self.multi_collection_queries = 0
        self.request_history = []
    
    def record_request(self, tools_used: int, multi_collection: bool):
        """Record a request's usage"""
        self.total_requests += 1
        self.total_tool_calls += tools_used
        if multi_collection:
            self.multi_collection_queries += 1
        
        self.request_history.append({
            "timestamp": time.time(),
            "tools_used": tools_used,
            "multi_collection": multi_collection
        })
        
        # Keep only last 100 requests
        if len(self.request_history) > 100:
            self.request_history = self.request_history[-100:]
    
    def get_stats(self):
        """Get usage statistics"""
        if self.total_requests == 0:
            return {
                "total_requests": 0,
                "average_tools_per_request": 0,
                "multi_collection_rate": 0,
                "total_tool_calls": 0
            }
        
        avg_tools = self.total_tool_calls / self.total_requests
        multi_collection_rate = self.multi_collection_queries / self.total_requests
        
        return {
            "total_requests": self.total_requests,
            "total_tool_calls": self.total_tool_calls,
            "average_tools_per_request": round(avg_tools, 2),
            "multi_collection_rate": round(multi_collection_rate * 100, 2),
            "multi_collection_queries": self.multi_collection_queries,
            "recent_requests": len(self.request_history)
        }

# Initialize usage tracker
usage_tracker = UsageTracker()

@app.get("/api/v1/stats")
async def get_stats():
    """Get usage statistics"""
    return {
        "usage_stats": usage_tracker.get_stats(),
        "tools_available": len(agent.get_tools_info())
    }

@app.get("/api/v1/tools")
async def get_tools():
    """Get available tools information"""
    return {
        "tools": agent.get_tools_info()
    }

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """Chat endpoint with multi-collection query support"""
    try:
        # Process with agent
        result = await agent.chat(request.message)
        
        # Use the agent's determination of multi-collection
        is_multi_collection = result.get("is_multi_collection", False)
        
        # Record usage
        usage_tracker.record_request(
            tools_used=result.get("tools_used", 0),
            multi_collection=is_multi_collection
        )
        
        return {
            "success": result["success"],
            "response": result["response"],
            "tools_used": result["tools_used"],
            "unique_tools": result.get("unique_tools", 0),
            "tool_names": result.get("tool_names", []),
            "multi_collection": is_multi_collection,
            "agent_steps": result.get("agent_steps", [])
        }
        
    except Exception as e:
        return {
            "success": False,
            "response": f"Error processing request: {str(e)}",
            "tools_used": 0,
            "unique_tools": 0,
            "tool_names": [],
            "multi_collection": False,
            "agent_steps": []
        }

@app.get("/api/v1/history")
async def get_history():
    """Get conversation history"""
    return {
        "success": True,
        "history": agent.get_conversation_history()
    }

@app.post("/api/v1/clear-history")
async def clear_history():
    """Clear conversation history"""
    agent.clear_history()
    return {
        "success": True,
        "message": "Conversation history cleared"
    }

@app.get("/api/v1/test-connection")
async def test_connection():
    """Test API connection"""
    try:
        # Test basic agent functionality
        test_result = await agent.chat("Hello, can you tell me about your capabilities?")
        
        return {
            "status": "success",
            "message": "Chatbot is working properly",
            "test_response": test_result["response"][:200] + "..." if len(test_result["response"]) > 200 else test_result["response"]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection test failed: {str(e)}"
        }

@app.get("/api/v1/cache-health")
async def get_cache_health():
    """Get cache health status"""
    try:
        cache_health = agent.api_service.get_cache_health_status()
        monitor_status = get_cache_monitor_status()
        
        return {
            "cache_health": cache_health,
            "monitor_status": monitor_status,
            "message": "Cache health check completed"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Cache health check failed: {str(e)}"
        }

@app.get("/api/v1/rate-limit-status")
async def get_rate_limit_status():
    """Get rate limit status"""
    try:
        remaining = rate_limiter.get_remaining_requests()
        return {
            "rate_limit_enabled": Config.RATE_LIMIT_ENABLED,
            "limits": {
                "requests_per_minute": Config.MAX_REQUESTS_PER_MINUTE,
                "requests_per_day": Config.MAX_REQUESTS_PER_DAY
            },
            "remaining": remaining,
            "message": "Rate limit status retrieved"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Rate limit status failed: {str(e)}"
        }

@app.get("/", response_class=HTMLResponse)
async def root():
    """Modern chatbot interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LeetCode Chatbot</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 900px;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                height: 80vh;
            }
            
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            
            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 10px;
                font-weight: 300;
            }
            
            .header p {
                font-size: 1.1rem;
                opacity: 0.9;
            }
            
            .chat-container {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                background: #f8f9fa;
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            
            .message {
                max-width: 80%;
                padding: 15px 20px;
                border-radius: 20px;
                word-wrap: break-word;
                line-height: 1.5;
                animation: fadeIn 0.3s ease-in;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .user-message {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                align-self: flex-end;
                border-bottom-right-radius: 5px;
            }
            
            .bot-message {
                background: white;
                color: #333;
                align-self: flex-start;
                border-bottom-left-radius: 5px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .input-section {
                padding: 20px;
                background: white;
                border-top: 1px solid #eee;
                display: flex;
                gap: 15px;
                align-items: center;
            }
            
            #messageInput {
                flex: 1;
                padding: 15px 20px;
                border: 2px solid #e9ecef;
                border-radius: 25px;
                font-size: 16px;
                outline: none;
                transition: border-color 0.3s ease;
            }
            
            #messageInput:focus {
                border-color: #667eea;
            }
            
            .btn {
                padding: 15px 25px;
                border: none;
                border-radius: 25px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            
            .btn-secondary {
                background: #6c757d;
                color: white;
            }
            
            .btn-secondary:hover {
                background: #5a6268;
                transform: translateY(-2px);
            }
            
            .typing-indicator {
                display: none;
                align-self: flex-start;
                background: white;
                padding: 15px 20px;
                border-radius: 20px;
                border-bottom-left-radius: 5px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .typing-dots {
                display: flex;
                gap: 4px;
            }
            
            .typing-dots span {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #667eea;
                animation: typing 1.4s infinite ease-in-out;
            }
            
            .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
            .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
            
            @keyframes typing {
                0%, 80%, 100% { transform: scale(0); }
                40% { transform: scale(1); }
            }
            
            .tool-info {
                font-size: 12px;
                color: #6c757d;
                margin-top: 5px;
                font-style: italic;
            }
            
            @media (max-width: 768px) {
                .container {
                    height: 100vh;
                    border-radius: 0;
                }
                
                .header h1 {
                    font-size: 2rem;
                }
                
                .message {
                    max-width: 90%;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 LeetCode Chatbot</h1>
                <p>Your intelligent assistant for LeetCode data and analytics</p>
            </div>
            
            <div class="chat-container" id="chatContainer">
                <div class="message bot-message">
                    👋 Hello! I'm your LeetCode tracking assistant. I can help you with:
                    <br><br>
                    • 📊 Student information and rankings<br>
                    • 🏆 Contest details and leaderboards<br>
                    • 📈 Batch and section analytics<br>
                    • 🎯 Top performers by rating and problems solved<br>
                    <br>
                    What would you like to know?
                </div>
            </div>
            
            <div class="typing-indicator" id="typingIndicator">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
            
            <div class="input-section">
                <input type="text" id="messageInput" placeholder="Ask me anything about LeetCode data..." onkeypress="handleKeyPress(event)">
                <button class="btn btn-primary" onclick="sendMessage()">Send</button>
                <button class="btn btn-secondary" onclick="clearChat()">Clear</button>
            </div>
        </div>

        <script>
            async function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                if (!message) return;
                
                // Add user message
                addMessage(message, 'user');
                input.value = '';
                
                // Show typing indicator
                showTypingIndicator();
                
                try {
                    const response = await fetch('/api/v1/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: message })
                    });
                    
                    const data = await response.json();
                    
                    // Hide typing indicator
                    hideTypingIndicator();
                    
                    if (data.success) {
                        addMessage(data.response, 'bot');
                        
                        // Add tool usage info if tools were used
                        if (data.tools_used > 0) {
                            const toolInfo = data.multi_collection 
                                ? `🔗 Multi-collection query used ${data.unique_tools} tools`
                                : `🛠️ Used ${data.tools_used} tool(s)`;
                            addMessage(toolInfo, 'bot');
                        }
                    } else {
                        addMessage("❌ Error: " + data.response, 'bot');
                    }
                } catch (error) {
                    hideTypingIndicator();
                    addMessage("❌ Error connecting to server: " + error.message, 'bot');
                }
            }
            
            function addMessage(text, sender) {
                const container = document.getElementById('chatContainer');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}-message`;
                messageDiv.innerHTML = text.replace(/\\n/g, '<br>');
                container.appendChild(messageDiv);
                container.scrollTop = container.scrollHeight;
            }
            
            function showTypingIndicator() {
                document.getElementById('typingIndicator').style.display = 'block';
                document.getElementById('chatContainer').scrollTop = document.getElementById('chatContainer').scrollHeight;
            }
            
            function hideTypingIndicator() {
                document.getElementById('typingIndicator').style.display = 'none';
            }
            
            function clearChat() {
                document.getElementById('chatContainer').innerHTML = 
                    '<div class="message bot-message">Chat cleared. How can I help you?</div>';
            }
            
            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }
            
            // Focus on input when page loads
            window.onload = function() {
                document.getElementById('messageInput').focus();
            };
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 