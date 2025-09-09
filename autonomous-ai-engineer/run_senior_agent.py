# run_senior_agent.py (Ultimate Final Version - Self-Describing Toolbox)

import os
import json
import argparse
import inspect
from dotenv import load_dotenv
import google.generativeai as genai
import docker
from docker.errors import ContainerError, ImageNotFound
import PIL.Image

# --- PART 1: THE TOOLBOX (with all tools) ---

def read_file(filepath: str) -> str:
    """Reads the content of a specified file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"

def write_file(filepath: str, content: str) -> str:
    """Writes content to a specified file."""
    try:
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Success: Content written to '{filepath}'."
    except Exception as e:
        return f"Error: {e}"

def list_directory(path: str) -> str:
    """Lists files and directories."""
    try:
        if not os.path.isdir(path):
            return f"Error: '{path}' is not a valid directory."
        items = os.listdir(path)
        if not items:
            return f"The directory '{path}' is empty."
        return f"Contents of '{path}':\n- " + "\n- ".join(items)
    except Exception as e:
        return f"Error: {e}"

def execute_shell_command(command: str) -> str:
    """Executes a shell command in a secure Docker container."""
    print(f"--- EXECUTING SHELL COMMAND (in Docker) ---\n{command}\n-----------------------------")
    try:
        host_dir = os.getcwd()
        volumes = {host_dir: {'bind': '/workspace', 'mode': 'rw'}}
        client = docker.from_env()
        output = client.containers.run(
            "python:3.9-slim",
            ["/bin/sh", "-c", command],
            remove=True,
            stdout=True, stderr=True, detach=False,
            volumes=volumes,
            working_dir="/workspace"
        )
        return output.decode('utf-8')
    except Exception as e:
        return f"Docker Error: {e}"

def analyze_image(image_path: str, prompt: str) -> str:
    """
    Analyzes an image and answers a question about it. Use this to understand UI mockups, diagrams, or other visual information.
    """
    print(f"--- ANALYZING IMAGE: {image_path} ---")
    try:
        img = PIL.Image.open(image_path)
        vision_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = vision_model.generate_content([prompt, img])
        return response.text
    except Exception as e:
        return f"Error analyzing image: {e}"

# --- PART 2: THE "GROUNDED" PLANNER ---

class Planner:
    def __init__(self, model, available_tools):
        self.model = model
        self.system_prompt = self._build_system_prompt(available_tools)

    def _build_system_prompt(self, available_tools):
        tool_docs = ""
        for name, func in available_tools.items():
            signature = inspect.signature(func)
            description = func.__doc__
            tool_docs += f"- `{name}{signature}`: {description}\n"
        
        return f"""
You are an expert software architect. Your only job is to create a plan of tool calls to achieve a user's goal.
The plan must ONLY use the following available tools, and you MUST use the exact argument names specified in the function signature:
{tool_docs}
You MUST follow these rules:
1.  Create a realistic plan assuming all file operations happen in the current directory.
2.  The plan must include a final step to test that the goal was achieved.
3.  Respond with ONLY a valid JSON array of objects. Each object must have a "tool" key and an "args" key.
4.  Do NOT add any other text.
"""
    def create_plan(self, goal: str) -> list[dict]:
        print(f"--- Generating plan for goal: '{goal}' ---")
        chat = self.model.start_chat(history=[
            {'role': 'user', 'parts': [self.system_prompt]},
            {'role': 'model', 'parts': ["OK, I will create a plan using the exact tool signatures provided."]}
        ])
        try:
            response = chat.send_message(goal)
            text_response = response.text
            start_index = text_response.find('[')
            end_index = text_response.rfind(']')
            if start_index != -1 and end_index != -1:
                json_text = text_response[start_index : end_index + 1]
                plan = json.loads(json_text)
                print("--- Plan Generated Successfully ---")
                for i, step in enumerate(plan, 1):
                    print(f"Step {i}: {step['tool']}({step['args']})")
                print("---------------------------------")
                return plan
            else:
                print("Error: Could not find a valid JSON list in the model's response.")
                return []
        except Exception as e:
            print(f"An unexpected error occurred during planning: {e}")
            return []

# --- PART 3: THE "SUPERVISOR" ORCHESTRATOR / EXECUTOR ---

def check_completion(goal, full_plan, observation, supervisor_model):
    """Uses an AI Supervisor to check if the goal has been met."""
    print("--- SUPERVISOR: Checking if goal is complete... ---")
    prompt = f"""
As a supervisor, your job is to determine if the original goal has been fully achieved.
- Original Goal: "{goal}"
- The Full Plan: {full_plan}
- The result of the last executed step was: "{observation}"
Based on the result of the last step, has the original goal been fully completed? The goal is complete only if the final step of the plan was a test that produced a successful result. Respond with only "YES" or "NO".
"""
    response = supervisor_model.generate_content(prompt)
    return "YES" in response.text

def main():
    load_dotenv()
    try:
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    except KeyError:
        print("ERROR: GOOGLE_API_KEY not found. Make sure it's in your .env file.")
        return

    parser = argparse.ArgumentParser(description="Run the Autonomous AI Engineer.")
    parser.add_argument("goal", type=str, help="The high-level goal.")
    args = parser.parse_args()

    print("--- INITIALIZING AUTONOMOUS AI ENGINEER ---")
    
    tool_functions = {
        "read_file": read_file, "write_file": write_file,
        "list_directory": list_directory, "execute_shell_command": execute_shell_command,
        "analyze_image": analyze_image,
    }

    planner_model = genai.GenerativeModel("gemini-1.5-flash-latest")
    supervisor_model = genai.GenerativeModel("gemini-1.5-flash-latest")
    planner = Planner(model=planner_model, available_tools=tool_functions)
    
    plan = planner.create_plan(args.goal)

    if not plan:
        print("--- SYSTEM: Could not generate a plan. Shutting down. ---")
        return

    print("\n--- SYSTEM: Starting execution of the plan ---")
    
    original_plan = list(plan)

    for i, step in enumerate(plan, 1):
        tool_name = step["tool"]
        tool_args = step["args"]
        print(f"\n--- EXECUTING STEP {i} of {len(original_plan)}: {tool_name}({tool_args}) ---")
        
        tool_function = tool_functions.get(tool_name)
        if not tool_function:
            print(f"Error: Tool '{tool_name}' not found.")
            continue
        
        observation = tool_function(**tool_args)
        print(f"Observation: {observation}")

        if check_completion(args.goal, original_plan, observation, supervisor_model):
            print("\n--- SUPERVISOR: Goal has been successfully completed! ---")
            break
    
    print("\n--- SYSTEM: Execution finished. ---")

if __name__ == "__main__":
    main()

