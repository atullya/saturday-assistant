import discord
from discord import app_commands
import ollama
import os
import re
import socket
import time
import asyncio
from dotenv import load_dotenv

try:
    _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _lock_socket.bind(('127.0.0.1', 49132))
except OSError:
    print("Another instance is running. Waiting infinitely to prevent duplicate connections.")
    while True: time.sleep(3600)

from services.gmail.gmail_service import (
    get_inbox, get_unread, read_email, search_emails, send_email
)
from services.rent.rent_service import handle_rent
from services.todo.todo_service import (
    get_all_todos, get_pending_todos, get_completed_todos,
    add_todo, mark_done, mark_undone, delete_todo, clear_completed, format_todos
)
from services.portfolio.portfolio_service import (
    get_portfolio_status, get_portfolio_links,
    ask_portfolio_question, get_specific_portfolio
)
from services.calendar.calendar_service import (
    get_upcoming_events, get_today_events,
    add_event, delete_event, format_events
)

load_dotenv()

PORTFOLIOS     = ["personal", "startup"]
DISCORD_TOKEN  = os.getenv("DISCORD_TOKEN")
OLLAMA_MODEL   = "llama3.2:1b"
ASSISTANT_NAME = "Saturday"

GMAIL_CMD      = "!gmail"
TODO_CMD       = "!todo"
SATURDAY_CMD   = "!saturday"
SATURDAY_SHORT = "!s"
PORTFOLIO_CMD  = "!portfolio"
RENT_CMD       = "!rent"
CAL_CMD        = "!cal"

# ── Allowed user IDs ──────────────────────────────────────────
OWNER_ID = os.getenv("OWNER_ID")
ALLOWED_USERS = {int(OWNER_ID)} if OWNER_ID else set()

def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_USERS

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ── Helper: run blocking calls in thread ──────────────────────
async def run_blocking(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)

# ══════════════════════════════════════════════════════════════
# MODALS
# ══════════════════════════════════════════════════════════════
class TodoModal(discord.ui.Modal, title="Add Todo"):
    def __init__(self):
        super().__init__()
        self.title_input = discord.ui.TextInput(
            label="Todo title",
            style=discord.TextStyle.short,
            placeholder="Write your todo here",
            required=True,
            max_length=250
        )
        self.add_item(self.title_input)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        import traceback
        print(f"❌ Modal error: {error}")
        traceback.print_exc()
        try:
            await interaction.response.send_message(f"❌ Error: {error}", ephemeral=True)
        except:
            pass

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        title = self.children[0].value.strip()
        print(f"DEBUG modal callback triggered, title='{title}'")
        if not title:
            await interaction.followup.send("❌ Title cannot be empty", ephemeral=True)
            return
        result = await run_blocking(add_todo, title)
        print(f"DEBUG add_todo result: {result}")
        if isinstance(result, dict) and "error" in result:
            await interaction.followup.send(f"❌ API error: {result['error']}", ephemeral=True)
            return
        await interaction.followup.send(f"✅ Added! `#{result['id']}` — {result['title']}", ephemeral=True)


class TestModal(discord.ui.Modal, title="Test Modal"):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.TextInput(label="Type anything"))

    async def callback(self, interaction: discord.Interaction):
        value = self.children[0].value
        print(f"DEBUG TestModal got: '{value}'")
        await interaction.response.send_message(f"✅ Got: {value}", ephemeral=True)


class AddTodoView(discord.ui.View):
    @discord.ui.button(label="Open Todo Modal", style=discord.ButtonStyle.primary)
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TodoModal())


# ══════════════════════════════════════════════════════════════
# SLASH COMMANDS
# ══════════════════════════════════════════════════════════════
tree = discord.app_commands.CommandTree(client)

# ── Todo slash group ──────────────────────────────────────────
todo_group = discord.app_commands.Group(name="todo", description="Todo commands")

@todo_group.command(name="list")
async def todo_list(interaction: discord.Interaction):
    await interaction.response.defer()
    todos = await run_blocking(get_all_todos)
    if isinstance(todos, dict) and "error" in todos:
        await interaction.followup.send(f"❌ API error: {todos['error']}", ephemeral=True)
        return
    await interaction.followup.send(f"📋 **All Todos:**\n{format_todos(todos)}")

@todo_group.command(name="pending")
async def todo_pending(interaction: discord.Interaction):
    await interaction.response.defer()
    todos = await run_blocking(get_pending_todos)
    if isinstance(todos, dict) and "error" in todos:
        await interaction.followup.send(f"❌ API error: {todos['error']}", ephemeral=True)
        return
    await interaction.followup.send(f"⏳ **Pending Todos:**\n{format_todos(todos)}")

@todo_group.command(name="completed")
async def todo_completed(interaction: discord.Interaction):
    await interaction.response.defer()
    todos = await run_blocking(get_completed_todos)
    if isinstance(todos, dict) and "error" in todos:
        await interaction.followup.send(f"❌ API error: {todos['error']}", ephemeral=True)
        return
    await interaction.followup.send(f"✅ **Completed Todos:**\n{format_todos(todos)}")

@todo_group.command(name="add")
@app_commands.describe(title="Todo title (optional — leave blank for modal)")
async def todo_add(interaction: discord.Interaction, title: str | None = None):
    if not title or not title.strip():
        await interaction.response.send_modal(TodoModal())
        return
    await interaction.response.defer()
    try:
        result = await run_blocking(add_todo, title.strip())
        print(f"DEBUG add_todo result: {result}")
        if isinstance(result, dict) and "error" in result:
            await interaction.followup.send(f"❌ API error: {result['error']}", ephemeral=True)
            return
        await interaction.followup.send(f"✅ Added! `#{result['id']}` — {result['title']}")
    except Exception as e:
        await interaction.followup.send(f"❌ Internal error: {e}", ephemeral=True)
        raise

@todo_group.command(name="modal")
async def todo_modal(interaction: discord.Interaction):
    try:
        await interaction.response.send_modal(TodoModal())
    except Exception as e:
        await interaction.response.send_message(f"❌ Could not open modal: {e}", ephemeral=True)

@todo_group.command(name="test")
async def todo_test(interaction: discord.Interaction):
    await interaction.response.send_modal(TestModal())

@todo_group.command(name="done")
async def todo_done(interaction: discord.Interaction, todo_id: str):
    await interaction.response.defer()
    result = await run_blocking(mark_done, todo_id)
    if isinstance(result, dict) and "error" in result:
        await interaction.followup.send(f"❌ {result['error']}", ephemeral=True)
        return
    await interaction.followup.send(f"✅ Done! `#{result['id']}` — {result['title']}")

@todo_group.command(name="undone")
async def todo_undone(interaction: discord.Interaction, todo_id: str):
    await interaction.response.defer()
    result = await run_blocking(mark_undone, todo_id)
    if isinstance(result, dict) and "error" in result:
        await interaction.followup.send(f"❌ {result['error']}", ephemeral=True)
        return
    await interaction.followup.send(f"↩️ Undone! `#{result['id']}` — {result['title']}")

@todo_group.command(name="delete")
async def todo_delete(interaction: discord.Interaction, todo_id: str):
    await interaction.response.defer()
    result = await run_blocking(delete_todo, todo_id)
    if isinstance(result, dict) and "error" in result:
        await interaction.followup.send(f"❌ {result['error']}", ephemeral=True)
        return
    await interaction.followup.send(f"🗑️ {result['message']}")

@todo_group.command(name="clear")
async def todo_clear(interaction: discord.Interaction):
    await interaction.response.defer()
    result = await run_blocking(clear_completed)
    await interaction.followup.send(f"🧹 {result['message']}")

tree.add_command(todo_group)

# ── Calendar slash group ──────────────────────────────────────
cal_group = discord.app_commands.Group(name="cal", description="Calendar commands")

@cal_group.command(name="today")
async def cal_today(interaction: discord.Interaction):
    await interaction.response.defer()
    events = await run_blocking(get_today_events)
    if isinstance(events, dict) and "error" in events:
        await interaction.followup.send(f"❌ {events['error']}", ephemeral=True)
        return
    await interaction.followup.send(f"📅 **Today's Events:**\n{format_events(events)}")

@cal_group.command(name="upcoming")
async def cal_upcoming(interaction: discord.Interaction):
    await interaction.response.defer()
    events = await run_blocking(get_upcoming_events)
    if isinstance(events, dict) and "error" in events:
        await interaction.followup.send(f"❌ {events['error']}", ephemeral=True)
        return
    await interaction.followup.send(f"📅 **Upcoming Events:**\n{format_events(events)}")

@cal_group.command(name="add")
@app_commands.describe(
    title="Event title",
    date="today / tomorrow / YYYY-MM-DD",
    time="24h time e.g. 14:30 (optional)",
    duration="Duration in minutes (default 60)",
    description="Optional description"
)
async def cal_add(
    interaction: discord.Interaction,
    title: str,
    date: str,
    time: str | None = None,
    duration: int = 60,
    description: str = ""
):
    await interaction.response.defer()
    result = await run_blocking(add_event, title, date, time, duration, description)
    if isinstance(result, dict) and "error" in result:
        await interaction.followup.send(f"❌ {result['error']}", ephemeral=True)
        return
    await interaction.followup.send(
        f"✅ **{result['summary']}** created!\n🔗 {result.get('htmlLink', 'N/A')}"
    )

@cal_group.command(name="delete")
@app_commands.describe(event_id="Event ID from /cal today or /cal upcoming")
async def cal_delete(interaction: discord.Interaction, event_id: str):
    await interaction.response.defer()
    result = await run_blocking(delete_event, event_id)
    if isinstance(result, dict) and "error" in result:
        await interaction.followup.send(f"❌ {result['error']}", ephemeral=True)
        return
    await interaction.followup.send(f"🗑️ {result['message']}")

tree.add_command(cal_group)


# ══════════════════════════════════════════════════════════════
# PREFIX COMMAND HANDLERS
# ══════════════════════════════════════════════════════════════
async def handle_calendar(message, text):
    parts   = text.split(" ", 2)
    command = parts[1].lower() if len(parts) > 1 else "help"

    if command == "today":
        events = await run_blocking(get_today_events)
        await message.reply(f"📅 **Today's Events:**\n{format_events(events)}")

    elif command == "upcoming":
        events = await run_blocking(get_upcoming_events)
        await message.reply(f"📅 **Upcoming Events:**\n{format_events(events)}")

    elif command == "add":
        raw    = text[len("!cal add"):].strip()
        tokens = raw.split(" ", 2)

        if len(tokens) < 2:
            await message.reply(
                "❌ Usage:\n"
                "`!cal add today 14:30 Team Meeting`\n"
                "`!cal add tomorrow Doctor Appointment`\n"
                "`!cal add 2026-04-01 10:00 Interview`"
            )
            return

        date_str = tokens[0]

        if len(tokens) >= 3 and re.match(r'^\d{1,2}:\d{2}$', tokens[1]):
            time_str = tokens[1]
            title    = tokens[2]
        else:
            time_str = None
            title    = " ".join(tokens[1:])

        print(f"DEBUG cal add: date='{date_str}' time='{time_str}' title='{title}'")

        result = await run_blocking(add_event, title, date_str, time_str)
        if isinstance(result, dict) and "error" in result:
            await message.reply(f"❌ {result['error']}")
            return
        await message.reply(f"✅ **{result['summary']}** created!\n🔗 {result.get('htmlLink', 'N/A')}")

    elif command == "delete":
        if len(parts) < 3:
            await message.reply("❌ Usage: `!cal delete <event_id>`")
            return
        result = await run_blocking(delete_event, parts[2])
        if isinstance(result, dict) and "error" in result:
            await message.reply(f"❌ {result['error']}")
            return
        await message.reply(f"🗑️ {result['message']}")

    else:
        await message.reply(
            f"📅 **Saturday Calendar Commands:**\n\n"
            f"`!cal today`                           — today's events\n"
            f"`!cal upcoming`                        — next 5 events\n"
            f"`!cal add <date> <time> <title>`       — create event\n"
            f"`!cal delete <event_id>`               — delete event\n\n"
            f"**Examples:**\n"
            f"`!cal add today 14:30 Team Meeting`\n"
            f"`!cal add tomorrow Doctor Appointment`\n"
            f"`!cal add 2026-04-01 10:00 Interview`"
        )


async def handle_todo(message, text):
    parts   = text.split(" ", 2)
    command = parts[1].lower() if len(parts) > 1 else "help"

    if command == "list":
        todos = await run_blocking(get_all_todos)
        if isinstance(todos, dict) and "error" in todos:
            await message.reply(f"❌ API error: {todos['error']}")
            return
        await message.reply(f"📋 **All Todos:**\n{format_todos(todos)}")

    elif command == "pending":
        todos = await run_blocking(get_pending_todos)
        if isinstance(todos, dict) and "error" in todos:
            await message.reply(f"❌ API error: {todos['error']}")
            return
        await message.reply(f"⏳ **Pending Todos:**\n{format_todos(todos)}")

    elif command == "completed":
        todos = await run_blocking(get_completed_todos)
        if isinstance(todos, dict) and "error" in todos:
            await message.reply(f"❌ API error: {todos['error']}")
            return
        await message.reply(f"✅ **Completed Todos:**\n{format_todos(todos)}")

    elif command == "add":
        if len(parts) >= 3 and parts[2].strip().lower() == "modal":
            await message.reply("📝 Click the button to add a todo:", view=AddTodoView())
            return
        if len(parts) < 3 or not parts[2].strip():
            await message.reply(
                "📝 To add a todo via modal, click the button below (or use `!todo add <title>`).",
                view=AddTodoView()
            )
            return
        result = await run_blocking(add_todo, parts[2])
        if isinstance(result, dict) and "error" in result:
            await message.reply(f"❌ API error: {result['error']}")
            return
        await message.reply(f"✅ Added! `#{result['id']}` — {result['title']}")

    elif command == "done":
        if len(parts) < 3:
            await message.reply("❌ Usage: `!todo done <id>`")
            return
        result = await run_blocking(mark_done, parts[2])
        if isinstance(result, dict) and "error" in result:
            await message.reply(f"❌ {result['error']}")
            return
        await message.reply(f"✅ Done! `#{result['id']}` — {result['title']}")

    elif command == "undone":
        if len(parts) < 3:
            await message.reply("❌ Usage: `!todo undone <id>`")
            return
        result = await run_blocking(mark_undone, parts[2])
        if isinstance(result, dict) and "error" in result:
            await message.reply(f"❌ {result['error']}")
            return
        await message.reply(f"↩️ Undone! `#{result['id']}` — {result['title']}")

    elif command == "delete":
        if len(parts) < 3:
            await message.reply("❌ Usage: `!todo delete <id>`")
            return
        result = await run_blocking(delete_todo, parts[2])
        if isinstance(result, dict) and "error" in result:
            await message.reply(f"❌ {result['error']}")
            return
        await message.reply(f"🗑️ {result['message']}")

    elif command == "clear":
        result = await run_blocking(clear_completed)
        await message.reply(f"🧹 {result['message']}")

    else:
        await message.reply(
            f"📋 **Todo Commands:**\n"
            f"`!todo list` `!todo pending` `!todo completed`\n"
            f"`!todo add <title>` `!todo done <id>`\n"
            f"`!todo undone <id>` `!todo delete <id>` `!todo clear`"
        )


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
        parts   = text.split(" ", 2)
        command = parts[1].lower() if len(parts) > 1 else "help"

        if command == "status":
            await message.reply(await run_blocking(get_portfolio_status))
        elif command == "links":
            await message.reply(await run_blocking(get_portfolio_links))
        elif command == "ask":
            if len(parts) < 3:
                await message.reply("❌ Usage: `!portfolio ask <your question>`")
                return
            await message.reply("🔍 Scraping portfolio and thinking... please wait!")
            async with message.channel.typing():
                reply = await run_blocking(ask_portfolio_question, parts[2])
            await message.reply(f"🤖 **Saturday:** {reply}")
        elif command in PORTFOLIOS:
            await message.reply(await run_blocking(get_specific_portfolio, command))
        else:
            await message.reply(
                f"🌐 **Saturday Portfolio Commands:**\n\n"
                f"`{PORTFOLIO_CMD} status`              — check if sites are up\n"
                f"`{PORTFOLIO_CMD} links`               — show portfolio links\n"
                f"`{PORTFOLIO_CMD} personal`            — show personal portfolio\n"
                f"`{PORTFOLIO_CMD} startup`             — show startup portfolio\n"
                f"`{PORTFOLIO_CMD} ask <question>`      — ask anything about your portfolio\n\n"
                f"**Examples:**\n"
                f"`!portfolio ask what projects have you built`\n"
                f"`!portfolio ask what skills do you have`\n"
                f"`!portfolio ask are you available for work`"
            )
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

    # ── GMAIL ─────────────────────────────────────────────────
    if text.lower().startswith(GMAIL_CMD):
        if not is_allowed(message.author.id):
            await message.reply("❌ Unauthorized. Only the owner can access Gmail commands.")
            return
        parts   = text.split(" ", 3)
        command = parts[1].lower() if len(parts) > 1 else "help"

        if command == "inbox":
            await message.reply("📬 Fetching inbox...")
            emails = await run_blocking(get_inbox, 5)
            if not emails:
                await message.reply("📭 Inbox is empty!")
                return
            if "error" in emails[0]:
                await message.reply(f"❌ Error: {emails[0]['error']}")
                return
            lines = ["📬 **Latest 5 Emails:**\n"]
            for i, e in enumerate(emails, 1):
                unread = "🔵" if e['unread'] else "⚪"
                lines.append(f"{unread} `#{i}` **{e['subject']}**\n      From: {e['from']}\n")
            await message.reply("\n".join(lines))

        elif command == "unread":
            await message.reply("🔵 Fetching unread emails...")
            emails = await run_blocking(get_unread, 5)
            if not emails:
                await message.reply("✅ No unread emails!")
                return
            if "error" in emails[0]:
                await message.reply(f"❌ Error: {emails[0]['error']}")
                return
            lines = [f"🔵 **{len(emails)} Unread Emails:**\n"]
            for i, e in enumerate(emails, 1):
                lines.append(f"`#{i}` **{e['subject']}**\n      From: {e['from']}\n")
            await message.reply("\n".join(lines))

        elif command == "read":
            if len(parts) < 3:
                await message.reply("❌ Usage: `!gmail read <number>`")
                return
            try:
                index = int(parts[2])
            except ValueError:
                await message.reply("❌ Number must be an integer. Example: `!gmail read 1`")
                return
            await message.reply(f"📖 Reading email #{index}...")
            e = await run_blocking(read_email, index)
            if "error" in e:
                await message.reply(f"❌ Error: {e['error']}")
                return
            await message.reply(
                f"📧 **Email #{index}**\n"
                f"**From:** {e['from']}\n"
                f"**Subject:** {e['subject']}\n"
                f"**Date:** {e['date']}\n"
                f"─────────────────\n"
                f"{e['body'][:1000]}"
            )

        elif command == "search":
            if len(parts) < 3:
                await message.reply("❌ Usage: `!gmail search <keyword>`")
                return
            query = parts[2]
            await message.reply(f"🔍 Searching emails for `{query}`...")
            emails = await run_blocking(search_emails, query, 5)
            if not emails:
                await message.reply(f"📭 No emails found for `{query}`")
                return
            if "error" in emails[0]:
                await message.reply(f"❌ Error: {emails[0]['error']}")
                return
            lines = [f"🔍 **Search results for '{query}':**\n"]
            for i, e in enumerate(emails, 1):
                lines.append(f"`#{i}` **{e['subject']}**\n      From: {e['from']}\n")
            await message.reply("\n".join(lines))

        elif command == "send":
            full = message.content.strip()
            print(f"DEBUG send command: '{full}'")
            try:
                after_cmd = full[len("!gmail send"):].strip()
                if "::" not in after_cmd:
                    await message.reply(
                        "❌ Format: `!gmail send email@gmail.com Subject :: Body`\n"
                        "Example: `!gmail send friend@gmail.com Hello :: How are you?`"
                    )
                    return
                before_body, body = after_cmd.split("::", 1)
                body        = body.strip()
                before_body = before_body.strip()
                space_idx   = before_body.index(" ")
                to          = before_body[:space_idx].strip()
                subject     = before_body[space_idx:].strip()
                print(f"DEBUG to='{to}' subject='{subject}' body='{body}'")
                if "@" not in to or "." not in to:
                    await message.reply(f"❌ Invalid email address: `{to}`")
                    return
                if not subject:
                    await message.reply("❌ Subject cannot be empty")
                    return
                if not body:
                    await message.reply("❌ Body cannot be empty")
                    return
            except Exception as e:
                await message.reply(
                    f"❌ Could not parse command: {e}\n"
                    f"Format: `!gmail send email@gmail.com Subject :: Body`"
                )
                return

            attachment_path = None
            if message.attachments:
                attachment      = message.attachments[0]
                attachment_path = f"/tmp/{attachment.filename}"
                await message.reply(f"📎 Downloading `{attachment.filename}`...")
                file_data = await attachment.read()
                with open(attachment_path, "wb") as f:
                    f.write(file_data)

            await message.reply(f"📤 Sending to `{to}`...")
            result = await run_blocking(send_email, to, subject, body, attachment_path)

            if attachment_path and os.path.exists(attachment_path):
                os.remove(attachment_path)

            if result['success']:
                msg_type = "with attachment!" if attachment_path else "successfully!"
                await message.reply(f"✅ Email sent to `{to}` {msg_type}")
            else:
                await message.reply(f"❌ Failed: {result['error']}")

        else:
            await message.reply(
                f"📧 **Saturday Gmail Commands:**\n\n"
                f"`!gmail inbox`                      — latest 5 emails\n"
                f"`!gmail unread`                     — unread emails\n"
                f"`!gmail read <number>`              — read full email\n"
                f"`!gmail search <keyword>`           — search emails\n"
                f"`!gmail send email subject :: body`  — send email\n\n"
                f"**Examples:**\n"
                f"`!gmail read 1`\n"
                f"`!gmail search invoice`\n"
                f"`!gmail send friend@gmail.com Hey :: How are you?`"
            )
        return

    # ── SATURDAY AI ───────────────────────────────────────────
    if not text.lower().startswith((SATURDAY_CMD, SATURDAY_SHORT)):
        return

    if text.lower().startswith(SATURDAY_CMD):
        question = text[len(SATURDAY_CMD):].strip()
    else:
        question = text[len(SATURDAY_SHORT):].strip()

    if not question:
        await message.reply(
            f"Yes? Ask me something!\n"
            f"`!saturday what is python`\n"
            f"`!portfolio ask what projects have you built`"
        )
        return

    async with message.channel.typing():
        try:
            response = await run_blocking(
                lambda: ollama.chat(
                    model=OLLAMA_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                f"You are {ASSISTANT_NAME}, a helpful personal assistant. "
                                "Keep answers short — max 3 sentences."
                            )
                        },
                        {"role": "user", "content": question}
                    ]
                )
            )
            reply = response['message']['content']
        except Exception as e:
            reply = f"❌ Error: {e}"

    await message.reply(f"🤖 **{ASSISTANT_NAME}:** {reply}")

client.run(DISCORD_TOKEN)