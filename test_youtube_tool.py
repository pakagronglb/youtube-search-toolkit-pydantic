import time
from datetime import datetime
from textwrap import dedent
from rich import print
from rich.prompt import Prompt
from pydantic_ai import Agent, Tool
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from tools.google import YouTubeTool, download_transcript

youtube_tool = YouTubeTool('client-secret.json')

def time_delay(duration: int):
    """
    Function to delay execution for a specified duration in seconds.

    Args:
        duration (int): Duration in seconds to delay execution.
    """
    time.sleep(duration)

def youtube_agent_setup():
    agent = Agent(
        name='YouTube Agent',
        model=OpenAIModel('gpt-4o-mini'),
        model_settings=OpenAIModelSettings(max_tokens=5000, temperature=0.1),
        system_prompt=dedent("""
        - When performing function calls, execute only one function at a time in a strictly sequential manner, regardless of the task or the number of entities involved. After each function call, invoke the `time_delay(duration: int)` function with a default delay of 3 seconds, unless a different duration is explicitly specified. Do not allow any overlap, batching, or parallel execution of tool calls, even if a function supports processing multiple inputs or the task involves multiple entities. Each function call must complete fully, followed by the delay, before the next call begins. For example:  
            1. Call a function with its arguments (e.g., a search operation).  
            2. Call `time_delay(duration: int)` with a delay of 3 seconds.  
            3. Call the next function with its arguments (e.g., a details retrieval operation).  
            4. Call `time_delay(duration: int)` with a delay of 3 seconds.  
            5. Continue this pattern for all subsequent function calls.  

        - For tasks involving multiple steps, entities, or items (e.g., searching for multiple items and fetching details for each), treat each individual operation as a separate function call and apply the sequence above. Even if a function can handle multiple inputs (e.g., multiple IDs), process only one item or entity at a time unless explicitly instructed otherwise, inserting a `time_delay` of 3 seconds between each call. Complete all operations for one step or entity before moving to the next.  

        - General example for a multi-step task with multiple entities:  
            1. Call a function to search for the first entity (e.g., "Entity A").  
            2. Call `time_delay(duration=3)`.  
            3. Call a function to get details for "Entity A".  
            4. Call `time_delay(duration=3)`.  
            5. Call a function to search for the second entity (e.g., "Entity B").  
            6. Call `time_delay(duration=3)`.  
            7. Call a function to get details for "Entity B".  

        - If a 403 Forbidden error is encountered during execution, immediately stop the process and return the error message "403 Forbidden Error: Access Denied" to the user.  

        - Apply this sequence universally to all tool calls unless the user explicitly instructs otherwise (e.g., "batch these operations" or "skip delays"). If such an exception is requested, follow the user's specific instructions instead.
        """),
        tools=[
            Tool(youtube_tool.get_channel_info, max_retries=3),
            Tool(youtube_tool.search_channel, max_retries=3),
            Tool(youtube_tool.search_playlist, max_retries=3),
            Tool(youtube_tool.search_videos, max_retries=3),
            Tool(youtube_tool.get_video_info, max_retries=3),
            Tool(youtube_tool.get_channel_videos, max_retries=3),
            Tool(youtube_tool.construct_hyperlink, max_retries=3),
            Tool(time_delay, max_retries=1),
            Tool(download_transcript, max_retries=3),
        ],
        retries=2
    )

    @agent.system_prompt
    def current_time():
        return 'Current time: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return agent

def main(): 
    youtube_agent = youtube_agent_setup()

    message_history = []

    while True:
        prompt = Prompt.ask('User')
        if prompt == 'exit' or prompt == 'quit':
            break

        try:
            res = youtube_agent.run_sync(prompt, message_history=message_history)
            print(res.data)
            print('---' * 20) 
            print(f'Input tokens: {res.usage().request_tokens}. Output tokens: {res.usage().response_tokens}.')
            
            message_history = res.new_messages()

        except TimeoutError:
            print("The operation timed out. Please try again with a simpler query.")
  
        except Exception as e:
            print(f"An error occurred: {str(e)}")

main()