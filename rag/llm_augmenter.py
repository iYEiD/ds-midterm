"""
LLM augmenter for NBA statistics using OpenAI GPT-4
Combines retrieved stats with LLM to generate contextual responses
"""
from openai import OpenAI
from typing import List, Dict, Optional
from loguru import logger
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from rag.retriever import StatsRetriever

# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)


class LLMAugmenter:
    """LLM augmenter for NBA statistics"""
    
    def __init__(self):
        """Initialize OpenAI client and retriever"""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.retriever = StatsRetriever()
        logger.info(f"LLMAugmenter initialized with model: {self.model}")
    
    def create_prompt(self, query: str, retrieved_stats: List[Dict]) -> str:
        """
        Create prompt for LLM with query and retrieved stats
        
        Args:
            query: User query
            retrieved_stats: Retrieved player statistics
            
        Returns:
            Formatted prompt
        """
        # Build context from retrieved stats
        context_parts = ["Relevant NBA Player Statistics:\n"]
        
        for idx, stat in enumerate(retrieved_stats, 1):
            player = stat['metadata'].get('player', 'Unknown')
            document = stat['document']
            similarity = stat.get('similarity_score', 0)
            
            context_parts.append(f"{idx}. {player} (relevance: {similarity:.2f})")
            context_parts.append(f"   {document}\n")
        
        context = "\n".join(context_parts)
        
        # Create prompt
        prompt = f"""You are an expert NBA statistics analyst. Based on the following player statistics, answer the user's question accurately and insightfully.

{context}

User Question: {query}

Instructions:
- Provide a clear, accurate answer based on the statistics provided
- Include specific numbers and comparisons when relevant
- Offer insights about era differences, playing styles, or historical context if applicable
- Be concise but informative
- If the statistics don't fully answer the question, acknowledge that

Answer:"""
        
        return prompt
    
    def generate_response(self, query: str, top_k: int = 5, 
                         temperature: float = 0.7) -> Dict:
        """
        Generate response for a query using RAG
        
        Args:
            query: User query
            top_k: Number of results to retrieve
            temperature: LLM temperature (0-1)
            
        Returns:
            Dictionary with query, response, and retrieved stats
        """
        try:
            # Retrieve relevant stats
            logger.info(f"Processing query: '{query}'")
            retrieved_stats = self.retriever.retrieve(query, top_k=top_k)
            
            if not retrieved_stats:
                return {
                    'query': query,
                    'response': "I couldn't find relevant statistics to answer your question. The database may not have been populated yet.",
                    'retrieved_stats': [],
                    'status': 'no_results'
                }
            
            # Create prompt
            prompt = self.create_prompt(query, retrieved_stats)
            
            # Generate response with GPT-4
            logger.info(f"Generating response with {self.model}")
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert NBA statistics analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=500
            )
            
            response_text = completion.choices[0].message.content
            
            logger.info(f"Response generated successfully")
            return {
                'query': query,
                'response': response_text,
                'retrieved_stats': retrieved_stats,
                'status': 'success',
                'model': self.model,
                'tokens_used': completion.usage.total_tokens
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'query': query,
                'response': f"Error generating response: {str(e)}",
                'retrieved_stats': [],
                'status': 'error'
            }
    
    def compare_players(self, player1: str, player2: str) -> Dict:
        """
        Generate comparison between two players
        
        Args:
            player1: First player name
            player2: Second player name
            
        Returns:
            Comparison response
        """
        query = f"Compare {player1} and {player2}. Who had the better career and why?"
        return self.generate_response(query, top_k=6)
    
    def get_leaders(self, category: str, top_n: int = 10) -> Dict:
        """
        Get and explain leaders in a specific category
        
        Args:
            category: Stat category
            top_n: Number of leaders to retrieve
            
        Returns:
            Leaders response
        """
        query = f"Who are the top {top_n} leaders in {category} in NBA history? Provide insights about their dominance."
        return self.generate_response(query, top_k=top_n)
    
    def answer_custom_query(self, query: str) -> Dict:
        """
        Answer a custom query about NBA statistics
        
        Args:
            query: User query
            
        Returns:
            Response dictionary
        """
        return self.generate_response(query, top_k=5)


def test_llm_augmenter():
    """Test the LLM augmenter"""
    print(f"\n{'='*60}")
    print("LLM AUGMENTER TEST")
    print('='*60)
    
    # Initialize
    augmenter = LLMAugmenter()
    
    # Check if collection has data
    info = augmenter.retriever.get_collection_stats()
    print(f"\nCollection status:")
    print(f"  Embeddings: {info['count']}")
    
    if info['count'] == 0:
        print("\n⚠ No embeddings in collection.")
        print("  Creating test embeddings...")
        
        # Add test data to vector store
        from rag.embedder import StatsEmbedder
        embedder = StatsEmbedder()
        
        test_players = [
            {
                'player_name': 'LeBron James',
                'stats': {'games_played': 1421, 'points': 40474, 'rebounds': 11373, 'assists': 10934},
                'metadata': {'season_type': 'Regular Season', 'stat_category': 'points'}
            },
            {
                'player_name': 'Kareem Abdul-Jabbar',
                'stats': {'games_played': 1560, 'points': 38387, 'rebounds': 17440, 'assists': 5660},
                'metadata': {'season_type': 'Regular Season', 'stat_category': 'points'}
            }
        ]
        
        # Embed and store
        embedded = embedder.embed_players_batch(test_players)
        
        ids = [f"player_{i}" for i in range(len(embedded))]
        embeddings = [e['embedding'] for e in embedded]
        documents = [e['text'] for e in embedded]
        metadatas = [{'player': e['player_name'], **e['metadata']} for e in embedded]
        
        augmenter.retriever.vector_store.add_embeddings(ids, embeddings, documents, metadatas)
        print(f"  ✓ Added {len(embedded)} test embeddings")
    
    # Test query
    print(f"\n{'='*60}")
    print("Testing RAG Query")
    print('='*60)
    
    test_query = "Who is the all-time leading scorer in NBA history?"
    print(f"\nQuery: '{test_query}'")
    print("\nGenerating response...")
    
    result = augmenter.generate_response(test_query, top_k=3)
    
    print(f"\nStatus: {result['status']}")
    if result['status'] == 'success':
        print(f"Model: {result['model']}")
        print(f"Tokens used: {result.get('tokens_used', 'N/A')}")
        print(f"\nRetrieved stats: {len(result['retrieved_stats'])}")
        for i, stat in enumerate(result['retrieved_stats'], 1):
            player = stat['metadata'].get('player', 'Unknown')
            print(f"  {i}. {player}")
        
        print(f"\nResponse:")
        print(f"  {result['response']}")
    else:
        print(f"Error: {result['response']}")


if __name__ == "__main__":
    test_llm_augmenter()
