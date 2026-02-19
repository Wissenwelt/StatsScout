import os
import json
from tools import fetch_live_match_context, check_scouting_notes
from dotenv import load_dotenv

load_dotenv()

def test_tools():
    print("Testing fetch_live_match_context...")
    live_context = fetch_live_match_context.invoke({})
    print(f"Live Context: {live_context[:500]}...") # Truncate for display

    print("\nTesting check_scouting_notes for Player...")
    notes = check_scouting_notes.invoke("V. Kohli")
    print(f"Notes for V. Kohli: {notes}")
    
    print("\nTesting check_scouting_notes for Team...")
    team_notes = check_scouting_notes.invoke("India")
    print(f"Notes for India: {team_notes}")

    print("\nTesting check_scouting_notes for Missing Entry...")
    notes_fail = check_scouting_notes.invoke("NonExistentPlayer")
    print(f"Notes for NonExistentPlayer: {notes_fail}")

if __name__ == "__main__":
    test_tools()
