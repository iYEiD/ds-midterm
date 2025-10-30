"""
Text embedder for NBA statistics using OpenAI
Converts player stats to descriptive text and generates embeddings
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

# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)


class StatsEmbedder:
    """Embedder for NBA statistics"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_EMBEDDING_MODEL
        logger.info(f"StatsEmbedder initialized with model: {self.model}")
    
    def stats_to_text(self, player_name: str, stats: Dict, metadata: Optional[Dict] = None) -> str:
        """
        Convert player statistics to descriptive text
        
        Args:
            player_name: Player name
            stats: Statistics dictionary
            metadata: Optional metadata
            
        Returns:
            Descriptive text representation
        """
        # Get key stats
        games_played = stats.get('games_played', stats.get('GP', 'N/A'))
        points = stats.get('points', stats.get('PTS', 'N/A'))
        rebounds = stats.get('rebounds', stats.get('REB', 'N/A'))
        assists = stats.get('assists', stats.get('AST', 'N/A'))
        steals = stats.get('steals', stats.get('STL', 'N/A'))
        blocks = stats.get('blocks', stats.get('BLK', 'N/A'))
        fg_pct = stats.get('field_goal_percentage', stats.get('FG%', 'N/A'))
        
        # Build descriptive text
        text_parts = [f"{player_name} NBA Statistics"]
        
        # Season type if available
        if metadata and 'season_type' in metadata:
            text_parts.append(f"Season: {metadata['season_type']}")
        
        # Career stats
        text_parts.append(f"Games played: {games_played}")
        text_parts.append(f"Total points: {points}")
        text_parts.append(f"Total rebounds: {rebounds}")
        text_parts.append(f"Total assists: {assists}")
        text_parts.append(f"Total steals: {steals}")
        text_parts.append(f"Total blocks: {blocks}")
        
        if fg_pct != 'N/A':
            text_parts.append(f"Field goal percentage: {fg_pct}%")
        
        # Per-game stats if available
        if 'per_game' in stats:
            per_game = stats['per_game']
            ppg = per_game.get('points', 'N/A')
            rpg = per_game.get('rebounds', 'N/A')
            apg = per_game.get('assists', 'N/A')
            
            text_parts.append(f"Per game: {ppg} points, {rpg} rebounds, {apg} assists")
        
        # Stat category if specified
        if metadata and 'stat_category' in metadata:
            category = metadata['stat_category']
            text_parts.append(f"Leader category: {category}")
        
        return ". ".join(text_parts) + "."
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using OpenAI
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding of dimension {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            embeddings = [item.embedding for item in response.data]
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [None] * len(texts)
    
    def embed_player_stats(self, player_name: str, stats: Dict, 
                          metadata: Optional[Dict] = None) -> Optional[Dict]:
        """
        Convert player stats to text and generate embedding
        
        Args:
            player_name: Player name
            stats: Statistics dictionary
            metadata: Optional metadata
            
        Returns:
            Dictionary with text, embedding, and metadata
        """
        # Convert to text
        text = self.stats_to_text(player_name, stats, metadata)
        
        # Generate embedding
        embedding = self.generate_embedding(text)
        
        if embedding is None:
            return None
        
        return {
            'player_name': player_name,
            'text': text,
            'embedding': embedding,
            'metadata': metadata or {}
        }
    
    def embed_players_batch(self, players_data: List[Dict]) -> List[Dict]:
        """
        Embed multiple players' statistics
        
        Args:
            players_data: List of player data dictionaries
            
        Returns:
            List of embedding dictionaries
        """
        # Convert all to text
        texts = []
        player_info = []
        
        for player_data in players_data:
            player_name = player_data.get('player_name', '')
            stats = player_data.get('stats', {})
            metadata = player_data.get('metadata', {})
            
            if player_name:
                text = self.stats_to_text(player_name, stats, metadata)
                texts.append(text)
                player_info.append({
                    'player_name': player_name,
                    'text': text,
                    'metadata': metadata
                })
        
        # Generate embeddings in batch
        embeddings = self.generate_embeddings_batch(texts)
        
        # Combine results
        results = []
        for info, embedding in zip(player_info, embeddings):
            if embedding:
                results.append({
                    **info,
                    'embedding': embedding
                })
        
        logger.info(f"Successfully embedded {len(results)} players")
        return results


def test_embedder():
    """Test the embedder"""
    print(f"\n{'='*60}")
    print("STATS EMBEDDER TEST")
    print('='*60)
    
    # Initialize
    embedder = StatsEmbedder()
    
    # Test data
    test_player = {
        'player_name': 'LeBron James',
        'stats': {
            'games_played': 1421,
            'points': 40474,
            'rebounds': 11373,
            'assists': 10934,
            'steals': 2267,
            'blocks': 1095,
            'field_goal_percentage': 50.5,
            'per_game': {
                'points': 28.48,
                'rebounds': 8.0,
                'assists': 7.69
            }
        },
        'metadata': {
            'season_type': 'Regular Season',
            'stat_category': 'points'
        }
    }
    
    # Convert to text
    print(f"\nPlayer: {test_player['player_name']}")
    text = embedder.stats_to_text(
        test_player['player_name'],
        test_player['stats'],
        test_player['metadata']
    )
    print(f"\nGenerated text:")
    print(f"  {text}")
    
    # Generate embedding
    print(f"\nGenerating embedding...")
    result = embedder.embed_player_stats(
        test_player['player_name'],
        test_player['stats'],
        test_player['metadata']
    )
    
    if result:
        print(f"  ✓ Success!")
        print(f"  Embedding dimension: {len(result['embedding'])}")
        print(f"  First 5 values: {result['embedding'][:5]}")
    else:
        print(f"  ✗ Failed")
    
    # Test batch embedding
    print(f"\nTesting batch embedding with 2 players...")
    batch_data = [
        test_player,
        {
            'player_name': 'Michael Jordan',
            'stats': {
                'games_played': 1072,
                'points': 32292,
                'rebounds': 6672,
                'assists': 5633
            },
            'metadata': {'season_type': 'Regular Season'}
        }
    ]
    
    batch_results = embedder.embed_players_batch(batch_data)
    print(f"  Successfully embedded: {len(batch_results)} players")
    for i, res in enumerate(batch_results, 1):
        print(f"  {i}. {res['player_name']} - {len(res['embedding'])} dimensions")


if __name__ == "__main__":
    test_embedder()
