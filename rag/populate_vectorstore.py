"""
Script to populate ChromaDB with NBA player statistics from MongoDB
"""
import sys
from pathlib import Path
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from scraper.storage import get_storage
from rag.vector_store import get_vector_store
from rag.embedder import StatsEmbedder

# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)


def populate_vector_store(batch_size: int = 50, reset: bool = False):
    """
    Populate ChromaDB with embeddings from MongoDB
    
    Args:
        batch_size: Number of players to process in each batch
        reset: Whether to reset the collection first
    """
    print(f"\n{'='*60}")
    print("POPULATING VECTOR STORE")
    print('='*60)
    
    # Initialize components
    storage = get_storage()
    vector_store = get_vector_store()
    embedder = StatsEmbedder()
    
    # Reset collection if requested
    if reset:
        print(f"\nResetting collection...")
        vector_store.reset_collection()
        print(f"  ✓ Collection reset")
    
    # Get player stats from MongoDB
    print(f"\nFetching player stats from MongoDB...")
    player_docs = list(storage.processed_data.find().limit(batch_size))
    
    if not player_docs:
        print(f"  ⚠ No player stats found in MongoDB")
        print(f"  Run scraping first to populate data")
        return
    
    print(f"  Found {len(player_docs)} players")
    
    # Prepare player data for embedding
    players_data = []
    for doc in player_docs:
        player_name = doc.get('player_name', '')
        stats = doc.get('stats', {})
        metadata = doc.get('metadata', {})
        
        if player_name:
            players_data.append({
                'player_name': player_name,
                'stats': stats,
                'metadata': metadata
            })
    
    # Generate embeddings
    print(f"\nGenerating embeddings for {len(players_data)} players...")
    embedded_players = embedder.embed_players_batch(players_data)
    
    if not embedded_players:
        print(f"  ✗ Failed to generate embeddings")
        return
    
    print(f"  ✓ Generated {len(embedded_players)} embeddings")
    
    # Prepare data for ChromaDB
    ids = [f"player_{player['player_name'].replace(' ', '_')}" for player in embedded_players]
    embeddings = [player['embedding'] for player in embedded_players]
    documents = [player['text'] for player in embedded_players]
    
    # Convert metadata to ChromaDB-compatible format (strings, ints, floats, bools only)
    metadatas = []
    for player in embedded_players:
        metadata = {'player': player['player_name']}
        
        # Add safe metadata fields
        for key, value in player['metadata'].items():
            if isinstance(value, (str, int, float, bool)):
                metadata[key] = value
            elif value is not None:
                metadata[key] = str(value)  # Convert other types to string
        
        metadatas.append(metadata)
    
    # Add to vector store
    print(f"\nAdding embeddings to ChromaDB...")
    success = vector_store.add_embeddings(ids, embeddings, documents, metadatas)
    
    if success:
        print(f"  ✓ Successfully added {len(ids)} embeddings to vector store")
    else:
        print(f"  ✗ Failed to add embeddings")
    
    # Show collection info
    info = vector_store.get_collection_info()
    print(f"\nCollection Info:")
    print(f"  Name: {info['name']}")
    print(f"  Total embeddings: {info['count']}")
    
    # Show sample embeddings
    print(f"\nSample embeddings:")
    for i in range(min(5, len(embedded_players))):
        player = embedded_players[i]
        print(f"  {i+1}. {player['player_name']}")
        print(f"     {player['text'][:100]}...")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Populate ChromaDB with NBA player embeddings')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size for processing')
    parser.add_argument('--reset', action='store_true', help='Reset collection before populating')
    
    args = parser.parse_args()
    
    populate_vector_store(batch_size=args.batch_size, reset=args.reset)
