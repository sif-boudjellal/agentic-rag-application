# 🚀 Quick Start Guide - Agentic RAG System

Get your RAG system up and running in 5 minutes!

## 📋 Prerequisites

- Docker and Docker Compose installed
- Gemini API key (get one from [Google AI Studio](https://makersuite.google.com/app/apikey))

## ⚡ Quick Setup

### 1. Clone and Setup
```bash
git clone https://github.com/your-org/agentic-rag-system.git
cd agentic-rag-system
```

### 2. Configure Environment
```bash
# Copy the example environment file
cp env.example .env

# Edit the .env file with your API key
# Replace 'your_gemini_api_key_here' with your actual Gemini API key
```

### 3. Start the System
```bash
# Start all services
docker-compose up --build

# Wait for all services to be ready (about 2-3 minutes)
```

### 4. Access the Application
- **Streamlit UI**: http://localhost:8501
- **Neo4j Browser**: http://localhost:7474 (username: neo4j, password: test)

## 🧪 Test the System

### Option 1: Use the Web Interface
1. Open http://localhost:8501
2. Upload one or more PDF documents
3. Click "Process Documents" to build the knowledge base
4. Ask questions about any document or across all documents
5. See citations and confidence scores

### Option 2: Run the Test Script
```bash
# Run the comprehensive test
python test_rag_system.py
```

## 📊 Monitor the System

### Current Demo
- **Streamlit UI**: Real-time chat interface
- **Neo4j Browser**: View vector database contents
- **Application Logs**: Check container logs

## 🔧 Configuration Options

### Model Selection
In the Streamlit sidebar, you can configure:
- **Chunk Size**: 256-1024 tokens
- **Memory Limit**: 1000-5000 tokens

### Environment Variables
Key configuration options in `.env`:
```env
# Required
GEMINI_API_KEY=your_api_key

# Performance tuning
DEFAULT_CHUNK_SIZE=512
DEFAULT_MEMORY_LIMIT=3000
```

## 🐛 Troubleshooting

### Common Issues

**1. API Key Error**
```
Error: GEMINI_API_KEY is required
```
**Solution**: Add your Gemini API key to the `.env` file

**2. Neo4j Connection Error**
```
Error: Failed to initialize Neo4j vector store
```
**Solution**: Wait for Neo4j to fully start (check http://localhost:7474)

**3. Memory Issues**
```
Error: Out of memory
```
**Solution**: Increase Docker memory allocation or reduce chunk size

**4. Slow Performance**
**Solutions**:
- Reduce chunk size in sidebar
- Use smaller documents
- Increase Docker resources

### Debug Mode
```bash
# Enable debug logging
echo "DEBUG=True" >> .env
echo "LOG_LEVEL=DEBUG" >> .env

# Restart services
docker-compose down && docker-compose up --build
```

## 📈 Performance Tips

### For Better Response Quality
- Use chunk size 512-1024 for detailed documents
- Set memory limit to 3000-5000 for complex conversations
- Upload high-quality PDFs with clear text

### For Faster Processing
- Use smaller chunk sizes (256-512)
- Reduce memory limit for simple queries
- Use Gemini embeddings for optimal performance

## 🔄 Development Mode

### Local Development
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run Streamlit directly
streamlit run interface/main.py

# Run tests
python test_rag_system.py
```

### Code Changes
```bash
# The system auto-reloads on code changes
# Just save your files and refresh the browser
```

## 📚 Example Usage

### Sample Questions to Try
1. "What is the main topic of each document?"
2. "Summarize the key requirements across all documents"
3. "What are the benefits mentioned in all documents?"
4. "Compare the different requirements and incentives"
5. "What is the complete process for registration?"
6. "What are all the tax-related information mentioned?"
7. "List all the incentives and their durations"

### Expected Features
- ✅ Accurate citations with page numbers
- ✅ Confidence scores for responses
- ✅ Memory for follow-up questions
- ✅ No hallucination protection
- ✅ Arabic text support
- ✅ Multiple document processing
- ✅ Cross-document queries
- ✅ Gemini-powered embeddings

## 🚀 Next Steps

### Current Demo Features
- Multiple document upload and batch processing
- Intelligent Q&A with citations from any document
- Cross-document queries and comparisons
- Memory-enabled conversations
- Configurable parameters
- Duplicate file detection
- Gemini embeddings for optimal performance

### Future Enhancements
- User authentication and management
- Document versioning and organization
- Advanced analytics and monitoring
- API endpoints for integration
- Background processing for large documents

## 📞 Support

- **Documentation**: Check the main README.md
- **Issues**: Report bugs on GitHub
- **Questions**: Use GitHub Discussions
- **Examples**: See test_rag_system.py for usage examples

---

**Ready to start?** Run `docker-compose up --build` and visit http://localhost:8501! 🎉 