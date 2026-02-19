import React from 'react';
import { Plus, MessageSquare } from 'lucide-react';

interface SidebarProps {
    onNewChat: () => void;
    sessions: { id: string; title: string }[];
    activeSessionId: string;
    onSelectSession: (id: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ onNewChat, sessions, activeSessionId, onSelectSession }) => {
    return (
        <div className="w-64 bg-zinc-50 h-screen flex flex-col text-zinc-900 border-r border-zinc-200">
            <div className="p-4">
                <button
                    onClick={onNewChat}
                    className="w-full flex items-center gap-3 px-3 py-2 border border-zinc-300 rounded-lg hover:bg-zinc-100 transition-colors text-sm font-medium mb-4 shadow-sm bg-white"
                >
                    <Plus size={16} />
                    New chat
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-2 space-y-1">
                <div className="px-3 mb-2">
                    <p className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">History</p>
                </div>
                {sessions.map((session) => (
                    <button
                        key={session.id}
                        onClick={() => onSelectSession(session.id)}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-sm text-left truncate group relative ${activeSessionId === session.id
                                ? 'bg-zinc-200 text-zinc-900 font-medium'
                                : 'text-zinc-600 hover:bg-zinc-100'
                            }`}
                    >
                        <MessageSquare size={16} className={`shrink-0 ${activeSessionId === session.id ? 'text-zinc-900' : 'text-zinc-400'}`} />
                        <span className="truncate">{session.title}</span>
                    </button>
                ))}
            </div>

            <div className="p-4 border-t border-zinc-200">
                <div className="flex items-center gap-3 px-2 py-1">
                    <div className="w-7 h-7 rounded-full bg-zinc-200 flex items-center justify-center font-bold text-[10px] text-zinc-600 border border-zinc-300">
                        VJ
                    </div>
                    <div className="flex-1 text-xs font-medium truncate text-zinc-600">
                        Vijendra
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
