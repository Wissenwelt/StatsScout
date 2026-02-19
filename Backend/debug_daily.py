from sportradar_client import SportradarClient
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

key = os.getenv('SPORTRADAR_API_KEY')
if not key:
    print("No API Key found")
    exit(1)

client = SportradarClient(key)
today = datetime.now().strftime('%Y-%m-%d')
print(f"Checking schedule for: {today}")

try:
    with open('debug_output_utf8.txt', 'w', encoding='utf-8') as f:
        schedule = client.get_daily_schedule(today)
        if not schedule:
            f.write("Schedule is None or empty response\n")
        else:
            events = schedule.get('sport_events', [])
            f.write(f"Total Events Found: {len(events)}\n")
            
            for i, match in enumerate(events):
                status = match.get('sport_event_status', {}).get('status', 'Unknown')
                competitors = match.get('competitors', [])
                t1 = competitors[0].get('name', 'T1') if len(competitors) > 0 else 'Unknown'
                t2 = competitors[1].get('name', 'T2') if len(competitors) > 1 else 'Unknown'
                start_time = match.get('scheduled', 'No Time')
                f.write(f"{i+1}. [{status}] {t1} vs {t2} (ID: {match.get('id')}) Time: {start_time}\n")
    print("Done writing to debug_output_utf8.txt")
            
except Exception as e:
    print(f"Error: {e}")
