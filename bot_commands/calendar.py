import discord
from discord import app_commands
import re
from .utils import run_blocking
from services.calendar.calendar_service import (
    get_upcoming_events, get_today_events,
    add_event, delete_event, format_events
)

# Slash Commands
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

# Prefix Commands
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
