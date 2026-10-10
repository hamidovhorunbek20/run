import os
import json
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

# Tokenni kodga yozmang! Terminalda:  export BOT_TOKEN="yangi_token"
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8539937553"))
# HTML faylingiz joylangan HTTPS manzil (GitHub Pages, Netlify, Vercel...)
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://SIZNING-SAYT.uz/index.html")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Muhim: sendData faqat KEYBOARD tugma orqali ochilgan WebApp'da ishlaydi
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton("🛡 KRYSEC Akademiyasiga yozilish", web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True,
    )
    await update.message.reply_text(
        "KRYSEC Cyber Academy'ga xush kelibsiz! Quyidagi tugmani bosing 👇",
        reply_markup=kb,
    )


async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.effective_message.web_app_data.data
    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        return
    if d.get("type") != "ACADEMY_REGISTRATION":
        return

    user = update.effective_user
    text = (
        "📥 Yangi ariza\n\n"
        f"👤 Ism: {d.get('fullname')}\n"
        f"📞 Telefon: {d.get('phone')}\n"
        f"📅 Kunlar: {d.get('class_days')}\n"
        f"🕐 Vaqt: {d.get('class_time')}\n\n"
        f"Telegram: @{user.username or '-'} (ID: {user.id})"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=text)
    await update.effective_message.reply_text("✅ Arizangiz qabul qilindi! Tez orada bog'lanamiz.")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    app.run_polling()


if __name__ == "__main__":
    main()
