# Student Helper Telegram Bot

A free Telegram bot for students. It can:

- convert one image to PNG / JPG / WebP / PDF, or compress it
- turn many images into one PDF (`/topdf`)
- merge PDFs (`/merge`)
- split a PDF or extract pages (just send a PDF)
- make a QR code (`/qr`), a password (`/pass`), a percentage (`/percent`), CGPA to % (`/cgpa`) and grams for a solution (`/grams`)

Files up to 20 MB (Telegram's limit for bots). Files are processed in memory and not stored.

## IMPORTANT: keep your token secret

The bot token is like a password. **Never** paste it into a file in this repo and never post it publicly.
If it leaks, open @BotFather → `/revoke` to get a new one.

---

## Step 1 — Create the bot (2 minutes)

1. Open Telegram and search for **@BotFather** (the one with the blue tick).
2. Send `/newbot`.
3. Give it a name (e.g. `Student Helper`) and a username that ends in `bot` (e.g. `my_student_helper_bot`).
4. BotFather replies with a **token** (looks like `123456789:AA...`). Copy it and keep it private.

## Step 2 — Try it first (optional, on a computer)

You need Python 3.9+ on a computer.

```bash
cd telegram-bot
pip install -r requirements.txt
# Linux / Mac:
BOT_TOKEN="paste-your-token" python bot.py
# Windows (Command Prompt):
set BOT_TOKEN=paste-your-token
python bot.py
```

Open your bot in Telegram and send `/start`. It works while this window stays open.

## Step 3 — Keep it running for free (PythonAnywhere)

This uses a "webhook": Telegram sends each message to your small web app. These steps are written from how PythonAnywhere's free plan worked when this was written. If a screen looks different, follow their on-screen help.

1. Create a free **Beginner** account at pythonanywhere.com. Remember your username.
2. Open a **Bash console** (Consoles tab) and run:
   ```bash
   git clone https://github.com/aggarwalhim/github.com-aggarwalhim-student-tools.git
   cd github.com-aggarwalhim-student-tools/telegram-bot
   pip install --user -r requirements.txt
   ```
3. Go to the **Web** tab → **Add a new web app** → **Manual configuration** → choose a Python version (3.10 or newer).
4. On the Web tab, open the **WSGI configuration file**, delete everything in it, and paste this (change `YOURUSERNAME`, the token and the secret):
   ```python
   import sys, os
   path = '/home/YOURUSERNAME/github.com-aggarwalhim-student-tools/telegram-bot'
   if path not in sys.path:
       sys.path.insert(0, path)

   os.environ['BOT_TOKEN'] = 'HTTP API:
9064162198:AAEwvFpPwondJWb-2Yi3FvbnFlQ9erbSUTk'
   os.environ['WEBHOOK_SECRET'] = 'any-long-random-text-you-invent'

   from bot import app as application
   ```
   This file is on PythonAnywhere only — it is **not** part of GitHub, so your token stays private.
5. Click the green **Reload** button on the Web tab. Open `https://YOURUSERNAME.pythonanywhere.com/` — you should see "Student bot is running."
6. Back in the Bash console, tell Telegram where your bot lives:
   ```bash
   cd ~/github.com-aggarwalhim-student-tools/telegram-bot
   BOT_TOKEN="HTTP API:
9064162198:AAEwvFpPwondJWb-2Yi3FvbnFlQ9erbSUTk" \
   WEBHOOK_SECRET="the-same-random-text" \
   WEBHOOK_URL="https://YOURUSERNAME.pythonanywhere.com/webhook" \
   python set_webhook.py
   ```
   It should print `Webhook set: True`.
7. Send `/start` to your bot in Telegram.

### Free-plan notes (please check on PythonAnywhere's site)

- Free accounts usually have to press an "extend / run until" button on the Web tab every so often, or the app is switched off.
- Free accounts can only reach certain websites. Telegram's API is normally on that list, but check their "allowlist" help page if the bot does not reply.
- Free accounts have limited CPU time. Very large PDFs may fail.

## Commands

| Command | What it does |
|---|---|
| send an image | choose PNG / JPG / WebP / PDF / Compress |
| `/topdf` then images, then `/done` | many images → one PDF |
| `/merge` then PDFs, then `/done` | many PDFs → one PDF |
| send a PDF | reply `1-3,5` for those pages, or `all` for one PDF per page |
| `/qr text` | QR code image |
| `/pass 14` | random password |
| `/percent 450 600` | percentage |
| `/cgpa 8.2` | percentage (× 9.5; or `/cgpa 8.2 9.25`) |
| `/grams 58.44 0.1 500` | grams to weigh (mol. weight, molarity, mL) |
| `/cancel` | stop the current task |

## Files

- `bot.py` — the Telegram bot and web app
- `converters.py` — the conversion and calculator code (no Telegram inside)
- `set_webhook.py` — run once to connect Telegram to your web app
- `requirements.txt` — libraries to install
