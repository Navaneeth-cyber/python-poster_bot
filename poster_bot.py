import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)

# ---------------- Configuration ---------------- #
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8538257165:AAEEck3afTpes9-NCRxIi9rH4b4iYi14HIA")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8207746599"))
PORT = int(os.environ.get("PORT", "10000"))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://python-poster-bot.onrender.com")

# ---------------- States ---------------- #
ASK_CHANNEL, ASK_IMAGE, ASK_TITLE, ASK_LINKS = range(4)

TEMP = {}

# ---------------- Handlers ---------------- #
async def start_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return ConversationHandler.END

    await update.message.reply_text("📌 Enter channel username (e.g., @MyChannel):")
    return ASK_CHANNEL


async def ask_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel = update.message.text.strip()

    if not channel.startswith("@"):
        await update.message.reply_text("⚠️ Channel must start with '@'. Try again:")
        return ASK_CHANNEL

    TEMP["channel"] = channel

    await update.message.reply_text("📸 Send image OR type 'skip' to continue without an image:")
    return ASK_IMAGE


async def ask_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        TEMP["image"] = update.message.photo[-1].file_id
    else:
        if update.message.text and update.message.text.lower() == "skip":
            TEMP["image"] = None
        else:
            await update.message.reply_text("⚠️ Send a valid photo or type 'skip':")
            return ASK_IMAGE

    await update.message.reply_text("✏️ Enter title:")
    return ASK_TITLE


async def ask_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    TEMP["title"] = update.message.text.strip()

    await update.message.reply_text(
        "🔗 Enter links separated by comma (,):\nExample:\nlink1, link2, link3"
    )
    return ASK_LINKS


async def post_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_links = update.message.text.strip()

    links = [x.strip() for x in raw_links.split(",") if x.strip()]

    if not links:
        await update.message.reply_text("⚠️ Enter at least one link:")
        return ASK_LINKS

    buttons = []
    for i, link in enumerate(links):
        buttons.append([InlineKeyboardButton(f"Ep {i+1}", url=link)])

    keyboard = InlineKeyboardMarkup(buttons)

    channel = TEMP["channel"]

    try:
        if TEMP["image"]:
            await context.bot.send_photo(
                chat_id=channel,
                photo=TEMP["image"],
                caption=TEMP["title"],
                reply_markup=keyboard
            )
        else:
            await context.bot.send_message(
                chat_id=channel,
                text=TEMP["title"],
                reply_markup=keyboard
            )

        await update.message.reply_text(f"✅ Successfully posted to {channel}")

    except Exception as e:
        await update.message.reply_text(f"❌ Failed to post:\n{e}")

    TEMP.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    TEMP.clear()
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END


# ---------------- Bot Setup ---------------- #
app = ApplicationBuilder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("post", start_post)],
    states={
        ASK_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_image)],
        ASK_IMAGE: [
            MessageHandler(filters.PHOTO, ask_title),
            MessageHandler(filters.TEXT & ~filters.COMMAND, ask_title),
        ],
        ASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_links)],
        ASK_LINKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_to_channel)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)

# ---------------- Webhook ---------------- #
WEBHOOK_URL = f"{RENDER_URL}/{BOT_TOKEN}"

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=BOT_TOKEN,
    webhook_url=WEBHOOK_URL
)
