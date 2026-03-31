import ollama
from .utils import run_blocking

OLLAMA_MODEL   = "llama3.2:1b"
ASSISTANT_NAME = "Saturday"
SATURDAY_CMD   = "!saturday"
SATURDAY_SHORT = "!s"

async def handle_saturday(message, text):
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
