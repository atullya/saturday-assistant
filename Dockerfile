FROM python:3.12-slim

# Install system dependencies
# gcc, build-essential and portaudio19-dev are required for PyAudio and sounddevice
# ffmpeg is used for audio processing (whisper/discord)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    build-essential \
    portaudio19-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependencies list and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the remaining project files
COPY . .

# Run the discord bot
CMD ["python", "discord_bot.py"]