"""
HTML Parser for NBA statistics tables
Extracts and structures table data from raw HTML
"""
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from loguru import logger
import re


class NBATableParser:
    """Parser for NBA statistics tables"""
    
    def __init__(self):
        """Initialize parser"""
        logger.info("NBATableParser initialized")
    
    def parse_html(self, html_content: str) -> List[Dict]:
        """
        Parse HTML content and extract tables
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            List of parsed tables with headers and data
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            tables = []
            
            # Find all tables in the HTML
            html_tables = soup.find_all('table')
            
            for idx, table in enumerate(html_tables):
                parsed_table = self._parse_table(table, idx)
                if parsed_table and parsed_table.get('data'):
                    tables.append(parsed_table)
            
            logger.info(f"Parsed {len(tables)} tables from HTML")
            return tables
            
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return []
    
    def _parse_table(self, table, table_index: int) -> Optional[Dict]:
        """
        Parse a single HTML table
        
        Args:
            table: BeautifulSoup table element
            table_index: Index of table in document
            
        Returns:
            Dictionary with headers and row data
        """
        try:
            # Extract headers
            headers = []
            header_row = table.find('thead')
            
            if header_row:
                header_cells = header_row.find_all(['th', 'td'])
                headers = [self._clean_text(cell.get_text()) for cell in header_cells]
            else:
                # Try to get headers from first row
                first_row = table.find('tr')
                if first_row:
                    header_cells = first_row.find_all(['th', 'td'])
                    headers = [self._clean_text(cell.get_text()) for cell in header_cells]
            
            if not headers:
                logger.warning(f"No headers found in table {table_index}")
                return None
            
            # Extract data rows
            data_rows = []
            tbody = table.find('tbody')
            rows = tbody.find_all('tr') if tbody else table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if not cells:
                    continue
                
                row_data = {}
                for idx, cell in enumerate(cells):
                    if idx < len(headers):
                        # Extract text, handling links
                        text = self._extract_cell_text(cell)
                        row_data[headers[idx]] = text
                
                if row_data:
                    data_rows.append(row_data)
            
            logger.info(f"Table {table_index}: {len(headers)} headers, {len(data_rows)} rows")
            
            return {
                'table_index': table_index,
                'headers': headers,
                'data': data_rows,
                'row_count': len(data_rows)
            }
            
        except Exception as e:
            logger.error(f"Error parsing table {table_index}: {e}")
            return None
    
    def _extract_cell_text(self, cell) -> str:
        """
        Extract text from table cell, handling links and nested elements
        
        Args:
            cell: BeautifulSoup cell element
            
        Returns:
            Cleaned text content
        """
        # Check for links first
        link = cell.find('a')
        if link:
            text = link.get_text()
        else:
            text = cell.get_text()
        
        return self._clean_text(text)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters but keep numbers, letters, spaces, and common punctuation
        text = text.strip()
        
        return text
    
    def parse_player_stats(self, raw_data: Dict) -> List[Dict]:
        """
        Parse player statistics from various formats
        
        Args:
            raw_data: Raw data dictionary with table information
            
        Returns:
            List of player statistics dictionaries
        """
        try:
            headers = raw_data.get('headers', [])
            data_rows = raw_data.get('data', [])
            
            player_stats = []
            
            for row in data_rows:
                player_name = row.get('PLAYER', row.get('Player', ''))
                
                if not player_name or player_name == 'PLAYER':
                    continue
                
                # Create stats dictionary
                stats = {}
                for key, value in row.items():
                    if key != 'PLAYER' and key != 'Player' and key != '#':
                        stats[key] = self._parse_stat_value(value)
                
                player_stats.append({
                    'player_name': player_name,
                    'rank': row.get('#', ''),
                    'stats': stats
                })
            
            logger.info(f"Parsed stats for {len(player_stats)} players")
            return player_stats
            
        except Exception as e:
            logger.error(f"Error parsing player stats: {e}")
            return []
    
    def _parse_stat_value(self, value: str) -> str:
        """
        Parse and clean statistical value
        
        Args:
            value: Raw stat value
            
        Returns:
            Cleaned value
        """
        if not value:
            return ""
        
        # Remove commas from numbers
        value = value.replace(',', '')
        
        # Handle percentages
        if '%' in value:
            return value
        
        return value


def test_parser():
    """Test the HTML parser"""
    # Sample HTML
    sample_html = """
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>PLAYER</th>
                <th>PTS</th>
                <th>GP</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>1</td>
                <td><a href="#">LeBron James</a></td>
                <td>40,474</td>
                <td>1,421</td>
            </tr>
            <tr>
                <td>2</td>
                <td><a href="#">Kareem Abdul-Jabbar</a></td>
                <td>38,387</td>
                <td>1,560</td>
            </tr>
        </tbody>
    </table>
    """
    
    parser = NBATableParser()
    tables = parser.parse_html(sample_html)
    
    print(f"\n{'='*60}")
    print("HTML PARSER TEST")
    print('='*60)
    
    for table in tables:
        print(f"\nTable {table['table_index']}:")
        print(f"  Headers: {table['headers']}")
        print(f"  Rows: {table['row_count']}")
        print(f"\nSample data:")
        for row in table['data'][:2]:
            print(f"  {row}")
        
        # Parse player stats
        player_stats = parser.parse_player_stats(table)
        print(f"\nPlayer stats:")
        for player in player_stats[:2]:
            print(f"  {player['player_name']}: {player['stats']}")


if __name__ == "__main__":
    test_parser()
