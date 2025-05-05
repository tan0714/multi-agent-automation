# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
import asyncio
import sys
import contextlib
import time
from pathlib import Path
from typing import List, Dict, Any
import os

from colorama import Fore, init
from dotenv import load_dotenv

from camel.agents.chat_agent import ToolCallingRecord
from camel.models import ModelFactory
from camel.toolkits import FunctionTool, MCPToolkit
from camel.types import ModelPlatformType, ModelType
from camel.logger import set_log_level
from camel.utils import print_text_animated

from owl.utils.enhanced_role_playing import OwlRolePlaying, arun_society

import pathlib

# Initialize colorama for cross-platform colored terminal output
init()

base_dir = pathlib.Path(__file__).parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))

set_log_level(level="INFO")


async def construct_society(
    question: str,
    tools: List[FunctionTool],
) -> OwlRolePlaying:
    r"""Build a multi-agent OwlRolePlaying instance for task completion.

    Args:
        question (str): The task to perform.
        tools (List[FunctionTool]): The MCP tools to use for interaction.

    Returns:
        OwlRolePlaying: The configured society of agents.
    """
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.QWEN,
            model_type=ModelType.QWEN_PLUS_LATEST,
            model_config_dict={"temperature": 0},
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.QWEN,
            model_type=ModelType.QWEN_PLUS_LATEST,
            model_config_dict={"temperature": 0},
        ),
    }

    user_agent_kwargs = {"model": models["user"]}
    assistant_agent_kwargs = {
        "model": models["assistant"],
        "tools": tools,
    }

    task_kwargs = {
        "task_prompt": question,
        "with_task_specify": False,
    }

    society = OwlRolePlaying(
        **task_kwargs,
        user_role_name="user",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="assistant",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )
    return society


def create_md_file(task: str) -> str:
    """Create a markdown file for the conversation with timestamp in filename.
    
    Args:
        task (str): The task being performed.
        
    Returns:
        str: Path to the created markdown file.
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    # Create logs directory if it doesn't exist
    logs_dir = Path("conversation_logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create a shortened task name for the filename
    task_short = task[:30].replace(" ", "_").replace("/", "_")
    filename = f"{logs_dir}/conversation_{timestamp}_{task_short}.md"
    
    # Initialize the file with header
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Agent Conversation: {task}\n\n")
        f.write(f"*Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write("## Task Details\n\n")
        f.write(f"**Task:** {task}\n\n")
        f.write("## Conversation\n\n")
    
    return filename


def write_to_md(filename: str, content: Dict[str, Any]) -> None:
    """Write content to the markdown file.
    
    Args:
        filename (str): Path to the markdown file.
        content (Dict[str, Any]): Content to write to the file.
    """
    with open(filename, "a", encoding="utf-8") as f:
        if "system_info" in content:
            f.write(f"### System Information\n\n")
            for key, value in content["system_info"].items():
                f.write(f"**{key}:** {value}\n\n")
        
        if "assistant" in content:
            f.write(f"### 🤖 Assistant\n\n")
            if "tool_calls" in content:
                f.write("**Tool Calls:**\n\n")
                for tool_call in content["tool_calls"]:
                    f.write(f"```\n{tool_call}\n```\n\n")
            f.write(f"{content['assistant']}\n\n")
            
        if "user" in content:
            f.write(f"### 👤 User\n\n")
            f.write(f"{content['user']}\n\n")
            
        if "summary" in content:
            f.write(f"## Summary\n\n")
            f.write(f"{content['summary']}\n\n")
            
        if "token_count" in content:
            f.write(f"**Total tokens used:** {content['token_count']}\n\n")


async def run_society_with_formatted_output(society: OwlRolePlaying, md_filename: str, round_limit: int = 15):
    """Run the society with nicely formatted terminal output and write to markdown.
    
    Args:
        society (OwlRolePlaying): The society to run.
        md_filename (str): Path to the markdown file for output.
        round_limit (int, optional): Maximum number of conversation rounds. Defaults to 15.
        
    Returns:
        tuple: (answer, chat_history, token_count)
    """
    print(Fore.GREEN + f"AI Assistant sys message:\n{society.assistant_sys_msg}\n")
    print(Fore.BLUE + f"AI User sys message:\n{society.user_sys_msg}\n")
    
    print(Fore.YELLOW + f"Original task prompt:\n{society.task_prompt}\n")
    print(Fore.CYAN + "Specified task prompt:" + f"\n{society.specified_task_prompt}\n")
    print(Fore.RED + f"Final task prompt:\n{society.task_prompt}\n")
    
    # Write system information to markdown
    write_to_md(md_filename, {
        "system_info": {
            "AI Assistant System Message": society.assistant_sys_msg,
            "AI User System Message": society.user_sys_msg,
            "Original Task Prompt": society.task_prompt,
            "Specified Task Prompt": society.specified_task_prompt,
            "Final Task Prompt": society.task_prompt
        }
    })
    
    input_msg = society.init_chat()
    chat_history = []
    token_count = {"total": 0}
    n = 0
    
    while n < round_limit:
        n += 1
        assistant_response, user_response = await society.astep(input_msg)
        
        md_content = {}
        
        if assistant_response.terminated:
            termination_msg = f"AI Assistant terminated. Reason: {assistant_response.info['termination_reasons']}."
            print(Fore.GREEN + termination_msg)
            md_content["summary"] = termination_msg
            write_to_md(md_filename, md_content)
            break
            
        if user_response.terminated:
            termination_msg = f"AI User terminated. Reason: {user_response.info['termination_reasons']}."
            print(Fore.GREEN + termination_msg)
            md_content["summary"] = termination_msg
            write_to_md(md_filename, md_content)
            break
            
        # Handle tool calls for both terminal and markdown
        if "tool_calls" in assistant_response.info:
            tool_calls: List[ToolCallingRecord] = [
                ToolCallingRecord(**call.as_dict())
                for call in assistant_response.info['tool_calls']
            ]
            md_content["tool_calls"] = tool_calls
            
            # Print to terminal
            print(Fore.GREEN + "AI Assistant:")
            for func_record in tool_calls:
                print(f"{func_record}")
        else:
            print(Fore.GREEN + "AI Assistant:")
            
        # Print assistant response to terminal
        print(f"{assistant_response.msg.content}\n")
        
        # Print user response to terminal
        print(Fore.BLUE + f"AI User:\n\n{user_response.msg.content}\n")
        
        # Build content for markdown file
        md_content["assistant"] = assistant_response.msg.content
        md_content["user"] = user_response.msg.content
        
        # Write to markdown
        write_to_md(md_filename, md_content)
        
        # Update chat history
        chat_history.append({
            "assistant": assistant_response.msg.content,
            "user": user_response.msg.content,
        })
        
        # Update token count
        if "token_count" in assistant_response.info:
            token_count["total"] += assistant_response.info["token_count"]
        
        if "TASK_DONE" in user_response.msg.content:
            task_done_msg = "Task completed successfully!"
            print(Fore.YELLOW + task_done_msg + "\n")
            write_to_md(md_filename, {"summary": task_done_msg})
            break
            
        input_msg = assistant_response.msg
    
    # Write token count information
    write_to_md(md_filename, {"token_count": token_count["total"]})
    
    # Extract final answer
    answer = assistant_response.msg.content if assistant_response and assistant_response.msg else ""
    
    return answer, chat_history, token_count


@contextlib.asynccontextmanager
async def mcp_toolkit_context(config_path):
    """Context manager for safely handling MCP Toolkit connection/disconnection.
    
    Args:
        config_path (str): Path to the MCP configuration file.
        
    Yields:
        MCPToolkit: The connected MCPToolkit instance.
    """
    toolkit = MCPToolkit(config_path=str(config_path))
    try:
        await toolkit.connect()
        print(Fore.GREEN + "Successfully connected to SSE server")
        yield toolkit
    finally:
        # Use a separate try/except to ensure we always attempt to disconnect
        try:
            await toolkit.disconnect()
            print(Fore.GREEN + "Successfully disconnected from SSE server")
        except Exception as e:
            # Just log the error but don't re-raise as we're in cleanup
            print(Fore.RED + f"Warning: Error during disconnect: {e}")


async def main():
    # Load SSE server configuration
    config_path = Path(__file__).parent / "mcp_sse_config.json"
    
    # Set default task - a simple example query
    default_task = (
        "Visit the Qwen3 GitHub repository, summarize the introduction of the repository."
        "Write a comprehensive HTML documentation site with the following features:"
        "A clear introduction to Qwen3"
        "Well-organized sections of the technical documentation"
        "Practical code examples"
        "A visually appealing purple technology theme (e.g. modern, clean, purple-accented design)"
        "Finally, deploy the HTML site and open it in the browser."
    )
    
    # Use command line argument if provided, otherwise use default task
    task = sys.argv[1] if len(sys.argv) > 1 else default_task
    
    try:
        # Create markdown file for conversation export
        md_filename = create_md_file(task)
        print(Fore.CYAN + f"Conversation will be saved to: {md_filename}")
        
        async with mcp_toolkit_context(config_path) as mcp_toolkit:
            # Get available tools
            tools = [*mcp_toolkit.get_tools()]
            
            # Build and run society
            print(Fore.YELLOW + f"Starting task: {task}\n")
            society = await construct_society(task, tools)
            answer, chat_history, token_count = await run_society_with_formatted_output(society, md_filename)
            
            print(Fore.GREEN + f"\nFinal Result: {answer}")
            print(Fore.CYAN + f"Total tokens used: {token_count['total']}")
            print(Fore.CYAN + f"Full conversation log saved to: {md_filename}")
            
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nReceived exit signal, shutting down...")
    except Exception as e:
        print(Fore.RED + f"Error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
