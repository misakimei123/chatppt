"""
Streamlit Frontend for ChatPPT

Features:
1. Chat input box + history display
2. Generation progress visualization (current executing Agent status)
3. PPT preview (download button + key slide thumbnails)
4. Support for incremental edit instructions like "modify page 3"

Tech Stack: Streamlit + HTTPX calling backend FastAPI
"""

import asyncio
import io
import os
from typing import Any, Optional

import httpx
import streamlit as st

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TIMEOUT_SECONDS = 120


def init_session_state() -> None:
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "generation_id" not in st.session_state:
        st.session_state.generation_id = None
    if "pptx_bytes" not in st.session_state:
        st.session_state.pptx_bytes = None
    if "generation_status" not in st.session_state:
        st.session_state.generation_status = None
    if "current_agent" not in st.session_state:
        st.session_state.current_agent = "idle"


def render_chat_history() -> None:
    """Render chat message history."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show generation status if it's an assistant message with status
            if message["role"] == "assistant" and "status" in message:
                with st.expander("📊 Generation Progress"):
                    st.json(message["status"])


async def send_to_backend(
    prompt: str,
    generation_id: Optional[str] = None,
) -> dict[str, Any]:
    """Send request to backend API."""
    url = f"{BACKEND_URL}/api/v1/generate-and-store"
    
    payload = {"brief": prompt}
    if generation_id:
        payload["generation_id"] = generation_id
    
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


async def edit_slide(
    generation_id: str,
    edit_instruction: str,
) -> dict[str, Any]:
    """Send edit request to backend API."""
    url = f"{BACKEND_URL}/api/v1/edit-slide"
    
    payload = {
        "generation_id": generation_id,
        "edit_instruction": edit_instruction,
    }
    
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


def download_pptx(pptx_bytes: bytes, filename: str = "presentation.pptx") -> None:
    """Provide download button for PPTX file."""
    st.download_button(
        label="📥 Download PowerPoint",
        data=pptx_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


def render_agent_status(current_agent: str) -> None:
    """Render current agent execution status."""
    agent_descriptions = {
        "idle": "⏸️ Idle",
        "clarifier": "🤔 Clarifier - Refining requirements",
        "evidence_builder": "🔍 Evidence Builder - Gathering facts",
        "outline_planner": "📋 Outline Planner - Structuring content",
        "slide_planner": "📝 Slide Planner - Designing slides",
        "renderer": "🎨 Renderer - Creating PPTX",
        "validator": "✅ Validator - Checking quality",
        "complete": "✨ Complete!",
    }
    
    description = agent_descriptions.get(current_agent, f"🔄 {current_agent}")
    st.sidebar.markdown(f"**Current Stage:** {description}")
    
    # Progress bar
    agent_order = ["idle", "clarifier", "evidence_builder", "outline_planner", 
                   "slide_planner", "renderer", "validator", "complete"]
    
    if current_agent in agent_order:
        progress = agent_order.index(current_agent) / (len(agent_order) - 1)
        st.sidebar.progress(progress)


def main() -> None:
    """Main Streamlit application."""
    st.set_page_config(
        page_title="ChatPPT",
        page_icon="📊",
        layout="wide",
    )
    
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Settings")
        
        # Backend URL configuration
        backend_url_input = st.text_input(
            "Backend URL",
            value=BACKEND_URL,
            help="URL of the ChatPPT backend API",
        )
        
        if backend_url_input != BACKEND_URL:
            st.session_state.backend_url = backend_url_input
            st.rerun()
        
        st.divider()
        
        # Render agent status
        render_agent_status(st.session_state.current_agent)
        
        st.divider()
        
        # Info section
        st.markdown("""
        ### 💡 Tips
        - Use natural language to describe your presentation
        - Be specific about audience and use case
        - Request edits by saying "modify page X"
        """)
    
    # Main content
    st.title("📊 ChatPPT")
    st.markdown("Generate professional presentations using AI-powered multi-agent collaboration")
    
    # Render chat history
    render_chat_history()
    
    # Chat input
    if prompt := st.chat_input("Describe your presentation..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Check if this is an edit request
        is_edit_request = any(keyword in prompt.lower() for keyword in 
                             ["modify", "change", "update", "edit", "page", "slide"])
        
        # Process request
        with st.chat_message("assistant"):
            status_container = st.empty()
            status_container.info("🔄 Processing your request...")
            
            try:
                if is_edit_request and st.session_state.generation_id:
                    # Handle edit request
                    st.session_state.current_agent = "edit_parser"
                    status_container.info("✏️ Parsing edit instruction...")
                    
                    result = asyncio.run(edit_slide(
                        generation_id=st.session_state.generation_id,
                        edit_instruction=prompt,
                    ))
                    
                    st.session_state.current_agent = "complete"
                    status_container.success("✅ Edit applied successfully!")
                    
                    response_text = "I've updated the presentation based on your request."
                    
                else:
                    # Handle new generation request
                    st.session_state.current_agent = "clarifier"
                    
                    result = asyncio.run(send_to_backend(prompt))
                    
                    st.session_state.generation_id = result.get("generation_id")
                    st.session_state.current_agent = "complete"
                    
                    status_container.success("✅ Presentation generated successfully!")
                    response_text = f"Your presentation is ready! Generation ID: `{result.get('generation_id')}`"
                
                # Add assistant response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "status": result,
                })
                
                # Show result details
                with st.expander("📄 View Generation Details"):
                    st.json(result)
                
                # Try to download PPTX if available
                if st.session_state.generation_id:
                    try:
                        # Fetch the generated PPTX
                        async def fetch_pptx():
                            url = f"{BACKEND_URL}/api/v1/download/{st.session_state.generation_id}"
                            async with httpx.AsyncClient(timeout=30) as client:
                                response = await client.get(url)
                                if response.status_code == 200:
                                    return response.content
                            return None
                        
                        pptx_bytes = asyncio.run(fetch_pptx())
                        if pptx_bytes:
                            st.session_state.pptx_bytes = pptx_bytes
                            download_pptx(pptx_bytes)
                    except Exception as e:
                        st.warning(f"Could not fetch PPTX preview: {e}")
                
                st.rerun()
                
            except httpx.HTTPError as e:
                error_msg = f"❌ API Error: {str(e)}"
                status_container.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })
                st.session_state.current_agent = "idle"
            except Exception as e:
                error_msg = f"❌ Unexpected error: {str(e)}"
                status_container.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })
                st.session_state.current_agent = "idle"
    
    # Show download button if PPTX is available
    if st.session_state.pptx_bytes:
        with st.sidebar:
            st.markdown("### 📥 Download")
            download_pptx(st.session_state.pptx_bytes)


if __name__ == "__main__":
    main()
