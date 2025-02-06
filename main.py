from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sys
import logging
import signal

# Configurations
TOKEN: Final = "7598466336:AAHgl2qX8zE80knqWZe1agsItTvkBDVjEUM"
BOT_USERNAME: Final = "@ZgsNat_Bot"

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(livename)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    await update.message.reply_text("Hello! I'm your expense manager bot. How can I assist you today?")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command."""
    await update.message.reply_text("I can help you manage expenses. Try sending 'Hello' or other simple commands!")

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle a custom command."""
    await update.message.reply_text("This is a custom command response!")

# Message Responses
def handle_response(text: str) -> str:
    """Process user messages and generate appropriate responses."""
    processed_text = text.lower()
    if "hello" in processed_text:
        return "Hello! How can I help you?"
    
    if "bye" in processed_text:
        return "Goodbye!"

    return "I'm not sure how to respond to that."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages."""
    message_type: str = update.message.chat.type
    text: str = update.message.text

    logger.info(f"User ({update.message.chat.id}) in {message_type} sent: {text}")

    # Bot only responds in groups when mentioned
    if message_type == "group" and BOT_USERNAME not in text:
        return

    response: str = handle_response(text.replace(BOT_USERNAME, "").strip() if message_type == "group" else text)
    logger.info(f"Bot response: {response}")
    await update.message.reply_text(response)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the bot."""
    logger.error(f"Update {update} caused error: {context.error}")
    if update and update.message:
        await update.message.reply_text("Oops! Something went wrong.")

def stop_bot(signal_received, frame):
    """Gracefully stop the bot when SIGINT is detected."""
    logger.info("Bot is stopping...")
    sys.exit(0)

if __name__ == "__main__":
    # Handle SIGINT to stop bot gracefully
    signal.signal(signal.SIGINT, stop_bot)

    # Ensure UTF-8 for Windows console
    sys.stdout.reconfigure(encoding='utf-8')

    logger.info("Starting the bot...")
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("custom", custom_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Errors
    app.add_error_handler(error_handler)

    # Start polling
    logger.info("Bot is polling...")
    app.run_polling(poll_interval=3)
