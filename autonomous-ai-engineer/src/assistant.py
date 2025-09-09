# src/assistant.py

import os
import chromadb
import google.generativeai as genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

class JuniorAssistant:
    """
    A class representing the Junior Assistant, capable of ingesting
    a codebase and answering questions about it.
    """
    def __init__(self, db_path="./chroma_db", collection_name="codebase_collection"):
        load_dotenv()
        self._configure_genai()

        # Constants
        self.VALID_EXTENSIONS = ('.py', '.js', '.ts', '.html', '.css', '.md', '.java', '.cpp')
        self.COLLECTION_NAME = collection_name
        
        # Initialize ChromaDB client
        self.db_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.db_client.get_or_create_collection(name=self.COLLECTION_NAME)

        # Initialize the generative model
        self.model = genai.GenerativeModel("gemini-1.5-flash-latest")

    def _configure_genai(self):
        """Configures the Google Generative AI client."""
        try:
            genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        except KeyError:
            print("ERROR: GOOGLE_API_KEY not found in environment variables.")
            exit(1)

    def ingest(self, codebase_path: str):
        """
        Discovers, chunks, vectorizes, and indexes a codebase.
        """
        print(f"Starting ingestion for directory: {codebase_path}...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)

        for root, _, files in os.walk(codebase_path):
            for file in files:
                if file.endswith(self.VALID_EXTENSIONS):
                    file_path = os.path.join(root, file)
                    print(f"  - Processing file: {file_path}")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        chunks = text_splitter.split_text(content)
                        print(f"    - Split into {len(chunks)} chunks.")
                        
                        for i, chunk in enumerate(chunks):
                            response = genai.embed_content(
                                model="models/embedding-001",
                                content=chunk,
                                task_type="RETRIEVAL_DOCUMENT",
                                title=f"Chunk from {file_path}"
                            )
                            
                            self.collection.add(
                                embeddings=[response['embedding']],
                                documents=[chunk],
                                metadatas=[{"source": file_path}],
                                ids=[f"{file_path}-{i}"]
                            )
                    except Exception as e:
                        print(f"    - ERROR processing file {file_path}: {e}")

        print("\nIngestion complete!")
        print(f"Total documents in collection: {self.collection.count()}")

    def query(self, question: str) -> str:
        """
        Queries the vectorized codebase to answer a user's question.
        """
        question_embedding = genai.embed_content(
            model="models/embedding-001",
            content=question,
            task_type="RETRIEVAL_QUERY"
        )['embedding']

        results = self.collection.query(
            query_embeddings=[question_embedding],
            n_results=5
        )
        
        context = "\n---\n".join(results['documents'][0])
        
        prompt_template = f"""
        You are an expert AI software engineering assistant. Your task is to answer questions about a codebase.
        You will be given a user's question and a context of relevant code snippets.
        Your answer must be based ONLY on the provided context.
        If the context does not contain the information needed to answer the question, you must state that you cannot answer.
        
        CONTEXT:
        {context}
        
        QUESTION:
        {question}
        
        ANSWER:
        """
        
        response = self.model.generate_content(prompt_template)
        return response.text