import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)

# ---------------- Configuration ---------------- #
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8538257165:AAEEck3afTpes9-NCRxIi9rH4b4iYi14HIA")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8207746599"))  # your Telegram ID
PORT = int(os.environ.get("PORT", 8443))  # Render provides this
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://your-app.onrender.com")  # your app URL

# ---------------- Conversation States ---------------- #
ASK_CHANNEL, ASK_IMAGE, ASK_TITLE, ASK_LINKS = range(4)

# Temporary storage for post data
TEMP_POST = {}

# ---------------- Handlers ---------------- #

async def start_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return ConversationHandler.END

    await update.message.reply_text(
        "📌 Enter the channel username to post (e.g., @MyChannel):"
    )
    return ASK_CHANNEL

async def ask_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    TEMP_POST["channel"] = update.message.text.strip()
    await update.message.reply_text(
        "📸 Send the image for the post or type 'skip' to post without image:"
    )
    return ASK_IMAGE

async def ask_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text.lower() == "skip":
        TEMP_POST["image"] = None
    else:
        if update.message.photo:
            TEMP_POST["image"] = update.message.photo[-1].file_id
        else:
            await update.message.reply_text("⚠️ Please send a valid image or type 'skip'.")
            return ASK_IMAGE

    await update.message.reply_text("✏️ Enter the anime title:")
    return ASK_TITLE

async def ask_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    TEMP_POST["title"] = update.message.text
    await update.message.reply_text(
        "🔗 Enter all download/short links separated by comma (e.g., link1, link2, link3):"
    )
    return ASK_LINKS

async def post_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    links_text = update.message.text
    links = [link.strip() for link in links_text.split(",") if link.strip()]

    if not links:
        await update.message.reply_text("⚠️ You must enter at least one link.")
        return ASK_LINKS

    buttons = [[InlineKeyboardButton(f"{TEMP_POST['title']} Ep{i+1}", url=link)] for i, link in enumerate(links)]
    keyboard = InlineKeyboardMarkup(buttons)

    channel_id = TEMP_POST["channel"]
    try:
        if TEMP_POST["image"]:
            await context.bot.send_photo(
                chat_id=channel_id,
                photo=TEMP_POST["image"],
                caption=TEMP_POST["title"],
                reply_markup=keyboard
            )
        else:
            await context.bot.send_message(
                chat_id=channel_id,
                text=TEMP_POST["title"],
                reply_markup=keyboard
            )
        await update.message.reply_text(f"✅ Post published successfully to {channel_id}!")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to post: {e}")

    TEMP_POST.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    TEMP_POST.clear()
    await update.message.reply_text("❌ Posting cancelled.")
    return ConversationHandler.END

# ---------------- Bot Setup ---------------- #
app = ApplicationBuilder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("post", start_post)],
    states={
        ASK_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_image)],
        ASK_IMAGE: [MessageHandler(filters.PHOTO | filters.TEXT, ask_title)],
        ASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_links)],
        ASK_LINKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_to_channel)]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)

# ---------------- Webhook Setup ---------------- #
WEBHOOK_URL = f"{RENDER_URL}/{BOT_TOKEN}"

# Start webhook
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=BOT_TOKEN,
    webhook_url=WEBHOOK_URL
)
