import os
from .utils import run_blocking
from services.rag.rag_service import (  add_text_file, add_pdf, ask as rag_ask,
    list_documents, delete_document
)

async def handle_rag(message, text):
    parts   = text.split(" ", 2)
    command = parts[1].lower() if len(parts) > 1 else "help"

    if command == "ask":
        if len(parts) < 3:
            await message.reply("❌ Usage: `!rag ask <question>`")
            return
        question = parts[2]
        await message.reply("🔍 Searching your documents...")
        async with message.channel.typing():
            answer = await run_blocking(rag_ask, question)
        await message.reply(f"🤖 **Saturday:** {answer}")

    elif command == "add":
        if not message.attachments:
            await message.reply(
                "❌ Attach a `.txt` or `.pdf` file with the command.\n"
                "Example: attach your CV.pdf and type `!rag add`"
            )
            return
        attachment = message.attachments[0]
        filename   = attachment.filename
        tmp_path   = f"/tmp/{filename}"
        file_data  = await attachment.read()
        with open(tmp_path, "wb") as f:
            f.write(file_data)

        await message.reply(f"📄 Processing `{filename}`...")
        async with message.channel.typing():
            if filename.lower().endswith(".pdf"):
                result = await run_blocking(add_pdf, tmp_path)
            elif filename.lower().endswith(".txt"):
                result = await run_blocking(add_text_file, tmp_path)
            else:
                await message.reply("❌ Only `.txt` and `.pdf` supported.")
                os.remove(tmp_path)
                return

        os.remove(tmp_path)

        if isinstance(result, dict) and "error" in result:
            await message.reply(f"❌ {result['error']}")
            return
        await message.reply(f"✅ `{filename}` indexed! {result} chunks stored.")

    elif command == "list":
        docs = await run_blocking(list_documents)
        if not docs:
            await message.reply("📭 No documents indexed yet.")
            return
        doc_list = "\n".join([f"• `{d}`" for d in docs])
        await message.reply(f"📚 **Indexed Documents:**\n{doc_list}")

    elif command == "delete":
        if len(parts) < 3:
            await message.reply("❌ Usage: `!rag delete <filename>`")
            return
        deleted = await run_blocking(delete_document, parts[2])
        if deleted:
            await message.reply(f"🗑️ Deleted `{parts[2]}` from index.")
        else:
            await message.reply(f"❌ `{parts[2]}` not found. Use `!rag list` to see documents.")

    else:
        await message.reply(
            f"🧠 **Saturday RAG Commands:**\n\n"
            f"`!rag add`              — attach .txt or .pdf to index\n"
            f"`!rag ask <question>`   — ask from your documents\n"
            f"`!rag list`             — show indexed documents\n"
            f"`!rag delete <name>`    — remove a document\n\n"
            f"**CV Examples:**\n"
            f"`!rag ask what are his skills`\n"
            f"`!rag ask what projects has he built`\n"
            f"`!rag ask what is his work experience`\n"
            f"`!rag ask is he available for work`"
        )
