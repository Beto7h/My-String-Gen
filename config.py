import os

class Config:
    API_ID = int(os.environ.get("API_ID", 12345)) # El default es ejemplo
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
