import React from 'react';
import { Calendar, Clock, Trophy } from 'lucide-react';
import type { Match } from '../types';

interface MatchListProps {
    matches: {
        live: Match[];
        upcoming: Match[];
        recent: Match[];
    };
    onSelectMatch?: (match: Match) => void;
}

const MatchList: React.FC<MatchListProps> = ({ matches, onSelectMatch }) => {
    const hasMatches = matches.live.length > 0 || matches.upcoming.length > 0 || matches.recent.length > 0;

    if (!hasMatches) {
        return (
            <div className="flex flex-col items-center justify-center p-8 text-zinc-400">
                <Trophy size={32} className="mb-2 opacity-50" />
                <p>No matches found.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Live Matches */}
            {matches.live.length > 0 && (
                <div className="space-y-2">
                    <h3 className="text-xs font-semibold text-red-500 uppercase tracking-wider flex items-center gap-1.5">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                        </span>
                        Live Now
                    </h3>
                    <div className="space-y-2">
                        {matches.live.map((match) => (
                            <div
                                key={match.id}
                                onClick={() => onSelectMatch?.(match)}
                                className="bg-white border border-red-100 rounded-lg p-3 shadow-sm hover:border-red-200 hover:shadow-md transition-all cursor-pointer relative overflow-hidden group"
                            >
                                <div className="absolute top-0 right-0 p-1.5 bg-red-50 rounded-bl-lg">
                                    <span className="text-[10px] font-bold text-red-600 px-1">LIVE</span>
                                </div>
                                <div className="space-y-1">
                                    <div className="font-semibold text-zinc-800 text-sm">{match.team1}</div>
                                    <div className="text-xs text-zinc-400 font-medium">vs</div>
                                    <div className="font-semibold text-zinc-800 text-sm">{match.team2}</div>
                                </div>
                                {match.score && (
                                    <div className="mt-2 pt-2 border-t border-red-50 text-xs text-red-700 font-mono">
                                        {match.score}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Upcoming Matches */}
            {matches.upcoming.length > 0 && (
                <div className="space-y-2">
                    <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider flex items-center gap-1.5">
                        <Calendar size={12} />
                        Upcoming
                    </h3>
                    <div className="space-y-2">
                        {matches.upcoming.map((match) => (
                            <div
                                key={match.id}
                                className="bg-white border border-zinc-200 rounded-lg p-3 hover:border-zinc-300 transition-colors"
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <div className="space-y-0.5">
                                        <div className="text-sm font-medium text-zinc-900">{match.team1}</div>
                                        <div className="text-sm font-medium text-zinc-900">{match.team2}</div>
                                    </div>
                                    {match.startTime && (
                                        <div className="text-[10px] bg-zinc-100 text-zinc-500 px-1.5 py-0.5 rounded flex items-center gap-1">
                                            <Clock size={10} />
                                            {new Date(match.startTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Recent Matches */}
            {matches.recent.length > 0 && (
                <div className="space-y-2">
                    <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider flex items-center gap-1.5">
                        <Trophy size={12} />
                        Completed
                    </h3>
                    <div className="space-y-2">
                        {matches.recent.map((match) => (
                            <div
                                key={match.id}
                                className="bg-zinc-50 border border-zinc-200 rounded-lg p-3 hover:border-zinc-300 transition-colors"
                            >
                                <div className="flex flex-col gap-2">
                                    <div className="font-semibold text-sm text-zinc-900 flex items-center justify-between">
                                        <span>{match.team1}</span>
                                        <span className="text-xs text-zinc-400 font-normal px-1">vs</span>
                                        <span>{match.team2}</span>
                                    </div>

                                    {match.score && (
                                        <div className="text-xs font-mono text-zinc-700 bg-white border border-zinc-100 rounded px-2 py-1.5 text-center shadow-sm">
                                            {match.score}
                                        </div>
                                    )}

                                    {match.result ? (
                                        <div className="text-xs font-medium text-emerald-700 flex items-center justify-center gap-1.5 bg-emerald-50/50 py-1 rounded">
                                            <Trophy size={10} className="text-emerald-500" />
                                            {match.result}
                                        </div>
                                    ) : (
                                        <div className="text-[10px] text-zinc-400 uppercase tracking-wider text-center">
                                            {match.status.replace(/_/g, " ")}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default MatchList;
