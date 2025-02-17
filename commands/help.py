from collections import defaultdict
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, Application

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hiển thị danh sách lệnh theo nhóm."""
    category_map = {
        'User': ['start', 'help'],
        'Categories': ['add_cate', 'delete_cate', 'update_cate', 'list_cate'],
        'Google Sheets': ['apply_email', 'delete_email', 'list_emails'],
        'Khác': ['add_expense']
    }

    categories = defaultdict(list)
    
    # Lấy tất cả lệnh và mô tả
    for handler in context.application.handlers[0]:
        if isinstance(handler, CommandHandler):
            for command in handler.commands:
                description = handler.callback.__doc__ or "Không có mô tả"
                # Tìm kiếm category cho lệnh
                category = next(
                    (cat for cat, cmds in category_map.items() if command in cmds), 'Khác'
                )
                categories[category].append(f'/{command} - {description}')
    
    # Tạo chuỗi help text
    help_text = "**Danh sách các lệnh:**\n"
    
    # Duyệt qua các category và lệnh, thêm vào help_text
    for category, commands in sorted(categories.items()):
        help_text += f"\n**{category}**\n" + "\n".join(commands) + "\n"

    # Escape dấu `_` để Telegram không hiểu là Markdown syntax
    help_text = help_text.replace("_", "\\_")  # Escape dấu gạch dưới trong lệnh

    # Gửi phản hồi cho người dùng
    await update.message.reply_text(help_text, parse_mode="MarkdownV2")
def get_handlers():
    return CommandHandler("help", help_command)