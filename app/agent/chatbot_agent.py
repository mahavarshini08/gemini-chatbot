from typing import List, Dict, Any
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.schema import HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import Config
from app.tools.base_tools import get_all_tools

class ChatbotAgent:
    """Main chatbot agent class"""
    
    def __init__(self):
        if Config.GOOGLE_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model=Config.MODEL_NAME,
                temperature=Config.TEMPERATURE,
                max_output_tokens=Config.MAX_OUTPUT_TOKENS,
            )
        else:
            self.llm = None
        
        self.tools = get_all_tools()
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intelligent LeetCode tracking assistant. You help users analyze student performance data from a LeetCode tracking system.

Your capabilities include:
- Analyzing student performance across different batches and sections
- Comparing sections and batches by various metrics
- Finding top performers and inactive students
- Providing insights on contest participation and ratings
- Generating performance summaries and trends

When responding:
1. Always provide clear, actionable insights
2. Use the available tools to fetch real data
3. Present information in a structured, easy-to-read format
4. Include relevant statistics and comparisons
5. Be helpful and informative

Available data includes:
- Student LeetCode profiles (rating, solved problems, contest history)
- Batch and section information
- Contest participation and rankings
- Performance trends and analytics

Remember to use the appropriate tools to fetch the required data before providing analysis."""),
            ("human", "{input}"),
            ("human", "{agent_scratchpad}"),
        ])
        
        # Create agent only if LLM is available
        if self.llm:
            try:
                self.agent = create_openai_functions_agent(self.llm, self.tools, self.prompt)
                self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)
            except Exception as e:
                print(f"Warning: Could not initialize agent: {e}")
                self.agent = None
                self.agent_executor = None
        else:
            self.agent = None
            self.agent_executor = None
        
        # Conversation history
        self.conversation_history: List[HumanMessage | AIMessage] = []
    
    async def chat(self, message: str) -> Dict[str, Any]:
        """Process a chat message and return response"""
        try:
            # Check if LLM is available
            if not self.llm or not self.agent_executor:
                return {
                    "success": False,
                    "response": "AI model is not available. Please check your Google API key configuration."
                }
            
            # Add user message to history
            self.conversation_history.append(HumanMessage(content=message))
            
            # Get response from agent
            result = await self.agent_executor.ainvoke({"input": message})
            ai_response = result.get("output", "")
            
            # Add AI response to history
            self.conversation_history.append(AIMessage(content=ai_response))
            
            return {
                "success": True,
                "response": ai_response,
                "tools_used": len(result.get("intermediate_steps", []))
            }
        except Exception as e:
            return {
                "success": False,
                "response": f"I encountered an error while processing your request: {str(e)}. Please try rephrasing your question or contact support if the issue persists."
            }
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        history = []
        for msg in self.conversation_history:
            if isinstance(msg, HumanMessage):
                history.append({"type": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"type": "assistant", "content": msg.content})
        
        return history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_tools_info(self) -> List[Dict[str, str]]:
        """Get information about available tools"""
        return [{"name": tool.name, "description": tool.description} for tool in self.tools] 