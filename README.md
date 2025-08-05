# 🚀 Enhanced LeetCode Chatbot

An intelligent chatbot that can answer complex queries requiring data from multiple collections with smart data access patterns.

## ✨ Enhanced Features

### 🔗 Multi-Collection Queries
The chatbot can fetch data from multiple collections in a single query and automatically detects when multiple collections are needed:
- **Batches Collection**: Only accessed when needed for batch/section queries
- **Contest Questions Collection**: Only accessed for contest details (not student performance)
- **Students Collection**: Contains all student details with performance in latest 5 contests
- **Automatic Detection**: The agent determines when a query requires multiple collections
- **All-Batches Default**: When no specific batch is mentioned, automatically provides data across ALL batches

### 🧠 Smart Data Access Patterns
- **Batches**: Only fetched when asked about number of batches, batch names, or number of sections
- **Contests**: Only fetched when asked about contest details (names, questions, etc.)
- **Students**: Contains all student information including performance in latest 5 contests only

### 📊 Enhanced Query Capabilities

#### 1. Total Sections Across All Batches
```
"How many sections are there in total across all batches?"
```
- Fetches from batches collection
- Sums up section counts from all batches
- Provides breakdown by batch

#### 2. Contest Information
```
"What contests are available?"
"What questions were asked in the contests?"
```
- Fetches contest details only (same across all batches)
- Does not access student performance data
- Provides contest names, questions, and general information
- No batch specification needed since contest details are identical across all batches

#### 3. Student Performance (Limited to Latest 5 Contests)
```
"What is the performance of student john-doe in batch24-25?"
```
- Shows student details and latest 5 contests only
- Clearly informs about the 5-contest limitation
- Provides comprehensive student information

#### 4. Top Students (Both Rankings)
```
"Show me top 50 students in batch24-25"
"Who are the top 10 students?"  # Automatically across all batches
```
- Always provides both rating and problems solved rankings
- Can work for specific batches or across all batches
- Automatically defaults to all batches when no specific batch mentioned
- Shows batch information for each student when querying across all batches

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Google API Key for Gemini
- Backend API URL (GraphQL endpoint)

### Environment Variables
Create a `.env` file:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   BACKEND_API_URL=http://localhost:4000/graphql
   ```

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run the chatbot
python run.py
```

## 🎯 Usage Examples

### 1. Batch and Section Queries
```bash
# Get total sections across all batches
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "How many sections are there in total across all batches?"}'

# Get batch information
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What batches are available and how many sections do they have?"}'
```

### 2. Contest Information Queries
```bash
# Get contest information (same across all batches)
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What contests are available?"}'

# Get contest questions
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What questions were asked in the contests?"}'
```

### 3. Student Performance Queries
```bash
# Get student performance (latest 5 contests only)
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the performance of student john-doe in batch24-25?"}'
```

### 4. Top Students Queries
```bash
# Get top students by both metrics (specific batch)
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me top 50 students in batch24-25"}'

# Get top students across all batches (automatic)
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Who are the top 10 students?"}'
```

## 📊 API Endpoints

### Chat Endpoint
```http
POST /api/v1/chat
Content-Type: application/json

{
  "message": "Your question here"
}
```

Response:
```json
{
  "success": true,
  "response": "Answer from the chatbot",
  "tools_used": 2,
  "unique_tools": 2,
  "tool_names": ["getBatchesInfo", "findTopStudentsEnhanced"],
  "multi_collection": true,
  "agent_steps": [...]
}
```

### Statistics Endpoint
```http
GET /api/v1/stats
```

### Tools Information
```http
GET /api/v1/tools
```

### Agent Capabilities
```http
GET /api/v1/capabilities
```

## 🔧 Available Tools

### 1. `getBatchesInfo`
- **Purpose**: Get comprehensive batch information
- **Use when**: Asked about number of batches, batch names, or number of sections
- **Input**: None required
- **Output**: Total batches, total sections, breakdown by batch

### 2. `getContestInfo`
- **Purpose**: Get contest information (not student performance)
- **Use when**: Asked about contest details, names, questions
- **Input**: No input required (contest details are same across all batches)
- **Output**: Contest information, questions, general details

### 3. `getStudentPerformance`
- **Purpose**: Get student performance with latest 5 contests
- **Use when**: Asked about specific student performance
- **Input**: 'batch,username' (e.g., 'batch24-25,john-doe')
- **Output**: Student details with latest 5 contests only

### 4. `findTopStudentsEnhanced`
- **Purpose**: Find top students by both rating and problems solved
- **Use when**: Asked about top students
- **Input**: 'limit,batch' (e.g., '50,batch24-25' or '10,all')
- **Output**: Both rating and problems solved rankings

### 5. `getTotalSections`
- **Purpose**: Get total sections across all batches
- **Use when**: Asked about total sections
- **Input**: None required
- **Output**: Total sections with breakdown

### 6. `multiCollectionQuery`
- **Purpose**: Handle complex cross-collection queries
- **Use when**: Complex queries requiring multiple collections
- **Input**: Natural language question
- **Output**: Comprehensive answer using multiple tools

## 🚨 Data Limitations

### Student Performance
- **Limitation**: Only latest 5 contests available
- **Reason**: Database stores only recent contest data
- **Response**: System clearly informs about this limitation

### Contest Information
- **Access Pattern**: Only for contest details, not student performance
- **Reason**: Separate concerns for better performance
- **Benefit**: Faster queries when only contest info is needed

### Batch Information
- **Access Pattern**: Only when needed for batch/section queries
- **Reason**: Optimize data access
- **Benefit**: Reduced unnecessary API calls

## 🎨 Web Interface

The chatbot includes a beautiful web interface at `http://localhost:8000` with:

- **Real-time chat**: Interactive chat interface
- **Enhanced capabilities display**: Shows all available features
- **Multi-collection indicators**: Shows when queries use multiple collections
- **Responsive design**: Works on desktop and mobile

## 🔍 Query Examples

### Simple Queries
```
"How many batches are there?"
"What are the batch names?"
"How many sections are in batch24-25?"
```

### Complex Queries
```
"How many sections are there in total across all batches?"
"Show me top 50 students in batch24-25"
"What contests are available?"
"What is the performance of student john-doe in batch24-25?"
"Show me top 10 students"  # Automatically across all batches
```

### Multi-Collection Queries
```
"Compare the performance of top students across different batches"
"Show me contest information and top performers for batch24-25"
```

## 🛠️ Development

### File Structure
```
app/
├── agent/
│   └── agent.py                   # Enhanced agent with multi-collection support
├── tools/
│   └── tools.py                   # Enhanced tools for smart data access
├── services/
│   └── api_service.py             # API service for backend communication
└── main.py                        # Enhanced FastAPI application

run.py                             # Chatbot runner
ENHANCED_README.md                 # This file
```

### Adding New Tools
1. Create new tool class in `app/tools/tools.py`
2. Add to `get_enhanced_tools()` function
3. Update agent prompt in `app/agent/agent.py`
4. Test with various queries

### Extending Capabilities
1. Modify `EnhancedMultiCollectionQueryTool` in `app/tools/tools.py` for new query patterns
2. Add new data access patterns in the agent prompt in `app/agent/agent.py`
3. Update the capabilities endpoint response

## 🚀 Performance Benefits

### Smart Data Access
- **Reduced API calls**: Only fetch data when needed
- **Faster responses**: Optimized data access patterns
- **Better resource usage**: Efficient collection access

### Multi-Collection Optimization
- **Automatic detection**: Agent determines when multiple collections are needed
- **Single query responses**: Complex questions answered efficiently
- **Reduced latency**: Multiple tools in sequence
- **Better user experience**: Comprehensive answers
- **Intelligent tool selection**: Uses the most appropriate tools for each query

## 🔧 Troubleshooting

### Common Issues

1. **API Connection Error**
   - Check `BACKEND_API_URL` in `.env`
   - Ensure backend server is running

2. **Google API Key Error**
   - Verify `GOOGLE_API_KEY` in `.env`
   - Check API key permissions

3. **Tool Execution Error**
   - Check backend API responses
   - Verify data format expectations

### Debug Endpoints
```http
GET /api/v1/test-connection    # Test API connectivity
GET /api/v1/stats              # View usage statistics
GET /api/v1/capabilities       # Check agent capabilities
```

## 📈 Monitoring

### Usage Statistics
- Total requests processed
- Average tools per request
- Multi-collection query rate
- Tool usage patterns

### Performance Metrics
- Response times
- Tool execution success rates
- Error rates and types

## 🤝 Contributing

1. Follow the existing code structure
2. Add comprehensive error handling
3. Include proper documentation
4. Test with various query patterns
5. Update this README for new features

## 📄 License

This project is part of the LeetCode tracking system. See the main project license for details. 