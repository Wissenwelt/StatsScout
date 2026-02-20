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
        _requiresApproval?: boolean;
        _approvalAction?: string;
    };
    onApprove?: () => void;
    onReject?: () => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, onApprove, onReject }) => {
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

                    {/* Action Needed Button */}
                    {isAssistant && message._requiresApproval && onApprove && (
                        <div className="mt-4 pt-4 border-t border-zinc-100 flex items-center justify-between bg-orange-50/50 p-4 rounded-lg border border-orange-100">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center text-orange-600 shrink-0">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" /><path d="M12 9v4" /><path d="M12 17h.01" /></svg>
                                </div>
                                <div>
                                    <p className="text-sm font-medium text-orange-900">Action Required</p>
                                    <p className="text-xs text-orange-700 mt-0.5">{message._approvalAction || "Approve action"}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={onReject}
                                    className="px-4 py-2 bg-white hover:bg-zinc-50 border border-zinc-200 text-zinc-700 text-sm font-medium rounded-md shadow-sm transition-colors"
                                >
                                    Reject
                                </button>
                                <button
                                    onClick={onApprove}
                                    className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white text-sm font-medium rounded-md shadow-sm transition-colors"
                                >
                                    Approve
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ChatMessage;
