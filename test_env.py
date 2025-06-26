import os
from dotenv import load_dotenv
from pathlib import Path

dotenv_path = Path('.') / '.env'
print("Loading .env from:", dotenv_path.resolve())

success = load_dotenv(dotenv_path)
print("load_dotenv returned:", success)

token = os.getenv("DISCORD_TOKEN")
print("DISCORD_TOKEN:", token)
print("Type of token:", type(token))
