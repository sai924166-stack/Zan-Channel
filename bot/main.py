import logging
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
import datetime

# ------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------
TOKEN = "8515688348:AAEyFdAE81stzDwgWmjaPMDtxcgOnbOdtEc"  # Replace with your BotFather token
ADMIN_ID = 123456789             # Replace with the Admin's numeric Telegram ID
CHANNEL_ID = -1001234567890      # Replace with your Private Channel ID

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ------------------------------------------------------------------------------
# STATES FOR CONVERSATION HANDLER
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
# MOCK DATABASE / DATA
# ------------------------------------------------------------------------------
PAYMENT_METHODS = ["KPay", "WavePay", "AYA Pay", "CB Pay"]

PAYMENT_INFO = {
    "KPay": {"name": "U Kyaw", "phone": "09123456789", "qr": "kpay_qr.jpg"},
    "WavePay": {"name": "U Kyaw", "phone": "09987654321", "qr": "wave_qr.jpg"},
    "AYA Pay": {"name": "U Kyaw", "phone": "09111222333", "qr": "aya_qr.jpg"},
    "CB Pay": {"name": "U Kyaw", "phone": "09555666777", "qr": "cb_qr.jpg"},
}

MOVIES = {
    "m1": {"title": "Avengers", "price": "1000 MMK", "post_id": 100},
    "m2": {"title": "Titanic", "price": "800 MMK", "post_id": 101},
    "m3": {"title": "Avatar", "price": "1200 MMK", "post_id": 102},
    "m4": {"title": "Inception", "price": "1000 MMK", "post_id": 103},
}

# ------------------------------------------------------------------------------
# TIMEOUT CALLBACKS (BACKGROUND JOBS)
# ------------------------------------------------------------------------------

async def payment_timeout_callback(context: ContextTypes.DEFAULT_TYPE):
    """Triggered if 5 minutes pass without slip upload."""
    job = context.job
    await context.bot.send_message(
        chat_id=job.chat_id,
        text="⚠️ ငွေလွှဲရန် သတ်မှတ်ချိန် (၅) မိနစ် ကုန်ဆုံးသွားပါပြီ။ ပင်မစာမျက်နှာသို့ ပြန်သွားပါမည်။"
    )
    # In a real scenario, we might want to force reset the user's state here,
    # but ConversationHandler usually waits for input. We inform the user to restart.
    await start(None, context, chat_id=job.chat_id)

async def preview_kick_callback(context: ContextTypes.DEFAULT_TYPE):
    """Triggered 3 minutes after preview starts."""
    job = context.job
    user_id = job.user_id
    
    try:
        # Kick (Ban) the user to remove them, then Unban to allow re-join later if they pay
        await context.bot.ban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        await context.bot.unban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        
        await context.bot.send_message(
            chat_id=job.chat_id,
            text="⏳ နမူနာကြည့်ရှုချိန် (၃) မိနစ် ပြည့်သွားပါပြီ။\nဒီကားကို ဆက်ကြည့်ရန် ဝယ်ယူပြီးမှသာ ကြည့်နိုင်ပါမည်။"
        )
    except Exception as e:
        logging.error(f"Failed to kick user {user_id}: {e}")

# ------------------------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id=None):
    """Entry point: /start command."""
    # Handle both direct updates and calls from other functions
    target_id = chat_id if chat_id else update.effective_chat.id

    keyboard = [
        [InlineKeyboardButton("👑 VIP Member ဝင်ရန်", callback_data="flow_vip")],
        [InlineKeyboardButton("🎬 နမူနာကြည့်ရန်", callback_data="flow_preview")],
        [InlineKeyboardButton("🎞️ တစ်ကားချင်းဝယ်ရန်", callback_data="flow_single")],
        [InlineKeyboardButton("❓ အခြား", callback_data="flow_other")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "မင်္ဂလာပါ။ Movie Bot မှ ကြိုဆိုပါတယ်။\nဝန်ဆောင်မှု ရယူရန် အောက်ပါ ခလုတ်များကို နှိပ်ပါ။"
    
    if update:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=target_id, text=text, reply_markup=reply_markup)

    return SELECTING_ACTION

# ------------------------------------------------------------------------------
# FLOW 1: VIP MEMBER
# ------------------------------------------------------------------------------

async def vip_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    # Create rows of 2 buttons
    row = []
    for method in PAYMENT_METHODS:
        row.append(InlineKeyboardButton(method, callback_data=f"vip_pay_{method}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_home")])

    await query.edit_message_text(
        text="👑 VIP Member ဝင်ရန် ငွေပေးချေမှုစနစ် ရွေးချယ်ပါ။",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return VIP_PAYMENT_SELECT

async def vip_payment_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    method = query.data.replace("vip_pay_", "")
    info = PAYMENT_INFO.get(method)
    
    # Save context
    context.user_data['payment_type'] = 'VIP'
    context.user_data['method'] = method

    text = (
        f"🏧 <b>{method} Payment Information</b>\n\n"
        f"Name: {info['name']}\n"
        f"Phone: {info['phone']}\n"
        f"Amount: 5000 MMK (Monthly)\n\n" # Example VIP Price
        f"⚠️ ငွေလွှဲပြီးပါက ပြေစာ screenshot ကို (၅) မိနစ်အတွင်း upload လုပ်ပေးပါ။"
    )

    # Start 5-minute timer (300 seconds)
    context.job_queue.run_once(
        payment_timeout_callback, 
        300, 
        chat_id=query.message.chat_id, 
        name=str(query.message.chat_id)
    )

    await query.edit_message_text(text=text, parse_mode='HTML')
    # Note: In a real app, you would send the QR code image here using send_photo
    
    return VIP_UPLOAD_SLIP

# ------------------------------------------------------------------------------
# FLOW 2: SINGLE MOVIE PURCHASE
# ------------------------------------------------------------------------------

async def single_movie_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = []
    for mid, mdata in MOVIES.items():
        btn_text = f"{mdata['title']} ({mdata['price']})"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"buy_mov_{mid}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_home")])

    await query.edit_message_text(
        text="ဝယ်ယူလိုသော ဇာတ်ကားကို ရွေးချယ်ပါ။",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MOVIE_BROWSE

async def single_movie_pay_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    movie_id = query.data.replace("buy_mov_", "")
    movie = MOVIES[movie_id]
    context.user_data['selected_movie'] = movie
    
    keyboard = []
    row = []
    for method in PAYMENT_METHODS:
        row.append(InlineKeyboardButton(method, callback_data=f"mov_pay_{method}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    
    await query.edit_message_text(
        text=f"🎞️ <b>{movie['title']}</b>\n💰 Price: {movie['price']}\n\nငွေပေးချေမှုစနစ် ရွေးချယ်ပါ။",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return MOVIE_PAYMENT_SELECT

async def single_movie_payment_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    method = query.data.replace("mov_pay_", "")
    info = PAYMENT_INFO.get(method)
    movie = context.user_data['selected_movie']
    
    context.user_data['payment_type'] = 'SINGLE'
    context.user_data['method'] = method

    text = (
        f"🏧 <b>{method} Payment Information</b>\n"
        f"Movie: {movie['title']}\n"
        f"Price: {movie['price']}\n\n"
        f"Name: {info['name']}\n"
        f"Phone: {info['phone']}\n\n"
        f"⚠️ ငွေလွှဲပြီးပါက ပြေစာ screenshot ကို (၅) မိနစ်အတွင်း upload လုပ်ပေးပါ။"
    )

    # Start 5-minute timer
    context.job_queue.run_once(
        payment_timeout_callback, 
        300, 
        chat_id=query.message.chat_id, 
        name=str(query.message.chat_id)
    )

    await query.edit_message_text(text=text, parse_mode='HTML')
    return MOVIE_UPLOAD_SLIP

# ------------------------------------------------------------------------------
# COMMON: HANDLE SLIP UPLOAD
# ------------------------------------------------------------------------------

async def handle_slip_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    photo_file = await update.message.photo[-1].get_file()
    
    # 1. Stop the 5-minute timer
    current_jobs = context.job_queue.get_jobs_by_name(str(update.message.chat_id))
    for job in current_jobs:
        job.schedule_removal()

    # 2. Get Info
    pay_type = context.user_data.get('payment_type', 'Unknown')
    method = context.user_data.get('method', 'Unknown')
    details = ""
    
    if pay_type == 'SINGLE':
        movie = context.user_data.get('selected_movie', {})
        details = f"Movie: {movie.get('title')}"
    else:
        details = "VIP Purchase"

    # 3. Forward to Admin
    caption = (
        f"📩 <b>New Payment Slip Received!</b>\n"
        f"User: {user.full_name} (ID: {user.id})\n"
        f"Type: {pay_type}\n"
        f"Method: {method}\n"
        f"{details}\n\n"
        f"Please verify and approve manually."
    )

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file.file_id,
            caption=caption,
            parse_mode='HTML'
        )
        await update.message.reply_text("✅ ငွေလွှဲပြေစာ လက်ခံရရှိပါသည်။ Admin မှ စစ်ဆေးပြီး အကြောင်းပြန်ပါမည်။")
    except Exception as e:
        await update.message.reply_text("❌ Error sending to admin. Please try again.")
        logging.error(e)

    # Return to start state or end conversation
    return ConversationHandler.END

# ------------------------------------------------------------------------------
# FLOW 3: PREVIEW (3 MINUTES)
# ------------------------------------------------------------------------------

async def preview_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = []
    for mid, mdata in MOVIES.items():
        # Tag callback with "prev_"
        keyboard.append([InlineKeyboardButton(mdata['title'], callback_data=f"prev_{mid}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_home")])

    await query.edit_message_text(
        text="နမူနာကြည့်ရန် ဇာတ်ကားရွေးချယ်ပါ။ (၃ မိနစ်သာ ကြည့်ရှုခွင့်ရပါမည်)",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PREVIEW_BROWSE

async def preview_grant_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    movie_id = query.data.replace("prev_", "")
    movie = MOVIES[movie_id]

    # 1. Generate a temporary Invite Link (valid for join, but we kick via job queue)
    # Note: "expire_date" in create_chat_invite_link makes the LINK invalid, not the user session.
    try:
        invite_link = await context.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1,
            name=f"Preview-{query.from_user.id}"
        )
        
        # 2. Schedule Kick Job (3 minutes = 180 seconds)
        context.job_queue.run_once(
            preview_kick_callback, 
            180, 
            chat_id=query.message.chat_id, 
            user_id=query.from_user.id
        )

        text = (
            f"🎬 <b>{movie['title']} Preview</b>\n\n"
            f"အောက်ပါ Link ကို နှိပ်ပြီး ဝင်ရောက်ကြည့်ရှုပါ။\n"
            f"အချိန် (၃) မိနစ်ပြည့်ပါက အလိုအလျောက် access ပိတ်ပါမည်။\n\n"
            f"Link: {invite_link.invite_link}"
        )
        
        await query.edit_message_text(text=text, parse_mode='HTML')
        
    except Exception as e:
        await query.edit_message_text(f"Error generating link. Is the bot admin in the channel? {e}")

    return ConversationHandler.END

# ------------------------------------------------------------------------------
# UTILS: BACK & CANCEL
# ------------------------------------------------------------------------------

async def back_to_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resets to main menu."""
    query = update.callback_query
    await query.answer()
    await start(None, context, chat_id=query.message.chat_id)
    return SELECTING_ACTION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

# ------------------------------------------------------------------------------
# MAIN EXECUTION
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    # Setup Conversation Handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(vip_start, pattern='^flow_vip$'),
                CallbackQueryHandler(single_movie_start, pattern='^flow_single$'),
                CallbackQueryHandler(preview_start, pattern='^flow_preview$'),
                CallbackQueryHandler(start, pattern='^flow_other$'), # Placeholder
            ],
            
            # VIP FLOW STATES
            VIP_PAYMENT_SELECT: [
                CallbackQueryHandler(vip_payment_details, pattern='^vip_pay_'),
                CallbackQueryHandler(back_to_home, pattern='^back_home$')
            ],
            VIP_UPLOAD_SLIP: [
                MessageHandler(filters.PHOTO, handle_slip_upload)
            ],

            # SINGLE MOVIE FLOW STATES
            MOVIE_BROWSE: [
                CallbackQueryHandler(single_movie_pay_select, pattern='^buy_mov_'),
                CallbackQueryHandler(back_to_home, pattern='^back_home$')
            ],
            MOVIE_PAYMENT_SELECT: [
                CallbackQueryHandler(single_movie_payment_details, pattern='^mov_pay_'),
                CallbackQueryHandler(single_movie_start, pattern='^back_list$') # Optional back logic
            ],
            MOVIE_UPLOAD_SLIP: [
                MessageHandler(filters.PHOTO, handle_slip_upload)
            ],

            # PREVIEW FLOW STATES
            PREVIEW_BROWSE: [
                CallbackQueryHandler(preview_grant_access, pattern='^prev_'),
                CallbackQueryHandler(back_to_home, pattern='^back_home$')
            ]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    application.add_handler(conv_handler)

    print("Bot is running...")
    application.run_polling()
