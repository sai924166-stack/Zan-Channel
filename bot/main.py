import logging
import os
import http.server
import socketserver
import threading
import sys
import time
import signal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

# ------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------
TOKEN = "8515688348:AAEyFdAE81stzDwgWmjaPMDtxcgOnbOdtEc" 
ADMIN_ID = 6445257462             # သင့် User ID
CHANNEL_ID = "@ZanchannelMM"      # သင့် Channel Username

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ------------------------------------------------------------------------------
# RENDER HEALTH CHECK SERVER (Ultra-Lightweight)
# ------------------------------------------------------------------------------
class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Render needs a quick 200 OK to verify the service is up
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        # Keep logs clean by ignoring health check hits
        return

def run_health_check_server():
    # Render maps its external port to the PORT env variable
    port = int(os.environ.get("PORT", 8080))
    server_address = ("0.0.0.0", port)
    
    # TCPServer with immediate port reuse
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(server_address, HealthCheckHandler) as httpd:
            logging.info(f"✅ Health Check Server active on port {port}")
            httpd.serve_forever()
    except Exception as e:
        logging.error(f"❌ Web Server Error: {e}")

# ------------------------------------------------------------------------------
# STATES
# ------------------------------------------------------------------------------
(
    SELECTING_ACTION,
    VIP_PAYMENT_SELECT,
    VIP_UPLOAD_SLIP,
    MOVIE_BROWSE,
    MOVIE_PAYMENT_SELECT,
    MOVIE_UPLOAD_SLIP,
    PREVIEW_BROWSE
) = range(7)

# ------------------------------------------------------------------------------
# DATA
# ------------------------------------------------------------------------------
PAYMENT_METHODS = ["KPay", "WavePay", "AYA Pay", "CB Pay"]

PAYMENT_INFO = {
    "KPay": {"name": "U Kyaw", "phone": "09123456789"},
    "WavePay": {"name": "U Kyaw", "phone": "09987654321"},
    "AYA Pay": {"name": "U Kyaw", "phone": "09111222333"},
    "CB Pay": {"name": "U Kyaw", "phone": "09555666777"},
}

MOVIES = {
    "m1": {"title": "Avengers (Endgame)", "price": "1000 MMK"},
    "m2": {"title": "Titanic", "price": "1500 MMK"},
    "m3": {"title": "Avatar 2", "price": "1200 MMK"},
}

# ------------------------------------------------------------------------------
# LOGIC
# ------------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id=None):
    target_id = chat_id if chat_id else update.effective_chat.id
    keyboard = [
        [InlineKeyboardButton("👑 VIP Member ဝင်ရန်", callback_data="flow_vip")],
        [InlineKeyboardButton("🎬 နမူနာကြည့်ရန်", callback_data="flow_preview")],
        [InlineKeyboardButton("🎞️ တစ်ကားချင်းဝယ်ရန်", callback_data="flow_single")],
        [InlineKeyboardButton("❓ အခြား", callback_data="flow_other")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "မင်္ဂလာပါ။ Movie Bot မှ ကြိုဆိုပါတယ်။\nဝန်ဆောင်မှု ရယူရန် အောက်ပါ ခလုတ်များကို နှိပ်ပါ။"
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=target_id, text=text, reply_markup=reply_markup)
    return SELECTING_ACTION

async def vip_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(m, callback_data=f"vip_pay_{m}")] for m in PAYMENT_METHODS]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_home")])
    await query.edit_message_text("👑 VIP Member အတွက် ငွေပေးချေမှုစနစ် ရွေးချယ်ပါ။", reply_markup=InlineKeyboardMarkup(keyboard))
    return VIP_PAYMENT_SELECT

async def vip_payment_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    method = query.data.replace("vip_pay_", "")
    info = PAYMENT_INFO[method]
    context.user_data['pay_method'] = method
    context.user_data['pay_type'] = "VIP"
    text = f"🏧 {method}\nName: {info['name']}\nPhone: {info['phone']}\nAmount: 5000 MMK\n\nငွေလွှဲပြီးပါက ပြေစာ screenshot ကို ၅ မိနစ်အတွင်း ပို့ပေးပါ။"
    await query.edit_message_text(text)
    return VIP_UPLOAD_SLIP

async def single_movie_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(f"{m['title']} - {m['price']}", callback_data=f"buy_mov_{mid}")] for mid, m in MOVIES.items()]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_home")])
    await query.edit_message_text("ဝယ်ယူလိုသော ဇာတ်ကားကို ရွေးချယ်ပါ။", reply_markup=InlineKeyboardMarkup(keyboard))
    return MOVIE_BROWSE

async def movie_pay_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    movie_id = query.data.replace("buy_mov_", "")
    context.user_data['selected_movie'] = MOVIES[movie_id]
    keyboard = [[InlineKeyboardButton(m, callback_data=f"mov_pay_{m}")] for m in PAYMENT_METHODS]
    await query.edit_message_text(f"🎬 {MOVIES[movie_id]['title']}\nငွေပေးချေမှုစနစ် ရွေးချယ်ပါ။", reply_markup=InlineKeyboardMarkup(keyboard))
    return MOVIE_PAYMENT_SELECT

async def movie_payment_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    method = query.data.replace("mov_pay_", "")
    info = PAYMENT_INFO[method]
    movie = context.user_data['selected_movie']
    context.user_data['pay_method'] = method
    context.user_data['pay_type'] = f"Single Movie: {movie['title']}"
    text = f"🏧 {method}\nMovie: {movie['title']}\nPrice: {movie['price']}\nName: {info['name']}\nPhone: {info['phone']}\n\nပြေစာကို ၅ မိနစ်အတွင်း ပို့ပေးပါ။"
    await query.edit_message_text(text)
    return MOVIE_UPLOAD_SLIP

async def handle_slip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    photo = update.message.photo[-1].file_id
    method = context.user_data.get('pay_method')
    p_type = context.user_data.get('pay_type')
    
    caption = f"📩 New Slip Received!\nUser: {user.full_name} ({user.id})\nMethod: {method}\nType: {p_type}"
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo, caption=caption)
    await update.message.reply_text("✅ ပြေစာလက်ခံရရှိပါသည်။ Admin မှ စစ်ဆေးပြီးနောက် ဝယ်ယူထားသော ကားကို ပို့ပေးပါမည်။")
    return ConversationHandler.END

async def preview_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(m['title'], callback_data=f"prev_{mid}")] for mid, m in MOVIES.items()]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_home")])
    await query.edit_message_text("နမူနာကြည့်ရန် ဇာတ်ကားရွေးချယ်ပါ။", reply_markup=InlineKeyboardMarkup(keyboard))
    return PREVIEW_BROWSE

async def preview_grant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        link = await context.bot.create_chat_invite_link(chat_id=CHANNEL_ID, member_limit=1)
        await query.edit_message_text(f"🎬 ဝင်ရောက်ကြည့်ရှုရန် Link: {link.invite_link}\n(Link ကို နှိပ်ပြီး ၃ မိနစ်သာ ကြည့်ရှုခွင့်ရပါမည်။)")
    except Exception as e:
        logging.error(f"Invite Link Error: {e}")
        await query.edit_message_text("❌ စနစ်ချို့ယွင်းနေပါသည်။ Admin ကို အကြောင်းကြားထားပါသည်။")
    return ConversationHandler.END

async def back_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await start(update, context)

# ------------------------------------------------------------------------------
# MAIN EXECUTION
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # 1. Start Health Check server in background
    web_thread = threading.Thread(target=run_health_check_server, daemon=True)
    web_thread.start()
    
    # Give the web server a head start to bind the port
    time.sleep(2)
    
    # 2. Build and start the Telegram Bot
    try:
        app = ApplicationBuilder().token(TOKEN).build()
        
        conv = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                SELECTING_ACTION: [
                    CallbackQueryHandler(vip_start, pattern="^flow_vip$"),
                    CallbackQueryHandler(preview_start, pattern="^flow_preview$"),
                    CallbackQueryHandler(single_movie_start, pattern="^flow_single$"),
                    CallbackQueryHandler(back_home, pattern="^flow_other$"),
                ],
                VIP_PAYMENT_SELECT: [
                    CallbackQueryHandler(vip_payment_details, pattern="^vip_pay_"),
                    CallbackQueryHandler(back_home, pattern="^back_home$")
                ],
                VIP_UPLOAD_SLIP: [MessageHandler(filters.PHOTO, handle_slip)],
                MOVIE_BROWSE: [
                    CallbackQueryHandler(movie_pay_select, pattern="^buy_mov_"),
                    CallbackQueryHandler(back_home, pattern="^back_home$")
                ],
                MOVIE_PAYMENT_SELECT: [CallbackQueryHandler(movie_payment_details, pattern="^mov_pay_")],
                MOVIE_UPLOAD_SLIP: [MessageHandler(filters.PHOTO, handle_slip)],
                PREVIEW_BROWSE: [
                    CallbackQueryHandler(preview_grant, pattern="^prev_"),
                    CallbackQueryHandler(back_home, pattern="^back_home$")
                ]
            },
            fallbacks=[CommandHandler('start', start)]
        )
        
        app.add_handler(conv)
        app.add_handler(CallbackQueryHandler(back_home, pattern="^back_home$"))
        
        logging.info("🚀 Zan-Channel Bot is starting polling...")
        
        # stop_signals=None is used sometimes if external supervisor is used, 
        # but here we use default to let it handle SIGTERM correctly.
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logging.critical(f"💥 Fatal Error: {e}")
        sys.exit(1)
