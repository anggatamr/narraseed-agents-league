import os
from pathlib import Path
from dotenv import load_dotenv

# Locate and load the .env file in the backend directory
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()
