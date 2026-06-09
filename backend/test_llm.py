import os
import asyncio
from dotenv import load_dotenv

# Load env before importing tools
load_dotenv()
os.environ["LLM_MODEL"] = "gemini-pro"

from github.reader import fetch_repo
from agent.workflow import analyze_with_llm

async def test():
    print("Fetching repo...")
    fetch = await fetch_repo("https://github.com/RyanCodrai/turbovec")
    print(f"Tree paths: {len(fetch.tree_paths)}")
    
    print("Running LLM analysis...")
    res = await analyze_with_llm(fetch)
    print(f"Result: {res}")

if __name__ == "__main__":
    asyncio.run(test())
