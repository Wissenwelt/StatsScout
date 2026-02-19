export interface Player {
    id: string;
    name: string;
    role: string;
    runs?: number;
    balls?: number;
    strikeRate?: number;
    wickets?: number;
    economy?: number;
    team: string;
}

export interface Match {
    id: string;
    team1: string;
    team2: string;
    status: string;
    startTime?: string;
    score?: string;
    result?: string;
    type: 'live' | 'upcoming' | 'recent' | 'scheduled';
}

export interface MatchListResponse {
    live: Match[];
    upcoming: Match[];
    recent: Match[];
}
