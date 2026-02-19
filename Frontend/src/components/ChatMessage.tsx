import React from 'react';
import { User } from 'lucide-react';
import CricketBotIcon from './CricketBotIcon';
import ThinkingProcess from './ThinkingProcess';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatMessageProps {
    message: {
        role: 'user' | 'assistant';
        content: string;
        thinking?: { type: 'thought' | 'action' | 'observation', content: string }[];
    };
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
    const isAssistant = message.role === 'assistant';

    // Parse tags
    let content = message.content;
    const isScoutingReport = content.includes('[SCOUTING REPORT]');
    const isKnowledgeBase = content.includes('[SOURCE: KNOWLEDGE_BASE]');

    // Clean content
    content = content.replace('[SCOUTING REPORT]', '').replace('[SOURCE: KNOWLEDGE_BASE]', '').trim();

    return (
        <div className={`w-full py-8 ${isAssistant ? 'bg-zinc-50/50 border-y border-zinc-100' : 'bg-white'}`}>
            <div className="max-w-3xl mx-auto flex gap-6 px-4 shrink-0">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 shadow-sm border ${isAssistant ? 'bg-white border-zinc-200 text-zinc-600' : 'bg-zinc-100 border-zinc-200 text-zinc-500'
                    }`}>
                    {isAssistant ? <CricketBotIcon size={18} /> : <User size={18} />}
                </div>
                <div className="flex-1 space-y-2 overflow-hidden min-w-0">
                    {/* Thinking Process (Only for Assistant) */}
                    {isAssistant && message.thinking && message.thinking.length > 0 && (
                        <ThinkingProcess logs={message.thinking} />
                    )}

                    {/* Scouting Badges */}
                    {(isScoutingReport || isKnowledgeBase) && (
                        <div className="flex gap-2 mb-3">
                            {isScoutingReport && (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
                                    Scouting Report
                                </span>
                            )}
                            {isKnowledgeBase && (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 border border-emerald-200">
                                    Knowledge Base
                                </span>
                            )}
                        </div>
                    )}

                    <div className="text-zinc-800 leading-relaxed text-[15px] prose prose-zinc max-w-none prose-p:leading-relaxed prose-pre:bg-zinc-100 prose-pre:border prose-pre:border-zinc-200">
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                table: ({ node, ...props }) => <div className="overflow-x-auto my-4 border rounded-lg"><table className="w-full text-sm text-left" {...props} /></div>,
                                thead: ({ node, ...props }) => <thead className="bg-zinc-100 uppercase text-xs font-semibold text-zinc-600" {...props} />,
                                th: ({ node, ...props }) => <th className="px-4 py-2 border-b border-zinc-200" {...props} />,
                                td: ({ node, ...props }) => <td className="px-4 py-2 border-b border-zinc-100" {...props} />,
                                tr: ({ node, ...props }) => <tr className="hover:bg-zinc-50/50" {...props} />
                            }}
                        >
                            {content}
                        </ReactMarkdown>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatMessage;
