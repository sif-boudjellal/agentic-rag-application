from llama_index.core.query_engine import CitationQueryEngine
from llama_index.llms.gemini import Gemini
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage
from config.settings import GEMINI_API_KEY, LLM_MODEL, SYSTEM_PROMPT
import logging
import re
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger(__name__)


class QueryEngine:
    """Query engine focused on reliable citation-based responses."""
    
    def __init__(self, 
                 index,
                 memory_token_limit: int = 3000,
                 temperature: float = 0.1,
                 similarity_top_k: int = 5):
        """
        Initialize the query engine.
        
        Args:
            index: LlamaIndex vector index
            memory_token_limit: Maximum tokens to keep in memory
            temperature: LLM temperature for response generation
            similarity_top_k: Number of similar chunks to retrieve
        """
        self.index = index
        self.memory_token_limit = memory_token_limit
        self.temperature = temperature
        self.similarity_top_k = similarity_top_k
        
        # Initialize components
        self.llm = self._create_llm()
        self.memory = self._create_memory()
        self.citation_engine = self._create_citation_engine()
    
    def _create_llm(self) -> Gemini:
        """Create Gemini LLM instance."""
        try:
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is required")
            
            llm = Gemini(
                api_key=GEMINI_API_KEY,
                model=LLM_MODEL,
                temperature=self.temperature
            )
            logger.info("Gemini LLM initialized successfully")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            raise Exception(f"LLM initialization failed: {str(e)}")
    
    def _create_memory(self) -> ChatMemoryBuffer:
        """Create memory buffer for conversation context."""
        try:
            memory = ChatMemoryBuffer.from_defaults(
                token_limit=self.memory_token_limit
            )
            logger.info("Memory buffer created successfully")
            return memory
        except Exception as e:
            logger.error(f"Failed to create memory: {str(e)}")
            raise Exception(f"Memory creation failed: {str(e)}")
    
    def _create_citation_engine(self) -> CitationQueryEngine:
        """Create citation query engine with custom prompt."""
        try:
            # Custom system prompt for better citation formatting
            
            citation_engine = CitationQueryEngine.from_args(
                index=self.index,
                llm=self.llm,
                similarity_top_k=self.similarity_top_k,
                response_mode="tree_summarize",
                system_prompt=SYSTEM_PROMPT
            )
            logger.info("Citation query engine created successfully")
            return citation_engine
        except Exception as e:
            logger.error(f"Failed to create citation engine: {str(e)}")
            raise Exception(f"Citation engine creation failed: {str(e)}")
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Process a user question and return response with citations.
        
        Args:
            question (str): User's question
            
        Returns:
            Dict[str, Any]: Response with answer and citations
        """
        try:
            if not question.strip():
                return {
                    "answer": "Please provide a valid question.",
                    "citations": [],
                    "sources": [],
                    "confidence": 0.0,
                    "source_documents": []
                }
            
            logger.info(f"Processing question: {question[:100]}...")
            
            # Add conversation context if memory exists
            contextualized_question = self._add_context(question)
            
            # Get response from citation engine
            response = self.citation_engine.query(contextualized_question)
            response_text = str(response)
            
            # Extract citations and metadata from source nodes
            citations = self._extract_citations_from_response(response)
            sources = self._extract_sources_from_response(response)
            source_documents = self._extract_source_documents(response)
            
            # Add to memory for context - FIXED: Use proper ChatMessage format
            user_message = ChatMessage(role="user", content=question)
            assistant_message = ChatMessage(role="assistant", content=response_text)
            
            self.memory.put(user_message)
            self.memory.put(assistant_message)
            
            # Check if response indicates no answer found
            if self._is_no_answer_response(response_text):
                return {
                    "answer": "No answer found in the provided documents.",
                    "citations": [],
                    "sources": [],
                    "confidence": 0.0,
                    "source_documents": []
                }
            
            # Calculate confidence based on response quality and citations
            confidence = self._calculate_confidence(response_text, citations, len(source_documents))
            
            return {
                "answer": response_text,
                "citations": citations,
                "sources": sources,
                "confidence": confidence,
                "source_documents": source_documents
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "answer": f"Error processing your question: {str(e)}",
                "citations": [],
                "sources": [],
                "confidence": 0.0,
                "source_documents": []
            }
    
    def _add_context(self, question: str) -> str:
        """Add conversation context to the question if memory exists."""
        try:
            # Get conversation history from memory
            chat_history = self.memory.get()
            
            if not chat_history:
                return question
            
            # Format context with recent conversation
            context_str = "Previous conversation context:\n"
            for msg in chat_history[-6:]:  # Last 6 messages (3 exchanges)
                if hasattr(msg, 'content') and hasattr(msg, 'role'):
                    context_str += f"{msg.role}: {msg.content}\n"
            
            contextualized = f"{context_str}\nCurrent question: {question}"
            return contextualized
            
        except Exception as e:
            logger.warning(f"Failed to add context: {str(e)}")
            return question
    
    def _extract_citations_from_response(self, response) -> List[Dict[str, Any]]:
        """Extract citations from the response object and text."""
        citations = []
        
        try:
            # Method 1: Extract from source nodes (most reliable)
            if hasattr(response, 'source_nodes'):
                for i, node in enumerate(response.source_nodes):
                    metadata = node.metadata
                    file_name = metadata.get('file_name', f'Document_{i+1}')
                    page_num = metadata.get('page', 1)
                    
                    citation = {
                        "file": file_name,
                        "page": page_num,
                        "text_snippet": node.text[:200] + "..." if len(node.text) > 200 else node.text,
                        "score": getattr(node, 'score', 0.0)
                    }
                    citations.append(citation)
            
            # Method 2: Extract from response text using regex patterns
            response_text = str(response)
            text_citations = self._extract_citations_from_text(response_text)
            
            # Merge citations, prioritizing source nodes
            file_page_pairs = {(c['file'], c['page']) for c in citations}
            for text_cite in text_citations:
                pair = (text_cite['file'], text_cite['page'])
                if pair not in file_page_pairs:
                    citations.append(text_cite)
            
        except Exception as e:
            logger.warning(f"Error extracting citations: {str(e)}")
        
        return citations
    
    def _extract_citations_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract citations from response text using multiple patterns."""
        citations = []
        
        # Pattern 1: [Source: filename.pdf, Page: X]
        pattern1 = r'\[Source:\s*([^,]+\.pdf),\s*Page:\s*(\d+)\]'
        matches1 = re.findall(pattern1, text, re.IGNORECASE)
        
        for file_name, page in matches1:
            citations.append({
                "file": file_name.strip(),
                "page": int(page),
                "type": "text_citation"
            })
        
        # Pattern 2: filename.pdf - Page X
        pattern2 = r'([^,\s]+\.pdf)\s*-\s*Page\s*(\d+)'
        matches2 = re.findall(pattern2, text, re.IGNORECASE)
        
        for file_name, page in matches2:
            citations.append({
                "file": file_name.strip(),
                "page": int(page),
                "type": "text_citation"
            })
        
        # Pattern 3: (filename.pdf, p. X)
        pattern3 = r'\(([^,]+\.pdf),\s*p\.\s*(\d+)\)'
        matches3 = re.findall(pattern3, text, re.IGNORECASE)
        
        for file_name, page in matches3:
            citations.append({
                "file": file_name.strip(),
                "page": int(page),
                "type": "text_citation"
            })
        
        return citations
    
    def _extract_sources_from_response(self, response) -> List[str]:
        """Extract unique source files from response."""
        sources = set()
        
        try:
            # From source nodes
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    file_name = node.metadata.get('file_name')
                    if file_name:
                        sources.add(file_name)
            
            # From response text
            response_text = str(response)
            citations = self._extract_citations_from_text(response_text)
            for citation in citations:
                sources.add(citation['file'])
                
        except Exception as e:
            logger.warning(f"Error extracting sources: {str(e)}")
        
        return list(sources)
    
    def _extract_source_documents(self, response) -> List[Dict[str, Any]]:
        """Extract detailed source document information."""
        documents = []
        
        try:
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    doc_info = {
                        "file_name": node.metadata.get('file_name', 'Unknown'),
                        "page": node.metadata.get('page', 1),
                        "text_snippet": node.text[:300] + "..." if len(node.text) > 300 else node.text,
                        "relevance_score": getattr(node, 'score', 0.0),
                        "metadata": node.metadata
                    }
                    documents.append(doc_info)
        except Exception as e:
            logger.warning(f"Error extracting source documents: {str(e)}")
        
        return documents
    
    def _is_no_answer_response(self, response_text: str) -> bool:
        """Check if response indicates no answer found."""
        no_answer_indicators = [
            "no answer found",
            "no information found",
            "no relevant information",
            "not found in the documents",
            "no sources found",
            "cannot find",
            "unable to find",
            "not mentioned in the documents",
            "no specific information"
        ]
        
        response_lower = response_text.lower()
        return any(indicator in response_lower for indicator in no_answer_indicators)
    
    def _calculate_confidence(self, response_text: str, citations: List[Dict], num_sources: int) -> float:
        """Calculate confidence score for the response."""
        confidence = 0.3  # Base confidence
        
        # Increase confidence based on citations
        if citations:
            confidence += min(0.4, len(citations) * 0.1)  # Up to 0.4 for citations
        
        # Increase confidence based on number of source documents
        if num_sources > 0:
            confidence += min(0.2, num_sources * 0.05)  # Up to 0.2 for sources
        
        # Increase confidence if response is detailed
        word_count = len(response_text.split())
        if word_count > 50:
            confidence += 0.1
        elif word_count > 20:
            confidence += 0.05
        
        # Decrease confidence if response is too short
        if word_count < 10:
            confidence -= 0.2
        
        # Decrease confidence if no specific citations
        if not citations:
            confidence -= 0.3
        
        # Check for specific factual indicators
        if any(indicator in response_text.lower() for indicator in ['according to', 'states that', 'specifies', 'indicates']):
            confidence += 0.1
        
        return min(max(confidence, 0.0), 1.0)
    
    def clear_memory(self):
        """Clear conversation memory."""
        try:
            self.memory.reset()
            logger.info("Memory cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear memory: {str(e)}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        try:
            chat_history = self.memory.get()
            return {
                "messages_count": len(chat_history) if chat_history else 0,
                "memory_limit": self.memory_token_limit,
                "has_context": bool(chat_history)
            }
        except Exception as e:
            logger.error(f"Failed to get memory stats: {str(e)}")
            return {"error": str(e)}