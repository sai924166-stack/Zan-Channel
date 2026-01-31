import os
import asyncio
import logging
import http.server
import socketserver
import threading

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIG
# =========================
BOT_TOKEN = "8515688348:AAE0a7XcOIfRF9DJfrbdLNFsnJxPJFem18o"
ADMIN_ID = 6445257462
CHANNEL_LINK = "https://t.me/ZanchannelMM"

# ======================================================
# STATES
# ======================================================
MENU, VIP_PAY, VIP_SLIP, BUY_MOVIE, BUY_PAY, BUY_SLIP = range(6)

# ======================================================
# DATA
# ======================================================
PAY_METHODS = ["KPay", "WavePay", "AYA Pay", "CB Pay"]

PAY_INFO = {
    "KPay": "KPay\nName: U Kyaw\nPhone: 09123456789\nAmount: 5000 MMK",
    "WavePay": "WavePay\nName: U Kyaw\nPhone: 09987654321\nAmount: 5000 MMK",
    "AYA Pay": "AYA Pay\nName: U Kyaw\nPhone: 09111222333\nAmount: 5000 MMK",
    "CB Pay": "CB Pay\nName: U Kyaw\nPhone: 09555666777\nAmount: 5000 MMK",
}

MOVIES = {
    "m1": ("Avengers", "1000 MMK"),
    "m2": ("Titanic", "1500 MMK"),
    "m3": ("Avatar 2", "1200 MMK"),
}

# ======================================================
# START / MAIN MENU
# ======================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👑 VIP Member ဝင်ရန်", callback_data="vip")],
        [InlineKeyboardButton("🎬 နမူနာကြည့်ရန်", callback_data="preview")],
        [InlineKeyboardButton("🎞️ တစ်ကားချင်းဝယ်ရန်", callback_data="buy")],
    ]
    await update.message.reply_text(
        "🎥 Zan Channel Bot မှ ကြိုဆိုပါတယ်\nအောက်ကခလုတ်ကို ရွေးပါ",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return MENU

# ======================================================
# VIP FLOW
# ======================================================
async def vip_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    keyboard = [[InlineKeyboardButton(m, callback_data=f"vip_{m}")] for m in PAY_METHODS]
    await q.edit_message_text(
        "👑 VIP Payment Method ရွေးပါ",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return VIP_PAY

async def vip_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    method = q.data.replace("vip_", "")
    await q.edit_message_text(
        PAY_INFO[method] + "\n\n📸 ပြေစာ ပို့ပါ"
    )
    return VIP_SLIP

async def vip_slip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1].file_id
    user = update.message.from_user
    await context.bot.send_photo(
        ADMIN_ID,
        photo,
        caption=f"VIP SLIP\nUser: {user.full_name}\nID: {user.id}",
    )
    await update.message.reply_text("✅ ပြေစာ လက်ခံပြီးပါပြီ")
    return ConversationHandler.END

# ======================================================
# BUY MOVIE FLOW
# ======================================================
async def buy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    keyboard = [
        [InlineKeyboardButton(f"{v[0]} - {v[1]}", callback_data=k)]
        for k, v in MOVIES.items()
    ]
    await q.edit_message_text(
        "🎞️ ဇာတ်ကား ရွေးပါ",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return BUY_MOVIE

async def buy_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    movie = MOVIES[q.data]
    context.user_data["movie"] = movie
    keyboard = [[InlineKeyboardButton(m, callback_data=f"buy_{m}")] for m in PAY_METHODS]
    await q.edit_message_text(
        f"{movie[0]} ({movie[1]})\nPayment Method ရွေးပါ",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return BUY_PAY

async def buy_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    method = q.data.replace("buy_", "")
    movie = context.user_data["movie"]
    await q.edit_message_text(
        f"{movie[0]} ({movie[1]})\n\n{PAY_INFO[method]}\n\n📸 ပြေစာ ပို့ပါ"
    )
    return BUY_SLIP

async def buy_slip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1].file_id
    user = update.message.from_user
    await context.bot.send_photo(
        ADMIN_ID,
        photo,
        caption=f"MOVIE BUY\nUser: {user.full_name}\nID: {user.id}",
    )
    await update.message.reply_text("✅ ပြေစာ လက်ခံပြီးပါပြီ")
    return ConversationHandler.END

# ======================================================
# PREVIEW
# ======================================================
async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        f"🎬 Preview (3 မိနစ်)\n{CHANNEL_LINK}\n\nပြီးရင် ဝယ်ယူရပါမည်"
    )
    return ConversationHandler.END

# ======================================================
# HEALTH CHECK SERVER (Render Free)
# ======================================================
class Health(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    with socketserver.TCPServer(("0.0.0.0", port), Health) as httpd:
        httpd.serve_forever()

# ======================================================
# MAIN
# ======================================================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [
                CallbackQueryHandler(vip_menu, pattern="^vip$"),
                CallbackQueryHandler(buy_menu, pattern="^buy$"),
                CallbackQueryHandler(preview, pattern="^preview$"),
            ],
            VIP_PAY: [CallbackQueryHandler(vip_pay, pattern="^vip_")],
            VIP_SLIP: [MessageHandler(filters.PHOTO, vip_slip)],
            BUY_MOVIE: [CallbackQueryHandler(buy_select)],
            BUY_PAY: [CallbackQueryHandler(buy_pay, pattern="^buy_")],
            BUY_SLIP: [MessageHandler(filters.PHOTO, buy_slip)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv)

    # Run health server in a separate thread
    threading.Thread(target=run_health_server, daemon=True).start()

    # Run the bot
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
