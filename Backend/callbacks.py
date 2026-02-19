import json
import asyncio
from typing import Any, Dict, List, Optional
from uuid import UUID
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult

class AgentCallbackHandler(AsyncCallbackHandler):
    """Callback handler for streaming LangChain agent events to a queue."""

    def __init__(self, queue: asyncio.Queue):
        self.queue = queue

    async def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Run when LLM starts running."""
        # We might not want to show raw LLM start to user, 
        # but we could show "Thinking..."
        pass

    async def on_chat_model_start(
        self, serialized: Dict[str, Any], messages: List[List[Any]], **kwargs: Any
    ) -> None:
        """Run when Chat Model starts running."""
        pass

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available with streaming=True on LLM."""
        # For agent "thoughts", we usually get them as full blocks in on_llm_end 
        # or we can stream tokens if we enable streaming on the LLM itself.
        # For now, let's focus on larger events (Thought/Action).
        pass

    async def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Run when tool starts running."""
        print(f"[Callback] Tool Start: {serialized.get('name')}")
        await self.queue.put(json.dumps({
            "type": "action",
            "content": f"Accessing tool: {serialized.get('name')}",
            "details": input_str
        }))

    async def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Run when tool ends running."""
        print(f"[Callback] Tool End: {output[:50]}...")
        # Do not truncate output as it might be JSON data for the frontend
        # display_output = output[:200] + "..." if len(output) > 200 else output
        await self.queue.put(json.dumps({
            "type": "observation",
            "content": output  # Send full output
        }))

    async def on_agent_action(self, action: Any, **kwargs: Any) -> None:
        """Run on agent action."""
        print(f"[Callback] Agent Action: {action.log[:50]}...")
        await self.queue.put(json.dumps({
            "type": "thought",
            "content": f"Thinking: {action.log}"
        }))

    async def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Run when chain ends running."""
        # We can handle final answer here or in the main loop
        pass
        
    async def on_text(self, text: str, **kwargs: Any) -> None:
        """Run on arbitrary text."""
        # Sometimes thoughts come here
        pass
