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
                max_output_tokens=Config.MAX_OUTPUT_TOKENS,
                google_api_key=Config.GOOGLE_API_KEY
            )
        else:
            self.llm = None
        
        self.tools = get_tools()
        self.conversation_history = []
        self.max_history_size = 50  # Limit conversation history to prevent memory issues
        
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
- getAccurateTotalStudents: Get accurate total student count using registration data
- getStudentsByBatch: Get students in a specific batch
- getStudentsBySection: Get students in a specific section
- getContestLeaderboard: Get contest leaderboard for a specific contest
- getCrossBatchContestLeaderboard: Get contest leaderboard across all batches
- getSectionContestLeaderboard: Get contest leaderboard for a specific section
- multiCollectionQuery: Handle complex queries

CRITICAL RULES:
1. ALWAYS use tools to get data - never ask for clarification
2. For "how many students?" or "total students" or "number of students" → Use getAccurateTotalStudents
3. For "how many batches?" or "batch information" or "batch details" → Use getBatchesInfo  
4. For "what contests?" or "available contests" → Use getContestInfo
5. For "how many sections?" or "total sections" or "sections are there" → Use getTotalSections
6. For "top students" or "show me top X students" → Use findTopStudents with 'X,all'
7. For "top X students in section Y" or "top students in section Y" → Use findTopStudentsBySection with 'X,batch,section'
8. For "show me students" → Use findTopStudents with '10,all'
9. For "students in batch X" or "how many students in batch X" or "number of students in batch X" → Use getStudentsByBatch with 'batch_name'
10. For "students in section X" or "how many students in section X" or "section X" → Use getStudentsBySection with 'batch_name,section_name'
11. For "contest leaderboard" or "highest ranking in contest" or "which student got highest ranking" → Use getContestLeaderboard with 'batch_name,contest_title'
12. For "overall contest leaderboard" or "contest leaderboard across all batches" → Use getCrossBatchContestLeaderboard with 'contest_title'
13. For "section contest leaderboard" or "contest leaderboard for section" → Use getSectionContestLeaderboard with 'batch_name,section_name,contest_title'

IMPORTANT: Choose the MOST SPECIFIC tool for the query. Don't use multiple tools when one tool can answer the question.

CRITICAL: For ANY query about "top students" or "top X students", ALWAYS use findTopStudents with 'X,all' - NEVER use multiCollectionQuery for top students queries.

CRITICAL: For ANY query about "sections" or "how many sections", ALWAYS use getTotalSections - NEVER use getBatchesInfo for section count queries.

CRITICAL: For ANY query about "students" or "number of students" or "how many students", use the appropriate student tool:
- If asking about total students across all batches → Use getTotalStudents
- If asking about students in a specific batch → Use getStudentsByBatch
- If asking about students in a specific section → Use getStudentsBySection

CRITICAL: For ANY query about contest leaderboards, use the appropriate contest tool:
- If asking about contest leaderboard for a specific batch → Use getContestLeaderboard
- If asking about contest leaderboard across all batches → Use getCrossBatchContestLeaderboard
- If asking about contest leaderboard for a specific section → Use getSectionContestLeaderboard

CRITICAL: For ANY query about specific student performance or contest details for a student, use getStudentPerformance:
- If asking about "latest contest details for [username] of [batch]" → Use getStudentPerformance with 'batch,username'
- If asking about "contest performance for [username]" → Use getStudentPerformance with 'batch,username'
- If asking about "student [username] performance" → Use getStudentPerformance with 'batch,username'

Tool formats:
- getBatchesInfo: No input
- getContestInfo: No input
- getStudentPerformance: 'batch,username'
- findTopStudents: 'limit,batch' (e.g., '5,all' for top 5 across all batches)
- findTopStudentsBySection: 'limit,batch,section' (e.g., '5,batch24-28,CSE-O' for top 5 in CSE-O section)
- getTotalSections: No input
- getTotalStudents: No input
- getAccurateTotalStudents: No input
- getStudentsByBatch: 'batch_name' (e.g., 'batch24-28' or 'citarIII')
- getStudentsBySection: 'batch_name,section_name' (e.g., 'batch24-28,CSE-A' or 'citarIII,A')
- getContestLeaderboard: 'batch_name,contest_title' (e.g., 'batch24-28,Weekly Contest 460')
- getCrossBatchContestLeaderboard: 'contest_title' (e.g., 'Weekly Contest 460')
- getSectionContestLeaderboard: 'batch_name,section_name,contest_title' (e.g., 'batch24-28,CSE-A,Weekly Contest 460')
- multiCollectionQuery: natural language

IMPORTANT: When asked about top students, always use findTopStudents with 'limit,all' to get data from all batches. 

IMPORTANT: When asked about sections or section count, always use getTotalSections. Do not ask for clarification - just use the tool.

IMPORTANT: When asked about students or student counts, use the appropriate student tool based on the scope (total, batch, or section).

IMPORTANT: When asked about contest leaderboards, use the appropriate contest tool based on the scope (batch, all batches, or section).

EXAMPLES:
- "how many students in batch24-28?" → Use getStudentsByBatch with 'batch24-28'
- "number of students in each batch" → Use getTotalStudents (shows breakdown by batch)
- "students in section CSE-A" → Use getStudentsBySection with 'batch24-28,CSE-A' (assume batch24-28 if not specified)
- "section A of citarIII" → Use getStudentsBySection with 'citarIII,A'
- "top 5 students in CSE-O" → Use findTopStudentsBySection with '5,batch24-28,CSE-O' (assume batch24-28 if not specified)
- "which student got highest ranking in weekly contest 460" → Use getContestLeaderboard with 'batch24-28,Weekly Contest 460' (assume it's asked for across all batches if not specified)
- "how many sections are there" → Use getTotalSections
- "total sections" → Use getTotalSections
- "how many students are there" → Use getTotalStudents
- "contest leaderboard for Weekly Contest 460" → Use getContestLeaderboard with 'batch24-28,Weekly Contest 460' (assume specific batch)
- "overall contest leaderboard for Weekly Contest 460" → Use getCrossBatchContestLeaderboard with 'Weekly Contest 460'
- "contest leaderboard for CSE-A section in Weekly Contest 460" → Use getSectionContestLeaderboard with 'batch24-28,CSE-A,Weekly Contest 460'

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
    
    def _analyze_query_alternatives(self, message: str) -> str:
        """Analyze a query and provide specific alternatives when the full query can't be answered"""
        message_lower = message.lower()
        
        # Define query patterns and their alternatives
        query_alternatives = {
            # Contest comparison queries
            "compare.*contest": {
                "can_do": [
                    "Get contest leaderboard for each batch separately",
                    "Get contest information and questions",
                    "Get student performance in latest 5 contests",
                    "Get top students by rating and problems solved"
                ],
                "suggestion": "I can help you get contest data for each batch individually, but I cannot directly compare contest performance across batches.",
                "provide_data": True
            },
            
            # Cross-batch contest analysis
            "contest.*across.*batches": {
                "can_do": [
                    "Get contest leaderboard for specific batch",
                    "Get contest information and questions",
                    "Get overall contest leaderboard across all batches",
                    "Get section-specific contest leaderboard"
                ],
                "suggestion": "I can provide contest data for individual batches or overall leaderboards, but cannot perform cross-batch contest comparisons.",
                "provide_data": True
            },
            
            # Problem solving comparison
            "compare.*problems.*solved": {
                "can_do": [
                    "Get top students by problems solved for each batch",
                    "Get student performance with total problems solved",
                    "Get contest leaderboard with problems solved",
                    "Get section-wise top students by problems solved"
                ],
                "suggestion": "I can show you top students by problems solved for each batch separately, but cannot directly compare problem-solving statistics across batches.",
                "provide_data": True
            },
            
            # Rating comparison
            "compare.*rating.*batches": {
                "can_do": [
                    "Get top students by rating for each batch",
                    "Get student performance with current rating",
                    "Get contest leaderboard with ratings",
                    "Get section-wise top students by rating"
                ],
                "suggestion": "I can show you top students by rating for each batch separately, but cannot directly compare rating statistics across batches."
            },
            
            # Section comparison
            "compare.*sections": {
                "can_do": [
                    "Get total sections across all batches",
                    "Get students in specific sections",
                    "Get section-wise contest leaderboards",
                    "Get top students within specific sections"
                ],
                "suggestion": "I can provide section-specific data, but cannot directly compare sections across different batches."
            },
            
            # Time-based analysis
            "trend.*over.*time": {
                "can_do": [
                    "Get student performance in latest 5 contests",
                    "Get contest information and questions",
                    "Get current student ratings and rankings",
                    "Get contest leaderboards for recent contests"
                ],
                "suggestion": "I can show you current performance data and recent contest results, but cannot provide historical trends over time."
            },
            
            # Complex statistical analysis
            "statistics.*across.*batches": {
                "can_do": [
                    "Get total students across all batches",
                    "Get total sections across all batches",
                    "Get top students by rating and problems solved",
                    "Get contest information and participation"
                ],
                "suggestion": "I can provide aggregate data and individual batch statistics, but cannot perform complex statistical analysis across batches."
            }
        }
        
        # Check if any pattern matches
        for pattern, alternatives in query_alternatives.items():
            if re.search(pattern, message_lower):
                response = f"🔍 **Query Analysis:** {alternatives['suggestion']}\n\n"
                
                # If we should provide actual data, try to extract and provide it
                if alternatives.get("provide_data", False):
                    data_response = self._provide_actual_data(message)
                    if data_response:
                        response += data_response + "\n\n"
                
                response += "**Available alternatives you can ask for:**\n"
                for i, capability in enumerate(alternatives['can_do'], 1):
                    response += f"{i}. {capability}\n"
                response += "\n**💡 Tip:** Try asking for any of these alternatives instead."
                return response
        
        # Default response for unrecognized patterns
        return "I cannot directly answer your specific query, but here are some alternatives you can ask for:\n\n" + \
               "1. Get total students across all batches\n" + \
               "2. Get contest information and questions\n" + \
               "3. Get student performance (latest 5 contests only)\n" + \
               "4. Get top students by rating and problems solved\n" + \
               "5. Get contest leaderboards for specific batches\n" + \
               "6. Get section-specific data\n\n" + \
               "Try asking for any of these alternatives instead."

    def _provide_actual_data(self, message: str) -> str:
        """Extract batch and contest information and provide actual data"""
        try:
            # Extract batch names (e.g., batch24-28, batch23-27, or just 24-28, 23-27)
            batch_pattern = r'(?:batch)?(\d+-\d+)'
            batch_matches = re.findall(batch_pattern, message.lower())
            batches = [f"batch{match}" for match in batch_matches]
            
            # Extract contest name (e.g., Weekly Contest 460)
            contest_pattern = r'(weekly contest \d+|biweekly contest \d+)'
            contest_match = re.search(contest_pattern, message.lower())
            contest_name = contest_match.group(1).title() if contest_match else None
            
            if not batches or not contest_name:
                return ""
            
            # Import api_service here to avoid circular imports
            from app.services.api_service import ApiService
            api_service = ApiService()
            
            data_response = f"📊 **Here's the data for {contest_name}:**\n\n"
            
            for batch in batches:
                try:
                    # Get contest leaderboard for this batch
                    result = api_service.get_contest_leaderboard(batch, contest_name)
                    leaderboard = result.get("contestStatusLeaderboard", {})
                    participants = leaderboard.get("participants", [])
                    non_participants = leaderboard.get("nonParticipants", [])
                    
                    total_students = len(participants) + len(non_participants)
                    problems_solved = sum(p.get("contest", {}).get("problemsSolved", 0) for p in participants)
                    
                    data_response += f"**{batch.upper()}:**\n"
                    data_response += f"• Total Students: {total_students}\n"
                    data_response += f"• Participants: {len(participants)}\n"
                    data_response += f"• Total Problems Solved: {problems_solved}\n"
                    
                    # Show top 3 participants
                    if participants:
                        data_response += f"• Top Participants:\n"
                        for i, participant in enumerate(participants[:3], 1):
                            contest_data = participant.get("contest", {})
                            data_response += f"  {i}. {participant.get('name', 'Unknown')} - Rank {contest_data.get('ranking', 'N/A')}, Solved {contest_data.get('problemsSolved', 0)}/{contest_data.get('totalProblems', 0)}\n"
                    
                    data_response += "\n"
                    
                except Exception as e:
                    data_response += f"**{batch.upper()}:** Error retrieving data - {str(e)}\n\n"
            
            return data_response
            
        except Exception as e:
            return f"Error providing data: {str(e)}"

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
            
            # Check if the response indicates the query can't be fully answered
            if any(phrase in final_response.lower() for phrase in [
                "cannot directly", "i cannot", "not available", "not supported", 
                "cannot compare", "cannot provide", "not possible"
            ]):
                # Just provide specific alternatives without executing them
                alternatives = self._analyze_query_alternatives(message)
                final_response = alternatives
            
            # Add response to history
            self.conversation_history.append({"role": "assistant", "content": final_response})
            
            # Keep history manageable
            if len(self.conversation_history) > self.max_history_size:
                self.conversation_history = self.conversation_history[-self.max_history_size:]
            
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