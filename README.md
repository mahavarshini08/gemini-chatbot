# LeetCode Chatbot

An intelligent chatbot for analyzing LeetCode student performance data using Gemini AI and LangChain.

## Features

- **Database Analysis**: Query and analyze student performance data
- **Batch & Section Comparison**: Compare different batches and sections by various metrics
- **Student Analytics**: Find top performers, inactive students, and detailed student information
- **Contest Analysis**: Analyze contest participation and leaderboards
- **Advanced Analytics**: Generate insights and trends from the data

## Project Structure

```
gemini-chatbot/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── models.py            # Pydantic models
│   ├── agent/
│   │   ├── __init__.py
│   │   └── chatbot_agent.py # LangChain agent
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API routes
│   ├── services/
│   │   ├── __init__.py
│   │   └── api_service.py   # GraphQL API service
│   └── tools/
│       ├── __init__.py
│       └── base_tools.py    # LangChain tools
├── run.py                   # Application runner
├── requirements.txt          # Python dependencies
└── README.md               # This file
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd gemini-chatbot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   BACKEND_API_URL=http://localhost:4000/graphql
   PORT=3001
   HOST=0.0.0.0
   ```

## Usage

### Running the Application

```bash
python run.py
```

The application will start on `http://localhost:3001` (or the port specified in your `.env` file).

### API Endpoints

- `GET /` - Root endpoint with API information
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /api/v1/health` - Health check
- `GET /api/v1/test-connection` - Test Gemini API connection
- `POST /api/v1/chat` - Main chat endpoint
- `GET /api/v1/conversation-history` - Get conversation history
- `POST /api/v1/clear-history` - Clear conversation history
- `GET /api/v1/tools` - Get available tools information
- `GET /api/v1/example-queries` - Get example queries

### Example Usage

```python
import requests

# Send a chat message
response = requests.post("http://localhost:3001/api/v1/chat", json={
    "message": "Show me all available batches"
})

print(response.json())
```

## Available Tools

The chatbot has access to the following tools:

1. **getAllBatches** - Get all available batches
2. **getStudentsByBatch** - Get all students in a specific batch
3. **getStudent** - Get detailed information about a specific student
4. **getContestLeaderboard** - Get contest leaderboard
5. **getAllContests** - Get all contests for a batch
6. **compareSections** - Compare two sections by metrics
7. **findTopStudents** - Find top students across all batches
8. **findInactiveStudents** - Find inactive students

## Example Queries

### Batch Analysis
- "Show me all available batches"
- "Get all students in batch23-27"
- "Compare secA and secB in batch24-28 by rating"

### Student Analysis
- "Get details for student luvitta-stina in batch23-27"
- "Find top 10 students by rating across all batches"
- "Find inactive students in batch24-28 who haven't participated in the last 7 days"

### Contest Analysis
- "Get all contests for batch23-27"
- "Show contest leaderboard for weekly-contest-460 in batch23-27"

## Configuration

The application uses environment variables for configuration:

- `GOOGLE_API_KEY`: Your Google API key for Gemini
- `BACKEND_API_URL`: URL of your GraphQL backend (default: http://localhost:4000/graphql)
- `PORT`: Port to run the server on (default: 3001)
- `HOST`: Host to bind to (default: 0.0.0.0)

## Development

### Project Structure

The project is organized into clean, modular components:

- **Config**: Centralized configuration management
- **Models**: Pydantic models for request/response schemas
- **Services**: Business logic and external API interactions
- **Tools**: LangChain tools for database operations
- **Agent**: Main chatbot agent with LangChain integration
- **API**: FastAPI routes and endpoints

### Adding New Tools

To add a new tool:

1. Create a new tool class in `app/tools/base_tools.py`
2. Inherit from `BaseTool`
3. Implement the `_run` method
4. Add the tool to the `get_all_tools()` function

### Adding New API Endpoints

To add new endpoints:

1. Add the route to `app/api/routes.py`
2. Create corresponding Pydantic models in `app/models.py` if needed

## Dependencies

Key dependencies include:

- **FastAPI**: Web framework
- **LangChain**: LLM framework
- **Google Generative AI**: Gemini integration
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server
