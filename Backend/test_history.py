from tools import fetch_player_career_stats, fetch_live_match_context
import json

def test_history():
    print("--- Testing Historical Stats Tool ---")
    # We will try to fetch stats for a dummy ID or a known one if we can get it.
    # Since we don't have a known valid ID handy without a live match, 
    # we will rely on how the tool handles a "Not Found" or invalid ID first,
    # or ideally correct handling if we had one.
    
    # Let's try to mock or just call it with a random ID structure
    # Real API might 404, but we want to see if the tool code crashes.
    print(fetch_player_career_stats.invoke({"player_id": "sr:player:123456"}))

if __name__ == "__main__":
    test_history()
