"""
Embedding Service - Creates vector embeddings for RAG indexing.
Part of TRACK-003: RAG System Integration
"""
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger("worker.embed")

# Check if chromadb is available
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("chromadb not installed. Embedding disabled.")

# Check if sentence-transformers is available
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDER_AVAILABLE = True
except ImportError:
    EMBEDDER_AVAILABLE = False
    logger.warning("sentence-transformers not installed.")


class EmbeddingService:
    """
    Creates embeddings and stores them in ChromaDB.
    """
    
    def __init__(
        self,
        persist_directory: str = "F:/conductor/data/chromadb",
        model_name: str = "all-MiniLM-L6-v2"
    ):
        self.persist_directory = persist_directory
        self.model_name = model_name
        self.embedder: Optional[SentenceTransformer] = None
        self.client: Optional[chromadb.Client] = None
        self.collection = None
        
        if not CHROMA_AVAILABLE or not EMBEDDER_AVAILABLE:
            logger.error("Embedding service unavailable - missing dependencies")
            return
        
        # Initialize embedder
        logger.info(f"Loading embedding model: {model_name}")
        try:
            self.embedder = SentenceTransformer(model_name)
        except Exception as e:
            logger.error(f"Failed to load embedder: {e}")
            return
        
        # Initialize ChromaDB
        os.makedirs(persist_directory, exist_ok=True)
        try:
            self.client = chromadb.PersistentClient(path=persist_directory)
            self.collection = self.client.get_or_create_collection(
                name="conductor_documents",
                metadata={"description": "Conductor document embeddings"}
            )
            logger.info(f"ChromaDB initialized at {persist_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
    
    def embed_document(self, doc_path: str, content: Optional[str] = None) -> bool:
        """
        Embed a document and store in ChromaDB.
        
        Args:
            doc_path: Path to the document (used as ID)
            content: Optional content override. If None, reads from file.
            
        Returns:
            True if successful
        """
        if not self.embedder or not self.collection:
            return False
        
        doc_path = str(doc_path)
        
        # Read content if not provided
        if content is None:
            try:
                content = Path(doc_path).read_text(encoding="utf-8")
            except Exception as e:
                logger.error(f"Failed to read document: {e}")
                return False
        
        # Skip empty documents
        if not content.strip():
            logger.warning(f"Skipping empty document: {doc_path}")
            return False
        
        # Chunk long documents (max ~500 tokens each)
        chunks = self._chunk_text(content, max_chars=2000)
        
        try:
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_path}::chunk_{i}"
                
                # Check if already exists
                existing = self.collection.get(ids=[chunk_id])
                if existing["ids"]:
                    continue  # Skip already indexed
                
                # Create embedding
                embedding = self.embedder.encode(chunk, convert_to_numpy=True).tolist()
                
                # Store in ChromaDB
                self.collection.add(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        "source_path": doc_path,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    }]
                )
            
            logger.info(f"Embedded {len(chunks)} chunks from: {doc_path}")
            return True
            
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return False
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Returns list of {document, metadata, distance}
        """
        if not self.embedder or not self.collection:
            return []
        
        try:
            query_embedding = self.embedder.encode(query, convert_to_numpy=True).tolist()
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
            )
            
            output = []
            for i, doc in enumerate(results["documents"][0]):
                output.append({
                    "document": doc,
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                })
            
            return output
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        if not self.collection:
            return {"error": "Not initialized"}
        
        return {
            "total_documents": self.collection.count(),
            "persist_directory": self.persist_directory,
        }
    
    @staticmethod
    def _chunk_text(text: str, max_chars: int = 2000) -> List[str]:
        """Split text into chunks at paragraph boundaries."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) > max_chars and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += "\n\n" + para
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text[:max_chars]]


# Singleton instance
_service: Optional[EmbeddingService] = None

def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton."""
    global _service
    if _service is None:
        _service = EmbeddingService()
    return _service


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    service = get_embedding_service()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "search" and len(sys.argv) > 2:
            results = service.search(" ".join(sys.argv[2:]))
            for r in results:
                print(f"[{r['distance']:.3f}] {r['metadata']['source_path']}")
                print(f"  {r['document'][:200]}...\n")
        else:
            success = service.embed_document(sys.argv[1])
            print(f"Embedded: {success}")
    else:
        stats = service.get_stats()
        print(f"Stats: {stats}")
