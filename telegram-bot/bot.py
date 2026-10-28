"""Student helper Telegram bot: file converter + small calculators.

Two ways to run it:
  1. On your own computer / phone (testing):   BOT_TOKEN=xxx python bot.py
  2. On a free web host with a webhook (always on): see README.md

NEVER write your bot token inside this file or commit it to GitHub.
"""
import io
import logging
import os

import telebot
from telebot import types
from flask import Flask, abort, request

import converters as cv

TOKEN = os.environ.get("BOT_TOKEN")
SECRET = os.environ.get("WEBHOOK_SECRET", "")
if not TOKEN:
    raise SystemExit("Please set the BOT_TOKEN environment variable (see README.md).")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("studentbot")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

MAX_ITEMS = 20            # images / PDFs collected in one session
MAX_FILE_BYTES = 20 * 1024 * 1024   # Telegram bots can download up to 20 MB

# Simple in-memory state (forgotten when the bot restarts - that is fine).
sessions = {}     # chat_id -> {"mode": ..., "items": [file_id, ...], "pdf": bytes}
last_image = {}   # chat_id -> file_id of the last single image sent

HELP = (
    "Hi! I am a student helper bot.\n\n"
    "FILES\n"
    "• Send me one image → choose PNG / JPG / WebP / PDF / Compress\n"
    "• /topdf → send many images, then /done → one PDF\n"
    "• /merge → send many PDFs, then /done → one PDF\n"
    "• Send me a PDF → I will split it or extract pages\n"
    "• /cancel → stop what I was doing\n\n"
    "TOOLS\n"
    "• /qr your text or link\n"
    "• /pass 14 → password (length 8-64)\n"
    "• /percent 450 600 → percentage\n"
    "• /cgpa 8.2 → percentage (x9.5; or /cgpa 8.2 9.25)\n"
    "• /grams 58.44 0.1 500 → grams needed (mol. weight, molarity, mL)\n\n"
    "Tip: send photos as a FILE (paperclip → File) to keep full quality.\n"
    "Files up to 20 MB. Your files are processed and not stored."
)


# ------------------------------------------------------------- helpers
def send_bytes(chat_id, data, filename, caption=None):
    bio = io.BytesIO(data)
    bio.name = filename
    bot.send_document(chat_id, bio, caption=caption)


def download(file_id):
    info = bot.get_file(file_id)
    if info.file_size and info.file_size > MAX_FILE_BYTES:
        raise cv.UserError("That file is bigger than 20 MB. Please send a smaller one.")
    return bot.download_file(info.file_path)


def safe(handler):
    """Show friendly errors to the user and log real bugs."""
    def wrapper(obj, *a, **k):
        chat_id = obj.message.chat.id if hasattr(obj, "message") and obj.message else obj.chat.id
        try:
            return handler(obj, *a, **k)
        except cv.UserError as e:
            bot.send_message(chat_id, str(e))
        except Exception:
            log.exception("Unexpected error")
            bot.send_message(chat_id, "Sorry, something went wrong. Please try again.")
    wrapper.__name__ = handler.__name__
    return wrapper


def args_of(message):
    parts = (message.text or "").split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ""


def numbers(text, count):
    try:
        vals = [float(x) for x in text.split()]
    except ValueError:
        raise cv.UserError("Please type numbers only, separated by spaces.")
    if len(vals) < count:
        raise cv.UserError("I need %d numbers. Send /help to see examples." % count)
    return vals


def nice(x):
    return ("%.4f" % x).rstrip("0").rstrip(".")


# ------------------------------------------------------------ commands
@bot.message_handler(commands=["start", "help"])
def cmd_help(message):
    bot.send_message(message.chat.id, HELP)


@bot.message_handler(commands=["cancel"])
def cmd_cancel(message):
    sessions.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "Cancelled. Send /help to see what I can do.")


@bot.message_handler(commands=["topdf"])
def cmd_topdf(message):
    sessions[message.chat.id] = {"mode": "pdf", "items": []}
    bot.send_message(message.chat.id, "Send me the images in order (up to %d). When finished, send /done." % MAX_ITEMS)


@bot.message_handler(commands=["merge"])
def cmd_merge(message):
    sessions[message.chat.id] = {"mode": "merge", "items": []}
    bot.send_message(message.chat.id, "Send me the PDFs in order (up to %d). When finished, send /done." % MAX_ITEMS)


@bot.message_handler(commands=["done"])
@safe
def cmd_done(message):
    cid = message.chat.id
    s = sessions.get(cid)
    if not s or s["mode"] not in ("pdf", "merge"):
        bot.send_message(cid, "Nothing to finish. Send /topdf or /merge first.")
        return
    if not s["items"]:
        bot.send_message(cid, "You have not sent any files yet.")
        return
    bot.send_chat_action(cid, "upload_document")
    files = [download(f) for f in s["items"]]
    if s["mode"] == "pdf":
        data, name = cv.images_to_pdf(files), "images.pdf"
    else:
        data, name = cv.merge_pdfs(files), "merged.pdf"
    sessions.pop(cid, None)
    send_bytes(cid, data, name, "Done! %d file(s) combined." % len(files))


@bot.message_handler(commands=["qr"])
@safe
def cmd_qr(message):
    text = args_of(message)
    if not text:
        bot.send_message(message.chat.id, "Usage: /qr https://example.com")
        return
    data = cv.make_qr(text)
    bio = io.BytesIO(data)
    bio.name = "qr.png"
    bot.send_photo(message.chat.id, bio)


@bot.message_handler(commands=["pass"])
@safe
def cmd_pass(message):
    arg = args_of(message)
    length = int(arg) if arg.isdigit() else 14
    bot.send_message(message.chat.id, "`%s`" % cv.make_password(length), parse_mode="Markdown")


@bot.message_handler(commands=["percent"])
@safe
def cmd_percent(message):
    a, b = numbers(args_of(message), 2)[:2]
    bot.send_message(message.chat.id, "Percentage: %s%%" % nice(cv.percent(a, b)))


@bot.message_handler(commands=["cgpa"])
@safe
def cmd_cgpa(message):
    vals = numbers(args_of(message), 1)
    mult = vals[1] if len(vals) > 1 else 9.5
    bot.send_message(message.chat.id, "Percentage: %s%% (CGPA x %s). Your university may use a different formula." % (nice(cv.cgpa_to_percent(vals[0], mult)), nice(mult)))


@bot.message_handler(commands=["grams"])
@safe
def cmd_grams(message):
    mw, m, ml = numbers(args_of(message), 3)[:3]
    bot.send_message(message.chat.id, "Weigh %s g for %s mL of %s M solution." % (nice(cv.grams_needed(mw, m, ml)), nice(ml), nice(m)))


# --------------------------------------------------------------- files
def image_menu(chat_id):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("PNG", callback_data="img:png"),
        types.InlineKeyboardButton("JPG", callback_data="img:jpg"),
        types.InlineKeyboardButton("WebP", callback_data="img:webp"),
        types.InlineKeyboardButton("PDF", callback_data="img:pdf"),
        types.InlineKeyboardButton("Compress", callback_data="img:small"),
    )
    bot.send_message(chat_id, "What should I do with this image?", reply_markup=kb)


def got_image(message, file_id):
    cid = message.chat.id
    s = sessions.get(cid)
    if s and s["mode"] == "pdf":
        if len(s["items"]) >= MAX_ITEMS:
            bot.send_message(cid, "That is the maximum. Send /done now.")
            return
        s["items"].append(file_id)
        bot.send_message(cid, "Got image %d. Send more, or /done to make the PDF." % len(s["items"]))
        return
    last_image[cid] = file_id
    image_menu(cid)


@bot.message_handler(content_types=["photo"])
@safe
def on_photo(message):
    got_image(message, message.photo[-1].file_id)


@bot.message_handler(content_types=["document"])
@safe
def on_document(message):
    cid = message.chat.id
    doc = message.document
    mime = (doc.mime_type or "").lower()
    name = (doc.file_name or "").lower()
    if mime.startswith("image/"):
        got_image(message, doc.file_id)
    elif mime == "application/pdf" or name.endswith(".pdf"):
        got_pdf(message, doc.file_id)
    else:
        bot.send_message(cid, "I can work with images and PDFs. Send /help to see what I can do.")


def got_pdf(message, file_id):
    cid = message.chat.id
    s = sessions.get(cid)
    if s and s["mode"] == "merge":
        if len(s["items"]) >= MAX_ITEMS:
            bot.send_message(cid, "That is the maximum. Send /done now.")
            return
        s["items"].append(file_id)
        bot.send_message(cid, "Got PDF %d. Send more, or /done to merge." % len(s["items"]))
        return
    data = download(file_id)
    n = cv.page_count(data)
    sessions[cid] = {"mode": "split", "pdf": data, "pages": n}
    bot.send_message(cid, "This PDF has %d page(s).\nReply with the pages to extract, like 1-3,5\nor type all to get every page as a separate PDF (up to 30 pages).\nSend /cancel to stop." % n)


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("img:"))
@safe
def on_image_choice(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    file_id = last_image.get(cid)
    if not file_id:
        bot.send_message(cid, "Please send the image again.")
        return
    bot.send_chat_action(cid, "upload_document")
    data = download(file_id)
    choice = call.data.split(":", 1)[1]
    if choice == "png":
        send_bytes(cid, cv.convert_image(data, "PNG"), "image.png")
    elif choice == "jpg":
        send_bytes(cid, cv.convert_image(data, "JPEG"), "image.jpg")
    elif choice == "webp":
        send_bytes(cid, cv.convert_image(data, "WEBP"), "image.webp")
    elif choice == "pdf":
        send_bytes(cid, cv.images_to_pdf([data]), "image.pdf")
    elif choice == "small":
        small = cv.compress_image(data)
        send_bytes(cid, small, "compressed.jpg", "%d KB → %d KB" % (len(data) // 1024, len(small) // 1024))


@bot.message_handler(content_types=["text"])
@safe
def on_text(message):
    cid = message.chat.id
    s = sessions.get(cid)
    if s and s["mode"] == "split":
        text = message.text.strip().lower()
        bot.send_chat_action(cid, "upload_document")
        if text == "all":
            if s["pages"] > 30:
                raise cv.UserError("That PDF has more than 30 pages. Please give page numbers like 1-3,5")
            for i in range(s["pages"]):
                send_bytes(cid, cv.extract_pages(s["pdf"], [i]), "page-%d.pdf" % (i + 1))
        else:
            idx = cv.parse_ranges(text, s["pages"])
            send_bytes(cid, cv.extract_pages(s["pdf"], idx), "pages.pdf", "%d page(s) extracted." % len(idx))
        sessions.pop(cid, None)
        return
    bot.send_message(cid, "Send /help to see what I can do.")


# ------------------------------------------------------- web (webhook)
@app.route("/", methods=["GET"])
def index():
    return "Student bot is running."


@app.route("/webhook", methods=["POST"])
def webhook():
    if SECRET and request.headers.get("X-Telegram-Bot-Api-Secret-Token") != SECRET:
        abort(403)
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "ok"


if __name__ == "__main__":
    # Local testing mode: the bot asks Telegram for new messages.
    bot.remove_webhook()
    print("Bot is running. Press Ctrl+C to stop.")
    bot.infinity_polling()
