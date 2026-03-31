import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

OWNER_ID = os.getenv("OWNER_ID")
ALLOWED_USERS = {int(OWNER_ID)} if OWNER_ID else set()

def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_USERS

# Helper: run blocking calls in thread
async def run_blocking(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)
