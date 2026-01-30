import os
import logging
import http.server
import socketserver
import asyncio

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# ------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")          # Render ENV
ADMIN_ID = 6445257462                      # YOUR TELEGRAM ID
CHANNEL_LINK = "https://t.me/ZanchannelMM" # YOUR CHANNEL LINK

logging.basicConfig(level=logging.INFO)

# ------------------------------------------------------------------
# STATES
# ------------------------------------------------------------------
(
    MENU,
    VIP_PAY,
    VIP_SLIP,
    BUY_MOVIE,
    BUY_PAY,
    BUY_SLIP,
    PREVIEW,
) = range(7)

# ------------------------------------------------------------------
# DATA
# ------------------------------------------------------------------
PAY_METHODS = ["KPay", "WavePay", "AYA Pay", "CB Pay"]

PAY_INFO = {
    "KPay": "KPay\nName: U Kyaw\nPh: 09123456789\nAmount: 5000 MMK",
    "WavePay": "WavePay\nName: U Kyaw\nPh: 09987654321\nAmount: 5000 MMK",
    "AYA Pay": "AYA Pay\nName: U Kyaw\nPh: 09111222333\nAmount: 5000 MMK",
    "CB Pay": "CB Pay\nName: U Kyaw\nPh: 09555666777\nAmount: 5000 MMK",
}

MOVIES = {
    "m1": ("Avengers", "1000 MMK"),
    "m2": ("Titanic", "1500 MMK"),
    "m3": ("Avatar 2", "1200 MMK"),
}

# ------------------------------------------------------------------
# START + MAIN MENU
# ------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("👑 VIP Member ဝင်ရန်", callback_data="vip")],
        [InlineKeyboardButton("🎬 နမူနာကြည့်ရန်", callback_data="preview")],
        [InlineKeyboardButton("🎞️ တစ်ကားချင်းဝယ်ရန်", callback_data="buy")],
    ]
    await update.message.reply_text(
        "🎥 Zan Channel Bot မှ ကြိုဆိုပါတယ်\nအောက်ကခလုတ်ကို ရွေးပါ",
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return MENU

# ------------------------------------------------------------------
# VIP FLOW
# ------------------------------------------------------------------
async def vip_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    kb = [[InlineKeyboardButton(m, callback_data=f"vip_{m}")] for m in PAY_METHODS]
    kb.append([InlineKeyboardButton("⬅ Back", callback_data="back")])

    await q.edit_message_text(
        "👑 VIP Payment Method ရွေးပါ",
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return VIP_PAY


async def vip_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    method = q.data.replace("vip_", "")
    context.user_data["pay"] = method

    await q.edit_message_text(
        f"{PAY_INFO[method]}\n\n📸 ပြေစာကို 5 မိနစ်အတွင်း ပို့ပါ"
    )

    asyncio.create_task(timeout_back(context, q.message.chat_id))
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

# ------------------------------------------------------------------
# BUY MOVIE FLOW
# ------------------------------------------------------------------
async def buy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    kb = [
        [InlineKeyboardButton(f"{v[0]} - {v[1]}", callback_data=k)]
        for k, v in MOVIES.items()
    ]
    kb.append([InlineKeyboardButton("⬅ Back", callback_data="back")])

    await q.edit_message_text(
        "🎞️ ဇာတ်ကား ရွေးပါ",
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return BUY_MOVIE


async def buy_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    movie_id = q.data
    context.user_data["movie"] = MOVIES[movie_id]

    kb = [[InlineKeyboardButton(m, callback_data=f"buy_{m}")] for m in PAY_METHODS]

    await q.edit_message_text(
        f"{MOVIES[movie_id][0]} ({MOVIES[movie_id][1]})\nPayment Method ရွေးပါ",
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return BUY_PAY


async def buy_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    method = q.data.replace("buy_", "")
    movie = context.user_data["movie"]

    await q.edit_message_text(
        f"{movie[0]}\n{movie[1]}\n\n{PAY_INFO[method]}\n\n📸 ပြေစာကို 5 မိနစ်အတွင်း ပို့ပါ"
    )

    asyncio.create_task(timeout_back(context, q.message.chat_id))
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

# ------------------------------------------------------------------
# PREVIEW
# ------------------------------------------------------------------
async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    await q.edit_message_text(
        f"🎬 3 မိနစ် Preview\n{CHANNEL_LINK}\n\nအချိန်ပြီးရင် ဝယ်ယူရပါမည်"
    )
    return ConversationHandler.END

# ------------------------------------------------------------------
# BACK + TIMEOUT
# ------------------------------------------------------------------
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await start(update, context)
    return MENU


async def timeout_back(context, chat_id):
    await asyncio.sleep(300)
    await context.bot.send_message(chat_id, "⏰ အချိန်ကျော်သွားပါပြီ /start ပြန်နှိပ်ပါ")

# ------------------------------------------------------------------
# HEALTH CHECK (RENDER)
# ------------------------------------------------------------------
class Health(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [
                CallbackQueryHandler(vip_menu, pattern="^vip$"),
                CallbackQueryHandler(buy_menu, pattern="^buy$"),
                CallbackQueryHandler(preview, pattern="^preview$"),
            ],
            VIP_PAY: [CallbackQueryHandler(vip_payment, pattern="^vip_")],
            VIP_SLIP: [MessageHandler(filters.PHOTO, vip_slip)],
            BUY_MOVIE: [CallbackQueryHandler(buy_select)],
            BUY_PAY: [CallbackQueryHandler(buy_payment, pattern="^buy_")],
            BUY_SLIP: [MessageHandler(filters.PHOTO, buy_slip)],
        },
        fallbacks=[CallbackQueryHandler(back, pattern="^back$")],
    )

    app.add_handler(conv)

    asyncio.get_event_loop().create_task(app.run_polling())

    port = int(os.environ.get("PORT", 10000))
    with socketserver.TCPServer(("0.0.0.0", port), Health) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
