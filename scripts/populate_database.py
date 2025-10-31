#!/usr/bin/env python3
"""
Script to populate the NBA stats database with more players.
This submits scraping jobs for a list of popular NBA players.
"""

import requests
import sys

API_URL = "http://localhost:8000/api/v1/scrape/submit"

# List of popular NBA players to scrape
PLAYER_URLS = [
    # Current superstars
    "https://www.basketball-reference.com/players/j/jamesle01.html",  # LeBron James
    "https://www.basketball-reference.com/players/c/curryst01.html",  # Stephen Curry
    "https://www.basketball-reference.com/players/d/duranke01.html",  # Kevin Durant
    "https://www.basketball-reference.com/players/a/antetgi01.html",  # Giannis Antetokounmpo
    "https://www.basketball-reference.com/players/j/jokicni01.html",  # Nikola Jokic
    "https://www.basketball-reference.com/players/e/embiijo01.html",  # Joel Embiid
    "https://www.basketball-reference.com/players/d/doncilu01.html",  # Luka Doncic
    "https://www.basketball-reference.com/players/t/tatumja01.html",  # Jayson Tatum
    "https://www.basketball-reference.com/players/b/bookede01.html",  # Devin Booker
    "https://www.basketball-reference.com/players/l/lillada01.html",  # Damian Lillard
    
    # All-time greats
    "https://www.basketball-reference.com/players/j/jordami01.html",  # Michael Jordan
    "https://www.basketball-reference.com/players/b/bryanko01.html",  # Kobe Bryant
    "https://www.basketball-reference.com/players/o/onealsh01.html",  # Shaquille O'Neal
    "https://www.basketball-reference.com/players/d/duncati01.html",  # Tim Duncan
    "https://www.basketball-reference.com/players/b/bryanko01.html",  # Kobe Bryant
    "https://www.basketball-reference.com/players/n/nowitdi01.html",  # Dirk Nowitzki
    "https://www.basketball-reference.com/players/w/wadedw01.html",   # Dwyane Wade
    "https://www.basketball-reference.com/players/p/paulch01.html",   # Chris Paul
    "https://www.basketball-reference.com/players/h/hardeja01.html",  # James Harden
    "https://www.basketball-reference.com/players/w/westbru01.html",  # Russell Westbrook
    
    # Rising stars
    "https://www.basketball-reference.com/players/y/youngtr01.html",  # Trae Young
    "https://www.basketball-reference.com/players/m/murraja01.html",  # Jamal Murray
    "https://www.basketball-reference.com/players/b/ballla01.html",   # LaMelo Ball
    "https://www.basketball-reference.com/players/m/moblewi01.html",  # Evan Mobley
    "https://www.basketball-reference.com/players/b/bartode01.html",  # Desmond Bane
]

def submit_scraping_job(urls):
    """Submit a scraping job to the API."""
    try:
        response = requests.post(
            API_URL,
            json={"urls": urls},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error submitting job: {e}")
        return None

def main():
    print("NBA Stats Database Populator")
    print("=" * 50)
    print(f"Submitting {len(PLAYER_URLS)} player URLs for scraping...")
    
    result = submit_scraping_job(PLAYER_URLS)
    
    if result:
        print(f"\n✅ Job submitted successfully!")
        print(f"Job ID: {result.get('job_id', 'N/A')}")
        print(f"Status: {result.get('status', 'N/A')}")
        print(f"Message: {result.get('message', 'N/A')}")
        print("\nThe scraping workers will process these URLs in the background.")
        print("Check the Dashboard to see the data populate!")
    else:
        print("\n❌ Failed to submit job.")
        sys.exit(1)

if __name__ == "__main__":
    main()
