from sportradar_client import SportradarClient
import os
from dotenv import load_dotenv
import json

load_dotenv()
API_KEY = os.getenv("SPORTRADAR_API_KEY")

if API_KEY:
    client = SportradarClient(API_KEY)
    # Virat Kohli's ID (or a known player ID)
    # We need a valid ID. Let's try to get one from live schedule or knowledge base if possible.
    # For this test, I'll use a hardcoded common ID if I can find one, 
    # OR I'll search for a player first if there was a search endpoint (there isn't one easily accessible without looking up).
    # Let's rely on the fact that we might have an ID from previous logs? 
    # Actually, let's just fetch a live match, get a player ID, and then fetch their profile.
    
    print("Fetching live schedule to find a player...")
    live = client.get_live_schedule()
    if live and 'sport_events' in live and len(live['sport_events']) > 0:
        match_id = live['sport_events'][0]['id']
        print(f"Found match: {match_id}. Fetching summary...")
        summary = client.get_match_summary(match_id)
        if summary and 'statistics' in summary:
            teams = summary.get('statistics', {}).get('teams', [])
            if teams:
                 player = teams[0].get('players', [])[0]
                 player_id = player.get('id')
                 player_name = player.get('name')
                 print(f"Fetching profile for {player_name} ({player_id})...")
                 
                 profile = client.get_player_profile(player_id)
                 print(json.dumps(profile, indent=2))
        else:
            print("No statistics in summary.")
    else:
        print("No live matches. Cannot dynamically find ID.")
else:
    print("No API Key.")
