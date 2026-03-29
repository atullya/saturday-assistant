using Microsoft.EntityFrameworkCore;
using TodoApi.Data;
using TodoApi.Models;
using TodoApi.Repositories;  // ← add this

var builder = WebApplication.CreateBuilder(args);

// ── Services ──────────────────────────────────────────────────
builder.Services.AddControllers().AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.ReferenceHandler =
            System.Text.Json.Serialization.ReferenceHandler.IgnoreCycles;
    });

// ── PostgreSQL ────────────────────────────────────────────────
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(builder.Configuration
        .GetConnectionString("DefaultConnection")));

// ── Rent Repository ───────────────────────────────────────────
builder.Services.AddScoped<IRentRepository, RentRepository>();  // ← add this

var app = builder.Build();

// ── Auto migrate on startup ───────────────────────────────────
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider
                  .GetRequiredService<AppDbContext>();
    db.Database.Migrate();  // ← changed from EnsureCreated to Migrate
}

// ── Map attribute-routed controllers (for Rent API) ───────────
app.MapControllers();  // ← add this

// ── GET all todos ─────────────────────────────────────────────
app.MapGet("/api/todos", async (AppDbContext db) =>
{
    var todos = await db.Todos
        .OrderBy(t => t.IsCompleted)
        .ThenByDescending(t => t.CreatedAt)
        .ToListAsync();
    return Results.Ok(todos);
});

// ── GET single todo ───────────────────────────────────────────
app.MapGet("/api/todos/{id}", async (int id, AppDbContext db) =>
{
    var todo = await db.Todos.FindAsync(id);
    return todo is null
        ? Results.NotFound(new { message = $"Todo {id} not found" })
        : Results.Ok(todo);
});

// ── GET only pending todos ────────────────────────────────────
app.MapGet("/api/todos/pending", async (AppDbContext db) =>
{
    var todos = await db.Todos
        .Where(t => !t.IsCompleted)
        .OrderByDescending(t => t.CreatedAt)
        .ToListAsync();
    return Results.Ok(todos);
});

// ── GET only completed todos ──────────────────────────────────
app.MapGet("/api/todos/completed", async (AppDbContext db) =>
{
    var todos = await db.Todos
        .Where(t => t.IsCompleted)
        .OrderByDescending(t => t.CreatedAt)
        .ToListAsync();
    return Results.Ok(todos);
});

// ── POST create todo ──────────────────────────────────────────
app.MapPost("/api/todos", async (Todo todo, AppDbContext db) =>
{
    if (string.IsNullOrWhiteSpace(todo.Title))
        return Results.BadRequest(new { message = "Title is required" });

    todo.CreatedAt = DateTime.UtcNow;
    todo.IsCompleted = false;

    db.Todos.Add(todo);
    await db.SaveChangesAsync();

    return Results.Created($"/api/todos/{todo.Id}", todo);
});

// ── PUT update todo ───────────────────────────────────────────
app.MapPut("/api/todos/{id}", async (int id, Todo updated, AppDbContext db) =>
{
    var todo = await db.Todos.FindAsync(id);
    if (todo is null)
        return Results.NotFound(new { message = $"Todo {id} not found" });

    todo.Title = updated.Title;
    todo.Description = updated.Description;
    todo.IsCompleted = updated.IsCompleted;

    await db.SaveChangesAsync();
    return Results.Ok(todo);
});

// ── PATCH mark as done ────────────────────────────────────────
app.MapPatch("/api/todos/{id}/done", async (int id, AppDbContext db) =>
{
    var todo = await db.Todos.FindAsync(id);
    if (todo is null)
        return Results.NotFound(new { message = $"Todo {id} not found" });

    todo.IsCompleted = true;
    await db.SaveChangesAsync();
    return Results.Ok(todo);
});

// ── PATCH mark as undone ──────────────────────────────────────
app.MapPatch("/api/todos/{id}/undone", async (int id, AppDbContext db) =>
{
    var todo = await db.Todos.FindAsync(id);
    if (todo is null)
        return Results.NotFound(new { message = $"Todo {id} not found" });

    todo.IsCompleted = false;
    await db.SaveChangesAsync();
    return Results.Ok(todo);
});

// ── DELETE todo ───────────────────────────────────────────────
app.MapDelete("/api/todos/{id}", async (int id, AppDbContext db) =>
{
    var todo = await db.Todos.FindAsync(id);
    if (todo is null)
        return Results.NotFound(new { message = $"Todo {id} not found" });

    db.Todos.Remove(todo);
    await db.SaveChangesAsync();
    return Results.Ok(new { message = $"Todo {id} deleted successfully" });
});

// ── DELETE all completed ──────────────────────────────────────
app.MapDelete("/api/todos/completed", async (AppDbContext db) =>
{
    var completed = await db.Todos
        .Where(t => t.IsCompleted)
        .ToListAsync();

    db.Todos.RemoveRange(completed);
    await db.SaveChangesAsync();
    return Results.Ok(new { message = $"Deleted {completed.Count} completed todos" });
});

app.Run("http://localhost:5000");