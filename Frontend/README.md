# Frontend - StatsScout Dashboard

This is the React-based client for StatsScout. It provides the conversational UI and the data-driven match center.

## Key Components

-   **`Dashboard.tsx`**: The main layout. It orchestrates the chat session and the live data panels.
    -   **Client-Side "Magic"**: When the backend agent sends a `fetch_live_match_context` tool call result, the Dashboard *intercepts* this JSON payload and automatically updates the `livePlayers` state, refreshing the right-hand panel instantly without user intervention.
-   **`ChatInput.tsx`**: Manages user queries.
-   **`PlayerTable.tsx`**: Displays active player stats (Runs, Balls, SR) in a clean table format.
-   **`MatchList.tsx`**: Shows live/upcoming games using `api/match-list` endpoint.

## Tech Stack
-   **React + Vite**: For blazing fast development.
-   **TailwindCSS**: Utilitarian styling.
-   **Lucide React**: Minimalistic icons.

## Setup

1.  **Install Dependencies:**
    ```bash
    npm install
    ```

2.  **Environment:**
    The frontend is configured to connect to the backend at `http://localhost:8000` by default.
    **CRITICAL:** Ensure your backend is running on port 8000.
    
    To change the backend URL, create a `.env` file in the `Frontend` directory:
    ```bash
    VITE_API_URL=http://your-backend-url:port
    ```

3.  **Running:**
    ```bash
    npm run dev
    ```
    App runs on `http://localhost:5173`.
