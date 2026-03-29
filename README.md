# Automation Project

This project contains a Discord bot with various automation features, including Gmail integration, todo management, rent tracking, portfolio monitoring, and AI chat capabilities.

## Project Structure

```
automation/
├── services/                    # Modular services for different features
│   ├── gmail/
│   │   ├── __init__.py
│   │   └── gmail_service.py     # Gmail API integration
│   ├── rent/
│   │   ├── __init__.py
│   │   └── rent_service.py      # Rent management commands
│   ├── todo/
│   │   ├── __init__.py
│   │   └── todo_service.py      # Todo API interactions
│   └── portfolio/
│       ├── __init__.py
│       └── portfolio_service.py # Portfolio scraping and analysis
├── utils/                       # Utility scripts
│   └── assistant.py              # Voice assistant using Whisper and Ollama
├── TodoApi/                     # ASP.NET Core API for todo and rent management
├── discord_bot.py               # Main Discord bot
├── credentials.json             # Gmail API credentials
├── token.json                   # Gmail API token
└── README.md
```

## Features

### Discord Bot Commands

- `!gmail` - Gmail operations (inbox, unread, read, search, send)
- `!todo` - Todo management (list, add, done, delete, etc.)
- `!rent` - Rent tracking (tenants, bills, payments, dues)
- `!portfolio` - Portfolio monitoring (status, links, ask questions)
- `!saturday` or `!s` - AI chat using Ollama

### Voice Assistant

- Wake word detection ("Hey Saturday" or "Hey Jarvis")
- Speech-to-text using Whisper
- AI responses using Ollama
- Text-to-speech using pyttsx3

### TodoApi

- REST API for managing todos, tenants, bills, and payments
- Built with ASP.NET Core and Entity Framework

## Setup

1. Install dependencies for Python and .NET
2. Set up Gmail API credentials
3. Configure environment variables (DISCORD_TOKEN, etc.)
4. Run the TodoApi: `dotnet run` in TodoApi directory
5. Run the Discord bot: `python discord_bot.py`
6. Run the voice assistant: `python utils/assistant.py`

## Environment Variables

Create a `.env` file with:

```
DISCORD_TOKEN=your_discord_bot_token
```

## Gmail Setup

1. Enable Gmail API in Google Cloud Console
2. Download credentials.json
3. First run will prompt for authentication

## API Endpoints

The TodoApi runs on `http://localhost:5000` with endpoints for:

- `/api/todos` - Todo management
- `/api/tenants` - Tenant management
- `/api/bills` - Bill management
- `/api/payments` - Payment tracking
