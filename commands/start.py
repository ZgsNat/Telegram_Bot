from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Welcome to the Expense Bot. How can I help you?")

# Hàm trả về handler để tự động load
def get_handler():
    return CommandHandler("start", start_command)