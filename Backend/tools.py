import os
import json
from langchain.tools import tool
from sportradar_client import SportradarClient
from dotenv import load_dotenv

class ApprovalRequiredException(Exception):
    def __init__(self, action_description):
        self.action_description = action_description
        self.message = json.dumps({
            "status": "approval_required",
            "message": f"Please approve the following action: {action_description}",
            "action": action_description
        })
        super().__init__(self.message)

load_dotenv()

GLOBAL_USER_MESSAGE = ""

def verify_approval(action_description: str):
    if not GLOBAL_USER_MESSAGE.strip().startswith("I approve. Proceed with:"):
        raise ApprovalRequiredException(action_description)

# Initialize Client
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY")
client = None
if SPORTRADAR_API_KEY:
    client = SportradarClient(SPORTRADAR_API_KEY)
else:
    print("WARNING: SPORTRADAR_API_KEY not found. Sportradar tools will fail.")

# Load Knowledge Base
KNOWLEDGE_FILE = os.path.join(os.path.dirname(__file__), "knowledge.json")
knowledge_base = {}
try:
    with open(KNOWLEDGE_FILE, "r") as f:
        knowledge_base = json.load(f)
except Exception as e:
    print(f"Error loading knowledge.json: {e}")

def harvest_player_ids(match_list):
    """
    Helper function to extract player IDs from match data and update knowledge.json.
    Input: List of match objects (internal standardized format).
    """
    try:
        updated = False
        players_kb = knowledge_base.get("players", {})
        
        for match in match_list:
            for p in match.get('players', []):
                p_name = p.get('name')
                p_id = p.get('id')
                
                if p_name and p_id and p_name not in players_kb:
                    # New player found!
                    players_kb[p_name] = {"id": p_id}
                    updated = True
                elif p_name and p_id and "id" not in players_kb[p_name]:
                    # Existing player, adding ID
                    players_kb[p_name]["id"] = p_id
                    updated = True
                    
        if updated:
            knowledge_base["players"] = players_kb
            with open(KNOWLEDGE_FILE, "w") as f:
                json.dump(knowledge_base, f, indent=4)
            print("Knowledge Base updated with new Player IDs.")
            
    except Exception as e:
        print(f"Error harvesting IDs: {e}")

@tool
def fetch_daily_results(query: str = ""):
    """
    Fetches the list of cricket matches completed today.
    Returns the results and automatically learns player IDs from these matches.
    Useful for checking past game scores and updating the player database.
    **CRITICAL**: DO NOT USE THIS TOOL DIRECTLY. You MUST call `request_user_approval` first and wait for the user's explicit permission.
    """
    verify_approval("fetch_daily_results")
    if not client:
        return json.dumps({"error": "Sportradar Client not initialized."})

    try:
        import datetime
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        daily_data = client.get_daily_schedule(today)
        
        if not daily_data:
             return json.dumps({"message": "No matches found for today."})

        matches = daily_data.get('sport_events', [])
        results = []
        
        # Limit to top 5 completed matches to avoid rate limits when fetching summaries
        completed_matches = [m for m in matches if m.get('status') == 'closed' or m.get('status') == 'ended']
        
        for match in completed_matches[:5]:
            match_id = match.get('id')
            try:
                # Fetch summary to get players
                summary = client.get_match_summary(match_id)
                if not summary: continue
                
                # Parse to standard format (reuse logic or keep simple)
                # We need to extract players to learn.
                # Simplification: We'll just extract players here directly for harvesting
                # and return a simple score string.
                
                # Extract Score & Players
                teams = summary.get('statistics', {}).get('teams', [])
                match_players = []
                
                for t in teams:
                    for p in t.get('players', []):
                        match_players.append({
                            "name": p.get('name'),
                            "id": p.get('id')
                        })
                
                # Harvest IDs immediately
                harvest_player_ids([{"players": match_players}])
                
                # Format Result for Output
                competitors = match.get('competitors', [])
                t1 = competitors[0].get('name', 'Team 1') if len(competitors) > 0 else 'T1'
                t2 = competitors[1].get('name', 'Team 2') if len(competitors) > 1 else 'T2'
                status = summary.get('sport_event_status', {})
                score = status.get('display_score') or status.get('status', 'Ended')
                
                results.append({
                    "id": match_id,
                    "match": f"{t1} vs {t2}",
                    "result": score
                })
                
            except Exception as e:
                print(f"Error processing match {match_id}: {e}")
                
        return json.dumps({"daily_results": results, "note": "Player IDs from these matches have been learned."}, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Error fetching daily results: {e}"})

@tool
def fetch_live_match_context(query: str = ""):
    """
    Fetches the current live cricket match context. 
    Returns the scorecard and active players for any live matches as a JSON string.
    Useful for finding out who is currently batting or bowling.
    **CRITICAL**: DO NOT USE THIS TOOL DIRECTLY. You MUST call `request_user_approval` first and wait for the user's explicit permission.
    """
    verify_approval("fetch_live_match_context")
    if not client:
        return json.dumps({"error": "Sportradar Client not initialized (Missing API Key)."})
    
    try:
        live_data = client.get_live_schedule()
        if not live_data:
            return json.dumps({"error": "No live data available or error fetching."})
        
        matches = live_data.get('sport_events', [])
        if not matches:
            return json.dumps({"message": "No live matches currently in progress."})
            
        # We will return a structured object with 'matches' list
        # Each match has id, team1, team2, status, score, players (if available)
        result_data = {"matches": []}

        for match in matches:
            # ... [Existing parsing logic] ...
            competitors = match.get('competitors', [])
            team1 = competitors[0].get('name', 'Unknown') if len(competitors) > 0 else 'Unknown'
            team2 = competitors[1].get('name', 'Unknown') if len(competitors) > 1 else 'Unknown'
            match_id = match.get('id')
            venue_info = match.get('venue', {})
            venue_name = venue_info.get('name', 'Unknown Venue')
            
            match_info = {
                "id": match_id,
                "team1": team1,
                "team2": team2,
                "venue": venue_name,
                "status": "Live",
                "score": "",
                "players": []
            }
            
            try:
                summary = client.get_match_summary(match_id)
                if summary:
                    # Extract Score
                    status = summary.get('sport_event_status', {})
                    match_info['status'] = status.get('status', 'Live')
                    
                    # Extract Detailed Match Stats
                    match_info['match_status'] = status.get('match_status') # e.g. second_innings_away_team
                    match_info['display_overs'] = status.get('display_overs') # e.g. 14.1
                    match_info['run_rate'] = status.get('run_rate')
                    match_info['required_run_rate'] = status.get('required_run_rate')
                    
                    scores = []
                    match_info['innings_scores'] = []
                    if 'period_scores' in status:
                        for p in status['period_scores']:
                            scores.append(f"{p.get('type')}: {p.get('display_score')}")
                            # Save structured innings data for calculation
                            match_info['innings_scores'].append({
                                "inning": p.get('number'),
                                "score": p.get('display_score'),
                                "runs": p.get('home_score') if p.get('home_score') > 0 else p.get('away_score'),
                                "wickets": p.get('home_wickets') if p.get('home_score') > 0 else p.get('away_wickets')
                            })
                    match_info['score'] = ", ".join(scores)
                    
                    # Extract Lineups / Players
                    stats = summary.get('statistics', {})
                    teams_stats = stats.get('teams', [])
                    
                    for team in teams_stats:
                        t_name = team.get('name', 'Unknown Team')
                        players = team.get('players', [])
                        for p in players:
                            # Standardize player object for frontend
                            # Frontend expects: id, name, role, team, runs, balls, strikeRate, wickets, economy
                            
                            # Parse batting if available (very dependent on API structure)
                            # Sportradar structure is complex. We'll try to get basic stats if present.
                            # Usually 'statistics' inside player object.
                            p_stats = p.get('statistics', {})
                            batting = p_stats.get('batting', {})
                            bowling = p_stats.get('bowling', {})
                            
                            player_obj = {
                                "id": p.get('id'),
                                "name": p.get('name'),
                                "team": t_name,
                                "role": p.get('type', 'Player'), # e.g. batsman, bowler
                                "runs": batting.get('runs'),
                                "balls": batting.get('balls'),
                                "strikeRate": batting.get('strike_rate'),
                                "wickets": bowling.get('wickets'),
                                "economy": bowling.get('economy')
                            }
                            match_info['players'].append(player_obj)
                            
            except Exception as e:
                match_info['error'] = f"Could not fetch summary: {str(e)}"
            
            result_data['matches'].append(match_info)
        
        # Harvest IDs from Live Data
        harvest_player_ids(result_data['matches'])

        return json.dumps(result_data, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Error fetching live match context: {str(e)}"})

@tool
def fetch_player_profile(player_id: str):
    """
    Fetches detailed profile and statistics for a specific player using their Sportradar Player ID (URN).
    Input should be the player ID (e.g., "sr:player:123456") obtained from `fetch_live_match_context`.
    **CRITICAL**: DO NOT USE THIS TOOL DIRECTLY. You MUST call `request_user_approval` first and wait for the user's explicit permission.
    """
    verify_approval("fetch_player_profile")
    if not client:
        return "Error: Client not initialized."
    
    try:
        profile = client.get_player_profile(player_id)
        if not profile:
             return "No profile found."
        return json.dumps(profile)
    except Exception as e:
        return f"Error fetching player profile: {e}"

@tool
def check_scouting_notes(name: str):
    """
    Checks the local scouting knowledge base for reports on a specific player, team, or venue.
    Input should be the EXACT player name (e.g., "V. Kohli") or team name (e.g., "India", "Zimbabwe").
    Returns the scouting report if found in knowledge.json.
    **CRITICAL**: DO NOT USE THIS TOOL DIRECTLY. You MUST call `request_user_approval` first and wait for the user's explicit permission.
    """
    verify_approval("check_scouting_notes")
    # Simple fuzzy search or direct key match
    # knowledge.json structure: {"players": {...}, "teams": {...}}
    players = knowledge_base.get("players", {})
    teams = knowledge_base.get("teams", {})
    
    name_lower = name.lower()
    
    reports = []
    
    # Check Teams
    if name in teams:
        reports.append(f"Team Report ({name}): {json.dumps(teams[name])}")
    else:
        for t_name, report in teams.items():
            if name_lower in t_name.lower() or t_name.lower() in name_lower:
                reports.append(f"Team Report ({t_name}): {json.dumps(report)}")

    # Check Players (match name or if the query is in their report, e.g. "India")
    for p_name, report in players.items():
        if name_lower in p_name.lower() or p_name.lower() in name_lower:
             reports.append(f"Player Report ({p_name}): {json.dumps(report)}")
        elif "scouting_report" in report and name_lower in report["scouting_report"].lower():
             reports.append(f"Player Report ({p_name}): {json.dumps(report)}")

    # Check Venues
    venues = knowledge_base.get("venues", {})
    if name in venues:
        reports.append(f"Venue Report ({name}): {json.dumps(venues[name])}")
    else:
        for v_name, report in venues.items():
            if name_lower in v_name.lower() or v_name.lower() in name_lower:
                reports.append(f"Venue Report ({v_name}): {json.dumps(report)}")
            
    if reports:
        return "\n".join(reports)
    return f"No scouting report found for '{name}'."

@tool
def calculate_win_probability(runs_needed: int, balls_remaining: int, wickets_in_hand: int, target_score: int, chasing_team: str, defending_team: str, format: str = "T20"):
    """
    Calculates the win probability for the chasing team and provides tactical context.
    
    Args:
        runs_needed (int): Runs required to win.
        balls_remaining (int): Balls left in the innings.
        wickets_in_hand (int): Number of wickets remaining (10 - wickets_lost).
        target_score (int): The total score the chasing team is chasing.
        chasing_team (str): Name of the team batting second (e.g., "India").
        defending_team (str): Name of the team bowling second (e.g., "Zimbabwe").
        format (str): Match format ('T20' or 'ODI'). Default is 'T20'.
        
    Returns:
        str: A formatted string with Win Probability %, Required Run Rate, and analysis combined with team knowledge.
    
    **CRITICAL**: DO NOT USE THIS TOOL DIRECTLY. You MUST call `request_user_approval` first and wait for the user's explicit permission.
    """
    verify_approval("calculate_win_probability")
    try:
        if balls_remaining <= 0:
            if runs_needed <= 0:
                return "Match Over: Chasing team wins!"
            return "Match Over: Defending team wins!"

        rrr = (runs_needed / balls_remaining) * 6
        
        # Basic heuristic model for T20
        win_prob = 50.0
        
        # Adjust for RRR
        diff_rrr = 8.0 - rrr
        win_prob += (diff_rrr * 5)
        
        # Adjust for Wickets
        if wickets_in_hand < 4:
            win_prob -= 20
        elif wickets_in_hand > 7:
            win_prob += 10
            
        # Cap probability
        if win_prob > 99: win_prob = 99
        if win_prob < 1: win_prob = 1
        
        analysis = ""
        if rrr > 12:
            analysis = "Required Run Rate is extremely high. Only a miracle or bad bowling can save this."
        elif rrr > 10:
            analysis = "Tough ask. Needs boundaries every over."
        elif rrr < 6:
            analysis = "Cruising. Just need to rotate strike."
        else:
            analysis = "Balanced game. Wickets will differentiate the winner."

        # Fetch Context from Knowledge Base
        teams_kb = knowledge_base.get("teams", {})
        chasing_info = teams_kb.get(chasing_team, {})
        defending_info = teams_kb.get(defending_team, {})

        context_analysis = "\n\n**Qualitative Context:**"
        
        if chasing_info.get("strengths"):
            context_analysis += f"\n- {chasing_team} Strengths: " + ", ".join(chasing_info["strengths"])
        if chasing_info.get("weaknesses"):
            context_analysis += f"\n- {chasing_team} Weaknesses: " + ", ".join(chasing_info["weaknesses"])
            
        if defending_info.get("strengths"):
            context_analysis += f"\n- {defending_team} Strengths: " + ", ".join(defending_info["strengths"])
        if defending_info.get("weaknesses"):
            context_analysis += f"\n- {defending_team} Weaknesses: " + ", ".join(defending_info["weaknesses"])
            
        if not chasing_info and not defending_info:
            context_analysis = "\n\n*(No tactical scouting reports found in local knowledge base for these teams to enhance this prediction.)*"
            
        return f"**Mathematical Win Probability**: {win_prob:.1f}%\n**Required Run Rate**: {rrr:.2f}\n**Situation**: {analysis}{context_analysis}"
        
    except Exception as e:
        return f"Error calculating probability: {e}"

@tool
def request_user_approval(action_description: str):
    """
    Halts execution to ask the user for permission to proceed with a sensitive action (like calculating win probability).
    Args:
        action_description (str): A clear description of what you want to do (e.g., "Calculate win probability for India vs Zimbabwe").
    Returns:
        str: A JSON string indicating approval is required. The UI will pause and wait for user input.
    """
    # Simply returning a string does not stop the Langchain Agent Executor.
    # We MUST raise an exception to physically break the while loop of the agent.
    raise ApprovalRequiredException(action_description)

@tool
def fetch_player_career_stats(player_id: str):
    """
    Fetches and summarizes a player's career statistics (Batting/Bowling).
    Use this to validate a player's quality or form.
    Input: Player ID (e.g., "sr:player:123456") OR Player Name (e.g. "Virat Kohli").
    **CRITICAL**: DO NOT USE THIS TOOL DIRECTLY. You MUST call `request_user_approval` first and wait for the user's explicit permission.
    """
    verify_approval("fetch_player_career_stats")
    if not client:
        return "Error: Client not initialized."
    
    # Name Lookup Logic
    if not player_id.startswith("sr:player:"):
        print(f"Searching for player ID for name: {player_id}")
        
        found_id = None
        search_name = player_id.lower()
        
        # 1. First check if we have a direct ID mapping in knowledge.json (for speed)
        players_kb = knowledge_base.get("players", {})
        if player_id in players_kb and "id" in players_kb[player_id]:
             found_id = players_kb[player_id]["id"]
             print(f"Found direct match in KB: {found_id}")

        # 2. If not, search through KNOWN TEAMS via API
        if not found_id:
            teams = knowledge_base.get("teams", {})
            for team_name, team_data in teams.items():
                team_id = team_data.get("id")
                if not team_id: continue
                
                print(f"Checking roster of {team_name} ({team_id})...")
                try:
                    # Fetch Team Profile from API
                    team_profile = client.get_team_profile(team_id)
                    if not team_profile: continue
                    
                    # Check players in roster
                    roster = team_profile.get('players', [])
                    for p in roster:
                        p_name = p.get('name', '').lower()
                        # Simple fuzzy match: "Virat Kohli" in "Virat Kohli" or "Kohli" in "Virat Kohli"
                        if search_name == p_name or search_name in p_name or p_name in search_name:
                             found_id = p.get('id')
                             print(f"Found API match in {team_name}: {p.get('name')} -> {found_id}")
                             break
                    
                    if found_id: break
                except Exception as e:
                    print(f"Error checking team {team_name}: {e}")
        
        if found_id:
            player_id = found_id
        else:
            return f"Error: Could not find a Player ID for '{player_id}'. I checked the rosters of known teams ({', '.join(knowledge_base.get('teams', {}).keys())}) but found no match. Please provide the exact Sportradar Player ID (URN) or try a more specific name."

    try:
        profile = client.get_player_profile(player_id)
        if not profile:
             return "No profile found."
        
        # Parse Profile
        player_name = profile.get('player', {}).get('name', 'Unknown')
        role = profile.get('player', {}).get('type', 'Unknown')
        
        # Sportradar structure varies, but usually `statistics` contains `seasons` or `career`
        # For this exercise, we'll try to find a 'career' or 'total' object, 
        # or iterate through roles.
        # Since we don't have the exact schema trace, we will provide a safe summary.
        
        output = [f"Player: {player_name} ({role})"]
        
        # Check for Career Stats (Generic Parsing)
        # Note: In real Sportradar API, stats are often in a separate 'statistics' endpoint or 
        # nested deep in profile. We will check 'statistics' key.
        stats = profile.get('statistics', {})
        if not stats:
            # Fallback for some endpoints
            output.append("Detailed career stats not found in profile response.")
            output.append("Raw Data Keys: " + ", ".join(profile.keys()))
        else:
            # Try to find batting/bowling summaries
            # This is best-effort parsing without live data reference
            if 'total' in stats:
                total = stats['total']
                if 'batting' in total:
                    bat = total['batting']
                    runs = bat.get('runs', 0)
                    matches = bat.get('matches', 0)
                    avg = bat.get('average', 'N/A')
                    sr = bat.get('strike_rate', 'N/A')
                    output.append(f"Career Batting: {matches} Matches, {runs} Runs, Avg: {avg}, SR: {sr}")
                
                if 'bowling' in total:
                    bowl = total['bowling']
                    wickets = bowl.get('wickets', 0)
                    matches = bowl.get('matches', 0)
                    econ = bowl.get('economy', 'N/A')
                    avg = bowl.get('average', 'N/A')
                    output.append(f"Career Bowling: {matches} Matches, {wickets} Wickets, Econ: {econ}, Avg: {avg}")
            else:
                output.append("No 'total' stats found. Raw stats keys: " + ", ".join(stats.keys()))

        return "\n".join(output)

    except Exception as e:
        return f"Error fetching career stats: {e}"

@tool
def analyze_match_matchup(match_id: str = None, team_names: list = None):
    """
    Fetches detailed team profiles and rosters for a specific match to enable deep analysis 
    of strengths, weaknesses, and win predictions.
    
    Args:
        match_id (str): The Sportradar Match ID (e.g. "sr:match:123456"). Preferred.
        team_names (list): List of two team names if ID is unknown (e.g. ["India", "Australia"]).
        
    Returns:
        str: JSON string containing full rosters and details for both teams.
        
    **CRITICAL**: DO NOT USE THIS TOOL DIRECTLY. You MUST call `request_user_approval` first and wait for the user's explicit permission.
    """
    verify_approval("analyze_match_matchup")
    if not client:
        return "Error: Client not initialized."
    
    try:
        team_ids = []
        team_names_found = []
        
        # 1. Resolve Team IDs from Match ID
        if match_id:
            try:
                summary = client.get_match_summary(match_id)
                if summary:
                    competitors = summary.get('sport_event', {}).get('competitors', []) \
                                  or summary.get('competitors', []) # fallback
                    for c in competitors:
                        team_ids.append(c.get('id'))
                        team_names_found.append(c.get('name'))
            except Exception as e:
                return f"Error fetching match summary for {match_id}: {e}"
        
        # 2. Fallback: Search by Name (if match_id failed or not provided)
        # Note: This is less reliable without a team search API, relies on Knowledge Base
        if not team_ids and team_names and len(team_names) >= 2:
            teams_kb = knowledge_base.get("teams", {})
            for name in team_names:
                # Check KB
                found = False
                for t_name, t_data in teams_kb.items():
                    if name.lower() in t_name.lower():
                         team_ids.append(t_data.get('id'))
                         team_names_found.append(t_name)
                         found = True
                         break
                
                if not found:
                     return f"Could not find Team ID for '{name}' in knowledge base. Please try providing the Match ID from 'fetch_live_match_context'."

        if len(team_ids) < 2:
            return "Error: Could not identify both teams. Please provide a valid 'match_id'."
            
        # 3. Fetch Full Profiles for Both Teams
        matchup_data = {"teams": [], "message": ""}
        
        has_rosters = False
        
        for tid in team_ids:
            t_profile = client.get_team_profile(tid)
            if t_profile:
                t_data = {
                    "name": t_profile.get('team', {}).get('name'),
                    "id": tid,
                    "roster": []
                }
                
                # Extract Roster
                players = t_profile.get('players', [])
                for p in players:
                    t_data["roster"].append({
                        "name": p.get('name'),
                        "id": p.get('id'),
                        "role": p.get('type', 'Player'),
                        "batting": p.get('statistics', {}).get('batting', {}), # opportunistic fetch
                        "bowling": p.get('statistics', {}).get('bowling', {})
                    })
                
                if t_data["roster"]:
                     has_rosters = True

                matchup_data["teams"].append(t_data)
        
        if not has_rosters:
             matchup_data["message"] = "WARNING: Live roster data is unavailable from Sportradar API. Please immediately use the `check_scouting_notes` tool to check your local Knowledge Base for these teams (" + ", ".join([t['name'] for t in matchup_data["teams"]]) + ") to provide an analysis."
                
        return json.dumps(matchup_data, indent=2)

    except Exception as e:
        return f"Error analyzing matchup: {e}"
