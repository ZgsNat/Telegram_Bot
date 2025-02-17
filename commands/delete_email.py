from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from database.google_sheets import get_user_sheet, list_permissions, delete_email_permission

# commands/delete_email.py
async def delete_email_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xoá quyền chỉnh sửa Google Sheet của một email"""
    user_email = context.args[0] if context.args else None
    if not user_email:
        await update.message.reply_text("❌ Vui lòng nhập email: /delete_email <email>")
        return

    sheet_id = get_user_sheet(update.message.from_user.id)
    if sheet_id and delete_email_permission(sheet_id, user_email):
        await update.message.reply_text(f"✅ Đã xoá quyền của {user_email}.")
    else:
        await update.message.reply_text(f"❌ Không tìm thấy email {user_email} hoặc không có quyền.")

def get_handlers():
    return CommandHandler("delete_email", delete_email_command)