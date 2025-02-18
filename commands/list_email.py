from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from database.google_sheets_v2 import get_user_sheet, list_permissions

# commands/list_emails.py
async def list_emails_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Liệt kê các email được cấp quyền chỉnh sửa Google Sheet"""
    sheet_id = await get_user_sheet(update.message.from_user.id)  # Lấy sheet_id bất đồng bộ
    if sheet_id:
        emails = await list_permissions(sheet_id)  # Lấy danh sách email bất đồng bộ
        await update.message.reply_text("📧 Các email được cấp quyền: \n" + '\n'.join(emails))
    else:
        await update.message.reply_text("❌ Bạn chưa có Google Sheet.")

def get_handlers():
    return CommandHandler("list_emails", list_emails_command)
