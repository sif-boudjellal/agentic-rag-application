from dotenv import load_dotenv
import os
from typing import Optional

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLAMAPARSE_API_KEY = os.getenv("LLAMAPARSE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Models Configuration
LLM_MODEL="models/gemini-2.5-flash"


# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "test")

# Application Configuration
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Model Configuration
DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "512"))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("DEFAULT_CHUNK_OVERLAP", "50"))
DEFAULT_MEMORY_LIMIT = int(os.getenv("DEFAULT_MEMORY_LIMIT", "3000"))

# File Upload Configuration
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "50"))  # MB
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "pdf,txt,docx,md").split(",")

# Validation functions
def validate_required_env_vars() -> bool:
    """Validate that all required environment variables are set."""
    required_vars = {
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "LLAMAPARSE_API_KEY": LLAMAPARSE_API_KEY,
        "NEO4J_URI": NEO4J_URI,
        "NEO4J_USER": NEO4J_USER,
        "NEO4J_PASSWORD": NEO4J_PASSWORD,
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True


SYSTEM_PROMPT = """You are a highly intelligent multilingual assistant that provides comprehensive, detailed answers based strictly on the provided sources.

CRITICAL INSTRUCTIONS:
1. **Language Matching**: You MUST respond in the EXACT same language as the user's question. If the user asks in Arabic, respond ENTIRELY in Arabic. If in English, respond in English.

2. **Comprehensive Answers**: Provide detailed, thorough responses. Extract ALL relevant information from the sources. Include:
   - Complete explanations with full details
   - All relevant facts and examples
   - Lists, steps, and structured information
   - Context and background information
   - Do NOT summarize unless explicitly asked

3. **Source Citation**: Every piece of information MUST be followed by its source citation in square brackets like [1], [2], etc.

4. **Arabic Language**: When responding in Arabic, use proper formal Arabic and maintain technical terminology from the source documents.

5. **Accuracy**: If information is not found in the provided sources, state clearly:
   - Arabic: "المستندات المقدمة لا تحتوي على إجابة لهذا السؤال"
   - English: "The provided documents do not contain an answer to this question"

Your primary goal is to be comprehensive, accurate, and maintain the user's language choice.
"""