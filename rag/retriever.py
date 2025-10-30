"""
Retriever for NBA statistics using ChromaDB and OpenAI embeddings
"""
from typing import List, Dict, Optional
from loguru import logger
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from rag.vector_store import get_vector_store
from rag.embedder import StatsEmbedder

# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)


class StatsRetriever:
    """Retriever for NBA statistics"""
    
    def __init__(self, collection_name: str = "nba_stats_embeddings"):
        """
        Initialize retriever
        
        Args:
            collection_name: ChromaDB collection name
        """
        self.vector_store = get_vector_store(collection_name)
        self.embedder = StatsEmbedder()
        logger.info("StatsRetriever initialized")
    
    def retrieve(self, query: str, top_k: int = 5, 
                filters: Optional[Dict] = None) -> List[Dict]:
        """
        Retrieve relevant player statistics for a query
        
        Args:
            query: Natural language query
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of retrieved results with stats and similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embedder.generate_embedding(query)
            
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            # Query vector store
            results = self.vector_store.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters
            )
            
            # Format results
            retrieved = []
            for idx in range(len(results['ids'][0])):
                retrieved.append({
                    'id': results['ids'][0][idx],
                    'document': results['documents'][0][idx],
                    'metadata': results['metadatas'][0][idx],
                    'distance': results['distances'][0][idx],
                    'similarity_score': 1 - results['distances'][0][idx]  # Convert distance to similarity
                })
            
            logger.info(f"Retrieved {len(retrieved)} results for query: '{query}'")
            return retrieved
            
        except Exception as e:
            logger.error(f"Error retrieving results: {e}")
            return []
    
    def retrieve_by_player(self, player_name: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve statistics for a specific player
        
        Args:
            player_name: Player name to search for
            top_k: Number of results to return
            
        Returns:
            List of retrieved results
        """
        query = f"Statistics for {player_name}"
        return self.retrieve(query, top_k=top_k)
    
    def retrieve_by_category(self, category: str, top_k: int = 10) -> List[Dict]:
        """
        Retrieve top players in a specific category
        
        Args:
            category: Stat category (points, rebounds, assists, steals, blocks)
            top_k: Number of results to return
            
        Returns:
            List of retrieved results
        """
        queries = {
            'points': 'Who are the all-time leading scorers in NBA history?',
            'rebounds': 'Who are the all-time leading rebounders in NBA history?',
            'assists': 'Who are the all-time leaders in assists in NBA history?',
            'steals': 'Who are the all-time leaders in steals in NBA history?',
            'blocks': 'Who are the all-time leaders in blocks in NBA history?'
        }
        
        query = queries.get(category.lower(), f"Top {category} leaders in NBA history")
        return self.retrieve(query, top_k=top_k)
    
    def compare_players(self, player1: str, player2: str) -> Dict:
        """
        Retrieve and compare statistics for two players
        
        Args:
            player1: First player name
            player2: Second player name
            
        Returns:
            Dictionary with both players' stats
        """
        results1 = self.retrieve_by_player(player1, top_k=1)
        results2 = self.retrieve_by_player(player2, top_k=1)
        
        return {
            'player1': results1[0] if results1 else None,
            'player2': results2[0] if results2 else None,
            'comparison_query': f"Compare {player1} and {player2}"
        }
    
    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the vector store collection
        
        Returns:
            Collection statistics
        """
        return self.vector_store.get_collection_info()


def test_retriever():
    """Test the retriever"""
    print(f"\n{'='*60}")
    print("STATS RETRIEVER TEST")
    print('='*60)
    
    # Initialize
    retriever = StatsRetriever()
    
    # Check collection
    info = retriever.get_collection_stats()
    print(f"\nCollection Info:")
    print(f"  Name: {info['name']}")
    print(f"  Count: {info['count']}")
    
    if info['count'] == 0:
        print("\n⚠ No embeddings in collection. Run embedding script first.")
        print("  Skipping retrieval tests.")
        return
    
    # Test queries
    test_queries = [
        "Who is the all-time leading scorer?",
        "Best point guards in history",
        "Players with most steals"
    ]
    
    print(f"\nTesting retrieval with sample queries:")
    for query in test_queries:
        print(f"\n  Query: '{query}'")
        results = retriever.retrieve(query, top_k=3)
        
        if results:
            print(f"  Results ({len(results)}):")
            for i, result in enumerate(results, 1):
                player = result['metadata'].get('player', 'Unknown')
                similarity = result['similarity_score']
                print(f"    {i}. {player} (similarity: {similarity:.4f})")
                print(f"       {result['document'][:80]}...")
        else:
            print(f"  No results found")
    
    # Test player comparison
    print(f"\n  Testing player comparison:")
    comparison = retriever.compare_players("LeBron James", "Michael Jordan")
    
    if comparison['player1'] and comparison['player2']:
        print(f"    Player 1: {comparison['player1']['metadata'].get('player', 'Unknown')}")
        print(f"    Player 2: {comparison['player2']['metadata'].get('player', 'Unknown')}")
    else:
        print(f"    ⚠ Could not find both players in collection")


if __name__ == "__main__":
    test_retriever()
