import React, { useState, useRef, useEffect } from 'react';
import { SendHorizontal, Paperclip } from 'lucide-react';

interface ChatInputProps {
    onSendMessage: (message: string) => void;
    isLoading?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, isLoading }) => {
    const [input, setInput] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
        }
    }, [input]);

    const handleSubmit = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (input.trim() && !isLoading) {
            onSendMessage(input.trim());
            setInput('');
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!isLoading) {
                handleSubmit();
            }
        }
    };

    return (
        <div className="w-full pt-2 pb-6 px-4">
            <form
                onSubmit={handleSubmit}
                className="max-w-3xl mx-auto relative flex items-end gap-2 bg-white border border-zinc-200 rounded-2xl p-3 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07),0_10px_20px_-2px_rgba(0,0,0,0.04)] focus-within:border-zinc-300 focus-within:shadow-[0_2px_20px_-3px_rgba(0,0,0,0.1)] transition-all"
            >
                <button
                    type="button"
                    className="p-2 text-zinc-400 hover:text-zinc-600 transition-colors shrink-0"
                >
                    <Paperclip size={20} />
                </button>

                <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Type a message..."
                    rows={1}
                    className="flex-1 bg-transparent border-none focus:ring-0 text-zinc-800 py-2 px-1 resize-none max-h-[200px] text-sm md:text-[16px] placeholder:text-zinc-400"
                />

                <button
                    type="submit"
                    disabled={!input.trim() || isLoading}
                    className={`p-2 rounded-xl transition-all shrink-0 ${input.trim() && !isLoading
                        ? 'bg-zinc-900 text-white hover:bg-zinc-800'
                        : 'text-zinc-300 cursor-not-allowed'
                        }`}
                >
                    <SendHorizontal size={20} />
                </button>
            </form>
        </div>
    );
};

export default ChatInput;
