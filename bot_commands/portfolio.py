from .utils import run_blocking
from services.portfolio.portfolio_service import (
    get_portfolio_status, get_portfolio_links,
    ask_portfolio_question, get_specific_portfolio
)

PORTFOLIOS = ["personal", "startup"]
PORTFOLIO_CMD = "!portfolio"

async def handle_portfolio(message, text):
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
