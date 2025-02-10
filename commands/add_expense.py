from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from services.expense_service import add_expense_entry

async def add_expense_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /add_expense <amount> <description>")
        return
    
    amount = context.args[0]
    description = " ".join(context.args[1:])
    add_expense_entry(amount, description)
    await update.message.reply_text(f"Added expense: {amount} for {description}")

def get_handler():
    return CommandHandler("add_expense", add_expense_command)