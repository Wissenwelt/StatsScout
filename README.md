# 🏏 StatsScout - VIBE Code Submission

**StatsScout** is an agentic cricket analytics dashboard where "Smart Scout" (an AI agent) helps users analyze live matches, predict outcomes, and scout players using real-time data and historical knowledge.

## 🚀 The Goal
Build a "thin-slice" agentic web app that demonstrates:
1.  **Real-world API Integration:** Fetching live sports data (Sportradar).
2.  **Agentic Workflow:** Planning, tool use, and fallback logic for robust analysis.
3.  **Knowledge Integration:** Combining live data with a curated "Scouting Notebook" (JSON knowledge base).
4.  **Client-Side "Magic":** The agent controls the UI (e.g., populating the Match Center) based on its findings.

## 🛠️ Tech Stack
-   **Backend:** Python (FastAPI), LangChain (Agent Logic).
-   **Frontend:** React (Vite), TailwindCSS, Lucide Icons.
-   **Data:** Sportradar API (Live Cricket Data), `knowledge.json` (Internal Knowledge Base).

## ✨ Key Features (Requirements Mapping)

### 1. Agent Behaviour
-   **Goal:** "Who will win Sri Lanka vs Zimbabwe?"
-   **Plan:** The agent checks live scores -> identifies players -> consults internal knowledge -> calculates win probability -> delivers verdict.
-   **Trace:** The UI displays a "Thinking..." accordion showing every tool call and thought process.

### 2. Server-Side Actions (Tools)
The agent has access to 5+ robust tools:
-   `fetch_live_match_context`: **(Data Fetching)** Hits Sportradar API for live scores/players.
-   `calculate_win_probability`: **(Logic)** Uses a custom algorithm (RRR, Wickets, Overs) to predict winners.
-   `check_scouting_notes`: **(Retrieval)** Searches `knowledge.json` for qualitative player insights.
-   `analyze_match_matchup`: **(Complex Workflow)** Fetches full team rosters and provides a fallback if data is missing.
-   `fetch_player_career_stats`: **(Validation)** Looks up historical stats to validate claims.

### 3. Client-Side Actions
-   **Match Center Auto-Update:** When the agent runs `fetch_live_match_context`, the frontend **automatically detects the data** and populates the "Match Center" panel with the live scorecard and active player table. This is a direct Agent-to-UI side effect.
-   **Dynamic Titles:** Chat session titles automatically rename to match the topic of your first message.
-   **Agent-Triggered Highlight:** The agent can command the UI to **highlight a specific player** (e.g., `[HIGHLIGHT: Player Name]`) when discussing them, focusing the user's attention on the relevant stats in the live table.

### 4. Knowledge Mechanism
-   **`knowledge.json`:** A curated file containing scouting reports (e.g., "Kohli struggles against left-arm pace").
-   **Fallback Logic:** If the live API fails (e.g., empty rosters), the agent is explicitly instructed to **fallback to internal knowledge** to provide a qualitative answer, ensuring resilience.

### 5. Control & Safety
-   **Read-Only:** All actions are non-destructive (fetching/analyzing).
-   **Fallback Warnings:** The `analyze_match_matchup` tool returns explicit warnings ("WARNING: Live roster data unavailable") which the agent must acknowledge, preventing hallucinations.

## 🏃‍♂️ How to Run

### Prerequisites
-   Node.js & npm
-   Python 3.10+
-   Sportradar API Key (Cricket)

### 1. Setup Backend
```bash
cd Backend
# create .env file with SPORTRADAR_API_KEY=your_key_here
pip install -r requirements.txt
python main.py
# Server runs on http://localhost:8000
# NOTE: The Frontend expects the backend on port 8000.
```

### 2. Setup Frontend
```bash
cd Frontend
npm install
npm run dev
```

### 3. Usage
1.  Open `http://localhost:5173`.
2.  Ask: *"Who is playing right now?"* -> **Watch the Right Panel update!**
3.  Ask: *"Who will win detailed analysis?"* -> **See the Agent plan and use Knowledge.**

## 🌐 Web Proof
-   **Network:** Observe `/chat` requests returning streaming JSON.
-   **Console:** Logs show "Auto-updating Live Context" when the agent pushes new match data.
