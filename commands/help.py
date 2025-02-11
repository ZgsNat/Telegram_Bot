from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, Application

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the available commands."""
    help_text = "Here are the available commands:\n"
    for handler in context.application.handlers[0]:
        if isinstance(handler, CommandHandler):
            commands = handler.commands
            for command in commands:
                help_text += f"/{command} - {handler.callback.__doc__}\n"
    await update.message.reply_text(help_text)

def get_handlers():
    return CommandHandler("help", help_command)