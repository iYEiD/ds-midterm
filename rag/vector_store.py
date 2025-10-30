"""
ChromaDB vector store for NBA statistics embeddings
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from loguru import logger
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings

# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)


class VectorStore:
    """ChromaDB vector store manager"""
    
    def __init__(self, collection_name: str = "nba_stats_embeddings"):
        """
        Initialize ChromaDB client and collection
        
        Args:
            collection_name: Name of the ChromaDB collection
        """
        self.collection_name = collection_name
        
        # Create persistent directory if it doesn't exist
        persist_dir = Path(settings.CHROMA_PERSIST_DIR)
        persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "NBA player statistics embeddings"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def add_embeddings(self, ids: List[str], embeddings: List[List[float]], 
                      documents: List[str], metadatas: List[Dict]) -> bool:
        """
        Add embeddings to the collection
        
        Args:
            ids: List of unique IDs
            embeddings: List of embedding vectors
            documents: List of text documents
            metadatas: List of metadata dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Added {len(ids)} embeddings to collection")
            return True
            
        except Exception as e:
            logger.error(f"Error adding embeddings: {e}")
            return False
    
    def query(self, query_embeddings: List[List[float]], 
             n_results: int = 5, 
             where: Optional[Dict] = None) -> Dict:
        """
        Query the collection with embedding vectors
        
        Args:
            query_embeddings: List of query embedding vectors
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Query results dictionary
        """
        try:
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where
            )
            logger.info(f"Query returned {len(results['ids'][0])} results")
            return results
            
        except Exception as e:
            logger.error(f"Error querying collection: {e}")
            return {'ids': [[]], 'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
    
    def get_by_ids(self, ids: List[str]) -> Dict:
        """
        Get embeddings by IDs
        
        Args:
            ids: List of IDs to retrieve
            
        Returns:
            Retrieved embeddings and metadata
        """
        try:
            results = self.collection.get(ids=ids)
            logger.info(f"Retrieved {len(results['ids'])} embeddings")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving embeddings: {e}")
            return {'ids': [], 'documents': [], 'metadatas': [], 'embeddings': []}
    
    def delete_by_ids(self, ids: List[str]) -> bool:
        """
        Delete embeddings by IDs
        
        Args:
            ids: List of IDs to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} embeddings")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting embeddings: {e}")
            return False
    
    def count(self) -> int:
        """
        Get count of embeddings in collection
        
        Returns:
            Number of embeddings
        """
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error counting embeddings: {e}")
            return 0
    
    def reset_collection(self) -> bool:
        """
        Reset (clear) the collection
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "NBA player statistics embeddings"}
            )
            logger.info(f"Reset collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            return False
    
    def get_collection_info(self) -> Dict:
        """
        Get information about the collection
        
        Returns:
            Collection information dictionary
        """
        return {
            'name': self.collection_name,
            'count': self.count(),
            'metadata': self.collection.metadata
        }


# Global instance
_vector_store = None


def get_vector_store(collection_name: str = "nba_stats_embeddings") -> VectorStore:
    """
    Get or create the global vector store instance
    
    Args:
        collection_name: Name of the ChromaDB collection
        
    Returns:
        VectorStore instance
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(collection_name)
    return _vector_store


def test_vector_store():
    """Test the vector store"""
    print(f"\n{'='*60}")
    print("VECTOR STORE TEST")
    print('='*60)
    
    # Initialize
    store = get_vector_store()
    
    # Get info
    info = store.get_collection_info()
    print(f"\nCollection Info:")
    print(f"  Name: {info['name']}")
    print(f"  Count: {info['count']}")
    print(f"  Metadata: {info['metadata']}")
    
    # Test adding embeddings (dummy data)
    test_ids = ["player_1", "player_2", "player_3"]
    test_embeddings = [
        [0.1, 0.2, 0.3, 0.4, 0.5],
        [0.2, 0.3, 0.4, 0.5, 0.6],
        [0.3, 0.4, 0.5, 0.6, 0.7]
    ]
    test_documents = [
        "LeBron James: 40,474 points in 1,421 games",
        "Kareem Abdul-Jabbar: 38,387 points in 1,560 games",
        "Karl Malone: 36,928 points in 1,476 games"
    ]
    test_metadatas = [
        {"player": "LeBron James", "category": "points"},
        {"player": "Kareem Abdul-Jabbar", "category": "points"},
        {"player": "Karl Malone", "category": "points"}
    ]
    
    print(f"\nAdding {len(test_ids)} test embeddings...")
    success = store.add_embeddings(test_ids, test_embeddings, test_documents, test_metadatas)
    print(f"  Success: {success}")
    
    # Query
    print(f"\nQuerying with test embedding...")
    query_embedding = [[0.15, 0.25, 0.35, 0.45, 0.55]]
    results = store.query(query_embedding, n_results=2)
    
    print(f"\nQuery Results:")
    for i, (doc, meta, dist) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        print(f"  {i+1}. {doc}")
        print(f"     Player: {meta['player']}")
        print(f"     Distance: {dist:.4f}")
    
    # Get updated count
    print(f"\nFinal count: {store.count()}")


if __name__ == "__main__":
    test_vector_store()
