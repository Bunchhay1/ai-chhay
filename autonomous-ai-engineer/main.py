# main.py

import argparse
import os
from dotenv import load_dotenv
from src.assistant import JuniorAssistant
# Note: We no longer import Agent here
import google.generativeai as genai

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="An autonomous AI software engineer.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Ingest command
    parser_ingest = subparsers.add_parser("ingest", help="Ingest a codebase into the vector database.")
    parser_ingest.add_argument("path", type=str, help="The path to the codebase directory to ingest.")

    # Query command
    parser_query = subparsers.add_parser("query", help="Ask a question about the ingested codebase.")
    parser_query.add_argument("question", type=str, nargs='?', default=None, help="The question to ask. If not provided, enters interactive chat mode.")
    
    # We no longer have the "agent" command in this file
    
    args = parser.parse_args()
    
    try:
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    except KeyError:
        print("ERROR: GOOGLE_API_KEY not found in environment variables. Make sure it's in your .env file.")
        return

    if args.command == "ingest":
        assistant = JuniorAssistant()
        assistant.ingest(args.path)
    elif args.command == "query":
        assistant = JuniorAssistant()
        if args.question:
            answer = assistant.query(args.question)
            print("\n--- AI's Answer ---\n")
            print(answer)
            print("\n---------------------\n")
        else:
            print("Entering interactive chat mode. Type 'exit' to end.")
            while True:
                user_question = input("\nAsk a question: ")
                if user_question.lower() == 'exit':
                    break
                answer = assistant.query(user_question)
                print("\n--- AI's Answer ---\n")
                print(answer)
                print("\n---------------------\n")

if __name__ == "__main__":
    main()