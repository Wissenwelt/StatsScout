/**
 * API Service for StatsScout
 * Following industry standards for type-safety and separation of concerns.
 */

export interface ChatRequest {
    message: string;
}

export interface ChatResponse {
    role: 'assistant';
    content: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const chatService = {
    /**
     * Sends a message to the backend and streams the response.
     * Yields partial updates as they arrive.
     */
    async *streamMessage(content: string): AsyncGenerator<any, void, unknown> {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: content } as ChatRequest),
        });

        if (!response.ok) {
            const errorBody = await response.text();
            throw new Error(`API Error (${response.status}): ${errorBody || 'Unable to connect to service'}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) throw new Error('Response body is not readable');

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        yield data;
                    } catch (e) {
                        console.warn('Failed to parse SSE data:', line);
                    }
                }
            }
        }
    }
};
