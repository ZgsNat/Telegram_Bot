from telegram import Update
from telegram.ext import CommandHandler, Application, ContextTypes,CallbackContext
from services.category_crud_service import add_category, get_categories, delete_category, update_category

async def list_categories(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    categories = get_categories(user_id)
    if not categories:
        await update.message.reply_text("Chưa có categories nào.")
    else:
        await update.message.reply_text("📂 Danh sách Categories:\n" + "\n".join(categories))

async def add_category_handler(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    category_name = " ".join(context.args)
    if not category_name:
        await update.message.reply_text("Vui lòng nhập tên category.")
        return

    result = add_category(user_id, category_name)
    await update.message.reply_text(result)

async def delete_category_handler(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    category_name = " ".join(context.args)
    if not category_name:
        await update.message.reply_text("Vui lòng nhập tên category để xóa.")
        return

    result = delete_category(user_id, category_name)
    await update.message.reply_text(result)

async def update_category_handler(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Vui lòng nhập: /update_category <tên cũ> <tên mới>")
        return

    old_name, new_name = args[0], " ".join(args[1:])
    result = update_category(user_id, old_name, new_name)
    await update.message.reply_text(result)

def get_handlers():
    return [
        CommandHandler("add_cate", add_category_handler),
        CommandHandler("list_cate", list_categories),
        CommandHandler("delete_cate", delete_category_handler),
        CommandHandler("update_cate", update_category_handler),
    ]
