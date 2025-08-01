import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import firebase_admin
from firebase_admin import credentials, firestore

# ✅ Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
firebase_cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
project_id = os.getenv("FIREBASE_PROJECT_ID")

if not api_key:
    print("❌ Google API Key not found. Please check your .env file.")
    exit()

# ✅ Initialize Firebase (Firestore only)
try:
    if firebase_cred_path and os.path.exists(firebase_cred_path):
        cred = credentials.Certificate(firebase_cred_path)
        firebase_admin.initialize_app(cred, {'projectId': project_id})
    else:
        firebase_admin.initialize_app()
    
    db = firestore.client()
    print("✅ Firestore connected successfully!")
    
except Exception as e:
    print(f"❌ Failed to initialize Firebase: {e}")
    exit()

# ✅ Initialize Gemini
try:
    chat = ChatGoogleGenerativeAI(
        model="models/gemini-2.5-flash",
        temperature=0.3,
        google_api_key=api_key
    )
except Exception as e:
    print(f"❌ Failed to initialize Gemini model: {e}")
    exit()

# ✅ Advanced Firestore Query Functions
def get_all_collections():
    """Get list of all Firestore collections"""
    try:
        collections = db.collections()
        return [col.id for col in collections]
    except Exception as e:
        return f"Error getting collections: {e}"

def get_collection_data(collection_name, limit=None):
    """Get all documents from a collection"""
    try:
        query = db.collection(collection_name)
        if limit:
            query = query.limit(limit)
        
        docs = query.stream()
        data = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['_document_id'] = doc.id
            data.append(doc_data)
        return data
    except Exception as e:
        return f"Error querying collection '{collection_name}': {e}"

def query_with_filters(collection_name, filters=None, order_by=None, limit=None):
    """Advanced querying with filters and sorting"""
    try:
        query = db.collection(collection_name)
        
        # Apply filters
        if filters:
            for field, operator, value in filters:
                query = query.where(field, operator, value)
        
        # Apply ordering
        if order_by:
            for field, direction in order_by:
                if direction.lower() == 'desc':
                    query = query.order_by(field, direction=firestore.Query.DESCENDING)
                else:
                    query = query.order_by(field, direction=firestore.Query.ASCENDING)
        
        # Apply limit
        if limit:
            query = query.limit(limit)
        
        docs = query.stream()
        data = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['_document_id'] = doc.id
            data.append(doc_data)
        return data
    except Exception as e:
        return f"Error with advanced query: {e}"

def get_analytics_data(collection_name):
    """Get comprehensive analytics data for analysis"""
    try:
        all_data = get_collection_data(collection_name)
        if isinstance(all_data, str):  # Error case
            return all_data
        
        # Basic analytics
        analytics = {
            "total_documents": len(all_data),
            "sample_data": all_data[:3] if all_data else [],
            "fields_available": list(all_data[0].keys()) if all_data else [],
            "data": all_data  # Full data for complex analysis
        }
        return analytics
    except Exception as e:
        return f"Error getting analytics: {e}"

def process_complex_query(user_query, collections_data):
    """Process complex analytical queries"""
    query_lower = user_query.lower()
    
    # Performance Ranking Queries
    if any(phrase in query_lower for phrase in ["top", "ranking", "best", "highest"]):
        if "cse" in query_lower and "rating" in query_lower:
            return "🎯 RANKING QUERY DETECTED: Top CSE students by rating"
        elif "problems" in query_lower and "solved" in query_lower:
            return "🎯 RANKING QUERY DETECTED: Top students by problems solved"
        elif "performers" in query_lower and "section" in query_lower:
            return "🎯 RANKING QUERY DETECTED: Top performers by section"
    
    # Filtering Queries
    elif any(phrase in query_lower for phrase in ["list", "who", "show", "filter"]):
        if "more than" in query_lower and "problems" in query_lower:
            return "🔍 FILTER QUERY DETECTED: Students with >X problems solved"
        elif "improved" in query_lower and "rank" in query_lower:
            return "🔍 FILTER QUERY DETECTED: Students who improved ranking"
        elif "rating above" in query_lower:
            return "🔍 FILTER QUERY DETECTED: Students with rating above threshold"
    
    # Grouping & Analysis
    elif any(phrase in query_lower for phrase in ["how many", "average", "sort", "group"]):
        if "section" in query_lower and "problems" in query_lower:
            return "🔁 GROUPING QUERY DETECTED: Problems solved by section"
        elif "average rating" in query_lower:
            return "🔁 ANALYSIS QUERY DETECTED: Average rating comparison"
        elif "sort" in query_lower:
            return "🔁 SORTING QUERY DETECTED: Sort students by criteria"
    
    # Time-based Analysis
    elif any(phrase in query_lower for phrase in ["last", "this week", "this month", "trend", "inactive"]):
        if "submissions" in query_lower and "days" in query_lower:
            return "📅 TIME QUERY DETECTED: Recent submission activity"
        elif "inactive" in query_lower:
            return "📅 TIME QUERY DETECTED: Inactive students analysis"
        elif "trend" in query_lower:
            return "📅 TIME QUERY DETECTED: Submission trends"
    
    # Combined Complex Queries
    elif "and" in query_lower or "who" in query_lower:
        if "rating above" in query_lower and "problems" in query_lower:
            return "📐 COMPLEX QUERY DETECTED: Multiple criteria filtering"
        elif "didn't submit" in query_lower:
            return "📐 COMPLEX QUERY DETECTED: Inactive students with criteria"
    
    # Edge Case Analysis
    elif any(phrase in query_lower for phrase in ["dropped", "streak", "improved most"]):
        return "🧠 ADVANCED ANALYSIS DETECTED: Performance trend analysis"
    
    # Provide relevant data context
    context = "Available data for analysis:\n"
    for collection, data in collections_data.items():
        if isinstance(data, dict) and 'fields_available' in data:
            context += f"- {collection}: {data['fields_available']}\n"
    
    return context

def get_database_overview():
    """Get comprehensive database overview with analytics focus"""
    collections = get_all_collections()
    
    if isinstance(collections, str):
        return {"error": collections}
    
    overview = {
        "total_collections": len(collections),
        "collections": collections,
        "analytics_data": {}
    }
    
    # Get detailed data for analysis
    for collection in collections:
        analytics = get_analytics_data(collection)
        if not isinstance(analytics, str):  # Not an error
            overview["analytics_data"][collection] = analytics
    
    return overview

# ✅ Enhanced query processing
def process_database_query(user_query):
    """Enhanced processing for analytical queries"""
    query_lower = user_query.lower()
    
    # Get all data for analysis
    database_overview = get_database_overview()
    
    # Basic info queries
    if any(word in query_lower for word in ["collections", "what data", "overview"]):
        return f"📊 Database Overview:\n{json.dumps(database_overview, indent=2, default=str)}"
    
    # Complex analytical queries
    elif any(word in query_lower for word in ["top", "ranking", "best", "filter", "list", "how many", "average", "last", "trend", "improved", "dropped"]):
        analysis_context = process_complex_query(user_query, database_overview.get("analytics_data", {}))
        full_context = f"ANALYTICAL QUERY DETECTED:\n{analysis_context}\n\nFull Database Context:\n{json.dumps(database_overview, indent=2, default=str)}"
        return full_context
    
    # Show specific collection data
    elif "show" in query_lower or "get" in query_lower:
        words = user_query.replace(",", "").split()
        collection_name = None
        
        for i, word in enumerate(words):
            if word.lower() in ["from", "in", "collection"]:
                if i + 1 < len(words):
                    collection_name = words[i + 1]
                    break
        
        if collection_name and collection_name in database_overview.get("analytics_data", {}):
            data = database_overview["analytics_data"][collection_name]
            return f"📄 Complete data from '{collection_name}':\n{json.dumps(data, indent=2, default=str)}"
    
    # Default comprehensive context
    return f"Database context for analysis:\n{json.dumps(database_overview, indent=2, default=str)}"

# ✅ Initialize enhanced conversation
conversation_history = []

database_overview = get_database_overview()
enhanced_system_message = SystemMessage(content=f"""
You are an advanced AI assistant with access to a Firestore database containing student performance data.

Database Overview:
{json.dumps(database_overview, indent=2, default=str)}

You excel at:
📊 PERFORMANCE ANALYSIS:
- Ranking students by rating, problems solved, performance metrics
- Identifying top performers by section, batch, criteria
- Comparative analysis between sections/batches

🔍 FILTERING & SEARCH:
- Finding students matching specific criteria
- Complex multi-condition filtering
- Threshold-based queries (rating above X, problems > Y)

🔁 GROUPING & AGGREGATION:
- Calculating averages, totals, distributions
- Grouping by section, batch, time periods
- Sorting and ranking operations

📅 TIME-BASED ANALYSIS:
- Recent activity analysis (last 7 days, this month)
- Trend identification and pattern recognition
- Inactive user detection

📐 ADVANCED ANALYTICS:
- Multi-criteria analysis
- Performance improvement tracking
- Streak and consistency analysis
- Comparative performance metrics

When users ask analytical questions, provide:
1. Direct answers with specific data
2. Insights and patterns you observe
3. Actionable recommendations
4. Clear formatting with numbers and rankings

Always base your analysis on the actual data structure and fields available in the database.
""")

conversation_history.append(enhanced_system_message)

# ✅ Enhanced main loop
print("🎯 Advanced Student Performance Analytics Chatbot")
print("🔥 Connected to your Firestore Database")
print("📊 Ready for complex analytical queries!")
print("\n💡 Example queries:")
print("   • Who are the top 10 CSE students by rating?")
print("   • List CSE students who solved more than 50 problems")
print("   • What is the average rating in CSE-A vs CSE-B?")
print("   • Show weekly submission trend for CSE-A")
print("\nCommands: 'exit', 'clear', 'overview', 'collections'")
print("-" * 70)

while True:
    try:
        user_input = input("\n🔍 Analytics Query: ").strip()
        
        if not user_input:
            continue
            
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Happy analyzing!")
            break
            
        if user_input.lower() == "clear":
            conversation_history = [enhanced_system_message]
            print("🧹 Analysis session cleared!")
            continue
        
        # Direct commands
        if user_input.lower() in ["overview", "schema"]:
            overview = get_database_overview()
            print(f"📊 Database Analytics Overview:\n{json.dumps(overview, indent=2, default=str)}")
            continue
            
        if user_input.lower() == "collections":
            collections = get_all_collections()
            print(f"📁 Available collections: {collections}")
            continue
        
        # Process analytical queries
        conversation_history.append(HumanMessage(content=user_input))
        
        # Always add database context for analytical queries
        db_context = process_database_query(user_input)
        enhanced_message = f"""
ANALYTICAL QUERY: {user_input}

DATABASE CONTEXT FOR ANALYSIS:
{db_context}

Please provide a comprehensive analysis based on the available data. If specific calculations are needed, work with the data provided above.
"""
        
        conversation_history[-1] = HumanMessage(content=enhanced_message)
        
        # Get AI response
        response = chat.invoke(conversation_history)
        conversation_history.append(AIMessage(content=response.content))
        
        print(f"\n🤖 Analysis: {response.content}")
        
    except KeyboardInterrupt:
        print("\n\n👋 Happy analyzing!")
        break
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please try again or type 'exit' to quit.")