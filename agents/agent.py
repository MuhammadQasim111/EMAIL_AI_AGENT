# agents-sdk-course-2/email-agent/agents/agent.py

import google.generativeai as genai
import os
import json
from typing import List, Dict, Any, Optional, Callable

# It's good practice to define a base class for tools if you have many
# For simplicity, we'll assume tools are just callables for now.

class Agent: # This is the class definition line
    """
    A foundational AI agent class that interacts with the Gemini LLM.
    It can be configured with a name, instructions, and a set of tools it can use.
    """
    # This 'def __init__' line MUST be indented by 4 spaces (or 1 tab) from 'class Agent:'
    def __init__(self, name: str, instructions: str, tools: Optional[List[Callable]] = None, model: str = "gemini-1.5-flash-latest"):
        # All lines below this 'def __init__', until the next method, MUST be indented by another 4 spaces
        self.name = name
        self.instructions = instructions
        self.tools = tools if tools is not None else []
        self.model_name = model
        
        # Configure Gemini API using an environment variable for the API key
        # Ensure GEMINI_API_KEY is set in your environment before running the app.
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set. Please set it before running.")
        
        genai.configure(api_key=gemini_api_key)
        
        # Initialize the generative model
        # If tools are provided, pass them to the model for function calling capabilities
        if self.tools:
            # Gemini models can use tools (function calling)
            # We need to convert Python functions to Google Generative AI tool format
            # This is a simplified conversion; for complex tools, you might need a more robust schema generation.
            gemini_tools = []
            for tool_func in self.tools:
                # Basic attempt to create a tool schema from function signature
                # This is a placeholder; a real implementation would use inspect or a library
                # to generate proper OpenAPI specs for the tool.
                tool_name = tool_func.__name__
                tool_description = tool_func.__doc__ if tool_func.__doc__ else f"Tool for {tool_name}"
                
                # For demonstration, we'll assume simple tools without complex arguments
                # A more robust solution would parse function signatures to define properties.
                # For now, we'll assume tools take arguments that can be passed as a dictionary.
                gemini_tools.append(
                    {
                        "function_declarations": [
                            {
                                "name": tool_name,
                                "description": tool_description,
                                "parameters": {
                                    "type": "OBJECT",
                                    "properties": {}, # Placeholder: actual properties need to be defined
                                    "required": []
                                }
                            }
                        ]
                    }
                )
            
            self.llm = genai.GenerativeModel(self.model_name, tools=gemini_tools)
        else:
            self.llm = genai.GenerativeModel(self.model_name)

    # This 'async def generate_response' line MUST be indented by 4 spaces from 'class Agent:'
    async def generate_response(self, prompt_message: str) -> str:
        """
        Generates a response from the LLM based on the prompt.
        This method is for direct LLM calls without tool orchestration.
        """
        try:
            response = await self.llm.generate_content_async(prompt_message)
            return response.text
        except Exception as e:
            print(f"Error during LLM content generation for agent {self.name}: {e}")
            return "An error occurred while processing your request with the AI."

    # This 'async def process_with_tools' line MUST be indented by 4 spaces from 'class Agent:'
    async def process_with_tools(self, chat_history: List[Dict[str, str]], context: Any) -> Dict[str, Any]:
        """
        Processes a conversation turn, potentially using tools.
        This method will be called by the Runner.
        Args:
            chat_history: A list of messages representing the conversation.
            context: The application-specific context (e.g., EmailContext).
        Returns:
            A dictionary containing 'final_output' and potentially 'tool_calls'.
        """
        try:
            # Prepare the chat history for the LLM
            # Ensure the last message is from the user
            contents = [{"role": m["role"], "parts": [{"text": m["content"]}]} for m in chat_history]
            
            chat_session = self.llm.start_chat(history=contents[:-1]) # Start chat with history excluding current user message
            
            # Get the user message text from the last message in contents
            user_message = contents[-1]["parts"][0]["text"]
            
            response = await chat_session.send_message_async(user_message)

            tool_calls = []
            final_output = ""

            # Check if the response contains tool calls or text
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate.content, "parts"):
                    for part in candidate.content.parts:
                        if hasattr(part, "function_call") and part.function_call:
                            tool_call = {
                                "name": getattr(part.function_call, "name", ""),
                                "args": dict(getattr(part.function_call, "args", {})) # Convert to dict
                            }
                            tool_calls.append(tool_call)
                        elif hasattr(part, "text") and part.text:
                            final_output += part.text

            return {
                "final_output": final_output,
                "tool_calls": tool_calls
            }

        except Exception as e:
            print(f"Error in agent {self.name} processing with tools: {e}")
            return {"final_output": f"An error occurred in agent {self.name}: {e}", "tool_calls": []}


 
  