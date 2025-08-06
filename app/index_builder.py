
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.neo4jvector import Neo4jVectorStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from config.settings import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER, OPENAI_API_KEY
import os
import logging
from typing import List, Optional
from llama_index.core.schema import Document
import time
from neo4j import GraphDatabase

# Configure logging
logger = logging.getLogger(__name__)


class IndexBuilder:
    """Enhanced index builder with Gemini embeddings and modern LlamaIndex Settings."""
    
    def __init__(self, 
                 chunk_size: int = 512,
                 chunk_overlap: int = 50):
        """
        Initialize the index builder.
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.neo4j_uri = NEO4J_URI
        self.neo4j_user = NEO4J_USER
        self.neo4j_password = NEO4J_PASSWORD
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Configure global settings first
        self._configure_settings()
        
        # Initialize vector store
        self.vector_store = self._create_vector_store()

    def _wait_for_neo4j(self, max_retries=5, retry_delay=10):
        """Wait for Neo4j to be available before proceeding."""
        from neo4j import exceptions

        for attempt in range(max_retries):
            try:
                with GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password)) as driver:
                    driver.verify_connectivity()
                    logger.info("Neo4j is ready!")
                    return True
            except exceptions.ServiceUnavailable as e:
                logger.warning(f"Neo4j not ready yet (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_delay)
        
        logger.error("Could not connect to Neo4j after multiple retries.")
        return False

    def _configure_settings(self):
        """Configure global Settings instead of ServiceContext."""
        try:
            # embed_model = GeminiEmbedding(model_name="models/embedding-001")
            embed_model = OpenAIEmbedding(
                api_key=OPENAI_API_KEY,
                model="text-embedding-3-large"  # or another OpenAI embedding model
            )
            node_parser = SentenceSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)

            Settings.embed_model = embed_model
            Settings.node_parser = node_parser
            Settings.chunk_size = self.chunk_size
            Settings.chunk_overlap = self.chunk_overlap
            
            logger.info("Global settings configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to configure settings: {str(e)}")
            raise

    def _create_vector_store(self) -> Neo4jVectorStore:
        """Create and configure Neo4j vector store."""
        if not self._wait_for_neo4j():
            raise RuntimeError("Neo4j connection failed.")

        try:
            # Get embedding dimension dynamically
            embedding_dimension = len(Settings.embed_model.get_text_embedding("test"))
            logger.info(f"Detected embedding dimension: {embedding_dimension}")
            
            vector_store = Neo4jVectorStore(
                url=self.neo4j_uri,
                username=self.neo4j_user,
                password=self.neo4j_password,
                embedding_dimension=embedding_dimension,
                use_in_transaction=False  # Crucial for avoiding transaction errors
            )
            logger.info("Neo4j vector store initialized successfully")
            return vector_store
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j vector store: {str(e)}")
            raise
    
    def build_index(self, documents: List[Document]) -> VectorStoreIndex:
        """Build vector index from documents."""
        try:
            if not documents:
                raise ValueError("No documents provided for indexing")
            
            logger.info(f"Building index for {len(documents)} documents")
            
            storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
            
            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context,
                show_progress=True
            )
            
            logger.info("Index built successfully")
            return index
            
        except Exception as e:
            logger.error(f"Failed to build index: {str(e)}")
            raise

    def get_index_stats(self, index: VectorStoreIndex) -> dict:
        """Get statistics about the built index."""
        try:
            stats = {
                "total_nodes": len(index.docstore.docs),
                "embedding_model": "gemini",
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get index stats: {str(e)}")
            return {"error": str(e)}

    def get_existing_document_names(self) -> List[str]:
        """Query Neo4j to get the names of all documents already indexed."""
        if not self._wait_for_neo4j():
            logger.error("Cannot check for existing documents, Neo4j is not available.")
            return []

        try:
            with GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password)) as driver:
                query = "MATCH (c:Chunk) WHERE c.file_name IS NOT NULL RETURN DISTINCT c.file_name AS fileName"
                records, _, _ = driver.execute_query(query)
                file_names = sorted([record["fileName"] for record in records])
                if file_names:
                    logger.info(f"Found existing documents in Neo4j: {file_names}")
                else:
                    logger.info("No existing documents found in Neo4j.")
                return file_names
        except Exception as e:
            logger.error(f"Failed to query for existing documents: {str(e)}")
            return []

    def delete_all_documents(self):
        """
        Deletes all Chunk nodes and the associated vector index from Neo4j.
        USE WITH CAUTION: This action is irreversible.
        """
        if not self._wait_for_neo4j():
            logger.error("Cannot delete documents, Neo4j is not available.")
            return

        try:
            with GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password)) as driver:
                # 1. Delete all nodes with the 'Chunk' label
                driver.execute_query("MATCH (c:Chunk) DETACH DELETE c")
                logger.info("Deleted all 'Chunk' nodes from Neo4j.")
                
                # 2. Drop the vector index (default name is 'vector')
                indexes, _, _ = driver.execute_query("SHOW INDEXES")
                vector_index_name = "vector" 
                if any(index['name'] == vector_index_name for index in indexes):
                    driver.execute_query(f"DROP INDEX {vector_index_name}")
                    logger.info(f"Dropped vector index '{vector_index_name}'.")
                
                logger.info("Successfully cleared all indexed documents from the database.")
        except Exception as e:
            logger.error(f"Failed to delete all documents: {str(e)}")
            raise