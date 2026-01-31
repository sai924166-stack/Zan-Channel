import os
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
    filters,
)

# =========================
# CONFIG
# =========================
BOT_TOKEN = "YOUR_BOT_TOKEN"

# Run the application
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()  # Corrected line here

    # ... (rest of your main code unchanged)


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
def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("👑 VIP Member ဝင်ရန်", callback_data="vip")],
        [InlineKeyboardButton("🎬 နမူနာကြည့်ရန်", callback_data="preview")],
        [InlineKeyboardButton("🎞️ တစ်ကားချင်းဝယ်ရန်", callback_data="buy")],
    ]
    update.message.reply_text(
        "🎥 Zan Channel Bot မှ ကြိုဆိုပါတယ်\nအောက်ကခလုတ်ကို ရွေးပါ",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return MENU

# ======================================================
# VIP FLOW
# ======================================================
def vip_menu(update: Update, context):
    query = update.callback_query
    query.answer()
    keyboard = [[InlineKeyboardButton(m, callback_data=f"vip_{m}")] for m in PAY_METHODS]
    query.edit_message_text(
        "👑 VIP Payment Method ရွေးပါ",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return VIP_PAY

def vip_pay(update: Update, context):
    query = update.callback_query
    query.answer()
    method = query.data.replace("vip_", "")
    query.edit_message_text(
        PAY_INFO[method] + "\n\n📸 ပြေစာ ပို့ပါ"
    )
    return VIP_SLIP

def vip_slip(update: Update, context):
    photo = update.message.photo[-1].file_id
    user = update.message.from_user
    context.bot.send_photo(
        ADMIN_ID,
        photo,
        caption=f"VIP SLIP\nUser: {user.full_name}\nID: {user.id}",
    )
    update.message.reply_text("✅ ပြေစာ လက်ခံပြီးပါပြီ")
    return ConversationHandler.END

# ======================================================
# BUY MOVIE FLOW
# ======================================================
def buy_menu(update: Update, context):
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton(f"{v[0]} - {v[1]}", callback_data=k)]
        for k, v in MOVIES.items()
    ]
    query.edit_message_text(
        "🎞️ ဇာတ်ကား ရွေးပါ",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return BUY_MOVIE

def buy_select(update: Update, context):
    query = update.callback_query
    query.answer()
    movie = MOVIES[query.data]
    context.user_data["movie"] = movie
    keyboard = [[InlineKeyboardButton(m, callback_data=f"buy_{m}")] for m in PAY_METHODS]
    query.edit_message_text(
        f"{movie[0]} ({movie[1]})\nPayment Method ရွေးပါ",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return BUY_PAY

def buy_pay(update: Update, context):
    query = update.callback_query
    query.answer()
    method = query.data.replace("buy_", "")
    movie = context.user_data["movie"]
    query.edit_message_text(
        f"{movie[0]} ({movie[1]})\n\n{PAY_INFO[method]}\n\n📸 ပြေစာ ပို့ပါ"
    )
    return BUY_SLIP

def buy_slip(update: Update, context):
    photo = update.message.photo[-1].file_id
    user = update.message.from_user
    context.bot.send_photo(
        ADMIN_ID,
        photo,
        caption=f"MOVIE BUY\nUser: {user.full_name}\nID: {user.id}",
    )
    update.message.reply_text("✅ ပြေစာ လက်ခံပြီးပါပြီ")
    return ConversationHandler.END

# ======================================================
# PREVIEW
# ======================================================
def preview(update: Update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(
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
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

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

    application.add_handler(conv)

    # Run health server in a separate thread
    threading.Thread(target=run_health_server, daemon=True).start()

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
