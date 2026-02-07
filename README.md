# Discord Music & AI Bot

This is a **personal, ongoing project** built to learn and experiment with Discord bot development in Python. The bot combines basic **music playback** features with a simple **AI-powered `/ask` command** using OpenAI. The project is still actively being worked on and refined.

The code is intentionally kept straightforward and readable, focusing on learning.

---

## What it does

* Plays music from YouTube in Discord voice channels
* Supports a queue (add, remove, clear, show)
* Pause, resume, skip, join, and leave commands
* Automatically disconnects when the voice channel is empty
* `/ask` command that returns short, single-paragraph AI answers

---

## Platform

* **macOS only** (tested and developed on macOS)

---

## Running the bot (macOS)

### Requirements

Make sure the following are installed before running the bot:

* Python 3.11 or newer
* FFmpeg
* Opus
* Required Python libraries: `py-cord`, `yt-dlp`, `openai`, `pynacl`
* A Discord bot token
* An OpenAI API key

Install system dependencies using Homebrew:

```bash
brew install ffmpeg opus
```

### Setup

```bash
git clone https://github.com/ahmetunaymak/discord-bot.git
cd discord-bot
python3 -m venv venv
source venv/bin/activate
pip install py-cord yt-dlp openai pynacl
```

### Environment variables

Tokens are **not** stored in the code.

```bash
export DISCORD_TOKEN="your_discord_bot_token"
export OPENAI_API_KEY="your_openai_api_key"
```

### Start the bot

```bash
python bot.py
```

If successful, the bot will log in and register its slash commands.

---

## Notes

* This project is **not finished** and is being improved
* Designed for personal use and learning
* Keep your tokens private
