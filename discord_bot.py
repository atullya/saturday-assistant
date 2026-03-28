import discord
import ollama
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from gmail_service import (
    get_inbox,
    get_unread,
    read_email,
    search_emails,
    send_email
)
load_dotenv()

DISCORD_TOKEN   = os.getenv("DISCORD_TOKEN")
OLLAMA_MODEL    = "llama3.2:1b"
ASSISTANT_NAME  = "Saturday"
API_BASE        = "http://localhost:5000/api/todos"

# ── Command prefixes ──────────────────────────────────────────
GMAIL_CMD = "!gmail"
TODO_CMD        = "!todo"
SATURDAY_CMD    = "!saturday"
SATURDAY_SHORT  = "!s"
PORTFOLIO_CMD   = "!portfolio"

# ── Portfolio links ───────────────────────────────────────────
PORTFOLIOS = {
    "personal"  : "https://portfolio.atullyamaharjan.com.np/",
    "startup"   : "https://portfolio-startup.onrender.com/",
}

# ── Scrape portfolio text ─────────────────────────────────────
def scrape_portfolio(url):
    try:
        res  = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)

        # keep it under 3000 chars so Ollama doesn't choke
        return text[:3000]
    except Exception as e:
        return f"Error scraping: {e}"

# ── Check if site is up ───────────────────────────────────────
def check_site_status(url):
    try:
        res = requests.get(url, timeout=10)
        return {
            "up"      : True,
            "status"  : res.status_code,
            "time_ms" : int(res.elapsed.total_seconds() * 1000)
        }
    except requests.exceptions.ConnectionError:
        return {"up": False, "status": "unreachable", "time_ms": 0}
    except requests.exceptions.Timeout:
        return {"up": False, "status": "timeout",     "time_ms": 0}
    except Exception as e:
        return {"up": False, "status": str(e),        "time_ms": 0}

# ── Ask Ollama about portfolio content ────────────────────────
def ask_about_portfolio(content, question):
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Saturday, a personal assistant. "
                        "Answer questions based ONLY on the portfolio content provided. "
                        "Keep answers short — 2 to 3 sentences. "
                        "If the answer is not in the content, say 'I could not find that in the portfolio.'"
                    )
                },
                {
                    "role": "user",
                    "content": f"Portfolio content:\n{content}\n\nQuestion: {question}"
                }
            ]
        )
        return response['message']['content']
    except Exception as e:
        return f"❌ Ollama error: {e}"

# ── Helper: todo API calls ────────────────────────────────────
def api_get(url):
    try:
        return requests.get(url).json()
    except Exception as e:
        return {"error": str(e)}

def api_post(url, data):
    try:
        return requests.post(url, json=data).json()
    except Exception as e:
        return {"error": str(e)}

def api_patch(url):
    try:
        return requests.patch(url).json()
    except Exception as e:
        return {"error": str(e)}

def api_delete(url):
    try:
        return requests.delete(url).json()
    except Exception as e:
        return {"error": str(e)}

# ── Format todos ──────────────────────────────────────────────
def format_todos(todos):
    if not todos:
        return "📭 No todos found!"
    lines = []
    for t in todos:
        status = "✅" if t["isCompleted"] else "⏳"
        desc   = f" — {t['description']}" if t.get("description") else ""
        lines.append(f"{status} `#{t['id']}` {t['title']}{desc}")
    return "\n".join(lines)

# ── On ready ──────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
@client.event
async def on_ready():
    print(f"✅ {ASSISTANT_NAME} is online as {client.user}")


# ── On message ────────────────────────────────────────────────
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    text = message.content.strip()

    # ══════════════════════════════════════════════════════════
    # PORTFOLIO COMMANDS
    # ══════════════════════════════════════════════════════════
    if text.lower().startswith(PORTFOLIO_CMD):
        parts   = text.split(" ", 2)
        command = parts[1].lower() if len(parts) > 1 else "help"

        # !portfolio status
        if command == "status":
            lines = ["🌐 **Portfolio Status:**\n"]
            for name, url in PORTFOLIOS.items():
                s = check_site_status(url)
                if s["up"]:
                    lines.append(f"✅ **{name}** — UP `{s['time_ms']}ms`\n🔗 {url}")
                else:
                    lines.append(f"❌ **{name}** — DOWN `{s['status']}`\n🔗 {url}")
            await message.reply("\n".join(lines))

        # !portfolio links
        elif command == "links":
            lines = ["🔗 **My Portfolios:**\n"]
            for name, url in PORTFOLIOS.items():
                lines.append(f"**{name.capitalize()}** → {url}")
            await message.reply("\n".join(lines))

        # !portfolio ask what projects have you built
        elif command == "ask":
            if len(parts) < 3:
                await message.reply("❌ Usage: `!portfolio ask <your question>`")
                return

            question = parts[2]
            await message.reply("🔍 Scraping portfolio and thinking... please wait!")

            async with message.channel.typing():
                # scrape both portfolios and combine
                combined_content = ""
                for name, url in PORTFOLIOS.items():
                    content = scrape_portfolio(url)
                    combined_content += f"\n\n--- {name} portfolio ---\n{content}"

                reply = ask_about_portfolio(combined_content, question)

            await message.reply(f"🤖 **Saturday:** {reply}")

        # !portfolio personal  or  !portfolio startup
        elif command in PORTFOLIOS:
            url = PORTFOLIOS[command]
            s   = check_site_status(url)
            status_text = f"✅ UP `{s['time_ms']}ms`" if s["up"] else f"❌ DOWN"
            await message.reply(
                f"🔗 **{command.capitalize()} Portfolio**\n"
                f"{url}\n"
                f"Status: {status_text}"
            )

        # !portfolio help
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

    # ══════════════════════════════════════════════════════════
    # TODO COMMANDS
    # ══════════════════════════════════════════════════════════
    if text.lower().startswith(TODO_CMD):
        parts   = text.split(" ", 2)
        command = parts[1].lower() if len(parts) > 1 else "help"

        if command == "list":
            todos = api_get(API_BASE)
            if "error" in todos:
                await message.reply(f"❌ API error: {todos['error']}")
                return
            await message.reply(f"📋 **All Todos:**\n{format_todos(todos)}")

        elif command == "pending":
            todos = api_get(f"{API_BASE}/pending")
            if "error" in todos:
                await message.reply(f"❌ API error: {todos['error']}")
                return
            await message.reply(f"⏳ **Pending Todos:**\n{format_todos(todos)}")

        elif command == "completed":
            todos = api_get(f"{API_BASE}/completed")
            if "error" in todos:
                await message.reply(f"❌ API error: {todos['error']}")
                return
            await message.reply(f"✅ **Completed Todos:**\n{format_todos(todos)}")

        elif command == "add":
            if len(parts) < 3:
                await message.reply("❌ Usage: `!todo add your task title`")
                return
            result = api_post(API_BASE, {"title": parts[2]})
            if "error" in result:
                await message.reply(f"❌ API error: {result['error']}")
                return
            await message.reply(f"✅ Added! `#{result['id']}` — {result['title']}")

        elif command == "done":
            if len(parts) < 3:
                await message.reply("❌ Usage: `!todo done <id>`")
                return
            try:
                result = api_patch(f"{API_BASE}/{int(parts[2])}/done")
                await message.reply(f"✅ Done! `#{result['id']}` — {result['title']}")
            except ValueError:
                await message.reply("❌ ID must be a number.")

        elif command == "undone":
            if len(parts) < 3:
                await message.reply("❌ Usage: `!todo undone <id>`")
                return
            try:
                result = api_patch(f"{API_BASE}/{int(parts[2])}/undone")
                await message.reply(f"↩️ Undone! `#{result['id']}` — {result['title']}")
            except ValueError:
                await message.reply("❌ ID must be a number.")

        elif command == "delete":
            if len(parts) < 3:
                await message.reply("❌ Usage: `!todo delete <id>`")
                return
            try:
                result = api_delete(f"{API_BASE}/{int(parts[2])}")
                await message.reply(f"🗑️ {result['message']}")
            except ValueError:
                await message.reply("❌ ID must be a number.")

        elif command == "clear":
            result = api_delete(f"{API_BASE}/completed")
            await message.reply(f"🧹 {result['message']}")

        else:
            await message.reply(
                f"📋 **Todo Commands:**\n"
                f"`!todo list` `!todo pending` `!todo completed`\n"
                f"`!todo add <title>` `!todo done <id>`\n"
                f"`!todo undone <id>` `!todo delete <id>` `!todo clear`"
            )
        return


        # ══════════════════════════════════════════════════════════
    # GMAIL COMMANDS
    # ══════════════════════════════════════════════════════════
    if text.lower().startswith(GMAIL_CMD):
        parts   = text.split(" ", 3)
        command = parts[1].lower() if len(parts) > 1 else "help"

        # !gmail inbox
        if command == "inbox":
            await message.reply("📬 Fetching inbox...")
            emails = get_inbox(5)
            if not emails:
                await message.reply("📭 Inbox is empty!")
                return
            if "error" in emails[0]:
                await message.reply(f"❌ Error: {emails[0]['error']}")
                return
            lines = ["📬 **Latest 5 Emails:**\n"]
            for i, e in enumerate(emails, 1):
                unread = "🔵" if e['unread'] else "⚪"
                lines.append(
                    f"{unread} `#{i}` **{e['subject']}**\n"
                    f"      From: {e['from']}\n"
                )
            await message.reply("\n".join(lines))

        # !gmail unread
        elif command == "unread":
            await message.reply("🔵 Fetching unread emails...")
            emails = get_unread(5)
            if not emails:
                await message.reply("✅ No unread emails!")
                return
            if "error" in emails[0]:
                await message.reply(f"❌ Error: {emails[0]['error']}")
                return
            lines = [f"🔵 **{len(emails)} Unread Emails:**\n"]
            for i, e in enumerate(emails, 1):
                lines.append(
                    f"`#{i}` **{e['subject']}**\n"
                    f"      From: {e['from']}\n"
                )
            await message.reply("\n".join(lines))

        # !gmail read 1
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
            e = read_email(index)
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

        # !gmail search python
        elif command == "search":
            if len(parts) < 3:
                await message.reply("❌ Usage: `!gmail search <keyword>`")
                return
            query  = parts[2]
            await message.reply(f"🔍 Searching emails for `{query}`...")
            emails = search_emails(query, 5)
            if not emails:
                await message.reply(f"📭 No emails found for `{query}`")
                return
            if "error" in emails[0]:
                await message.reply(f"❌ Error: {emails[0]['error']}")
                return
            lines = [f"🔍 **Search results for '{query}':**\n"]
            for i, e in enumerate(emails, 1):
                lines.append(
                    f"`#{i}` **{e['subject']}**\n"
                    f"      From: {e['from']}\n"
                )
            await message.reply("\n".join(lines))

        # !gmail send to@gmail.com Subject :: Body
        elif command == "send":
            # format: !gmail send to@email.com Subject here :: Body here
            if len(parts) < 3:
                await message.reply(
                    "❌ Usage: `!gmail send to@email.com Subject :: Body`\n"
                    "Example: `!gmail send friend@gmail.com Hello there :: Hey how are you?`"
                )
                return
            rest = text[len(GMAIL_CMD) + len(" send "):].strip()
            if "::" not in rest:
                await message.reply(
                    "❌ Separate subject and body with `::`\n"
                    "Example: `!gmail send friend@gmail.com Hello :: How are you?`"
                )
                return
            # parse:  to@email.com Subject :: Body
            to_and_subject, body = rest.split("::", 1)
            to_parts = to_and_subject.strip().split(" ", 1)
            if len(to_parts) < 2:
                await message.reply("❌ Format: `!gmail send email@gmail.com Subject :: Body`")
                return
            to      = to_parts[0].strip()
            subject = to_parts[1].strip()
            body    = body.strip()

            await message.reply(f"📤 Sending email to `{to}`...")
            result = send_email(to, subject, body)
            if result['success']:
                await message.reply(f"✅ Email sent to `{to}`!")
            else:
                await message.reply(f"❌ Failed: {result['error']}")

        # !gmail help
        else:
            await message.reply(
                f"📧 **Saturday Gmail Commands:**\n\n"
                f"`!gmail inbox`                    — latest 5 emails\n"
                f"`!gmail unread`                   — unread emails\n"
                f"`!gmail read <number>`             — read full email\n"
                f"`!gmail search <keyword>`          — search emails\n"
                f"`!gmail send email subject :: body` — send email\n\n"
                f"**Examples:**\n"
                f"`!gmail read 1`\n"
                f"`!gmail search invoice`\n"
                f"`!gmail send friend@gmail.com Hey :: How are you?`"
            )
        return

    # ══════════════════════════════════════════════════════════
    # SATURDAY AI COMMANDS
    # ══════════════════════════════════════════════════════════
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
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are {ASSISTANT_NAME}, a helpful personal assistant. "
                            "Keep answers short — max 3 sentences."
                        )
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            )
            reply = response['message']['content']
        except Exception as e:
            reply = f"❌ Error: {e}"

    await message.reply(f"🤖 **{ASSISTANT_NAME}:** {reply}")

client.run(DISCORD_TOKEN)