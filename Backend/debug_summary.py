from sportradar_client import SportradarClient
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
client = SportradarClient(os.getenv('SPORTRADAR_API_KEY'))

# Fetch daily schedule to find a completed match
today = datetime.now().strftime("%Y-%m-%d")
schedule = client.get_daily_schedule(today)
events = schedule.get('sport_events', []) if schedule else []

completed_match_id = None
for evt in events:
    if evt.get('sport_event_status', {}).get('status') == 'ended':
        completed_match_id = evt.get('id')
        print(f"Found completed match: {evt.get('competitors', [{},{}])[0].get('name')} vs {evt.get('competitors', [{},{}])[1].get('name')} ({completed_match_id})")
        break

if completed_match_id:
    print(f"Fetching summary for {completed_match_id}...")
    summary = client.get_match_summary(completed_match_id)
    if summary:
        print(json.dumps(summary, indent=2))
    else:
        print("Summary is None")
else:
    print("No ended matches found in today's schedule to test with.")
