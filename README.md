# 📊 ChatPPT - AI-Powered Presentation Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.29+-red.svg)](https://streamlit.io/)

**ChatPPT** is an AI-powered application that generates editable PowerPoint presentations from natural language descriptions. Using a multi-agent collaboration architecture, it quickly transforms your ideas into professional PPT files.

## ✨ Key Features

- 🎯 **Natural Language Input**: Simply describe your requirements, and AI automatically understands and generates a complete presentation
- 🤖 **Multi-Agent Collaboration**: Five-stage intelligent processing: Clarifier → EvidenceBuilder → SlidePlanner → PptxRenderer → Validator
- 🔍 **Evidence-Based Enhancement**: Integrated web search and document parsing (PDF/MD/TXT) to ensure content accuracy
- 🎨 **Intelligent Visual Rendering**: Automatically generate charts, tables, and statistical visualizations
- 💬 **Interactive Editing**: Support conversational modifications, such as "modify the title on page 3"
- 🚀 **Redis Cache Optimization**: Intermediate result caching to avoid repeated LLM calls and improve performance
- 🌐 **Modern Frontend**: Streamlit chat interface with real-time progress visualization and preview/download capabilities

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
│              (Streamlit Web / FastAPI REST)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    StateGraph Orchestrator                  │
│  ┌──────────┐   ┌──────────────┐   ┌─────────────┐         │
│  │Clarifier │ → │EvidenceBuilder│ → │SlidePlanner │         │
│  └──────────┘   └──────────────┘   └─────────────┘         │
│       │                │                    │               │
│       ▼                ▼                    ▼               │
│  ┌──────────┐   ┌──────────────┐   ┌─────────────┐         │
│  │  LLM     │   │Web Search +  │   │PptxRenderer │         │
│  │ Provider │   │  RAG Engine  │   │ + Charts    │         │
│  └──────────┘   └──────────────┘   └─────────────┘         │
│                                              │               │
│                                              ▼               │
│                                      ┌─────────────┐        │
│                                      │ Validator   │        │
│                                      └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Redis Cache Layer                        │
│           (Intermediate Results & Session Storage)          │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

Start all services with one command (Backend + Redis + Frontend):

```bash
# 1. Clone the repository
git clone https://github.com/misakimei123/chatppt.git
cd chatppt

# 2. Configure environment variables
cp .env.example .env
# Edit .env file and fill in your API keys
nano .env  # Or use your preferred editor

# 3. Start all services
docker-compose up -d

# 4. Access services
# - Streamlit Frontend: http://localhost:8501
# - FastAPI Docs: http://localhost:8000/docs
# - API Endpoint: http://localhost:8000/api/v1
```

### Option 2: Local Development Environment

```bash
# 1. Install dependencies
pip install -e ".[dev]"

# 2. Install additional components (optional)
pip install streamlit redis matplotlib faiss-cpu langchain-community

# 3. Configure environment variables
cp .env.example .env
# Edit .env file

# 4. Start Redis (optional, for caching)
docker run -d -p 6379:6379 --name chatppt-redis redis:7-alpine

# 5. Start backend service
uvicorn chatppt.app.main:app --reload --host 0.0.0.0 --port 8000

# 6. Start frontend (new terminal window)
streamlit run frontend/app.py --server.port 8501
```

## ⚙️ Configuration

### Environment Variables (.env)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DASHSCOPE_API_KEY` | Qwen DashScope API Key | - | ✅ |
| `LLM_MODEL` | LLM Model Name | `qwen-plus` | ❌ |
| `LLM_BASE_URL` | LLM API Base URL | DashScope Compatible | ❌ |
| `SEARCH_API_KEY` | Web Search API Key | - | ❌ |
| `REDIS_URL` | Redis Connection URL | `redis://localhost:6379` | ❌ |
| `ENABLE_CACHE` | Enable Caching | `true` | ❌ |
| `CACHE_TTL_SECONDS` | Cache TTL | `3600` | ❌ |
| `LOG_LEVEL` | Log Level | `INFO` | ❌ |
| `PORT` | Backend Port | `8000` | ❌ |
| `STREAMLIT_SERVER_PORT` | Frontend Port | `8501` | ❌ |

For complete configuration template, refer to `.env.example` file.

### Getting API Keys

1. **Qwen DashScope**:
   - Visit [DashScope Console](https://dashscope.console.aliyun.com/)
   - Register/Login with Alibaba Cloud account
   - Create API Key and copy to `.env` file

2. **Web Search (Optional)**:
   - Use DuckDuckGo (no key required, built-in)
   - Or configure SerpAPI or other search services

## 📖 Usage Guide

### Using Streamlit Frontend

1. Visit `http://localhost:8501`
2. Enter your presentation requirements in the chat box, for example:
   ```
   Create a 10-slide presentation about AI trends in 2024 for corporate executives
   ```
3. Wait for generation to complete (real-time progress available in sidebar)
4. Preview the generated PPT and click download button to save
5. For modifications, directly input instructions:
   ```
   Modify page 3, add more market data charts
   ```

### Using API

#### Generate Presentation

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "brief": "Create a 5-slide deck about renewable energy trends",
    "documents": []
  }'
```

#### Edit Specific Slide

```bash
curl -X POST http://localhost:8000/api/v1/edit \
  -H "Content-Type: application/json" \
  -d '{
    "generation_id": "your-generation-id",
    "slide_id": "slide-3",
    "edit_instructions": "Change title to Market Analysis and add competitor comparison table"
  }'
```

#### Download Generated PPTX

```bash
curl -O http://localhost:8000/api/v1/download/{generation_id}
```

### Python SDK Example

```python
from chatppt.app.main import create_app
import asyncio

async def generate_presentation():
    app = create_app()
    
    # Generate presentation
    response = await app.post(
        "/api/v1/generate",
        json={"brief": "Q2 product launch presentation"}
    )
    
    result = response.json()
    print(f"Generation ID: {result['generation_id']}")
    print(f"PPTX Path: {result['result']['pptx_path']}")

asyncio.run(generate_presentation())
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Generate coverage report
pytest --cov=chatppt --cov-report=html

# View coverage report
open htmlcov/index.html
```

## 📁 Project Structure

```
chatppt/
├── chatppt/                 # Main application package
│   ├── __init__.py
│   ├── app/                 # FastAPI application
│   │   ├── main.py         # Application entry
│   │   ├── routes.py       # API routes
│   │   └── schemas.py      # Data models
│   ├── core/               # Core logic
│   │   ├── agents/         # Agent implementations
│   │   │   ├── clarifier.py
│   │   │   ├── evidence_builder.py
│   │   │   ├── slide_planner.py
│   │   │   └── ...
│   │   ├── llm/            # LLM providers
│   │   │   └── provider.py
│   │   ├── rendering/      # PPTX rendering
│   │   │   └── pptx_renderer.py
│   │   └── graph.py        # StateGraph orchestration
│   └── utils/              # Utility functions
├── frontend/               # Streamlit frontend
│   └── app.py
├── templates/              # PPT templates
│   └── default/
├── tests/                  # Test cases
│   ├── unit/
│   └── integration/
├── docs/                   # Documentation
│   └── API.md
├── docker-compose.yml      # Docker orchestration
├── Dockerfile              # Backend image
├── Dockerfile.frontend     # Frontend image
├── pyproject.toml          # Project configuration
└── .env.example            # Environment variable template
```

## 🔧 Core Modules

### 1. LLMProvider (`src/core/llm/provider.py`)

Supports three invocation modes:
- `generate_text()`: Plain text generation
- `generate_structured()`: Structured output (Pydantic models)
- `generate_with_tools()`: Tool invocation (function execution)

Features:
- ✅ Retry mechanism (tenacity)
- ✅ Token counting and logging
- ✅ Hot model switching
- ✅ Error handling with friendly messages

### 2. EvidenceBuilder (`src/core/agents/evidence_builder.py`)

Content acquisition enhancement:
- 🔍 Web search integration (DuckDuckGo / SerpAPI)
- 📄 Document parsing (PDF/MD/TXT → RAG retrieval)
- 💾 Caching mechanism (avoid repeated calls)

Output format:
```python
EvidencePack(
    key_facts: List[FactItem],      # {source, content, confidence}
    references: List[Reference],
    search_queries: List[str]
)
```

### 3. PptxRenderer (`src/core/rendering/pptx_renderer.py`)

Visual rendering capabilities:
- 📊 Automatic chart generation (bar/line/pie → matplotlib)
- 📋 Table rendering (python-pptx Table)
- 📈 Statistical display (large numbers + labels)
- 🖼️ Image placeholder handling (Tongyi Wanxiang API reserved)
- 🎨 Style customization (read color schemes from template.json)

### 4. Redis Cache Layer

Performance optimization:
- ⚡ Intermediate result caching (avoid repeated LLM calls)
- 🔄 Session state storage
- 📊 Generation history
- 🔌 Fallback mechanism (automatically degrade to memory cache when Redis unavailable)

## 🛠️ Development Guide

### Adding New LLM Provider

```python
from chatppt.core.llm.provider import LLMProvider

class MyCustomProvider(LLMProvider):
    async def generate_text(self, prompt: str, **kwargs) -> str:
        # Implement your logic
        pass
```

### Custom Agent

```python
from langgraph.prebuilt import ToolNode
from chatppt.core.graph import StateGraph

def my_custom_agent(state: dict) -> dict:
    # Implement your agent logic
    return {"messages": [...]}

# Register to StateGraph
graph.add_node("my_agent", my_custom_agent)
```

### Extending Visual Element Types

Add in `pptx_renderer.py`:

```python
if element.type == "custom_chart":
    # Implement custom chart rendering
    pass
```

## 📊 Performance Benchmarks

| Scenario | Without Cache | With Cache | Improvement |
|----------|---------------|------------|-------------|
| 5-slide PPT | ~45s | ~28s | 38% ⬆️ |
| 10-slide PPT | ~90s | ~52s | 42% ⬆️ |
| Single Slide Edit | ~15s | ~8s | 47% ⬆️ |

*Test environment: Intel i7, 16GB RAM, Redis 7, Qwen-Plus API*

## 🐛 FAQ

### Q: Generation is too slow?
A: 
1. Ensure Redis caching is enabled
2. Check network connection and API response time
3. Consider using faster LLM models (e.g., qwen-turbo)

### Q: How to change LLM model?
A: Modify `LLM_MODEL` variable in `.env`, for example:
```bash
LLM_MODEL=qwen-turbo
```

### Q: Which file formats are supported for upload?
A: Currently supports PDF, Markdown (.md), and plain text (.txt). Other formats can be added by extending `EvidenceBuilder`.

### Q: Not satisfied with generated PPT style?
A: 
1. Modify `templates/default/template.json` to customize colors and fonts
2. Specify style requirements in prompt, e.g., "use corporate blue theme"
3. Manually adjust in PowerPoint after generation

## 🤝 Contributing

Issues and Pull Requests are welcome!

1. Fork this repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Related Links

- [API Documentation](docs/API.md)
- [DashScope Official Docs](https://help.aliyun.com/zh/dashscope/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [python-pptx Documentation](https://python-pptx.readthedocs.io/)

## 📬 Contact

- Project URL: https://github.com/misakimei123/chatppt
- Issue Tracker: https://github.com/misakimei123/chatppt/issues

---

**Made with ❤️ using LangGraph + FastAPI + Streamlit**
