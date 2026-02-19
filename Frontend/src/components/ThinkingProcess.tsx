import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Calculator, Database, Brain, CheckCircle2 } from 'lucide-react';

interface LogEntry {
    type: 'thought' | 'action' | 'observation';
    content: string;
}

interface ThinkingProcessProps {
    logs: LogEntry[];
}

const ThinkingProcess: React.FC<ThinkingProcessProps> = ({ logs }) => {
    const [isOpen, setIsOpen] = useState(true);

    if (!logs || logs.length === 0) return null;

    return (
        <div className="mb-4 rounded-lg border border-zinc-200 bg-zinc-50 overflow-hidden">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between p-3 bg-zinc-100 hover:bg-zinc-200/50 transition-colors"
            >
                <div className="flex items-center gap-2 text-sm font-medium text-zinc-700">
                    <Brain size={16} className="text-purple-600" />
                    <span>Thinking Process</span>
                    <span className="bg-zinc-200 text-zinc-600 px-2 py-0.5 rounded-full text-xs">
                        {logs.length} steps
                    </span>
                </div>
                {isOpen ? <ChevronDown size={16} className="text-zinc-500" /> : <ChevronRight size={16} className="text-zinc-500" />}
            </button>

            {isOpen && (
                <div className="p-4 space-y-3 bg-zinc-50/50">
                    {logs.map((log, index) => (
                        <div key={index} className="flex gap-3 text-sm group">
                            <div className="mt-0.5 shrink-0">
                                {log.type === 'thought' && <div className="w-1.5 h-1.5 rounded-full bg-zinc-400 mt-2" />}
                                {log.type === 'action' && <Calculator size={14} className="text-blue-500" />}
                                {log.type === 'observation' && <Database size={14} className="text-emerald-500" />}
                            </div>

                            <div className="flex-1 min-w-0">
                                <p className={`whitespace-pre-wrap break-words ${log.type === 'thought' ? 'text-zinc-500 italic' :
                                        log.type === 'action' ? 'text-blue-700 font-mono text-xs bg-blue-50/50 p-2 rounded border border-blue-100' :
                                            'text-emerald-700 font-mono text-xs bg-emerald-50/50 p-2 rounded border border-emerald-100'
                                    }`}>
                                    {log.content}
                                </p>
                            </div>
                        </div>
                    ))}
                    <div className="flex gap-3 text-sm items-center text-zinc-400 pl-7 pt-1">
                        <CheckCircle2 size={12} />
                        <span className="text-xs">Reasoning complete</span>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ThinkingProcess;
