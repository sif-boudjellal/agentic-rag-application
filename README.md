
# 🧠 Agentic RAG System - Professional Document Q&A

A production-ready Retrieval-Augmented Generation (RAG) system that enables users to upload documents, interact through a chat interface, and receive accurate answers with precise citations including file names and page numbers.

## 🚀 Demo Features

### ✅ Core Functionality
- **📄 Multi-Document Upload**: Support for multiple PDF documents with robust extraction of Arabic text and tables.
- **💾 Persistent Knowledge Base**: Indexed documents are stored in Neo4j, allowing instant access in future sessions.
- **📚 Accurate Citations**: Every answer is supported by precise file name and page number references.
- **🧠 Conversation Memory**: Ask contextual follow-up questions using a built-in chat memory.
- **🛡️ No Hallucination**: Provides a clear "No answer found" response when information is not in the source documents.
- **🌐 Arabic Language Support**: Full support for parsing and responding in Arabic.
- **🔄 Smart Batch Processing**: Efficiently processes multiple files, automatically skipping duplicates already in the database.
- **📊 Cross-Document Queries**: Ask complex questions that require synthesizing information from all uploaded documents.


### ✅ Technical Stack
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Parser** | LlamaParse | Document extraction with Arabic & table support. |
| **Indexing** | LlamaIndex | Vector indexing and retrieval orchestration. |
| **Embeddings** | OpenAI (`text-embedding-3-large`) | State-of-the-art text vectorization. |
| **Vector DB** | Neo4j | Persistent, high-performance vector storage. |
| **LLM** | Gemini (`gemini-1.5-flash`) | Advanced reasoning and response generation. |
| **Query Engine**| `CitationQueryEngine` | Generates responses with direct source citations. |
| **Memory** | `ChatMemoryBuffer` | Manages conversation context. |
| **UI** | Streamlit | Interactive web interface. |
| **Container** | Docker + Compose | Production-ready deployment. |

### ✅ Advanced Features
- **OpenAI Embeddings**: High-quality text vectorization for superior semantic search.
- **Configurable Chunking**: Adjustable text chunk size and overlap via the UI.
- **Stateful Memory**: Conversation history is maintained for contextual understanding.
- **Confidence Scoring**: Each response is given a confidence score to assess reliability.
- **Robust Error Handling**: Graceful error management and clear user feedback.

## 📦 Project Structure

```
rag/
├── app/
│   ├── document_parser.py    # Enhanced PDF parsing with Arabic support
│   ├── index_builder.py      # Vector index creation with Gemini embeddings
│   ├── query_engine.py       # Enhanced query engine with citations
│   └── memory_manager.py     # Conversation memory management
├── config/
│   └── settings.py           # Environment configuration and validation
├── interface/
│   └── main.py              # Streamlit web interface
├── uploads/                  # Document storage
├── logs/                     # Application logs
├── Dockerfile               # Container configuration
├── docker-compose.yml       # Multi-service orchestration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```
## ⚙️ Installation & Setup

### 1. Prerequisites
- Docker and Docker Compose
- Python 3.10+ (for local development)
- **OpenAI API Key** (for embeddings)
- **Gemini API Key** (for generation)
- **LlamaParse API Key** (for parsing)

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
# --- Required API Keys ---
OPENAI_API_KEY="sk-..."
GEMINI_API_KEY="AIza..."
LLAMAPARSE_API_KEY="llx-..."

# --- Neo4j Configuration ---
# These credentials must match docker-compose.yml
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=test1234
```

### 3. API Key Setup
You'll need to obtain API keys for the following services:

1. **Gemini API Key**: 
   - Visit: https://makersuite.google.com/app/apikey

2. **LlamaParse API Key**:
   - Visit: https://cloud.llamaindex.ai/
   - Sign up and create an API key for PDF parsing

3. **OpenAI API Key**:
   - Visit: https://platform.openai.com/api-keys

### 4. Quick Start
```bash
# Clone the repository
git clone https://github.com/your-org/agentic-rag-system.git
cd agentic-rag-system

# Create and edit your .env file with the API keys
# nano .env

# Start all services
docker-compose up --build

# Access the application
# Streamlit UI: http://localhost:8501
# Neo4j Browser: http://localhost:7474
```

## 🚀 Project Development Journey

This RAG demo was developed over approximately **22 hours** across 4 working days. A key strategic decision for this demo was to start with a **"naive" RAG system**—one without complex reasoning agents—to first establish a solid baseline for retrieval and citation. This journey involved iterative development, debugging, and a critical pivot in the choice of embedding models, which was key to achieving high-quality, accurate responses.

**Total Development Time**: ~22 hours

---

#### **Step 1: Research & Foundation (2 hours)**
The initial phase focused on getting up-to-date with the latest LlamaIndex documentation and tutorials, especially after a period of working with other frameworks (CrewAI). This was followed by designing the project architecture and setting up the local repository.

---

#### **Step 2: Initial Development & Challenges (7 hours)**
The first functional version was developed based on the official LlamaIndex [`CitationQueryEngine`](https://docs.llamaindex.ai/en/stable/examples/query_engine/citation_query_engine/) documentation. While the system was operational and could process documents and queries, the quality of the generated answers was poor. The responses lacked accuracy and relevance, indicating a fundamental issue with the initial setup.

---

#### **Step 3: Unsuccessful Tuning & Pivotal Realization (5 hours)**
Significant time was invested in trying to improve response quality by tuning hyperparameters and modifying application logic. This included upgrading the LLM from `gemini-2.5-flash` to the more powerful `gemini-2.5-pro`, which did provide a **significant improvement** in response coherence. However, the fundamental issue of inaccurate retrieval and poor citation quality persisted. This led to the critical realization that the bottleneck was not the generative model, but the embedding model's inability to capture the semantic nuance required for accurate retrieval.

---

#### **Step 4: The Breakthrough - Switching to OpenAI Embeddings (4 hours)**
The turning point of the project came when the embedding model was switched from Gemini to OpenAI's `text-embedding-3-large`. The improvement was immediate and dramatic, especially for documents in Arabic. With a high-quality semantic foundation, further optimizations became highly effective. Specifically, setting a high `similarity_top_k=15` yielded the best results by providing the LLM a much wider and more relevant context from which to synthesize its answer.

---

#### **Step 5: Documentation & Deployment (4 hours)**
With the core functionality working reliably, the final step involved writing comprehensive documentation (this `README.md` file), containerizing the application with Docker, and finalizing the deployment configuration.

---

## 💡 Key Learnings & Takeaways

This project yielded several important insights for building high-quality RAG systems:

1.  **The Embedding Model is Paramount**: The single most critical factor for this system's success was the quality of the embedding model. A powerful generative LLM cannot compensate for poor retrieval. For multilingual or specialized documents, investing in the best possible embedding model is non-negotiable.

2.  **Model Performance on Arabic**: A key observation was the superior performance of OpenAI's models on Arabic language documents compared to the Gemini models tested. **For projects heavily focused on Arabic content, GPT-4 models currently appear to have a distinct advantage** in both embedding quality and generative understanding.

3.  **A Wide Context Window is Key**: Once retrieval quality is high, providing the LLM with more context is highly beneficial. Increasing `similarity_top_k` to a large value like `15` allowed the model to see a broader set of relevant text chunks, leading to more comprehensive and accurate answers. A high `top_k` with a poor retriever, however, would only add noise.

---

**Developer**: **Sif Eddine Boudjellal**  
**Contact**: [LinkedIn](https://www.linkedin.com/in/sif-eddine-boudjellal/)

**Development Time**: ~22 hours for demo  
**Last Updated**: 06-08-2025 

**Version**: 1.0.0 (Demo)