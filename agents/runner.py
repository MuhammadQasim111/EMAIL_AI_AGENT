# agents-sdk-course-2/email-agent/agents/runner.py

from typing import List, Dict, Any, Callable, Optional
import asyncio
import json
import inspect

# Assuming Agent class is defined in agent.py
from .agent import Agent 

class Runner:
    """
    The Runner class orchestrates the interaction with an AI agent,
    managing conversation history, tool execution, and context.
    """

    @staticmethod
    async def run(agent_instance: Agent, messages: List[Dict[str, str]], context: Any) -> Any:
        """
        Runs the agent's logic, including potential tool calls.
        Args:
            agent_instance: An instance of the Agent class.
            messages: A list of messages forming the conversation history.
            context: The application-specific context (e.g., EmailContext).
        Returns:
            A Result object containing the final output.
        """
        
        # We'll use a simple loop for demonstration.
        # In a more complex scenario, this would be a sophisticated agent loop
        # that handles multiple turns, tool outputs, and re-prompting the LLM.
        
        # The agent.process_with_tools method is designed to handle the LLM call
        # and identify potential tool calls.
        
        response_from_agent = await agent_instance.process_with_tools(messages, context)
        
        final_output = response_from_agent.get("final_output", "")
        tool_calls = response_from_agent.get("tool_calls", [])

        # Execute tools if the agent decided to call them
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Find the actual function from the agent's registered tools
            tool_func = next((t for t in agent_instance.tools if t.__name__ == tool_name), None)

            if tool_func:
                try:
                    # Inspect the function signature to correctly pass arguments
                    sig = inspect.signature(tool_func)
                    
                    # Filter args to only include those expected by the function
                    # and ensure 'context' is passed if the tool expects it.
                    filtered_args = {}
                    for param_name, param in sig.parameters.items():
                        if param_name == 'context':
                            filtered_args[param_name] = context
                        elif param_name in tool_args:
                            filtered_args[param_name] = tool_args[param_name]
                    
                    # Execute the tool function
                    print(f"Executing tool: {tool_name} with args: {filtered_args}")
                    tool_result = await asyncio.to_thread(tool_func, **filtered_args) # Run sync func in thread pool
                    final_output += f"\nTool `{tool_name}` executed. Result: {tool_result}"
                except Exception as e:
                    final_output += f"\nError executing tool `{tool_name}`: {e}"
            else:
                final_output += f"\nAgent requested unknown tool: `{tool_name}`"

        class Result:
            def __init__(self, final_output_str):
                self.final_output = final_output_str
        
        return Result(final_output)

