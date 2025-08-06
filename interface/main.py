
import streamlit as st
import os
import sys
import tempfile
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.document_parser import parse_pdf, validate_pdf
from app.index_builder import IndexBuilder
from app.query_engine import QueryEngine
from llama_index.core import VectorStoreIndex
import logging
from typing import List, Dict, Any
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Agentic RAG Chatbot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to match the dark theme from the image ---
st.markdown("""
<style>
    /* Set the base background color for the main app area */
    .stApp {
        background-color: #0F172A; /* Dark Slate Blue */
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FFFFFF; /* White text */
        text-align: center;
        margin-bottom: 2rem;
    }
    .upload-section {
        background-color: #1E293B; /* Darker Slate */
        padding: 2rem;
        border-radius: 1rem;
        margin: 1rem 0;
        border: 1px solid #334155;
    }
    /* User's question bubble - Light Blue */
    .chat-question {
        background-color: #E0F2FE; /* Light Cyan */
        color: #0c4a6e; /* Dark Cyan text for readability */
        padding: 1rem;
        border-radius: 0.75rem; /* More rounded corners */
        margin: 0.5rem 0;
        border-left: 5px solid #3B82F6; /* Brighter Blue border */
    }
    /* Assistant's answer bubble - Light Lavender */
    .chat-answer {
        background-color: #F3E8FF; /* Light Lavender */
        color: #581c87; /* Dark Purple text for readability */
        padding: 1rem;
        border-radius: 0.75rem; /* More rounded corners */
        margin: 0.5rem 0;
        border-left: 5px solid #9333EA; /* Brighter Purple border */
    }
    /* Source document snippets - Dark themed */
    .source-document {
        background-color: #1F2937; /* Dark Gray */
        padding: 0.8rem;
        border-radius: 0.5rem;
        margin: 0.3rem 0;
        border-left: 3px solid #0D9488; /* Teal border */
        font-size: 0.9rem;
    }
    /* Confidence scores */
    .confidence-high { color: #22C55E; font-weight: bold; } /* Bright Green from image */
    .confidence-medium { color: #F59E0B; font-weight: bold; } /* Amber */
    .confidence-low { color: #EF4444; font-weight: bold; } /* Red */

    /* General text color for dark theme */
    div, p, span, li {
        color: #E2E8F0; /* Light Slate Gray for text */
    }
    /* Headers and titles */
    h1, h2, h3 {
        color: #FFFFFF;
    }
    /* Sidebar styling */
    .st-emotion-cache-16txtl3 {
        background-color: #1E293B; /* Dark Slate for sidebar */
    }
    /* Ensure chat text inside bubbles has the correct color */
    .chat-question p, .chat-question li {
        color: #0c4a6e;
    }
    .chat-answer p, .chat-answer li {
        color: #581c87;
    }
    /* Change button style to be more visible on dark theme */
    .stButton>button {
        border-color: #334155;
        background-color: #334155;
        color: #FFFFFF;
    }
    .stButton>button:hover {
        border-color: #475569;
        background-color: #475569;
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)


def get_file_hash(file_content: bytes) -> str:
    """Generate a hash for file content to detect duplicates."""
    return hashlib.md5(file_content).hexdigest()

def process_uploaded_files(uploaded_files: List[Any]) -> Dict[str, Any]:
    """Process multiple uploaded files, avoiding duplicates already in the DB."""
    results = {
        'documents': [], 'errors': [],
        'stats': {'total_files': len(uploaded_files), 'successful_files': 0, 'failed_files': 0, 'total_pages': 0, 'total_size': 0}
    }
    existing_files_in_db = st.session_state.get("indexed_files", [])
    
    with tempfile.TemporaryDirectory() as temp_dir:
        for uploaded_file in uploaded_files:
            if uploaded_file.name in existing_files_in_db:
                results['errors'].append({'file_name': uploaded_file.name, 'error': 'File already exists in the database. Skipped.'})
                results['stats']['failed_files'] += 1
                continue
            try:
                file_content = uploaded_file.getbuffer()
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_path, "wb") as f: f.write(file_content)
                if not validate_pdf(temp_path):
                    results['errors'].append({'file_name': uploaded_file.name, 'error': 'Invalid PDF file'})
                    results['stats']['failed_files'] += 1
                    continue
                docs = parse_pdf(temp_path)
                file_size = len(file_content)
                for doc in docs:
                    doc.metadata.update({'file_name': uploaded_file.name, 'file_size': file_size, 'upload_timestamp': datetime.datetime.now().isoformat()})
                results['documents'].extend(docs)
                results['stats']['successful_files'] += 1
                results['stats']['total_pages'] += len(docs)
                results['stats']['total_size'] += file_size
                logger.info(f"Successfully parsed {uploaded_file.name} for indexing.")
            except Exception as e:
                error_msg = f"Error processing {uploaded_file.name}: {str(e)}"
                results['errors'].append({'file_name': uploaded_file.name, 'error': str(e)})
                results['stats']['failed_files'] += 1
                logger.error(error_msg)
    return results

def display_source_documents(source_docs: List[Dict]):
    """Display source documents with snippets."""
    if not source_docs: return
    st.markdown("<h4>📚 Source Documents:</h4>", unsafe_allow_html=True)
    for i, doc in enumerate(source_docs[:3]):
        st.markdown(f"""
        <div class="source-document">
            <strong>📄 {doc.get('file_name', 'Unknown')} - Page {doc.get('page', 1)}</strong> (Relevance: {doc.get('relevance_score', 0.0):.2f})<br>
            <em>"{doc.get('text_snippet', '')}"</em>
        </div>
        """, unsafe_allow_html=True)

def on_submit_query():
    """Callback function to process user query."""
    user_query = st.session_state.user_input
    if user_query and st.session_state.get("chat_engine"):
        with st.spinner("🤔 Analyzing documents..."):
            response = st.session_state["chat_engine"].query(user_query)
            st.session_state["chat_history"].append({**response, "question": user_query})

def initialize_chat_engine(memory_limit, similarity_top_k):
    """Initializes the chat engine and stores it in session state."""
    if "chat_engine" in st.session_state and st.session_state["chat_engine"]:
        return # Already initialized
    try:
        with st.spinner("🚀 Initializing chat engine..."):
            index_builder = IndexBuilder()
            index = VectorStoreIndex.from_vector_store(index_builder.vector_store)
            chat_engine = QueryEngine(index=index, memory_token_limit=memory_limit, similarity_top_k=similarity_top_k)
            st.session_state["chat_engine"] = chat_engine
            logger.info("Chat engine initialized successfully.")
    except Exception as e:
        st.error(f"❌ Failed to initialize chat engine: {e}")
        logger.error(f"Chat engine initialization failed: {e}")

def main():
    st.markdown('<h1 class="main-header">🧠 Agentic RAG Chatbot</h1>', unsafe_allow_html=True)

    # --- Session State Initialization ---
    if "db_checked" not in st.session_state:
        st.session_state["db_checked"] = False
        st.session_state["chat_engine"] = None
        st.session_state["chat_history"] = []
        st.session_state["indexed_files"] = []

    # --- Sidebar ---
    with st.sidebar:
        st.header("⚙️ Configuration")
        chunk_size = st.slider("Chunk Size", 256, 1024, 512, 128, help="Size of text chunks for new documents")
        memory_limit = st.slider("Memory Token Limit", 1000, 5000, 3000, 500, help="Max tokens in conversation memory")
        similarity_top_k = st.slider("Similarity Search Results", 1, 30, 15, 1, help="Number of similar chunks to retrieve")

        st.header("🔄 Actions")
        if st.button("🗑️ Clear Chat Memory"):
            if "chat_engine" in st.session_state and st.session_state["chat_engine"]:
                st.session_state["chat_engine"].clear_memory()
            st.session_state["chat_history"] = []
            st.success("Chat memory cleared!")
            st.rerun()

        if st.button("⚠️ Clear Database & Reset", type="primary"):
            with st.spinner("Deleting all documents from database..."):
                try:
                    builder = IndexBuilder()
                    builder.delete_all_documents()
                    for key in list(st.session_state.keys()): del st.session_state[key]
                    st.success("Database cleared. Refreshing...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to clear database: {e}")

        # --- Document & Memory Stats ---
        if st.session_state.get("indexed_files"):
            st.header("📊 Knowledge Base")
            st.metric("Indexed Documents", len(st.session_state["indexed_files"]))
            with st.expander("View Indexed Files", expanded=True):
                for name in st.session_state["indexed_files"]:
                    st.write(f"• {name}")
        
        if st.session_state.get("chat_engine"):
            memory_stats = st.session_state["chat_engine"].get_memory_stats()
            if "error" not in memory_stats:
                st.metric("Memory Messages", memory_stats.get('messages_count', 0))

    # --- Initial DB Check ---
    if not st.session_state["db_checked"]:
        with st.spinner("Connecting to database..."):
            try:
                builder = IndexBuilder()
                existing_files = builder.get_existing_document_names()
                st.session_state["indexed_files"] = existing_files
                st.session_state["db_checked"] = True 
                if existing_files:
                    st.toast(f"Found {len(existing_files)} documents in the database.", icon="📚")
                    st.rerun() 
                else:
                    st.toast("No existing documents found.", icon="📄")
            except Exception as e:
                st.error(f"❌ Could not connect to Neo4j. Check settings. Error: {e}")
                st.session_state["db_checked"] = True 
    
    # --- Chat Engine Initialization Logic ---
    if st.session_state.get("indexed_files") and not st.session_state.get("chat_engine"):
        initialize_chat_engine(memory_limit, similarity_top_k)

    # --- File Upload & Processing Section ---
    upload_label = "Add More Documents" if st.session_state.get("chat_engine") else "Upload Documents to Begin"
    with st.expander(upload_label, expanded=not st.session_state.get("indexed_files")):
        uploaded_files = st.file_uploader("Select PDF files", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed")
        if st.button("🔄 Process Uploaded Files", type="primary", disabled=not uploaded_files):
            with st.spinner("Processing documents..."):
                results = process_uploaded_files(uploaded_files)
                if results['errors']:
                    st.subheader("⚠️ Processing Issues")
                    for error in results['errors']: st.warning(f"**{error['file_name']}**: {error['error']}")
                if results['documents']:
                    with st.spinner("Adding new documents to the search index..."):
                        try:
                            builder = IndexBuilder(chunk_size=chunk_size)
                            builder.build_index(results['documents'])
                            st.success(f"✅ Added {results['stats']['successful_files']} new document(s)!")
                            st.session_state['db_checked'] = False 
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error building index: {e}")
                elif not results['errors']:
                    st.info("No new files to process.")

    # --- Chat Interface ---
    if st.session_state.get("chat_engine"):
        st.header("💬 Chat with your Documents")
        st.text_input("Ask a question:", key="user_input", on_change=on_submit_query, placeholder="e.g., What are the registration requirements?")
        
        # Display chat history
        if st.session_state["chat_history"]:
            st.subheader("📝 Conversation History")
            for i, chat in enumerate(reversed(st.session_state["chat_history"])):
                # --- MODIFIED: Use new icons and styling ---
                st.markdown(f'<div class="chat-question"><strong>🧐 You:</strong> {chat["question"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="chat-answer"><strong>🤖 Assistant:</strong><br>{chat["answer"]}</div>', unsafe_allow_html=True)
                
                # Confidence and Citations
                confidence = chat['confidence']
                conf_class = "high" if confidence > 0.7 else "medium" if confidence > 0.4 else "low"
                st.markdown(f"<p class='confidence-{conf_class}'>Confidence: {confidence:.2f}</p>", unsafe_allow_html=True)
                
                if chat.get('source_documents'):
                    with st.expander(f"📚 View Source Documents ({len(chat['source_documents'])} found)"):
                        display_source_documents(chat['source_documents'])
                st.markdown("<hr style='border-top: 1px solid #334155;'>", unsafe_allow_html=True)
    else:
        st.info("📄 Please upload PDF documents to build a knowledge base and start chatting.")

if __name__ == "__main__":
    main()