# run_agent.py (version 9 - FINAL)

import os
import json
import inspect
import docker
from docker.errors import ContainerError, ImageNotFound
from dotenv import load_dotenv
import google.generativeai as genai
import argparse

# --- PART 1: DEFINE ALL TOOLS ---
# (This part is unchanged and correct)
def read_file(filepath: str) -> str:
    """Reads the content of a specified file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return f.read()
    except Exception as e: return f"Error: {e}"

def write_file(filepath: str, content: str) -> str:
    """Writes content to a specified file."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f: f.write(content)
        return f"Success: Content written to '{filepath}'."
    except Exception as e: return f"Error: {e}"

def list_directory(path: str) -> str:
    """Lists the files and directories in a specified path."""
    try:
        if not os.path.isdir(path): return f"Error: '{path}' is not a directory."
        items = os.listdir(path)
        if not items: return f"The directory '{path}' is empty."
        return f"Contents of '{path}':\n- " + "\n- ".join(items)
    except Exception as e: return f"Error: {e}"

def execute_python_code(code: str) -> str:
    """Executes Python code in a secure Docker container."""
    print(f"--- EXECUTING CODE ---\n{code}\n----------------------")
    try:
        client = docker.from_env()
        output = client.containers.run(
            "python:3.9-slim", ["python", "-c", code], remove=True,
            stdout=True, stderr=True, detach=False
        )
        return output.decode('utf-8')
    except Exception as e: return f"Docker Error: {e}"

# --- PART 2: THE FINAL, CORRECTED AGENT LOGIC ---
def run_agent(task: str):
    """Initializes and runs the agent with the final, correct logic."""
    tool_functions = {
        "read_file": read_file, "write_file": write_file,
        "list_directory": list_directory, "execute_python_code": execute_python_code,
    }

    print("Initializing agent...")
    model = genai.GenerativeModel("gemini-1.5-flash-latest", tools=tool_functions.values())
    chat = model.start_chat()

    print(f"--- Running task ---\n{task}\n--------------------")
    response = chat.send_message(task)

    while True:
        function_calls_to_make = []
        for part in response.candidates[0].content.parts:
            if part.function_call:
                function_calls_to_make.append(part.function_call)

        if function_calls_to_make:
            print(f"Action: Model wants to call {len(function_calls_to_make)} tool(s)...")
            tool_responses = []
            for call in function_calls_to_make:
                tool_name = call.name
                tool_args = {key: value for key, value in call.args.items()}
                print(f"  - Calling: {tool_name}({tool_args})")

                tool_function = tool_functions.get(tool_name)
                if not tool_function: raise ValueError(f"Unknown tool: {tool_name}")
                
                try:
                    tool_result = tool_function(**tool_args)
                    # --- THE ONLY CHANGE IS ON THE NEXT LINE ---
                    # We wrap the string result in a dictionary as the API expects.
                    tool_responses.append({"name": tool_name, "response": {"result": tool_result}})
                except Exception as e:
                    tool_responses.append({"name": tool_name, "response": {"result": f"Error: {e}"}})

            print("Observation: Sending tool results back to the model...\n")
            response = chat.send_message([{"function_response": r} for r in tool_responses])
        
        else:
            print("--- Task Finished ---")
            print(response.text)
            break

# --- PART 3: RUN THE AGENT ---
# (This part is unchanged)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the autonomous agent.")
    parser.add_argument("task", type=str, help="The task for the agent.")
    args = parser.parse_args()

    load_dotenv()
    try:
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    except KeyError:
        print("ERROR: GOOGLE_API_KEY not found in your .env file.")
        exit()

    run_agent(args.task)