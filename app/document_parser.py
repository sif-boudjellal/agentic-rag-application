from llama_parse import LlamaParse
from llama_index.core.schema import Document
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
import os
import hashlib
from datetime import datetime
from config.settings import LLAMAPARSE_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_pdf(file_path: str, api_key: Optional[str] = None) -> List[Document]:
    """
    Parse PDF documents with enhanced support for Arabic text and tables.
    
    Args:
        file_path (str): Path to the PDF file
        api_key (Optional[str]): LlamaParse API key (optional for local parsing)
    
    Returns:
        List[Document]: Parsed documents with metadata
    """
    try:
        # Use provided API key or fall back to environment variable
        if api_key is None:
            api_key = LLAMAPARSE_API_KEY
        
        if not api_key:
            raise ValueError("LlamaParse API key is required. Please set LLAMAPARSE_API_KEY environment variable.")
        
        # Initialize LlamaParse with enhanced settings for Arabic and tables
        parser = LlamaParse(
            api_key=api_key,
            result_type="markdown",  # Changed from "all" to "markdown"
            verbose=True,
             invalidate_cache=True,
            # Enhanced settings for better Arabic and table support
            parsing_instruction="Extract all text including Arabic content and preserve table structures. Maintain original formatting where possible."
        )
        
        # Parse the document
        documents = parser.load_data(Path(file_path))
        
        # Add metadata to each document
        file_name = Path(file_path).name
        file_size = os.path.getsize(file_path)
        file_hash = get_file_hash(file_path)
        
        for i, doc in enumerate(documents):
            doc.metadata.update({
                "file_name": file_name,
                "page": i + 1,
                "file_path": str(file_path),
                "file_size": file_size,
                "file_hash": file_hash,
                "parsing_method": "llamaparse",
                "parsing_timestamp": datetime.now().isoformat()
            })
            
            # Log parsing progress
            logger.info(f"Parsed page {i + 1} from {file_name}")
        
        logger.info(f"Successfully parsed {len(documents)} pages from {file_name}")
        return documents
        
    except Exception as e:
        logger.error(f"Error parsing PDF {file_path}: {str(e)}")
        raise Exception(f"Failed to parse PDF: {str(e)}")


def parse_multiple_pdfs(file_paths: List[str], api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse multiple PDF files and return comprehensive results.
    
    Args:
        file_paths (List[str]): List of PDF file paths
        api_key (Optional[str]): LlamaParse API key
    
    Returns:
        Dict[str, Any]: Results with documents, stats, and errors
    """
    results = {
        'documents': [],
        'errors': [],
        'stats': {
            'total_files': len(file_paths),
            'successful_files': 0,
            'failed_files': 0,
            'total_pages': 0,
            'total_size': 0,
            'processing_time': 0
        }
    }
    
    start_time = datetime.now()
    processed_hashes = set()
    
    for file_path in file_paths:
        try:
            # Check for duplicates
            file_hash = get_file_hash(file_path)
            if file_hash in processed_hashes:
                results['errors'].append({
                    'file_path': file_path,
                    'error': 'Duplicate file detected'
                })
                results['stats']['failed_files'] += 1
                continue
            
            # Validate PDF
            if not validate_pdf(file_path):
                results['errors'].append({
                    'file_path': file_path,
                    'error': 'Invalid PDF file'
                })
                results['stats']['failed_files'] += 1
                continue
            
            # Parse PDF
            docs = parse_pdf(file_path, api_key)
            
            # Add batch metadata
            for doc in docs:
                doc.metadata.update({
                    'batch_id': start_time.isoformat(),
                    'file_hash': file_hash
                })
            
            results['documents'].extend(docs)
            results['stats']['successful_files'] += 1
            results['stats']['total_pages'] += len(docs)
            results['stats']['total_size'] += os.path.getsize(file_path)
            processed_hashes.add(file_hash)
            
            logger.info(f"Successfully processed {file_path}: {len(docs)} pages")
            
        except Exception as e:
            error_msg = f"Error processing {file_path}: {str(e)}"
            results['errors'].append({
                'file_path': file_path,
                'error': str(e)
            })
            results['stats']['failed_files'] += 1
            logger.error(error_msg)
    
    # Calculate processing time
    end_time = datetime.now()
    results['stats']['processing_time'] = (end_time - start_time).total_seconds()
    
    logger.info(f"Batch processing completed: {results['stats']['successful_files']} successful, {results['stats']['failed_files']} failed")
    
    return results


def get_file_hash(file_path: str) -> str:
    """
    Generate a hash for file content to detect duplicates.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: MD5 hash of the file
    """
    try:
        with open(file_path, 'rb') as f:
            file_content = f.read()
        return hashlib.md5(file_content).hexdigest()
    except Exception as e:
        logger.error(f"Error generating hash for {file_path}: {str(e)}")
        return ""


def validate_pdf(file_path: str) -> bool:
    """
    Validate if the file is a valid PDF and accessible.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        bool: True if valid PDF, False otherwise
    """
    try:
        if not os.path.exists(file_path):
            return False
            
        if not file_path.lower().endswith('.pdf'):
            return False
            
        # Check file size (max 50MB)
        if os.path.getsize(file_path) > 50 * 1024 * 1024:
            return False
            
        # Basic PDF validation (check for PDF header)
        with open(file_path, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                return False
            
        return True
        
    except Exception:
        return False


def get_document_stats(documents: List[Document]) -> Dict[str, Any]:
    """
    Get comprehensive statistics about processed documents.
    
    Args:
        documents (List[Document]): List of processed documents
        
    Returns:
        Dict[str, Any]: Document statistics
    """
    stats = {
        'total_documents': len(documents),
        'total_pages': 0,
        'total_size': 0,
        'files': {},
        'languages': set(),
        'avg_text_length': 0
    }
    
    if not documents:
        return stats
    
    total_text_length = 0
    
    for doc in documents:
        # Count pages
        stats['total_pages'] += 1
        
        # Calculate text length
        text_length = len(doc.text)
        total_text_length += text_length
        
        # Track file information
        file_name = doc.metadata.get('file_name', 'Unknown')
        if file_name not in stats['files']:
            stats['files'][file_name] = {
                'pages': 0,
                'size': doc.metadata.get('file_size', 0),
                'total_text_length': 0
            }
        
        stats['files'][file_name]['pages'] += 1
        stats['files'][file_name]['total_text_length'] += text_length
        stats['total_size'] += doc.metadata.get('file_size', 0)
        
        # Detect language (basic Arabic detection)
        if any('\u0600' <= char <= '\u06FF' for char in doc.text):
            stats['languages'].add('Arabic')
        else:
            stats['languages'].add('English')
    
    # Calculate averages
    stats['avg_text_length'] = total_text_length / len(documents)
    stats['languages'] = list(stats['languages'])
    
    return stats