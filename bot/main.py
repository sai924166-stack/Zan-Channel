import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("💎 VIP Member ဝင်ရန်", callback_data="vip")],
        [InlineKeyboardButton("🎬 နမူနာကြည့်ရန်", callback_data="preview")],
        [InlineKeyboardButton("🛒 တစ်ကားချင်းဝယ်ရန်", callback_data="buy")],
        [InlineKeyboardButton("ℹ️ အခြား", callback_data="other")]
    ]
    await update.message.reply_text(
        "Zan Channel Bot မှ ကြိုဆိုပါတယ် 👋\nစတင်ရန် button ကိုနှိပ်ပါ",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
