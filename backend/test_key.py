import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY", "")

if not api_key:
    print("OPENAI_API_KEY is completely missing from .env")
elif api_key.startswith('"') or api_key.endswith('"') or api_key.startswith("'") or api_key.endswith("'"):
    print("❌ Your API key has quotes around it. Remove the quotes in .env.")
elif api_key != api_key.strip():
    print("❌ Your API key has trailing or leading spaces. Remove them in .env.")
elif not api_key.startswith("sk-"):
    print("❌ Your API key does not start with 'sk-'. It might be copied incorrectly.")
else:
    print("✅ The formatting of the key looks correct (no quotes, no spaces, starts with sk-).")
    print(f"Length of key: {len(api_key)} characters")
