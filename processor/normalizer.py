"""
Data normalizer for NBA statistics
Cleans and standardizes player statistics data
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
import re


class StatsNormalizer:
    """Normalizer for NBA statistics data"""
    
    # Standard stat abbreviations and their full names
    STAT_MAPPING = {
        'GP': 'games_played',
        'MIN': 'minutes',
        'PTS': 'points',
        'FGM': 'field_goals_made',
        'FGA': 'field_goals_attempted',
        'FG%': 'field_goal_percentage',
        '3PM': 'three_pointers_made',
        '3PA': 'three_pointers_attempted',
        '3P%': 'three_point_percentage',
        'FTM': 'free_throws_made',
        'FTA': 'free_throws_attempted',
        'FT%': 'free_throw_percentage',
        'OREB': 'offensive_rebounds',
        'DREB': 'defensive_rebounds',
        'REB': 'rebounds',
        'AST': 'assists',
        'STL': 'steals',
        'BLK': 'blocks',
        'TOV': 'turnovers',
        'EFG%': 'effective_field_goal_percentage',
        'TS%': 'true_shooting_percentage',
        'PF': 'personal_fouls'
    }
    
    def __init__(self):
        """Initialize normalizer"""
        logger.info("StatsNormalizer initialized")
    
    def normalize_player_stats(self, player_name: str, stats: Dict[str, Any], 
                               metadata: Optional[Dict] = None) -> Dict:
        """
        Normalize player statistics to standard format
        
        Args:
            player_name: Player name
            stats: Raw statistics dictionary
            metadata: Additional metadata
            
        Returns:
            Normalized statistics dictionary
        """
        try:
            normalized = {
                'player_name': self._normalize_player_name(player_name),
                'stats': {},
                'stats_raw': {},  # Keep original values
                'metadata': {
                    'normalized_at': datetime.utcnow().isoformat(),
                    'season_type': metadata.get('season_type', 'Regular Season') if metadata else 'Regular Season'
                }
            }
            
            # Add additional metadata if provided
            if metadata:
                normalized['metadata'].update({
                    k: v for k, v in metadata.items() 
                    if k not in ['normalized_at', 'season_type']
                })
            
            # Normalize each stat
            for key, value in stats.items():
                # Skip non-stat fields
                if key in ['#', 'PLAYER', 'Player', 'stat_category', 'source_url']:
                    continue
                
                # Store raw value
                normalized['stats_raw'][key] = value
                
                # Get normalized key
                norm_key = self.STAT_MAPPING.get(key, key.lower().replace(' ', '_'))
                
                # Parse and normalize value
                norm_value = self._normalize_stat_value(key, value)
                
                if norm_value is not None:
                    normalized['stats'][norm_key] = norm_value
            
            # Calculate per-game averages if games played is available
            if 'games_played' in normalized['stats']:
                normalized['stats']['per_game'] = self._calculate_per_game_stats(
                    normalized['stats']
                )
            
            logger.debug(f"Normalized stats for {player_name}: {len(normalized['stats'])} stats")
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing stats for {player_name}: {e}")
            return {}
    
    def _normalize_player_name(self, name: str) -> str:
        """
        Normalize player name
        
        Args:
            name: Raw player name
            
        Returns:
            Normalized name
        """
        if not name:
            return ""
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Title case
        name = name.title()
        
        return name
    
    def _normalize_stat_value(self, stat_key: str, value: str) -> Optional[float]:
        """
        Normalize statistical value to appropriate type
        
        Args:
            stat_key: Stat key/name
            value: Raw value as string
            
        Returns:
            Normalized value (int or float)
        """
        if not value or value == '-' or value == 'N/A':
            return None
        
        try:
            # Remove commas
            value = str(value).replace(',', '')
            
            # Handle percentages
            if '%' in stat_key or '%' in value:
                # Remove % sign and convert to decimal
                value = value.replace('%', '')
                return round(float(value), 1)
            
            # Try to convert to number
            if '.' in value:
                return round(float(value), 3)
            else:
                return int(value)
                
        except (ValueError, TypeError):
            logger.warning(f"Could not parse value '{value}' for stat '{stat_key}'")
            return None
    
    def _calculate_per_game_stats(self, stats: Dict) -> Dict:
        """
        Calculate per-game statistics
        
        Args:
            stats: Normalized stats dictionary
            
        Returns:
            Per-game stats dictionary
        """
        per_game = {}
        games = stats.get('games_played', 0)
        
        if games == 0:
            return per_game
        
        # Stats to calculate per-game averages for
        avg_stats = [
            'points', 'rebounds', 'assists', 'steals', 'blocks',
            'minutes', 'turnovers', 'field_goals_made', 'field_goals_attempted',
            'three_pointers_made', 'three_pointers_attempted',
            'free_throws_made', 'free_throws_attempted',
            'offensive_rebounds', 'defensive_rebounds'
        ]
        
        for stat_key in avg_stats:
            if stat_key in stats:
                value = stats[stat_key]
                if isinstance(value, (int, float)):
                    per_game[stat_key] = round(value / games, 2)
        
        return per_game
    
    def normalize_batch(self, players_data: List[Dict]) -> List[Dict]:
        """
        Normalize a batch of player statistics
        
        Args:
            players_data: List of player data dictionaries
            
        Returns:
            List of normalized player statistics
        """
        normalized_players = []
        
        for player_data in players_data:
            player_name = player_data.get('player_name', player_data.get('PLAYER', ''))
            stats = player_data.get('stats', player_data)
            metadata = player_data.get('metadata', {})
            
            if player_name:
                normalized = self.normalize_player_stats(player_name, stats, metadata)
                if normalized:
                    normalized_players.append(normalized)
        
        logger.info(f"Normalized {len(normalized_players)} players")
        return normalized_players
    
    def validate_stats(self, stats: Dict) -> bool:
        """
        Validate normalized statistics
        
        Args:
            stats: Normalized stats dictionary
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if not stats.get('player_name'):
                logger.warning("Missing player_name")
                return False
            
            if not stats.get('stats'):
                logger.warning("Missing stats")
                return False
            
            # Validate percentage values
            percentages = [
                'field_goal_percentage', 'three_point_percentage',
                'free_throw_percentage', 'effective_field_goal_percentage',
                'true_shooting_percentage'
            ]
            
            for pct_key in percentages:
                if pct_key in stats['stats']:
                    value = stats['stats'][pct_key]
                    if value < 0 or value > 100:
                        logger.warning(f"Invalid percentage for {pct_key}: {value}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating stats: {e}")
            return False


def test_normalizer():
    """Test the stats normalizer"""
    # Sample raw stats
    sample_stats = {
        'PLAYER': 'LeBron James',
        'GP': '1,421',
        'MIN': '54,637',
        'PTS': '40,474',
        'FG%': '50.5',
        'AST': '10,934',
        'REB': '11,373',
        'STL': '2,267',
        'BLK': '1,095'
    }
    
    normalizer = StatsNormalizer()
    
    print(f"\n{'='*60}")
    print("STATS NORMALIZER TEST")
    print('='*60)
    
    print(f"\nRaw stats:")
    for key, value in sample_stats.items():
        print(f"  {key}: {value}")
    
    # Normalize
    normalized = normalizer.normalize_player_stats(
        player_name=sample_stats['PLAYER'],
        stats=sample_stats,
        metadata={'season_type': 'Regular Season', 'source': 'test'}
    )
    
    print(f"\nNormalized stats:")
    print(f"  Player: {normalized['player_name']}")
    print(f"  Stats count: {len(normalized['stats'])}")
    print(f"\nNormalized values:")
    for key, value in normalized['stats'].items():
        if key != 'per_game':
            print(f"  {key}: {value}")
    
    if 'per_game' in normalized['stats']:
        print(f"\nPer-game averages:")
        for key, value in normalized['stats']['per_game'].items():
            print(f"  {key}: {value}")
    
    print(f"\nMetadata:")
    for key, value in normalized['metadata'].items():
        print(f"  {key}: {value}")
    
    # Validate
    is_valid = normalizer.validate_stats(normalized)
    print(f"\nValidation: {'✓ PASSED' if is_valid else '✗ FAILED'}")


if __name__ == "__main__":
    test_normalizer()
