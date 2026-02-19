
import os
import requests
import functools
import time
from datetime import datetime, timedelta

class SportradarClient:
    """
    Cricket Client for Sportradar API.
    Handles API requests, rate limiting, and basic error handling.
    """
    def __init__(self, api_key, access_level='t', language_code='en', timeout=10):
        self.api_key = api_key
        # Restore real URL
        self.base_url = "https://api.sportradar.com/cricket-{access_level}2/{language_code}".format(
            access_level=access_level,
            language_code=language_code
        )
        self.timeout = timeout
        self.last_request_time = 0

    def _get(self, endpoint, params=None):
        if params is None:
            params = {}
        params['api_key'] = self.api_key
        
        # RATE LIMITING: Enforce ~1 request per second (1 QPS limit)
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < 1.2:  # Wait 1.2s to be safe
            sleep_time = 1.2 - time_since_last
            print(f"⏳ Rate Limit: Sleeping for {sleep_time:.2f}s...")
            time.sleep(sleep_time)
        
        url = f"{self.base_url}{endpoint}"
        print(f"📡 [Sportradar API] Requesting: {endpoint}")
        
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            self.last_request_time = time.time() # Update time after request
            
            if response.status_code == 429:
                print("⚠️ Quota Exceeded (429). Waiting 2 seconds before retry...")
                time.sleep(2)
                response = requests.get(url, params=params, timeout=self.timeout)
                self.last_request_time = time.time()

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    @functools.lru_cache(maxsize=32)
    def get_daily_schedule(self, date_str):
        """
        Fetches the daily schedule for a formatted date string YYYY-MM-DD.
        Cached, but respects rate limits on fetch.
        """
        endpoint = f"/schedules/{date_str}/schedule.json"
        return self._get(endpoint)

    def get_live_schedule(self):
        """
        Fetches the schedule for currently live matches.
        """
        endpoint = "/schedules/live/schedule.json"
        return self._get(endpoint)

    @functools.lru_cache(maxsize=10)
    def get_match_summary(self, match_id):
        """
        Fetches the summary for a specific match.
        Cached for single-turn analysis.
        """
        # Correct endpoint for match summary
        endpoint = f"/matches/{match_id}/summary.json"
        return self._get(endpoint)

    @functools.lru_cache(maxsize=10)
    def get_player_profile(self, player_id):
        """
        Fetches the profile and statistics for a specific player.
        """
        endpoint = f"/players/{player_id}/profile.json"
        return self._get(endpoint)

    @functools.lru_cache(maxsize=5)
    def get_team_profile(self, team_id):
        """
        Fetches the team profile, including the current player roster.
        """
        endpoint = f"/teams/{team_id}/profile.json"
        return self._get(endpoint)

# Simple test block
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    API_KEY = os.getenv("SPORTRADAR_API_KEY")
    if API_KEY:
        client = SportradarClient(API_KEY)
        
        # Test Live Schedule
        print("Fetching Live Schedule...")
        live = client.get_live_schedule()
        if live:
            print(f"Live matches found: {len(live.get('sport_events', []))}")
            if live.get('sport_events'):
                first_match = live['sport_events'][0]
                print(f"First match: {first_match.get('competitors', [{},{}])[0].get('name')} vs {first_match.get('competitors', [{},{}])[1].get('name')}")
                match_id = first_match['id']
                
                # Test Summary
                print(f"Fetching Summary for {match_id}...")
                summary = client.get_match_summary(match_id)
                if summary:
                    print("Summary fetched successfully.")
        else:
            print("No live matches or error fetching.")
            
        # Test Daily Schedule
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"Fetching Daily Schedule for {today}...")
        schedule = client.get_daily_schedule(today)
        if schedule:
             print(f"Scheduled matches today: {len(schedule.get('sport_events', []))}")
    else:
        print("SPORTRADAR_API_KEY not set.")
