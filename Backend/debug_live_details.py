import os
import json
import traceback
from dotenv import load_dotenv
from sportradar_client import SportradarClient

load_dotenv()
api_key = os.getenv("SPORTRADAR_API_KEY")
client = SportradarClient(api_key)

def debug_match_details(match_id):
    with open("debug_live_log.txt", "w", encoding="utf-8") as f:
        try:
            f.write(f"Fetching summary for {match_id}...\n")
            summary = client.get_match_summary(match_id)
            
            if not summary:
                f.write("No summary returned.\n")
                return

            # 1. Check Sport Event Status (often has overs/RR)
            status = summary.get('sport_event_status', {})
            f.write(f"Status Keys: {list(status.keys())}\n")
            f.write(f"Status Dump: {json.dumps(status, indent=2)}\n")

            # 2. Check Statistics -> Innings (often has over-by-over data)
            stats = summary.get('statistics', {})
            if 'innings' in stats:
                innings = stats['innings']
                f.write(f"Innings found: {len(innings)}\n")
                for i, inn in enumerate(innings):
                    f.write(f"--- Inning {i+1} ---\n")
                    f.write(f"Keys: {list(inn.keys())}\n")
                    f.write(f"Dump: {json.dumps(inn, indent=2)}\n")
            else:
                 f.write("'innings' NOT found in statistics.\n")
                 
        except Exception as e:
            f.write(f"Error: {traceback.format_exc()}\n")

if __name__ == "__main__":
    # Sri Lanka vs Zimbabwe
    debug_match_details('sr:match:66187896')
