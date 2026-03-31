import discord
from discord import app_commands
from .utils import run_blocking
from services.todo.todo_service import (
    get_all_todos, get_pending_todos, get_completed_todos,
    add_todo, mark_done, mark_undone, delete_todo, clear_completed, format_todos
)

# Modals
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


# Slash commands
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


# Prefix Command Handlers
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
