import { useState, useEffect, useRef } from 'react';
import ChatInput from './ChatInput';
import ChatMessage from './ChatMessage';
import Sidebar from './Sidebar';
import PlayerTable from './PlayerTable';
import MatchList from './MatchList';
import type { Player, Match } from '../types';
import { chatService } from '../services/api';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    thinking?: { type: 'thought' | 'action' | 'observation', content: string }[];
}

interface Session {
    id: string;
    title: string;
    messages: Message[];
}

function Dashboard() {
    // Chat State with Sessions
    const [sessions, setSessions] = useState<Session[]>([{
        id: '1',
        title: 'New Chat',
        messages: [{ role: 'assistant', content: 'Hello! I am StatsScout, your AI cricket analyst. Ask me about **live matches**, **player stats**, or **win predictions**!' }]
    }]);
    const [activeSessionId, setActiveSessionId] = useState('1');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Derived State
    const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0];
    const messages = activeSession.messages;

    // Wrapper for setMessages to update the active session
    const setMessages = (action: Message[] | ((prev: Message[]) => Message[])) => {
        setSessions(prevSessions => prevSessions.map(session => {
            if (session.id === activeSessionId) {
                const newMessages = typeof action === 'function' ? action(session.messages) : action;

                // Auto-update title based on first user message
                let newTitle = session.title;
                if (session.title === 'New Chat' && newMessages.length > 1) {
                    const userMsg = newMessages.find(m => m.role === 'user');
                    if (userMsg) {
                        newTitle = userMsg.content.slice(0, 25) + (userMsg.content.length > 25 ? '...' : '');
                    }
                }

                return { ...session, messages: newMessages, title: newTitle };
            }
            return session;
        }));
    };

    // Dashboard State
    const [livePlayers, setLivePlayers] = useState<Player[]>([]);
    const [highlightedPlayerId, setHighlightedPlayerId] = useState<string | undefined>(undefined);

    // Match List State
    const [matches, setMatches] = useState<{ live: Match[], upcoming: Match[], recent: Match[] }>({
        live: [],
        upcoming: [],
        recent: []
    });

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Fetch Match Data
    const fetchMatches = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/match-list');
            if (response.ok) {
                const data = await response.json();
                setMatches(data);
            }
        } catch (error) {
            console.error("Failed to fetch matches:", error);
        }
    };

    useEffect(() => {
        fetchMatches();
        const interval = setInterval(fetchMatches, 300000); // Refresh every 5 mins
        return () => clearInterval(interval);
    }, []);

    const handleSendMessage = async (content: string) => {
        const userMessage: Message = { role: 'user', content };
        setMessages((prev) => [...prev, userMessage]);
        setIsLoading(true);

        try {
            const assistantMessage: Message = {
                role: 'assistant',
                content: '',
                thinking: []
            };

            setMessages((prev) => [...prev, assistantMessage]);

            for await (const chunk of chatService.streamMessage(content)) {
                setMessages((prev) => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];

                    if (lastMsg.role === 'assistant') {
                        if (chunk.type === 'thought' || chunk.type === 'action' || chunk.type === 'observation') {
                            const currentThinking = lastMsg.thinking || [];
                            const lastThought = currentThinking[currentThinking.length - 1];
                            const isDuplicate = lastThought &&
                                lastThought.type === chunk.type &&
                                lastThought.content === chunk.content;

                            if (!isDuplicate) {
                                lastMsg.thinking = [...currentThinking, { type: chunk.type, content: chunk.content }];
                            }

                            // Check for Side Effects (Context Updates)
                            if (chunk.type === 'observation') {
                                try {
                                    // chunk.content is the tool output. 
                                    // If it's JSON from fetch_live_match_context, it will have "matches" key.
                                    const data = JSON.parse(chunk.content);
                                    if (data.matches && Array.isArray(data.matches)) {
                                        console.log("Auto-updating Live Context:", data);
                                        // Update the Live Players table with data from the first match found
                                        if (data.matches.length > 0) {
                                            setLivePlayers(data.matches[0].players || []);
                                        }
                                    }
                                } catch (e) {
                                    // Not JSON or non-match data, ignore.
                                }
                            }

                        } else if (chunk.type === 'answer') {
                            lastMsg.content += chunk.content;

                            // Client-Side Action 2: Agent-Triggered Player Highlight
                            // Agent can output "[HIGHLIGHT: Player Name]" to focus the UI
                            const highlightMatch = chunk.content.match(/\[HIGHLIGHT: (.*?)\]/);
                            if (highlightMatch) {
                                const playerName = highlightMatch[1];
                                console.log("Agent triggered highlight for:", playerName);
                                // Find player ID from livePlayers
                                const player = livePlayers.find(p => p.name.toLowerCase().includes(playerName.toLowerCase()));
                                if (player) {
                                    setHighlightedPlayerId(player.id);
                                }
                                // Remove the command from the visible message (optional, but cleaner)
                                lastMsg.content = lastMsg.content.replace(highlightMatch[0], "");
                            }

                        } else if (chunk.type === 'error') {
                            lastMsg.content += `\n[Error: ${chunk.content}]`;
                        }
                    }
                    return newMessages;
                });
            }
        } catch (error) {
            console.error('Chat Error:', error);
            const errorMessage: Message = {
                role: 'assistant',
                content: "**Error:** Could not reach the stats engine. Is the backend running?"
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleNewChat = () => {
        const newId = Date.now().toString();
        const newSession: Session = {
            id: newId,
            title: 'New Chat',
            messages: [{ role: 'assistant', content: 'Hello! I am StatsScout. Ready for a new match analysis!' }]
        };
        setSessions(prev => [newSession, ...prev]); // Add new session to top
        setActiveSessionId(newId);
        setHighlightedPlayerId(undefined); // Clear old context
    };

    const handleSelectSession = (id: string) => {
        setActiveSessionId(id);
    };



    return (
        <div className="flex bg-zinc-50 h-screen w-screen overflow-hidden text-zinc-900 antialiased font-sans">
            {/* Sidebar (Fixed width) */}
            <Sidebar
                onNewChat={handleNewChat}
                sessions={sessions}
                activeSessionId={activeSessionId}
                onSelectSession={handleSelectSession}
            />

            <div className="flex-1 flex flex-row overflow-hidden relative">

                {/* Left Panel: Chat (60%) */}
                <main className="flex-1 flex flex-col h-full bg-white border-r border-zinc-200 relative min-w-[400px]">
                    <div className="flex-1 overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-zinc-200 p-0">
                        <div className="flex flex-col min-h-full">
                            {messages.map((msg, index) => (
                                <ChatMessage key={index} message={msg} />
                            ))}
                            {isLoading && (
                                <div className="w-full py-8 bg-zinc-50/50 border-y border-zinc-100">
                                    <div className="max-w-3xl mx-auto flex gap-6 px-4">
                                        <div className="w-8 h-8 rounded-lg bg-zinc-100 flex items-center justify-center shrink-0">
                                            <div className="animate-spin w-4 h-4 rounded-full border-2 border-zinc-300 border-t-zinc-600" />
                                        </div>
                                        <div className="space-y-2 w-full max-w-md">
                                            <div className="h-2 bg-zinc-100 rounded w-full animate-pulse" />
                                            <div className="h-2 bg-zinc-100 rounded w-2/3 animate-pulse" />
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} className="h-32 shrink-0" />
                        </div>
                    </div>

                    <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-white via-white to-transparent pb-6 pt-10 px-4">
                        <div className="max-w-3xl mx-auto">
                            <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
                        </div>
                    </div>
                </main>

                {/* Right Panel: Live Stats (40%) */}
                <aside className="w-[450px] bg-zinc-50/50 flex flex-col border-l border-zinc-200 shrink-0">
                    <div className="p-4 border-b border-zinc-200 bg-white flex items-center justify-between">
                        <h2 className="font-semibold text-zinc-800">Match Center</h2>
                        <div className="flex items-center gap-2">
                            <span className="text-[10px] text-zinc-400 font-medium uppercase tracking-wider">
                                Auto-refreshing
                            </span>
                            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {/* Live Players Table (Populated via Agent Tools) */}
                        {livePlayers.length > 0 ? (
                            <PlayerTable players={livePlayers} highlightedPlayerId={highlightedPlayerId} title="Active Players" />
                        ) : (
                            <div className="p-6 text-center border-2 border-dashed border-zinc-200 rounded-xl bg-zinc-50/50">
                                <Trophy size={24} className="mx-auto text-zinc-300 mb-2" />
                                <p className="text-sm text-zinc-500">No active match context.</p>
                                <p className="text-xs text-zinc-400 mt-1">Ask "Who is playing?" to load live data.</p>
                            </div>
                        )}

                        {/* Match List */}
                        <MatchList matches={matches} />
                    </div>
                </aside>

            </div>
        </div>
    );
}

// Icon for empty state
import { Trophy } from 'lucide-react';

export default Dashboard;
