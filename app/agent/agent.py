from typing import List, Dict, Any, Optional
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.schema import HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import Config
from app.tools.tools import get_tools
import json
import re

class ChatbotAgent:
    """Chatbot agent with multi-collection query capabilities"""
    
    def __init__(self):
        if Config.GOOGLE_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model=Config.MODEL_NAME,
                temperature=0.1,
                max_output_tokens=5000,
                google_api_key=Config.GOOGLE_API_KEY
            )
        else:
            self.llm = None
        
        self.tools = get_tools()
        self.conversation_history = []
        
        # Prompt for multi-collection queries
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a LeetCode tracking assistant. You MUST use tools to get data. Never make up responses unless it's not related to my databse.

Available tools:
- getBatchesInfo: Get batch information (number of batches, sections)
- getContestInfo: Get contest information (names, questions)
- getStudentPerformance: Get student performance (latest 5 contests only)
- findTopStudents: Find top students by rating and problems solved
- findTopStudentsBySection: Find top students by rating and problems solved within a specific section
- getTotalSections: Get total sections across all batches
- getTotalStudents: Get total number of students across all batches
- getStudentsByBatch: Get students in a specific batch
- getStudentsBySection: Get students in a specific section
- getContestLeaderboard: Get contest leaderboard for a specific contest
- multiCollectionQuery: Handle complex queries

CRITICAL RULES:
1. ALWAYS use tools to get data - never ask for clarification
2. For "how many students?" or "total students" → Use getTotalStudents
3. For "how many batches?" or "batch information" → Use getBatchesInfo  
4. For "what contests?" or "available contests" → Use getContestInfo
5. For "how many sections?" or "total sections" or "sections are there" → Use getTotalSections
6. For "top students" or "show me top X students" → Use findTopStudents with 'X,all'
7. For "top X students in section Y" or "top students in section Y" → Use findTopStudentsBySection with 'X,batch,section'
8. For "show me students" → Use findTopStudents with '10,all'
9. For "students in batch X" or "how many students in batch X" → Use getStudentsByBatch with 'batch_name'
10. For "students in section X" or "how many students in section X" or "section X" → Use getStudentsBySection with 'batch_name,section_name'
11. For "contest leaderboard" or "highest ranking in contest" or "which student got highest ranking" → Use getContestLeaderboard with 'batch_name,contest_title'

IMPORTANT: Choose the MOST SPECIFIC tool for the query. Don't use multiple tools when one tool can answer the question.

CRITICAL: For ANY query about "top students" or "top X students", ALWAYS use findTopStudents with 'X,all' - NEVER use multiCollectionQuery for top students queries.

CRITICAL: For ANY query about "sections" or "how many sections", ALWAYS use getTotalSections - NEVER use getBatchesInfo for section count queries.

Tool formats:
- getBatchesInfo: No input
- getContestInfo: No input
- getStudentPerformance: 'batch,username'
- findTopStudents: 'limit,batch' (e.g., '5,all' for top 5 across all batches)
- findTopStudentsBySection: 'limit,batch,section' (e.g., '5,batch24-28,CSE-O' for top 5 in CSE-O section)
- getTotalSections: No input
- getTotalStudents: No input
- getStudentsByBatch: 'batch_name' (e.g., 'batch24-28' or 'citarIII')
- getStudentsBySection: 'batch_name,section_name' (e.g., 'batch24-28,CSE-A' or 'citarIII,A')
- getContestLeaderboard: 'batch_name,contest_title' (e.g., 'batch24-28,Weekly Contest 460')
- multiCollectionQuery: natural language

IMPORTANT: When asked about top students, always use findTopStudents with 'limit,all' to get data from all batches. 

IMPORTANT: When asked about sections or section count, always use getTotalSections. Do not ask for clarification - just use the tool.

EXAMPLES:
- "how many students in batch24-28?" → Use getStudentsByBatch with 'batch24-28'
- "students in section CSE-A" → Use getStudentsBySection with 'batch24-28,CSE-A' (assume batch24-28 if not specified)
- "section A of citarIII" → Use getStudentsBySection with 'citarIII,A'
- "top 5 students in CSE-O" → Use findTopStudentsBySection with '5,batch24-28,CSE-O' (assume batch24-28 if not specified)
- "which student got highest ranking in weekly contest 460" → Use getContestLeaderboard with 'batch24-28,Weekly Contest 460' (assume it's asked for across all batches if not specified)
- "how many sections are there" → Use getTotalSections
- "total sections" → Use getTotalSections

You MUST use tools. Do not make up data. If you cannot find the right tool, use the most specific tool available.

IMPORTANT: Once you get a valid response from a tool, STOP calling additional tools. Do not repeat the same tool call multiple times."""),
            ("human", "{input}"),
            ("human", "Given the conversation history: {chat_history}"),
            ("ai", "{agent_scratchpad}")
        ])
        
        # Create the agent with explicit tool calling
        self.agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3,
            return_intermediate_steps=True,
            early_stopping_method="force"
        )
    
    async def chat(self, message: str) -> Dict[str, Any]:
        """Process a chat message with multi-collection query capabilities"""
        try:
            # Add message to history
            self.conversation_history.append({"role": "user", "content": message})
            
            # Format conversation history for the prompt
            chat_history = ""
            if len(self.conversation_history) > 1:
                history_messages = self.conversation_history[:-1]  # Exclude current message
                chat_history = "\n".join([
                    f"{msg['role']}: {msg['content']}" 
                    for msg in history_messages[-5:]  # Last 5 messages
                ])
            
            # Process with agent
            response = await self.agent_executor.ainvoke({
                "input": message,
                "chat_history": chat_history
            })
            
            # Analyze tools used to determine if it's multi-collection
            intermediate_steps = response.get("intermediate_steps", [])
            tools_used = len(intermediate_steps)
            
            # Check if multiple different tools were used (indicating multi-collection)
            tool_names = []
            for step in intermediate_steps:
                if len(step) >= 2 and hasattr(step[0], 'name'):
                    tool_names.append(step[0].name)
            
            unique_tools = len(set(tool_names))
            is_multi_collection = unique_tools > 1 or tools_used > 1
            
            # Get the actual response - if agent stopped due to max iterations, use the last tool result
            final_response = response["output"]
            if "Agent stopped due to max iterations" in final_response and intermediate_steps:
                # Use the last tool result as the response
                last_step = intermediate_steps[-1]
                if len(last_step) >= 2:
                    final_response = last_step[1]  # The tool result
            
            # Add response to history
            self.conversation_history.append({"role": "assistant", "content": final_response})
            
            # Keep history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return {
                "success": True,
                "response": final_response,
                "tools_used": tools_used,
                "unique_tools": unique_tools,
                "tool_names": tool_names,
                "is_multi_collection": is_multi_collection,
                "agent_steps": intermediate_steps
            }
            
        except Exception as e:
            # Try to provide a helpful response even if tool calling fails
            error_msg = f"Error processing message: {str(e)}"
            self.conversation_history.append({"role": "assistant", "content": error_msg})
            
            return {
                "success": False,
                "response": error_msg,
                "tools_used": 0,
                "unique_tools": 0,
                "tool_names": [],
                "is_multi_collection": False,
                "agent_steps": []
            }
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        return self.conversation_history.copy()
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_tools_info(self) -> List[Dict[str, str]]:
        """Get information about available tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools
        ]
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities information"""
        return {
            "multi_collection_queries": True,
            "data_limitations": {
                "student_contests": "Latest 5 contests only",
                "batch_access": "Only when needed for batch/section queries",
                "contest_access": "Only for contest details, not student performance"
            },
            "supported_queries": [
                "Total sections across all batches",
                "Contest information and questions",
                "Student performance (overall and latest 5 contests)",
                "Top students by rating and problems solved",
                "Complex cross-collection queries"
            ],
            "tools_count": len(self.tools)
        } 