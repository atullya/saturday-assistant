import discord
from discord import app_commands
import os
import socket
import time
from dotenv import load_dotenv

try:
    _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _lock_socket.bind(('127.0.0.1', 49132))
except OSError:
    print("Another instance is running. Waiting infinitely to prevent duplicate connections.")
    while True: time.sleep(3600)

load_dotenv()

DISCORD_TOKEN  = os.getenv("DISCORD_TOKEN")
ASSISTANT_NAME = "Saturday"

GMAIL_CMD      = "!gmail"
TODO_CMD       = "!todo"
SATURDAY_CMD   = "!saturday"
SATURDAY_SHORT = "!s"
PORTFOLIO_CMD  = "!portfolio"
RENT_CMD       = "!rent"
CAL_CMD        = "!cal"
RAG_CMD        = "!rag"

from bot_commands.utils import is_allowed

# Prefix command handlers
from bot_commands.gmail import handle_gmail
from bot_commands.todo import handle_todo, todo_group
from bot_commands.calendar import handle_calendar, cal_group
from bot_commands.rag import handle_rag
from bot_commands.portfolio import handle_portfolio
from bot_commands.saturday import handle_saturday
from services.rent.rent_service import handle_rent

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ══════════════════════════════════════════════════════════════
# SLASH COMMANDS
# ══════════════════════════════════════════════════════════════
tree = discord.app_commands.CommandTree(client)

tree.add_command(todo_group)
tree.add_command(cal_group)

# ══════════════════════════════════════════════════════════════
# EVENTS
# ══════════════════════════════════════════════════════════════
@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ {ASSISTANT_NAME} is online as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    text = message.content.strip()

    # ── RENT ──────────────────────────────────────────────────
    if text.lower().startswith(RENT_CMD):
        await handle_rent(message, text)
        return

    # ── PORTFOLIO ─────────────────────────────────────────────
    if text.lower().startswith(PORTFOLIO_CMD):
        await handle_portfolio(message, text)
        return

    # ── TODO ──────────────────────────────────────────────────
    if text.lower().startswith(TODO_CMD):
        await handle_todo(message, text)
        return

    # ── CALENDAR ──────────────────────────────────────────────
    if text.lower().startswith(CAL_CMD):
        if not is_allowed(message.author.id):
            await message.reply("❌ Unauthorized. Only the owner can access calendar commands.")
            return
        await handle_calendar(message, text)
        return

    # ── RAG ───────────────────────────────────────────────────────
    if text.lower().startswith(RAG_CMD):
        await handle_rag(message, text)
        return

    # ── GMAIL ─────────────────────────────────────────────────
    if text.lower().startswith(GMAIL_CMD):
        if not is_allowed(message.author.id):
            await message.reply("❌ Unauthorized. Only the owner can access Gmail commands.")
            return
        await handle_gmail(message, text)
        return

    # ── SATURDAY AI ───────────────────────────────────────────
    if text.lower().startswith((SATURDAY_CMD, SATURDAY_SHORT)):
        await handle_saturday(message, text)
        return

client.run(DISCORD_TOKEN)