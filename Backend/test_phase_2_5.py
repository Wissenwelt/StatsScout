from tools import calculate_win_probability, check_scouting_notes

def test_win_probability():
    print("--- Testing Win Predictor ---")
    # Case 1: Easy Win
    print(calculate_win_probability.invoke({"runs_needed": 20, "balls_remaining": 30, "wickets_in_hand": 8, "target_score": 150}))
    # Case 2: Hard Win
    print(calculate_win_probability.invoke({"runs_needed": 60, "balls_remaining": 24, "wickets_in_hand": 4, "target_score": 180}))
    # Case 3: Impossible
    print(calculate_win_probability.invoke({"runs_needed": 36, "balls_remaining": 6, "wickets_in_hand": 2, "target_score": 200}))

def test_venue_search():
    print("\n--- Testing Venue Search ---")
    print(check_scouting_notes.invoke({"name": "Wankhede Stadium"}))
    print(check_scouting_notes.invoke({"name": "Eden Gardens"}))
    print(check_scouting_notes.invoke({"name": "Unknown Stadium"}))

if __name__ == "__main__":
    test_win_probability()
    test_venue_search()
