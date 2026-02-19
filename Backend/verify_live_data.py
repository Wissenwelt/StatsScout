from tools import fetch_live_match_context
import json

output = []
output.append("Fetching live match context...")
result = fetch_live_match_context.invoke({})
data = json.loads(result)

if "matches" in data:
    for m in data["matches"]:
        output.append(f"\nMatch: {m.get('team1')} vs {m.get('team2')}")
        output.append(f"Status: {m.get('status')}")
        output.append(f"Overs: {m.get('display_overs')}")
        output.append(f"CRR: {m.get('run_rate')}")
        output.append(f"RRR: {m.get('required_run_rate')}")
        output.append(f"Innings Scores: {m.get('innings_scores')}")
else:
    output.append(result)

with open("verification_result.txt", "w") as f:
    f.write("\n".join(output))
