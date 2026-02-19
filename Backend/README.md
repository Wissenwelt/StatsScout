# Backend - StatsScout

This is the Python-based API server that powers StatsScout. It uses **FastAPI** to serve endpoints and **LangChain** to orchestrate the "Smart Scout" agent.

## Folder Structure

-   `main.py`: Entry point. Initializes the FastAPI app, WebSocket/Streaming logic, and the LangChain Agent Executor.
-   `tools.py`: Contains the custom tools used by the agent:
    -   `fetch_live_match_context`: Retrieves live match data.
    -   `calculate_win_probability`: Quantitative logic based on RRR/wickets.
    -   `check_scouting_notes`: Retrieval from `knowledge.json`.
    -   `analyze_match_matchup`: Deep analysis + Fallback logic.
    -   `fetch_player_career_stats`: Validation tool.
-   `sportradar_client.py`: Wrapper for Sportradar API interactions.
-   `knowledge.json`: The **Knowledge Base** containing specific player/team reports.
-   `debug_*.py`: Temporary scripts used for verification and debugging during development.

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables:**
    Copy `.env.example` to `.env` and add your API Keys (Gemini, Sportradar).

3.  **Run Server:**
    ```bash
    python main.py
    ```
    The server runs on `http://localhost:8000`.
    **IMPORTANT:** The Frontend expects the backend to be running on this exact port (8000).

## API Endpoints

-   `POST /chat`: Accepting a JSON payload `{"message": "user question"}` and streaming the agent's response (including thoughts/tool calls) via SSE.
-   `GET /api/match-list`: Returns a JSON list of matches for the dashboard.
