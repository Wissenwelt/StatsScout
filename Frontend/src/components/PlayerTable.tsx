import React from 'react';
import { Activity } from 'lucide-react';

import type { Player } from '../types';

interface PlayerTableProps {
    players: Player[];
    highlightedPlayerId?: string;
    title: string;
}

const PlayerTable: React.FC<PlayerTableProps> = ({ players, highlightedPlayerId, title }) => {
    return (
        <div className="w-full bg-white rounded-xl border border-zinc-200 overflow-hidden shadow-sm">
            <div className="bg-zinc-50 border-b border-zinc-100 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Activity size={16} className="text-indigo-500" />
                    <h3 className="font-semibold text-zinc-800 text-sm">{title}</h3>
                </div>
                <span className="text-xs text-zinc-500 font-medium bg-zinc-100 px-2 py-1 rounded-full">
                    Live
                </span>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                    <thead className="text-xs text-zinc-500 uppercase bg-zinc-50/50 border-b border-zinc-100">
                        <tr>
                            <th className="px-4 py-3 font-medium">Player</th>
                            <th className="px-4 py-3 font-medium text-right">R (B)</th>
                            <th className="px-4 py-3 font-medium text-right">SR</th>
                            <th className="px-4 py-3 font-medium text-right">Wkt (Econ)</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-100">
                        {players.length > 0 ? (
                            players.map((player) => {
                                const isHighlighted = highlightedPlayerId === player.id;
                                return (
                                    <tr
                                        key={player.id}
                                        className={`transition-colors duration-300 ${isHighlighted ? 'bg-yellow-50 hover:bg-yellow-100' : 'hover:bg-zinc-50'}`}
                                    >
                                        <td className="px-4 py-3 font-medium text-zinc-900 flex items-center gap-2">
                                            {isHighlighted && <div className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />}
                                            <div className="flex flex-col">
                                                <span>{player.name}</span>
                                                <span className="text-[10px] text-zinc-400 uppercase tracking-wider font-semibold">{player.role}</span>
                                            </div>
                                        </td>
                                        <td className="px-4 py-3 text-right text-zinc-600 font-mono">
                                            {player.runs !== undefined ? (
                                                <span>
                                                    <span className="font-bold text-zinc-900">{player.runs}</span>
                                                    <span className="text-zinc-400 text-xs"> ({player.balls})</span>
                                                </span>
                                            ) : '-'}
                                        </td>
                                        <td className="px-4 py-3 text-right text-zinc-600 font-mono">
                                            {player.strikeRate || '-'}
                                        </td>
                                        <td className="px-4 py-3 text-right text-zinc-600 font-mono">
                                            {player.wickets !== undefined ? (
                                                <span>
                                                    <span className="font-bold text-indigo-600">{player.wickets}</span>
                                                    <span className="text-zinc-400 text-xs"> ({player.economy})</span>
                                                </span>
                                            ) : '-'}
                                        </td>
                                    </tr>
                                );
                            })
                        ) : (
                            <tr>
                                <td colSpan={4} className="px-4 py-8 text-center text-zinc-400 italic">
                                    No players active or data unavailable.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default PlayerTable;
