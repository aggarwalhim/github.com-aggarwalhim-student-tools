"""Run this ONCE after your web app is live, to tell Telegram where to send messages.

Needs three environment variables:
  BOT_TOKEN       your token from @BotFather
  WEBHOOK_URL     https://YOURNAME.pythonanywhere.com/webhook
  WEBHOOK_SECRET  any long random text you invent (same as in your web app)
"""
import os

import telebot

token = os.environ["BOT_TOKEN"]
url = os.environ["WEBHOOK_URL"]
secret = os.environ.get("WEBHOOK_SECRET") or None

bot = telebot.TeleBot(token)
bot.remove_webhook()
ok = bot.set_webhook(url=url, secret_token=secret)
print("Webhook set:", ok)
