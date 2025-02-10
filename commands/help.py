from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Here are the available commands: /start, /add_expense, /help")

def get_handler():
    return CommandHandler("help", help_command)