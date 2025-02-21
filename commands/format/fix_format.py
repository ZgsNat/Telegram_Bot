from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from database.google_sheets_v2 import get_user_sheet_for_current_year, format_month_worksheet, get_google_client
import gspread
import calendar

async def fix_format_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cập nhật format cho worksheet của tháng được chọn"""
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or f"user_{user_id}"
    
    # Lấy danh sách tham số từ tin nhắn
    args = context.args
    if not args:
        await update.message.reply_text("⚠ Vui lòng nhập số tháng. Ví dụ: `/fix_format 3`")
        return
    
    try:
        month_num = int(args[0])  # Lấy số tháng từ tham số
        if month_num < 1 or month_num > 12:
            raise ValueError
        month = calendar.month_name[month_num]  # Chuyển đổi số tháng thành tên tháng
    except ValueError:
        await update.message.reply_text("⚠ Vui lòng nhập số tháng hợp lệ từ 1 đến 12. Ví dụ: `/fix_format 3`")
        return

    # Lấy Google Sheet ID của năm hiện tại
    sheet_id = await get_user_sheet_for_current_year(user_id, username, update)

    if not sheet_id:
        await update.message.reply_text("❌ Bạn chưa có Google Sheet.")
        return

    try:
        # Mở Google Sheet và chọn worksheet theo tháng
        client = await get_google_client()
        sheet = await client.open_by_key(sheet_id)
        worksheet = await sheet.worksheet(month)  

        # Gọi hàm format worksheet
        await format_month_worksheet(worksheet, sheet_id)

        await update.message.reply_text(f"✅ Đã áp dụng định dạng cho sheet {month}!")

    except gspread.WorksheetNotFound:
        await update.message.reply_text(f"❌ Không tìm thấy sheet `{month}`. Hãy kiểm tra lại số tháng.")

def get_handlers():
    return CommandHandler("fix_format", fix_format_command)