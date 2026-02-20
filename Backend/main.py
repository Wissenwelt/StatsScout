import sys
import io

# Fix Windows charmap error when printing emojis
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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
    request_user_approval,
    client
)
from callbacks import AgentCallbackHandler

load_dotenv()

class ApprovalRequiredException(Exception):
    def __init__(self, action_description):
        self.action_description = action_description
        self.message = json.dumps({
            "status": "approval_required",
            "message": f"Please approve the following action: {action_description}",
            "action": action_description
        })
        super().__init__(self.message)


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
    analyze_match_matchup,
    request_user_approval
]

# Agent Setup
SYSTEM_PROMPT = """
**ORCHESTRATOR ROUTING LOGIC:**
You are the Master Orchestrator. When the user asks a question, you must intelligently determine *which specific tool* is needed to answer it, rather than blindly fetching live scores every time.
Follow this routing guide:
- **"Who is playing?" / "What's the score?"**: Route to `fetch_live_match_context`.
- **"Compare X and Y" / "Who will win?"**: Route to `analyze_match_matchup` or `calculate_win_probability`.
- **"What are [Player]'s stats?"**: Route to `fetch_player_career_stats`.
- **"What are the weaknesses of [Team/Player]?"**: Route to `check_scouting_notes`.

**STRICT EXECUTION WORKFLOW:**
1. **Analyze:** Read the user's prompt and use the Orchestrator Routing Logic to decide on the single best tool to use.
2. **Request Approval (Mandatory):** BEFORE executing that tool, you MUST call `request_user_approval`. For the `action_description` argument, state the exact tool you want to use and why. 
    - Example: `{"action": "request_user_approval", "action_input": "Use check_scouting_notes to compare the strengths of India and Sri Lanka."}`
3. **Wait:** DO NOT output any other tool calls at this stage. Stop and wait for the user to reply.
4. **Vague Answers:** If the user replies vaguely, ask: "I did not understand. Do I have your permission to proceed with the tool call? Please say Yes or No."
5. **Execute:** ONLY proceed to call your chosen tool if the user's message explicitly starts with "I approve. Proceed with:".

**UI COMMANDS:**
- If discussing a specific player after approval, output `[HIGHLIGHT: Player Name]` to focus the UI.

You have access to the following tools:
- fetch_live_match_context: Get current match scorecard and players. REQUIRES APPROVAL.
- check_scouting_notes: Search for scouting reports on specific players/venues. REQUIRES APPROVAL.
- fetch_player_career_stats: Get historical career stats (Runs, Wickets, Avg). REQUIRES APPROVAL.
- calculate_win_probability: Calculate win %. REQUIRES APPROVAL.
- analyze_match_matchup: Fetch full team rosters. REQUIRES APPROVAL.
- request_user_approval: THE ONLY TOOL YOU CAN CALL FREELY. YOU MUST CALL THIS FIRST TO GET PERMISSION TO CALL ANY OF THE OTHER TOOLS.

Always explain your reasoning step-by-step.
"""

agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
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
    import tools
    tools.GLOBAL_USER_MESSAGE = message
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
                        exc = task.exception()
                        # Check if it's our custom approval exception
                        if "approval_required" in str(exc):
                            try:
                                # Extract just the JSON portion if it's wrapped in an Exception string
                                err_str = str(exc)
                                # The exception message is exactly the JSON string due to our custom Exception
                                msg_data = json.loads(err_str)
                                yield f"data: {json.dumps({'type': 'observation', 'content': err_str, '_requiresApproval': True, '_approvalAction': msg_data.get('action')})}\n\n"
                            except json.JSONDecodeError:
                                yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"
                        else:
                            error_msg = json.dumps({"type": "error", "content": str(exc)})
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

@app.get("/api/match/{match_id}/refresh")
async def refresh_match(match_id: str):
    """
    Fetches the latest summary for a specific match.
    Used for manual live score refreshing.
    """
    if not client:
        raise HTTPException(status_code=500, detail="Sportradar Client not initialized")
    
    try:
        summary = client.get_match_summary(match_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Match not found or data unavailable")
        
        status_obj = summary.get('sport_event_status', {})
        display_status = status_obj.get('status', 'Live')
        score = ""
        
        if 'period_scores' in status_obj:
            scores = []
            for p in status_obj['period_scores']:
                scores.append(f"{p.get('type')}: {p.get('display_score')}")
            score = ", ".join(scores)
            
        return {
            "id": match_id,
            "status": display_status,
            "score": score
        }
            
    except Exception as e:
        print(f"Error refreshing match {match_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    print(f"--- Streaming Request: {request.message[:50]}... ---")
    return StreamingResponse(generate_response(request.message), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
