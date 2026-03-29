# Saturday: The Ultimate Automation Assistant

Saturday is a comprehensive, multi-modal Discord bot and voice assistant designed to streamline daily tasks, manage technical operations, and provide unified automation across multiple services. Built with a modular Python architecture and a robust ASP.NET Core API backend, Saturday acts as a central hub for personal and professional productivity.

## Features

### Core Assistant Capabilities
- **Advanced AI Chat**: Seamless conversational capabilities powered by local Ollama models (`!saturday` or `!s`).
- **Voice Operations**: Wake word detection ("Hey Saturday" / "Hey Jarvis"), speech-to-text via Whisper, and TTS using pyttsx3.

### Google Integration (Gmail & Calendar)
*Note: These commands are protected and restricted to the `OWNER_ID` defined in the environment.*
- **Calendar Management**: View upcoming events, check today's schedule, and create or delete events directly from Discord (`!cal` / `/cal`).
- **Gmail Operations**: Read your inbox, check unread messages, search threads, and send emails with attachments directly through Discord (`!gmail`).

###  Task & Rent Management
- **Todo System**: Full CRUD management for tasks (`!todo` / `/todo`), including a streamlined interactive modal for quick entries.
- **Rent Tracking**: Manage tenants, track bills, process payments, and calculate dues in real-time (`!rent`).

### Portfolio Monitoring
- **Live Status**: Check the uptime and status of personal and startup portfolios.
- **Interactive Q&A**: Scrape your live portfolio and ask Saturday AI queries about your projects, skills, or experience (`!portfolio`).

## Project Architecture

```text
automation/
├── services/                    # Core micro-services
│   ├── calendar/                # Google Calendar API integration
│   ├── gmail/                   # Google Gmail API operations
│   ├── rent/                    # Tenant and rent calculation logic
│   ├── todo/                    # To-Do list processing
│   └── portfolio/               # Portfolio scraping and AI QA
├── utils/                       # Shared utilities (logging, voice assistant)
├── TodoApi/                     # ASP.NET Core Entity Framework REST API
├── discord_bot.py               # Main Discord Gateway client
├── credentials.json             # Google OAuth2 App Credentials
├── token.json                   # Google OAuth2 Authorized Token
└── .env                         # Environment configuration
```

##  Setup & Deployment

### 1. Prerequisites
- Python 3.10+
- .NET 8.0+ SDK (for TodoApi)
- An active Discord Bot Token
- Google Cloud Console project with **Gmail API** and **Google Calendar API** enabled.

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
DISCORD_TOKEN=your_discord_bot_token_here
OWNER_ID=your_discord_user_id_here
```
*(The `OWNER_ID` is used to restrict sensitive commands like Gmail and Calendar to the bot owner).*

### 3. Google API Setup
1. Download your `credentials.json` from the Google Cloud Console.
2. Place it in the root directory.
3. On the first run, the script will open a local web server to authenticate your Google Account and generate `token.json` automatically.

### 4. Running the Assistant
You need to run the backend API, the Discord bot, and the voice assistant concurrently:

**Terminal 1: ASP.NET Core API**
```bash
cd TodoApi
dotnet run
```
*API endpoints will be available at `http://localhost:5000` (`/api/todos`, `/api/tenants`, `/api/bills`, `/api/payments`).*

**Terminal 2: Discord Bot**
```bash
python discord_bot.py
```

**Terminal 3: Voice Assistant**
```bash
python utils/assistant.py
```

##  Security & Privacy
- **Owner-Only Commands**: Sensitive endpoints integrating with personal Google accounts (`!gmail`, `!cal`) gracefully block unauthorized Discord users.
- **Single Instance Lock**: The Discord bot runs an internal socket lock to prevent multiple supervised processes from running simultaneously and duplicating interaction acknowledgements.
