import os
from .utils import run_blocking, is_allowed
from services.gmail.gmail_service import (
    get_inbox, get_unread, read_email, search_emails, send_email
)

async def handle_gmail(message, text):
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
