import os
import uvicorn
import asyncio
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentType, initialize_agent
from tools import (
    fetch_live_match_context, 
    check_scouting_notes,
    fetch_player_profile,
    calculate_win_probability,
    fetch_player_career_stats,
    analyze_match_matchup,
    client
)
from callbacks import AgentCallbackHandler

load_dotenv()

# --- Configuration ---
# Simple Chatbot Configuration
# Strictly using model from .env
MODEL_NAME = os.getenv("GEMINI_MODEL")
if not MODEL_NAME:
    print("CRITICAL: GEMINI_MODEL not found in .env")
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("CRITICAL: GEMINI_API_KEY not found in .env")

# Initialize the LLM directly
# Streaming required for token-level updates, but we engage mainly with tool events
llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    google_api_key=API_KEY,
    temperature=0.7,
    streaming=True,
    convert_system_message_to_human=True
)

# Tools
tools = [
    fetch_live_match_context, 
    check_scouting_notes,
    fetch_player_profile,
    calculate_win_probability,
    fetch_player_career_stats,
    analyze_match_matchup
]

# Agent Setup
SYSTEM_PROMPT = """
You are "Smart Scout", an advanced cricket analytics assistant.
Your goal is to provide tactical insights by combining live match data with historical scouting reports.

Follow this thought process STRICTLY for every request:
1. Check the live match context first to see who is playing.
2. Identify the active batsman or key players involved.
   - **UI ACTION:** If discussing a specific player, output `[HIGHLIGHT: Player Name]` at the start of your sentence to focus the UI on them.
3. Cross-reference their names with your Scouting Notes (knowledge base).
4. **Deep Match Analysis (Qualitative):** If the user asks for a prediction, "strength/weakness", or "who will win?", AND live data is sparse (e.g. no balls/runs info), use `analyze_match_matchup`.
   - This tool gets you full team rosters. Use these rosters to judge Team Strength to make a prediction.
   - **CRITICAL FALLBACK:** If the tool returns "WARNING: Live roster data is unavailable", you **MUST** use your own INTERNAL KNOWLEDGE about these teams/players (e.g. "Sri Lanka is known for spin", "Zimbabwe has Sikandar Raza") to provide the analysis. Do not refuse to answer.
5. **Historical Validation:** If you need to assess a player's quality (e.g., "Is he a good T20 bowler?"), use `fetch_player_career_stats`.
6. **Win Probability (Quantitative):** If and ONLY IF you have precise live data (runs needed, balls remaining, wickets), use `calculate_win_probability`.
   - If this tool fails or data is missing, FALLBACK to the qualitative analysis from Step 4.
7. Suggest a tactical move or highlight a weakness based on the data.

You have access to the following tools:
- fetch_live_match_context: Get current match scorecard and players.
- check_scouting_notes: Search for scouting reports on specific players/venues.
- fetch_player_career_stats: Get historical career stats (Runs, Wickets, Avg).
- calculate_win_probability: Calculate win % based on math.
- analyze_match_matchup: Fetch full team rosters/profiles for a match. Use this for predictions when live data is insufficient.

Always explain your reasoning step-by-step.
"""

agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={
        "system_message": SystemMessage(content=SYSTEM_PROMPT)
    }
)

app = FastAPI(title="StatsScout Agent Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: list = []

async def generate_response(message: str):
    queue = asyncio.Queue()
    handler = AgentCallbackHandler(queue)
    
    # Send initial event (Optional, removing to reduce noise)
    # await queue.put(json.dumps({"type": "thought", "content": "Agent started..."}))

    # Run the agent in a background task
    task = asyncio.create_task(
        agent_executor.ainvoke(
            {"input": message},
            config={"callbacks": [handler]}
        )
    )

    try:
        # Loop until task is done or valid break
        while True:
            # Wait for next item from queue
            # We use a timeout to check if task is done if queue is empty
            try:
                # Wait for a brief moment for new events
                event = await asyncio.wait_for(queue.get(), timeout=0.1)
                yield f"data: {event}\n\n"
            except asyncio.TimeoutError:
                # If queue is empty, check if task is finished
                if task.done():
                    # Check for exceptions
                    if task.exception():
                        error_msg = json.dumps({"type": "error", "content": str(task.exception())})
                        yield f"data: {error_msg}\n\n"
                    else:
                        # Get result
                        result = task.result()
                        final_output = result.get("output", "No output generated.")
                        final_msg = json.dumps({"type": "answer", "content": final_output})
                        yield f"data: {final_msg}\n\n"
                    break
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

from datetime import datetime, timedelta

@app.get("/api/match-list")
async def get_match_list():
    """
    Fetches live and daily match limits.
    Returns JSON with 'live', 'upcoming', 'recent'.
    """
    if not client:
        raise HTTPException(status_code=500, detail="Sportradar Client not initialized")
    
    try:
        # 1. Fetch Live Matches
        live_data = client.get_live_schedule()
        live_matches = []
        if live_data and 'sport_events' in live_data:
            for match in live_data['sport_events']:
                match_id = match.get('id')
                # Try to get more detail (score)
                summary = client.get_match_summary(match_id)
                display_status = "Live"
                score = ""
                
                if summary:
                    status = summary.get('sport_event_status', {})
                    display_status = status.get('status', 'Live')
                    if 'period_scores' in status:
                        scores = []
                        for p in status['period_scores']:
                            scores.append(f"{p.get('type')}: {p.get('display_score')}")
                        score = ", ".join(scores)

                competitors = match.get('competitors', [])
                team1 = competitors[0].get('name', 'Unknown') if len(competitors) > 0 else 'Unknown'
                team2 = competitors[1].get('name', 'Unknown') if len(competitors) > 1 else 'Unknown'

                live_matches.append({
                    "id": match_id,
                    "team1": team1,
                    "team2": team2,
                    "status": display_status,
                    "score": score,
                    "type": "live"
                })

        # 2. Fetch Daily Schedule for "Upcoming" and "Recent"
        # Since matches often span midnight or users check "tonight's game" after midnight,
        # we fetch BOTH today and yesterday.
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Parallel fetch if we were async, but sequential is fine for now
        schedule_today = client.get_daily_schedule(today)
        schedule_yesterday = client.get_daily_schedule(yesterday)
        
        all_events = []
        if schedule_today:
            all_events.extend(schedule_today.get('sport_events', []))
        if schedule_yesterday:
            all_events.extend(schedule_yesterday.get('sport_events', []))
            
        upcoming_matches = []
        recent_matches = []
        
        # Deduplicate by ID just in case
        seen_ids = set()
        
        # Sort all events by time (descending for processing simplification? No, just sort result lists)
        
        for match in all_events:
            match_id = match.get('id')
            if match_id in seen_ids: continue
            seen_ids.add(match_id)
            
            # Filter out active live matches
            if any(m['id'] == match_id for m in live_matches):
                continue
                
            status = match.get('sport_event_status', {}).get('status', '')
            competitors = match.get('competitors', [])
            if len(competitors) < 2: continue
            
            team1 = competitors[0].get('name', 'Unknown')
            team2 = competitors[1].get('name', 'Unknown')
            start_time = match.get('scheduled', '') # ISO string

            # Determine Status if missing
            if not status or status == 'Unknown':
                try:
                    # Parse start_time (e.g. 2026-02-19T21:30:00+00:00)
                    # Handle Z if present
                    st = start_time.replace('Z', '+00:00')
                    dt = datetime.fromisoformat(st)
                    if dt.timestamp() < now.timestamp():
                        status = 'ended' # Assume ended if in past
                    else:
                        status = 'not_started'
                except Exception:
                    status = 'scheduled' # Fallback

            item = {
                "id": match_id,
                "team1": team1,
                "team2": team2,
                "status": status,
                "startTime": start_time,
                "type": "scheduled",
                "score": "",
                "result": ""
            }

            if status == "closed" or status == "ended" or status == "postponed":
                item['type'] = 'recent'
                recent_matches.append(item)
            elif status == "not_started" or status == "scheduled":
                item['type'] = 'upcoming'
                upcoming_matches.append(item)

        # Sort Lists
        recent_matches.sort(key=lambda x: x['startTime'] or "", reverse=True)
        upcoming_matches.sort(key=lambda x: x['startTime'] or "")
        
        # Fetch Scores for Top 10 Recent
        for i, item in enumerate(recent_matches[:10]):
            try:
                summary = client.get_match_summary(item['id'])
                if summary:
                    status_obj = summary.get('sport_event_status', {})
                    item['status'] = status_obj.get('status', item['status'])
                    
                    # 1. Get Detailed Score from Periods (Innings)
                    period_scores = status_obj.get('period_scores', [])
                    innings_scores = []
                    for p in period_scores:
                        # Only take innings, ignore super overs for now unless they are crucial
                        if p.get('display_score'):
                             innings_scores.append(p.get('display_score'))
                    
                    if innings_scores:
                        item['score'] = " vs ".join(innings_scores)
                    else:
                        item['score'] = status_obj.get('display_score') or ""
                    
                    # 2. Get Result Text
                    result_text = status_obj.get('match_result') or status_obj.get('match_status')
                    if result_text and str(result_text).lower() not in ['ended', 'closed', 'finished', 'not_started']:
                         item['result'] = str(result_text)
                    else:
                         # Try fallback to just "Ended" if we have scores but no result text
                         if item['score']:
                              item['result'] = "Match Ended"
                         else:
                              item['result'] = ""
            except Exception:
                pass
        
        return {
            "live": live_matches,
            "upcoming": upcoming_matches,
            "recent": recent_matches 
        }

    except Exception as e:
        print(f"Error in match-list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    print(f"--- Streaming Request: {request.message[:50]}... ---")
    return StreamingResponse(generate_response(request.message), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
