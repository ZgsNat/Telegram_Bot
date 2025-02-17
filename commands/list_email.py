# commands/list_emails.py
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from database.google_sheets import get_user_sheet, list_permissions

# commands/list_emails.py
async def list_emails_command(update : Update, context : ContextTypes.DEFAULT_TYPE):
    """Liệt kê các email được cấp quyền chỉnh sửa Google Sheet"""
    sheet_id = get_user_sheet(update.message.from_user.id)
    if sheet_id:
        emails = list_permissions(sheet_id)
        await update.message.reply_text("📧 Các email được cấp quyền: \n" + '\n'.join(emails))
    else:
        await update.message.reply_text("❌ Bạn chưa có Google Sheet.")

def get_handlers():
    return CommandHandler("list_emails", list_emails_command)