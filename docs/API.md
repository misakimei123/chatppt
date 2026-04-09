# ChatPPT API Documentation

## Overview

ChatPPT is a FastAPI-based service that generates editable PowerPoint presentations from natural language descriptions using multi-agent collaboration.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, no authentication is required. All endpoints are publicly accessible.

---

## Endpoints

### 1. Generate Presentation

**POST** `/generate`

Generate a complete presentation from a natural language brief.

#### Request Body

```json
{
  "brief": "Create a Q2 product launch presentation for executives",
  "documents": [
    {
      "title": "Product Specs",
      "uri": "file:///path/to/specs.pdf",
      "content": "FACT: Product launches in Q2\nSUGGESTION: Include market analysis",
      "source_type": "user_upload"
    }
  ]
}
```

#### Response

```json
{
  "generation_id": "uuid-string",
  "result": {
    "deck": {
      "slides": [
        {
          "slide_id": "slide-1",
          "section_id": "section-1",
          "purpose": "Introduction",
          "title": "Q2 Product Launch",
          "content_blocks": [...],
          "visual_slots": [...]
        }
      ]
    },
    "outline": {...},
    "evidence_pack": {...},
    "manifest": {...},
    "validation_report": {
      "passed": true,
      "issues": []
    },
    "editable_deck_state": {...},
    "pptx_path": "/path/to/generated_deck.pptx"
  }
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"brief": "Create a 5-slide deck about AI trends"}'
```

---

### 2. Edit Slide

**POST** `/edit`

Edit a specific slide in an existing presentation.

#### Request Body

```json
{
  "generation_id": "uuid-string",
  "slide_id": "slide-3",
  "edit_instructions": "Change the title to 'Market Analysis' and add bullet points about competitors"
}
```

#### Response

```json
{
  "success": true,
  "updated_slide": {
    "slide_id": "slide-3",
    "title": "Market Analysis",
    "content_blocks": [...]
  },
  "pptx_path": "/path/to/updated_deck.pptx"
}
```

---

### 3. Get Templates

**GET** `/templates`

List available presentation templates.

#### Response

```json
[
  {
    "template_id": "default",
    "name": "Default Template",
    "layouts": [
      {
        "layout_name": "title_slide",
        "placeholder_dimensions": {...}
      }
    ]
  }
]
```

---

### 4. Generate and Store

**POST** `/generate-and-store`

Generate a presentation and store it in memory for later editing.

#### Request Body

```json
{
  "brief": "Create a sales pitch deck"
}
```

#### Response

```json
{
  "generation_id": "uuid-string",
  "result": {
    "deck": {...},
    "pptx_path": "/path/to/generated_deck.pptx"
  }
}
```

---

## Data Models

### ClarifiedSpec

```json
{
  "topic": "string",
  "audience": "string",
  "use_case": "string",
  "desired_tone": "string",
  "expected_duration_minutes": 8,
  "preferred_language": "en",
  "must_include": ["item1", "item2"],
  "must_avoid": ["item3"],
  "available_materials": [],
  "approval_mode": "manual_review"
}
```

### EvidencePack

```json
{
  "facts": [
    {
      "fact_id": "fact-1",
      "claim": "string",
      "source": {
        "source_type": "web_search",
        "title": "Source Title",
        "uri": "https://example.com",
        "reliability": 0.75
      }
    }
  ],
  "suggestions": [...],
  "constraints": ["Avoid: technical jargon"],
  "search_queries": ["AI trends 2024"]
}
```

### DeckIR

```json
{
  "slides": [
    {
      "slide_id": "slide-1",
      "section_id": "section-1",
      "purpose": "Introduction",
      "title": "Title Text",
      "content_blocks": [
        {
          "block_id": "block-1",
          "kind": "bullet_list",
          "text": "• Point 1\n• Point 2",
          "evidence_refs": ["fact-1"]
        }
      ],
      "visual_slots": [
        {
          "slot_id": "visual-1",
          "kind": "chart",
          "semantic_description": "Bar chart showing growth"
        }
      ],
      "allowed_edit_operations": ["change_title", "add_content"]
    }
  ]
}
```

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Missing required field: brief"
}
```

### 500 Internal Server Error

```json
{
  "detail": "No real LLM provider is configured. Inject a provider implementation before handling live traffic."
}
```

---

## Configuration

Configure the service using environment variables. See `.env.example` for available options:

```bash
# LLM Configuration
DASHSCOPE_API_KEY=sk-your-api-key
LLM_MODEL=qwen-plus
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Application Settings
LOG_LEVEL=INFO
PORT=8000
```

---

## Running Locally

```bash
# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env

# Start server
uvicorn chatppt.app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the create_app factory
python -c "from chatppt.app.main import create_app; import uvicorn; uvicorn.run(create_app())"
```

---

## Testing

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run with coverage
pytest --cov=chatppt
```

---

## OpenAPI Schema

Access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
